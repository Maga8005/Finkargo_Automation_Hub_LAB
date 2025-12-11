"""
Finance Routes for Facturación MX automation.

This module contains all API endpoints for the Mexico invoicing
automation feature including Excel upload, search, and ZIP generation.
"""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict
import io

from src.interface.finance_dtos import (
    ExcelValidationResponse,
    InvoiceSearchRequest,
    InvoiceSearchResponse,
    ZipGenerationRequest,
    CombinedUploadResponse,
    CombinedSearchRequest,
    CombinedSearchResponse,
    CombinedSearchResult,
    DocumentType,
    ArchivoEstado
)
from src.interface.finance_dtos_co import (
    COProcessingResponse,
    COProcessingStats,
    COReportSheet,
    FileType,
    SheetDestination,
    COSTOS_FIJOS_COLUMNS,
    MANDATO_COLUMNS,
    COFilterRequest,
    COFilterResponse,
    CODistinctValuesResponse,
)
from src.core.servicios.excel_validation_service import ExcelValidationService
from src.core.servicios.invoice_search_service import (
    InvoiceSearchService,
    get_invoice_search_service
)
from src.core.servicios.zip_generator_service import get_zip_service
from src.core.servicios.google_drive_service import get_drive_service
from src.core.servicios.excel_merge_service import get_excel_merge_service
from src.core.servicios.file_processor_co import get_co_file_processor
from src.core.servicios.google_drive_service_co import (
    get_drive_service_co,
    ExcelValidationError as DriveExcelValidationError
)
from src.core.servicios.excel_merge_service_co import (
    get_excel_merge_service_co,
    MergeValidationError
)
from src.core.servicios.filter_service_co import get_filter_service_co
from src.core.servicios.zip_generator_service_co import get_zip_service_co
from src.core.servicios.filter_service_mx import get_filter_service_mx
from src.core.servicios.combined_excel_service import get_combined_excel_service
from src.core.servicios.combined_search_service import get_combined_search_service
from src.core.servicios.excel_merge_service_mx import get_excel_merge_service_mx
from src.interface.finance_dtos_mx import (
    MXFilterRequest,
    MXFilterResponse,
    MXDistinctValuesResponse,
)
from src.adapter.rest.dependencies import get_current_user
from src.interface.finance_history_dtos import (
    FinanceReportDetail,
    FinanceReportSummary,
    FinanceHistoryFilter,
    FinanceReportStats,
    FinanceHistoryResponse,
    ReportCountry,
    ReportType,
    ReportStatus
)
from src.repositorio.finance_report_repository import (
    FinanceReportRepository,
    get_finance_report_repository
)
from src.config.supabase_config import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/finance", tags=["Finance - Facturación MX"])

# Temporary session storage for CO reports (in-memory)
# In production, use Redis or persistent storage
_co_report_sessions: Dict[str, bytes] = {}


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
                    "uuid_relacionados": invoice.uuid_relacionados,
                    "tipo_comprobante": invoice.tipo_comprobante
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
                    "uuid_relacionados": r.uuid_relacionados,
                    "tipo_comprobante": r.tipo_comprobante
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
                    "uuid_relacionados": invoice.uuid_relacionados,
                    "tipo_comprobante": invoice.tipo_comprobante
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


# ============================================================================
# Colombia (CO) Endpoints
# ============================================================================

@router.post(
    "/co/process-files",
    response_model=COProcessingResponse,
    summary="Process Colombia Excel files (by pairs)",
    description="""
    Process Colombia invoicing files and generate consolidated report.

    You can upload files in pairs:
    - Pair 1: Netsuite Facturas + Noova Facturas
    - Pair 2: Netsuite NC + Noova NC

    At least ONE complete pair is required (both Netsuite and Noova from the same category).

    The endpoint will:
    1. Read and validate uploaded files
    2. Consolidate data with LEFT JOIN by numero_factura
    3. Classify by product code (146 codes) and keywords
    4. Separate into 2 sheets (Costos Fijos and Mandato)
    5. Generate Excel report

    Returns processing statistics and download URL.
    """,
    tags=["Finance - Facturación CO"]
)
async def process_co_files(
    netsuite: Optional[UploadFile] = File(None, description="Netsuite Facturas Excel file (optional)"),
    netsuite_nc: Optional[UploadFile] = File(None, description="Netsuite NC Excel file (optional)"),
    noova_facturas: Optional[UploadFile] = File(None, description="Noova Facturas Excel file (optional)"),
    noova_nc: Optional[UploadFile] = File(None, description="Noova NC Excel file (optional)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Process 4 Colombia Excel files and generate consolidated report.

    Args:
        netsuite: Netsuite facturas file
        netsuite_nc: Netsuite notas de crédito file
        noova_facturas: Noova facturas file
        noova_nc: Noova notas de crédito file
        current_user: Authenticated user

    Returns:
        COProcessingResponse with statistics and download URL

    Raises:
        HTTPException: If validation or processing fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    session_id = f"co_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    logger.info(f"User {user_email} processing CO files - Session {session_id}")

    try:
        # Validate that at least one complete pair is present
        facturas_pair_complete = netsuite and noova_facturas
        nc_pair_complete = netsuite_nc and noova_nc

        if not (facturas_pair_complete or nc_pair_complete):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Debe subir al menos una pareja completa de archivos:\n"
                    "- Pareja 1: Netsuite Facturas + Noova Facturas\n"
                    "- Pareja 2: Netsuite NC + Noova NC"
                )
            )

        # Validate uploaded files are Excel
        files_to_validate = [
            ("Netsuite Facturas", netsuite),
            ("Netsuite NC", netsuite_nc),
            ("Noova Facturas", noova_facturas),
            ("Noova NC", noova_nc)
        ]

        for file_label, file in files_to_validate:
            if file:  # Only validate if file was uploaded
                if not file.filename:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Nombre de archivo es requerido para {file_label}"
                    )
                if not file.filename.endswith(('.xlsx', '.xls')):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Formato inválido para {file_label}. Use .xlsx o .xls"
                    )

        # Initialize processor
        processor = get_co_file_processor()

        # Step 1: Read Netsuite files (if uploaded)
        logger.info("Leyendo archivos Netsuite...")
        netsuite_records = []
        netsuite_errors = []
        netsuite_nc_records = []
        netsuite_nc_errors = []

        if netsuite:
            netsuite_records, netsuite_errors = await processor.read_excel_file(
                netsuite, FileType.NETSUITE
            )
            logger.info(f"Netsuite Facturas: {len(netsuite_records)} registros")

        if netsuite_nc:
            netsuite_nc_records, netsuite_nc_errors = await processor.read_excel_file(
                netsuite_nc, FileType.NETSUITE_NC
            )
            logger.info(f"Netsuite NC: {len(netsuite_nc_records)} registros")

        all_netsuite = netsuite_records + netsuite_nc_records
        logger.info(f"Total Netsuite records: {len(all_netsuite)}")

        # Step 2: Read Noova files (if uploaded)
        logger.info("Leyendo archivos Noova...")
        noova_facturas_records = []
        noova_f_errors = []
        noova_nc_records = []
        noova_nc_errors = []

        if noova_facturas:
            noova_facturas_records, noova_f_errors = await processor.read_excel_file(
                noova_facturas, FileType.NOOVA_FACTURAS
            )
            logger.info(f"Noova Facturas: {len(noova_facturas_records)} registros")

        if noova_nc:
            noova_nc_records, noova_nc_errors = await processor.read_excel_file(
                noova_nc, FileType.NOOVA_NC
            )
            logger.info(f"Noova NC: {len(noova_nc_records)} registros")

        all_noova = noova_facturas_records + noova_nc_records
        logger.info(f"Total Noova records: {len(all_noova)}")

        # Collect all errors
        all_errors = (
            netsuite_errors + netsuite_nc_errors +
            noova_f_errors + noova_nc_errors
        )

        if len(all_errors) > 100:
            logger.warning(f"Demasiados errores de validación: {len(all_errors)}")
            raise HTTPException(
                status_code=400,
                detail=f"Demasiados errores de validación: {len(all_errors)}. "
                       f"Revise la estructura de los archivos."
            )

        # Step 3: Consolidate data (LEFT JOIN by numero_factura)
        logger.info("Consolidando datos (LEFT JOIN)...")
        consolidated = processor.consolidate_data(all_noova, all_netsuite)

        # Step 4: Classify records
        logger.info("Clasificando registros por código de producto...")
        classified = processor.classify_records(consolidated)

        # Step 5: Separate by destination sheet
        logger.info("Separando por hoja de destino...")
        costos_fijos, mandato = processor.separate_by_sheet(classified)

        # Step 6: Merge with existing Drive master and upload
        logger.info("Iniciando sincronización con Google Drive...")
        drive_uploaded = False
        drive_folder_id = None
        merge_stats = None

        try:
            drive_service_co = get_drive_service_co()
            merge_service_co = get_excel_merge_service_co()
            drive_folder_id = drive_service_co.folder_id

            # Convert records to dicts for merging
            new_costos_dicts = merge_service_co.convert_records_to_dicts(costos_fijos, "costos_fijos")
            new_mandato_dicts = merge_service_co.convert_records_to_dicts(mandato, "mandato")

            logger.info(f"Nuevos registros: {len(new_costos_dicts)} Costos Fijos, {len(new_mandato_dicts)} Mandato")

            # Download existing master from Drive
            master_bytes = drive_service_co.download_master_excel()

            if master_bytes:
                # Master exists - merge with new data
                logger.info("Master Excel encontrado - realizando merge...")
                existing_data = merge_service_co.read_excel_from_bytes(master_bytes)
                merged_data, merge_stats = merge_service_co.merge_excel_data(
                    existing_data,
                    new_costos_dicts,
                    new_mandato_dicts
                )
                logger.info(f"Merge completado: {merge_stats}")
            else:
                # No master - new data becomes the master
                logger.info("No existe master Excel - creando nuevo...")
                merged_data = {
                    merge_service_co.costos_fijos_sheet: new_costos_dicts,
                    merge_service_co.mandato_sheet: new_mandato_dicts
                }
                merge_stats = {
                    merge_service_co.costos_fijos_sheet: {"added": len(new_costos_dicts), "updated": 0},
                    merge_service_co.mandato_sheet: {"added": len(new_mandato_dicts), "updated": 0}
                }

            # Write merged Excel (with validation to prevent empty files)
            excel_bytes = merge_service_co.write_merged_excel(
                merged_data,
                existing_data=existing_data,
                validate=True
            )

            # Upload to Drive (with validation and automatic backup)
            upload_success = drive_service_co.upload_master_excel(
                excel_bytes,
                validate=True,
                create_backup=True,
                min_rows_per_sheet=0  # Allow adding first records
            )
            if upload_success:
                drive_uploaded = True
                logger.info("Master Excel CO actualizado en Google Drive (con backup)")
            else:
                logger.warning("No se pudo subir el master Excel a Drive")

        except MergeValidationError as merge_error:
            logger.error(f"Error de validación en merge: {merge_error}")
            # Fallback: generate report without merge (don't upload invalid data)
            logger.info("Generando reporte sin merge debido a error de validación...")
            excel_bytes = processor.generate_excel_report(costos_fijos, mandato)

        except DriveExcelValidationError as validation_error:
            logger.error(f"Error de validación al subir a Drive: {validation_error}")
            # The Excel failed validation - don't upload, use local report
            logger.info("Reporte generado localmente (no se subió a Drive por validación fallida)")
            excel_bytes = processor.generate_excel_report(costos_fijos, mandato)

        except Exception as drive_error:
            logger.error(f"Error en sincronización con Drive: {drive_error}", exc_info=True)
            # Fallback: generate report without merge
            logger.info("Generando reporte sin merge (fallback)...")
            excel_bytes = processor.generate_excel_report(costos_fijos, mandato)

        # Store in session for download
        _co_report_sessions[session_id] = excel_bytes
        logger.info(f"Reporte almacenado en sesión {session_id}")

        # Calculate statistics
        matched_count = sum(1 for r in consolidated if r.valor_netsuite is not None)
        stats = COProcessingStats(
            total_records_noova=len(all_noova),
            total_records_netsuite=len(all_netsuite),
            total_consolidated=len(consolidated),
            matched_with_netsuite=matched_count,
            unmatched_noova=len(consolidated) - matched_count,
            costos_fijos_count=len(costos_fijos),
            mandato_count=len(mandato),
            errors=[f"{e.file_type}: {e.message}" for e in all_errors[:10]]  # First 10 errors
        )

        # Sheet information
        sheets = [
            COReportSheet(
                sheet_name=SheetDestination.COSTOS_FIJOS,
                column_count=len(COSTOS_FIJOS_COLUMNS),
                row_count=len(costos_fijos),
                columns=COSTOS_FIJOS_COLUMNS
            ),
            COReportSheet(
                sheet_name=SheetDestination.MANDATO,
                column_count=len(MANDATO_COLUMNS),
                row_count=len(mandato),
                columns=MANDATO_COLUMNS
            )
        ]

        # Build message based on Drive upload status
        if drive_uploaded:
            message = "Procesamiento completado y reporte subido a Google Drive"
        else:
            message = "Procesamiento completado (reporte no subido a Drive)"

        response = COProcessingResponse(
            success=True,
            session_id=session_id,
            stats=stats,
            sheets=sheets,
            download_url=f"/api/finance/co/download/{session_id}",
            drive_uploaded=drive_uploaded,
            drive_url=f"https://drive.google.com/drive/folders/{drive_folder_id}" if drive_uploaded and drive_folder_id else None,
            message=message
        )

        logger.info(f"Procesamiento CO completado: {stats.total_consolidated} registros")
        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error de validación en procesamiento CO: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en procesamiento CO: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar archivos CO: {str(e)}"
        )


