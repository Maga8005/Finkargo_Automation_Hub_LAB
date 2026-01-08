"""
Filter Service for Colombia (CO)

Servicio para consultar y filtrar datos del Excel maestro de facturación CO
almacenado en Google Drive.

Soporta filtros por:
- Operación(es) + rango de fecha
- NIT + rango de fecha
- NIT + operaciones + rango de fecha (combinación)
"""

import io
import logging
from datetime import date, datetime
from typing import List, Dict, Optional, Any
import pandas as pd

from src.core.servicios.google_drive_service_co import get_drive_service_co
from src.interface.finance_dtos_co import (
    COFilterRequest,
    COFilterResponse,
    COFilteredRecord,
    CODistinctValuesResponse,
)

logger = logging.getLogger(__name__)


class COFilterService:
    """
    Servicio para filtrar datos del Excel maestro de Colombia.

    Lee el archivo Reporte_Facturacion_CO_2025.xlsx desde Google Drive
    y permite aplicar filtros por operación, NIT y rango de fechas.
    """

    # Column mappings for each sheet
    COSTOS_FIJOS_COLUMNS = {
        "codigo_operacion": "Codigo del desembolso",
        "fecha": "Fecha Facturacion",
        "numero_factura": "# Factura",
        "nit": "Nit",
        "moneda": "Moneda",
        "valor_costos_fijos": "Valor Costos Fijos",
        "seguro_iva": "Seguro + Iva",
        "int_corriente": "Int. Corriente Facturado FK",
        "int_mora": "Int. Mora Facturado FK",
        "retencion_fuente": "(-) Retencion en la Fuente",
        "valor_neto": "Valor Neto Facturado",
        "otros_valor": "Otros Valor",
    }

    MANDATO_COLUMNS = {
        "codigo_operacion": "Codigo del desembolso",
        "mes_facturacion": "Mes facturacion",
        "int_corriente": "Interes Corriente Facturado",
        "int_mora": "Interes Mora Facturado Mandato",
        "valor_neto": "Valor Neto Facturado",
        "fecha": "Fecha Factura",
        "numero_factura": "# Factura",
        "moneda": "Moneda",
        "nit": "Nit",
        "otros_valor": "Otros Valor",
    }

    SHEET_COSTOS_FIJOS = "Relacion facturas Costos Fijos"
    SHEET_MANDATO = "Relación facturas mandato"

    def __init__(self):
        """Inicializa el servicio de filtrado."""
        self.drive_service = get_drive_service_co()
        self._cached_data: Optional[Dict[str, pd.DataFrame]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes cache

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if self._cached_data is None or self._cache_timestamp is None:
            return False
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl_seconds

    def _load_excel_from_drive(self) -> Dict[str, pd.DataFrame]:
        """
        Descarga y lee el Excel maestro desde Google Drive.

        Returns:
            Dict with sheet names as keys and DataFrames as values.

        Raises:
            ValueError: If file not found or cannot be read.
        """
        # Check cache first
        if self._is_cache_valid():
            logger.debug("Using cached Excel data")
            return self._cached_data

        logger.info("Descargando Excel maestro de Google Drive CO...")
        excel_bytes = self.drive_service.download_master_excel()

        if not excel_bytes:
            raise ValueError(
                "No se encontró el archivo maestro de facturación CO en Google Drive. "
                "Primero debe procesar archivos para generar el reporte."
            )

        logger.info(f"Excel descargado: {len(excel_bytes)} bytes")

        # Read Excel into DataFrames
        excel_buffer = io.BytesIO(excel_bytes)

        try:
            # Read both sheets - don't force dtype=str to preserve numeric values
            df_costos = pd.read_excel(
                excel_buffer,
                sheet_name=self.SHEET_COSTOS_FIJOS
            )
            logger.info(f"Hoja '{self.SHEET_COSTOS_FIJOS}': {len(df_costos)} filas, columnas: {list(df_costos.columns)}")

            # Log sample of numeric columns for debugging
            if len(df_costos) > 0:
                sample_row = df_costos.iloc[0]
                logger.info(f"[Costos Fijos] Columnas disponibles: {list(df_costos.columns)}")
                logger.info(f"[Costos Fijos] Primera fila - Valor Costos Fijos: {sample_row.get('Valor Costos Fijos')} (type: {type(sample_row.get('Valor Costos Fijos'))}), "
                           f"Int. Corriente: {sample_row.get('Int. Corriente Facturado FK')} (type: {type(sample_row.get('Int. Corriente Facturado FK'))}), "
                           f"Valor Neto: {sample_row.get('Valor Neto Facturado')} (type: {type(sample_row.get('Valor Neto Facturado'))}), "
                           f"Otros Valor: {sample_row.get('Otros Valor')} (type: {type(sample_row.get('Otros Valor'))})")

            excel_buffer.seek(0)  # Reset buffer position

            df_mandato = pd.read_excel(
                excel_buffer,
                sheet_name=self.SHEET_MANDATO
            )
            logger.info(f"Hoja '{self.SHEET_MANDATO}': {len(df_mandato)} filas, columnas: {list(df_mandato.columns)}")

            # Cache the data
            self._cached_data = {
                self.SHEET_COSTOS_FIJOS: df_costos,
                self.SHEET_MANDATO: df_mandato
            }
            self._cache_timestamp = datetime.now()

            return self._cached_data

        except Exception as e:
            logger.error(f"Error leyendo Excel: {e}", exc_info=True)
            raise ValueError(f"Error al leer el archivo Excel: {str(e)}")

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse date string to date object.
        Handles multiple formats: YYYY-MM-DD, DD/MM/YYYY, etc.
        """
        if not date_str or pd.isna(date_str):
            return None

        date_str = str(date_str).strip()

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
        sheet_name: str,
        request: COFilterRequest
    ) -> pd.DataFrame:
        """
        Apply filters to a DataFrame.

        Args:
            df: DataFrame to filter
            sheet_name: Name of the sheet being filtered
            request: Filter request with criteria

        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df

        result_df = df.copy()

        # Determine column mapping based on sheet
        if sheet_name == self.SHEET_COSTOS_FIJOS:
            col_map = self.COSTOS_FIJOS_COLUMNS
        else:
            col_map = self.MANDATO_COLUMNS

        # Filter by operaciones (codigo_operacion)
        if request.operaciones and len(request.operaciones) > 0:
            operacion_col = col_map.get("codigo_operacion")
            if operacion_col and operacion_col in result_df.columns:
                # Convert both to uppercase for case-insensitive matching
                operaciones_upper = [op.upper().strip() for op in request.operaciones]
                result_df = result_df[
                    result_df[operacion_col].astype(str).str.upper().str.strip().isin(operaciones_upper)
                ]
                logger.debug(f"Después de filtro operaciones: {len(result_df)} filas")

        # Filter by NIT
        if request.nit:
            nit_col = col_map.get("nit")
            if nit_col and nit_col in result_df.columns:
                nit_search = request.nit.strip()
                # Partial match (contains)
                result_df = result_df[
                    result_df[nit_col].astype(str).str.contains(nit_search, case=False, na=False)
                ]
                logger.debug(f"Después de filtro NIT: {len(result_df)} filas")

        # Filter by date range
        if request.fecha_inicio or request.fecha_fin:
            fecha_col = col_map.get("fecha")
            if fecha_col and fecha_col in result_df.columns:
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
                logger.debug(f"Después de filtro fecha: {len(result_df)} filas")

        return result_df

    def _df_to_records(
        self,
        df: pd.DataFrame,
        sheet_name: str
    ) -> List[COFilteredRecord]:
        """
        Convert DataFrame rows to COFilteredRecord objects.
        """
        records = []

        # Column mapping based on sheet
        if sheet_name == self.SHEET_COSTOS_FIJOS:
            col_map = self.COSTOS_FIJOS_COLUMNS
        else:
            col_map = self.MANDATO_COLUMNS

        # Log available columns for debugging
        logger.info(f"Sheet '{sheet_name}' columns: {list(df.columns)}")
        logger.info(f"Expected column mapping: {col_map}")

        # Track if we've logged debug info
        logged_debug = False

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
                            # Handle both numeric and string values
                            if isinstance(val, (int, float)):
                                result = float(val)
                                # Return None for zero values to avoid showing $0
                                return result if result != 0 else None
                            # Try parsing string
                            str_val = str(val).replace(",", "").strip()
                            if str_val == "" or str_val == "0" or str_val == "0.0":
                                return None
                            return float(str_val)
                        except (ValueError, TypeError):
                            return None
                    # Convert to string and remove trailing .0 for numeric IDs (like NIT)
                    str_val = str(val) if val else None
                    if str_val and str_val.endswith('.0'):
                        str_val = str_val[:-2]
                    return str_val

                # Log raw values for first row
                if not logged_debug:
                    logged_debug = True
                    logger.info(f"[_df_to_records] Sheet '{sheet_name}' - Raw row sample:")
                    for key in ["valor_costos_fijos", "int_corriente", "int_mora", "valor_neto", "otros_valor"]:
                        col_name = col_map.get(key)
                        if col_name and col_name in row.index:
                            raw_val = row[col_name]
                            logger.info(f"  {key} ({col_name}): {raw_val} (type: {type(raw_val).__name__})")

                record = COFilteredRecord(
                    codigo_operacion=safe_get("codigo_operacion"),
                    fecha=safe_get("fecha"),
                    numero_factura=safe_get("numero_factura"),
                    nit=safe_get("nit"),
                    moneda=safe_get("moneda"),
                    valor_costos_fijos=safe_get("valor_costos_fijos", as_float=True),
                    seguro_iva=safe_get("seguro_iva", as_float=True),
                    int_corriente=safe_get("int_corriente", as_float=True),
                    int_mora=safe_get("int_mora", as_float=True),
                    retencion_fuente=safe_get("retencion_fuente", as_float=True),
                    valor_neto=safe_get("valor_neto", as_float=True),
                    otros_valor=safe_get("otros_valor", as_float=True),
                    hoja_origen=sheet_name,
                )
                records.append(record)

                # Log first few records for debugging
                if len(records) <= 3:
                    logger.info(f"Sample record {len(records)}: valor_costos_fijos={record.valor_costos_fijos}, "
                               f"int_corriente={record.int_corriente}, valor_neto={record.valor_neto}, "
                               f"otros_valor={record.otros_valor}")
            except Exception as e:
                logger.warning(f"Error convirtiendo fila a record: {e}")
                continue

        return records

    def filter_records(self, request: COFilterRequest) -> COFilterResponse:
        """
        Filter records from the CO master Excel based on request criteria.

        Args:
            request: Filter criteria

        Returns:
            COFilterResponse with matching records
        """
        try:
            # Load Excel data from Drive
            excel_data = self._load_excel_from_drive()

            all_records: List[COFilteredRecord] = []
            sheets_searched: List[str] = []
            filters_applied: Dict[str, str] = {}

            # Build filters_applied summary
            if request.operaciones:
                filters_applied["operaciones"] = ", ".join(request.operaciones)
            if request.nit:
                filters_applied["nit"] = request.nit
            if request.fecha_inicio or request.fecha_fin:
                fecha_str = ""
                if request.fecha_inicio:
                    fecha_str = str(request.fecha_inicio)
                if request.fecha_fin:
                    fecha_str += f" a {request.fecha_fin}" if fecha_str else str(request.fecha_fin)
                filters_applied["fecha_rango"] = fecha_str

            # Determine which sheets to search
            sheets_to_search = []
            if request.hoja:
                if request.hoja.lower() == "costos_fijos":
                    sheets_to_search = [self.SHEET_COSTOS_FIJOS]
                elif request.hoja.lower() == "mandato":
                    sheets_to_search = [self.SHEET_MANDATO]
                else:
                    sheets_to_search = [self.SHEET_COSTOS_FIJOS, self.SHEET_MANDATO]
            else:
                # Search both sheets by default
                sheets_to_search = [self.SHEET_COSTOS_FIJOS, self.SHEET_MANDATO]

            # Apply filters to each sheet
            for sheet_name in sheets_to_search:
                if sheet_name not in excel_data:
                    logger.warning(f"Sheet '{sheet_name}' not found in Excel")
                    continue

                df = excel_data[sheet_name]
                sheets_searched.append(sheet_name)

                # Apply filters
                filtered_df = self._apply_filters(df, sheet_name, request)

                # Convert to records
                records = self._df_to_records(filtered_df, sheet_name)
                all_records.extend(records)

                logger.info(f"Sheet '{sheet_name}': {len(records)} registros después de filtros")

            # Build response
            message = f"Se encontraron {len(all_records)} registros"
            if not all_records:
                message = "No se encontraron registros con los filtros especificados"

            return COFilterResponse(
                success=True,
                total_records=len(all_records),
                records=all_records,
                filters_applied=filters_applied,
                sheets_searched=sheets_searched,
                message=message
            )

        except ValueError as e:
            logger.error(f"Error de validación en filtro: {e}")
            return COFilterResponse(
                success=False,
                total_records=0,
                records=[],
                filters_applied={},
                sheets_searched=[],
                message=str(e)
            )
        except Exception as e:
            logger.error(f"Error inesperado en filtro: {e}", exc_info=True)
            return COFilterResponse(
                success=False,
                total_records=0,
                records=[],
                filters_applied={},
                sheets_searched=[],
                message=f"Error al consultar datos: {str(e)}"
            )

    def get_distinct_values(
        self,
        field: str,
        limit: int = 100
    ) -> CODistinctValuesResponse:
        """
        Get distinct values for a field (for autocomplete).

        Args:
            field: Field name to get distinct values for ('nit', 'operacion')
            limit: Maximum number of values to return

        Returns:
            CODistinctValuesResponse with unique values
        """
        try:
            excel_data = self._load_excel_from_drive()

            all_values: set = set()

            # Map field to column names
            field_mapping = {
                "nit": "Nit",
                "operacion": "Codigo del desembolso",
                "codigo_operacion": "Codigo del desembolso",
            }

            column_name = field_mapping.get(field.lower())
            if not column_name:
                return CODistinctValuesResponse(
                    success=False,
                    field=field,
                    values=[],
                    count=0
                )

            # Collect values from both sheets
            for sheet_name, df in excel_data.items():
                if column_name in df.columns:
                    values = df[column_name].dropna().astype(str).str.strip()
                    # Remove trailing .0 from numeric values (e.g., "800065887.0" -> "800065887")
                    values = values.str.replace(r'\.0$', '', regex=True)
                    values = values[values != ""]
                    all_values.update(values.unique())

            # Sort and limit
            sorted_values = sorted(all_values)[:limit]

            return CODistinctValuesResponse(
                success=True,
                field=field,
                values=sorted_values,
                count=len(sorted_values)
            )

        except Exception as e:
            logger.error(f"Error obteniendo valores distintos: {e}", exc_info=True)
            return CODistinctValuesResponse(
                success=False,
                field=field,
                values=[],
                count=0
            )

    def get_operations_by_nit(
        self,
        nit: str,
        limit: int = 100
    ) -> CODistinctValuesResponse:
        """
        Get distinct operation codes for a specific NIT.

        Args:
            nit: Client NIT to filter by
            limit: Maximum number of values to return

        Returns:
            CODistinctValuesResponse with unique operation codes for the NIT
        """
        try:
            excel_data = self._load_excel_from_drive()

            all_operations: set = set()
            nit_search = nit.strip()

            # Collect operations from both sheets where NIT matches
            for sheet_name, df in excel_data.items():
                # Get column names based on sheet
                if sheet_name == self.SHEET_COSTOS_FIJOS:
                    col_map = self.COSTOS_FIJOS_COLUMNS
                else:
                    col_map = self.MANDATO_COLUMNS

                nit_col = col_map.get("nit")
                operacion_col = col_map.get("codigo_operacion")

                if nit_col and operacion_col and nit_col in df.columns and operacion_col in df.columns:
                    # Clean NIT column (remove .0 suffix) for comparison
                    nit_values = df[nit_col].astype(str).str.replace(r'\.0$', '', regex=True)
                    # Filter by NIT (partial match)
                    nit_mask = nit_values.str.contains(nit_search, case=False, na=False)
                    filtered_df = df[nit_mask]

                    # Get unique operations
                    operations = filtered_df[operacion_col].dropna().astype(str).str.strip()
                    operations = operations[operations != ""]
                    all_operations.update(operations.unique())

            # Sort and limit
            sorted_operations = sorted(all_operations)[:limit]

            return CODistinctValuesResponse(
                success=True,
                field="operacion",
                values=sorted_operations,
                count=len(sorted_operations)
            )

        except Exception as e:
            logger.error(f"Error obteniendo operaciones por NIT: {e}", exc_info=True)
            return CODistinctValuesResponse(
                success=False,
                field="operacion",
                values=[],
                count=0
            )

    def clear_cache(self) -> None:
        """Clear the cached Excel data."""
        self._cached_data = None
        self._cache_timestamp = None
        logger.info("Cache de filtros CO limpiado")

    def get_all_records(self) -> List[COFilteredRecord]:
        """
        Get ALL records from the CO master Excel (no filtering).
        Used for precaching Drive file IDs.

        Returns:
            List[COFilteredRecord]: All records from both sheets.
        """
        try:
            # Load Excel data from Drive
            excel_data = self._load_excel_from_drive()

            all_records: List[COFilteredRecord] = []

            # Process both sheets
            for sheet_name in [self.SHEET_COSTOS_FIJOS, self.SHEET_MANDATO]:
                if sheet_name not in excel_data:
                    logger.warning(f"Sheet '{sheet_name}' not found in Excel")
                    continue

                df = excel_data[sheet_name]

                # Convert to records (no filtering)
                records = self._df_to_records(df, sheet_name)
                all_records.extend(records)

                logger.info(f"[get_all_records] Sheet '{sheet_name}': {len(records)} registros")

            logger.info(f"[get_all_records] Total: {len(all_records)} registros de ambas hojas")
            return all_records

        except Exception as e:
            logger.error(f"Error getting all records: {e}", exc_info=True)
            return []

    def get_all_invoice_numbers(self) -> List[str]:
        """
        Get all unique invoice numbers (numero_factura) from the master Excel.
        Used for precaching Drive file IDs.

        Returns:
            List[str]: Unique invoice numbers.
        """
        try:
            all_records = self.get_all_records()

            # Extract unique invoice numbers
            invoice_numbers = set()
            for record in all_records:
                if record.numero_factura:
                    invoice_numbers.add(record.numero_factura)

            invoice_list = list(invoice_numbers)
            logger.info(f"[get_all_invoice_numbers] Found {len(invoice_list)} unique invoice numbers")
            return invoice_list

        except Exception as e:
            logger.error(f"Error getting invoice numbers: {e}", exc_info=True)
            return []


# Singleton instance
_filter_service_co_instance: Optional[COFilterService] = None


def get_filter_service_co() -> COFilterService:
    """
    Obtiene la instancia singleton del servicio de filtrado CO.

    Returns:
        COFilterService: Instancia del servicio.
    """
    global _filter_service_co_instance
    if _filter_service_co_instance is None:
        _filter_service_co_instance = COFilterService()
    return _filter_service_co_instance
