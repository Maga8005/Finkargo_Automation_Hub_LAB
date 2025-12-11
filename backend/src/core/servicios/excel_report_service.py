"""
Excel Report Service

Servicio para generar reportes de facturación en formato Excel.
Utiliza openpyxl para crear archivos Excel con formato profesional.
"""

import io
import logging
from typing import List, Dict
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExcelReportService:
    """
    Servicio para generar reportes de facturación en Excel.

    Genera archivos Excel con:
    - Headers formateados
    - Datos de facturas
    - Totales calculados
    - Resumen de archivos encontrados/faltantes
    """

    # Estilos
    HEADER_FONT = Font(name='Arial', size=11, bold=True, color='FFFFFF')
    HEADER_FILL = PatternFill(start_color='0C147B', end_color='0C147B', fill_type='solid')
    HEADER_ALIGNMENT = Alignment(horizontal='center', vertical='center', wrap_text=True)

    DATA_FONT = Font(name='Arial', size=10)
    DATA_ALIGNMENT = Alignment(horizontal='left', vertical='center')
    NUMBER_ALIGNMENT = Alignment(horizontal='right', vertical='center')

    TOTAL_FONT = Font(name='Arial', size=11, bold=True)
    TOTAL_FILL = PatternFill(start_color='E5E7EB', end_color='E5E7EB', fill_type='solid')

    BORDER_THIN = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    def __init__(self):
        """Inicializa el servicio de generación de Excel."""
        pass

    def generate_invoice_report(
        self,
        invoices: List[Dict],
        file_status: Dict[str, Dict[str, bool]],
        metadata: Dict = None
    ) -> io.BytesIO:
        """
        Genera un reporte de facturas en formato Excel.

        Args:
            invoices: Lista de facturas con datos.
            file_status: Dict con UUID como key y {pdf_found, xml_found} como value.
            metadata: Información adicional (código operación, RFC, fechas, etc.).

        Returns:
            BytesIO: Contenido del archivo Excel.
        """
        try:
            wb = Workbook()

            # Check if this is a combined report (has document_type field)
            has_combined_data = any(
                invoice.get("document_type") == "complemento_pago"
                for invoice in invoices
            )

            if has_combined_data:
                # Separate facturas and complementos
                facturas = [i for i in invoices if i.get("document_type") != "complemento_pago"]
                complementos = [i for i in invoices if i.get("document_type") == "complemento_pago"]

                # Create Facturas sheet
                ws_facturas = wb.active
                ws_facturas.title = "Facturas"
                self._generate_sheet_content(ws_facturas, facturas, file_status, metadata, "Facturas")

                # Create Complementos sheet if there are any
                if complementos:
                    ws_complementos = wb.create_sheet(title="Complementos de Pago")
                    self._generate_sheet_content(ws_complementos, complementos, file_status, metadata, "Complementos de Pago")

                # Create Resumen sheet
                ws_resumen = wb.create_sheet(title="Resumen")
                self._generate_summary_sheet(ws_resumen, facturas, complementos, file_status, metadata)

                logger.info(
                    f"Reporte Excel combinado generado: {len(facturas)} facturas, "
                    f"{len(complementos)} complementos"
                )
            else:
                # Standard single-sheet report
                ws = wb.active
                ws.title = "Reporte Facturación"
                self._generate_sheet_content(ws, invoices, file_status, metadata)

                logger.info(f"Reporte Excel generado: {len(invoices)} facturas")

            # Guardar en BytesIO
            excel_buffer = io.BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)

            return excel_buffer

        except Exception as e:
            logger.error(f"Error al generar reporte Excel: {str(e)}")
            raise

    def _generate_sheet_content(
        self,
        ws,
        invoices: List[Dict],
        file_status: Dict[str, Dict[str, bool]],
        metadata: Dict = None,
        sheet_title: str = None
    ):
        """
        Generates content for a single sheet.

        Args:
            ws: Worksheet to populate
            invoices: List of invoice data
            file_status: Dict with file availability status
            metadata: Report metadata
            sheet_title: Optional title for the sheet header
        """
        # Metadata del reporte
        if metadata:
            self._add_report_metadata(ws, metadata, sheet_title)
            start_row = 6
        else:
            start_row = 1

        # Headers
        headers = [
            "UUID",
            "Código Operación",
            "Conceptos",
            "RFC Receptor",
            "Razón Social",
            "Fecha Emisión",
            "SubTotal",
            "IVA Trasladado",
            "IVA Exento",
            "Total",
            "UUIDs relacionados",
            "Tipo",
            "Estado PDF",
            "Estado XML"
        ]

        self._add_headers(ws, headers, start_row)

        # Datos
        data_start_row = start_row + 1
        missing_files = []

        for idx, invoice in enumerate(invoices, start=1):
            row = data_start_row + idx - 1
            uuid = invoice.get("uuid", "")

            # Status de archivos
            status = file_status.get(uuid, {"pdf_found": False, "xml_found": False})
            pdf_status = "Disponible" if status["pdf_found"] else "No disponible"
            xml_status = "Disponible" if status["xml_found"] else "No disponible"

            if not status["pdf_found"] or not status["xml_found"]:
                missing_files.append({
                    "uuid": uuid,
                    "codigo": invoice.get("codigo_operacion", ""),
                    "pdf": status["pdf_found"],
                    "xml": status["xml_found"]
                })

            # Datos de la fila
            row_data = [
                uuid,
                invoice.get("codigo_operacion", ""),
                invoice.get("conceptos", ""),
                invoice.get("rfc_receptor", ""),
                invoice.get("razon_receptor", ""),
                invoice.get("fecha_emision", ""),
                invoice.get("subtotal", 0),
                invoice.get("iva_trasladado", 0),
                invoice.get("iva_exento", 0),
                invoice.get("total", 0),
                invoice.get("uuid_relacionados", ""),
                invoice.get("tipo_comprobante", ""),
                pdf_status,
                xml_status
            ]

            self._add_data_row(ws, row, row_data)

        # Totales
        if invoices:
            total_row = data_start_row + len(invoices)
            self._add_totals_row(ws, total_row, data_start_row, len(invoices), len(headers))

            # Resumen de archivos faltantes
            if missing_files:
                summary_row = total_row + 3
                self._add_missing_files_summary(ws, summary_row, missing_files)

        # Ajustar anchos de columna
        self._adjust_column_widths(ws, headers)

    def _generate_summary_sheet(
        self,
        ws,
        facturas: List[Dict],
        complementos: List[Dict],
        file_status: Dict[str, Dict[str, bool]],
        metadata: Dict = None
    ):
        """
        Generates a summary sheet for combined reports.

        Args:
            ws: Worksheet to populate
            facturas: List of invoice data
            complementos: List of payment supplement data
            file_status: Dict with file availability status
            metadata: Report metadata
        """
        # Title
        ws['A1'] = "RESUMEN DEL REPORTE COMBINADO"
        ws['A1'].font = Font(name='Arial', size=16, bold=True, color='0C147B')
        ws.merge_cells('A1:D1')

        ws['A3'] = f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A3'].font = Font(name='Arial', size=10, italic=True)

        # Metadata
        if metadata:
            row = 5
            if metadata.get("codigo_operacion"):
                ws[f'A{row}'] = f"Código de Operación: {metadata['codigo_operacion']}"
                row += 1
            if metadata.get("rfc"):
                ws[f'A{row}'] = f"RFC: {metadata['rfc']}"
                row += 1

        # Summary table
        start_row = 8

        # Headers
        headers = ["Tipo de Documento", "Cantidad", "Total (USD)", "PDFs Disponibles", "XMLs Disponibles"]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=start_row, column=col_idx)
            cell.value = header
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.HEADER_ALIGNMENT
            cell.border = self.BORDER_THIN

        # Facturas row
        facturas_pdfs = sum(1 for f in facturas if file_status.get(f.get("uuid", ""), {}).get("pdf_found", False))
        facturas_xmls = sum(1 for f in facturas if file_status.get(f.get("uuid", ""), {}).get("xml_found", False))
        facturas_total = sum(f.get("total", 0) for f in facturas)

        facturas_row = start_row + 1
        ws.cell(row=facturas_row, column=1).value = "Facturas"
        ws.cell(row=facturas_row, column=2).value = len(facturas)
        ws.cell(row=facturas_row, column=3).value = facturas_total
        ws.cell(row=facturas_row, column=3).number_format = '$#,##0.00'
        ws.cell(row=facturas_row, column=4).value = f"{facturas_pdfs}/{len(facturas)}"
        ws.cell(row=facturas_row, column=5).value = f"{facturas_xmls}/{len(facturas)}"

        for col in range(1, 6):
            ws.cell(row=facturas_row, column=col).border = self.BORDER_THIN
            ws.cell(row=facturas_row, column=col).font = self.DATA_FONT

        # Complementos row
        complementos_pdfs = sum(1 for c in complementos if file_status.get(c.get("uuid", ""), {}).get("pdf_found", False))
        complementos_xmls = sum(1 for c in complementos if file_status.get(c.get("uuid", ""), {}).get("xml_found", False))
        complementos_total = sum(c.get("total", 0) for c in complementos)

        complementos_row = start_row + 2
        ws.cell(row=complementos_row, column=1).value = "Complementos de Pago"
        ws.cell(row=complementos_row, column=2).value = len(complementos)
        ws.cell(row=complementos_row, column=3).value = complementos_total
        ws.cell(row=complementos_row, column=3).number_format = '$#,##0.00'
        ws.cell(row=complementos_row, column=4).value = f"{complementos_pdfs}/{len(complementos)}"
        ws.cell(row=complementos_row, column=5).value = f"{complementos_xmls}/{len(complementos)}"

        for col in range(1, 6):
            ws.cell(row=complementos_row, column=col).border = self.BORDER_THIN
            ws.cell(row=complementos_row, column=col).font = self.DATA_FONT

        # Totals row
        total_row = start_row + 3
        ws.cell(row=total_row, column=1).value = "TOTAL"
        ws.cell(row=total_row, column=1).font = self.TOTAL_FONT
        ws.cell(row=total_row, column=2).value = len(facturas) + len(complementos)
        ws.cell(row=total_row, column=2).font = self.TOTAL_FONT
        ws.cell(row=total_row, column=3).value = facturas_total + complementos_total
        ws.cell(row=total_row, column=3).font = self.TOTAL_FONT
        ws.cell(row=total_row, column=3).number_format = '$#,##0.00'

        for col in range(1, 6):
            ws.cell(row=total_row, column=col).fill = self.TOTAL_FILL
            ws.cell(row=total_row, column=col).border = self.BORDER_THIN

        # Adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 18

    def _add_report_metadata(self, ws, metadata: Dict, sheet_title: str = None):
        """Agrega metadata del reporte al inicio del Excel."""
        if sheet_title:
            ws['A1'] = f"Reporte de {sheet_title} - Finkargo MX"
        else:
            ws['A1'] = "Reporte de Facturación - Finkargo MX"
        ws['A1'].font = Font(name='Arial', size=14, bold=True, color='0C147B')

        row = 2
        if metadata.get("codigo_operacion"):
            ws[f'A{row}'] = f"Código de Operación: {metadata['codigo_operacion']}"
            row += 1

        if metadata.get("rfc"):
            ws[f'A{row}'] = f"RFC: {metadata['rfc']}"
            row += 1

        if metadata.get("fecha_inicio") and metadata.get("fecha_fin"):
            ws[f'A{row}'] = f"Período: {metadata['fecha_inicio']} - {metadata['fecha_fin']}"
            row += 1

        ws[f'A{row}'] = f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def _add_headers(self, ws, headers: List[str], row: int):
        """Agrega headers con formato al Excel."""
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col_idx)
            cell.value = header
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = self.HEADER_ALIGNMENT
            cell.border = self.BORDER_THIN

    def _add_data_row(self, ws, row: int, row_data: List):
        """Agrega una fila de datos con formato."""
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row, column=col_idx)
            cell.value = value
            cell.font = self.DATA_FONT
            cell.border = self.BORDER_THIN

            # Formato específico por columna
            if col_idx in [7, 8, 9, 10]:  # Columnas de montos
                cell.alignment = self.NUMBER_ALIGNMENT
                cell.number_format = '$#,##0.00'
            elif col_idx == 6:  # Fecha
                cell.alignment = self.DATA_ALIGNMENT
                if isinstance(value, datetime):
                    cell.number_format = 'DD/MM/YYYY'
            else:
                cell.alignment = self.DATA_ALIGNMENT

            # Color para archivos no disponibles
            if col_idx in [13, 14] and value == "No disponible":
                cell.font = Font(name='Arial', size=10, color='CC071E')

    def _add_totals_row(self, ws, row: int, data_start_row: int, num_rows: int, num_cols: int):
        """Agrega fila de totales."""
        # Label
        cell = ws.cell(row=row, column=1)
        cell.value = "TOTAL"
        cell.font = self.TOTAL_FONT
        cell.fill = self.TOTAL_FILL
        cell.alignment = Alignment(horizontal='right', vertical='center')
        cell.border = self.BORDER_THIN

        # Merge cells for label
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)

        # Totales de montos (columnas 7, 8, 9, 10)
        for col_idx in [7, 8, 9, 10]:
            cell = ws.cell(row=row, column=col_idx)
            col_letter = get_column_letter(col_idx)
            cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{data_start_row + num_rows - 1})"
            cell.font = self.TOTAL_FONT
            cell.fill = self.TOTAL_FILL
            cell.alignment = self.NUMBER_ALIGNMENT
            cell.number_format = '$#,##0.00'
            cell.border = self.BORDER_THIN

        # Celdas vacías restantes
        for col_idx in range(11, num_cols + 1):
            cell = ws.cell(row=row, column=col_idx)
            cell.fill = self.TOTAL_FILL
            cell.border = self.BORDER_THIN

    def _add_missing_files_summary(self, ws, start_row: int, missing_files: List[Dict]):
        """Agrega resumen de archivos faltantes."""
        # Título
        ws[f'A{start_row}'] = "ARCHIVOS FALTANTES"
        ws[f'A{start_row}'].font = Font(name='Arial', size=12, bold=True, color='CC071E')

        # Headers
        header_row = start_row + 1
        ws[f'A{header_row}'] = "UUID"
        ws[f'B{header_row}'] = "Código Operación"
        ws[f'C{header_row}'] = "PDF"
        ws[f'D{header_row}'] = "XML"

        for col in ['A', 'B', 'C', 'D']:
            ws[f'{col}{header_row}'].font = Font(name='Arial', size=10, bold=True)
            ws[f'{col}{header_row}'].fill = PatternFill(start_color='FFE4E4', end_color='FFE4E4', fill_type='solid')

        # Datos de archivos faltantes
        for idx, file_info in enumerate(missing_files, start=1):
            row = header_row + idx
            ws[f'A{row}'] = file_info["uuid"]
            ws[f'B{row}'] = file_info["codigo"]
            ws[f'C{row}'] = "✓" if file_info["pdf"] else "✗"
            ws[f'D{row}'] = "✓" if file_info["xml"] else "✗"

    def _adjust_column_widths(self, ws, headers: List[str]):
        """Ajusta automáticamente el ancho de las columnas."""
        column_widths = {
            1: 38,  # UUID
            2: 25,  # Código Operación
            3: 30,  # Conceptos
            4: 15,  # RFC
            5: 35,  # Razón Social
            6: 12,  # Fecha
            7: 12,  # SubTotal
            8: 12,  # IVA Trasladado
            9: 12,  # IVA Exento
            10: 12,  # Total
            11: 38,  # UUIDs relacionados
            12: 15,  # Tipo
            13: 14,  # Estado PDF
            14: 14,  # Estado XML
        }

        for col_idx, width in column_widths.items():
            ws.column_dimensions[get_column_letter(col_idx)].width = width


# Singleton instance
_excel_service_instance = None


def get_excel_service() -> ExcelReportService:
    """
    Obtiene la instancia singleton del servicio de Excel.

    Returns:
        ExcelReportService: Instancia del servicio.
    """
    global _excel_service_instance
    if _excel_service_instance is None:
        _excel_service_instance = ExcelReportService()
    return _excel_service_instance
