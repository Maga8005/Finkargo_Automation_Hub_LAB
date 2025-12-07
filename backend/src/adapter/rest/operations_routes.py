"""
Operations Department - FastAPI Routes
Handles contract generation requests and approved contract downloads
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import io

from src.config.supabase_config import get_supabase_client
from src.repositorio.client_repository import ClientRepository
from src.repositorio.contract_repository import ContractRepository
from src.repositorio.template_repository import TemplateRepository
from src.core.servicios.contract_service import ContractService
from src.core.servicios.document_service import DocumentService
from src.core.servicios.rut_parser_service import RUTParserService
from src.core.servicios.cotizacion_parser_service import CotizacionParserService
from src.adapter.rest.rbac_dependencies import require_operations_role
from src.interface.legal_dtos import (
    ContractGenerationRequest,
    ContractGenerationResponse,
    ContractGenerationDetail,
    ContractType,
    CotizacionData,
    SolicitudDesembolsoRequest,
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

    # Log incoming request
    logger.info(f"Contract generation request received - NIT: {client_nit}, Type: {contract_type}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Get user_id from authenticated user (dict)
        user_id = current_user['id']

        # Validate contract type
        try:
            contract_type_enum = ContractType(contract_type)
        except ValueError as e:
            logger.error(f"Invalid contract type '{contract_type}' for NIT {client_nit}: {e}")
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
        # Handle both dict and object response types
        contract_id = contract.contract_id if hasattr(contract, 'contract_id') else contract.get('contract_id', 'unknown')
        logger.info(f"Contract generated successfully - Contract ID: {contract_id}, NIT: {client_nit}, Type: {contract_type}")
        return contract
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error for NIT {client_nit}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating contract for NIT {client_nit}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Solicitud de Desembolso Endpoints ====================

@router.post("/contracts/solicitud-desembolso/parse-cotizacion", response_model=CotizacionData)
async def parse_cotizacion_pdf(
    file: UploadFile = File(..., description="Cotización PDF document"),
    current_user: dict = Depends(require_operations_role)
):
    """
    Parse Cotización PDF and extract disbursement request data (Operations role or Admin required)

    This endpoint extracts structured data from Cotización PDFs including:
    - Quote number (numero_cotizacion)
    - Credit contract date
    - Legal representative information
    - Anexo I table items with amounts
    - Total amount

    Returns extracted data for form pre-population
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Cotización PDF parse request - File: {file.filename}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Validate file type
        if file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed"
            )

        # Validate file size (5MB limit)
        pdf_bytes = await file.read()
        if len(pdf_bytes) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="PDF file size exceeds 5MB limit"
            )

        # Parse Cotización document
        logger.info(f"Parsing Cotización document: {file.filename}")
        parser = CotizacionParserService()

        try:
            cotizacion_data = parser.parse_cotizacion(pdf_bytes)
            logger.info(f"Cotización parsed successfully - Quote: {cotizacion_data.numero_cotizacion}, Items: {len(cotizacion_data.anexo_items)}")
            return cotizacion_data
        except ValueError as e:
            logger.error(f"Cotización parsing failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Error parsing Cotización document: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing Cotización: {e}", exc_info=True)
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse Cotización document: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Cotización PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/solicitud-desembolso/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_solicitud_desembolso(
    request: SolicitudDesembolsoRequest,
    service: ContractService = Depends(get_contract_service),
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Generate Solicitud de Desembolso contract (Operations role or Admin required)

    This creates a Solicitud de Desembolso contract in UNDER_REVIEW status for Legal approval.

    The request must include:
    - client_nit: Client NIT for database lookup
    - numero_cotizacion_desembolso: Quote number
    - fecha_contrato_credito: Credit contract date (ISO format)
    - monto: Total disbursement amount
    - dias_plazo: Term in days (30-180)
    - anexo_items: List of Anexo I table items

    Returns the created contract with ID format: PLSD-YYYY-XXX
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Solicitud de Desembolso generation request - NIT: {request.client_nit}, Quote: {request.numero_cotizacion_desembolso}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Get user_id from authenticated user
        user_id = current_user['id']

        # Validate client exists
        client = await client_repo.get_by_nit(request.client_nit)
        if not client:
            logger.error(f"Client not found with NIT: {request.client_nit}")
            raise HTTPException(
                status_code=404,
                detail=f"Client with NIT {request.client_nit} not found"
            )

        # Build data snapshot combining client data + solicitud data
        from decimal import Decimal
        data_snapshot = {
            # Client data
            "nit": client.nit,
            "nombre_importador": client.nombre_importador,
            "representante_legal": client.representante_legal,
            "cedula_representante": client.cedula_representante,
            "ciudad_domicilio": client.ciudad_domicilio,
            "cupo_plataforma": float(client.cupo_plataforma) if isinstance(client.cupo_plataforma, Decimal) else client.cupo_plataforma,
            "direccion_comercial": client.direccion_comercial,
            "tipo_identificacion_representante": client.tipo_identificacion_representante,
            # Solicitud de Desembolso specific data
            "numero_cotizacion_desembolso": request.numero_cotizacion_desembolso,
            "fecha_contrato_credito": request.fecha_contrato_credito,
            "monto": float(request.monto),
            "dias_plazo": request.dias_plazo,
            "anexo_items": [
                {
                    "acreedor": item.acreedor,
                    "numero_instrumento": item.numero_instrumento,
                    "monto": float(item.monto)
                }
                for item in request.anexo_items
            ]
        }

        # Create contract generation request
        contract_request = ContractGenerationRequest(
            client_nit=request.client_nit,
            contract_type=ContractType.PL_CO_SOLICITUD_DESEMBOLSO,
            custodian_data=None  # Not needed for Solicitud de Desembolso
        )

        # Generate contract with custom data snapshot
        contract = await service.generate_contract(
            request=contract_request,
            user_id=user_id,
            custom_data_snapshot=data_snapshot
        )

        contract_id = contract.contract_id if hasattr(contract, 'contract_id') else contract.get('contract_id', 'unknown')
        logger.info(f"Solicitud de Desembolso generated successfully - Contract ID: {contract_id}, NIT: {request.client_nit}, Quote: {request.numero_cotizacion_desembolso}")
        return contract

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error for NIT {request.client_nit}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating Solicitud de Desembolso for NIT {request.client_nit}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/approved", response_model=List[ContractGenerationDetail])
async def get_approved_contracts(
    contract_type: Optional[str] = None,
    contract_types: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    client_name: Optional[str] = None,
    client_nit: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    cupo_min: Optional[float] = None,
    cupo_max: Optional[float] = None,
    contract_repo: ContractRepository = Depends(get_contract_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Get all approved contracts for Operations team (Operations role or Admin required)

    Query Parameters:
        contract_type: Optional filter by single contract type
        contract_types: Optional filter by multiple contract types (comma-separated)
        sort_by: Optional field to sort by (contract_id, contract_type, client_nit, reviewed_at,
                 data_snapshot->nombre_importador, data_snapshot->cupo_plataforma)
        sort_order: Optional sort order ('asc' or 'desc', defaults to 'desc')
        client_name: Optional filter by client name (partial match, case-insensitive)
        client_nit: Optional filter by NIT (partial match)
        date_from: Optional filter by approval date >= this date (ISO 8601 format)
        date_to: Optional filter by approval date <= this date (ISO 8601 format)
        cupo_min: Optional filter by credit limit >= this value
        cupo_max: Optional filter by credit limit <= this value

    Returns contracts with approved status and document URLs for download
    """
    try:
        # Validate sort_order
        validated_sort_order = sort_order if sort_order in ['asc', 'desc'] else 'desc'

        # Validate date range
        if date_from and date_to:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                if from_date > to_date:
                    raise HTTPException(
                        status_code=400,
                        detail="date_from must be less than or equal to date_to"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                )

        # Validate credit limit range
        if cupo_min is not None and cupo_max is not None:
            if cupo_min > cupo_max:
                raise HTTPException(
                    status_code=400,
                    detail="cupo_min must be less than or equal to cupo_max"
                )

        # Parse contract_types if provided (comma-separated string)
        contract_types_list: Optional[List[str]] = None
        if contract_types:
            contract_types_list = [ct.strip() for ct in contract_types.split(',') if ct.strip()]
        elif contract_type:
            # Single contract_type for backward compatibility
            contract_types_list = [contract_type]

        contracts = await contract_repo.get_approved_contracts(
            contract_types=contract_types_list,
            sort_by=sort_by,
            sort_order=validated_sort_order,
            client_name=client_name,
            client_nit=client_nit,
            date_from=date_from,
            date_to=date_to,
            cupo_min=cupo_min,
            cupo_max=cupo_max
        )
        return contracts
    except HTTPException:
        raise
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
