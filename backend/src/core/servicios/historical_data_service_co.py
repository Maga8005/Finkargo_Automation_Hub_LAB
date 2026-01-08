"""
Historical Data Service for Colombia (CO)

Service for reading and processing the historical invoice control file
("Archivo control facturacion mensual Finkargo Def.xlsx") to:
1. Extract all invoice numbers for cache population
2. Optionally sync data to the master report file

This file is READ-ONLY - we never modify it.
"""

import io
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import pandas as pd

from src.core.servicios.google_drive_service_co import get_drive_service_co

logger = logging.getLogger(__name__)


@dataclass
class HistoricalRecord:
    """Represents a record from the historical Excel file."""
    codigo_operacion: Optional[str] = None
    fecha: Optional[str] = None
    numero_factura: Optional[str] = None
    nit: Optional[str] = None
    moneda: Optional[str] = None
    valor_costos_fijos: Optional[float] = None
    seguro_iva: Optional[float] = None
    int_corriente: Optional[float] = None
    int_mora: Optional[float] = None
    retencion_fuente: Optional[float] = None
    valor_neto: Optional[float] = None
    hoja_origen: Optional[str] = None


class HistoricalDataServiceCO:
    """
    Service for processing the historical invoice control file.

    The file "Archivo control facturacion mensual Finkargo Def.xlsx" contains:
    - Sheet "Relacion facturas Costos Fijos" (same as master)
    - Sheet "Relación facturas mandato" (same as master)
    - Sheet "Cesion" (additional historical data)

    Note: Does NOT have "Otros Valor" column (unlike the master report).
    """

    # Sheet names in historical file (exact names from Excel)
    # Hoja 2: "Relacion facturas costos fijos" (lowercase 'c' and 'f')
    # Hoja 8: "Relacion facturas mandato" (no accent on 'o')
    SHEET_COSTOS_FIJOS = "Relacion facturas costos fijos"
    SHEET_MANDATO = "Relacion facturas mandato"
    SHEET_CESION = "Cesion"

    # Column mappings (same as filter_service_co but without otros_valor)
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
    }

    # Cesion columns - uses English names
    CESION_COLUMNS = {
        "numero_factura": "# Invoice",  # English name in Cesion sheet
    }

    def __init__(self):
        """Initialize the historical data service."""
        self.drive_service = get_drive_service_co()
        self._cached_data: Optional[Dict[str, pd.DataFrame]] = None

    def _load_historical_excel(self) -> Dict[str, pd.DataFrame]:
        """
        Download and read the historical Excel file from Google Drive.

        Returns:
            Dict with sheet names as keys and DataFrames as values.

        Raises:
            ValueError: If file not found or cannot be read.
        """
        if self._cached_data is not None:
            logger.debug("Using cached historical Excel data")
            return self._cached_data

        logger.info("Descargando archivo histórico de Google Drive CO...")
        excel_bytes = self.drive_service.download_historical_excel()

        if not excel_bytes:
            raise ValueError(
                "No se encontró el archivo histórico de facturación CO en Google Drive. "
                f"Buscando: {self.drive_service.historical_excel_name}"
            )

        logger.info(f"Archivo histórico descargado: {len(excel_bytes)} bytes")

        # Read Excel into DataFrames
        excel_buffer = io.BytesIO(excel_bytes)
        result = {}

        try:
            # Read only the main sheets (Cesion not needed)
            # Note: Historical file has 2 header rows (title + column names), so header=2
            for sheet_name in [self.SHEET_COSTOS_FIJOS, self.SHEET_MANDATO]:
                try:
                    excel_buffer.seek(0)
                    # Skip first 2 rows (empty + title), use row 3 as header
                    df = pd.read_excel(excel_buffer, sheet_name=sheet_name, header=2)
                    result[sheet_name] = df
                    logger.info(f"Hoja '{sheet_name}': {len(df)} filas, columnas: {list(df.columns)[:5]}...")
                except Exception as e:
                    logger.warning(f"No se pudo leer hoja '{sheet_name}': {e}")
                    continue

            if not result:
                raise ValueError("No se pudo leer ninguna hoja del archivo histórico")

            self._cached_data = result
            return result

        except Exception as e:
            logger.error(f"Error leyendo archivo histórico Excel: {e}", exc_info=True)
            raise ValueError(f"Error al leer el archivo histórico Excel: {str(e)}")

    def get_all_invoice_numbers(self) -> List[str]:
        """
        Extract all unique invoice numbers from the historical file.
        Reads from all three sheets: Costos Fijos, Mandato, and Cesion.

        Returns:
            List[str]: Unique invoice numbers found.
        """
        try:
            excel_data = self._load_historical_excel()
            all_invoice_numbers: Set[str] = set()

            # Process each sheet (Cesion not needed)
            sheet_configs = [
                (self.SHEET_COSTOS_FIJOS, self.COSTOS_FIJOS_COLUMNS),
                (self.SHEET_MANDATO, self.MANDATO_COLUMNS),
            ]

            for sheet_name, col_map in sheet_configs:
                if sheet_name not in excel_data:
                    logger.warning(f"Hoja '{sheet_name}' no encontrada en archivo histórico")
                    continue

                df = excel_data[sheet_name]
                factura_col = col_map.get("numero_factura", "# Factura")

                # Try to find the invoice column - prioritize exact match first
                actual_col = None

                # First try exact match
                if factura_col in df.columns:
                    actual_col = factura_col
                else:
                    # Then try common variations
                    for col in df.columns:
                        col_lower = col.lower().strip()
                        # Look for columns that are specifically invoice number columns
                        if col_lower in ["# factura", "#factura", "# invoice", "#invoice", "numero factura", "numero_factura"]:
                            actual_col = col
                            break

                if actual_col is None:
                    logger.warning(f"Columna de factura no encontrada en '{sheet_name}'. Columnas: {list(df.columns)}")
                    continue

                logger.info(f"[{sheet_name}] Usando columna: '{actual_col}'")

                # Extract invoice numbers
                invoices = df[actual_col].dropna().astype(str).str.strip()
                invoices = invoices[invoices != ""]
                invoices = invoices[~invoices.str.lower().isin(["nan", "none", ""])]

                count_before = len(all_invoice_numbers)
                all_invoice_numbers.update(invoices.unique())
                count_added = len(all_invoice_numbers) - count_before

                logger.info(f"[{sheet_name}] Encontradas {len(invoices)} facturas, {count_added} nuevas únicas")

            invoice_list = list(all_invoice_numbers)
            logger.info(f"[TOTAL] {len(invoice_list)} números de factura únicos del archivo histórico")
            return invoice_list

        except Exception as e:
            logger.error(f"Error extrayendo números de factura del histórico: {e}", exc_info=True)
            return []

    def get_all_records(self) -> List[HistoricalRecord]:
        """
        Get all records from the historical file (for syncing to master report).

        Returns:
            List[HistoricalRecord]: All records from Costos Fijos and Mandato sheets.
        """
        try:
            excel_data = self._load_historical_excel()
            all_records: List[HistoricalRecord] = []

            # Process Costos Fijos
            if self.SHEET_COSTOS_FIJOS in excel_data:
                df = excel_data[self.SHEET_COSTOS_FIJOS]
                records = self._df_to_records(df, self.SHEET_COSTOS_FIJOS, self.COSTOS_FIJOS_COLUMNS)
                all_records.extend(records)
                logger.info(f"[Costos Fijos] {len(records)} registros procesados")

            # Process Mandato
            if self.SHEET_MANDATO in excel_data:
                df = excel_data[self.SHEET_MANDATO]
                records = self._df_to_records(df, self.SHEET_MANDATO, self.MANDATO_COLUMNS)
                all_records.extend(records)
                logger.info(f"[Mandato] {len(records)} registros procesados")

            logger.info(f"[TOTAL] {len(all_records)} registros del archivo histórico")
            return all_records

        except Exception as e:
            logger.error(f"Error obteniendo registros del histórico: {e}", exc_info=True)
            return []

    def _df_to_records(
        self,
        df: pd.DataFrame,
        sheet_name: str,
        col_map: Dict[str, str]
    ) -> List[HistoricalRecord]:
        """Convert DataFrame rows to HistoricalRecord objects."""
        records = []

        def safe_get(row, key: str, as_float: bool = False):
            col_name = col_map.get(key)
            if not col_name or col_name not in row.index:
                return None
            val = row[col_name]
            if pd.isna(val):
                return None
            if as_float:
                try:
                    if isinstance(val, (int, float)):
                        result = float(val)
                        return result if result != 0 else None
                    str_val = str(val).replace(",", "").strip()
                    if str_val in ("", "0", "0.0"):
                        return None
                    return float(str_val)
                except (ValueError, TypeError):
                    return None
            return str(val) if val else None

        for _, row in df.iterrows():
            try:
                record = HistoricalRecord(
                    codigo_operacion=safe_get(row, "codigo_operacion"),
                    fecha=safe_get(row, "fecha"),
                    numero_factura=safe_get(row, "numero_factura"),
                    nit=safe_get(row, "nit"),
                    moneda=safe_get(row, "moneda"),
                    valor_costos_fijos=safe_get(row, "valor_costos_fijos", as_float=True),
                    seguro_iva=safe_get(row, "seguro_iva", as_float=True),
                    int_corriente=safe_get(row, "int_corriente", as_float=True),
                    int_mora=safe_get(row, "int_mora", as_float=True),
                    retencion_fuente=safe_get(row, "retencion_fuente", as_float=True),
                    valor_neto=safe_get(row, "valor_neto", as_float=True),
                    hoja_origen=sheet_name,
                )
                # Only add records with valid invoice number
                if record.numero_factura:
                    records.append(record)
            except Exception as e:
                logger.warning(f"Error convirtiendo fila a record: {e}")
                continue

        return records

    def clear_cache(self) -> None:
        """Clear the cached Excel data."""
        self._cached_data = None
        logger.info("Cache del archivo histórico CO limpiado")


# Singleton instance
_historical_service_instance: Optional[HistoricalDataServiceCO] = None


def get_historical_data_service_co() -> HistoricalDataServiceCO:
    """
    Get singleton instance of the historical data service.

    Returns:
        HistoricalDataServiceCO: Service instance.
    """
    global _historical_service_instance
    if _historical_service_instance is None:
        _historical_service_instance = HistoricalDataServiceCO()
    return _historical_service_instance
