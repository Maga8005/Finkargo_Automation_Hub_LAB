"""
Local Directory Scanner Service

This service scans a local directory structure containing PDF declaration files,
extracts metadata from folder names, and builds an inventory of all PDFs.

Expected folder structure: ROOT/{CUSTOMER_NAME}/{DATE or MONTH}/{AMOUNT}/PDF_FILE.pdf
Example: FINKARGO DCS/BIIRTUALSCORE SAS/12-09-2025/11.081,50/DC 11.081,50.pdf
Example: FINKARGO DCS/3G SINTETICOS SAS/Septiembre/09-09-2025/10.500,00/DC 10.500,00.pdf
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .folder_name_parser import (
    parse_date_from_folder_name,
    parse_amount_from_filename,
)


class InventoryRecord:
    """
    Represents a single inventory record for a PDF file with extracted metadata.
    """

    def __init__(
        self,
        customer_name: str,
        date_folder: str,
        amount_folder: str,
        pdf_file_path: str,
        pdf_file_name: str,
        declaration_number: Optional[str] = None,
        extraction_status: str = "pending",
        extraction_error: Optional[str] = None,
        parsed_date: Optional[datetime] = None,
        parsed_amount: Optional[float] = None
    ):
        self.customer_name = customer_name
        self.date_folder = date_folder
        self.amount_folder = amount_folder
        self.pdf_file_path = pdf_file_path
        self.pdf_file_name = pdf_file_name
        self.declaration_number = declaration_number
        self.extraction_status = extraction_status
        self.extraction_error = extraction_error
        self.parsed_date = parsed_date
        self.parsed_amount = parsed_amount

    def to_dict(self) -> Dict:
        """Convert record to dictionary for serialization."""
        return {
            'customer_name': self.customer_name,
            'date_folder': self.date_folder,
            'amount_folder': self.amount_folder,
            'pdf_file_path': self.pdf_file_path,
            'pdf_file_name': self.pdf_file_name,
            'declaration_number': self.declaration_number,
            'extraction_status': self.extraction_status,
            'extraction_error': self.extraction_error,
            'parsed_date': self.parsed_date.isoformat() if self.parsed_date else None,
            'parsed_amount': self.parsed_amount
        }


class LocalDirectoryScanner:
    """
    Service for scanning local directory structures and building PDF inventories.
    """

    def __init__(self, pdf_extensions: List[str] = None):
        """
        Initialize scanner with configurable PDF file extensions.

        Args:
            pdf_extensions: List of PDF file extensions to scan (default: ['.pdf', '.PDF'])
        """
        self.pdf_extensions = pdf_extensions or ['.pdf', '.PDF']
        print(f"INFO [LocalDirectoryScanner]: Initialized with extensions: {self.pdf_extensions}")

    def scan_directory(self, root_path: str, recursive: bool = True) -> List[InventoryRecord]:
        """
        Scan directory structure and build inventory of all PDFs with metadata.

        Args:
            root_path: Root directory path to scan (e.g., "FINKARGO DCS")
            recursive: Whether to scan subdirectories recursively

        Returns:
            List of InventoryRecord objects with folder structure metadata

        Raises:
            ValueError: If root_path does not exist or is not accessible
        """
        # Validate root path
        root_path_obj = Path(root_path)
        if not root_path_obj.exists():
            error_msg = f"Root path does not exist: {root_path}"
            print(f"ERROR [LocalDirectoryScanner]: {error_msg}")
            raise ValueError(error_msg)

        if not root_path_obj.is_dir():
            error_msg = f"Root path is not a directory: {root_path}"
            print(f"ERROR [LocalDirectoryScanner]: {error_msg}")
            raise ValueError(error_msg)

        print(f"INFO [LocalDirectoryScanner]: Starting directory scan at '{root_path}'")
        print(f"INFO [LocalDirectoryScanner]: Recursive mode: {recursive}")

        inventory_records = []
        total_folders_scanned = 0
        total_pdfs_found = 0

        try:
            # Scan customer folders (top-level folders in root)
            customer_records = self._scan_customer_folders(root_path_obj, recursive)
            inventory_records.extend(customer_records)
            total_pdfs_found = len(customer_records)

            print("SUCCESS [LocalDirectoryScanner]: Scan completed")
            print(f"INFO [LocalDirectoryScanner]: Total PDFs found: {total_pdfs_found}")
            print(f"INFO [LocalDirectoryScanner]: Total folders scanned: {total_folders_scanned}")

        except Exception as e:
            print(f"ERROR [LocalDirectoryScanner]: Scan failed with error: {str(e)}")
            raise

        return inventory_records

    def _scan_customer_folders(self, root_path: Path, recursive: bool) -> List[InventoryRecord]:
        """
        Recursively scan customer folders and extract metadata.

        Args:
            root_path: Root directory path
            recursive: Whether to scan subdirectories recursively

        Returns:
            List of InventoryRecord objects
        """
        records = []

        try:
            # Iterate through customer folders (top-level directories)
            for customer_folder in root_path.iterdir():
                if not customer_folder.is_dir():
                    continue

                customer_name = customer_folder.name
                print(f"INFO [LocalDirectoryScanner]: Scanning customer folder '{customer_name}'")

                # Scan date/month folders within customer folder
                customer_records = self._scan_date_folders(customer_folder, customer_name, recursive)
                records.extend(customer_records)

                print(f"INFO [LocalDirectoryScanner]: Found {len(customer_records)} PDFs for '{customer_name}'")

        except PermissionError as e:
            print(f"ERROR [LocalDirectoryScanner]: Permission denied accessing '{root_path}': {str(e)}")
        except Exception as e:
            print(f"ERROR [LocalDirectoryScanner]: Error scanning customer folders: {str(e)}")

        return records

    def _scan_date_folders(self, customer_folder: Path, customer_name: str, recursive: bool) -> List[InventoryRecord]:
        """
        Scan date/month folders within a customer folder.

        Args:
            customer_folder: Customer folder path
            customer_name: Customer name extracted from folder
            recursive: Whether to scan subdirectories recursively

        Returns:
            List of InventoryRecord objects
        """
        records = []

        try:
            for date_folder in customer_folder.iterdir():
                if not date_folder.is_dir():
                    continue

                date_folder_name = date_folder.name
                print(f"INFO [LocalDirectoryScanner]: Scanning date folder '{date_folder_name}' for '{customer_name}'")

                # Parse date from folder name
                parsed_date = parse_date_from_folder_name(date_folder_name)

                # Scan amount folders or directly for PDFs
                if recursive:
                    folder_records = self._scan_amount_folders(
                        date_folder, customer_name, date_folder_name, parsed_date
                    )
                    records.extend(folder_records)
                else:
                    # If not recursive, only scan for PDFs in date folder
                    pdf_records = self._locate_pdfs_in_folder(
                        date_folder, customer_name, date_folder_name, None, parsed_date, None
                    )
                    records.extend(pdf_records)

        except PermissionError as e:
            print(f"ERROR [LocalDirectoryScanner]: Permission denied accessing '{customer_folder}': {str(e)}")
        except Exception as e:
            print(f"ERROR [LocalDirectoryScanner]: Error scanning date folders: {str(e)}")

        return records

    def _scan_amount_folders(
        self, date_folder: Path, customer_name: str, date_folder_name: str, parsed_date: Optional[datetime]
    ) -> List[InventoryRecord]:
        """
        Scan amount folders within a date folder.

        Args:
            date_folder: Date folder path
            customer_name: Customer name
            date_folder_name: Date folder name
            parsed_date: Parsed date from folder name

        Returns:
            List of InventoryRecord objects
        """
        records = []

        try:
            for amount_folder in date_folder.iterdir():
                if not amount_folder.is_dir():
                    # Also check for PDFs directly in date folder
                    if amount_folder.is_file() and self._is_pdf_file(amount_folder):
                        # PDF directly in date folder (no amount subfolder)
                        record = self._create_inventory_record(
                            customer_name=customer_name,
                            date_folder_name=date_folder_name,
                            amount_folder_name=None,
                            pdf_path=amount_folder,
                            parsed_date=parsed_date,
                            parsed_amount=None
                        )
                        if record:
                            records.append(record)
                    continue

                amount_folder_name = amount_folder.name
                print(f"INFO [LocalDirectoryScanner]: Scanning amount folder '{amount_folder_name}'")

                # Parse amount from folder name
                parsed_amount = parse_amount_from_filename(amount_folder_name)

                # Locate PDFs in amount folder
                pdf_records = self._locate_pdfs_in_folder(
                    amount_folder, customer_name, date_folder_name, amount_folder_name, parsed_date, parsed_amount
                )
                records.extend(pdf_records)

        except PermissionError as e:
            print(f"ERROR [LocalDirectoryScanner]: Permission denied accessing '{date_folder}': {str(e)}")
        except Exception as e:
            print(f"ERROR [LocalDirectoryScanner]: Error scanning amount folders: {str(e)}")

        return records

    def _locate_pdfs_in_folder(
        self,
        folder: Path,
        customer_name: str,
        date_folder_name: str,
        amount_folder_name: Optional[str],
        parsed_date: Optional[datetime],
        parsed_amount: Optional[float]
    ) -> List[InventoryRecord]:
        """
        Locate all PDF files in a folder and create inventory records.

        Args:
            folder: Folder path to scan for PDFs
            customer_name: Customer name
            date_folder_name: Date folder name
            amount_folder_name: Amount folder name (optional)
            parsed_date: Parsed date from folder name
            parsed_amount: Parsed amount from folder name

        Returns:
            List of InventoryRecord objects
        """
        records = []

        try:
            for file_path in folder.iterdir():
                if file_path.is_file() and self._is_pdf_file(file_path):
                    record = self._create_inventory_record(
                        customer_name=customer_name,
                        date_folder_name=date_folder_name,
                        amount_folder_name=amount_folder_name,
                        pdf_path=file_path,
                        parsed_date=parsed_date,
                        parsed_amount=parsed_amount
                    )
                    if record:
                        records.append(record)
                        print(f"INFO [LocalDirectoryScanner]: Found PDF '{file_path.name}'")

        except PermissionError as e:
            print(f"ERROR [LocalDirectoryScanner]: Permission denied accessing '{folder}': {str(e)}")
        except Exception as e:
            print(f"ERROR [LocalDirectoryScanner]: Error locating PDFs: {str(e)}")

        return records

    def _is_pdf_file(self, file_path: Path) -> bool:
        """
        Check if file is a PDF based on file extension.

        Args:
            file_path: File path to check

        Returns:
            True if file is a PDF, False otherwise
        """
        return file_path.suffix in self.pdf_extensions

    def _create_inventory_record(
        self,
        customer_name: str,
        date_folder_name: str,
        amount_folder_name: Optional[str],
        pdf_path: Path,
        parsed_date: Optional[datetime],
        parsed_amount: Optional[float]
    ) -> Optional[InventoryRecord]:
        """
        Create an inventory record from extracted metadata.

        Args:
            customer_name: Customer name from folder
            date_folder_name: Date folder name
            amount_folder_name: Amount folder name (optional)
            pdf_path: Path to PDF file
            parsed_date: Parsed date
            parsed_amount: Parsed amount

        Returns:
            InventoryRecord object or None if creation fails
        """
        try:
            record = InventoryRecord(
                customer_name=customer_name,
                date_folder=date_folder_name,
                amount_folder=amount_folder_name or "N/A",
                pdf_file_path=str(pdf_path.absolute()),
                pdf_file_name=pdf_path.name,
                declaration_number=None,  # Will be extracted later
                extraction_status="pending",
                extraction_error=None,
                parsed_date=parsed_date,
                parsed_amount=parsed_amount
            )
            return record

        except Exception as e:
            print(f"ERROR [LocalDirectoryScanner]: Failed to create inventory record: {str(e)}")
            return None
