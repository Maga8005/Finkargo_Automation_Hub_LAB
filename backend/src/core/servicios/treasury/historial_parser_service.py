"""
Historial Parser Service for Treasury Declaration-Historial Matching.

Parses Historial de Pagos Excel files with column mapping variations
and returns structured records for grouping and matching.
"""

import pandas as pd
import io
import logging
import unicodedata
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from fastapi import UploadFile

from src.interface.treasury_matching_dtos import (
    HistorialRecord,
    ColumnValidationStatus,
)

logger = logging.getLogger(__name__)


# Column mappings to handle variations in column names
COLUMN_MAPPINGS = {
    'cliente': ['Cliente', 'CLIENTE', 'client', 'Cliente (Razón Social)'],
    'identificacion_cliente': ['Identificacion del cliente', 'Identificación del cliente', 'NIT', 'Identificación', 'IDENTIFICACION DEL CLIENTE'],
    'codigo_desembolso': ['Codigo de desembolso', 'Código de desembolso', 'CODIGO DE DESEMBOLSO'],
    'codigo_recaudo': ['Codigo de recaudo', 'Código de recaudo', 'CODIGO DE RECAUDO'],
    'numero_factura': ['Numero de factura', 'Número de factura', 'NUMERO DE FACTURA'],
    'fecha_desembolso': ['Fecha de desembolso', 'FECHA DE DESEMBOLSO'],
    'fecha_vencimiento': ['Fecha de vencimiento', 'FECHA DE VENCIMIENTO'],
    'valor_desembolso': ['Valor del desembolso', 'VALOR DEL DESEMBOLSO'],
    'estado_desembolso': ['Estado del desembolso', 'ESTADO DEL DESEMBOLSO'],
    'fecha_pago': ['Fecha de pago', 'Fecha Pago', 'FechaPago', 'Fecha Aplicacion', 'FECHA DE PAGO'],
    'total_pagado': ['Total pagado', 'TOTAL PAGADO'],
    'moneda': ['Moneda', 'MONEDA'],
    'medio_pago': ['Medio de pago', 'MEDIO DE PAGO'],
    'tasa_cambio': ['Tasa de cambio de FK/en linea', 'Tasa de cambio', 'TASA DE CAMBIO'],
    'total_pagado_usd': ['Total pagado [USD]', 'Total pagado USD', 'TOTAL PAGADO [USD]'],
    'capital': ['Capital', 'CAPITAL', 'Monto Capital'],
    'declaracion_cambio_numero': ['Declaracion de Cambio Numero', 'Declaración de Cambio Número', 'DC Numero', 'DECLARACION DE CAMBIO NUMERO'],
    'dc_nombre': ['DC Nombre', 'Nombre DC', 'PDF Nombre', 'DC NOMBRE'],
    'dim': ['DIM', 'Dim'],
    'factura_final': ['Factura Final', 'FACTURA FINAL'],
}

# Required columns that must be present for matching
REQUIRED_COLUMNS = ['cliente', 'fecha_pago', 'capital', 'identificacion_cliente']


