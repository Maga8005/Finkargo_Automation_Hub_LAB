"""
Finance Routes for Facturación MX automation.

This module contains all API endpoints for the Mexico invoicing
automation feature including Excel upload, search, and ZIP generation.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from src.interface.finance_dtos import (
    ExcelValidationResponse,
    InvoiceSearchRequest,
    InvoiceSearchResponse,
    ZipGenerationRequest,
    ZipGenerationResponse
)
from src.core.servicios.excel_validation_service import ExcelValidationService
from src.core.servicios.invoice_search_service import (
    InvoiceSearchService,
    get_invoice_search_service
)
from src.core.servicios.zip_generator_service import get_zip_service
from src.core.servicios.google_drive_service import get_drive_service
from src.core.servicios.excel_merge_service import get_excel_merge_service
from src.adapter.rest.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/finance", tags=["Finance - Facturación MX"])


def get_excel_validation_service() -> ExcelValidationService:
    """Dependency for Excel validation service."""
    return ExcelValidationService()


@router.post(
    "/upload-excel",
    response_model=ExcelValidationResponse,
    summary="Upload and validate master Excel file",
    description="""
    Upload an Excel file (.xlsx or .xls) containing invoice data.

    The file must contain the following columns:
    - UUID
    - CODIGO DE OPERACIÓN
    - Conceptos
    - Fecha emision
    - RFC receptor
    - Razon receptor
    - SubTotal
    - IVA Trasladado
    - IVA Exento
    - Total

    Returns validation results and a session_id for subsequent operations.
    """
)
async def upload_excel(
    file: UploadFile = File(..., description="Excel file with invoice data"),
    excel_service: ExcelValidationService = Depends(get_excel_validation_service),
    search_service: InvoiceSearchService = Depends(get_invoice_search_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and validate an Excel file with invoice data.

    Args:
        file: Excel file to upload
        excel_service: Excel validation service
        search_service: Invoice search service for session storage
        current_user: Authenticated user

    Returns:
        ExcelValidationResponse with parsed data and validation errors

    Raises:
        HTTPException: If file format is invalid or processing fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} uploading Excel: {file.filename}")

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo es requerido")

    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo no soportado. Use .xlsx o .xls"
        )

    # Validate content type
    valid_content_types = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'application/octet-stream'  # Some browsers send this
    ]
    if file.content_type and file.content_type not in valid_content_types:
        logger.warning(f"Unexpected content type: {file.content_type}")

    try:
        # Step 1: Validate uploaded Excel
        result = await excel_service.validate_excel(file)

        if not result.data:
            logger.warning("No valid data to process")
            return result

        # Step 2: Sync with Drive master Excel (32 columns)
        try:
            merge_service = get_excel_merge_service()
            drive_service = get_drive_service()

            logger.info("Starting Drive sync workflow (32 columns)...")

            # Read uploaded file as dicts (32 columns)
            uploaded_dicts = await merge_service.read_uploaded_excel_as_dicts(file)
            logger.info(f"Read {len(uploaded_dicts)} records from uploaded file (32 columns)")

            # Download Drive master Excel (if exists)
            master_excel_bytes = drive_service.download_master_excel()

            if master_excel_bytes:
                # Master exists - merge with uploaded data
                logger.info("Master Excel found - merging data (32 columns)")
                master_dicts = merge_service.read_excel_from_bytes(master_excel_bytes)
                merged_dicts, merge_stats = merge_service.merge_invoice_data(
                    uploaded_records=uploaded_dicts,
                    master_records=master_dicts
                )
                result.drive_sync_stats = merge_stats
            else:
                # No master - uploaded data becomes the new master
                logger.info("No master Excel found - creating new master (32 columns)")
                merged_dicts = uploaded_dicts
                result.drive_sync_stats = {
                    'new': len(uploaded_dicts),
                    'updated': 0,
                    'unchanged': 0
                }

            # Write merged data back to Drive (32 columns)
            merged_excel_bytes = merge_service.write_excel_to_bytes(merged_dicts)
            upload_success = drive_service.upload_master_excel(merged_excel_bytes)

            if upload_success:
                logger.info(f"Drive sync complete - {result.drive_sync_stats}")

                # Convert merged dicts to InvoiceRecords for session storage (11 columns)
                invoice_records = merge_service.convert_dicts_to_invoice_records(merged_dicts)
                result.data = invoice_records
                logger.info(f"Converted {len(invoice_records)} records for session storage")
            else:
                logger.warning("Failed to upload to Drive - using uploaded data only")

        except Exception as drive_error:
            logger.error(f"Drive sync failed: {drive_error}", exc_info=True)
            logger.warning("Continuing without Drive sync - using uploaded data only")
            result.drive_sync_stats = None

        # Step 3: Store data in session cache
        if result.data:
            search_service.store_session(result.session_id, result.data)
            logger.info(f"Session {result.session_id} created with {len(result.data)} records")

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing Excel: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el archivo: {str(e)}"
        )


@router.post(
    "/search",
    response_model=InvoiceSearchResponse,
    summary="Search invoices in session",
    description="""
    Search for invoices in a previously uploaded Excel file.

    Search types:
    - codigo_operacion: Search by operation code (partial match)
    - rfc: Search by RFC receptor (exact match)
    - fecha: Search by date range
    """
)
async def search_invoices(
    request: InvoiceSearchRequest,
    search_service: InvoiceSearchService = Depends(get_invoice_search_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for invoices based on provided criteria.

    Args:
        request: Search criteria
        search_service: Invoice search service
        current_user: Authenticated user

    Returns:
        InvoiceSearchResponse with matching results

    Raises:
        HTTPException: If session not found or search fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(
        f"User {user_email} searching in session {request.session_id} "
        f"by {request.search_type.value}"
    )

    try:
        results = search_service.search(request)
        return results

    except ValueError as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar facturas: {str(e)}"
        )


@router.get(
    "/session/{session_id}/stats",
    summary="Get session statistics",
    description="Get statistics about a session including record count and totals."
)
async def get_session_stats(
    session_id: str,
    search_service: InvoiceSearchService = Depends(get_invoice_search_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a session.

    Args:
        session_id: Session ID from Excel upload
        search_service: Invoice search service
        current_user: Authenticated user

    Returns:
        Dictionary with session statistics

    Raises:
        HTTPException: If session not found
    """
    data = search_service.get_session_data(session_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión no encontrada o expirada: {session_id}"
        )

    # Calculate statistics
    total_amount = sum(record.total for record in data)
    total_subtotal = sum(record.subtotal for record in data)
    total_iva = sum(record.iva_trasladado for record in data)

    # Get unique values
    unique_rfcs = set(record.rfc_receptor for record in data)
    unique_operaciones = set(record.codigo_operacion for record in data)

    return {
        "session_id": session_id,
        "total_records": len(data),
        "total_amount": round(total_amount, 2),
        "total_subtotal": round(total_subtotal, 2),
        "total_iva": round(total_iva, 2),
        "unique_rfcs": len(unique_rfcs),
        "unique_operaciones": len(unique_operaciones)
    }


