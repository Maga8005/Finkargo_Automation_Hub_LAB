"""
Broker Incentive Extractor Service

This service extracts incentive percentages and signatory information from
broker contract PDFs using regex patterns.

Supports two contract types:
1. "Bono" contracts - Contains credit line (apertura) and operations bonuses in Anexo A
2. "Incentivos" contracts - Older style with incentives in Artículo 3

Author: Finkargo Automation Hub
Date: 2025-12-16
"""

import re
import logging
from typing import Optional, List, Tuple
from datetime import datetime

import fitz  # PyMuPDF

from src.interface.broker_incentive_dtos import (
    BrokerIncentiveData,
    ContractType,
    SignatoryInfo,
)
from .broker_contract_scanner import BrokerFolder

logger = logging.getLogger(__name__)


class BrokerIncentiveExtractor:
    """
    Service for extracting incentive data from broker contract PDFs.

    Uses regex patterns to identify:
    - Contract type (Bono vs Incentivos)
    - Credit line incentive percentage (bono de apertura)
    - Operations incentive percentage
    - RFC (Mexican tax ID)
    - Signatory name

    Example usage:
        extractor = BrokerIncentiveExtractor()
        result = extractor.extract_from_pdf('/path/to/contract.pdf', 'Broker XYZ', '2024-05-15')
        print(f"Credit Line: {result.credit_line_incentive_pct}%")
    """

    # Total number of extractable fields for confidence calculation
    TOTAL_FIELDS = 5  # contract_type, credit_line, operations, rfc, signatory_name

    # ==================== Regex Patterns ====================

    # Bono Contract - Credit Line (Apertura) Patterns
    # Looking for patterns like:
    # "un bono equivalente al 2.5% del monto colocado...bono de apertura"
    BONO_CREDIT_LINE_PATTERNS = [
        # Match "bono equivalente al X% ... apertura" with flexible spacing
        r'bono\s+equivalente\s+al?\s*([\d.,]+)\s*%?\s*(?:por\s*ciento)?\s*del\s+monto\s+(?:colocado|a\s+cliente)[^.]*bono\s+de\s+apertura',
        # Match "bono de apertura ... equivalente al X%"
        r'bono\s+de\s+apertura[^.]*equivalente\s+al?\s*([\d.,]+)\s*%',
        # Alternative: apertura followed by percentage
        r'(?:comisi[oó]n|bono)\s+(?:de\s+)?apertura[:\s]+(?:de\s+)?(?:un\s+)?([\d.,]+)\s*%',
        # Anexo A patterns - look for apertura percentages
        r'apertura[^%]{0,50}([\d.,]+)\s*%',
    ]

    # Bono Contract - Operations Patterns
    # Looking for patterns like:
    # "un bono equivalente al 1%...operaciones elegibles"
    BONO_OPERATIONS_PATTERNS = [
        # Match "bono equivalente al X% ... operaciones elegibles"
        r'bono\s+equivalente\s+al?\s*([\d.,]+)\s*%?\s*(?:por\s*ciento)?[^.]*operaciones\s+elegibles',
        # Match "operaciones elegibles ... equivalente al X%"
        r'operaciones\s+elegibles[^.]*equivalente\s+al?\s*([\d.,]+)\s*%',
        # Alternative: operaciones or operativa followed by percentage
        r'(?:comisi[oó]n|bono)\s+(?:de\s+)?(?:operaciones?|operativa)[:\s]+(?:de\s+)?(?:un\s+)?([\d.,]+)\s*%',
        # Anexo A patterns - look for operations percentages
        r'(?:operacion(?:es)?|operativa)[^%]{0,50}([\d.,]+)\s*%',
    ]

    # Incentivos Contract Patterns (older style)
    # Looking for patterns like:
    # "Finkargo reconocerá un incentivo de 2.5%"
    INCENTIVOS_PATTERNS = [
        r'(?:Finkargo|finkargo)\s*reconocer[áa]\s*(?:un\s*)?incentivo\s*(?:de\s*)?([\d.,]+)\s*%',
        r'incentivo\s+(?:de\s+)?([\d.,]+)\s*%\s*(?:del|sobre)',
        r'Art[ií]culo\s+3[^.]*incentivo\s+(?:de\s+)?([\d.,]+)\s*%',
    ]

    # RFC Patterns (Mexican Tax ID)
    # RFC format: 3-4 letters + 6 digits + 3 alphanumeric
    RFC_PATTERNS = [
        r'R\.?F\.?C\.?[:\s]*([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})',
        r'RFC[:\s]+([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})',
        r'Registro\s+Federal[^:]*[:\s]*([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})',
        # Look for RFC near "broker" or "aliado"
        r'(?:broker|aliado)[^.]{0,100}RFC[:\s]*([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})',
    ]

    # Signatory Name Patterns
    # Looking for patterns near signature lines
    SIGNATORY_PATTERNS = [
        # "Por El Broker:" or "Por el Aliado:" followed by name
        r'(?:Por\s+)?(?:El|La)\s+(?:Broker|Aliado)[:\s]*\n*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})',
        # "Representante Legal:" followed by name
        r'Representante\s+Legal[:\s]*\n*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})',
        # Name followed by RFC on same or next line
        r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})\s*\n*R\.?F\.?C\.?',
    ]

    # Contract Type Detection Patterns
    CONTRACT_TYPE_BONO_INDICATORS = [
        r'bono\s+(?:de\s+)?apertura',
        r'bono\s+equivalente',
        r'operaciones\s+elegibles',
        r'Anexo\s+A',
    ]

    CONTRACT_TYPE_INCENTIVOS_INDICATORS = [
        r'Art[ií]culo\s+3.*incentivo',
        r'Finkargo\s+reconocer[áa]\s+.*incentivo',
        r'CONTRATO\s+DE\s+INCENTIVOS',
    ]

    def __init__(self):
        """Initialize the broker incentive extractor."""
        logger.info("BrokerIncentiveExtractor initialized")

    def extract_from_pdf(
        self,
        pdf_path: str,
        broker_name: str,
        contract_date: Optional[str] = None
    ) -> BrokerIncentiveData:
        """
        Extract incentive data from a broker contract PDF.

        Args:
            pdf_path: Path to the PDF file
            broker_name: Broker name (from folder)
            contract_date: Contract date (from folder)

        Returns:
            BrokerIncentiveData with extracted fields
        """
        logger.info(f"Extracting incentives from: {pdf_path}")

        warnings: List[str] = []
        fields_found = 0

        try:
            # Extract text from PDF
            text = self._extract_pdf_text(pdf_path)

            if not text or len(text.strip()) < 100:
                logger.warning(f"PDF has little extractable text: {pdf_path}")
                warnings.append("PDF appears to be scanned or has little extractable text")
                return BrokerIncentiveData(
                    broker_name=broker_name,
                    contract_date=contract_date,
                    pdf_path=pdf_path,
                    warnings=warnings,
                    extraction_confidence=0.0
                )

            # Identify contract type
            contract_type = self.identify_contract_type(text)
            if contract_type != ContractType.UNKNOWN:
                fields_found += 1
            else:
                warnings.append("Could not determine contract type")

            # Extract incentive percentages
            credit_line_pct = None
            operations_pct = None

            if contract_type == ContractType.BONO:
                credit_line_pct = self.extract_credit_line_incentive(text)
                operations_pct = self.extract_operations_incentive(text)
            elif contract_type == ContractType.INCENTIVOS:
                # For incentivos contracts, the main percentage applies to both
                incentivo_pct = self._extract_incentivos_percentage(text)
                if incentivo_pct is not None:
                    credit_line_pct = incentivo_pct
                    operations_pct = incentivo_pct
            else:
                # Try both extraction methods
                credit_line_pct = self.extract_credit_line_incentive(text)
                operations_pct = self.extract_operations_incentive(text)

            if credit_line_pct is not None:
                fields_found += 1
            else:
                warnings.append("Credit line incentive not found")

            if operations_pct is not None:
                fields_found += 1
            else:
                warnings.append("Operations incentive not found")

            # Extract signatory info
            signatory_info = self.extract_signatory_info(text)

            if signatory_info.rfc:
                fields_found += 1
            else:
                warnings.append("RFC not found in document")

            if signatory_info.name:
                fields_found += 1
            else:
                warnings.append("Signatory name not found")

            # Calculate confidence
            confidence = fields_found / self.TOTAL_FIELDS

            logger.info(
                f"Extraction complete for {broker_name}: "
                f"type={contract_type.value}, "
                f"credit_line={credit_line_pct}%, "
                f"operations={operations_pct}%, "
                f"confidence={confidence:.2f}"
            )

            return BrokerIncentiveData(
                broker_name=broker_name,
                contract_date=contract_date,
                rfc=signatory_info.rfc,
                signatory_name=signatory_info.name,
                credit_line_incentive_pct=credit_line_pct,
                operations_incentive_pct=operations_pct,
                contract_type=contract_type,
                pdf_path=pdf_path,
                extraction_date=datetime.now().isoformat(),
                warnings=warnings,
                extraction_confidence=confidence
            )

        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {e}")
            warnings.append(f"Extraction error: {str(e)}")
            return BrokerIncentiveData(
                broker_name=broker_name,
                contract_date=contract_date,
                pdf_path=pdf_path,
                warnings=warnings,
                extraction_confidence=0.0
            )

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        try:
            pdf_document = fitz.open(pdf_path)
            text_parts = []

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)

            pdf_document.close()

            full_text = '\n'.join(text_parts)
            logger.debug(f"Extracted {len(full_text)} characters from PDF")

            return full_text

        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise

    def identify_contract_type(self, text: str) -> ContractType:
        """
        Identify the type of broker contract.

        Args:
            text: Full text content of the contract

        Returns:
            ContractType enum value
        """
        text_lower = text.lower()

        # Check for Bono indicators
        bono_score = 0
        for pattern in self.CONTRACT_TYPE_BONO_INDICATORS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                bono_score += 1

        # Check for Incentivos indicators
        incentivos_score = 0
        for pattern in self.CONTRACT_TYPE_INCENTIVOS_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                incentivos_score += 1

        if bono_score > incentivos_score and bono_score > 0:
            logger.debug(f"Contract type: BONO (score: {bono_score})")
            return ContractType.BONO
        elif incentivos_score > bono_score and incentivos_score > 0:
            logger.debug(f"Contract type: INCENTIVOS (score: {incentivos_score})")
            return ContractType.INCENTIVOS
        else:
            logger.debug("Contract type: UNKNOWN")
            return ContractType.UNKNOWN

    def extract_credit_line_incentive(self, text: str) -> Optional[float]:
        """
        Extract credit line (apertura) incentive percentage.

        Args:
            text: Full text content of the contract

        Returns:
            Percentage as float, or None if not found
        """
        for pattern in self.BONO_CREDIT_LINE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value_str = match.group(1)
                value = self._parse_percentage(value_str)
                if value is not None and 0 < value <= 100:
                    logger.debug(f"Found credit line incentive: {value}%")
                    return value

        return None

    def extract_operations_incentive(self, text: str) -> Optional[float]:
        """
        Extract operations incentive percentage.

        Args:
            text: Full text content of the contract

        Returns:
            Percentage as float, or None if not found
        """
        for pattern in self.BONO_OPERATIONS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value_str = match.group(1)
                value = self._parse_percentage(value_str)
                if value is not None and 0 < value <= 100:
                    logger.debug(f"Found operations incentive: {value}%")
                    return value

        return None

    def _extract_incentivos_percentage(self, text: str) -> Optional[float]:
        """
        Extract incentive percentage from Incentivos-style contracts.

        Args:
            text: Full text content of the contract

        Returns:
            Percentage as float, or None if not found
        """
        for pattern in self.INCENTIVOS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value_str = match.group(1)
                value = self._parse_percentage(value_str)
                if value is not None and 0 < value <= 100:
                    logger.debug(f"Found incentivos percentage: {value}%")
                    return value

        return None

    def extract_signatory_info(self, text: str) -> SignatoryInfo:
        """
        Extract signatory name and RFC from contract.

        Args:
            text: Full text content of the contract

        Returns:
            SignatoryInfo with extracted name and RFC
        """
        rfc = None
        name = None

        # Extract RFC
        for pattern in self.RFC_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rfc = match.group(1).upper()
                logger.debug(f"Found RFC: {rfc}")
                break

        # Extract signatory name
        for pattern in self.SIGNATORY_PATTERNS:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                potential_name = match.group(1).strip()
                # Basic validation: should be 2-5 words, not too long
                word_count = len(potential_name.split())
                if 2 <= word_count <= 5 and len(potential_name) <= 60:
                    name = potential_name
                    logger.debug(f"Found signatory name: {name}")
                    break

        return SignatoryInfo(name=name, rfc=rfc)

    def _parse_percentage(self, value: str) -> Optional[float]:
        """
        Parse a percentage value, handling both comma and period decimals.

        Args:
            value: String representation of percentage

        Returns:
            Float value or None if parsing fails
        """
        if value is None:
            return None
        try:
            # Replace comma with period for decimal
            normalized = value.replace(',', '.')
            # Remove any spaces
            normalized = normalized.strip()
            return float(normalized)
        except ValueError:
            return None

    def extract_from_folder(self, folder: BrokerFolder) -> BrokerIncentiveData:
        """
        Extract incentive data from a broker folder.

        Finds the contract PDF and extracts data.

        Args:
            folder: BrokerFolder object with metadata

        Returns:
            BrokerIncentiveData with extracted fields
        """
        from .broker_contract_scanner import BrokerContractScanner

        scanner = BrokerContractScanner()
        contract_pdf = scanner.find_contract_pdf(folder)

        if not contract_pdf:
            logger.warning(f"No contract PDF found in folder: {folder.folder_name}")
            return BrokerIncentiveData(
                broker_name=folder.broker_name,
                contract_date=folder.contract_date,
                pdf_path=folder.folder_path,
                warnings=["No contract PDF found in folder"],
                extraction_confidence=0.0
            )

        return self.extract_from_pdf(
            pdf_path=contract_pdf,
            broker_name=folder.broker_name,
            contract_date=folder.contract_date
        )