class HistorialParserService:
    """
    Service for parsing Historial de Pagos Excel files.

    Handles column mapping variations, date parsing, and data normalization.
    """

    def __init__(self):
        """Initialize the parser service."""
        self.preview_rows = 5

    def _normalize_text(self, text: Optional[str]) -> str:
        """
        Normalize text for matching: uppercase, remove accents, trim whitespace.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Convert to string if not already
        text = str(text).strip()

        # Uppercase
        text = text.upper()

        # Remove accents
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))

        # Trim extra whitespace
        text = ' '.join(text.split())

        return text

    def _normalize_customer_name(self, name: Optional[str]) -> str:
        """
        Normalize customer name for matching.

        Removes common suffixes like SAS, SA, LTDA, S.A.S., etc.

        Args:
            name: Customer name to normalize

        Returns:
            Normalized customer name
        """
        if not name:
            return ""

        normalized = self._normalize_text(name)

        # Remove common Colombian company suffixes
        suffixes_to_remove = [
            ' S.A.S.', ' SAS', ' S.A.S', ' S A S',
            ' S.A.', ' SA', ' S A',
            ' LTDA.', ' LTDA', ' LIMITADA',
            ' E.U.', ' EU',
            ' & CIA', ' Y CIA', ' CIA',
            ' S EN C', ' S. EN C.', ' S EN C.',
            ' S.C.A.', ' SCA',
        ]

        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
            elif normalized.endswith(suffix.replace('.', '')):
                normalized = normalized[:-len(suffix.replace('.', ''))]

        return normalized.strip()

    def _find_column(self, df_columns: List[str], internal_name: str) -> Optional[str]:
        """
        Find a column in the DataFrame matching the internal name.

        Args:
            df_columns: List of column names in the DataFrame
            internal_name: Internal column identifier

        Returns:
            Actual column name found, or None
        """
        variations = COLUMN_MAPPINGS.get(internal_name, [])

        # Create normalized lookup
        df_columns_normalized = {
            self._normalize_text(col): col for col in df_columns
        }

        for variation in variations:
            normalized_variation = self._normalize_text(variation)
            if normalized_variation in df_columns_normalized:
                return df_columns_normalized[normalized_variation]

        return None

    def _parse_date(self, date_value) -> Optional[str]:
        """
        Parse date value to ISO format (YYYY-MM-DD).

        Handles multiple date formats commonly used in Colombian Excel files.

        Args:
            date_value: Raw date value from Excel

        Returns:
            Date in ISO format, or None if invalid
        """
        if pd.isna(date_value) or date_value is None:
            return None

        try:
            # Handle pandas Timestamp
            if isinstance(date_value, pd.Timestamp):
                return date_value.strftime("%Y-%m-%d")

            # Handle datetime
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d")

            # Handle string values
            date_str = str(date_value).strip()

            # Try common date formats
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%d-%m-%Y",
                "%Y/%m/%d",
                "%d.%m.%Y",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str.split()[0] if ' ' in date_str else date_str, fmt.split()[0])
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # If all parsing fails, return None
            logger.warning(f"Could not parse date: {date_value}")
            return None

        except Exception as e:
            logger.warning(f"Error parsing date {date_value}: {e}")
            return None

    def _parse_numeric(self, value) -> Optional[float]:
        """
        Parse numeric value, handling European format (comma as decimal).

        Args:
            value: Raw numeric value

        Returns:
            Float value, or None if invalid
        """
        if pd.isna(value) or value is None:
            return None

        try:
            # If already numeric
            if isinstance(value, (int, float)):
                return float(value)

            # Handle string values
            value_str = str(value).strip()

            # Remove currency symbols and whitespace
            value_str = value_str.replace('$', '').replace(' ', '')

            # Detect European format (8.111,43 vs 8,111.43)
            if ',' in value_str and '.' in value_str:
                last_comma = value_str.rfind(',')
                last_dot = value_str.rfind('.')
                if last_comma > last_dot:
                    # European: 8.111,43
                    value_str = value_str.replace('.', '').replace(',', '.')
                else:
                    # US: 8,111.43
                    value_str = value_str.replace(',', '')
            elif ',' in value_str:
                # Only comma - could be thousands separator or decimal
                # If there's exactly one comma and it's followed by 1-2 digits, treat as decimal
                comma_pos = value_str.rfind(',')
                after_comma = value_str[comma_pos + 1:]
                if len(after_comma) <= 2 and after_comma.isdigit():
                    value_str = value_str.replace(',', '.')
                else:
                    # Treat as thousands separator
                    value_str = value_str.replace(',', '')

            return float(value_str)

        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse numeric value: {value}, error: {e}")
            return None

    async def parse_historial(
        self,
        file: UploadFile
    ) -> Tuple[List[HistorialRecord], List[ColumnValidationStatus], List[str], List[Dict], pd.DataFrame]:
        """
        Parse Historial de Pagos Excel file.

        Args:
            file: Uploaded Excel file

        Returns:
            Tuple of (records, column_status, errors, preview_data, original_df)
        """
        logger.info("Parsing Historial de Pagos Excel file")

        records: List[HistorialRecord] = []
        column_status: List[ColumnValidationStatus] = []
        errors: List[str] = []
        preview_data: List[Dict] = []

        try:
            # Read file contents
            contents = await file.read()
            await file.seek(0)  # Reset for potential reuse

            # Load Excel file
            df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
            logger.info(f"Loaded Excel with {len(df)} rows and {len(df.columns)} columns")

            # Find columns
            column_mapping: Dict[str, Optional[str]] = {}
            for internal_name in COLUMN_MAPPINGS.keys():
                found_col = self._find_column(list(df.columns), internal_name)
                column_mapping[internal_name] = found_col

                # Track validation status for required columns
                if internal_name in REQUIRED_COLUMNS:
                    column_status.append(ColumnValidationStatus(
                        column_name=internal_name,
                        found=found_col is not None,
                        source_column=found_col
                    ))

            # Check required columns
            missing_required = [
                col for col in REQUIRED_COLUMNS
                if column_mapping.get(col) is None
            ]

            if missing_required:
                errors.append(f"Columnas requeridas no encontradas: {', '.join(missing_required)}")
                return records, column_status, errors, preview_data, df

            # Get preview data (first rows)
            for idx, row in df.head(self.preview_rows).iterrows():
                row_dict = {}
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val):
                        if isinstance(val, (pd.Timestamp, datetime)):
                            row_dict[col] = val.strftime("%Y-%m-%d")
                        else:
                            row_dict[col] = str(val)
                    else:
                        row_dict[col] = None
                preview_data.append(row_dict)

            # Parse each row
            for idx, row in df.iterrows():
                try:
                    row_number = int(idx) + 2  # Excel is 1-indexed and has header

                    # Get required fields
                    cliente_col = column_mapping['cliente']
                    fecha_pago_col = column_mapping['fecha_pago']
                    capital_col = column_mapping['capital']
                    identificacion_col = column_mapping['identificacion_cliente']

                    cliente = str(row[cliente_col]) if pd.notna(row[cliente_col]) else ""
                    fecha_pago_raw = row[fecha_pago_col] if pd.notna(row[fecha_pago_col]) else None
                    capital_raw = row[capital_col] if pd.notna(row[capital_col]) else None
                    identificacion = str(row[identificacion_col]) if pd.notna(row[identificacion_col]) else ""

                    # Skip rows with empty required fields
                    if not cliente or not fecha_pago_raw:
                        continue

                    # Parse date
                    fecha_pago = self._parse_date(fecha_pago_raw)
                    if not fecha_pago:
                        errors.append(f"Fila {row_number}: Fecha de pago inválida")
                        continue

                    # Parse capital
                    capital = self._parse_numeric(capital_raw)
                    if capital is None:
                        capital = 0.0

                    # Get optional fields
                    def get_value(internal_name: str) -> Optional[str]:
                        col = column_mapping.get(internal_name)
                        if col and col in row.index and pd.notna(row[col]):
                            return str(row[col])
                        return None

                    def get_numeric(internal_name: str) -> Optional[float]:
                        col = column_mapping.get(internal_name)
                        if col and col in row.index:
                            return self._parse_numeric(row[col])
                        return None

                    def get_date(internal_name: str) -> Optional[str]:
                        col = column_mapping.get(internal_name)
                        if col and col in row.index:
                            return self._parse_date(row[col])
                        return None

                    record = HistorialRecord(
                        row_number=row_number,
                        cliente=cliente,
                        cliente_normalized=self._normalize_customer_name(cliente),
                        identificacion_cliente=identificacion,
                        codigo_desembolso=get_value('codigo_desembolso'),
                        codigo_recaudo=get_value('codigo_recaudo'),
                        numero_factura=get_value('numero_factura'),
                        fecha_desembolso=get_date('fecha_desembolso'),
                        fecha_vencimiento=get_date('fecha_vencimiento'),
                        valor_desembolso=get_numeric('valor_desembolso'),
                        estado_desembolso=get_value('estado_desembolso'),
                        fecha_pago=fecha_pago,
                        total_pagado=get_numeric('total_pagado'),
                        moneda=get_value('moneda'),
                        medio_pago=get_value('medio_pago'),
                        tasa_cambio=get_numeric('tasa_cambio'),
                        total_pagado_usd=get_numeric('total_pagado_usd'),
                        capital=capital,
                        declaracion_cambio_numero=get_value('declaracion_cambio_numero'),
                        dc_nombre=get_value('dc_nombre'),
                        dim=get_value('dim'),
                        factura_final=get_value('factura_final'),
                    )

                    records.append(record)

                except Exception as e:
                    errors.append(f"Fila {int(idx) + 2}: Error al procesar - {str(e)}")
                    logger.warning(f"Error processing row {idx}: {e}")

            logger.info(f"Parsed {len(records)} records from {len(df)} rows")

            return records, column_status, errors, preview_data, df

        except Exception as e:
            logger.error(f"Error parsing Historial de Pagos: {e}")
            errors.append(f"Error al procesar archivo: {str(e)}")
            return records, column_status, errors, preview_data, pd.DataFrame()

    def get_column_mapping(self, df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """
        Get the column mapping for a DataFrame.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary mapping internal names to actual column names
        """
        column_mapping: Dict[str, Optional[str]] = {}
        for internal_name in COLUMN_MAPPINGS.keys():
            column_mapping[internal_name] = self._find_column(list(df.columns), internal_name)
        return column_mapping


# Singleton instance
historial_parser_service = HistorialParserService()
