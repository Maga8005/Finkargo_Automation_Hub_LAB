"""
Excel Merge Service

Service for merging uploaded Excel data with Drive master Excel.
Implements upsert logic by UUID (update if exists, insert if new).
"""

import logging
import io
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from src.interface.finance_dtos import InvoiceRecord

logger = logging.getLogger(__name__)


class ExcelMergeService:
    """
    Service for merging invoice data with Drive master Excel.

    Provides functionality for:
    - Reading Excel files from bytes
    - Merging invoice records by UUID (upsert logic)
    - Writing merged data back to Excel bytes
    - Tracking merge statistics
    """

    # Column headers for Excel file (32 columns - MASTER structure)
    HEADERS = [
        "Periodo",
        "Version",
        "UUID",
        "UUIDs relacionados",
        "CP Expedicion",
        "Serie",
        "Folio",
        "Tipo",
        "Fecha emision",
        "Regimen emisor",
        "RFC emisor",
        "Razon emisor",
        "RFC receptor",
        "Razon receptor",
        "Regimen receptor",
        "Domicilio receptor",
        "Claves de productos",
        "Conceptos",
        "Uso CFDI",
        "Efecto",
        "Estado",
        "Moneda",
        "Tipo de cambio",
        "Metodo pago",
        "Forma pago",
        "SubTotal",
        "IVA Trasladado",
        "IVA Exento",
        "ISR Retenido",
        "Total",
        "CONCEPTO",
        "CODIGO DE OPERACIÓN"
    ]

    def __init__(self):
        """Initialize the Excel merge service."""
        logger.info("ExcelMergeService initialized")

    async def read_uploaded_excel_as_dicts(self, file) -> List[Dict]:
        """
        Read uploaded Excel file as dictionaries (32 columns).

        Args:
            file: UploadFile object from FastAPI.

        Returns:
            List[Dict]: Records with all 32 columns.
        """
        try:
            # Reset file pointer to beginning before reading
            await file.seek(0)
            contents = await file.read()
            # Reset again for any subsequent reads
            await file.seek(0)
            return self.read_excel_from_bytes(contents)
        except Exception as e:
            logger.error(f"Error reading uploaded Excel: {e}")
            raise

    def convert_dicts_to_invoice_records(self, records: List[Dict]) -> List[InvoiceRecord]:
        """
        Convert 32-column dicts to InvoiceRecord objects (11 columns) for search/session.

        Args:
            records: List of dicts with 32 columns.

        Returns:
            List[InvoiceRecord]: Simplified records for search functionality.
        """
        invoice_records = []

        for record in records:
            try:
                # Parse date
                fecha_str = record.get("Fecha emision", "")
                if fecha_str:
                    if isinstance(fecha_str, str):
                        # Try to parse ISO format
                        try:
                            fecha_emision = datetime.fromisoformat(fecha_str).date()
                        except (ValueError, AttributeError):
                            # Try datetime object
                            fecha_emision = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    else:
                        fecha_emision = fecha_str
                else:
                    continue  # Skip records without date

                # Get optional fields
                uuid_rel = record.get("UUIDs relacionados")
                uuid_relacionados = str(uuid_rel).strip() if uuid_rel and str(uuid_rel).strip().lower() != 'nan' else None

                tipo_comp = record.get("Tipo")
                tipo_comprobante = str(tipo_comp).strip() if tipo_comp and str(tipo_comp).strip().lower() != 'nan' else None

                # Create InvoiceRecord
                invoice_record = InvoiceRecord(
                    uuid=str(record.get("UUID", "")).strip().upper(),
                    codigo_operacion=str(record.get("CODIGO DE OPERACIÓN", "")).strip(),
                    conceptos=str(record.get("Conceptos", "")).strip(),
                    fecha_emision=fecha_emision,
                    rfc_receptor=str(record.get("RFC receptor", "")).strip().upper(),
                    razon_receptor=str(record.get("Razon receptor", "")).strip(),
                    subtotal=float(record.get("SubTotal", 0) or 0),
                    iva_trasladado=float(record.get("IVA Trasladado", 0) or 0),
                    iva_exento=float(record.get("IVA Exento", 0) or 0),
                    total=float(record.get("Total", 0) or 0),
                    uuid_relacionados=uuid_relacionados,
                    tipo_comprobante=tipo_comprobante
                )
                invoice_records.append(invoice_record)

            except Exception as e:
                logger.warning(f"Error converting dict to InvoiceRecord: {e}")
                continue

        logger.info(f"Converted {len(invoice_records)} dicts to InvoiceRecords")
        return invoice_records

    def read_excel_from_bytes(self, excel_bytes: bytes) -> List[Dict]:
        """
        Read all rows from Excel file bytes (32 columns).

        Args:
            excel_bytes: Excel file content in bytes.

        Returns:
            List[Dict]: List of row data as dictionaries with all 32 columns.

        Raises:
            Exception: If Excel reading fails.
        """
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(excel_bytes))
            sheet = workbook.active

            records = []
            header_row = 1

            # Start from row 2 (skip header)
            for row_idx, row in enumerate(sheet.iter_rows(min_row=header_row + 1, values_only=True), start=header_row + 1):
                # UUID is in column 3 (index 2)
                if not row[2]:  # Skip empty rows (no UUID)
                    continue

                try:
                    # Create dictionary with all columns
                    record = {}
                    for col_idx, header in enumerate(self.HEADERS):
                        value = row[col_idx] if col_idx < len(row) else None

                        # Convert to string if not None
                        if value is not None:
                            if isinstance(value, datetime):
                                value = value.date().isoformat()
                            else:
                                value = str(value).strip()

                        record[header] = value

                    records.append(record)

                except Exception as e:
                    logger.warning(f"Error parsing row {row_idx}: {e}")
                    continue

            logger.info(f"Read {len(records)} records from Excel (32 columns)")
            return records

        except Exception as e:
            logger.error(f"Error reading Excel from bytes: {e}")
            raise

    def merge_invoice_data(
        self,
        uploaded_records: List[Dict],
        master_records: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Merge uploaded records with master records by UUID (32 columns).

        Logic:
        - If UUID exists in master → UPDATE with uploaded data
        - If UUID is new → INSERT new record

        Args:
            uploaded_records: Records from uploaded Excel file (dicts with 32 columns).
            master_records: Records from Drive master Excel file (dicts with 32 columns).

        Returns:
            Tuple[List[Dict], Dict]:
                - Merged list of records (dicts)
                - Statistics dict with 'new', 'updated', 'unchanged' counts
        """
        logger.info(f"Merging {len(uploaded_records)} uploaded records with {len(master_records)} master records")

        # Create UUID index for master records
        master_by_uuid = {record.get("UUID", "").strip().upper(): record for record in master_records if record.get("UUID")}

        merged_records = []
        stats = {
            'new': 0,
            'updated': 0,
            'unchanged': 0
        }

        # Process uploaded records
        for uploaded_record in uploaded_records:
            uuid = uploaded_record.get("UUID", "").strip().upper()

            if not uuid:
                logger.warning("Skipping record with empty UUID")
                continue

            if uuid in master_by_uuid:
                # UUID exists - this is an update
                stats['updated'] += 1
                # Use the uploaded data (overwrites master)
                merged_records.append(uploaded_record)
                # Mark as processed
                del master_by_uuid[uuid]
            else:
                # UUID is new - this is an insert
                stats['new'] += 1
                merged_records.append(uploaded_record)

        # Add remaining master records that weren't in uploaded file
        for remaining_record in master_by_uuid.values():
            stats['unchanged'] += 1
            merged_records.append(remaining_record)

        logger.info(
            f"Merge complete: {stats['new']} new, {stats['updated']} updated, "
            f"{stats['unchanged']} unchanged, {len(merged_records)} total"
        )

        return merged_records, stats

    def write_excel_to_bytes(self, records: List[Dict]) -> bytes:
        """
        Write records to Excel file bytes (32 columns).

        Args:
            records: List of record dicts to write.

        Returns:
            bytes: Excel file content as bytes.

        Raises:
            Exception: If Excel writing fails.
        """
        try:
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Facturación MX"

            # Write headers with styling
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            for col_idx, header in enumerate(self.HEADERS, start=1):
                cell = sheet.cell(row=1, column=col_idx, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Write data rows (all 32 columns)
            for row_idx, record in enumerate(records, start=2):
                for col_idx, header in enumerate(self.HEADERS, start=1):
                    value = record.get(header, "")
                    sheet.cell(row=row_idx, column=col_idx, value=value)

            # Auto-size columns (set reasonable widths)
            for col_idx, header in enumerate(self.HEADERS, start=1):
                column_letter = openpyxl.utils.get_column_letter(col_idx)
                # Set different widths based on column type
                if header in ["UUID", "UUIDs relacionados"]:
                    sheet.column_dimensions[column_letter].width = 40
                elif header in ["Conceptos", "Razon emisor", "Razon receptor", "Domicilio receptor"]:
                    sheet.column_dimensions[column_letter].width = 50
                elif header in ["RFC emisor", "RFC receptor"]:
                    sheet.column_dimensions[column_letter].width = 15
                else:
                    sheet.column_dimensions[column_letter].width = 20

            # Save to bytes
            excel_buffer = io.BytesIO()
            workbook.save(excel_buffer)
            excel_buffer.seek(0)
            excel_bytes = excel_buffer.read()

            logger.info(f"Wrote {len(records)} records to Excel with 32 columns ({len(excel_bytes)} bytes)")
            return excel_bytes

        except Exception as e:
            logger.error(f"Error writing Excel to bytes: {e}")
            raise


# Singleton instance
_excel_merge_service: Optional[ExcelMergeService] = None


def get_excel_merge_service() -> ExcelMergeService:
    """
    Get or create the Excel merge service singleton.

    Returns:
        ExcelMergeService instance.
    """
    global _excel_merge_service
    if _excel_merge_service is None:
        _excel_merge_service = ExcelMergeService()
    return _excel_merge_service
