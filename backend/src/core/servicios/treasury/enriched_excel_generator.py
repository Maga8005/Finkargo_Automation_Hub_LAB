"""
Enriched Excel Generator for Treasury Declaration-Historial Matching.

Generates output Excel file with declaration columns populated based on match results.
"""

import io
import logging
from typing import List, Dict, Optional
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

from src.interface.treasury_matching_dtos import (
    MatchResult,
    MatchStatus,
    MatchingStatistics,
)

logger = logging.getLogger(__name__)

# Finkargo brand colors
FINKARGO_PRIMARY = "0C147B"  # Dark blue
FINKARGO_LIGHT = "77A1E2"    # Light blue
FINKARGO_SUCCESS = "2CA14D"  # Green
FINKARGO_ERROR = "CC071E"    # Red
FINKARGO_WARNING = "F19F90"  # Coral


class EnrichedExcelGenerator:
    """
    Service for generating enriched Excel files with match results.

    Creates output Excel with:
    1. Original data with populated declaration columns
    2. Summary sheet with statistics
    3. Unmatched records sheet
    """

    def generate_enriched_excel(
        self,
        original_df: pd.DataFrame,
        results: List[MatchResult],
        statistics: MatchingStatistics,
        column_mapping: Dict[str, Optional[str]]
    ) -> bytes:
        """
        Generate enriched Excel file with match results.

        Args:
            original_df: Original Historial de Pagos DataFrame
            results: List of match results
            statistics: Matching statistics
            column_mapping: Column name mapping

        Returns:
            Excel file as bytes
        """
        logger.info(f"Generating enriched Excel with {len(results)} match results")

        # Create workbook
        wb = Workbook()

        # Create main data sheet
        ws_data = wb.active
        ws_data.title = "Historial Enriquecido"

        # Create summary sheet
        ws_summary = wb.create_sheet("Resumen")

        # Create unmatched sheet
        ws_unmatched = wb.create_sheet("No Coincidentes")

        # Build row-to-result mapping
        row_to_result: Dict[int, MatchResult] = {}
        for result in results:
            for row_num in result.payment_group.record_row_numbers:
                row_to_result[row_num] = result

        # Find or create declaration columns in original DataFrame
        declaracion_col = column_mapping.get('declaracion_cambio_numero')
        dc_nombre_col = column_mapping.get('dc_nombre')

        # Make a copy to avoid modifying original
        df_enriched = original_df.copy()

        # Add columns if they don't exist
        if declaracion_col is None:
            declaracion_col = 'Declaracion de Cambio Numero'
            df_enriched[declaracion_col] = ''
        if dc_nombre_col is None:
            dc_nombre_col = 'DC Nombre'
            df_enriched[dc_nombre_col] = ''

        # Populate declaration columns based on match results
        for idx, row in df_enriched.iterrows():
            row_number = int(idx) + 2  # Excel is 1-indexed with header

            if row_number in row_to_result:
                result = row_to_result[row_number]
                if result.declaration:
                    df_enriched.at[idx, declaracion_col] = result.declaration.declaration_number
                    df_enriched.at[idx, dc_nombre_col] = result.declaration.pdf_file_name

        # Write main data sheet
        self._write_data_sheet(ws_data, df_enriched)

        # Write summary sheet
        self._write_summary_sheet(ws_summary, statistics, results)

        # Write unmatched sheet
        unmatched_results = [r for r in results if r.match_status == MatchStatus.UNMATCHED]
        self._write_unmatched_sheet(ws_unmatched, unmatched_results, df_enriched, row_to_result)

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info("Enriched Excel generated successfully")
        return output.getvalue()

    def _write_data_sheet(self, ws, df: pd.DataFrame):
        """
        Write data to the main sheet with Finkargo styling.

        Args:
            ws: Worksheet to write to
            df: DataFrame with enriched data
        """
        # Define styles
        header_fill = PatternFill(start_color=FINKARGO_PRIMARY, end_color=FINKARGO_PRIMARY, fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Write DataFrame to worksheet
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True)):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx + 1, column=c_idx, value=value)
                cell.border = thin_border

                if r_idx == 0:
                    # Header row
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment

        # Adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Freeze header row
        ws.freeze_panes = "A2"

    def _write_summary_sheet(
        self,
        ws,
        statistics: MatchingStatistics,
        results: List[MatchResult]
    ):
        """
        Write summary statistics to sheet.

        Args:
            ws: Worksheet to write to
            statistics: Matching statistics
            results: Match results for detailed breakdown
        """
        # Define styles
        title_font = Font(size=14, bold=True, color=FINKARGO_PRIMARY)
        header_font = Font(bold=True)  # noqa: F841 - kept for future styling

        # Title
        ws['A1'] = "Resumen de Coincidencias"
        ws['A1'].font = title_font

        # Statistics
        stats_data = [
            ("Métrica", "Valor"),
            ("Total de Grupos de Pago", statistics.total_payment_groups),
            ("Grupos Coincidentes", statistics.matched_groups),
            ("Coincidencias Parciales", statistics.partial_matches),
            ("Grupos Sin Coincidencia", statistics.unmatched_groups),
            ("Grupos con Conflicto", statistics.conflict_groups),
            ("", ""),
            ("Porcentaje de Coincidencia", f"{statistics.match_percentage:.1f}%"),
            ("Confianza Promedio", f"{statistics.average_confidence:.2f}"),
            ("", ""),
            ("Total de Declaraciones", statistics.total_declarations),
            ("Declaraciones Usadas", statistics.declarations_used),
            ("Declaraciones Sin Usar", statistics.declarations_unused),
        ]

        for row_idx, (label, value) in enumerate(stats_data, start=3):
            ws.cell(row=row_idx, column=1, value=label)
            ws.cell(row=row_idx, column=2, value=value)

            if row_idx == 3:
                ws.cell(row=row_idx, column=1).font = header_font
                ws.cell(row=row_idx, column=2).font = header_font

        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20

        # Add confidence distribution
        ws['A20'] = "Distribución de Confianza"
        ws['A20'].font = title_font

        perfect_matches = sum(1 for r in results if r.match_confidence >= 0.95)
        good_matches = sum(1 for r in results if 0.70 <= r.match_confidence < 0.95)
        possible_matches = sum(1 for r in results if 0.50 <= r.match_confidence < 0.70)
        low_confidence = sum(1 for r in results if 0 < r.match_confidence < 0.50)

        confidence_data = [
            ("Rango", "Cantidad"),
            ("Perfecta (95-100%)", perfect_matches),
            ("Buena (70-94%)", good_matches),
            ("Posible (50-69%)", possible_matches),
            ("Baja (1-49%)", low_confidence),
        ]

        for row_idx, (label, value) in enumerate(confidence_data, start=22):
            ws.cell(row=row_idx, column=1, value=label)
            ws.cell(row=row_idx, column=2, value=value)

            if row_idx == 22:
                ws.cell(row=row_idx, column=1).font = header_font
                ws.cell(row=row_idx, column=2).font = header_font

    def _write_unmatched_sheet(
        self,
        ws,
        unmatched_results: List[MatchResult],
        df_enriched: pd.DataFrame,
        row_to_result: Dict[int, MatchResult]
    ):
        """
        Write unmatched records to a separate sheet.

        Args:
            ws: Worksheet to write to
            unmatched_results: List of unmatched results
            df_enriched: Enriched DataFrame
            row_to_result: Row to result mapping
        """
        # Define styles
        title_font = Font(size=14, bold=True, color=FINKARGO_PRIMARY)
        header_fill = PatternFill(start_color=FINKARGO_WARNING, end_color=FINKARGO_WARNING, fill_type="solid")
        header_font = Font(bold=True)

        # Title
        ws['A1'] = "Registros Sin Coincidencia"
        ws['A1'].font = title_font

        if not unmatched_results:
            ws['A3'] = "No hay registros sin coincidencia"
            return

        # Headers
        headers = ["Cliente", "NIT", "Fecha de Pago", "Capital Total", "Registros", "Filas"]
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font

        # Data
        for row_idx, result in enumerate(unmatched_results, start=4):
            group = result.payment_group
            ws.cell(row=row_idx, column=1, value=group.cliente)
            ws.cell(row=row_idx, column=2, value=group.identificacion_cliente)
            ws.cell(row=row_idx, column=3, value=group.fecha_pago)
            ws.cell(row=row_idx, column=4, value=group.total_capital)
            ws.cell(row=row_idx, column=5, value=group.record_count)
            ws.cell(row=row_idx, column=6, value=", ".join(map(str, group.record_row_numbers)))

        # Adjust column widths
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 30


# Singleton instance
enriched_excel_generator = EnrichedExcelGenerator()
