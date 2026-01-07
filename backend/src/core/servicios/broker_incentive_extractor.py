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
from typing import Optional, List
from datetime import datetime

import fitz  # PyMuPDF

from src.interface.broker_incentive_dtos import (
    BrokerIncentiveData,
    ContractType,
    ContractStatus,
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
        # Match "bono equivalente al X% ... del monto cobrado ... Bono de Apertura" (JOSE MARTIN GASPAR format)
        r'bono\s+equivalente\s+al?\s*([\d.,]+)\s*%?\s*\([^)]+\)\s*del\s+monto\s+cobrado[^.]*bono\s+de\s+apertura',
        # Match (a) style with percentage followed by "Bono de Apertura" anywhere
        r'\(a\)[^.]*bono\s+equivalente\s+al?\s*([\d.,]+)\s*%[^.]*(?:apertura|bono\s+fijo)',
        # Generic pattern: percentage before "Bono de Apertura" within sentence
        r'([\d.,]+)\s*%\s*\([^)]+\)[^.]*bono\s+de\s+apertura',
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
        # Match "bono equivalente al X% ... sobre el monto ... Operación Elegible" (JOSE MARTIN GASPAR format)
        r'bono\s+equivalente\s+al?\s*([\d.,]+)\s*%?\s*\([^)]+\)\s*sobre\s+el\s+monto[^.]*operaci[oó]n\s+elegible',
        # Match (b) style with percentage followed by "Operación Elegible" or "Bono Variable"
        r'\(b\)[^.]*bono\s+equivalente\s+al?\s*([\d.,]+)\s*%[^.]*(?:operaci[oó]n\s+elegible|bono\s+variable)',
        # Generic pattern: percentage before "Operación Elegible" within sentence
        r'([\d.,]+)\s*%\s*\([^)]+\)[^.]*operaci[oó]n\s+elegible',
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

    # COLABORACIÓN Contract Type Detection Patterns
    # Looking for "CONTRATO DE COLABORACIÓN" with "ARTÍCULO III INCENTIVOS"
    CONTRACT_TYPE_COLABORACION_INDICATORS = [
        r'CONTRATO\s+DE\s+COLABORACI[ÓO]N',
        r'ART[IÍ]CULO\s+III[.\s]*INCENTIVOS',
        r'Secci[oó]n\s+3\.01[^.]*Descripci[oó]n',
    ]

    # COLABORACIÓN Contract - Operations Incentive Patterns
    # Looking for patterns like:
    # "Finkargo reconocerá un incentivo equivalente al cero punto cero siete por ciento (0.07%)"
    COLABORACION_OPERATIONS_PATTERNS = [
        # Match "Finkargo reconocerá un incentivo equivalente al ... (X%)" for operations
        r'Finkargo\s+reconocer[áa]\s+un\s+incentivo\s+equivalente\s+al[^(]*\(([\d.,]+)\s*%\)[^.]*[Oo]peraci[oó]n',
        # Match "incentivo equivalente al ... (X%) sobre el monto de cada Operación Elegible"
        r'incentivo\s+equivalente\s+al[^(]*\(([\d.,]+)\s*%\)[^.]*sobre\s+el\s+monto[^.]*[Oo]peraci[oó]n',
        # Match Sección 3.01 with percentage in parentheses followed by Operación
        r'Secci[oó]n\s+3\.01[^(]*\(([\d.,]+)\s*%\)[^.]*[Oo]peraci[oó]n',
        # Generic pattern: percentage in parentheses before "Operación Elegible" in ARTÍCULO III context
        r'ART[IÍ]CULO\s+III[^(]*\(([\d.,]+)\s*%\)[^.]*[Oo]peraci[oó]n\s+[Ee]legible',
        # Fallback: any "incentivo ... (X%)" pattern near "Operación"
        r'incentivo[^(]{0,100}\(([\d.,]+)\s*%\)[^.]{0,50}[Oo]peraci[oó]n',
    ]

    # COLABORACIÓN Contract - Credit Line Patterns (may not exist in this contract type)
    # Looking for any apertura/línea de crédito references
    COLABORACION_CREDIT_LINE_PATTERNS = [
        # Match credit line incentive in COLABORACIÓN style if present
        r'incentivo\s+equivalente\s+al[^(]*\(([\d.,]+)\s*%\)[^.]*(?:l[ií]nea\s+de\s+cr[eé]dito|apertura)',
        r'l[ií]nea\s+de\s+cr[eé]dito[^(]*\(([\d.,]+)\s*%\)',
    ]

    # COLABORACIÓN Contract - RFC Patterns for FREELANCE/Broker column
    # In COLABORACIÓN contracts, the signature block has two columns:
    # - Left: FINKARGO (Alma Angélica Guzmán Martínez, RFC No. GUMA790902MR2)
    # - Right: FREELANCE (Broker name, RFC without "No.")
    # We need to extract the RFC from the FREELANCE column, NOT Finkargo's
    # Key distinction: Finkargo uses "RFC No." while FREELANCE uses just "RFC "
    COLABORACION_RFC_PATTERNS = [
        # Pattern: RFC (without "No.") followed by RFC value and "Por su propio derecho"
        # This is the key differentiator - FREELANCE section has "Por su propio derecho"
        r'RFC\s+([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})\s*\n*Por\s+su\s+propio\s+derecho',
        # Pattern: RFC without "No." pattern (Finkargo uses "RFC No.")
        r'RFC\s+(?!No\.)([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})',
    ]

    # COLABORACIÓN Contract - Signatory Name Patterns for FREELANCE/Broker column
    # Extract the broker's name from the FREELANCE column
    # The name appears right before "RFC " (without "No.") followed by "Por su propio derecho"
    COLABORACION_SIGNATORY_PATTERNS = [
        # Pattern: Capture name that appears before "RFC XXXX" + "Por su propio derecho"
        # Flexible whitespace handling for two-column PDF text extraction
        r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})\s+RFC\s+(?!No\.)[A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3}\s+Por\s+su\s+propio\s+derecho',
        # Alternative with line breaks
        r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4})\s*[\n\r]+\s*RFC\s+(?!No\.)[A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3}\s*[\n\r]+\s*Por\s+su\s+propio\s+derecho',
    ]

    # Known Finkargo RFC to exclude (used as fallback validation)
    FINKARGO_RFC = "GUMA790902MR2"
    FINKARGO_NAME = "Alma Angélica Guzmán Martínez"

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
            is_colaboracion = False

            if contract_type == ContractType.BONO:
                credit_line_pct = self.extract_credit_line_incentive(text)
                operations_pct = self.extract_operations_incentive(text)
            elif contract_type == ContractType.INCENTIVOS:
                # For incentivos contracts, the main percentage applies to both
                incentivo_pct = self._extract_incentivos_percentage(text)
                if incentivo_pct is not None:
                    credit_line_pct = incentivo_pct
                    operations_pct = incentivo_pct
            elif contract_type == ContractType.COLABORACION:
                # COLABORACIÓN contracts use ARTÍCULO III INCENTIVOS format
                is_colaboracion = True
                operations_pct = self._extract_colaboracion_operations_incentive(text)
                credit_line_pct = self._extract_colaboracion_credit_line_incentive(text)
            else:
                # Try all extraction methods as fallback
                credit_line_pct = self.extract_credit_line_incentive(text)
                operations_pct = self.extract_operations_incentive(text)

                # If no incentives found, try COLABORACIÓN patterns as last resort
                if credit_line_pct is None and operations_pct is None:
                    colab_ops = self._extract_colaboracion_operations_incentive(text)
                    colab_credit = self._extract_colaboracion_credit_line_incentive(text)
                    if colab_ops is not None or colab_credit is not None:
                        operations_pct = colab_ops
                        credit_line_pct = colab_credit
                        contract_type = ContractType.COLABORACION
                        is_colaboracion = True
                        # Remove the "Could not determine contract type" warning
                        warnings = [w for w in warnings if w != "Could not determine contract type"]
                        fields_found += 1  # Contract type now found

            if credit_line_pct is not None:
                fields_found += 1
            elif not is_colaboracion:
                # Only warn about missing credit line for non-COLABORACIÓN contracts
                warnings.append("Credit line incentive not found")

            if operations_pct is not None:
                fields_found += 1
            else:
                warnings.append("Operations incentive not found")

            # Extract signatory info (pass contract type for COLABORACIÓN-specific handling)
            signatory_info = self.extract_signatory_info(text, contract_type)

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

            # Determine contract status based on extraction confidence
            contract_status = ContractStatus.FOUND if confidence > 0 else ContractStatus.ERROR

            logger.info(
                f"Extraction complete for {broker_name}: "
                f"type={contract_type.value}, "
                f"credit_line={credit_line_pct}%, "
                f"operations={operations_pct}%, "
                f"confidence={confidence:.2f}, "
                f"status={contract_status.value}"
            )

            return BrokerIncentiveData(
                broker_name=broker_name,
                contract_date=contract_date,
                rfc=signatory_info.rfc,
                signatory_name=signatory_info.name,
                credit_line_incentive_pct=credit_line_pct,
                operations_incentive_pct=operations_pct,
                contract_type=contract_type,
                contract_status=contract_status,
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
                contract_status=ContractStatus.ERROR,
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

        # Check for COLABORACIÓN indicators
        colaboracion_score = 0
        for pattern in self.CONTRACT_TYPE_COLABORACION_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                colaboracion_score += 1

        # Determine contract type with precedence: BONO > INCENTIVOS > COLABORACION
        if bono_score > incentivos_score and bono_score > colaboracion_score and bono_score > 0:
            logger.debug(f"Contract type: BONO (score: {bono_score})")
            return ContractType.BONO
        elif incentivos_score > bono_score and incentivos_score > colaboracion_score and incentivos_score > 0:
            logger.debug(f"Contract type: INCENTIVOS (score: {incentivos_score})")
            return ContractType.INCENTIVOS
        elif colaboracion_score > 0:
            logger.debug(f"Contract type: COLABORACION (score: {colaboracion_score})")
            return ContractType.COLABORACION
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

    def _extract_colaboracion_operations_incentive(self, text: str) -> Optional[float]:
        """
        Extract operations incentive percentage from COLABORACIÓN contracts.

        These contracts use ARTÍCULO III INCENTIVOS with Sección 3.01 format,
        where percentages are typically in parentheses e.g., "(0.07%)".

        Args:
            text: Full text content of the contract

        Returns:
            Percentage as float, or None if not found
        """
        for pattern in self.COLABORACION_OPERATIONS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value_str = match.group(1)
                value = self._parse_percentage(value_str)
                if value is not None and 0 < value <= 100:
                    logger.debug(f"Found COLABORACIÓN operations incentive: {value}%")
                    return value

        return None

    def _extract_colaboracion_credit_line_incentive(self, text: str) -> Optional[float]:
        """
        Extract credit line incentive percentage from COLABORACIÓN contracts.

        Note: Many COLABORACIÓN contracts only have operations incentives and
        no credit line (apertura) incentives. This is expected behavior.

        Args:
            text: Full text content of the contract

        Returns:
            Percentage as float, or None if not found
        """
        for pattern in self.COLABORACION_CREDIT_LINE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value_str = match.group(1)
                value = self._parse_percentage(value_str)
                if value is not None and 0 < value <= 100:
                    logger.debug(f"Found COLABORACIÓN credit line incentive: {value}%")
                    return value

        return None

    def extract_signatory_info(
        self, text: str, contract_type: Optional[ContractType] = None
    ) -> SignatoryInfo:
        """
        Extract signatory name and RFC from contract.

        For COLABORACIÓN contracts, uses specialized patterns to extract
        the broker's info from the FREELANCE column (not Finkargo's info).

        Args:
            text: Full text content of the contract
            contract_type: Optional contract type to guide extraction

        Returns:
            SignatoryInfo with extracted name and RFC
        """
        # For COLABORACIÓN contracts, use specialized extraction first
        if contract_type == ContractType.COLABORACION:
            colaboracion_info = self._extract_colaboracion_signatory_info(text)
            if colaboracion_info.rfc or colaboracion_info.name:
                logger.debug(
                    f"Using COLABORACIÓN signatory info: "
                    f"name={colaboracion_info.name}, rfc={colaboracion_info.rfc}"
                )
                return colaboracion_info
            logger.debug("COLABORACIÓN extraction failed, falling back to generic")

        # Generic extraction for non-COLABORACIÓN contracts or fallback
        rfc = None
        name = None

        # Extract RFC
        for pattern in self.RFC_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rfc = match.group(1).upper()
                # For COLABORACIÓN contracts, skip Finkargo's RFC even in fallback
                if contract_type == ContractType.COLABORACION and rfc == self.FINKARGO_RFC:
                    logger.debug(f"Skipping Finkargo RFC in COLABORACIÓN: {rfc}")
                    continue
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
                    # For COLABORACIÓN contracts, skip Finkargo's name even in fallback
                    if contract_type == ContractType.COLABORACION and potential_name == self.FINKARGO_NAME:
                        logger.debug(f"Skipping Finkargo name in COLABORACIÓN: {potential_name}")
                        continue
                    name = potential_name
                    logger.debug(f"Found signatory name: {name}")
                    break

        return SignatoryInfo(name=name, rfc=rfc)

    def _extract_colaboracion_signatory_info(self, text: str) -> SignatoryInfo:
        """
        Extract signatory info specifically for COLABORACIÓN contracts.

        COLABORACIÓN contracts have a two-column signature block:
        - Left (FINKARGO): Alma Angélica Guzmán Martínez, RFC No. GUMA790902MR2
        - Right (FREELANCE): Broker name, RFC without "No."

        Key differentiator: Finkargo uses "RFC No." while FREELANCE uses just "RFC ".
        FREELANCE section also has "Por su propio derecho" below the RFC.

        This method extracts from the FREELANCE column specifically.

        Args:
            text: Full text content of the contract

        Returns:
            SignatoryInfo with broker's name and RFC from FREELANCE column
        """
        rfc = None
        name = None

        # Try COLABORACIÓN-specific RFC patterns first
        for pattern in self.COLABORACION_RFC_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                # Pattern captures only RFC
                potential_rfc = match.group(1).upper()

                # Ensure we didn't accidentally get Finkargo's RFC
                if potential_rfc and potential_rfc != self.FINKARGO_RFC:
                    rfc = potential_rfc
                    logger.debug(f"Found COLABORACIÓN RFC: {rfc}")
                    break

        # Extract name using the two-column layout parsing
        # The FREELANCE name is on the line BEFORE the RFC line, in the right half
        name = self._extract_colaboracion_name_from_columns(text)
        if name:
            logger.debug(f"Found COLABORACIÓN signatory from columns: {name}")

        # If column parsing failed, try signatory patterns as fallback
        if not name:
            for pattern in self.COLABORACION_SIGNATORY_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    potential_name = match.group(1).strip()
                    word_count = len(potential_name.split())
                    if 2 <= word_count <= 5 and len(potential_name) <= 60:
                        # Ensure we didn't get Finkargo's representative
                        if potential_name != self.FINKARGO_NAME:
                            name = potential_name
                            logger.debug(f"Found COLABORACIÓN signatory: {name}")
                            break

        return SignatoryInfo(name=name, rfc=rfc)

    def _extract_colaboracion_name_from_columns(self, text: str) -> Optional[str]:
        """
        Extract FREELANCE name from two-column layout in COLABORACIÓN contracts.

        The signature block has two columns:
        - Line with names: "Finkargo Name                   FREELANCE Name"
        - Line with RFCs: "RFC No. FINKARGO_RFC            RFC FREELANCE_RFC"
        - Line with roles: "Representante Legal            Por su propio derecho"

        This method finds the RFC line with "RFC No." and a second RFC, then
        looks at the line above to extract the FREELANCE name from the right half.

        Args:
            text: Full text content of the contract

        Returns:
            FREELANCE name or None if not found
        """
        lines = text.split('\n')

        # Find the line with both RFCs (RFC No. ... RFC ...)
        rfc_line_idx = None
        for i, line in enumerate(lines):
            # Look for a line with "RFC No." (Finkargo) and another RFC pattern
            if 'RFC No.' in line or 'RFC no.' in line:
                # Check if there's another RFC on the same line
                if re.search(r'RFC\s+[A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3}', line):
                    rfc_line_idx = i
                    break

        if rfc_line_idx is None:
            return None

        # Find the name line (the non-empty line before the RFC line)
        name_line_idx = rfc_line_idx - 1
        while name_line_idx >= 0 and not lines[name_line_idx].strip():
            name_line_idx -= 1

        if name_line_idx < 0:
            return None

        name_line = lines[name_line_idx]

        # Split by multiple spaces (>= 3 spaces indicates column separator)
        parts = re.split(r'\s{3,}', name_line)

        if len(parts) >= 2:
            # The right part is the FREELANCE name
            potential_name = parts[-1].strip()

            # Validate: should look like a name (2-5 words, not too long)
            word_count = len(potential_name.split())
            if 2 <= word_count <= 5 and len(potential_name) <= 60:
                # Ensure it's not Finkargo's name
                if potential_name != self.FINKARGO_NAME:
                    return potential_name

        return None

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

        Finds the contract PDF (using filename pattern matching) and extracts data.
        If no contract PDF is found, returns a record with contract_status=NOT_FOUND.

        Args:
            folder: BrokerFolder object with metadata

        Returns:
            BrokerIncentiveData with extracted fields
        """
        from .broker_contract_scanner import BrokerContractScanner

        scanner = BrokerContractScanner()
        contract_pdf = scanner.find_contract_pdf(folder)

        if not contract_pdf:
            # Determine appropriate warning based on PDF status
            warnings = []
            if not folder.pdf_files:
                warnings.append("No PDF files found in folder")
                logger.warning(f"No PDF files in folder: {folder.folder_name}")
            else:
                warnings.append(f"Folder contains {len(folder.pdf_files)} PDF(s) but no contract file found")
                logger.warning(
                    f"Folder '{folder.folder_name}' has {len(folder.pdf_files)} PDFs "
                    "but none match contract filename patterns"
                )

            return BrokerIncentiveData(
                broker_name=folder.broker_name,
                contract_date=folder.contract_date,
                pdf_path=folder.folder_path,
                contract_status=ContractStatus.NOT_FOUND,
                warnings=warnings,
                extraction_confidence=0.0
            )

        return self.extract_from_pdf(
            pdf_path=contract_pdf,
            broker_name=folder.broker_name,
            contract_date=folder.contract_date
        )
