"""
PA Routes - API endpoints for PA Report Classification feature.

Provides endpoints for:
- Rules management (catalog, classification rules, nexo rules)
- Report processing (upload, clean, classify, download)
- Processing history
"""

import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from io import BytesIO

from src.interface.pa_dtos import (
    PAAccountCatalogResponse,
    PAAccountCatalogUploadResponse,
    PAClassificationRulesResponse,
    PAClassificationRulesUploadResponse,
    PAClasificacionCuentaRulesResponse,
    PAClasificacionCuentaRulesUploadResponse,
    PANexoRulesResponse,
    PANexoRulesUploadResponse,
    PARulesSummary,
    PAUploadResponse,
    PACleanedPreview,
    PAClassifiedPreview,
    PAProcessingHistoryResponse,
    PAProcessingStats
)
from src.adapter.rest.dependencies import get_current_user
from src.adapter.rest.rbac_dependencies import require_roles
from src.config.supabase_config import get_supabase_client
from src.repositorio.pa_rules_repository import get_pa_rules_repository, PARulesRepository
from src.core.servicios.pa_rules_service import get_pa_rules_service, PARulesService
from src.core.servicios.pa_report_service import get_pa_report_service, PAReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/finance/pa", tags=["Finance - Reporte PA"])


# =============================================================================
# Dependencies
# =============================================================================

def get_repository() -> PARulesRepository:
    """Get PA rules repository instance."""
    supabase = get_supabase_client()
    # Use admin_client to access the actual Supabase Client with .table() methods
    return get_pa_rules_repository(supabase.admin_client)


def get_rules_service(repo: PARulesRepository = Depends(get_repository)) -> PARulesService:
    """Get PA rules service instance."""
    return get_pa_rules_service(repo)


def get_report_service(repo: PARulesRepository = Depends(get_repository)) -> PAReportService:
    """Get PA report service instance."""
    return get_pa_report_service(repo)


# =============================================================================
# Rules Summary
# =============================================================================

@router.get(
    "/rules/summary",
    response_model=PARulesSummary,
    summary="Get rules summary",
    description="Get summary of all loaded PA classification rules."
)
async def get_rules_summary(
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(get_current_user)
):
    """Get summary of all loaded rules."""
    return await service.get_rules_summary()


# =============================================================================
# Account Catalog Endpoints
# =============================================================================

@router.post(
    "/rules/catalog/upload",
    response_model=PAAccountCatalogUploadResponse,
    summary="Upload account catalog",
    description="Upload Excel file with PA account catalog for filtering and homologation."
)
async def upload_account_catalog(
    file: UploadFile = File(..., description="Excel file with account catalog"),
    replace_existing: bool = Query(True, description="Replace existing catalog entries"),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(require_roles(["finance_admin", "admin"]))
):
    """Upload PA account catalog Excel file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo es requerido")

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx o .xls")

    content = await file.read()
    user_id = getattr(current_user, "id", None) or current_user.get("id")

    return await service.upload_account_catalog(
        file_content=content,
        filename=file.filename,
        created_by=user_id,
        replace_existing=replace_existing
    )


@router.get(
    "/rules/catalog",
    response_model=PAAccountCatalogResponse,
    summary="Get account catalog",
    description="Get current PA account catalog entries."
)
async def get_account_catalog(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(get_current_user)
):
    """Get PA account catalog entries."""
    entries, total = await service.get_account_catalog(limit=limit, offset=offset)
    return PAAccountCatalogResponse(entries=entries, total_count=total)


# =============================================================================
# Classification Rules Endpoints
# =============================================================================

@router.post(
    "/rules/classification/upload",
    response_model=PAClassificationRulesUploadResponse,
    summary="Upload classification rules",
    description="Upload Excel file with main classification rules."
)
async def upload_classification_rules(
    file: UploadFile = File(..., description="Excel file with classification rules"),
    replace_existing: bool = Query(True, description="Replace existing rules"),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(require_roles(["finance_admin", "admin"]))
):
    """Upload classification rules Excel file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo es requerido")

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx o .xls")

    content = await file.read()
    user_id = getattr(current_user, "id", None) or current_user.get("id")

    return await service.upload_classification_rules(
        file_content=content,
        filename=file.filename,
        created_by=user_id,
        replace_existing=replace_existing
    )