@router.get(
    "/co/download/{session_id}",
    summary="Download CO processed report",
    description="Download the generated Excel report from a CO processing session.",
    tags=["Finance - Facturación CO"]
)
async def download_co_report(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download generated CO report Excel file.

    Args:
        session_id: Session ID from processing request
        current_user: Authenticated user

    Returns:
        StreamingResponse: Excel file download

    Raises:
        HTTPException: If session not found or download fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} downloading CO report: {session_id}")

    # Check if session exists
    if session_id not in _co_report_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión no encontrada o expirada: {session_id}"
        )

    try:
        excel_bytes = _co_report_sessions[session_id]

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Reporte_Facturacion_CO_{timestamp}.xlsx"

        logger.info(f"Enviando reporte CO: {filename}, {len(excel_bytes)} bytes")

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Session-ID": session_id
            }
        )

    except Exception as e:
        logger.error(f"Error descargando reporte CO: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al descargar reporte: {str(e)}"
        )


@router.delete(
    "/co/session/{session_id}",
    summary="Clear CO session data",
    description="Remove CO session data from cache to free memory.",
    tags=["Finance - Facturación CO"]
)
async def clear_co_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Clear CO session data from cache.

    Args:
        session_id: Session ID to clear
        current_user: Authenticated user

    Returns:
        Success message
    """
    if session_id in _co_report_sessions:
        del _co_report_sessions[session_id]
        return {"message": f"Sesión CO {session_id} eliminada exitosamente"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión no encontrada: {session_id}"
        )


# ============================================================================
# Colombia (CO) Filter Endpoints
# ============================================================================

@router.post(
    "/co/filter",
    response_model=COFilterResponse,
    summary="Filter CO master Excel data",
    description="""
    Query the CO master Excel file (Reporte_Facturacion_CO_2025.xlsx) from Google Drive
    with filters.

    **Supported filter combinations:**
    - Operación(es) + rango de fecha
    - NIT + rango de fecha
    - NIT + operaciones + rango de fecha (combinación completa)

    **Filter parameters:**
    - `operaciones`: List of operation codes (codigo_operacion)
    - `nit`: Client tax ID (supports partial match)
    - `fecha_inicio`: Start date (YYYY-MM-DD format)
    - `fecha_fin`: End date (YYYY-MM-DD format)
    - `hoja`: Sheet to search ('costos_fijos', 'mandato', or both if not specified)

    Returns matching records from the master Excel.
    """,
    tags=["Finance - Facturación CO - Filtros"]
)
async def filter_co_records(
    request: COFilterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Filter records from CO master Excel.

    Args:
        request: Filter criteria (operaciones, nit, fecha_inicio, fecha_fin)
        current_user: Authenticated user

    Returns:
        COFilterResponse with matching records

    Raises:
        HTTPException: If Excel not found or query fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} filtering CO data: {request}")

    try:
        filter_service = get_filter_service_co()
        response = filter_service.filter_records(request)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )

        logger.info(f"Filter CO returned {response.total_records} records")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering CO data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar datos: {str(e)}"
        )


@router.get(
    "/co/distinct/{field}",
    response_model=CODistinctValuesResponse,
    summary="Get distinct values for a field",
    description="""
    Get unique values for a specific field from the CO master Excel.
    Useful for populating filter dropdowns and autocomplete.

    **Supported fields:**
    - `nit`: Client tax IDs
    - `operacion` or `codigo_operacion`: Operation codes

    Returns up to 100 unique values by default.
    """,
    tags=["Finance - Facturación CO - Filtros"]
)
async def get_co_distinct_values(
    field: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get distinct values for autocomplete.

    Args:
        field: Field name ('nit', 'operacion')
        limit: Maximum values to return (default 100)
        current_user: Authenticated user

    Returns:
        CODistinctValuesResponse with unique values

    Raises:
        HTTPException: If field not supported or query fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} getting distinct values for: {field}")

    try:
        filter_service = get_filter_service_co()
        response = filter_service.get_distinct_values(field, limit)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=f"Campo no soportado: {field}"
            )

        logger.info(f"Found {response.count} distinct values for {field}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting distinct values: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener valores: {str(e)}"
        )


@router.post(
    "/co/filter/download",
    summary="Download filtered CO data as Excel",
    description="""
    Apply filters and download the matching records as an Excel file.
    Same filters as /co/filter endpoint.
    """,
    tags=["Finance - Facturación CO - Filtros"]
)
async def download_filtered_co_data(
    request: COFilterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Download filtered records as Excel file.

    Args:
        request: Filter criteria
        current_user: Authenticated user

    Returns:
        StreamingResponse: Excel file with filtered data

    Raises:
        HTTPException: If no records found or download fails
    """
    import pandas as pd
    from io import BytesIO

    user_email = getattr(current_user, 'email', 'unknown')
    user_id = getattr(current_user, 'id', None)
    logger.info(f"User {user_email} downloading filtered CO data")

    try:
        filter_service = get_filter_service_co()
        response = filter_service.filter_records(request)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )

        if response.total_records == 0:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron registros con los filtros especificados"
            )

        # Convert records to DataFrame with reorganized columns
        records_data = []
        for record in response.records:
            # Determine tipo de factura based on hoja_origen
            tipo_factura = "Costos Fijos" if record.hoja_origen and "Costos" in record.hoja_origen else "Mandato"

            records_data.append({
                "Tipo de Factura": tipo_factura,
                "Codigo del Desembolso": record.codigo_operacion,
                "Fecha Factura": record.fecha,
                "# Factura": record.numero_factura,
                "Moneda": record.moneda,
                "Valor Costos Fijos": record.valor_costos_fijos,
                "Seguro + IVA": record.seguro_iva,
                "Int. Corriente": record.int_corriente,
                "Int. Mora": record.int_mora,
                "(-) Retención en la Fuente": record.retencion_fuente,
                "Valor Neto Facturado": record.valor_neto,
                "Otros Valor": record.otros_valor,
                "NIT": record.nit,
            })

        df = pd.DataFrame(records_data)

        # Generate Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Datos Filtrados', index=False)

        excel_buffer.seek(0)
        excel_bytes = excel_buffer.read()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Reporte_Filtrado_CO_{timestamp}.xlsx"

        logger.info(f"Descarga filtrada: {filename}, {len(excel_bytes)} bytes, {response.total_records} registros")

        # Record in history
        await record_finance_report(
            country="CO",
            report_type="consulta",
            stats={
                "total_records": response.total_records,
                "sheets_searched": response.sheets_searched,
            },
            user_id=user_id,
            user_email=user_email,
            filters_applied={
                "nit": request.nit,
                "operaciones": request.operaciones,
                "fecha_inicio": request.fecha_inicio,
                "fecha_fin": request.fecha_fin,
                "hoja": request.hoja,
            },
            file_name=filename,
            status="completed"
        )

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(response.total_records)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading filtered data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar descarga: {str(e)}"
        )


