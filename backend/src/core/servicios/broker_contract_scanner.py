"""
Broker Contract Scanner Service

This service scans a local directory structure containing broker contract folders,
identifying folders that follow the naming convention `YYYYMMDD Broker Name`.

Expected folder structure: ROOT/{YYYYMMDD Broker Name}/contract.pdf
Example: Brokers/20240515 Broker XYZ/contrato.pdf

Author: Finkargo Automation Hub
Date: 2025-12-16
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BrokerFolder:
    """
    Represents a broker folder with extracted metadata.

    Attributes:
        folder_path: Absolute path to the broker folder
        folder_name: Name of the folder
        broker_name: Extracted broker name from folder
        contract_date: Extracted date from folder name
        pdf_files: List of PDF files found in the folder
    """
    folder_path: str
    folder_name: str
    broker_name: str
    contract_date: Optional[str]
    pdf_files: List[str]


class BrokerContractScanner:
    """
    Service for scanning directory structures containing broker contract folders.

    This service:
    1. Scans directories for folders matching `YYYYMMDD Broker Name` pattern
    2. Extracts broker name and date from folder names
    3. Locates PDF contract files within each folder
    4. Returns a list of BrokerFolder objects with metadata

    Example usage:
        scanner = BrokerContractScanner()
        folders = scanner.scan_directory('/path/to/brokers', include_subfolders=True)
        for folder in folders:
            print(f"Broker: {folder.broker_name}, Date: {folder.contract_date}")
    """

    # Regex pattern for folder names: YYYYMMDD followed by space and broker name
    FOLDER_DATE_PATTERN = re.compile(r'^(\d{8})\s+(.+)$')

    # Alternative patterns for flexibility
    FOLDER_DATE_PATTERN_ALT = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(.+)$')

    # PDF file extensions to look for
    PDF_EXTENSIONS = ['.pdf', '.PDF']

    # Max file size for PDFs (50MB)
    MAX_PDF_SIZE_BYTES = 50 * 1024 * 1024

    def __init__(self):
        """Initialize the broker contract scanner."""
        logger.info("BrokerContractScanner initialized")

    def scan_directory(
        self,
        root_path: str,
        include_subfolders: bool = True
    ) -> List[BrokerFolder]:
        """
        Scan directory structure for broker folders.

        Args:
            root_path: Root directory path to scan
            include_subfolders: Whether to scan subdirectories

        Returns:
            List of BrokerFolder objects with metadata

        Raises:
            ValueError: If root_path does not exist or is not accessible
        """
        # Validate and sanitize path
        root_path = self._sanitize_path(root_path)
        root_path_obj = Path(root_path)

        if not root_path_obj.exists():
            error_msg = f"Root path does not exist: {root_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not root_path_obj.is_dir():
            error_msg = f"Root path is not a directory: {root_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Starting directory scan at '{root_path}'")
        logger.info(f"Include subfolders: {include_subfolders}")

        broker_folders = []

        try:
            # Scan for broker folders
            broker_folders = self._scan_broker_folders(root_path_obj, include_subfolders)

            logger.info(f"Scan completed: Found {len(broker_folders)} broker folders")

        except PermissionError as e:
            logger.error(f"Permission denied accessing directory: {e}")
            raise ValueError(f"Permission denied: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            raise

        return broker_folders

    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize directory path to prevent path traversal attacks.

        Args:
            path: Input path string

        Returns:
            Sanitized path string

        Raises:
            ValueError: If path contains suspicious patterns
        """
        # Reject paths with .. to prevent traversal
        if '..' in path:
            raise ValueError("Path traversal detected: '..' not allowed in path")

        # Normalize the path
        normalized = os.path.normpath(path)

        return normalized

    def _scan_broker_folders(
        self,
        root_path: Path,
        include_subfolders: bool
    ) -> List[BrokerFolder]:
        """
        Scan for broker folders within the root directory.

        Args:
            root_path: Root directory path object
            include_subfolders: Whether to scan subdirectories

        Returns:
            List of BrokerFolder objects
        """
        broker_folders = []

        try:
            for entry in root_path.iterdir():
                if not entry.is_dir():
                    continue

                # Try to parse folder name for broker info
                broker_name, contract_date = self.parse_folder_name(entry.name)

                if broker_name:
                    # This folder matches our pattern
                    pdf_files = self._find_pdf_files(entry)

                    if pdf_files:  # Only include folders with PDFs
                        folder = BrokerFolder(
                            folder_path=str(entry.absolute()),
                            folder_name=entry.name,
                            broker_name=broker_name,
                            contract_date=contract_date,
                            pdf_files=pdf_files
                        )
                        broker_folders.append(folder)
                        logger.info(f"Found broker folder: {entry.name} ({len(pdf_files)} PDFs)")
                    else:
                        logger.warning(f"Folder '{entry.name}' has no PDF files, skipping")
                elif include_subfolders:
                    # Check if this folder contains broker subfolders
                    nested_folders = self._scan_broker_folders(entry, include_subfolders)
                    broker_folders.extend(nested_folders)

        except PermissionError as e:
            logger.warning(f"Permission denied accessing '{root_path}': {e}")
        except Exception as e:
            logger.error(f"Error scanning folder '{root_path}': {e}")

        return broker_folders

    def parse_folder_name(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract broker name and date from folder name.

        Expected format: YYYYMMDD Broker Name
        Alternative format: YYYY-MM-DD Broker Name

        Args:
            name: Folder name string

        Returns:
            Tuple of (broker_name, contract_date) or (None, None) if not matching
        """
        # Try primary pattern: YYYYMMDD Broker Name
        match = self.FOLDER_DATE_PATTERN.match(name)
        if match:
            date_str = match.group(1)
            broker_name = match.group(2).strip()

            # Validate and format date
            try:
                parsed_date = datetime.strptime(date_str, '%Y%m%d')
                contract_date = parsed_date.strftime('%Y-%m-%d')
                return broker_name, contract_date
            except ValueError:
                logger.warning(f"Invalid date in folder name: {date_str}")
                return broker_name, None

        # Try alternative pattern: YYYY-MM-DD Broker Name
        match = self.FOLDER_DATE_PATTERN_ALT.match(name)
        if match:
            date_str = match.group(1)
            broker_name = match.group(2).strip()

            # Validate date
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return broker_name, date_str
            except ValueError:
                logger.warning(f"Invalid date in folder name: {date_str}")
                return broker_name, None

        # No match - this folder doesn't follow our naming convention
        logger.debug(f"Folder '{name}' does not match expected pattern")
        return None, None

    def _find_pdf_files(self, folder: Path) -> List[str]:
        """
        Find all PDF files within a folder.

        Args:
            folder: Path object for folder to search

        Returns:
            List of absolute paths to PDF files
        """
        pdf_files = []

        try:
            for entry in folder.iterdir():
                if entry.is_file() and entry.suffix in self.PDF_EXTENSIONS:
                    # Check file size
                    file_size = entry.stat().st_size
                    if file_size > self.MAX_PDF_SIZE_BYTES:
                        logger.warning(
                            f"PDF file too large ({file_size / (1024*1024):.2f}MB), "
                            f"skipping: {entry.name}"
                        )
                        continue

                    pdf_files.append(str(entry.absolute()))
                    logger.debug(f"Found PDF: {entry.name}")

        except PermissionError as e:
            logger.warning(f"Permission denied accessing '{folder}': {e}")
        except Exception as e:
            logger.error(f"Error finding PDF files in '{folder}': {e}")

        return pdf_files

    def find_contract_pdf(self, folder: BrokerFolder) -> Optional[str]:
        """
        Find the main contract PDF in a broker folder.

        Looks for PDFs with common contract naming patterns.
        If multiple PDFs exist, returns the first one that looks like a contract.

        Args:
            folder: BrokerFolder object

        Returns:
            Path to contract PDF or None if not found
        """
        if not folder.pdf_files:
            return None

        # Common patterns for contract filenames
        contract_patterns = [
            r'contrato',
            r'contract',
            r'convenio',
            r'acuerdo',
            r'bono',
            r'incentivo',
        ]

        # First, look for files matching contract patterns
        for pdf_path in folder.pdf_files:
            filename_lower = Path(pdf_path).stem.lower()
            for pattern in contract_patterns:
                if pattern in filename_lower:
                    logger.debug(f"Found contract PDF by pattern '{pattern}': {pdf_path}")
                    return pdf_path

        # If no matching pattern, return the first PDF
        logger.debug(f"No contract pattern match, using first PDF: {folder.pdf_files[0]}")
        return folder.pdf_files[0]
