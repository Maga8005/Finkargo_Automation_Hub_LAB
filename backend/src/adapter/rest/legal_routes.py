"""
Legal Contract Automation - FastAPI Routes
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status, Path
from fastapi.responses import StreamingResponse
from typing import List, Optional
from uuid import UUID
import pandas as pd
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from src.config.supabase_config import get_supabase_client
from src.repositorio.client_repository import ClientRepository
from src.repositorio.contract_repository import ContractRepository
from src.repositorio.template_repository import TemplateRepository
from src.core.servicios.contract_service import ContractService
from src.core.servicios.document_service import DocumentService
from src.adapter.rest.rbac_dependencies import require_legal_role
from src.interface.legal_dtos import (
    ClientCreate,
    ClientResponse,
    ClientSearchRequest,
    ClientUpdate,
    ContractGenerationRequest,
    ContractGenerationResponse,
    ContractGenerationDetail,
    ContractReviewRequest,
    ContractReviewResponse,
    ContractHistoryFilter,
    ContractStats,
    BulkImportResult,
)

router = APIRouter(prefix="/api/legal", tags=["Legal Contracts"])


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
    # Create DocumentService with Supabase client for storage operations
    supabase = get_supabase_client()
    document_service = DocumentService(supabase_client=supabase)

    return ContractService(client_repo, contract_repo, template_repo, document_service)


# ==================== Client Endpoints ====================

@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_legal_role)
):
    """Create a new client (Legal role or Admin required)"""
    try:
        # Get user_id from authenticated user (dict)
        user_id = current_user['id']

        client = await client_repo.create(client_data, user_id)
        return client
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clients/search", response_model=List[ClientResponse])
async def search_clients(
    query: Optional[str] = None,
    nit: Optional[str] = None,
    nombre: Optional[str] = None,
    is_active: Optional[bool] = True,
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_legal_role)
):
    """Search clients by NIT or name (Legal role or Admin required)"""
    try:
        search_params = ClientSearchRequest(
            query=query,
            nit=nit,
            nombre=nombre,
            is_active=is_active
        )
        clients = await client_repo.search(search_params)
        return clients
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clients/{nit}", response_model=ClientResponse)
async def get_client_by_nit(
    nit: str,
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_legal_role)
):
    """Get client by NIT (Legal role or Admin required)"""
    client = await client_repo.get_by_nit(nit)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client with NIT {nit} not found")
    return client


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_legal_role)
):
    """Update client data (Legal role or Admin required)"""
    try:
        client = await client_repo.update(client_id, client_data)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/clients/import", response_model=BulkImportResult)
async def import_clients_csv(
    file: UploadFile = File(...),
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_legal_role)
):
    """
    Import clients from CSV or Excel file (Legal role or Admin required)

    Expected columns: nit, nombre_importador, representante_legal, cedula_representante, ciudad_domicilio, cupo_plataforma
    """
    try:
        # Get user_id from authenticated user (dict)
        user_id = current_user['id']

        # Read file
        contents = await file.read()

        # Determine file type and read accordingly
        if file.filename.endswith('.csv'):
            # Try multiple encodings for CSV files (common issue with Spanish characters)
            encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']
            df = None
            last_error = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding=encoding)
                    break  # Success, exit loop
                except UnicodeDecodeError as e:
                    last_error = e
                    continue

            if df is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not decode CSV file. Please ensure it's encoded in UTF-8, Latin-1, or Windows-1252. Error: {str(last_error)}"
                )
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="File must be CSV or Excel (.xlsx, .xls)")

        # Strip whitespace from column names (common CSV issue)
        df.columns = df.columns.str.strip()

        # Validate required columns
        required_columns = ['nit', 'nombre_importador', 'representante_legal',
                          'cedula_representante', 'ciudad_domicilio', 'cupo_plataforma']

        # Optional columns for contract template population
        optional_columns = ['direccion_comercial', 'tipo_identificacion_representante',
                           'nombre_contrato_marco', 'kam_nombre', 'kam_email',
                           'destinatario_nombre', 'destinatario_email']

        logger.info(f"CSV columns found: {list(df.columns)}")

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}. Found: {list(df.columns)}")
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(df.columns)}"
            )

        # Get all available columns (required + any present optional columns)
        available_columns = required_columns + [col for col in optional_columns if col in df.columns]

        # Convert to list of dicts
        clients = df[available_columns].to_dict('records')

        # Clean data (remove NaN, convert types)
        for client in clients:
            for key, value in client.items():
                if pd.isna(value):
                    client[key] = None if key != 'cupo_plataforma' else 0
                if key == 'cupo_plataforma':
                    client[key] = float(value) if value else 0

        # Bulk upsert
        result = await client_repo.bulk_upsert(clients, user_id)

        # Create import record (simplified - would normally track in data_imports table)
        return BulkImportResult(
            total_processed=result['total'],
            successful=result['successful'],
            failed=result['failed'],
            errors=result['errors'],
            import_id="placeholder-id"  # Would generate proper ID
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import failed with exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ==================== Contract Review Endpoints ====================

# IMPORTANT: Specific routes must come BEFORE parameterized routes
# Otherwise FastAPI will match "stats" as a contract_id parameter

@router.get("/contracts/stats", response_model=ContractStats)
async def get_contract_stats(
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_legal_role)
):
    """Get contract generation statistics (Legal role or Admin required)"""
    try:
        stats = await service.get_contract_stats()
        return ContractStats(
            total_generated=stats.get('total_generated', 0),
            pending_review=stats.get('pending_review', 0),
            approved=stats.get('approved', 0),
            rejected=stats.get('rejected', 0),
            generated_today=stats.get('generated_today', 0),
            generated_this_week=0,  # TODO: Calculate
            generated_this_month=0   # TODO: Calculate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/pending-review", response_model=List[ContractGenerationDetail])
async def get_pending_reviews(
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_legal_role)
):
    """Get all contracts pending legal review (Legal role or Admin required)"""
    try:
        contracts = await service.get_pending_reviews()
        return contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/contracts", response_model=List[ContractGenerationDetail])
async def get_contract_history(
    status: Optional[str] = None,
    client_nit: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    contract_repo: ContractRepository = Depends(get_contract_repo),
    current_user: dict = Depends(require_legal_role)
):
    """Get contract generation history with filters (Legal role or Admin required)"""
    try:
        from src.interface.legal_dtos import ContractStatus as StatusEnum

        filters = ContractHistoryFilter(
            status=StatusEnum(status) if status else None,
            client_nit=client_nit,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )

        contracts = await contract_repo.get_history(filters)
        return contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}", response_model=ContractGenerationDetail)
async def get_contract(
    contract_id: UUID = Path(..., description="Contract UUID"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_legal_role)
):
    """Get contract details by ID (Legal role or Admin required)"""
    contract = await service.get_contract_details(str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.get("/contracts/{contract_id}/preview")
async def preview_contract(
    contract_id: UUID = Path(..., description="Contract UUID"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_legal_role)
):
    """Get populated contract content for preview (Legal role or Admin required)"""
    try:
        content = await service.populate_template(str(contract_id))
        return {"content": content}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/{contract_id}/review", response_model=ContractReviewResponse)
async def review_contract(
    contract_id: UUID = Path(..., description="Contract UUID"),
    review: ContractReviewRequest = None,
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_legal_role)
):
    """Review a contract (approve or reject) - Legal role or Admin required"""
    try:
        # Get user_id from authenticated user (dict)
        reviewer_id = current_user['id']

        contract = await service.review_contract(
            contract_id=str(contract_id),
            action=review.action,
            reviewer_id=reviewer_id,
            notes=review.notes
        )
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Template Endpoints ====================

@router.get("/templates/active")
async def get_active_template(
    template_repo: TemplateRepository = Depends(get_template_repo),
    current_user: dict = Depends(require_legal_role)
):
    """Get active contract template (Legal role or Admin required)"""
    template = await template_repo.get_active_template('activos')
    if not template:
        raise HTTPException(status_code=404, detail="No active template found")
    return template


# ==================== Document Download Endpoints ====================

@router.get("/contracts/{contract_id}/download/docx")
async def download_contract_docx(
    contract_id: UUID = Path(..., description="Contract UUID"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_legal_role)
):
    """
    Download contract as DOCX file (Legal role or Admin required)

    Args:
        contract_id: Contract UUID

    Returns:
        StreamingResponse with DOCX file
    """
    try:
        logger.info(f"Starting DOCX generation for contract {contract_id}")
        # Generate document
        docx_bytes = await service.generate_contract_document(str(contract_id))
        logger.info(f"DOCX generated successfully for contract {contract_id}")

        # Get contract details for filename
        contract = await service.get_contract_details(str(contract_id))
        filename = f"{contract['contract_id']}.docx"

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        logger.error(f"ValueError in DOCX download: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in DOCX download: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")


@router.get("/contracts/{contract_id}/download/pdf")
async def download_contract_pdf(
    contract_id: UUID = Path(..., description="Contract UUID"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_legal_role)
):
    """
    Download contract as PDF file (Legal role or Admin required)

    Args:
        contract_id: Contract UUID

    Returns:
        StreamingResponse with PDF file
    """
    try:
        logger.info(f"Starting PDF generation for contract {contract_id}")
        # Generate PDF
        pdf_bytes = await service.generate_contract_pdf(str(contract_id))
        logger.info(f"PDF generated successfully for contract {contract_id}")

        # Get contract details for filename
        contract = await service.get_contract_details(str(contract_id))
        filename = f"{contract['contract_id']}.pdf"

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        logger.error(f"ValueError in PDF download: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # PDF conversion failed, offer DOCX instead
        logger.error(f"RuntimeError in PDF conversion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF conversion failed: {str(e)}. Please download DOCX instead."
        )
    except Exception as e:
        logger.error(f"Unexpected error in PDF download: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