@router.get(
    "/co/operations-by-nit/{nit}",
    response_model=CODistinctValuesResponse,
    summary="Get operations for a specific NIT",
    description="""
    Get distinct operation codes associated with a specific NIT (client tax ID).
    Useful for populating the operations dropdown after the user selects a NIT.

    **Parameters:**
    - `nit`: Client tax ID to filter by
    - `limit`: Maximum number of operations to return (default 100)

    Returns operation codes found in both Costos Fijos and Mandato sheets
    that are associated with the given NIT.
    """,
    tags=["Finance - Facturación CO - Filtros"]
)
async def get_co_operations_by_nit(
    nit: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get distinct operation codes for a specific NIT.

    Args:
        nit: Client NIT to filter by
        limit: Maximum values to return (default 100)
        current_user: Authenticated user

    Returns:
        CODistinctValuesResponse with unique operation codes for the NIT

    Raises:
        HTTPException: If query fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} getting operations for NIT: {nit}")

    try:
        filter_service = get_filter_service_co()
        response = filter_service.get_operations_by_nit(nit, limit)

        logger.info(f"Found {response.count} operations for NIT {nit}")
        return response

    except Exception as e:
        logger.error(f"Error getting operations by NIT: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener operaciones: {str(e)}"
        )


@router.delete(
    "/co/filter/cache",
    summary="Clear filter cache",
    description="Clear the cached Excel data to force a fresh download from Drive.",
    tags=["Finance - Facturación CO - Filtros"]
)
async def clear_co_filter_cache(
    current_user: dict = Depends(get_current_user)
):
    """
    Clear the filter service cache.

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    filter_service = get_filter_service_co()
    filter_service.clear_cache()
    return {"message": "Cache de filtros CO limpiado exitosamente"}


@router.post(
    "/co/filter/download-zip",
    summary="Download filtered CO data with PDFs as ZIP",
    description="""
    Apply filters and download the matching records along with their PDF files as a ZIP package.

    The ZIP will contain:
    - Excel report with filtered data
    - PDFs/ folder with invoice PDF files found in Google Drive
    - PDFs_no_encontrados.txt listing any PDFs not found

    Same filters as /co/filter endpoint.
    """,
    tags=["Finance - Facturación CO - Filtros"]
)
async def download_filtered_co_zip(
    request: COFilterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Download filtered records with PDFs as ZIP package.

    Args:
        request: Filter criteria
        current_user: Authenticated user

    Returns:
        StreamingResponse: ZIP file with Excel report and PDFs

    Raises:
        HTTPException: If no records found or download fails
    """
    import pandas as pd
    from io import BytesIO

    user_email = getattr(current_user, 'email', 'unknown')
    user_id = getattr(current_user, 'id', None)
    logger.info(f"User {user_email} downloading filtered CO ZIP with PDFs")

    try:
        # 1. Get filtered records
        filter_service = get_filter_service_co()
        response = filter_service.filter_records(request)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )

        if response.total_records == 0:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron registros con los filtros especificados"
            )

        # 2. Generate Excel content
        records_data = []
        records_for_pdf = []

        for record in response.records:
            # Determine tipo de factura based on hoja_origen
            tipo_factura = "Costos Fijos" if record.hoja_origen and "Costos" in record.hoja_origen else "Mandato"

            records_data.append({
                "Tipo de Factura": tipo_factura,
                "Codigo del Desembolso": record.codigo_operacion,
                "Fecha Factura": record.fecha,
                "# Factura": record.numero_factura,
                "Moneda": record.moneda,
                "Valor Costos Fijos": record.valor_costos_fijos,
                "Seguro + IVA": record.seguro_iva,
                "Int. Corriente": record.int_corriente,
                "Int. Mora": record.int_mora,
                "(-) Retención en la Fuente": record.retencion_fuente,
                "Valor Neto Facturado": record.valor_neto,
                "Otros Valor": record.otros_valor,
                "NIT": record.nit,
            })

            # Prepare for PDF search
            if record.numero_factura and record.fecha:
                records_for_pdf.append({
                    "numero_factura": record.numero_factura,
                    "fecha": record.fecha
                })

        df = pd.DataFrame(records_data)

        # Generate Excel bytes
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Datos Filtrados', index=False)
        excel_buffer.seek(0)
        excel_content = excel_buffer.read()

        # 3. Generate ZIP with PDFs
        zip_service = get_zip_service_co()

        # Build metadata for naming
        metadata = {}
        if request.nit:
            metadata["nit"] = request.nit
        if request.operaciones:
            metadata["operaciones"] = request.operaciones

        zip_buffer = zip_service.generate_invoice_package(
            records=records_for_pdf,
            excel_content=excel_content,
            metadata=metadata
        )

        # 4. Generate filename and return
        zip_filename = zip_service.generate_zip_filename(metadata)

        logger.info(
            f"ZIP CO generado: {zip_filename}, "
            f"{response.total_records} registros, "
            f"{len(zip_buffer.getvalue())} bytes"
        )

        # Record in history
        await record_finance_report(
            country="CO",
            report_type="zip_download",
            stats={
                "total_records": response.total_records,
                "sheets_searched": response.sheets_searched,
                "pdfs_included": len(records_for_pdf),
            },
            user_id=user_id,
            user_email=user_email,
            filters_applied={
                "nit": request.nit,
                "operaciones": request.operaciones,
                "fecha_inicio": request.fecha_inicio,
                "fecha_fin": request.fecha_fin,
                "hoja": request.hoja,
            },
            file_name=zip_filename,
            status="completed"
        )

        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "X-Total-Records": str(response.total_records)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating ZIP CO: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar paquete ZIP: {str(e)}"
        )


