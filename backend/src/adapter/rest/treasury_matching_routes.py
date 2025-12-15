"""
Treasury Matching Routes for Declaration-Historial Matching.

Provides API endpoints for the Exchange Declaration to Historial de Pagos
matching workflow.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
import io
import pandas as pd

from src.adapter.rest.rbac_dependencies import require_roles
from src.core.servicios.treasury import (
    historial_parser_service,
    payment_group_aggregator,
    declaration_payment_matcher,
    enriched_excel_generator,
)
from src.interface.treasury_matching_dtos import (
    HistorialUploadResponse,
    MatchConfig,
    MatchingSessionResponse,
    MatchingStatistics,
    ManualOverrideRequest,
    ManualOverrideResponse,
    DeclarationItem,
    DeclarationInventoryUploadResponse,
    PaymentGroup,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/treasury/declarations/match",
    tags=["Treasury Declaration Matching"]
)

# In-memory session storage (expires after 30 minutes)
# Structure: { session_id: { data, created_at, expires_at } }
_sessions: Dict[str, Dict] = {}
SESSION_TIMEOUT_MINUTES = 30


def _clean_expired_sessions():
    """Remove expired sessions from storage."""
    now = datetime.utcnow()
    expired = [
        sid for sid, session in _sessions.items()
        if session.get('expires_at', now) < now
    ]
    for sid in expired:
        del _sessions[sid]
        logger.info(f"Cleaned up expired session: {sid}")


def _get_session(session_id: str) -> Optional[Dict]:
    """Get session by ID, returning None if not found or expired."""
    _clean_expired_sessions()

    session = _sessions.get(session_id)
    if not session:
        return None

    # Extend expiration on access
    session['expires_at'] = datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    return session


def _create_session() -> str:
    """Create a new session and return its ID."""
    _clean_expired_sessions()

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES),
        'historial_records': [],
        'payment_groups': [],
        'declarations': [],
        'results': [],
        'statistics': None,
        'config': None,
        'original_df': None,
        'column_mapping': {},
    }
    return session_id


@router.post("/upload-historial", response_model=HistorialUploadResponse)
async def upload_historial(
    file: UploadFile = File(..., description="Historial de Pagos Excel file (.xlsx)"),
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Upload and parse a Historial de Pagos Excel file.

    Parses the Excel file, validates columns, and groups payments by (customer, date).
    Returns a session ID for subsequent operations.

    Required role: tesoreria (or admin)
    """
    logger.info(f"User {current_user.get('id')} uploading Historial de Pagos")

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Archivo debe ser Excel (.xlsx o .xls)"
        )

    try:
        # Parse the Excel file
        records, column_status, errors, preview_data, original_df = await historial_parser_service.parse_historial(file)

        if errors and not records:
            # Critical errors, couldn't parse any records
            return HistorialUploadResponse(
                success=False,
                session_id="",
                total_rows=0,
                valid_rows=0,
                payment_groups=[],
                group_count=0,
                column_status=column_status,
                errors=errors,
                preview_data=preview_data
            )

        # Aggregate into payment groups
        payment_groups = payment_group_aggregator.aggregate_payments(records)

        # Create session
        session_id = _create_session()
        session = _sessions[session_id]
        session['historial_records'] = records
        session['payment_groups'] = payment_groups
        session['original_df'] = original_df
        session['column_mapping'] = historial_parser_service.get_column_mapping(original_df)

        logger.info(
            f"Session {session_id} created: {len(records)} records, "
            f"{len(payment_groups)} groups"
        )

        return HistorialUploadResponse(
            success=True,
            session_id=session_id,
            total_rows=len(original_df),
            valid_rows=len(records),
            payment_groups=payment_groups,
            group_count=len(payment_groups),
            column_status=column_status,
            errors=errors,
            preview_data=preview_data
        )

    except Exception as e:
        logger.error(f"Error uploading Historial de Pagos: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar archivo: {str(e)}"
        )


