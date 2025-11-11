"""
Operations Department - FastAPI Routes
Handles contract generation requests and approved contract downloads
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
from uuid import UUID
import io

from src.config.supabase_config import get_supabase_client
from src.repositorio.client_repository import ClientRepository
from src.repositorio.contract_repository import ContractRepository
from src.repositorio.template_repository import TemplateRepository
from src.core.servicios.contract_service import ContractService
from src.core.servicios.document_service import DocumentService
from src.core.servicios.rut_parser_service import RUTParserService
from src.adapter.rest.rbac_dependencies import require_operations_role
from src.interface.legal_dtos import (
    ContractGenerationRequest,
    ContractGenerationResponse,
    ContractGenerationDetail,
    ContractType,
)

router = APIRouter(prefix="/api/operations", tags=["Operations"])


# Dependency to get repositories
def get_client_repo():
    """Get client repository with admin client (bypasses RLS)"""
    supabase = get_supabase_client()
    return ClientRepository(supabase.admin_client)


def get_contract_repo():
    """Get contract repository with admin client (bypasses RLS)"""
    supabase = get_supabase_client()
    return ContractRepository(supabase.admin_client)


def get_template_repo():
    """Get template repository with admin client (bypasses RLS)"""
    supabase = get_supabase_client()
    return TemplateRepository(supabase.admin_client)


def get_contract_service(
    client_repo: ClientRepository = Depends(get_client_repo),
    contract_repo: ContractRepository = Depends(get_contract_repo),
    template_repo: TemplateRepository = Depends(get_template_repo),
):
    """Get contract service with document service"""
    supabase = get_supabase_client()
    document_service = DocumentService(supabase_client=supabase.admin_client)
    return ContractService(client_repo, contract_repo, template_repo, document_service)


# ==================== Contract Generation Endpoints ====================

@router.post("/contracts/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def request_contract_generation(
    client_nit: str = Form(..., description="Client NIT"),
    contract_type: str = Form(..., description="Contract type (activos, otrosi, inventario_bodega)"),
    rut_file: Optional[UploadFile] = File(None, description="RUT PDF document (required for inventario_bodega)"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_operations_role)
):
    """
    Request a new contract generation (Operations role or Admin required)

    This creates a contract in UNDER_REVIEW status for Legal to approve.

    For Inventario Bodega contracts, a RUT document must be uploaded to extract custodian information.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Get user_id from authenticated user (dict)
        user_id = current_user['id']

        # Validate contract type
        try:
            contract_type_enum = ContractType(contract_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid contract type: {contract_type}. Must be one of: activos, otrosi, inventario_bodega"
            )

        # Parse custodian data from RUT if Inventario Bodega
        custodian_data = None
        if contract_type_enum == ContractType.INVENTARIO_BODEGA:
            if not rut_file:
                raise HTTPException(
                    status_code=400,
                    detail="RUT document is required for Inventario Bodega contracts"
                )

            # Validate file type
            if rut_file.content_type != 'application/pdf':
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {rut_file.content_type}. Only PDF files are allowed"
                )

            # Validate file size (5MB limit)
            rut_bytes = await rut_file.read()
            if len(rut_bytes) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="RUT file size exceeds 5MB limit"
                )

            # Parse RUT document
            logger.info(f"Parsing RUT document: {rut_file.filename}")
            parser = RUTParserService()

            try:
                custodian_data = parser.parse_rut_pdf(rut_bytes)
                logger.info(f"RUT parsed successfully for custodian: {custodian_data.nombre_operador_custodio}")
            except ValueError as e:
                logger.error(f"RUT parsing failed: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing RUT document: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Unexpected error parsing RUT: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse RUT document: {str(e)}"
                )

        # Create request object
        request = ContractGenerationRequest(
            client_nit=client_nit,
            contract_type=contract_type_enum,
            custodian_data=custodian_data
        )

        contract = await service.generate_contract(request, user_id)
        return contract
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating contract: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/approved", response_model=List[ContractGenerationDetail])
async def get_approved_contracts(
    contract_type: Optional[str] = None,
    contract_repo: ContractRepository = Depends(get_contract_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Get all approved contracts for Operations team (Operations role or Admin required)

    Query Parameters:
        contract_type: Optional filter by contract type ('activos' or 'otrosi')

    Returns contracts with approved status and document URLs for download
    """
    try:
        contracts = await contract_repo.get_approved_contracts(contract_type)
        return contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}", response_model=ContractGenerationDetail)
async def get_contract_details(
    contract_id: UUID = Path(..., description="Contract UUID"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_operations_role)
):
    """Get contract details by ID (Operations role or Admin required)"""
    contract = await service.get_contract_details(str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.get("/contracts/{contract_id}/download/pdf")
async def download_approved_contract_pdf(
    contract_id: UUID = Path(..., description="Contract UUID"),
    contract_repo: ContractRepository = Depends(get_contract_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Download approved contract PDF from storage (Operations role or Admin required)

    Args:
        contract_id: Contract UUID

    Returns:
        StreamingResponse with PDF file from Supabase Storage
    """
    try:
        # Get contract
        contract = await contract_repo.get_by_id(str(contract_id))
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Check if approved
        if contract['status'] != 'approved':
            raise HTTPException(
                status_code=400,
                detail=f"Contract is not approved. Current status: {contract['status']}"
            )

        # Check if PDF URL exists
        if not contract.get('approved_document_url'):
            raise HTTPException(
                status_code=404,
                detail="Approved PDF not available. Please contact Legal department."
            )

        # Get Supabase client
        supabase = get_supabase_client()

        # Download from storage
        # The approved_document_url is a public URL, so we can redirect
        # Or we can download and stream it
        from urllib.parse import urlparse
        pdf_url = contract['approved_document_url']

        # Extract bucket and path from URL
        # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
        parsed = urlparse(pdf_url)
        path_parts = parsed.path.split('/storage/v1/object/public/')
        if len(path_parts) < 2:
            raise HTTPException(status_code=500, detail="Invalid storage URL format")

        bucket_and_path = path_parts[1]
        bucket_name = bucket_and_path.split('/')[0]
        file_path = '/'.join(bucket_and_path.split('/')[1:])

        # Download file
        pdf_bytes = supabase.storage.from_(bucket_name).download(file_path)

        filename = f"{contract['contract_id']}_approved.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")