@router.post(
    "/co/precache-drive-files",
    summary="Pre-populate Drive file cache for Colombia",
    description="""
    Pre-populates the Supabase cache with Google Drive file IDs for all CO invoices.

    This dramatically speeds up ZIP downloads because:
    1. Lists ALL PDF files from Drive in ONE API call
    2. Matches invoice numbers in memory (instant)
    3. Stores file IDs in Supabase cache

    After running this, ZIP downloads use cached file IDs instead of
    searching Drive for each file individually.

    Recommended to run periodically (e.g., daily) or after uploading new files.
    """,
    tags=["Finance - Facturación CO - Cache"]
)
async def precache_drive_files_co(
    current_user: dict = Depends(get_current_user)
):
    """
    Pre-cache Drive file IDs for CO invoices.

    Workflow:
    1. Gets all invoice numbers from the CO master Excel in Drive
    2. Lists ALL PDF files from Drive (one API call)
    3. Matches invoice numbers to files in memory
    4. Stores file IDs in Supabase cache

    Returns:
        Dict with statistics: total, cached, not_found, already_cached
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} starting CO Drive file precache")

    try:
        # 1. Get all invoice numbers from CO filter service (reads master Excel from Drive)
        filter_service = get_filter_service_co()
        all_invoice_numbers = filter_service.get_all_invoice_numbers()

        if not all_invoice_numbers:
            return {
                "success": False,
                "message": "No se encontraron números de factura en el Excel maestro CO",
                "stats": {"total": 0, "cached": 0, "not_found": 0, "already_cached": 0}
            }

        logger.info(f"[CO] Found {len(all_invoice_numbers)} invoice numbers to precache")

        # 2. Run precache
        drive_service = get_drive_service_co()
        stats = drive_service.precache_drive_file_ids(all_invoice_numbers)

        logger.info(f"[CO] Precache completed: {stats}")

        return {
            "success": True,
            "message": f"Cache pre-populated for {stats['cached']} files",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error during CO precache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al pre-cachear archivos CO: {str(e)}"
        )


@router.get(
    "/co/cache-stats",
    summary="Get CO Drive cache statistics",
    description="Returns statistics about the Drive file cache for Colombia invoices.",
    tags=["Finance - Facturación CO - Cache"]
)
async def get_co_cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get cache statistics for CO Drive files.

    Returns:
        Dict with cache statistics including total_cached, pdf_count, and cache_ready flag.
    """
    try:
        from src.repositorio.drive_file_cache_repository import get_drive_file_cache_repository
        from src.config.supabase_config import get_supabase_client

        supabase = get_supabase_client()
        # Use admin_client to bypass RLS
        cache_repo = get_drive_file_cache_repository(supabase.admin_client)
        stats = cache_repo.get_cache_stats(country="CO")

        # Cache is ready if we have at least some files cached
        cache_ready = stats.get('total_cached', 0) > 0

        return {
            "success": True,
            "total_cached": stats.get('total_cached', 0),
            "pdf_count": stats.get('pdf_count', 0),
            "xml_count": stats.get('xml_count', 0),
            "cache_ready": cache_ready,
            "country": "CO"
        }

    except Exception as e:
        logger.error(f"Error getting CO cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas del cache: {str(e)}"
        )


@router.post(
    "/co/initialize-from-historical",
    summary="Initialize cache from historical file",
    description="""
    ONE-TIME initialization endpoint that reads the historical invoice control file
    ("Archivo control facturacion mensual Finkargo Def.xlsx") to:

    1. Extract ALL invoice numbers from the historical record (3 sheets)
    2. Pre-populate the Supabase cache with Drive file IDs

    This allows the team to use the system immediately without having to
    upload Noova/Netsuite files first.

    NOTE: This does NOT modify the historical file - it's read-only.
    The master report (Reporte_Facturacion_CO_2025.xlsx) continues to be
    updated separately through the normal upload flow.

    Recommended to run ONCE when setting up the system.
    """,
    tags=["Finance - Facturación CO - Cache"]
)
async def initialize_co_from_historical(
    current_user: dict = Depends(get_current_user)
):
    """
    Initialize CO cache from historical invoice control file.

    Workflow:
    1. Downloads "Archivo control facturacion mensual Finkargo Def.xlsx" from Drive
    2. Extracts invoice numbers from all sheets (Costos Fijos, Mandato, Cesion)
    3. Lists ALL PDF files from Drive
    4. Matches invoice numbers to files in memory
    5. Stores file IDs in Supabase cache

    Returns:
        Dict with statistics and status
    """
    from src.core.servicios.historical_data_service_co import get_historical_data_service_co

    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} starting CO initialization from historical file")

    try:
        # 1. Get all invoice numbers from historical file
        historical_service = get_historical_data_service_co()
        logger.info("[CO Init] Reading historical file from Drive...")

        all_invoice_numbers = historical_service.get_all_invoice_numbers()

        if not all_invoice_numbers:
            return {
                "success": False,
                "message": "No se encontraron números de factura en el archivo histórico",
                "stats": {
                    "historical_invoices": 0,
                    "cached": 0,
                    "not_found": 0,
                    "already_cached": 0
                }
            }

        logger.info(f"[CO Init] Found {len(all_invoice_numbers)} invoice numbers in historical file")

        # 2. Run precache with the historical invoice numbers
        drive_service = get_drive_service_co()
        cache_stats = drive_service.precache_drive_file_ids(all_invoice_numbers)

        logger.info(f"[CO Init] Precache completed: {cache_stats}")

        return {
            "success": True,
            "message": (
                f"Inicialización completada. "
                f"{len(all_invoice_numbers)} facturas del histórico, "
                f"{cache_stats['cached']} archivos cacheados, "
                f"{cache_stats['already_cached']} ya en cache, "
                f"{cache_stats['not_found']} no encontrados en Drive."
            ),
            "stats": {
                "historical_invoices": len(all_invoice_numbers),
                **cache_stats
            }
        }

    except ValueError as e:
        logger.error(f"Validation error during CO initialization: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during CO initialization from historical: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al inicializar desde archivo histórico: {str(e)}"
        )


# ============================================================================
# FINANCE REPORT HISTORY ENDPOINTS
# ============================================================================

def get_report_repository() -> FinanceReportRepository:
    """Dependency to get finance report repository."""
    supabase = get_supabase_client()
    # Use admin_client to access the actual Supabase Client with .table() and .rpc() methods
    return get_finance_report_repository(supabase.admin_client)