def parse_amount_value(value) -> Optional[float]:
    """Parse amount from various formats (European, US, or plain number).

    Handles:
    - European format: 8.111,43 (dots for thousands, comma for decimal)
    - US format: $4,862.00 (dollar sign, commas for thousands, dot for decimal)
    - Simple comma decimal: 8111,43
    - Standard number with commas: 8,111.43
    - Plain numbers: 8111.43
    """
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value).strip()

    # Empty string
    if not value_str:
        return None

    try:
        # US format: $4,862.00
        if '$' in value_str:
            clean = value_str.replace('$', '').replace(',', '').strip()
            return float(clean)

        # European format: 8.111,43 (dots for thousands, comma for decimal)
        if ',' in value_str and '.' in value_str:
            # European: remove dots (thousands), replace comma with dot (decimal)
            clean = value_str.replace('.', '').replace(',', '.')
            return float(clean)

        # Simple comma decimal: 8111,43
        if ',' in value_str and '.' not in value_str:
            clean = value_str.replace(',', '.')
            return float(clean)

        # Standard number with commas as thousands: 8,111.43
        clean = value_str.replace(',', '')
        return float(clean)
    except ValueError:
        return None


def find_col_with_priority(df_cols, variations):
    """Find column with priority (earlier in variations list = higher priority)."""
    df_cols_lower = {c.lower().strip(): c for c in df_cols}
    for var in variations:
        if var.lower().strip() in df_cols_lower:
            return df_cols_lower[var.lower().strip()]
    return None


