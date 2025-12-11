"""
Combined Excel Service for Facturas + Complementos de Pago.

This service handles the validation and parsing of both invoice files
and payment supplement files, combining them into a single dataset.
"""

import pandas as pd
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from fastapi import UploadFile
import io
import uuid as uuid_lib

from src.interface.finance_dtos import (
    ExcelValidationError,
    CombinedRecord,
    CombinedUploadResponse,
    DocumentType
)

logger = logging.getLogger(__name__)


class CombinedExcelService:
    """
    Service for validating and parsing combined Excel files (facturas + complementos).

    Payment supplements are identified by:
    - tipo_comprobante containing "CPO1 - Pagos"
    - conceptos containing "COMPLEMENTO DE PAGO"
    """

    REQUIRED_COLUMNS = [
        'UUID',
        'CODIGO DE OPERACIÓN',
        'Conceptos',
        'Fecha emision',
        'RFC receptor',
        'Razon receptor',
        'SubTotal',
        'IVA Trasladado',
        'IVA Exento',
        'Total'
    ]

    OPTIONAL_COLUMNS = [
        'UUIDs relacionados',
        'Tipo'
    ]

    COLUMN_MAPPING = {
        'UUID': 'uuid',
        'CODIGO DE OPERACIÓN': 'codigo_operacion',
        'Conceptos': 'conceptos',
        'Fecha emision': 'fecha_emision',
        'RFC receptor': 'rfc_receptor',
        'Razon receptor': 'razon_receptor',
        'SubTotal': 'subtotal',
        'IVA Trasladado': 'iva_trasladado',
        'IVA Exento': 'iva_exento',
        'Total': 'total',
        'UUIDs relacionados': 'uuid_relacionados',
        'Tipo': 'tipo_comprobante'
    }

    def is_complemento_pago(self, tipo: Optional[str], conceptos: Optional[str]) -> bool:
        """
        Determine if a record is a payment supplement based on tipo and conceptos.

        Args:
            tipo: Value from 'Tipo' column
            conceptos: Value from 'Conceptos' column

        Returns:
            True if the record is a payment supplement
        """
        # Check tipo_comprobante for "CPO1 - Pagos"
        if tipo and isinstance(tipo, str):
            tipo_upper = tipo.upper()
            if 'CPO1' in tipo_upper or 'PAGO' in tipo_upper:
                return True

        # Check conceptos for "COMPLEMENTO DE PAGO"
        if conceptos and isinstance(conceptos, str):
            conceptos_upper = conceptos.upper()
            if 'COMPLEMENTO DE PAGO' in conceptos_upper:
                return True

        return False

    async def validate_combined_excel(
        self,
        facturas_file: Optional[UploadFile] = None,
        complementos_file: Optional[UploadFile] = None
    ) -> CombinedUploadResponse:
        """
        Validate and parse both facturas and complementos Excel files.

        Args:
            facturas_file: Excel file with invoice data
            complementos_file: Excel file with payment supplement data

        Returns:
            CombinedUploadResponse with parsed data from both files
        """
        session_id = str(uuid_lib.uuid4())

        facturas_data: List[CombinedRecord] = []
        facturas_errors: List[ExcelValidationError] = []
        facturas_total = 0
        facturas_valid = 0

        complementos_data: List[CombinedRecord] = []
        complementos_errors: List[ExcelValidationError] = []
        complementos_total = 0
        complementos_valid = 0

        # Process facturas file
        if facturas_file:
            logger.info(f"Processing facturas file: {facturas_file.filename}")
            facturas_data, facturas_errors, facturas_total, facturas_valid = await self._process_file(
                facturas_file,
                DocumentType.FACTURA
            )
            logger.info(f"Facturas processed: {facturas_valid}/{facturas_total} valid")

        # Process complementos file
        if complementos_file:
            logger.info(f"Processing complementos file: {complementos_file.filename}")
            complementos_data, complementos_errors, complementos_total, complementos_valid = await self._process_file(
                complementos_file,
                DocumentType.COMPLEMENTO_PAGO
            )
            logger.info(f"Complementos processed: {complementos_valid}/{complementos_total} valid")

        total_records = len(facturas_data) + len(complementos_data)
        success = (len(facturas_errors) == 0 and len(complementos_errors) == 0) or total_records > 0

        return CombinedUploadResponse(
            success=success,
            session_id=session_id,
            facturas_total_rows=facturas_total,
            facturas_valid_rows=facturas_valid,
            facturas_data=facturas_data,
            facturas_errors=facturas_errors,
            complementos_total_rows=complementos_total,
            complementos_valid_rows=complementos_valid,
            complementos_data=complementos_data,
            complementos_errors=complementos_errors,
            total_records=total_records
        )

    async def _process_file(
        self,
        file: UploadFile,
        default_doc_type: DocumentType
    ) -> Tuple[List[CombinedRecord], List[ExcelValidationError], int, int]:
        """
        Process a single Excel file.

        Args:
            file: The Excel file to process
            default_doc_type: Default document type for records

        Returns:
            Tuple of (records, errors, total_rows, valid_rows)
        """
        content = await file.read()
        await file.seek(0)  # Reset file pointer for potential reuse

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024
        if len(content) > max_size:
            return [], [ExcelValidationError(
                row=0,
                column="file",
                message="El archivo excede el tamaño máximo de 10MB"
            )], 0, 0

        # Read Excel
        try:
            if file.filename and file.filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            elif file.filename and file.filename.endswith('.xls'):
                df = pd.read_excel(io.BytesIO(content), engine='xlrd')
            else:
                return [], [ExcelValidationError(
                    row=0,
                    column="file",
                    message="Formato de archivo no soportado. Use .xlsx o .xls"
                )], 0, 0
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return [], [ExcelValidationError(
                row=0,
                column="file",
                message=f"Error al leer el archivo Excel: {str(e)}"
            )], 0, 0

        # Normalize column names
        df.columns = df.columns.str.strip()

        # Validate required columns
        missing_columns = self._validate_columns(df)
        if missing_columns:
            return [], [
                ExcelValidationError(
                    row=0,
                    column=col,
                    message=f"Columna requerida no encontrada: {col}"
                )
                for col in missing_columns
            ], len(df), 0

        # Process rows
        records, errors = self._validate_rows(df, default_doc_type)

        return records, errors, len(df), len(records)

    def _validate_columns(self, df: pd.DataFrame) -> List[str]:
        """Check for missing required columns."""
        missing = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing.append(col)
        return missing

    def _validate_rows(
        self,
        df: pd.DataFrame,
        default_doc_type: DocumentType
    ) -> Tuple[List[CombinedRecord], List[ExcelValidationError]]:
        """
        Validate each row and extract records.

        Args:
            df: DataFrame with Excel data
            default_doc_type: Default document type for records

        Returns:
            Tuple of (valid_records, errors)
        """
        records = []
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel rows are 1-indexed, plus header

            try:
                # Extract required fields
                uuid_val = str(row.get('UUID', '')).strip()
                if not uuid_val or uuid_val.lower() == 'nan':
                    errors.append(ExcelValidationError(
                        row=row_num,
                        column='UUID',
                        message='UUID es requerido'
                    ))
                    continue

                codigo_op = str(row.get('CODIGO DE OPERACIÓN', '')).strip()
                if not codigo_op or codigo_op.lower() == 'nan':
                    errors.append(ExcelValidationError(
                        row=row_num,
                        column='CODIGO DE OPERACIÓN',
                        message='Código de operación es requerido'
                    ))
                    continue

                # Parse fecha
                fecha_val = row.get('Fecha emision')
                if pd.isna(fecha_val):
                    errors.append(ExcelValidationError(
                        row=row_num,
                        column='Fecha emision',
                        message='Fecha de emisión es requerida'
                    ))
                    continue

                try:
                    if isinstance(fecha_val, datetime):
                        fecha_emision = fecha_val.date()
                    elif isinstance(fecha_val, str):
                        fecha_emision = pd.to_datetime(fecha_val).date()
                    else:
                        fecha_emision = pd.Timestamp(fecha_val).date()
                except Exception:
                    errors.append(ExcelValidationError(
                        row=row_num,
                        column='Fecha emision',
                        message=f'Formato de fecha inválido: {fecha_val}'
                    ))
                    continue

                # Parse RFC
                rfc = str(row.get('RFC receptor', '')).strip().upper()
                if not rfc or rfc.lower() == 'nan':
                    errors.append(ExcelValidationError(
                        row=row_num,
                        column='RFC receptor',
                        message='RFC receptor es requerido'
                    ))
                    continue

                # Parse numeric fields with defaults
                subtotal = self._parse_numeric(row.get('SubTotal'), 0.0)
                iva_trasladado = self._parse_numeric(row.get('IVA Trasladado'), 0.0)
                iva_exento = self._parse_numeric(row.get('IVA Exento'), 0.0)
                total = self._parse_numeric(row.get('Total'), 0.0)

                # Optional fields
                conceptos = str(row.get('Conceptos', '')).strip()
                if conceptos.lower() == 'nan':
                    conceptos = ''

                razon = str(row.get('Razon receptor', '')).strip()
                if razon.lower() == 'nan':
                    razon = ''

                uuid_relacionados = None
                if 'UUIDs relacionados' in df.columns:
                    rel_val = str(row.get('UUIDs relacionados', '')).strip()
                    if rel_val and rel_val.lower() != 'nan':
                        uuid_relacionados = rel_val

                tipo_comprobante = None
                if 'Tipo' in df.columns:
                    tipo_val = str(row.get('Tipo', '')).strip()
                    if tipo_val and tipo_val.lower() != 'nan':
                        tipo_comprobante = tipo_val

                # Determine document type
                doc_type = default_doc_type
                if self.is_complemento_pago(tipo_comprobante, conceptos):
                    doc_type = DocumentType.COMPLEMENTO_PAGO

                record = CombinedRecord(
                    uuid=uuid_val.upper(),
                    codigo_operacion=codigo_op,
                    conceptos=conceptos[:1000] if conceptos else '',
                    fecha_emision=fecha_emision,
                    rfc_receptor=rfc,
                    razon_receptor=razon[:255] if razon else '',
                    subtotal=subtotal,
                    iva_trasladado=max(0, iva_trasladado),
                    iva_exento=max(0, iva_exento),
                    total=total,
                    uuid_relacionados=uuid_relacionados,
                    tipo_comprobante=tipo_comprobante,
                    document_type=doc_type
                )
                records.append(record)

            except Exception as e:
                logger.warning(f"Error processing row {row_num}: {e}")
                errors.append(ExcelValidationError(
                    row=row_num,
                    column='general',
                    message=f'Error procesando fila: {str(e)}'
                ))

        return records, errors

    def _parse_numeric(self, value, default: float = 0.0) -> float:
        """Parse a numeric value with fallback to default."""
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default


# Singleton instance
_combined_excel_service: Optional[CombinedExcelService] = None


def get_combined_excel_service() -> CombinedExcelService:
    """Get or create the combined Excel service instance."""
    global _combined_excel_service
    if _combined_excel_service is None:
        _combined_excel_service = CombinedExcelService()
    return _combined_excel_service
