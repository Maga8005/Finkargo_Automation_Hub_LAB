"""
Broker Incentive Excel Generator Service

This service generates styled Excel files from broker incentive extraction results.
Creates professional reports with:
- Main data sheet with all extracted records
- Summary statistics sheet
- Finkargo brand styling

Author: Finkargo Automation Hub
Date: 2025-12-16
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
import logging

from src.interface.broker_incentive_dtos import BrokerIncentiveData, ContractType

logger = logging.getLogger(__name__)


class BrokerIncentiveExcelGenerator:
    """
    Service for generating styled Excel files from broker incentive data.

    Creates professional Excel reports with:
    - Sheet 1 "Incentivos": All broker records with extracted data
    - Sheet 2 "Resumen": Summary statistics and analysis
    - Professional Finkargo styling with headers, borders, and filters

    Example usage:
        generator = BrokerIncentiveExcelGenerator()
        output_path = generator.generate_excel(
            records=incentive_records,
            output_path="/tmp/broker_incentives_20251216.xlsx"
        )
    """

    # Finkargo brand colors
    HEADER_BG_COLOR = '0C147B'  # Primary dark blue
    SUCCESS_BG_COLOR = 'E0F7E6'
    SUCCESS_TEXT_COLOR = '2CA14D'
    WARNING_BG_COLOR = 'FFF3CD'
    WARNING_TEXT_COLOR = '856404'
    ERROR_BG_COLOR = 'FFE4E4'
    ERROR_TEXT_COLOR = 'CC071E'
    NEUTRAL_BG_COLOR = 'E5E7EB'
    NEUTRAL_TEXT_COLOR = '6B7280'

    # Column mappings for Excel output
    COLUMN_MAPPING = {
        'broker_name': 'Nombre Broker',
        'rfc': 'RFC',
        'signatory_name': 'Nombre Firmante',
        'credit_line_incentive_pct': 'Incentivo Línea Crédito (%)',
        'operations_incentive_pct': 'Incentivo Operaciones (%)',
        'contract_type': 'Tipo Contrato',
        'contract_date': 'Fecha Contrato',
        'pdf_path': 'Archivo Fuente',
        'extraction_date': 'Fecha Extracción',
        'warnings': 'Notas',
    }

    def __init__(self):
        """Initialize the Excel generator service."""
        logger.info("BrokerIncentiveExcelGenerator initialized")

    def generate_excel(
        self,
        records: List[BrokerIncentiveData],
        output_path: str
    ) -> str:
        """
        Generate Excel file from broker incentive records.

        Args:
            records: List of BrokerIncentiveData objects
            output_path: Path where Excel file should be saved

        Returns:
            str: Absolute path to generated Excel file

        Raises:
            ValueError: If output directory doesn't exist
        """
        logger.info(f"Generating broker incentive Excel with {len(records)} records")

        # Validate output path
        output_path_obj = Path(output_path)
        if not output_path_obj.parent.exists():
            error_msg = f"Output directory does not exist: {output_path_obj.parent}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Create DataFrame from records
        df = self._create_dataframe(records)

        # Calculate statistics
        statistics = self._calculate_statistics(records)

        try:
            # Write to Excel with pandas
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write main data sheet
                df.to_excel(writer, sheet_name='Incentivos', index=False)

                # Write summary sheet
                self._create_summary_sheet(writer, statistics)

            # Apply styling
            self._apply_styling(output_path)

            file_size = output_path_obj.stat().st_size
            logger.info(f"Generated Excel file at '{output_path}' ({file_size} bytes)")

            return str(output_path_obj.absolute())

        except Exception as e:
            error_msg = f"Failed to generate Excel file: {e}"
            logger.error(error_msg)
            raise

    def _create_dataframe(self, records: List[BrokerIncentiveData]) -> pd.DataFrame:
        """
        Create pandas DataFrame from broker incentive records.

        Args:
            records: List of BrokerIncentiveData objects

        Returns:
            DataFrame with formatted columns
        """
        logger.info("Creating broker incentive DataFrame")

        data = []
        for record in records:
            row = {
                'Nombre Broker': record.broker_name,
                'RFC': record.rfc or 'N/A',
                'Nombre Firmante': record.signatory_name or 'N/A',
                'Incentivo Línea Crédito (%)': (
                    f"{record.credit_line_incentive_pct:.2f}%"
                    if record.credit_line_incentive_pct is not None
                    else 'N/A'
                ),
                'Incentivo Operaciones (%)': (
                    f"{record.operations_incentive_pct:.2f}%"
                    if record.operations_incentive_pct is not None
                    else 'N/A'
                ),
                'Tipo Contrato': self._format_contract_type(record.contract_type),
                'Fecha Contrato': record.contract_date or 'N/A',
                'Archivo Fuente': record.pdf_path,
                'Fecha Extracción': self._format_datetime(record.extraction_date),
                'Notas': '; '.join(record.warnings) if record.warnings else '',
            }
            data.append(row)

        df = pd.DataFrame(data)
        logger.info(f"Created DataFrame with {len(df)} rows")

        return df

    def _format_contract_type(self, contract_type: ContractType) -> str:
        """Format contract type for display."""
        if contract_type == ContractType.BONO:
            return "Bono"
        elif contract_type == ContractType.INCENTIVOS:
            return "Incentivos"
        else:
            return "Desconocido"

    def _format_datetime(self, iso_datetime: str) -> str:
        """Format ISO datetime for display."""
        try:
            dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError):
            return iso_datetime

    def _calculate_statistics(self, records: List[BrokerIncentiveData]) -> Dict[str, Any]:
        """
        Calculate summary statistics from records.

        Args:
            records: List of BrokerIncentiveData objects

        Returns:
            Dictionary with statistics
        """
        logger.info("Calculating statistics")

        total_records = len(records)

        # Contract type counts
        bono_count = sum(1 for r in records if r.contract_type == ContractType.BONO)
        incentivos_count = sum(1 for r in records if r.contract_type == ContractType.INCENTIVOS)
        unknown_count = sum(1 for r in records if r.contract_type == ContractType.UNKNOWN)

        # RFC and signatory completeness
        rfc_found = sum(1 for r in records if r.rfc)
        signatory_found = sum(1 for r in records if r.signatory_name)

        # Incentive percentages
        credit_line_values = [
            r.credit_line_incentive_pct
            for r in records
            if r.credit_line_incentive_pct is not None
        ]
        operations_values = [
            r.operations_incentive_pct
            for r in records
            if r.operations_incentive_pct is not None
        ]

        avg_credit_line = (
            sum(credit_line_values) / len(credit_line_values)
            if credit_line_values else 0
        )
        avg_operations = (
            sum(operations_values) / len(operations_values)
            if operations_values else 0
        )

        # Extraction success rate
        successful = sum(1 for r in records if r.extraction_confidence > 0.5)
        success_rate = (successful / total_records * 100) if total_records > 0 else 0

        statistics = {
            'total_records': total_records,
            'bono_contracts': bono_count,
            'incentivos_contracts': incentivos_count,
            'unknown_contracts': unknown_count,
            'rfc_found': rfc_found,
            'rfc_missing': total_records - rfc_found,
            'signatory_found': signatory_found,
            'signatory_missing': total_records - signatory_found,
            'credit_line_extracted': len(credit_line_values),
            'operations_extracted': len(operations_values),
            'average_credit_line_pct': avg_credit_line,
            'average_operations_pct': avg_operations,
            'extraction_success_rate': success_rate,
        }

        logger.info(f"Statistics calculated: {total_records} records, {success_rate:.1f}% success rate")

        return statistics

    def _create_summary_sheet(self, writer: pd.ExcelWriter, statistics: Dict[str, Any]):
        """
        Create summary statistics sheet.

        Args:
            writer: pandas ExcelWriter object
            statistics: Dictionary with calculated statistics
        """
        logger.info("Creating summary sheet")

        summary_data = [
            ['Resumen de Extracción de Incentivos Brokers', ''],
            ['', ''],
            ['Métrica', 'Valor'],
            ['Total de Registros', statistics['total_records']],
            ['Tasa de Éxito de Extracción', f"{statistics['extraction_success_rate']:.1f}%"],
            ['', ''],
            ['Tipos de Contrato', ''],
            ['  Contratos Bono', statistics['bono_contracts']],
            ['  Contratos Incentivos', statistics['incentivos_contracts']],
            ['  Contratos Desconocidos', statistics['unknown_contracts']],
            ['', ''],
            ['Completitud de Datos', ''],
            ['  RFC Encontrado', statistics['rfc_found']],
            ['  RFC Faltante', statistics['rfc_missing']],
            ['  Firmante Encontrado', statistics['signatory_found']],
            ['  Firmante Faltante', statistics['signatory_missing']],
            ['', ''],
            ['Incentivos Extraídos', ''],
            ['  Incentivo Línea Crédito (registros)', statistics['credit_line_extracted']],
            ['  Incentivo Operaciones (registros)', statistics['operations_extracted']],
            ['  Promedio Línea Crédito (%)', f"{statistics['average_credit_line_pct']:.2f}%"],
            ['  Promedio Operaciones (%)', f"{statistics['average_operations_pct']:.2f}%"],
            ['', ''],
            ['Generado', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumen', index=False, header=False)

        logger.info("Summary sheet created")

    def _apply_styling(self, file_path: str):
        """
        Apply professional styling to Excel file.

        Args:
            file_path: Path to Excel file
        """
        logger.info("Applying styling to Excel file")

        wb = load_workbook(file_path)

        # Style main data sheet
        self._style_data_sheet(wb['Incentivos'])

        # Style summary sheet
        self._style_summary_sheet(wb['Resumen'])

        wb.save(file_path)

        logger.info("Styling applied successfully")

    def _style_data_sheet(self, sheet):
        """
        Apply styling to the main data sheet.

        Args:
            sheet: openpyxl worksheet object
        """
        # Define styles
        header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(
            start_color=self.HEADER_BG_COLOR,
            end_color=self.HEADER_BG_COLOR,
            fill_type='solid'
        )
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        border_side = Side(style='thin', color='D1D5DB')
        border = Border(
            left=border_side,
            right=border_side,
            top=border_side,
            bottom=border_side
        )

        # Style header row
        for cell in sheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

        # Style data rows
        for row_idx in range(2, sheet.max_row + 1):
            for cell in sheet[row_idx]:
                cell.border = border
                cell.alignment = Alignment(vertical='center', wrap_text=False)

        # Conditional formatting for Tipo Contrato column (column 6)
        contract_type_col = 6
        for row_idx in range(2, sheet.max_row + 1):
            cell = sheet.cell(row=row_idx, column=contract_type_col)
            value = cell.value

            if value == 'Bono':
                cell.fill = PatternFill(
                    start_color=self.SUCCESS_BG_COLOR,
                    end_color=self.SUCCESS_BG_COLOR,
                    fill_type='solid'
                )
                cell.font = Font(color=self.SUCCESS_TEXT_COLOR, bold=True)
            elif value == 'Incentivos':
                cell.fill = PatternFill(
                    start_color=self.WARNING_BG_COLOR,
                    end_color=self.WARNING_BG_COLOR,
                    fill_type='solid'
                )
                cell.font = Font(color=self.WARNING_TEXT_COLOR, bold=True)
            elif value == 'Desconocido':
                cell.fill = PatternFill(
                    start_color=self.ERROR_BG_COLOR,
                    end_color=self.ERROR_BG_COLOR,
                    fill_type='solid'
                )
                cell.font = Font(color=self.ERROR_TEXT_COLOR, bold=True)

        # Highlight rows with N/A values in RFC or incentives
        for row_idx in range(2, sheet.max_row + 1):
            rfc_cell = sheet.cell(row=row_idx, column=2)  # RFC column
            credit_cell = sheet.cell(row=row_idx, column=4)  # Credit line column
            ops_cell = sheet.cell(row=row_idx, column=5)  # Operations column

            if rfc_cell.value == 'N/A':
                rfc_cell.fill = PatternFill(
                    start_color=self.NEUTRAL_BG_COLOR,
                    end_color=self.NEUTRAL_BG_COLOR,
                    fill_type='solid'
                )
                rfc_cell.font = Font(color=self.NEUTRAL_TEXT_COLOR)

            if credit_cell.value == 'N/A':
                credit_cell.fill = PatternFill(
                    start_color=self.NEUTRAL_BG_COLOR,
                    end_color=self.NEUTRAL_BG_COLOR,
                    fill_type='solid'
                )
                credit_cell.font = Font(color=self.NEUTRAL_TEXT_COLOR)

            if ops_cell.value == 'N/A':
                ops_cell.fill = PatternFill(
                    start_color=self.NEUTRAL_BG_COLOR,
                    end_color=self.NEUTRAL_BG_COLOR,
                    fill_type='solid'
                )
                ops_cell.font = Font(color=self.NEUTRAL_TEXT_COLOR)

        # Auto-size columns
        column_widths = [25, 15, 25, 22, 22, 15, 15, 50, 18, 40]
        for idx, width in enumerate(column_widths, start=1):
            sheet.column_dimensions[get_column_letter(idx)].width = width

        # Freeze header row
        sheet.freeze_panes = 'A2'

        # Add auto-filter
        sheet.auto_filter.ref = sheet.dimensions

        logger.info("Data sheet styled")

    def _style_summary_sheet(self, sheet):
        """
        Apply styling to the summary sheet.

        Args:
            sheet: openpyxl worksheet object
        """
        # Style title (row 1)
        title_cell = sheet.cell(row=1, column=1)
        title_cell.font = Font(name='Calibri', size=14, bold=True, color=self.HEADER_BG_COLOR)

        # Style headers in column A
        header_font = Font(name='Calibri', size=11, bold=True, color=self.HEADER_BG_COLOR)

        for row_idx in range(1, sheet.max_row + 1):
            cell_a = sheet.cell(row=row_idx, column=1)
            cell_b = sheet.cell(row=row_idx, column=2)

            if cell_a.value and not str(cell_a.value).startswith('  '):
                cell_a.font = header_font

            cell_a.alignment = Alignment(horizontal='left', vertical='center')
            cell_b.alignment = Alignment(horizontal='left', vertical='center')

        # Set column widths
        sheet.column_dimensions['A'].width = 35
        sheet.column_dimensions['B'].width = 25

        logger.info("Summary sheet styled")
