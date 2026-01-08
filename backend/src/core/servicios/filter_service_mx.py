"""
Filter Service for Mexico (MX)

Servicio para consultar y filtrar datos del Excel maestro de facturación MX
almacenado en Google Drive.

Soporta multi-sheet Excel con dos pestañas:
- Facturas (invoices)
- Complementos de Pago (payment supplements)

Soporta filtros por:
- Código de operación + rango de fecha
- RFC + rango de fecha
- RFC + código operación + rango de fecha (combinación)
- Tipo de documento (factura / complemento / ambos)
"""

import io
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Any
import pandas as pd

from src.core.servicios.google_drive_service import get_drive_service
from src.interface.finance_dtos_mx import (
    MXFilterRequest,
    MXFilterResponse,
    MXFilteredRecord,
    MXDistinctValuesResponse,
)

logger = logging.getLogger(__name__)

# Sheet names for multi-sheet Excel
SHEET_FACTURAS = "Facturas"
SHEET_COMPLEMENTOS = "Complementos de Pago"


class MXFilterService:
    """
    Servicio para filtrar datos del Excel maestro de México.

    Soporta multi-sheet Excel con dos pestañas:
    - Facturas (invoices)
    - Complementos de Pago (payment supplements)

    Lee el archivo Facturación MX 2025.xlsx desde Google Drive
    y permite aplicar filtros por código de operación, RFC y rango de fechas.
    """

    # Column mapping from Excel to internal names
    COLUMN_MAPPING = {
        "uuid": "UUID",
        "codigo_operacion": "CODIGO DE OPERACIÓN",
        "conceptos": "Conceptos",
        "fecha_emision": "Fecha emision",
        "rfc_receptor": "RFC receptor",
        "razon_receptor": "Razon receptor",
        "subtotal": "SubTotal",
        "iva_trasladado": "IVA Trasladado",
        "iva_exento": "IVA Exento",
        "total": "Total",
        "uuid_relacionados": "UUIDs relacionados",
        "tipo_comprobante": "Tipo",
    }

    def __init__(self):
        """Inicializa el servicio de filtrado."""
        self.drive_service = get_drive_service()
        # Multi-sheet cache
        self._cached_facturas: Optional[pd.DataFrame] = None
        self._cached_complementos: Optional[pd.DataFrame] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes cache

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if self._cache_timestamp is None:
            return False
        # At least one sheet must be cached
        if self._cached_facturas is None and self._cached_complementos is None:
            return False
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl_seconds

    def _load_excel_from_drive(self) -> pd.DataFrame:
        """
        Descarga y lee el Excel maestro desde Google Drive (combinando ambas hojas).

        Returns:
            DataFrame with combined invoice and payment supplement data.

        Raises:
            ValueError: If file not found or cannot be read.
        """
        # Check cache first
        if self._is_cache_valid():
            logger.debug("Using cached Excel data MX")
            return self._get_combined_dataframe()

        logger.info("Descargando Excel maestro de Google Drive MX...")
        excel_bytes = self.drive_service.download_master_excel()

        if not excel_bytes:
            raise ValueError(
                "No se encontró el archivo maestro de facturación MX en Google Drive. "
                "Primero debe cargar un archivo Excel para generar el reporte."
            )

        logger.info(f"Excel MX descargado: {len(excel_bytes)} bytes")

        # Load multi-sheet data
        self._load_multisheet_excel(excel_bytes)

        return self._get_combined_dataframe()

    def _load_multisheet_excel(self, excel_bytes: bytes) -> None:
        """
        Load multi-sheet Excel into separate cached DataFrames.

        Args:
            excel_bytes: Excel file content in bytes.
        """
        excel_buffer = io.BytesIO(excel_bytes)

        try:
            # Get all sheet names
            xl = pd.ExcelFile(excel_buffer)
            sheet_names = xl.sheet_names
            logger.info(f"Excel MX hojas encontradas: {sheet_names}")

            # Read Facturas sheet
            if SHEET_FACTURAS in sheet_names:
                self._cached_facturas = pd.read_excel(excel_buffer, sheet_name=SHEET_FACTURAS)
                logger.info(f"Excel MX Facturas: {len(self._cached_facturas)} filas")
            else:
                # Fallback: try first sheet as facturas
                self._cached_facturas = pd.read_excel(excel_buffer, sheet_name=0)
                logger.info(f"Excel MX (primera hoja como Facturas): {len(self._cached_facturas)} filas")

            # Reset buffer for second read
            excel_buffer.seek(0)

            # Read Complementos sheet
            if SHEET_COMPLEMENTOS in sheet_names:
                self._cached_complementos = pd.read_excel(excel_buffer, sheet_name=SHEET_COMPLEMENTOS)
                logger.info(f"Excel MX Complementos: {len(self._cached_complementos)} filas")
            else:
                # No complementos sheet, create empty DataFrame
                self._cached_complementos = pd.DataFrame()
                logger.info("Excel MX: No se encontró hoja de Complementos")

            self._cache_timestamp = datetime.now()

        except Exception as e:
            logger.error(f"Error leyendo Excel MX multi-sheet: {e}", exc_info=True)
            raise ValueError(f"Error al leer el archivo Excel: {str(e)}")

    def _get_combined_dataframe(self) -> pd.DataFrame:
        """
        Get combined DataFrame from cached facturas and complementos.

        Returns:
            Combined DataFrame with document_type column.
        """
        dfs_to_combine = []

        if self._cached_facturas is not None and not self._cached_facturas.empty:
            df_facturas = self._cached_facturas.copy()
            df_facturas['_document_type'] = 'factura'
            dfs_to_combine.append(df_facturas)

        if self._cached_complementos is not None and not self._cached_complementos.empty:
            df_complementos = self._cached_complementos.copy()
            df_complementos['_document_type'] = 'complemento_pago'
            dfs_to_combine.append(df_complementos)

        if not dfs_to_combine:
            return pd.DataFrame()

        combined = pd.concat(dfs_to_combine, ignore_index=True)
        logger.debug(f"Combined DataFrame: {len(combined)} filas totales")
        return combined

    def _load_sheet_from_drive(
        self,
        include_facturas: bool = True,
        include_complementos: bool = True
    ) -> pd.DataFrame:
        """
        Load specific sheets from Drive (for filtered queries).

        Args:
            include_facturas: Include facturas sheet.
            include_complementos: Include complementos sheet.

        Returns:
            DataFrame with requested data.
        """
        # Ensure cache is loaded
        if not self._is_cache_valid():
            self._load_excel_from_drive()

        dfs_to_combine = []

        if include_facturas and self._cached_facturas is not None and not self._cached_facturas.empty:
            df_facturas = self._cached_facturas.copy()
            df_facturas['_document_type'] = 'factura'
            dfs_to_combine.append(df_facturas)

        if include_complementos and self._cached_complementos is not None and not self._cached_complementos.empty:
            df_complementos = self._cached_complementos.copy()
            df_complementos['_document_type'] = 'complemento_pago'
            dfs_to_combine.append(df_complementos)

        if not dfs_to_combine:
            return pd.DataFrame()

        return pd.concat(dfs_to_combine, ignore_index=True)

    def _parse_date(self, date_val) -> Optional[date]:
        """
        Parse date value to date object.
        Handles multiple formats and types.
        """
        if date_val is None or pd.isna(date_val):
            return None

        # If already a date or datetime
        if isinstance(date_val, datetime):
            return date_val.date()
        if isinstance(date_val, date):
            return date_val

        date_str = str(date_val).strip()

        # Try multiple formats
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Try pandas datetime parsing as fallback
        try:
            # Use format='mixed' to avoid dayfirst warning with ISO format dates
            parsed = pd.to_datetime(date_str, format='mixed', dayfirst=True)
            if not pd.isna(parsed):
                return parsed.date()
        except Exception:
            pass

        return None

    def _apply_filters(
        self,
        df: pd.DataFrame,
        request: MXFilterRequest
    ) -> pd.DataFrame:
        """
        Apply filters to a DataFrame.

        Args:
            df: DataFrame to filter
            request: Filter request with criteria

        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df

        result_df = df.copy()
        col_map = self.COLUMN_MAPPING

        logger.info(f"[FILTER] DataFrame inicial: {len(result_df)} filas")
        logger.info(f"[FILTER] Filtros recibidos: operaciones={request.operaciones}, rfc={request.rfc}, fecha_inicio={request.fecha_inicio}, fecha_fin={request.fecha_fin}")

        # Filter by codigo_operacion(es)
        if request.operaciones and len(request.operaciones) > 0:
            operacion_col = col_map.get("codigo_operacion")
            if operacion_col and operacion_col in result_df.columns:
                # Convert both to uppercase for case-insensitive matching
                operaciones_upper = [op.upper().strip() for op in request.operaciones]
                logger.info(f"[FILTER] Filtrando por operaciones: {operaciones_upper}")
                result_df = result_df[
                    result_df[operacion_col].astype(str).str.upper().str.strip().isin(operaciones_upper)
                ]
                logger.info(f"[FILTER] Después de filtro operaciones: {len(result_df)} filas")

        # Filter by RFC
        if request.rfc:
            rfc_col = col_map.get("rfc_receptor")
            if rfc_col and rfc_col in result_df.columns:
                rfc_search = request.rfc.strip().upper()
                logger.info(f"[FILTER] Filtrando por RFC: {rfc_search}")
                # Partial match (contains)
                result_df = result_df[
                    result_df[rfc_col].astype(str).str.upper().str.contains(rfc_search, case=False, na=False)
                ]
                logger.info(f"[FILTER] Después de filtro RFC: {len(result_df)} filas")

        # Filter by date range
        if request.fecha_inicio or request.fecha_fin:
            fecha_col = col_map.get("fecha_emision")
            if fecha_col and fecha_col in result_df.columns:
                logger.info(f"[FILTER] Filtrando por fechas: {request.fecha_inicio} a {request.fecha_fin}")
                # Parse dates in DataFrame
                parsed_dates = result_df[fecha_col].apply(self._parse_date)

                if request.fecha_inicio and request.fecha_fin:
                    # Both dates specified
                    mask = (
                        parsed_dates.notna() &
                        (parsed_dates >= request.fecha_inicio) &
                        (parsed_dates <= request.fecha_fin)
                    )
                elif request.fecha_inicio:
                    # Only start date
                    mask = parsed_dates.notna() & (parsed_dates >= request.fecha_inicio)
                else:
                    # Only end date
                    mask = parsed_dates.notna() & (parsed_dates <= request.fecha_fin)

                result_df = result_df[mask]
                logger.info(f"[FILTER] Después de filtro fecha: {len(result_df)} filas")

        logger.info(f"[FILTER] Resultado final: {len(result_df)} filas")
        return result_df

    def _df_to_records(self, df: pd.DataFrame) -> List[MXFilteredRecord]:
        """
        Convert DataFrame rows to MXFilteredRecord objects.
        """
        records = []
        col_map = self.COLUMN_MAPPING

        for idx, row in df.iterrows():
            try:
                # Safely get values with proper type conversion
                def safe_get(key: str, as_float: bool = False) -> Any:
                    col_name = col_map.get(key)
                    if not col_name or col_name not in row.index:
                        return None
                    val = row[col_name]
                    if pd.isna(val):
                        return None
                    if as_float:
                        try:
                            if isinstance(val, (int, float)):
                                return float(val)
                            str_val = str(val).replace(",", "").strip()
                            if str_val == "" or str_val == "0":
                                return 0.0
                            return float(str_val)
                        except (ValueError, TypeError):
                            return 0.0
                    return str(val) if val else None

                # Format date
                fecha_val = row.get(col_map.get("fecha_emision"))
                fecha_str = None
                if fecha_val is not None and not pd.isna(fecha_val):
                    parsed_date = self._parse_date(fecha_val)
                    if parsed_date:
                        fecha_str = parsed_date.isoformat()

                record = MXFilteredRecord(
                    uuid=safe_get("uuid"),
                    codigo_operacion=safe_get("codigo_operacion"),
                    conceptos=safe_get("conceptos"),
                    fecha_emision=fecha_str,
                    rfc_receptor=safe_get("rfc_receptor"),
                    razon_receptor=safe_get("razon_receptor"),
                    subtotal=safe_get("subtotal", as_float=True),
                    iva_trasladado=safe_get("iva_trasladado", as_float=True),
                    iva_exento=safe_get("iva_exento", as_float=True),
                    total=safe_get("total", as_float=True),
                    uuid_relacionados=safe_get("uuid_relacionados"),
                    tipo_comprobante=safe_get("tipo_comprobante"),
                )
                records.append(record)

            except Exception as e:
                logger.warning(f"Error convirtiendo fila a record MX: {e}")
                continue

        return records

    def filter_records(self, request: MXFilterRequest) -> MXFilterResponse:
        """
        Filter records from the MX master Excel based on request criteria.

        Args:
            request: Filter criteria

        Returns:
            MXFilterResponse with matching records
        """
        try:
            # Load Excel data from Drive
            df = self._load_excel_from_drive()

            filters_applied: Dict[str, str] = {}

            # Build filters_applied summary
            if request.operaciones:
                filters_applied["operaciones"] = ", ".join(request.operaciones)
            if request.rfc:
                filters_applied["rfc"] = request.rfc
            if request.fecha_inicio or request.fecha_fin:
                fecha_str = ""
                if request.fecha_inicio:
                    fecha_str = str(request.fecha_inicio)
                if request.fecha_fin:
                    fecha_str += f" a {request.fecha_fin}" if fecha_str else str(request.fecha_fin)
                filters_applied["fecha_rango"] = fecha_str

            # Apply filters
            filtered_df = self._apply_filters(df, request)

            # Convert to records
            records = self._df_to_records(filtered_df)

            # Calculate totals
            total_amount = sum(r.total or 0 for r in records)
            total_subtotal = sum(r.subtotal or 0 for r in records)
            total_iva = sum(r.iva_trasladado or 0 for r in records)

            logger.info(f"Filtro MX: {len(records)} registros encontrados")

            # Build response
            message = f"Se encontraron {len(records)} registros"
            if not records:
                message = "No se encontraron registros con los filtros especificados"

            return MXFilterResponse(
                success=True,
                total_records=len(records),
                records=records,
                filters_applied=filters_applied,
                total_amount=round(total_amount, 2),
                total_subtotal=round(total_subtotal, 2),
                total_iva=round(total_iva, 2),
                message=message
            )

        except ValueError as e:
            logger.error(f"Error de validación en filtro MX: {e}")
            return MXFilterResponse(
                success=False,
                total_records=0,
                records=[],
                filters_applied={},
                total_amount=0,
                total_subtotal=0,
                total_iva=0,
                message=str(e)
            )
        except Exception as e:
            logger.error(f"Error inesperado en filtro MX: {e}", exc_info=True)
            return MXFilterResponse(
                success=False,
                total_records=0,
                records=[],
                filters_applied={},
                total_amount=0,
                total_subtotal=0,
                total_iva=0,
                message=f"Error al consultar datos: {str(e)}"
            )

    def get_all_records(self) -> List[MXFilteredRecord]:
        """
        Get all records from the MX master Excel (no filtering).

        Used for precaching Drive file IDs.

        Returns:
            List of all MXFilteredRecord objects
        """
        try:
            df = self._load_excel_from_drive()
            records = self._df_to_records(df)
            logger.info(f"Loaded {len(records)} total records from MX Excel")
            return records
        except Exception as e:
            logger.error(f"Error loading all MX records: {e}")
            return []

    def get_distinct_values(
        self,
        field: str,
        limit: int = 100
    ) -> MXDistinctValuesResponse:
        """
        Get distinct values for a field (for autocomplete).

        Args:
            field: Field name to get distinct values for ('rfc', 'operacion')
            limit: Maximum number of values to return

        Returns:
            MXDistinctValuesResponse with unique values
        """
        try:
            df = self._load_excel_from_drive()

            # Map field to column names
            field_mapping = {
                "rfc": "RFC receptor",
                "operacion": "CODIGO DE OPERACIÓN",
                "codigo_operacion": "CODIGO DE OPERACIÓN",
            }

            column_name = field_mapping.get(field.lower())
            if not column_name:
                return MXDistinctValuesResponse(
                    success=False,
                    field=field,
                    values=[],
                    count=0
                )

            if column_name not in df.columns:
                return MXDistinctValuesResponse(
                    success=False,
                    field=field,
                    values=[],
                    count=0
                )

            # Get unique values
            values = df[column_name].dropna().astype(str).str.strip()
            values = values[values != ""]
            unique_values = sorted(values.unique())[:limit]

            return MXDistinctValuesResponse(
                success=True,
                field=field,
                values=list(unique_values),
                count=len(unique_values)
            )

        except Exception as e:
            logger.error(f"Error obteniendo valores distintos MX: {e}", exc_info=True)
            return MXDistinctValuesResponse(
                success=False,
                field=field,
                values=[],
                count=0
            )

    def get_operations_by_rfc(
        self,
        rfc: str,
        limit: int = 100
    ) -> MXDistinctValuesResponse:
        """
        Get distinct operation codes for a specific RFC.

        Args:
            rfc: RFC to filter by
            limit: Maximum number of values to return

        Returns:
            MXDistinctValuesResponse with unique operation codes for the RFC
        """
        try:
            df = self._load_excel_from_drive()

            rfc_col = self.COLUMN_MAPPING.get("rfc_receptor")
            operacion_col = self.COLUMN_MAPPING.get("codigo_operacion")

            if not rfc_col or not operacion_col:
                return MXDistinctValuesResponse(
                    success=False,
                    field="operacion",
                    values=[],
                    count=0
                )

            if rfc_col not in df.columns or operacion_col not in df.columns:
                return MXDistinctValuesResponse(
                    success=False,
                    field="operacion",
                    values=[],
                    count=0
                )

            rfc_search = rfc.strip().upper()

            # Filter by RFC (partial match)
            rfc_mask = df[rfc_col].astype(str).str.upper().str.contains(rfc_search, case=False, na=False)
            filtered_df = df[rfc_mask]

            # Get unique operations
            operations = filtered_df[operacion_col].dropna().astype(str).str.strip()
            operations = operations[operations != ""]
            unique_operations = sorted(operations.unique())[:limit]

            return MXDistinctValuesResponse(
                success=True,
                field="operacion",
                values=list(unique_operations),
                count=len(unique_operations)
            )

        except Exception as e:
            logger.error(f"Error obteniendo operaciones por RFC MX: {e}", exc_info=True)
            return MXDistinctValuesResponse(
                success=False,
                field="operacion",
                values=[],
                count=0
            )

    def clear_cache(self) -> None:
        """Clear the cached Excel data (both sheets)."""
        self._cached_facturas = None
        self._cached_complementos = None
        self._cache_timestamp = None
        logger.info("Cache de filtros MX limpiado (ambas hojas)")


# Singleton instance
_filter_service_mx_instance: Optional[MXFilterService] = None


def get_filter_service_mx() -> MXFilterService:
    """
    Obtiene la instancia singleton del servicio de filtrado MX.

    Returns:
        MXFilterService: Instancia del servicio.
    """
    global _filter_service_mx_instance
    if _filter_service_mx_instance is None:
        _filter_service_mx_instance = MXFilterService()
    return _filter_service_mx_instance
