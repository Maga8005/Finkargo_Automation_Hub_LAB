"""
Excel Merge Service for Mexico (MX) - Multi-Sheet Version.

Service for merging uploaded Excel data with Drive master Excel.
Supports two sheets: Facturas and Complementos de Pago.
Implements upsert logic by UUID (update if exists, insert if new).
"""

import logging
import io
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from src.interface.finance_dtos import CombinedRecord, DocumentType

logger = logging.getLogger(__name__)


class ExcelMergeServiceMX:
    """
    Service for merging invoice data with Drive master Excel (multi-sheet).

    Provides functionality for:
    - Reading multi-sheet Excel files from bytes
    - Merging invoice records by UUID per sheet (upsert logic)
    - Writing merged data back to multi-sheet Excel bytes
    - Tracking merge statistics per sheet

    Sheets:
    - "Facturas": Invoice records (document_type = factura)
    - "Complementos de Pago": Payment supplement records (document_type = complemento_pago)
    """

    # Sheet names
    SHEET_FACTURAS = "Facturas"
    SHEET_COMPLEMENTOS = "Complementos de Pago"

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
        """Initialize the Excel merge service for MX."""
        logger.info("ExcelMergeServiceMX (multi-sheet) initialized")

    def read_multisheet_excel_from_bytes(
        self,
        excel_bytes: bytes
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Read all rows from multi-sheet Excel file bytes.

        Args:
            excel_bytes: Excel file content in bytes.

        Returns:
            Tuple[List[Dict], List[Dict]]: (facturas_records, complementos_records)

        Raises:
            Exception: If Excel reading fails.
        """
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(excel_bytes))

            facturas_records = []
            complementos_records = []

            # Read Facturas sheet
            if self.SHEET_FACTURAS in workbook.sheetnames:
                sheet = workbook[self.SHEET_FACTURAS]
                facturas_records = self._read_sheet_records(sheet)
                logger.info(f"Read {len(facturas_records)} records from {self.SHEET_FACTURAS} sheet")
            else:
                logger.warning(f"Sheet '{self.SHEET_FACTURAS}' not found in Excel")

            # Read Complementos sheet
            if self.SHEET_COMPLEMENTOS in workbook.sheetnames:
                sheet = workbook[self.SHEET_COMPLEMENTOS]
                complementos_records = self._read_sheet_records(sheet)
                logger.info(f"Read {len(complementos_records)} records from {self.SHEET_COMPLEMENTOS} sheet")
            else:
                logger.warning(f"Sheet '{self.SHEET_COMPLEMENTOS}' not found in Excel")

            # If no named sheets found, try reading from first sheet as facturas
            if not facturas_records and not complementos_records:
                active_sheet = workbook.active
                if active_sheet:
                    logger.info("No named sheets found, reading from active sheet as Facturas")
                    facturas_records = self._read_sheet_records(active_sheet)

            return facturas_records, complementos_records

        except Exception as e:
            logger.error(f"Error reading multi-sheet Excel from bytes: {e}")
            raise

    def _read_sheet_records(self, sheet) -> List[Dict]:
        """
        Read records from a single sheet.

        Args:
            sheet: openpyxl worksheet object.

        Returns:
            List[Dict]: List of row data as dictionaries with all 32 columns.
        """
        records = []
        header_row = 1

        # Start from row 2 (skip header)
        for row_idx, row in enumerate(sheet.iter_rows(min_row=header_row + 1, values_only=True), start=header_row + 1):
            # UUID is in column 3 (index 2)
            if len(row) < 3 or not row[2]:  # Skip empty rows (no UUID)
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

        return records

    async def read_uploaded_excel_as_dicts(
        self,
        file,
        document_type: DocumentType
    ) -> List[Dict]:
        """
        Read uploaded Excel file as dictionaries preserving ALL columns.

        Args:
            file: UploadFile object from FastAPI.
            document_type: Type of document (factura or complemento_pago).

        Returns:
            List[Dict]: Records with all original columns.
        """
        try:
            # Reset file pointer to beginning before reading
            await file.seek(0)
            contents = await file.read()
            # Reset again for any subsequent reads
            await file.seek(0)
            return self.read_single_sheet_excel_preserve_all(contents)
        except Exception as e:
            logger.error(f"Error reading uploaded Excel: {e}")
            raise

    def read_single_sheet_excel_preserve_all(
        self,
        excel_bytes: bytes
    ) -> List[Dict]:
        """
        Read records from a single-sheet uploaded Excel preserving ALL columns.

        This reads the Excel file and preserves every column present,
        not just the 32 standard columns.

        Args:
            excel_bytes: Excel file content in bytes.

        Returns:
            List[Dict]: Records with all original columns.
        """
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(excel_bytes))
            sheet = workbook.active

            records = []

            # Get actual headers from the first row
            headers = []
            for cell in sheet[1]:
                header = str(cell.value).strip() if cell.value else f"Column_{cell.column}"
                headers.append(header)

            logger.info(f"Excel headers found: {headers}")

            # Read data rows (starting from row 2)
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                # Check if row has UUID (typically column 3, but find it by header)
                uuid_col_idx = None
                for i, h in enumerate(headers):
                    if h.upper() == 'UUID':
                        uuid_col_idx = i
                        break

                # Skip empty rows
                if uuid_col_idx is not None and (len(row) <= uuid_col_idx or not row[uuid_col_idx]):
                    continue

                # If no UUID column found, skip rows where all values are empty
                if uuid_col_idx is None:
                    if all(v is None or str(v).strip() == '' for v in row):
                        continue

                try:
                    # Create dictionary with all columns
                    record = {}
                    for col_idx, header in enumerate(headers):
                        value = row[col_idx] if col_idx < len(row) else None

                        # Convert to appropriate string format
                        if value is not None:
                            if isinstance(value, datetime):
                                value = value.date().isoformat()
                            elif value is not None:
                                str_val = str(value).strip()
                                # Keep numeric values as-is for numeric columns
                                if str_val.lower() != 'nan' and str_val != '':
                                    value = str_val
                                else:
                                    value = ''
                        else:
                            value = ''

                        record[header] = value

                    records.append(record)

                except Exception as e:
                    logger.warning(f"Error parsing row {row_idx}: {e}")
                    continue

            logger.info(f"Read {len(records)} records with {len(headers)} columns from uploaded Excel")
            return records

        except Exception as e:
            logger.error(f"Error reading single-sheet Excel: {e}")
            raise

    def read_single_sheet_excel(
        self,
        excel_bytes: bytes,
        document_type: DocumentType
    ) -> List[Dict]:
        """
        Read records from a single-sheet uploaded Excel (legacy method).

        Args:
            excel_bytes: Excel file content in bytes.
            document_type: Type of document for these records.

        Returns:
            List[Dict]: Records with standard 32 columns.
        """
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(excel_bytes))
            sheet = workbook.active
            records = self._read_sheet_records(sheet)
            logger.info(f"Read {len(records)} {document_type.value} records from uploaded Excel")
            return records
        except Exception as e:
            logger.error(f"Error reading single-sheet Excel: {e}")
            raise

    def convert_combined_records_to_dicts(
        self,
        records: List[CombinedRecord]
    ) -> List[Dict]:
        """
        Convert CombinedRecord objects to 32-column dicts for Excel.

        Args:
            records: List of CombinedRecord objects.

        Returns:
            List[Dict]: Records with all 32 columns.
        """
        dicts = []

        for record in records:
            try:
                # Format date
                fecha_str = ""
                if record.fecha_emision:
                    if hasattr(record.fecha_emision, 'isoformat'):
                        fecha_str = record.fecha_emision.isoformat()
                    else:
                        fecha_str = str(record.fecha_emision)

                # Create 32-column dict (fill missing columns with empty)
                record_dict = {
                    "Periodo": "",
                    "Version": "",
                    "UUID": record.uuid,
                    "UUIDs relacionados": record.uuid_relacionados or "",
                    "CP Expedicion": "",
                    "Serie": "",
                    "Folio": "",
                    "Tipo": record.tipo_comprobante or "",
                    "Fecha emision": fecha_str,
                    "Regimen emisor": "",
                    "RFC emisor": "",
                    "Razon emisor": "",
                    "RFC receptor": record.rfc_receptor,
                    "Razon receptor": record.razon_receptor,
                    "Regimen receptor": "",
                    "Domicilio receptor": "",
                    "Claves de productos": "",
                    "Conceptos": record.conceptos,
                    "Uso CFDI": "",
                    "Efecto": "",
                    "Estado": "",
                    "Moneda": "",
                    "Tipo de cambio": "",
                    "Metodo pago": "",
                    "Forma pago": "",
                    "SubTotal": record.subtotal,
                    "IVA Trasladado": record.iva_trasladado,
                    "IVA Exento": record.iva_exento,
                    "ISR Retenido": 0,
                    "Total": record.total,
                    "CONCEPTO": "",
                    "CODIGO DE OPERACIÓN": record.codigo_operacion
                }
                dicts.append(record_dict)

            except Exception as e:
                logger.warning(f"Error converting CombinedRecord to dict: {e}")
                continue

        return dicts

    def merge_records_by_uuid(
        self,
        uploaded_records: List[Dict],
        master_records: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """
        Merge uploaded records with master records by UUID.

        Logic:
        - If UUID exists in master -> UPDATE with uploaded data
        - If UUID is new -> INSERT new record

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
        master_by_uuid = {
            record.get("UUID", "").strip().upper(): record
            for record in master_records
            if record.get("UUID")
        }

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

    def write_multisheet_excel_to_bytes(
        self,
        facturas_records: List[Dict],
        complementos_records: List[Dict]
    ) -> bytes:
        """
        Write records to multi-sheet Excel file bytes.

        Args:
            facturas_records: List of invoice record dicts.
            complementos_records: List of payment supplement record dicts.

        Returns:
            bytes: Excel file content as bytes.

        Raises:
            Exception: If Excel writing fails.
        """
        try:
            workbook = Workbook()

            # Remove default sheet
            if 'Sheet' in workbook.sheetnames:
                del workbook['Sheet']

            # Create Facturas sheet
            facturas_sheet = workbook.create_sheet(title=self.SHEET_FACTURAS)
            self._write_sheet(facturas_sheet, facturas_records)
            logger.info(f"Wrote {len(facturas_records)} records to {self.SHEET_FACTURAS} sheet")

            # Create Complementos sheet
            complementos_sheet = workbook.create_sheet(title=self.SHEET_COMPLEMENTOS)
            self._write_sheet(complementos_sheet, complementos_records)
            logger.info(f"Wrote {len(complementos_records)} records to {self.SHEET_COMPLEMENTOS} sheet")

            # Save to bytes
            excel_buffer = io.BytesIO()
            workbook.save(excel_buffer)
            excel_buffer.seek(0)
            excel_bytes = excel_buffer.read()

            total_records = len(facturas_records) + len(complementos_records)
            logger.info(f"Wrote {total_records} total records to multi-sheet Excel ({len(excel_bytes)} bytes)")
            return excel_bytes

        except Exception as e:
            logger.error(f"Error writing multi-sheet Excel to bytes: {e}")
            raise

    def _write_sheet(self, sheet, records: List[Dict]) -> None:
        """
        Write records to a single sheet with styling.

        Args:
            sheet: openpyxl worksheet object.
            records: List of record dicts to write.
        """
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

    async def merge_combined_upload_with_drive(
        self,
        facturas_records: List[CombinedRecord],
        complementos_records: List[CombinedRecord],
        master_excel_bytes: Optional[bytes]
    ) -> Tuple[bytes, Dict[str, Dict[str, int]]]:
        """
        Merge uploaded combined data with existing Drive master Excel.

        NOTE: This method uses CombinedRecord objects which have limited columns.
        For full column preservation, use merge_raw_excel_with_drive instead.

        Args:
            facturas_records: List of uploaded factura CombinedRecords.
            complementos_records: List of uploaded complemento CombinedRecords.
            master_excel_bytes: Current master Excel content (or None if new).

        Returns:
            Tuple[bytes, Dict]: (merged_excel_bytes, stats_by_sheet)
        """
        # Convert CombinedRecords to dicts
        uploaded_facturas_dicts = self.convert_combined_records_to_dicts(facturas_records)
        uploaded_complementos_dicts = self.convert_combined_records_to_dicts(complementos_records)

        # Read existing master data (if exists)
        master_facturas: List[Dict] = []
        master_complementos: List[Dict] = []

        if master_excel_bytes:
            try:
                master_facturas, master_complementos = self.read_multisheet_excel_from_bytes(master_excel_bytes)
                logger.info(f"Master Excel has {len(master_facturas)} facturas, {len(master_complementos)} complementos")
            except Exception as e:
                logger.warning(f"Could not read master Excel (will create new): {e}")

        # Merge each sheet independently
        merged_facturas, facturas_stats = self.merge_records_by_uuid(
            uploaded_facturas_dicts,
            master_facturas
        )

        merged_complementos, complementos_stats = self.merge_records_by_uuid(
            uploaded_complementos_dicts,
            master_complementos
        )

        # Write merged data to multi-sheet Excel
        merged_excel_bytes = self.write_multisheet_excel_to_bytes(
            merged_facturas,
            merged_complementos
        )

        stats = {
            'facturas': facturas_stats,
            'complementos': complementos_stats
        }

        return merged_excel_bytes, stats

    async def merge_raw_excel_with_drive(
        self,
        facturas_dicts: List[Dict],
        complementos_dicts: List[Dict],
        master_excel_bytes: Optional[bytes]
    ) -> Tuple[bytes, Dict[str, Dict[str, int]]]:
        """
        Merge uploaded raw Excel data (all columns) with existing Drive master Excel.

        This method preserves ALL columns from the uploaded files.

        Args:
            facturas_dicts: List of dicts from uploaded facturas Excel (all columns).
            complementos_dicts: List of dicts from uploaded complementos Excel (all columns).
            master_excel_bytes: Current master Excel content (or None if new).

        Returns:
            Tuple[bytes, Dict]: (merged_excel_bytes, stats_by_sheet)
        """
        # Read existing master data (if exists)
        master_facturas: List[Dict] = []
        master_complementos: List[Dict] = []

        if master_excel_bytes:
            try:
                master_facturas, master_complementos = self.read_multisheet_excel_from_bytes(master_excel_bytes)
                logger.info(f"Master Excel has {len(master_facturas)} facturas, {len(master_complementos)} complementos")
            except Exception as e:
                logger.warning(f"Could not read master Excel (will create new): {e}")

        # Merge each sheet independently
        merged_facturas, facturas_stats = self.merge_records_by_uuid(
            facturas_dicts,
            master_facturas
        )

        merged_complementos, complementos_stats = self.merge_records_by_uuid(
            complementos_dicts,
            master_complementos
        )

        # Collect all unique headers from merged data
        all_headers = self._collect_all_headers(merged_facturas, merged_complementos)
        logger.info(f"Writing Excel with {len(all_headers)} columns")

        # Write merged data to multi-sheet Excel with dynamic headers
        merged_excel_bytes = self.write_multisheet_excel_dynamic(
            merged_facturas,
            merged_complementos,
            all_headers
        )

        stats = {
            'facturas': facturas_stats,
            'complementos': complementos_stats
        }

        return merged_excel_bytes, stats

    def _collect_all_headers(
        self,
        facturas: List[Dict],
        complementos: List[Dict]
    ) -> List[str]:
        """
        Collect all unique headers from both facturas and complementos.

        Preserves order: standard headers first, then any additional columns.

        Args:
            facturas: List of factura dicts.
            complementos: List of complemento dicts.

        Returns:
            List[str]: Ordered list of all unique headers.
        """
        # Start with standard headers in order
        all_headers = list(self.HEADERS)
        seen = set(all_headers)

        # Add any additional headers from facturas
        for record in facturas:
            for key in record.keys():
                if key not in seen:
                    all_headers.append(key)
                    seen.add(key)

        # Add any additional headers from complementos
        for record in complementos:
            for key in record.keys():
                if key not in seen:
                    all_headers.append(key)
                    seen.add(key)

        return all_headers

    def write_multisheet_excel_dynamic(
        self,
        facturas_records: List[Dict],
        complementos_records: List[Dict],
        headers: List[str]
    ) -> bytes:
        """
        Write records to multi-sheet Excel with dynamic headers.

        This preserves ALL columns from the original data.

        Args:
            facturas_records: List of invoice record dicts.
            complementos_records: List of payment supplement record dicts.
            headers: List of all column headers to include.

        Returns:
            bytes: Excel file content as bytes.
        """
        try:
            workbook = Workbook()

            # Remove default sheet
            if 'Sheet' in workbook.sheetnames:
                del workbook['Sheet']

            # Create Facturas sheet
            facturas_sheet = workbook.create_sheet(title=self.SHEET_FACTURAS)
            self._write_sheet_dynamic(facturas_sheet, facturas_records, headers)
            logger.info(f"Wrote {len(facturas_records)} records to {self.SHEET_FACTURAS} sheet")

            # Create Complementos sheet
            complementos_sheet = workbook.create_sheet(title=self.SHEET_COMPLEMENTOS)
            self._write_sheet_dynamic(complementos_sheet, complementos_records, headers)
            logger.info(f"Wrote {len(complementos_records)} records to {self.SHEET_COMPLEMENTOS} sheet")

            # Save to bytes
            excel_buffer = io.BytesIO()
            workbook.save(excel_buffer)
            excel_buffer.seek(0)
            excel_bytes = excel_buffer.read()

            total_records = len(facturas_records) + len(complementos_records)
            logger.info(f"Wrote {total_records} total records with {len(headers)} columns to multi-sheet Excel ({len(excel_bytes)} bytes)")
            return excel_bytes

        except Exception as e:
            logger.error(f"Error writing multi-sheet Excel (dynamic): {e}")
            raise

    def _write_sheet_dynamic(
        self,
        sheet,
        records: List[Dict],
        headers: List[str]
    ) -> None:
        """
        Write records to a single sheet with dynamic headers.

        Args:
            sheet: openpyxl worksheet object.
            records: List of record dicts to write.
            headers: List of all column headers.
        """
        # Write headers with styling
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for col_idx, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Write data rows
        for row_idx, record in enumerate(records, start=2):
            for col_idx, header in enumerate(headers, start=1):
                value = record.get(header, "")
                sheet.cell(row=row_idx, column=col_idx, value=value)

        # Auto-size columns
        for col_idx, header in enumerate(headers, start=1):
            column_letter = openpyxl.utils.get_column_letter(col_idx)
            # Set different widths based on column type
            if header in ["UUID", "UUIDs relacionados"]:
                sheet.column_dimensions[column_letter].width = 40
            elif header in ["Conceptos", "Razon emisor", "Razon receptor", "Domicilio receptor"]:
                sheet.column_dimensions[column_letter].width = 50
            elif header in ["RFC emisor", "RFC receptor"]:
                sheet.column_dimensions[column_letter].width = 15
            else:
                sheet.column_dimensions[column_letter].width = 18


# Singleton instance
_excel_merge_service_mx: Optional[ExcelMergeServiceMX] = None


def get_excel_merge_service_mx() -> ExcelMergeServiceMX:
    """
    Get or create the Excel merge service MX singleton.

    Returns:
        ExcelMergeServiceMX instance.
    """
    global _excel_merge_service_mx
    if _excel_merge_service_mx is None:
        _excel_merge_service_mx = ExcelMergeServiceMX()
    return _excel_merge_service_mx