@router.get(
    "/rules/classification",
    response_model=PAClassificationRulesResponse,
    summary="Get classification rules",
    description="Get current PA classification rules."
)
async def get_classification_rules(
    active_only: bool = Query(True),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(get_current_user)
):
    """Get PA classification rules."""
    rules = await service.get_classification_rules(active_only=active_only)
    return PAClassificationRulesResponse(rules=rules, total_count=len(rules))


# =============================================================================
# Clasificación Cuenta Rules Endpoints
# =============================================================================

@router.post(
    "/rules/clasificacion-cuenta/upload",
    response_model=PAClasificacionCuentaRulesUploadResponse,
    summary="Upload clasificación cuenta rules",
    description="Upload Excel file with account name → classification rules."
)
async def upload_clasificacion_cuenta_rules(
    file: UploadFile = File(..., description="Excel file with clasificación cuenta rules"),
    replace_existing: bool = Query(True, description="Replace existing rules"),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(require_roles(["finance_admin", "admin"]))
):
    """Upload clasificación cuenta rules Excel file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo es requerido")

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx o .xls")

    content = await file.read()
    user_id = getattr(current_user, "id", None) or current_user.get("id")

    return await service.upload_clasificacion_cuenta_rules(
        file_content=content,
        filename=file.filename,
        created_by=user_id,
        replace_existing=replace_existing
    )


@router.get(
    "/rules/clasificacion-cuenta",
    response_model=PAClasificacionCuentaRulesResponse,
    summary="Get clasificación cuenta rules",
    description="Get current clasificación cuenta rules."
)
async def get_clasificacion_cuenta_rules(
    active_only: bool = Query(True),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(get_current_user)
):
    """Get clasificación cuenta rules."""
    rules = await service.get_clasificacion_cuenta_rules(active_only=active_only)
    return PAClasificacionCuentaRulesResponse(rules=rules, total_count=len(rules))


# =============================================================================
# Nexo Rules Endpoints
# =============================================================================

@router.post(
    "/rules/nexo/upload",
    response_model=PANexoRulesUploadResponse,
    summary="Upload nexo rules",
    description="Upload Excel file with account name → nexo rules."
)
async def upload_nexo_rules(
    file: UploadFile = File(..., description="Excel file with nexo rules"),
    replace_existing: bool = Query(True, description="Replace existing rules"),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(require_roles(["finance_admin", "admin"]))
):
    """Upload nexo rules Excel file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo es requerido")

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx o .xls")

    content = await file.read()
    user_id = getattr(current_user, "id", None) or current_user.get("id")

    return await service.upload_nexo_rules(
        file_content=content,
        filename=file.filename,
        created_by=user_id,
        replace_existing=replace_existing
    )


@router.get(
    "/rules/nexo",
    response_model=PANexoRulesResponse,
    summary="Get nexo rules",
    description="Get current nexo rules."
)
async def get_nexo_rules(
    active_only: bool = Query(True),
    service: PARulesService = Depends(get_rules_service),
    current_user: dict = Depends(get_current_user)
):
    """Get nexo rules."""
    rules = await service.get_nexo_rules(active_only=active_only)
    return PANexoRulesResponse(rules=rules, total_count=len(rules))


# =============================================================================
# Report Processing Endpoints
# =============================================================================