@router.delete(
    "/session/{session_id}",
    summary="Clear session data",
    description="Remove session data from cache to free memory."
)
async def clear_session(
    session_id: str,
    search_service: InvoiceSearchService = Depends(get_invoice_search_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Clear session data from cache.

    Args:
        session_id: Session ID to clear
        search_service: Invoice search service
        current_user: Authenticated user

    Returns:
        Success message
    """
    success = search_service.clear_session(session_id)
    if success:
        return {"message": f"Sesión {session_id} eliminada exitosamente"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión no encontrada: {session_id}"
        )


@router.post(
    "/generate-zip",
    summary="Generate ZIP package with invoices",
    description="""
    Generate a ZIP file containing PDFs, XMLs, and detailed Excel report.

    You can specify:
    - Specific UUIDs to include
    - Search criteria to filter invoices
    - Metadata for naming the ZIP file

    The ZIP will contain:
    - Detailed Excel report with all invoice data
    - PDFs/ folder with PDF files
    - XMLs/ folder with XML files

    Files not found in Google Drive will be marked as missing in the Excel report.
    """
)
async def generate_zip(
    request: ZipGenerationRequest,
    search_service: InvoiceSearchService = Depends(get_invoice_search_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a ZIP package with invoice PDFs, XMLs, and Excel report.

    Args:
        request: ZIP generation request with UUIDs or search criteria
        search_service: Invoice search service
        current_user: Authenticated user

    Returns:
        StreamingResponse: ZIP file download

    Raises:
        HTTPException: If session not found, no invoices to include, or generation fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(
        f"User {user_email} requesting ZIP generation for session {request.session_id}"
    )

    try:
        # Get session data
        session_data = search_service.get_session_data(request.session_id)
        if session_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Sesión no encontrada o expirada: {request.session_id}"
            )

        # Determine which invoices to include
        invoices_to_include = []

        if request.uuids:
            # Filter by specific UUIDs
            uuid_set = set(request.uuids)
            filtered_invoices = [
                invoice for invoice in session_data
                if invoice.uuid in uuid_set
            ]
            # Convert Pydantic models to dicts
            invoices_to_include = [
                {
                    "uuid": invoice.uuid,
                    "codigo_operacion": invoice.codigo_operacion,
                    "conceptos": invoice.conceptos,
                    "fecha_emision": invoice.fecha_emision,
                    "rfc_receptor": invoice.rfc_receptor,
                    "razon_receptor": invoice.razon_receptor,
                    "subtotal": invoice.subtotal,
                    "iva_trasladado": invoice.iva_trasladado,
                    "iva_exento": invoice.iva_exento,
                    "total": invoice.total,
                    "clasificacion_gasto": invoice.clasificacion_gasto.value if invoice.clasificacion_gasto else None
                }
                for invoice in filtered_invoices
            ]
            logger.info(f"Filtering by {len(request.uuids)} UUIDs, found {len(invoices_to_include)} invoices")

        elif request.search_criteria:
            # Filter by search criteria
            search_results = search_service.search(request.search_criteria)
            # Convert InvoiceSearchResult to dict
            invoices_to_include = [
                {
                    "uuid": r.uuid,
                    "codigo_operacion": r.codigo_operacion,
                    "conceptos": r.conceptos,
                    "fecha_emision": r.fecha_emision,
                    "rfc_receptor": r.rfc_receptor,
                    "razon_receptor": r.razon_receptor,
                    "subtotal": r.subtotal,
                    "iva_trasladado": r.iva_trasladado,
                    "iva_exento": r.iva_exento,
                    "total": r.total,
                    "clasificacion_gasto": r.clasificacion_gasto.value if r.clasificacion_gasto else None
                }
                for r in search_results.results
            ]
            logger.info(f"Search criteria returned {len(invoices_to_include)} invoices")

        else:
            # Include all session data
            invoices_to_include = [
                {
                    "uuid": invoice.uuid,
                    "codigo_operacion": invoice.codigo_operacion,
                    "conceptos": invoice.conceptos,
                    "fecha_emision": invoice.fecha_emision,
                    "rfc_receptor": invoice.rfc_receptor,
                    "razon_receptor": invoice.razon_receptor,
                    "subtotal": invoice.subtotal,
                    "iva_trasladado": invoice.iva_trasladado,
                    "iva_exento": invoice.iva_exento,
                    "total": invoice.total,
                    "clasificacion_gasto": invoice.clasificacion_gasto.value if invoice.clasificacion_gasto else None
                }
                for invoice in session_data
            ]
            logger.info(f"Including all {len(invoices_to_include)} invoices from session")

        if not invoices_to_include:
            raise HTTPException(
                status_code=400,
                detail="No se encontraron facturas para incluir en el ZIP"
            )

        # Generate ZIP
        zip_service = get_zip_service()
        zip_buffer = zip_service.generate_invoice_package(
            invoices_to_include,
            metadata=request.metadata
        )

        # Generate filename
        filename = zip_service.generate_zip_filename(metadata=request.metadata)

        logger.info(f"ZIP generation successful: {filename}, Size: {len(zip_buffer.getvalue())} bytes")

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Invoices": str(len(invoices_to_include))
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during ZIP generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating ZIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el paquete ZIP: {str(e)}"
        )
