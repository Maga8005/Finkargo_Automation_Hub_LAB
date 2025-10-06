"""
Operations Department - FastAPI Routes
Handles contract generation requests and approved contract downloads
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path
from fastapi.responses import StreamingResponse
from typing import List, Optional
from uuid import UUID
import io

from src.config.supabase_client import get_supabase_client
from src.repositorio.client_repository import ClientRepository
from src.repositorio.contract_repository import ContractRepository
from src.repositorio.template_repository import TemplateRepository
from src.core.servicios.contract_service import ContractService
from src.core.servicios.document_service import DocumentService
from src.interface.legal_dtos import (
    ContractGenerationRequest,
    ContractGenerationResponse,
    ContractGenerationDetail,
)

router = APIRouter(prefix="/api/operations", tags=["Operations"])


# Dependency to get repositories
def get_client_repo():
    """Get client repository"""
    db = get_supabase_client()
    return ClientRepository(db)


def get_contract_repo():
    """Get contract repository"""
    db = get_supabase_client()
    return ContractRepository(db)


def get_template_repo():
    """Get template repository"""
    db = get_supabase_client()
    return TemplateRepository(db)


def get_contract_service(
    client_repo: ClientRepository = Depends(get_client_repo),
    contract_repo: ContractRepository = Depends(get_contract_repo),
    template_repo: TemplateRepository = Depends(get_template_repo),
):
    """Get contract service with document service"""
    supabase = get_supabase_client()
    document_service = DocumentService(supabase_client=supabase)
    return ContractService(client_repo, contract_repo, template_repo, document_service)


# ==================== Contract Generation Endpoints ====================

@router.post("/contracts/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def request_contract_generation(
    request: ContractGenerationRequest,
    service: ContractService = Depends(get_contract_service)
):
    """
    Request a new contract generation (Operations initiates)

    This creates a contract in UNDER_REVIEW status for Legal to approve.
    """
    try:
        # TODO: Get user_id from auth token
        user_id = None  # NULL for now until auth is implemented

        contract = await service.generate_contract(request, user_id)
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/approved", response_model=List[ContractGenerationDetail])
async def get_approved_contracts(
    contract_repo: ContractRepository = Depends(get_contract_repo)
):
    """
    Get all approved contracts for Operations team

    Returns contracts with approved status and document URLs for download
    """
    try:
        contracts = await contract_repo.get_approved_contracts()
        return contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}", response_model=ContractGenerationDetail)
async def get_contract_details(
    contract_id: UUID = Path(..., description="Contract UUID"),
    service: ContractService = Depends(get_contract_service)
):
    """Get contract details by ID"""
    contract = await service.get_contract_details(str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.get("/contracts/{contract_id}/download/pdf")
async def download_approved_contract_pdf(
    contract_id: UUID = Path(..., description="Contract UUID"),
    contract_repo: ContractRepository = Depends(get_contract_repo)
):
    """
    Download approved contract PDF from storage

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