@router.post(
    "/process/upload",
    response_model=PAUploadResponse,
    summary="Upload NetSuite file",
    description="Upload NetSuite movements file and create processing session. Supports files up to 50 MB."
)
async def upload_netsuite_file(
    file: UploadFile = File(..., description="NetSuite movements Excel or CSV file"),
    service: PAReportService = Depends(get_report_service),
    current_user: dict = Depends(get_current_user)
):
    """Upload NetSuite movements file for processing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo es requerido")

    if not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx, .xls o .csv")

    try:
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        logger.info(f"Processing upload: {file.filename} ({file_size_mb:.2f} MB)")

        user_id = getattr(current_user, "id", None) or current_user.get("id")
        user_email = getattr(current_user, "email", None) or current_user.get("email")

        return await service.upload_netsuite_file(
            file_content=content,
            filename=file.filename,
            user_id=user_id,
            user_email=user_email
        )
    except MemoryError:
        logger.error(f"Memory error processing file: {file.filename}")
        raise HTTPException(
            status_code=413,
            detail="El archivo es demasiado grande para procesar. Intente con un archivo más pequeño o divídalo en partes."
        )
    except Exception as e:
        logger.error(f"Error processing upload {file.filename}: {e}", exc_info=True)
        # Re-raise HTTPExceptions as-is
        if isinstance(e, HTTPException):
            raise
        # Return a user-friendly error for other exceptions
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el archivo: {str(e)}"
        )


@router.post(
    "/process/{session_id}/clean",
    response_model=PACleanedPreview,
    summary="Clean data (Step 1)",
    description="Clean and prepare PA data for classification."
)
async def clean_data(
    session_id: str,
    service: PAReportService = Depends(get_report_service),
    current_user: dict = Depends(get_current_user)
):
    """Step 1: Clean and prepare PA data."""
    return await service.clean_data(session_id)


@router.get(
    "/process/{session_id}/clean/download",
    summary="Download cleaned file",
    description="Download cleaned PA data as Excel file."
)
async def download_cleaned_file(
    session_id: str,
    service: PAReportService = Depends(get_report_service),
    current_user: dict = Depends(get_current_user)
):
    """Download cleaned Excel file."""
    content = await service.get_cleaned_excel(session_id)

    if not content:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o sesión inválida")

    filename = f"PA_Limpio_{session_id}.xlsx"
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post(
    "/process/{session_id}/classify",
    response_model=PAClassifiedPreview,
    summary="Classify data (Step 2)",
    description="Apply classification rules to cleaned PA data."
)
async def classify_data(
    session_id: str,
    service: PAReportService = Depends(get_report_service),
    current_user: dict = Depends(get_current_user)
):
    """Step 2: Apply classification rules."""
    return await service.classify_data(session_id)


@router.get(
    "/process/{session_id}/classify/download",
    summary="Download classified file",
    description="Download classified PA data as Excel file."
)
async def download_classified_file(
    session_id: str,
    service: PAReportService = Depends(get_report_service),
    current_user: dict = Depends(get_current_user)
):
    """Download classified Excel file."""
    content = await service.get_classified_excel(session_id)

    if not content:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o sesión inválida")

    filename = f"PA_Clasificado_{session_id}.xlsx"
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get(
    "/process/{session_id}/stats",
    response_model=PAProcessingStats,
    summary="Get processing stats",
    description="Get statistics for a processing session."
)
async def get_session_stats(
    session_id: str,
    service: PAReportService = Depends(get_report_service),
    current_user: dict = Depends(get_current_user)
):
    """Get processing session statistics."""
    stats = await service.get_session_stats(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return stats


# =============================================================================
# History Endpoints
# =============================================================================

@router.get(
    "/history",
    response_model=PAProcessingHistoryResponse,
    summary="Get processing history",
    description="Get PA report processing history with filters."
)
async def get_processing_history(
    status: Optional[str] = Query(None),
    processed_by: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    repo: PARulesRepository = Depends(get_repository),
    current_user: dict = Depends(get_current_user)
):
    """Get processing history with filters."""
    entries, total = await repo.get_processing_history(
        status=status,
        processed_by=processed_by,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        limit=limit,
        offset=offset
    )

    return PAProcessingHistoryResponse(
        entries=entries,
        total_count=total,
        limit=limit,
        offset=offset
    )
