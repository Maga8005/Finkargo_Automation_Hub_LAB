"""
Inventory Excel Generator Service

This service generates styled Excel inventory files from local directory scan results.
It transforms inventory records into professional Excel reports with:
- Main inventory sheet with all PDF records
- Summary statistics sheet
- Professional styling (header formatting, borders, filters, column widths)
- Conditional formatting for extraction status
- Auto-sized columns for readability

The generated Excel files are suitable for:
- Comprehensive declaration inventory tracking
- Manual matching when automated matching fails
- Audit trails and verification
- Business review and analysis

Example usage:
    generator = InventoryExcelGenerator()
    output_path = generator.generate_inventory_excel(
        records=inventory_records,
        output_path="/tmp/inventory_20251103.xlsx"
    )
    print(f"Generated inventory Excel at {output_path}")

Author: Finkargo Engineering
Date: 2025-11-03
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from .local_directory_scanner import InventoryRecord


class InventoryExcelGenerator:
    """
    Service for generating styled Excel inventory files from directory scan results.

    This service takes a list of InventoryRecord objects and creates a professional
    Excel file with formatted inventory data and summary statistics.

    Excel Structure:
        - Sheet 1 "Inventory": All PDF records with metadata
        - Sheet 2 "Summary": Statistics and analysis
        - Professional styling with headers, borders, and filters
        - Conditional formatting for extraction status
    """

    def __init__(self):
        """Initialize the Excel generator service."""
        print(f"INFO [InventoryExcelGenerator]: Service initialized")

    def generate_inventory_excel(
        self,
        records: List[InventoryRecord],
        output_path: str
    ) -> str:
        """
        Generate Excel inventory file from scan results.

        Args:
            records: List of InventoryRecord objects from directory scan
            output_path: Path where Excel file should be saved

        Returns:
            str: Absolute path to generated Excel file

        Raises:
            ValueError: If output directory doesn't exist
            Exception: If Excel generation fails
        """
        print(f"INFO [InventoryExcelGenerator]: Generating inventory Excel with {len(records)} records")

        # Validate output path
        output_path_obj = Path(output_path)
        if not output_path_obj.parent.exists():
            error_msg = f"Output directory does not exist: {output_path_obj.parent}"
            print(f"ERROR [InventoryExcelGenerator]: {error_msg}")
            raise ValueError(error_msg)

        # Create DataFrame from inventory records
        df = self._create_inventory_dataframe(records)

        # Calculate statistics
        statistics = self._calculate_statistics(records)

        try:
            # Write to Excel with pandas
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write inventory sheet
                df.to_excel(writer, sheet_name='Inventory', index=False)

                # Write summary sheet
                self._create_summary_sheet(writer, statistics)

            # Apply styling using openpyxl
            self._apply_inventory_styling(output_path)

            file_size = output_path_obj.stat().st_size
            print(f"SUCCESS [InventoryExcelGenerator]: Generated Excel file at '{output_path}' ({file_size} bytes)")

            return str(output_path_obj.absolute())

        except Exception as e:
            error_msg = f"Failed to generate Excel file: {str(e)}"
            print(f"ERROR [InventoryExcelGenerator]: {error_msg}")
            raise

    def _create_inventory_dataframe(self, records: List[InventoryRecord]) -> pd.DataFrame:
        """
        Create pandas DataFrame from inventory records.

        Args:
            records: List of InventoryRecord objects

        Returns:
            DataFrame with inventory columns
        """
        print(f"INFO [InventoryExcelGenerator]: Creating inventory DataFrame")

        # Convert records to dictionaries
        data = []
        for record in records:
            row = {
                'Customer Name': record.customer_name,
                'Date Folder': record.date_folder,
                'Amount Folder': record.amount_folder,
                'PDF File Name': record.pdf_file_name,
                'PDF File Path': record.pdf_file_path,
                'Declaration Number': record.declaration_number or 'N/A',
                'Extraction Status': record.extraction_status.upper(),
                'Extraction Error': record.extraction_error or '',
                'Parsed Date': record.parsed_date.strftime('%Y-%m-%d') if record.parsed_date else 'N/A',
                'Parsed Amount': f"${record.parsed_amount:,.2f}" if record.parsed_amount else 'N/A'
            }
            data.append(row)

        df = pd.DataFrame(data)

        print(f"INFO [InventoryExcelGenerator]: Created DataFrame with {len(df)} rows and {len(df.columns)} columns")

        return df

    def _calculate_statistics(self, records: List[InventoryRecord]) -> Dict[str, Any]:
        """
        Calculate summary statistics from inventory records.

        Args:
            records: List of InventoryRecord objects

        Returns:
            Dictionary with statistics
        """
        print(f"INFO [InventoryExcelGenerator]: Calculating statistics")

        # Basic counts
        total_pdfs = len(records)
        successful = sum(1 for r in records if r.extraction_status == 'success')
        partial = sum(1 for r in records if r.extraction_status == 'partial')
        failed = sum(1 for r in records if r.extraction_status == 'failed')
        pending = sum(1 for r in records if r.extraction_status == 'pending')

        # Unique values
        unique_customers = len(set(r.customer_name for r in records))
        unique_dates = len(set(r.date_folder for r in records))

        # Amounts
        amounts = [r.parsed_amount for r in records if r.parsed_amount is not None]
        total_amount = sum(amounts) if amounts else 0
        avg_amount = total_amount / len(amounts) if amounts else 0

        # Declaration numbers extracted
        declarations_found = sum(1 for r in records if r.declaration_number is not None)

        statistics = {
            'total_pdfs': total_pdfs,
            'successful_extractions': successful,
            'partial_extractions': partial,
            'failed_extractions': failed,
            'pending_extractions': pending,
            'unique_customers': unique_customers,
            'unique_dates': unique_dates,
            'total_amount': total_amount,
            'average_amount': avg_amount,
            'declarations_found': declarations_found,
            'extraction_rate': (declarations_found / total_pdfs * 100) if total_pdfs > 0 else 0
        }

        print(f"SUCCESS [InventoryExcelGenerator]: Calculated statistics: {declarations_found}/{total_pdfs} declarations found ({statistics['extraction_rate']:.1f}%)")

        return statistics

    def _create_summary_sheet(self, writer: pd.ExcelWriter, statistics: Dict[str, Any]):
        """
        Create summary statistics sheet.

        Args:
            writer: pandas ExcelWriter object
            statistics: Dictionary with calculated statistics
        """
        print(f"INFO [InventoryExcelGenerator]: Creating summary sheet")

        # Create summary data
        summary_data = [
            ['Metric', 'Value'],
            ['Total PDFs Found', statistics['total_pdfs']],
            ['Declarations Extracted', statistics['declarations_found']],
            ['Extraction Rate', f"{statistics['extraction_rate']:.1f}%"],
            ['', ''],
            ['Extraction Status Breakdown', ''],
            ['  Successful', statistics['successful_extractions']],
            ['  Partial', statistics['partial_extractions']],
            ['  Failed', statistics['failed_extractions']],
            ['  Pending', statistics['pending_extractions']],
            ['', ''],
            ['Unique Customers', statistics['unique_customers']],
            ['Unique Date Folders', statistics['unique_dates']],
            ['', ''],
            ['Total Amount', f"${statistics['total_amount']:,.2f}"],
            ['Average Amount', f"${statistics['average_amount']:,.2f}"],
            ['', ''],
            ['Generated At', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]

        # Write summary sheet
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)

        print(f"INFO [InventoryExcelGenerator]: Summary sheet created")

    def _apply_inventory_styling(self, file_path: str):
        """
        Apply professional styling to Excel inventory file.

        Args:
            file_path: Path to Excel file
        """
        print(f"INFO [InventoryExcelGenerator]: Applying styling to Excel file")

        # Load workbook
        wb = load_workbook(file_path)

        # Style inventory sheet
        self._style_inventory_sheet(wb['Inventory'])

        # Style summary sheet
        self._style_summary_sheet(wb['Summary'])

        # Save workbook
        wb.save(file_path)

        print(f"SUCCESS [InventoryExcelGenerator]: Styling applied successfully")

    def _style_inventory_sheet(self, sheet):
        """
        Apply styling to inventory sheet.

        Args:
            sheet: openpyxl worksheet object
        """
        # Define styles
        header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='0C147B', end_color='0C147B', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        border_side = Side(style='thin', color='D1D5DB')
        border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

        # Style header row
        for cell in sheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

        # Style data rows
        for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(vertical='top', wrap_text=False)

        # Conditional formatting for Extraction Status column (column 7)
        status_col = 7
        for row_idx in range(2, sheet.max_row + 1):
            cell = sheet.cell(row=row_idx, column=status_col)
            status = cell.value

            if status == 'SUCCESS':
                cell.fill = PatternFill(start_color='E0F7E6', end_color='E0F7E6', fill_type='solid')
                cell.font = Font(color='2CA14D', bold=True)
            elif status == 'PARTIAL':
                cell.fill = PatternFill(start_color='FFF3CD', end_color='FFF3CD', fill_type='solid')
                cell.font = Font(color='856404', bold=True)
            elif status == 'FAILED':
                cell.fill = PatternFill(start_color='FFE4E4', end_color='FFE4E4', fill_type='solid')
                cell.font = Font(color='CC071E', bold=True)
            elif status == 'PENDING':
                cell.fill = PatternFill(start_color='E5E7EB', end_color='E5E7EB', fill_type='solid')
                cell.font = Font(color='6B7280')

        # Auto-size columns
        for column_cells in sheet.columns:
            length = max(len(str(cell.value or '')) for cell in column_cells)
            # Limit maximum column width
            adjusted_width = min(length + 2, 50)
            sheet.column_dimensions[get_column_letter(column_cells[0].column)].width = adjusted_width

        # Freeze header row
        sheet.freeze_panes = 'A2'

        # Add auto-filter
        sheet.auto_filter.ref = sheet.dimensions

        print(f"INFO [InventoryExcelGenerator]: Inventory sheet styled")

    def _style_summary_sheet(self, sheet):
        """
        Apply styling to summary sheet.

        Args:
            sheet: openpyxl worksheet object
        """
        # Style header cells (column A)
        header_font = Font(name='Calibri', size=11, bold=True, color='0C147B')
        header_alignment = Alignment(horizontal='left', vertical='center')

        for row_idx in range(1, sheet.max_row + 1):
            cell_a = sheet.cell(row=row_idx, column=1)
            cell_b = sheet.cell(row=row_idx, column=2)

            # Bold headers in column A
            if cell_a.value and cell_a.value != '':
                cell_a.font = header_font
                cell_a.alignment = header_alignment

            # Align values in column B
            if cell_b.value and cell_b.value != '':
                cell_b.alignment = Alignment(horizontal='left', vertical='center')

        # Auto-size columns
        sheet.column_dimensions['A'].width = 30
        sheet.column_dimensions['B'].width = 25

        print(f"INFO [InventoryExcelGenerator]: Summary sheet styled")