@router.get(
    "/history",
    response_model=FinanceHistoryResponse,
    summary="Get finance report history",
    description="Get paginated list of finance report generations with optional filters"
)
async def get_finance_history(
    country: Optional[str] = None,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get finance report history with optional filters.

    Query Parameters:
    - country: Filter by country (CO or MX)
    - report_type: Filter by type (facturacion, consulta, zip_download)
    - status: Filter by status (completed, failed, processing)
    - date_from: Start date filter
    - date_to: End date filter
    - limit: Max records to return (default 50, max 100)
    - offset: Records to skip for pagination
    """
    try:
        repo = get_report_repository()

        # Build filter object
        filters = FinanceHistoryFilter(
            country=ReportCountry(country) if country else None,
            report_type=ReportType(report_type) if report_type else None,
            status=ReportStatus(status) if status else None,
            date_from=date_from,
            date_to=date_to,
            limit=min(limit, 100),
            offset=offset
        )

        reports, total = await repo.get_history(filters)

        # Transform to summary format
        summaries = []
        for report in reports:
            # Create human-readable stats summary
            stats = report.get('stats', {})
            report_type = report.get('report_type', '')

            # Try different field names based on report type
            if report_type in ('consulta', 'zip_download'):
                # Filter/query reports use total_records
                total = stats.get('total_records', 0)
                stats_summary = f"{total} registros"
            elif report.get('country') == 'CO':
                # CO facturacion reports
                total = stats.get('total_consolidated', stats.get('total_records', 0))
                stats_summary = f"{total} registros"
            else:
                # MX facturacion reports
                total = stats.get('total_invoices', stats.get('total_records', 0))
                stats_summary = f"{total} facturas"

            summaries.append(FinanceReportSummary(
                id=report['id'],
                report_id=report['report_id'],
                country=ReportCountry(report['country']),
                report_type=ReportType(report['report_type']),
                status=ReportStatus(report['status']),
                generated_by_email=report.get('generated_by_email'),
                generated_at=report['generated_at'],
                stats_summary=stats_summary,
                drive_uploaded=report.get('drive_uploaded', False)
            ))

        page = (offset // limit) + 1 if limit > 0 else 1
        has_more = offset + limit < total

        return FinanceHistoryResponse(
            success=True,
            total=total,
            reports=summaries,
            page=page,
            page_size=limit,
            has_more=has_more
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting finance history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )


@router.get(
    "/history/stats",
    response_model=FinanceReportStats,
    summary="Get finance report statistics",
    description="Get statistics about finance report generations"
)
async def get_finance_stats(
    country: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for finance reports.

    Query Parameters:
    - country: Optional filter by country (CO or MX)
    """
    try:
        repo = get_report_repository()
        stats = await repo.get_stats(country)
        return FinanceReportStats(**stats)

    except Exception as e:
        logger.error(f"Error getting finance stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get(
    "/history/export/csv",
    summary="Export finance history to CSV",
    description="Download finance report history as CSV file with optional filters"
)
async def export_finance_history_csv(
    country: Optional[str] = None,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Export finance report history to CSV.

    Query Parameters:
    - country: Filter by country (CO or MX)
    - report_type: Filter by type (facturacion, consulta, zip_download)
    - status: Filter by status (completed, failed, processing)
    - date_from: Start date filter
    - date_to: End date filter
    """
    import csv
    from io import StringIO

    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} exporting finance history to CSV")
    logger.info(f"CSV export raw params - country: '{country}', report_type: '{report_type}', status: '{status}'")

    try:
        repo = get_report_repository()

        # Normalize empty strings to None
        country_val = country.strip() if country else None
        report_type_val = report_type.strip() if report_type else None
        status_val = status.strip() if status else None

        logger.info(f"CSV export normalized - country_val: '{country_val}', report_type_val: '{report_type_val}', status_val: '{status_val}'")

        # Convert to enums with explicit error handling
        country_enum = None
        report_type_enum = None
        status_enum = None

        if country_val:
            try:
                country_enum = ReportCountry(country_val)
            except ValueError as e:
                logger.error(f"Invalid country value '{country_val}': {e}")
                raise ValueError(f"País inválido: '{country_val}'. Use 'CO' o 'MX'")

        if report_type_val:
            try:
                report_type_enum = ReportType(report_type_val)
            except ValueError as e:
                logger.error(f"Invalid report_type value '{report_type_val}': {e}")
                raise ValueError(f"Tipo inválido: '{report_type_val}'. Use 'facturacion', 'consulta' o 'zip_download'")

        if status_val:
            try:
                status_enum = ReportStatus(status_val)
            except ValueError as e:
                logger.error(f"Invalid status value '{status_val}': {e}")
                raise ValueError(f"Estado inválido: '{status_val}'. Use 'completed', 'failed' o 'processing'")

        # Build filter object - get all records (large limit)
        filters = FinanceHistoryFilter(
            country=country_enum,
            report_type=report_type_enum,
            status=status_enum,
            date_from=date_from,
            date_to=date_to,
            limit=10000,  # Large limit to get all records
            offset=0
        )

        logger.info(f"CSV export filters built successfully: {filters}")

        reports, total = await repo.get_history(filters)
        logger.info(f"CSV export got {len(reports)} reports, total: {total}")

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID Reporte',
            'País',
            'Tipo',
            'Estado',
            'Registros',
            'Usuario',
            'Archivo',
            'Drive',
            'Filtros Aplicados',
            'Fecha Generación',
            'Fecha Creación'
        ])

        # Write data rows
        for report in reports:
            stats = report.get('stats', {})
            row_report_type = report.get('report_type', '')

            # Get record count based on report type
            if row_report_type in ('consulta', 'zip_download'):
                record_count = stats.get('total_records', 0)
            elif report.get('country') == 'CO':
                record_count = stats.get('total_consolidated', stats.get('total_records', 0))
            else:
                record_count = stats.get('total_invoices', stats.get('total_records', 0))

            # Format filters applied
            filters_applied = report.get('filters_applied', {})
            filters_str = ''
            if filters_applied:
                filter_parts = []
                if filters_applied.get('nit'):
                    filter_parts.append(f"NIT: {filters_applied['nit']}")
                if filters_applied.get('rfc'):
                    filter_parts.append(f"RFC: {filters_applied['rfc']}")
                if filters_applied.get('operaciones'):
                    ops = filters_applied['operaciones']
                    if isinstance(ops, list):
                        filter_parts.append(f"Operaciones: {', '.join(ops)}")
                    else:
                        filter_parts.append(f"Operaciones: {ops}")
                if filters_applied.get('fecha_inicio'):
                    filter_parts.append(f"Desde: {filters_applied['fecha_inicio']}")
                if filters_applied.get('fecha_fin'):
                    filter_parts.append(f"Hasta: {filters_applied['fecha_fin']}")
                if filters_applied.get('hoja'):
                    filter_parts.append(f"Hoja: {filters_applied['hoja']}")
                filters_str = '; '.join(filter_parts)

            # Format report type for display
            type_labels = {
                'facturacion': 'Procesamiento',
                'consulta': 'Consulta',
                'zip_download': 'Descarga ZIP'
            }

            # Format status for display
            status_labels = {
                'processing': 'Procesando',
                'completed': 'Completado',
                'failed': 'Fallido',
                'downloaded': 'Descargado'
            }

            # Format country
            country_labels = {'CO': 'Colombia', 'MX': 'México'}

            writer.writerow([
                report.get('report_id', ''),
                country_labels.get(report.get('country', ''), report.get('country', '')),
                type_labels.get(report.get('report_type', ''), report.get('report_type', '')),
                status_labels.get(report.get('status', ''), report.get('status', '')),
                record_count,
                report.get('generated_by_email', ''),
                report.get('file_name', ''),
                'Sí' if report.get('drive_uploaded') else 'No',
                filters_str,
                report.get('generated_at', ''),
                report.get('created_at', '')
            ])

        # Get CSV content
        csv_content = output.getvalue()
        output.close()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        country_suffix = f"_{country_val}" if country_val else ""
        filename = f"Historial_Reportes{country_suffix}_{timestamp}.csv"

        logger.info(f"CSV exported: {filename}, {total} records")

        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8-sig')),  # utf-8-sig for Excel compatibility
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(total)
            }
        )

    except ValueError as e:
        logger.warning(f"Invalid filter value for CSV export: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Valor de filtro inválido: {str(e)}. Valores permitidos - país: CO, MX; tipo: facturacion, consulta, zip_download; estado: completed, failed, processing"
        )
    except Exception as e:
        logger.error(f"Error exporting finance history to CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al exportar historial: {str(e)}"
        )


@router.get(
    "/history/{report_id}",
    response_model=FinanceReportDetail,
    summary="Get finance report details",
    description="Get detailed information about a specific finance report"
)
async def get_finance_report_detail(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific finance report.

    Path Parameters:
    - report_id: Report UUID or business ID (FIN-CO-2025-0001)
    """
    try:
        repo = get_report_repository()

        # Try to get by UUID first, then by business ID
        report = await repo.get_by_id(report_id)
        if not report:
            report = await repo.get_by_report_id(report_id)

        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Reporte no encontrado: {report_id}"
            )

        return FinanceReportDetail(
            id=report['id'],
            report_id=report['report_id'],
            country=ReportCountry(report['country']),
            report_type=ReportType(report['report_type']),
            status=ReportStatus(report['status']),
            generated_by=report.get('generated_by'),
            generated_by_email=report.get('generated_by_email'),
            generated_at=report['generated_at'],
            stats=report.get('stats', {}),
            filters_applied=report.get('filters_applied'),
            file_name=report.get('file_name'),
            file_size_bytes=report.get('file_size_bytes'),
            drive_uploaded=report.get('drive_uploaded', False),
            drive_url=report.get('drive_url'),
            error_message=report.get('error_message'),
            created_at=report['created_at'],
            updated_at=report['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener detalle del reporte: {str(e)}"
        )


async def record_finance_report(
    country: str,
    report_type: str,
    stats: dict,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    filters_applied: Optional[dict] = None,
    file_name: Optional[str] = None,
    drive_uploaded: bool = False,
    drive_url: Optional[str] = None,
    session_id: Optional[str] = None,
    status: str = "completed",
    error_message: Optional[str] = None
) -> Optional[dict]:
    """
    Helper function to record a finance report in history.

    This should be called after processing reports to track them.

    Args:
        country: Country code (CO or MX)
        report_type: Type of report (facturacion, consulta, zip_download)
        stats: Report statistics dict
        user_id: User who generated the report
        user_email: Email of user who generated the report
        filters_applied: Filters used (for consulta reports)
        file_name: Generated file name
        drive_uploaded: Whether file was uploaded to Drive
        drive_url: URL to file in Drive
        session_id: Session ID for download
        status: Report status
        error_message: Error message if failed

    Returns:
        Created report record or None if failed
    """
    try:
        repo = get_report_repository()

        report_data = {
            "country": country,
            "report_type": report_type,
            "status": status,
            "generated_by": user_id,
            "generated_by_email": user_email,
            "stats": stats,
            "filters_applied": filters_applied,
            "file_name": file_name,
            "drive_uploaded": drive_uploaded,
            "drive_url": drive_url,
            "session_id": session_id,
            "error_message": error_message
        }

        return await repo.create(report_data)

    except Exception as e:
        logger.error(f"Error recording finance report: {e}")
        return None


# ============================================================================
# Mexico (MX) Filter Endpoints
# ============================================================================

@router.post(
    "/mx/filter",
    response_model=MXFilterResponse,
    summary="Filter MX master Excel data",
    description="""
    Query the MX master Excel file (Facturación MX 2025.xlsx) from Google Drive
    with filters.

    **Supported filter combinations:**
    - Código(s) de operación + rango de fecha
    - RFC + rango de fecha
    - RFC + operaciones + rango de fecha (combinación completa)

    **Filter parameters:**
    - `operaciones`: List of operation codes
    - `rfc`: RFC receptor (supports partial match)
    - `fecha_inicio`: Start date (YYYY-MM-DD format)
    - `fecha_fin`: End date (YYYY-MM-DD format)

    Returns matching records from the master Excel.
    """,
    tags=["Finance - Facturación MX - Filtros"]
)
async def filter_mx_records(
    request: MXFilterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Filter records from MX master Excel.

    Args:
        request: Filter criteria (operaciones, rfc, fecha_inicio, fecha_fin)
        current_user: Authenticated user

    Returns:
        MXFilterResponse with matching records

    Raises:
        HTTPException: If Excel not found or query fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} filtering MX data")
    logger.info(f"[MX_FILTER_ENDPOINT] Request recibido: operaciones={request.operaciones}, rfc={request.rfc}, fecha_inicio={request.fecha_inicio}, fecha_fin={request.fecha_fin}")

    try:
        filter_service = get_filter_service_mx()
        response = filter_service.filter_records(request)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )

        logger.info(f"Filter MX returned {response.total_records} records")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering MX data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar datos: {str(e)}"
        )


