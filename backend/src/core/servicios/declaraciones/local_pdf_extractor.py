"""
Local PDF Extractor Service

Standalone service for extracting declaration numbers from PDF files stored in the local file system.
Designed to work without external dependencies beyond standard PDF libraries.

Author: Finkargo Engineering
Date: 2025-11-03
Updated: 2025-12-15 - Made standalone without PDFExtractorService dependency
"""

from typing import Dict, Any, Optional
from pathlib import Path
import re

# PDF extraction imports
import pdfplumber
from PyPDF2 import PdfReader


class LocalPDFExtractor:
    """
    Standalone service for extracting declaration numbers from local PDF files.

    Provides local file system support for PDF extraction without external dependencies.
    Uses pdfplumber as primary extractor with PyPDF2 as fallback.
    """

    # Patterns for extracting declaration numbers from Colombian declarations
    DECLARATION_PATTERNS = [
        # Pattern: "No. Declaración: 123456789" or "N° Declaración: 123456789"
        r'(?:No\.?|N[°º])\s*(?:de\s+)?Declaraci[oó]n[:.\s]+(\d{9,15})',
        # Pattern: "Declaración No. 123456789"
        r'Declaraci[oó]n\s+(?:No\.?|N[°º])[:.\s]*(\d{9,15})',
        # Pattern: Just a 9-15 digit number on its own line
        r'^\s*(\d{9,15})\s*$',
        # Pattern: "No.: 123456789"
        r'(?:No\.?|N[°º])[:.\s]+(\d{9,15})',
        # Pattern: Number near "DECLARACION"
        r'DECLARACI[OÓ]N[^0-9]*(\d{9,15})',
    ]

    def __init__(self, supabase_client: Any = None):
        """
        Initialize LocalPDFExtractor.

        Args:
            supabase_client: Unused, kept for interface compatibility
        """
        print("INFO [LocalPDFExtractor]: Service initialized for local file extraction")

    def extract_from_local_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract declaration number from a local PDF file.

        Args:
            file_path (str): Absolute path to local PDF file

        Returns:
            Dict[str, Any]: Extracted declaration data with fields:
                - declaration_number (str): Declaration number if found
                - extraction_status (str): "success", "partial", or "failed"
                - error_message (str): Error message if extraction failed
                - file_path (str): The original file path
        """
        print(f"INFO [LocalPDFExtractor]: Starting extraction from '{file_path}'")

        # Validate file path
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            error_msg = f"File does not exist: {file_path}"
            print(f"ERROR [LocalPDFExtractor]: {error_msg}")
            return {
                'extraction_status': 'failed',
                'error_message': error_msg,
                'file_path': file_path,
                'declaration_number': None
            }

        if not file_path_obj.is_file():
            error_msg = f"Path is not a file: {file_path}"
            print(f"ERROR [LocalPDFExtractor]: {error_msg}")
            return {
                'extraction_status': 'failed',
                'error_message': error_msg,
                'file_path': file_path,
                'declaration_number': None
            }

        # Check file extension
        if file_path_obj.suffix.lower() not in ['.pdf']:
            error_msg = f"File is not a PDF: {file_path}"
            print(f"ERROR [LocalPDFExtractor]: {error_msg}")
            return {
                'extraction_status': 'failed',
                'error_message': error_msg,
                'file_path': file_path,
                'declaration_number': None
            }

        try:
            # Extract text from PDF
            extracted_text, extraction_method = self._extract_text(file_path)

            if not extracted_text:
                return {
                    'file_path': file_path,
                    'extraction_status': 'failed',
                    'error_message': 'No text could be extracted from PDF',
                    'declaration_number': None
                }

            # Extract declaration number
            declaration_number = self._extract_declaration_number(extracted_text)

            result = {
                'file_path': file_path,
                'declaration_number': declaration_number,
                'extraction_status': 'success' if declaration_number else 'partial',
                'error_message': None if declaration_number else 'No declaration number found in PDF'
            }

            if declaration_number:
                print(f"SUCCESS [LocalPDFExtractor]: Extracted declaration number '{declaration_number}' from '{file_path_obj.name}'")
            else:
                print(f"WARN [LocalPDFExtractor]: No declaration number found in '{file_path_obj.name}'")

            return result

        except Exception as e:
            error_msg = f"Extraction error: {str(e)}"
            print(f"ERROR [LocalPDFExtractor]: {error_msg} for file '{file_path}'")

            return {
                'file_path': file_path,
                'extraction_status': 'failed',
                'error_message': error_msg,
                'declaration_number': None
            }

    def _extract_text(self, file_path: str) -> tuple[str, str]:
        """
        Extract text from PDF using pdfplumber with PyPDF2 as fallback.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, extraction_method)
        """
        extracted_text = ""
        extraction_method = "none"

        # Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                if text_parts:
                    extracted_text = "\n".join(text_parts)
                    extraction_method = "pdfplumber"
                    print(f"INFO [LocalPDFExtractor]: Extracted {len(extracted_text)} chars using pdfplumber")
        except Exception as e:
            print(f"WARN [LocalPDFExtractor]: pdfplumber failed: {str(e)}")

        # Fallback to PyPDF2 if pdfplumber didn't work
        if not extracted_text:
            try:
                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                if text_parts:
                    extracted_text = "\n".join(text_parts)
                    extraction_method = "pypdf2"
                    print(f"INFO [LocalPDFExtractor]: Extracted {len(extracted_text)} chars using PyPDF2")
            except Exception as e:
                print(f"WARN [LocalPDFExtractor]: PyPDF2 failed: {str(e)}")

        return extracted_text, extraction_method

    def _extract_declaration_number(self, text: str) -> Optional[str]:
        """
        Extract declaration number from text using regex patterns.

        Args:
            text: Extracted text from PDF

        Returns:
            Declaration number if found, None otherwise
        """
        if not text:
            return None

        # Try each pattern
        for pattern in self.DECLARATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Return the first valid match (9-15 digits)
                for match in matches:
                    if len(match) >= 9 and len(match) <= 15:
                        return match

        return None

    def extract_batch(self, file_paths: list[str]) -> list[Dict[str, Any]]:
        """
        Extract declaration data from multiple local PDF files.

        Args:
            file_paths: List of absolute paths to local PDF files

        Returns:
            List of extraction results
        """
        print(f"INFO [LocalPDFExtractor]: Starting batch extraction for {len(file_paths)} files")

        results = []
        successful = 0
        failed = 0

        for file_path in file_paths:
            try:
                result = self.extract_from_local_file(file_path)
                results.append(result)

                if result['extraction_status'] == 'success':
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                print(f"ERROR [LocalPDFExtractor]: Batch extraction error for '{file_path}': {str(e)}")
                results.append({
                    'file_path': file_path,
                    'extraction_status': 'failed',
                    'error_message': str(e),
                    'declaration_number': None
                })
                failed += 1

        print(f"SUCCESS [LocalPDFExtractor]: Batch extraction completed: {successful} successful, {failed} failed")

        return results
