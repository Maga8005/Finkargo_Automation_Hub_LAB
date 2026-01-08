"""
Excel Validation Service for Facturación MX.

This service handles the validation and parsing of master Excel files
containing invoice data for the Mexico invoicing automation.
"""

import pandas as pd
import logging
from typing import List, Tuple
from datetime import datetime
from fastapi import UploadFile
import io
import uuid as uuid_lib

from src.interface.finance_dtos import (
    InvoiceRecord,
    ExcelValidationError,
    ExcelValidationResponse
)

logger = logging.getLogger(__name__)


class ExcelValidationService:
    """
    Service for validating and parsing master Excel files.

    This service validates that the Excel contains all required columns
    and that each row has valid data according to business rules.
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

    # Optional columns (read if present, but not required)
    OPTIONAL_COLUMNS = [
        'UUIDs relacionados',
        'Tipo'
    ]

    # Column name mappings (Excel column -> internal field)
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


    async def validate_excel(self, file: UploadFile) -> ExcelValidationResponse:
        """
        Validate and parse the master Excel file.

        Args:
            file: Uploaded Excel file (.xlsx or .xls)

        Returns:
            ExcelValidationResponse with parsed data and any errors found

        Raises:
            ValueError: If file format is invalid or cannot be read
        """
        logger.info(f"Starting Excel validation for file: {file.filename}")

        # Read file content
        content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise ValueError("El archivo excede el tamaño máximo de 10MB")

        # Determine file type and read with pandas
        try:
            if file.filename.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            elif file.filename.endswith('.xls'):
                df = pd.read_excel(io.BytesIO(content), engine='xlrd')
            else:
                raise ValueError("Formato de archivo no soportado. Use .xlsx o .xls")
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise ValueError(f"Error al leer el archivo Excel: {str(e)}")

        # Validate columns
        column_errors = self._validate_columns(df)
        if column_errors:
            return ExcelValidationResponse(
                success=False,
                total_rows=len(df),
                valid_rows=0,
                errors=[
                    ExcelValidationError(row=0, column=col, message=f"Columna requerida no encontrada: {col}")
                    for col in column_errors
                ],
                data=[],
                session_id=str(uuid_lib.uuid4())
            )

        # Validate rows and extract data
        valid_records, errors = self._validate_rows(df)

        # Generate session ID
        session_id = str(uuid_lib.uuid4())

        logger.info(f"Excel validation complete. Valid rows: {len(valid_records)}, Errors: {len(errors)}")

        return ExcelValidationResponse(
            success=len(errors) == 0,
            total_rows=len(df),
            valid_rows=len(valid_records),
            errors=errors,
            data=valid_records,
            session_id=session_id
        )

    def _validate_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Verify that all required columns exist in the DataFrame.

        Args:
            df: Pandas DataFrame from Excel file

        Returns:
            List of missing column names (empty if all present)
        """
        # Normalize column names (strip whitespace)
        df.columns = df.columns.str.strip()

        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            # Check for exact match or case-insensitive match
            if col not in df.columns:
                # Try case-insensitive match
                matches = [c for c in df.columns if c.upper() == col.upper()]
                if not matches:
                    missing_columns.append(col)
                else:
                    # Rename to expected format
                    df.rename(columns={matches[0]: col}, inplace=True)

        return missing_columns

    def _validate_rows(self, df: pd.DataFrame) -> Tuple[List[InvoiceRecord], List[ExcelValidationError]]:
        """
        Validate each row and convert to InvoiceRecord objects.

        Args:
            df: Pandas DataFrame with required columns

        Returns:
            Tuple of (valid_records, errors)
        """
        valid_records: List[InvoiceRecord] = []
        errors: List[ExcelValidationError] = []

        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel rows are 1-indexed, plus header row
            row_errors: List[ExcelValidationError] = []

            # Validate UUID
            uuid_val = str(row.get('UUID', '')).strip()
            if not uuid_val or uuid_val.lower() == 'nan':
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='UUID',
                    message='UUID es requerido y no puede estar vacío'
                ))

            # Validate CODIGO DE OPERACIÓN
            codigo_op = str(row.get('CODIGO DE OPERACIÓN', '')).strip()
            if not codigo_op or codigo_op.lower() == 'nan':
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='CODIGO DE OPERACIÓN',
                    message='Código de operación es requerido'
                ))

            # Validate Conceptos
            conceptos = str(row.get('Conceptos', '')).strip()
            if not conceptos or conceptos.lower() == 'nan':
                conceptos = 'Sin descripción'

            # Validate Fecha emision
            fecha_emision = None
            try:
                fecha_val = row.get('Fecha emision')
                if pd.isna(fecha_val):
                    row_errors.append(ExcelValidationError(
                        row=row_num,
                        column='Fecha emision',
                        message='Fecha de emisión es requerida'
                    ))
                elif isinstance(fecha_val, datetime):
                    fecha_emision = fecha_val.date()
                elif isinstance(fecha_val, str):
                    # Try to parse string date with multiple formats
                    date_formats = [
                        '%Y-%m-%d %H:%M:%S',  # 2025-01-20 21:25:00
                        '%Y-%d-%m %H:%M:%S',  # 2025-20-01 21:25:00 (day-month swapped)
                        '%Y-%m-%d',           # 2025-01-20
                        '%d/%m/%Y %H:%M:%S',  # 20/01/2025 21:25:00
                        '%d/%m/%Y',           # 20/01/2025
                        '%d-%m-%Y %H:%M:%S',  # 20-01-2025 21:25:00
                        '%d-%m-%Y',           # 20-01-2025
                        '%m/%d/%Y',           # 01/20/2025
                        '%Y/%m/%d',           # 2025/01/20
                    ]
                    for fmt in date_formats:
                        try:
                            fecha_emision = datetime.strptime(fecha_val.strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                    if not fecha_emision:
                        # Try pandas as last resort
                        try:
                            fecha_emision = pd.to_datetime(fecha_val).date()
                        except Exception:
                            row_errors.append(ExcelValidationError(
                                row=row_num,
                                column='Fecha emision',
                                message='Formato de fecha inválido'
                            ))
                else:
                    fecha_emision = pd.to_datetime(fecha_val).date()
            except Exception as e:
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='Fecha emision',
                    message=f'Error al procesar fecha: {str(e)}'
                ))

            # Validate RFC receptor
            rfc_receptor = str(row.get('RFC receptor', '')).strip().upper()
            if not rfc_receptor or rfc_receptor.lower() == 'nan':
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='RFC receptor',
                    message='RFC receptor es requerido'
                ))
            elif len(rfc_receptor) < 12 or len(rfc_receptor) > 13:
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='RFC receptor',
                    message='RFC debe tener 12 o 13 caracteres'
                ))

            # Validate Razon receptor
            razon_receptor = str(row.get('Razon receptor', '')).strip()
            if not razon_receptor or razon_receptor.lower() == 'nan':
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='Razon receptor',
                    message='Razón social del receptor es requerida'
                ))

            # Validate SubTotal (can be negative for expenses/refunds)
            subtotal = 0.0
            try:
                subtotal_val = row.get('SubTotal')
                if pd.isna(subtotal_val):
                    row_errors.append(ExcelValidationError(
                        row=row_num,
                        column='SubTotal',
                        message='SubTotal es requerido'
                    ))
                else:
                    subtotal = float(subtotal_val)
            except (ValueError, TypeError):
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='SubTotal',
                    message='SubTotal debe ser un número válido'
                ))

            # Validate IVA Trasladado (optional, defaults to 0)
            iva_trasladado = 0.0
            try:
                iva_tras_val = row.get('IVA Trasladado')
                if not pd.isna(iva_tras_val):
                    iva_trasladado = float(iva_tras_val)
                    if iva_trasladado < 0:
                        row_errors.append(ExcelValidationError(
                            row=row_num,
                            column='IVA Trasladado',
                            message='IVA Trasladado no puede ser negativo'
                        ))
            except (ValueError, TypeError):
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='IVA Trasladado',
                    message='IVA Trasladado debe ser un número válido'
                ))

            # Validate IVA Exento (optional, defaults to 0)
            iva_exento = 0.0
            try:
                iva_exento_val = row.get('IVA Exento')
                if not pd.isna(iva_exento_val):
                    iva_exento = float(iva_exento_val)
                    if iva_exento < 0:
                        row_errors.append(ExcelValidationError(
                            row=row_num,
                            column='IVA Exento',
                            message='IVA Exento no puede ser negativo'
                        ))
            except (ValueError, TypeError):
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='IVA Exento',
                    message='IVA Exento debe ser un número válido'
                ))

            # Validate Total (can be negative for expenses/refunds)
            total = 0.0
            try:
                total_val = row.get('Total')
                if pd.isna(total_val):
                    row_errors.append(ExcelValidationError(
                        row=row_num,
                        column='Total',
                        message='Total es requerido'
                    ))
                else:
                    total = float(total_val)
            except (ValueError, TypeError):
                row_errors.append(ExcelValidationError(
                    row=row_num,
                    column='Total',
                    message='Total debe ser un número válido'
                ))

            # If there are errors for this row, add them and skip record
            if row_errors:
                errors.extend(row_errors)
                continue

            # Read optional columns
            uuid_relacionados = None
            uuid_rel_val = row.get('UUIDs relacionados', '')
            if pd.notna(uuid_rel_val) and str(uuid_rel_val).strip().lower() != 'nan':
                uuid_relacionados = str(uuid_rel_val).strip()

            tipo_comprobante = None
            tipo_comp_val = row.get('Tipo', '')
            if pd.notna(tipo_comp_val) and str(tipo_comp_val).strip().lower() != 'nan':
                tipo_comprobante = str(tipo_comp_val).strip()

            # Create valid record
            try:
                record = InvoiceRecord(
                    uuid=uuid_val.upper(),
                    codigo_operacion=codigo_op,
                    conceptos=conceptos,
                    fecha_emision=fecha_emision,
                    rfc_receptor=rfc_receptor,
                    razon_receptor=razon_receptor,
                    subtotal=subtotal,
                    iva_trasladado=iva_trasladado,
                    iva_exento=iva_exento,
                    total=total,
                    uuid_relacionados=uuid_relacionados,
                    tipo_comprobante=tipo_comprobante
                )
                valid_records.append(record)
            except Exception as e:
                logger.error(f"Error creating InvoiceRecord for row {row_num}: {e}")
                errors.append(ExcelValidationError(
                    row=row_num,
                    column='General',
                    message=f'Error al procesar registro: {str(e)}'
                ))

        return valid_records, errors