@router.post("/upload-declarations", response_model=DeclarationInventoryUploadResponse)
async def upload_declarations(
    session_id: str = Query(..., description="Session ID from upload-historial"),
    file: UploadFile = File(..., description="Declaration inventory Excel file (.xlsx)"),
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Upload declaration inventory Excel file.

    The Excel should have columns:
    - Customer name
    - Date (DD-MM-YYYY or YYYY-MM-DD)
    - Amount (USD)
    - Declaration number
    - PDF filename

    Required role: tesoreria (or admin)
    """
    logger.info(f"User {current_user.get('id')} uploading declaration inventory")

    session = _get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Archivo debe ser Excel (.xlsx o .xls)"
        )

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')

        declarations: List[DeclarationItem] = []
        errors: List[str] = []

        # Extended column variations (backward compatible + new scanner format)
        # Priority order: preferred columns listed first for date/amount
        customer_cols = ['Cliente', 'Customer', 'Nombre', 'customer_name', 'Customer Name']
        # Prefer Parsed Date (YYYY-MM-DD) over Date Folder (DD-MM-YYYY)
        date_cols_priority = ['Parsed Date', 'Fecha', 'Date', 'fecha', 'Date Folder']
        # Prefer Parsed Amount (standard) over Amount Folder (European format)
        amount_cols_priority = ['Parsed Amount', 'Monto', 'Amount', 'Valor', 'amount', 'Amount Folder']
        number_cols = ['Numero', 'Number', 'Declaracion', 'declaration_number', 'DC', 'Declaration Number']
        pdf_cols = ['PDF', 'Archivo', 'File', 'pdf_file_name', 'Nombre PDF', 'PDF File Name']

        customer_col = find_col_with_priority(df.columns, customer_cols)
        date_col = find_col_with_priority(df.columns, date_cols_priority)
        amount_col = find_col_with_priority(df.columns, amount_cols_priority)
        number_col = find_col_with_priority(df.columns, number_cols)
        pdf_col = find_col_with_priority(df.columns, pdf_cols)

        if not all([customer_col, date_col, amount_col, number_col]):
            missing = []
            if not customer_col:
                missing.append("Cliente")
            if not date_col:
                missing.append("Fecha")
            if not amount_col:
                missing.append("Monto")
            if not number_col:
                missing.append("Numero Declaracion")
            errors.append(f"Columnas requeridas no encontradas: {', '.join(missing)}")
            return DeclarationInventoryUploadResponse(
                success=False,
                session_id=session_id,
                total_declarations=0,
                declarations=[],
                errors=errors
            )

        for idx, row in df.iterrows():
            try:
                customer = str(row[customer_col]) if pd.notna(row[customer_col]) else ""
                if not customer:
                    continue

                # Parse date
                date_val = row[date_col]
                if pd.isna(date_val):
                    continue

                if isinstance(date_val, pd.Timestamp):
                    fecha = date_val.strftime("%Y-%m-%d")
                elif isinstance(date_val, datetime):
                    fecha = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val).strip()
                    # Try common formats
                    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"]:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            fecha = dt.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                    else:
                        errors.append(f"Fila {idx + 2}: Fecha inválida '{date_val}'")
                        continue

                # Parse amount using multi-format parser
                amount_val = row[amount_col]
                amount = parse_amount_value(amount_val)
                if amount is None:
                    errors.append(f"Fila {idx + 2}: Monto inválido '{amount_val}'")
                    continue

                # Handle NaN values for declaration number
                number_val = row[number_col]
                if pd.isna(number_val) or str(number_val).lower() == 'nan':
                    # Skip rows without declaration numbers
                    continue
                else:
                    # Convert float to int string (81590.0 → "81590")
                    if isinstance(number_val, float) and number_val == int(number_val):
                        declaration_number = str(int(number_val))
                    else:
                        declaration_number = str(number_val).strip()

                pdf_filename = str(row[pdf_col]) if pdf_col and pd.notna(row[pdf_col]) else f"DC_{declaration_number}.pdf"

                # Normalize customer name
                customer_normalized = historial_parser_service._normalize_customer_name(customer)

                declaration = DeclarationItem(
                    declaration_id=str(uuid.uuid4()),
                    declaration_number=declaration_number,
                    customer_name=customer,
                    customer_name_normalized=customer_normalized,
                    fecha=fecha,
                    amount=amount,
                    pdf_file_name=pdf_filename,
                    folder_path=None
                )
                declarations.append(declaration)

            except Exception as e:
                errors.append(f"Fila {idx + 2}: Error - {str(e)}")

        # Store declarations in session
        session['declarations'] = declarations

        logger.info(f"Loaded {len(declarations)} declarations for session {session_id}")

        return DeclarationInventoryUploadResponse(
            success=len(declarations) > 0,
            session_id=session_id,
            total_declarations=len(declarations),
            declarations=declarations,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error uploading declarations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar archivo: {str(e)}"
        )


@router.post("/execute", response_model=MatchingSessionResponse)
async def execute_matching(
    session_id: str = Query(..., description="Session ID"),
    config: MatchConfig = MatchConfig(),
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Execute the matching algorithm with the provided configuration.

    Required role: tesoreria (or admin)
    """
    logger.info(
        f"User {current_user.get('id')} executing matching for session {session_id}. "
        f"Config: date_tolerance={config.date_tolerance_days}, "
        f"amount_tolerance={config.amount_tolerance}"
    )

    session = _get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

    payment_groups = session.get('payment_groups', [])
    declarations = session.get('declarations', [])

    if not payment_groups:
        raise HTTPException(
            status_code=400,
            detail="No hay grupos de pago. Primero suba el archivo Historial de Pagos."
        )

    if not declarations:
        raise HTTPException(
            status_code=400,
            detail="No hay declaraciones. Primero suba el inventario de declaraciones."
        )

    try:
        # Execute matching
        results, statistics = declaration_payment_matcher.match_payments_to_declarations(
            payment_groups=payment_groups,
            declarations=declarations,
            config=config
        )

        # Store results in session
        session['results'] = results
        session['statistics'] = statistics
        session['config'] = config

        return MatchingSessionResponse(
            session_id=session_id,
            success=True,
            config=config,
            results=results,
            statistics=statistics,
            errors=[]
        )

    except Exception as e:
        logger.error(f"Error executing matching: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar coincidencias: {str(e)}"
        )


@router.get("/results/{session_id}", response_model=MatchingSessionResponse)
async def get_results(
    session_id: str,
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Get cached matching results for a session.

    Required role: tesoreria (or admin)
    """
    session = _get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

    results = session.get('results', [])
    statistics = session.get('statistics')
    config = session.get('config', MatchConfig())

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No hay resultados. Primero ejecute el algoritmo de coincidencias."
        )

    return MatchingSessionResponse(
        session_id=session_id,
        success=True,
        config=config,
        results=results,
        statistics=statistics or MatchingStatistics(),
        errors=[]
    )


@router.post("/override", response_model=ManualOverrideResponse)
async def manual_override(
    request: ManualOverrideRequest,
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Manually override a match result.

    Required role: tesoreria (or admin)
    """
    logger.info(
        f"User {current_user.get('id')} overriding match: "
        f"group={request.group_id}, declaration={request.declaration_id}"
    )

    session = _get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

    results = session.get('results', [])
    declarations = session.get('declarations', [])

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No hay resultados para modificar"
        )

    # Find declaration if provided
    declaration = None
    if request.declaration_id:
        for d in declarations:
            if d.declaration_id == request.declaration_id:
                declaration = d
                break
        if not declaration:
            raise HTTPException(
                status_code=404,
                detail=f"Declaración no encontrada: {request.declaration_id}"
            )

    # Apply override
    updated_results = declaration_payment_matcher.manual_override(
        results=results,
        group_id=request.group_id,
        declaration=declaration
    )

    session['results'] = updated_results

    # Find the updated result
    updated_result = None
    for r in updated_results:
        if r.group_id == request.group_id:
            updated_result = r
            break

    # Recalculate statistics
    used_declarations = set(
        r.declaration.declaration_id for r in updated_results
        if r.declaration
    )
    session['statistics'] = declaration_payment_matcher._calculate_statistics(
        updated_results, declarations, used_declarations
    )

    return ManualOverrideResponse(
        success=True,
        message="Coincidencia actualizada exitosamente",
        updated_result=updated_result
    )


@router.get("/download/{session_id}")
async def download_enriched_excel(
    session_id: str,
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Download the enriched Excel file with declaration columns populated.

    Required role: tesoreria (or admin)
    """
    logger.info(f"User {current_user.get('id')} downloading enriched Excel for session {session_id}")

    session = _get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

    results = session.get('results', [])
    statistics = session.get('statistics')
    original_df = session.get('original_df')
    column_mapping = session.get('column_mapping', {})

    if not results or original_df is None:
        raise HTTPException(
            status_code=400,
            detail="No hay resultados para descargar. Primero ejecute el algoritmo."
        )

    try:
        # Generate enriched Excel
        excel_bytes = enriched_excel_generator.generate_enriched_excel(
            original_df=original_df,
            results=results,
            statistics=statistics or MatchingStatistics(),
            column_mapping=column_mapping
        )

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Historial_Enriquecido_{timestamp}.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Match-Rate": f"{statistics.match_percentage if statistics else 0:.1f}%"
            }
        )

    except Exception as e:
        logger.error(f"Error generating enriched Excel: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar archivo: {str(e)}"
        )


@router.get("/declarations/{session_id}", response_model=List[DeclarationItem])
async def get_declarations(
    session_id: str,
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Get list of available declarations for a session.

    Required role: tesoreria (or admin)
    """
    session = _get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

    return session.get('declarations', [])


@router.get("/payment-groups/{session_id}", response_model=List[PaymentGroup])
async def get_payment_groups(
    session_id: str,
    current_user: dict = Depends(require_roles(['tesoreria']))
):
    """
    Get list of payment groups for a session.

    Required role: tesoreria (or admin)
    """
    session = _get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

    return session.get('payment_groups', [])