@router.get(
    "/mx/distinct/{field}",
    response_model=MXDistinctValuesResponse,
    summary="Get distinct values for a field (MX)",
    description="""
    Get unique values for a specific field from the MX master Excel.
    Useful for populating filter dropdowns and autocomplete.

    **Supported fields:**
    - `rfc`: RFC receptors
    - `operacion` or `codigo_operacion`: Operation codes

    Returns up to 100 unique values by default.
    """,
    tags=["Finance - Facturación MX - Filtros"]
)
async def get_mx_distinct_values(
    field: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get distinct values for autocomplete.

    Args:
        field: Field name ('rfc', 'operacion')
        limit: Maximum values to return (default 100)
        current_user: Authenticated user

    Returns:
        MXDistinctValuesResponse with unique values

    Raises:
        HTTPException: If field not supported or query fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} getting distinct values for MX: {field}")

    try:
        filter_service = get_filter_service_mx()
        response = filter_service.get_distinct_values(field, limit)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=f"Campo no soportado: {field}"
            )

        logger.info(f"Found {response.count} distinct values for {field} (MX)")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting distinct values MX: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener valores: {str(e)}"
        )


@router.get(
    "/mx/operations-by-rfc/{rfc}",
    response_model=MXDistinctValuesResponse,
    summary="Get operations for a specific RFC (MX)",
    description="""
    Get distinct operation codes associated with a specific RFC.
    Useful for populating the operations dropdown after the user selects an RFC.

    **Parameters:**
    - `rfc`: RFC to filter by
    - `limit`: Maximum number of operations to return (default 100)

    Returns operation codes associated with the given RFC.
    """,
    tags=["Finance - Facturación MX - Filtros"]
)
async def get_mx_operations_by_rfc(
    rfc: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get distinct operation codes for a specific RFC.

    Args:
        rfc: RFC to filter by
        limit: Maximum values to return (default 100)
        current_user: Authenticated user

    Returns:
        MXDistinctValuesResponse with unique operation codes for the RFC

    Raises:
        HTTPException: If query fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} getting operations for RFC MX: {rfc}")

    try:
        filter_service = get_filter_service_mx()
        response = filter_service.get_operations_by_rfc(rfc, limit)

        logger.info(f"Found {response.count} operations for RFC {rfc} (MX)")
        return response

    except Exception as e:
        logger.error(f"Error getting operations by RFC MX: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener operaciones: {str(e)}"
        )


@router.post(
    "/mx/filter/download",
    summary="Download filtered MX data as Excel",
    description="""
    Apply filters and download the matching records as an Excel file.
    Same filters as /mx/filter endpoint.
    """,
    tags=["Finance - Facturación MX - Filtros"]
)
async def download_filtered_mx_data(
    request: MXFilterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Download filtered records as Excel file.

    Args:
        request: Filter criteria
        current_user: Authenticated user

    Returns:
        StreamingResponse: Excel file with filtered data

    Raises:
        HTTPException: If no records found or download fails
    """
    import pandas as pd
    from io import BytesIO

    user_email = getattr(current_user, 'email', 'unknown')
    user_id = getattr(current_user, 'id', None)
    logger.info(f"User {user_email} downloading filtered MX data")

    try:
        filter_service = get_filter_service_mx()
        response = filter_service.filter_records(request)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )

        if response.total_records == 0:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron registros con los filtros especificados"
            )

        # Convert records to DataFrame
        records_data = []
        for record in response.records:
            records_data.append({
                "UUID": record.uuid,
                "Código Operación": record.codigo_operacion,
                "Conceptos": record.conceptos,
                "Fecha Emisión": record.fecha_emision,
                "RFC Receptor": record.rfc_receptor,
                "Razón Social": record.razon_receptor,
                "SubTotal": record.subtotal,
                "IVA Trasladado": record.iva_trasladado,
                "IVA Exento": record.iva_exento,
                "Total": record.total,
                "UUIDs relacionados": record.uuid_relacionados,
                "Tipo": record.tipo_comprobante,
            })

        df = pd.DataFrame(records_data)

        # Generate Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Datos Filtrados', index=False)

        excel_buffer.seek(0)
        excel_bytes = excel_buffer.read()

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Reporte_Filtrado_MX_{timestamp}.xlsx"

        logger.info(f"Descarga filtrada MX: {filename}, {len(excel_bytes)} bytes, {response.total_records} registros")

        # Record in history
        await record_finance_report(
            country="MX",
            report_type="consulta",
            stats={
                "total_records": response.total_records,
                "total_amount": response.total_amount,
                "total_subtotal": response.total_subtotal,
                "total_iva": response.total_iva,
            },
            user_id=user_id,
            user_email=user_email,
            filters_applied={
                "rfc": request.rfc,
                "operaciones": request.operaciones,
                "fecha_inicio": request.fecha_inicio,
                "fecha_fin": request.fecha_fin,
            },
            file_name=filename,
            status="completed"
        )

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(response.total_records)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading filtered data MX: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar descarga: {str(e)}"
        )


@router.post(
    "/mx/filter/download-zip",
    summary="Download filtered MX data with PDFs/XMLs as ZIP",
    description="""
    Apply filters and download the matching records along with their PDF and XML files as a ZIP package.

    The ZIP will contain:
    - Excel report with filtered data
    - PDFs/ folder with invoice PDF files found in Google Drive
    - XMLs/ folder with XML files found in Google Drive
    - missing_files.txt listing any files not found

    Same filters as /mx/filter endpoint.
    """,
    tags=["Finance - Facturación MX - Filtros"]
)
async def download_filtered_mx_zip(
    request: MXFilterRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Download filtered records with PDFs/XMLs as ZIP package.

    Args:
        request: Filter criteria
        current_user: Authenticated user

    Returns:
        StreamingResponse: ZIP file with Excel report and PDFs/XMLs

    Raises:
        HTTPException: If no records found or download fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    user_id = getattr(current_user, 'id', None)
    logger.info(f"User {user_email} downloading filtered MX ZIP with PDFs/XMLs")

    try:
        # 1. Get filtered records
        filter_service = get_filter_service_mx()
        response = filter_service.filter_records(request)

        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )

        if response.total_records == 0:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron registros con los filtros especificados"
            )

        # 2. Generate Excel content
        records_data = []
        invoices_for_zip = []

        for record in response.records:
            records_data.append({
                "UUID": record.uuid,
                "Código Operación": record.codigo_operacion,
                "Conceptos": record.conceptos,
                "Fecha Emisión": record.fecha_emision,
                "RFC Receptor": record.rfc_receptor,
                "Razón Social": record.razon_receptor,
                "SubTotal": record.subtotal,
                "IVA Trasladado": record.iva_trasladado,
                "IVA Exento": record.iva_exento,
                "Total": record.total,
                "UUIDs relacionados": record.uuid_relacionados,
                "Tipo": record.tipo_comprobante,
            })

            # Prepare for PDF/XML search
            if record.uuid and record.fecha_emision:
                invoices_for_zip.append({
                    "uuid": record.uuid,
                    "codigo_operacion": record.codigo_operacion,
                    "conceptos": record.conceptos,
                    "fecha_emision": record.fecha_emision,
                    "rfc_receptor": record.rfc_receptor,
                    "razon_receptor": record.razon_receptor,
                    "subtotal": record.subtotal,
                    "iva_trasladado": record.iva_trasladado,
                    "iva_exento": record.iva_exento,
                    "total": record.total,
                    "uuid_relacionados": record.uuid_relacionados,
                    "tipo_comprobante": record.tipo_comprobante,
                })

        # 3. Generate ZIP with PDFs/XMLs
        zip_service = get_zip_service()

        # Build metadata for naming
        metadata = {}
        if request.rfc:
            metadata["rfc"] = request.rfc
        if request.operaciones:
            metadata["codigo_operacion"] = request.operaciones[0] if len(request.operaciones) == 1 else "multiple"

        zip_buffer = zip_service.generate_invoice_package(
            invoices=invoices_for_zip,
            metadata=metadata,
            country="MX"  # Usar cache de MX
        )

        # 4. Generate filename and return
        zip_filename = zip_service.generate_zip_filename(metadata=metadata)

        logger.info(
            f"ZIP MX generado: {zip_filename}, "
            f"{response.total_records} registros, "
            f"{len(zip_buffer.getvalue())} bytes"
        )

        # Record in history
        await record_finance_report(
            country="MX",
            report_type="zip_download",
            stats={
                "total_records": response.total_records,
                "total_amount": response.total_amount,
                "total_subtotal": response.total_subtotal,
                "total_iva": response.total_iva,
                "invoices_for_zip": len(invoices_for_zip),
            },
            user_id=user_id,
            user_email=user_email,
            filters_applied={
                "rfc": request.rfc,
                "operaciones": request.operaciones,
                "fecha_inicio": request.fecha_inicio,
                "fecha_fin": request.fecha_fin,
            },
            file_name=zip_filename,
            status="completed"
        )

        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}",
                "X-Total-Records": str(response.total_records)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating ZIP MX: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar paquete ZIP: {str(e)}"
        )


@router.delete(
    "/mx/filter/cache",
    summary="Clear MX filter cache",
    description="Clear the cached Excel data to force a fresh download from Drive.",
    tags=["Finance - Facturación MX - Filtros"]
)
async def clear_mx_filter_cache(
    current_user: dict = Depends(get_current_user)
):
    """
    Clear the filter service cache.

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    filter_service = get_filter_service_mx()
    filter_service.clear_cache()
    return {"message": "Cache de filtros MX limpiado exitosamente"}


# ============================================================================
# Mexico (MX) Combined Upload Endpoints (Facturas + Complementos de Pago)
# ============================================================================

@router.post(
    "/mx/upload-combined",
    response_model=CombinedUploadResponse,
    summary="Upload facturas and complementos de pago Excel files",
    description="""
    Upload two Excel files: one for facturas (invoices) and one for complementos de pago (payment supplements).

    Both files must have the same column structure:
    - UUID, CODIGO DE OPERACIÓN, Conceptos, Fecha emision
    - RFC receptor, Razon receptor, SubTotal, IVA Trasladado
    - IVA Exento, Total, UUIDs relacionados (optional), Tipo (optional)

    Payment supplements are automatically identified by:
    - Tipo column containing "CPO1 - Pagos"
    - Conceptos containing "COMPLEMENTO DE PAGO"

    Returns a session_id for subsequent search and ZIP generation operations.
    """,
    tags=["Finance - Facturación MX - Complementos de Pago"]
)
async def upload_combined_excel(
    facturas_file: Optional[UploadFile] = File(None, description="Excel file with invoices (facturas)"),
    complementos_file: Optional[UploadFile] = File(None, description="Excel file with payment supplements (complementos de pago)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and validate both facturas and complementos de pago Excel files.

    Args:
        facturas_file: Excel file with invoice data
        complementos_file: Excel file with payment supplement data
        current_user: Authenticated user

    Returns:
        CombinedUploadResponse with parsed data from both files

    Raises:
        HTTPException: If no files provided or processing fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} uploading combined Excel files")

    # Validate that at least one file is provided
    if not facturas_file and not complementos_file:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos un archivo (facturas o complementos de pago)"
        )

    # Validate file formats
    for label, file in [("Facturas", facturas_file), ("Complementos", complementos_file)]:
        if file:
            if not file.filename:
                raise HTTPException(
                    status_code=400,
                    detail=f"Nombre de archivo es requerido para {label}"
                )
            if not file.filename.endswith(('.xlsx', '.xls')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato inválido para {label}. Use .xlsx o .xls"
                )

    try:
        # First, read raw Excel data (preserving ALL columns) for Drive sync
        merge_service = get_excel_merge_service_mx()
        raw_facturas_dicts = []
        raw_complementos_dicts = []

        if facturas_file:
            raw_facturas_dicts = await merge_service.read_uploaded_excel_as_dicts(
                facturas_file,
                DocumentType.FACTURA
            )
            logger.info(f"Read {len(raw_facturas_dicts)} raw facturas records with all columns")

        if complementos_file:
            raw_complementos_dicts = await merge_service.read_uploaded_excel_as_dicts(
                complementos_file,
                DocumentType.COMPLEMENTO_PAGO
            )
            logger.info(f"Read {len(raw_complementos_dicts)} raw complementos records with all columns")

        # Process files for session/search (simplified CombinedRecord format)
        combined_service = get_combined_excel_service()
        result = await combined_service.validate_combined_excel(
            facturas_file=facturas_file,
            complementos_file=complementos_file
        )

        # Store in session
        if result.success and (result.facturas_data or result.complementos_data):
            search_service = get_combined_search_service()
            search_service.store_session(
                result.session_id,
                result.facturas_data,
                result.complementos_data
            )
            logger.info(
                f"Combined session {result.session_id} created: "
                f"{len(result.facturas_data)} facturas, "
                f"{len(result.complementos_data)} complementos"
            )

            # Sync with Drive (merge and upload multi-sheet Excel preserving ALL columns)
            try:
                drive_service = get_drive_service()

                # Download existing master Excel (if exists)
                master_excel_bytes = drive_service.download_master_excel()
                if master_excel_bytes:
                    logger.info(f"Downloaded master Excel: {len(master_excel_bytes)} bytes")
                else:
                    logger.info("No existing master Excel, creating new multi-sheet file")

                # Merge uploaded RAW data with master (preserves ALL columns)
                merged_excel_bytes, merge_stats = await merge_service.merge_raw_excel_with_drive(
                    facturas_dicts=raw_facturas_dicts,
                    complementos_dicts=raw_complementos_dicts,
                    master_excel_bytes=master_excel_bytes
                )

                # Upload merged Excel back to Drive
                upload_success = drive_service.upload_master_excel(merged_excel_bytes)

                if upload_success:
                    logger.info(f"Drive sync successful - Facturas: {merge_stats['facturas']}, Complementos: {merge_stats['complementos']}")
                    # Add sync stats to response
                    result.drive_sync_stats = {
                        'new': merge_stats['facturas']['new'] + merge_stats['complementos']['new'],
                        'updated': merge_stats['facturas']['updated'] + merge_stats['complementos']['updated'],
                        'unchanged': merge_stats['facturas']['unchanged'] + merge_stats['complementos']['unchanged']
                    }

                    # Clear filter cache so new data is visible
                    filter_service = get_filter_service_mx()
                    filter_service.clear_cache()
                else:
                    logger.warning("Drive sync failed - upload unsuccessful")

            except Exception as e:
                logger.error(f"Drive sync error (non-blocking): {e}", exc_info=True)
                # Don't fail the whole upload if Drive sync fails

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing combined Excel files: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar los archivos: {str(e)}"
        )


@router.post(
    "/mx/search-combined",
    response_model=CombinedSearchResponse,
    summary="Search in combined facturas and complementos data",
    description="""
    Search for records in a combined session (facturas + complementos de pago).

    Search types:
    - codigo_operacion: Search by operation code (supports comma-separated values)
    - rfc: Search by RFC receptor (exact match)
    - fecha: Search by date range only

    Additional options:
    - include_facturas: Include invoices in results (default: true)
    - include_complementos: Include payment supplements in results (default: true)
    - fecha_inicio/fecha_fin: Filter by date range (works with all search types)
    """,
    tags=["Finance - Facturación MX - Complementos de Pago"]
)
async def search_combined(
    request: CombinedSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Search for records in combined data.

    Args:
        request: Search criteria
        current_user: Authenticated user

    Returns:
        CombinedSearchResponse with matching results

    Raises:
        HTTPException: If session not found or search fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(
        f"User {user_email} searching combined session {request.session_id} "
        f"by {request.search_type.value}"
    )

    try:
        search_service = get_combined_search_service()
        results = search_service.search(request)
        return results

    except ValueError as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during combined search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar: {str(e)}"
        )


@router.get(
    "/mx/combined-session/{session_id}/stats",
    summary="Get combined session statistics",
    description="Get statistics about a combined session including record counts and totals.",
    tags=["Finance - Facturación MX - Complementos de Pago"]
)
async def get_combined_session_stats(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics for a combined session.

    Args:
        session_id: Session ID from combined upload
        current_user: Authenticated user

    Returns:
        Dictionary with session statistics

    Raises:
        HTTPException: If session not found
    """
    search_service = get_combined_search_service()
    stats = search_service.get_session_stats(session_id)

    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión no encontrada o expirada: {session_id}"
        )

    return stats


@router.delete(
    "/mx/combined-session/{session_id}",
    summary="Clear combined session data",
    description="Remove combined session data from cache to free memory.",
    tags=["Finance - Facturación MX - Complementos de Pago"]
)
async def clear_combined_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Clear combined session data from cache.

    Args:
        session_id: Session ID to clear
        current_user: Authenticated user

    Returns:
        Success message
    """
    search_service = get_combined_search_service()
    success = search_service.clear_session(session_id)

    if success:
        return {"message": f"Sesión combinada {session_id} eliminada exitosamente"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión no encontrada: {session_id}"
        )


@router.post(
    "/mx/generate-combined-zip",
    summary="Generate ZIP with facturas and complementos de pago",
    description="""
    Generate a ZIP file containing PDFs, XMLs, and detailed Excel report for both
    facturas and complementos de pago.

    You can specify:
    - session_id: Required session from combined upload
    - search_criteria: Optional filters to include specific records
    - uuids: Optional list of specific UUIDs to include
    - metadata: Optional metadata for naming the ZIP file

    The ZIP will contain:
    - Detailed Excel report with facturas and complementos tabs
    - PDFs/ folder with PDF files
    - XMLs/ folder with XML files

    Files not found in Google Drive will be marked as missing in the Excel report.
    """,
    tags=["Finance - Facturación MX - Complementos de Pago"]
)
async def generate_combined_zip(
    session_id: str,
    search_criteria: Optional[CombinedSearchRequest] = None,
    uuids: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a ZIP package with facturas and complementos PDFs, XMLs, and Excel report.

    Args:
        session_id: Session ID from combined upload
        search_criteria: Optional search criteria to filter records
        uuids: Optional comma-separated UUIDs to include
        current_user: Authenticated user

    Returns:
        StreamingResponse: ZIP file download

    Raises:
        HTTPException: If session not found, no records to include, or generation fails
    """
    user_email = getattr(current_user, 'email', 'unknown')
    user_id = getattr(current_user, 'id', None)
    logger.info(f"User {user_email} requesting combined ZIP generation for session {session_id}")

    try:
        # Get session data
        search_service = get_combined_search_service()
        session_data = search_service.get_session_data(session_id)

        if session_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Sesión no encontrada o expirada: {session_id}"
            )

        # Determine which records to include
        all_records = session_data['facturas'] + session_data['complementos']
        records_to_include = []

        if uuids:
            # Filter by specific UUIDs
            uuid_set = set(u.strip().upper() for u in uuids.split(','))
            records_to_include = [
                r for r in all_records
                if r.uuid.upper() in uuid_set
            ]
            logger.info(f"Filtering by {len(uuid_set)} UUIDs, found {len(records_to_include)} records")

        elif search_criteria:
            # Filter by search criteria
            search_criteria.session_id = session_id
            search_results = search_service.search(search_criteria)
            records_to_include = [
                # Convert CombinedSearchResult back to dict for ZIP generation
                r for r in all_records
                if any(sr.uuid == r.uuid for sr in search_results.results)
            ]
            logger.info(f"Search criteria returned {len(records_to_include)} records")

        else:
            # Include all session data
            records_to_include = all_records
            logger.info(f"Including all {len(records_to_include)} records from session")

        if not records_to_include:
            raise HTTPException(
                status_code=400,
                detail="No se encontraron registros para incluir en el ZIP"
            )

        # Convert to dict format for ZIP service
        invoices_for_zip = [
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
                "uuid_relacionados": r.uuid_relacionados,
                "tipo_comprobante": r.tipo_comprobante,
                "document_type": r.document_type.value
            }
            for r in records_to_include
        ]

        # Build metadata
        facturas_count = len([r for r in records_to_include if r.document_type == DocumentType.FACTURA])
        complementos_count = len([r for r in records_to_include if r.document_type == DocumentType.COMPLEMENTO_PAGO])

        # Get unique operation codes for filename
        unique_ops = set(r.codigo_operacion for r in records_to_include)
        metadata = {
            "tipo": "combinado",
            "facturas_count": facturas_count,
            "complementos_count": complementos_count
        }
        if len(unique_ops) == 1:
            metadata["codigo_operacion"] = list(unique_ops)[0]

        # Generate ZIP using existing MX zip service
        zip_service = get_zip_service()
        zip_buffer = zip_service.generate_invoice_package(
            invoices=invoices_for_zip,
            metadata=metadata
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if metadata.get("codigo_operacion"):
            codigo = metadata["codigo_operacion"].replace(":", "-").replace("/", "-")
            filename = f"Facturacion_MX_Combinado_{codigo}_{timestamp}.zip"
        else:
            filename = f"Facturacion_MX_Combinado_{timestamp}.zip"

        logger.info(
            f"Combined ZIP generation successful: {filename}, "
            f"Size: {len(zip_buffer.getvalue())} bytes, "
            f"{facturas_count} facturas, {complementos_count} complementos"
        )

        # Record in history
        await record_finance_report(
            country="MX",
            report_type="zip_download",
            stats={
                "total_records": len(records_to_include),
                "facturas_count": facturas_count,
                "complementos_count": complementos_count,
                "total_amount": sum(r.total for r in records_to_include),
            },
            user_id=user_id,
            user_email=user_email,
            filters_applied={
                "session_id": session_id,
                "uuids_filter": uuids is not None,
                "search_criteria_used": search_criteria is not None,
            },
            file_name=filename,
            status="completed"
        )

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(len(records_to_include)),
                "X-Facturas-Count": str(facturas_count),
                "X-Complementos-Count": str(complementos_count)
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during combined ZIP generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating combined ZIP: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el paquete ZIP: {str(e)}"
        )


@router.post(
    "/mx/precache-drive-files",
    summary="Pre-populate Drive file cache",
    description="""
    Pre-populates the Supabase cache with Google Drive file IDs for all invoices.

    This dramatically speeds up ZIP downloads because:
    1. Lists ALL files from Drive in ONE API call
    2. Matches UUIDs in memory (instant)
    3. Stores file IDs in Supabase cache

    After running this, ZIP downloads use cached file IDs instead of
    searching Drive for each file individually.

    Recommended to run periodically (e.g., daily) or after uploading new files.
    """,
    tags=["Finance - Facturación MX - Cache"]
)
async def precache_drive_files_mx(
    current_user: dict = Depends(get_current_user)
):
    """
    Pre-cache Drive file IDs for MX invoices.

    Workflow:
    1. Gets all UUIDs from the MX master Excel in Drive
    2. Lists ALL files from Drive (one API call)
    3. Matches UUIDs to files in memory
    4. Stores file IDs in Supabase cache

    Returns:
        Dict with statistics: total, cached, not_found, already_cached
    """
    user_email = getattr(current_user, 'email', 'unknown')
    logger.info(f"User {user_email} starting MX Drive file precache")

    try:
        # 1. Get all UUIDs from MX filter service (reads master Excel from Drive)
        filter_service = get_filter_service_mx()
        all_records = filter_service.get_all_records()

        if not all_records:
            return {
                "success": False,
                "message": "No se encontraron registros en el Excel maestro",
                "stats": {"total": 0, "cached": 0, "not_found": 0, "already_cached": 0}
            }

        # Extract UUIDs
        uuids = [r.uuid for r in all_records if r.uuid]
        logger.info(f"Found {len(uuids)} UUIDs to precache")

        # 2. Run precache
        drive_service = get_drive_service()
        stats = drive_service.precache_drive_file_ids(uuids, country="MX")

        logger.info(f"Precache completed: {stats}")

        return {
            "success": True,
            "message": f"Cache pre-populated for {stats['cached']} files",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error during precache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al pre-cachear archivos: {str(e)}"
        )


@router.get(
    "/mx/cache-stats",
    summary="Get MX Drive cache statistics",
    description="Returns statistics about the Drive file cache for Mexico invoices.",
    tags=["Finance - Facturación MX - Cache"]
)
async def get_mx_cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get cache statistics for MX Drive files.

    Returns:
        Dict with cache statistics including total_cached, pdf_count, xml_count, and cache_ready flag.
    """
    try:
        from src.repositorio.drive_file_cache_repository import get_drive_file_cache_repository
        from src.config.supabase_config import get_supabase_client

        supabase = get_supabase_client()
        # Use admin_client to bypass RLS
        cache_repo = get_drive_file_cache_repository(supabase.admin_client)
        stats = cache_repo.get_cache_stats(country="MX")

        # Cache is ready if we have at least some files cached
        cache_ready = stats.get('total_cached', 0) > 0

        return {
            "success": True,
            "total_cached": stats.get('total_cached', 0),
            "pdf_count": stats.get('pdf_count', 0),
            "xml_count": stats.get('xml_count', 0),
            "cache_ready": cache_ready,
            "country": "MX"
        }

    except Exception as e:
        logger.error(f"Error getting MX cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas del cache: {str(e)}"
        )
