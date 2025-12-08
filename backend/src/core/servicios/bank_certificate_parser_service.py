"""
Bank Certificate Parser Service - Extracts data from Bank Certificate PDF documents

This service parses bank certificates from Colombian banks (primarily Bancolombia and BBVA)
to extract creditor bank account information for Instruccion de Mandato documents.
"""
import fitz  # PyMuPDF
from fitz import EmptyFileError, FileDataError
import logging
import re
from typing import Optional

from src.interface.legal_dtos import BankCertificateData

logger = logging.getLogger(__name__)


class BankCertificateParserService:
    """Service for parsing Bank Certificate PDF documents"""

    def __init__(self):
        """Initialize Bank Certificate parser service"""
        pass

    def parse_bank_certificate(self, pdf_bytes: bytes) -> BankCertificateData:
        """
        Parse Bank Certificate PDF and extract creditor bank account information

        Args:
            pdf_bytes: Bank Certificate PDF file content as bytes

        Returns:
            BankCertificateData: Extracted bank certificate information

        Raises:
            ValueError: If PDF is invalid or critical fields cannot be extracted
        """
        try:
            # Open PDF document
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            if len(doc) < 1:
                raise ValueError("Invalid Bank Certificate: PDF has no pages")

            logger.info(f"Parsing Bank Certificate with {len(doc)} pages")

            # Extract text from all pages
            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                full_text += page.get_text() + "\n"

            # Close document
            doc.close()

            # Auto-detect bank
            banco = self._extract_banco(full_text)
            logger.debug(f"Detected bank: {banco}")

            # Extract all fields
            razon_social = self._extract_razon_social(full_text)
            nit = self._extract_nit(full_text)
            tipo_cuenta = self._extract_tipo_cuenta(full_text)
            numero_cuenta = self._extract_numero_cuenta(full_text)

            # Optional fields
            numero_certificado = self._extract_numero_certificado(full_text)
            fecha_emision = self._extract_fecha_emision(full_text)

            # Validate critical fields
            if not razon_social:
                raise ValueError("Could not extract razon_social (company name) from certificate")

            if not nit:
                raise ValueError("Could not extract NIT (tax ID) from certificate")

            if not tipo_cuenta:
                raise ValueError("Could not extract tipo_cuenta (account type) from certificate")

            if not numero_cuenta:
                raise ValueError("Could not extract numero_cuenta (account number) from certificate")

            if not banco:
                logger.warning("Could not auto-detect bank name - using 'DESCONOCIDO'")
                banco = "DESCONOCIDO"

            logger.info("Bank Certificate parsing completed successfully")
            logger.debug(f"Extracted razon_social: {razon_social}")
            logger.debug(f"Extracted NIT: {nit}")
            logger.debug(f"Extracted banco: {banco}")
            logger.debug(f"Extracted tipo_cuenta: {tipo_cuenta}")
            logger.debug(f"Extracted numero_cuenta: {numero_cuenta}")

            # Create and return BankCertificateData model
            certificate_data = BankCertificateData(
                numero_certificado=numero_certificado,
                banco=banco,
                fecha_emision=fecha_emision,
                razon_social=razon_social,
                nit=nit,
                tipo_cuenta=tipo_cuenta,
                numero_cuenta=numero_cuenta
            )

            return certificate_data

        except EmptyFileError as e:
            logger.error(f"Empty PDF file: {str(e)}")
            raise ValueError("Invalid PDF: Cannot open empty file")
        except FileDataError as e:
            logger.error(f"Invalid PDF format: {str(e)}")
            raise ValueError(f"Invalid PDF file format: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing Bank Certificate: {str(e)}")
            raise

    def _extract_razon_social(self, text: str) -> Optional[str]:
        """
        Extract company name (razon social) from certificate text

        Typical patterns:
        - "informar que [COMPANY NAME] identificado(a) con NIT"
        - "certifica que [COMPANY NAME] identificado con"
        """
        patterns = [
            r'informar\s+que\s+([^\n]+?)\s+identificado',
            r'certifica\s+que\s+([^\n]+?)\s+identificado',
            r'informar\s+que\s+([^\n]+?)\s+con\s+NIT',
            r'titular:\s*([^\n]+)',
            r'nombre:\s*([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                razon_social = match.group(1).strip()
                # Clean up common artifacts
                razon_social = re.sub(r'\s+', ' ', razon_social)  # Normalize whitespace
                razon_social = razon_social.split('identificado')[0].strip()  # Remove trailing text
                if len(razon_social) > 3:  # Sanity check
                    logger.debug(f"Matched razon_social with pattern: {pattern}")
                    return razon_social

        logger.warning("Could not extract razon_social from certificate")
        return None

    def _extract_nit(self, text: str) -> Optional[str]:
        """
        Extract NIT (Colombian tax ID) from certificate text

        Typical patterns:
        - "NIT 900436389"
        - "NIT: 900.436.389-1"
        - "con NIT 900436389"
        """
        patterns = [
            r'NIT\s*:?\s*(\d[\d\.\-]+)',
            r'con\s+NIT\s+(\d[\d\.\-]+)',
            r'identificado.*?NIT\s*:?\s*(\d[\d\.\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nit = match.group(1).strip()
                # Clean NIT - remove dots and dashes for consistency (keep only digits)
                nit_clean = re.sub(r'[^\d]', '', nit)
                if len(nit_clean) >= 7:  # Colombian NITs are typically 9-10 digits
                    logger.debug(f"Matched NIT with pattern: {pattern}")
                    return nit_clean

        logger.warning("Could not extract NIT from certificate")
        return None

    def _extract_banco(self, text: str) -> Optional[str]:
        """
        Extract bank name from certificate header/logo area

        Auto-detects bank based on keywords in the document
        """
        text_upper = text.upper()

        # Check for major Colombian banks
        if 'BANCOLOMBIA' in text_upper:
            return 'BANCOLOMBIA'
        elif 'BBVA' in text_upper:
            return 'BBVA'
        elif 'DAVIVIENDA' in text_upper:
            return 'DAVIVIENDA'
        elif 'BANCO DE BOGOTA' in text_upper or 'BANCO DE BOGOTÁ' in text_upper:
            return 'BANCO DE BOGOTA'
        elif 'BANCO POPULAR' in text_upper:
            return 'BANCO POPULAR'
        elif 'SCOTIABANK' in text_upper:
            return 'SCOTIABANK'
        elif 'ITAU' in text_upper or 'ITAÚ' in text_upper:
            return 'ITAU'
        elif 'AV VILLAS' in text_upper:
            return 'AV VILLAS'
        elif 'BANCO CAJA SOCIAL' in text_upper:
            return 'BANCO CAJA SOCIAL'

        logger.warning("Could not detect bank name from certificate")
        return None

    def _extract_tipo_cuenta(self, text: str) -> Optional[str]:
        """
        Extract account type from certificate

        Typical types:
        - "CUENTA DE AHORROS"
        - "CUENTA CORRIENTE"
        - "Ahorros"
        - "Corriente"
        """
        patterns = [
            r'(CUENTA\s+DE\s+AHORROS)',
            r'(CUENTA\s+CORRIENTE)',
            r'Tipo:\s*(Ahorros|Corriente)',
            r'Producto:\s*(CUENTA\s+DE\s+AHORROS|CUENTA\s+CORRIENTE)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tipo = match.group(1).strip().upper()
                logger.debug(f"Matched tipo_cuenta with pattern: {pattern}")

                # Normalize to consistent format
                if 'AHORR' in tipo:
                    return 'CUENTA DE AHORROS'
                elif 'CORRIENTE' in tipo:
                    return 'CUENTA CORRIENTE'

                return tipo

        logger.warning("Could not extract tipo_cuenta from certificate")
        return None

    def _extract_numero_cuenta(self, text: str) -> Optional[str]:
        """
        Extract account number from certificate

        Typical patterns:
        - Account numbers are usually 10-16 digits
        - Often appear in a table or after "No. Producto", "Cuenta", "Número"
        """
        # Look for patterns like "No. Producto | 77500002334"
        patterns = [
            r'(?:No\.\s*Producto|Número|Cuenta|Account)\s*[:\|]?\s*(\d{10,16})',
            r'\|\s*(\d{10,16})\s*\|',  # Table cell with account number
            r'^(\d{10,16})$',  # Standalone number on a line
        ]

        # First try structured patterns
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                cuenta = match.group(1).strip()
                if 10 <= len(cuenta) <= 16:
                    logger.debug(f"Matched numero_cuenta with pattern: {pattern}")
                    return cuenta

        # Fallback: find any sequence of 10-16 digits that looks like an account number
        # This is more aggressive but may be necessary for some formats
        all_numbers = re.findall(r'\b(\d{10,16})\b', text)
        if all_numbers:
            # Take the first one that's not likely a NIT or phone number
            for num in all_numbers:
                # Skip if it looks like a NIT (typically 9-10 digits with specific patterns)
                if len(num) >= 12 or (len(num) == 11):
                    logger.debug(f"Using fallback match for numero_cuenta: {num}")
                    return num

        logger.warning("Could not extract numero_cuenta from certificate")
        return None

    def _extract_numero_certificado(self, text: str) -> Optional[str]:
        """
        Extract certificate number (optional field)

        Typical patterns:
        - "Certificado No. 123456"
        - "No. Certificado: ABC-123"
        """
        patterns = [
            r'Certificado\s+No\.?\s*:?\s*([A-Z0-9\-]+)',
            r'No\.\s*Certificado\s*:?\s*([A-Z0-9\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.debug(f"Matched numero_certificado with pattern: {pattern}")
                return match.group(1).strip()

        return None

    def _extract_fecha_emision(self, text: str) -> Optional[str]:
        """
        Extract certificate issue date (optional field)

        Typical patterns:
        - "Fecha: 2025-11-06"
        - "Fecha de expedición: 06/11/2025"
        """
        patterns = [
            r'Fecha\s+de\s+expedición\s*:?\s*(\d{2,4}[-/]\d{1,2}[-/]\d{2,4})',
            r'Fecha\s*:?\s*(\d{2,4}[-/]\d{1,2}[-/]\d{2,4})',
            r'Emitido\s*:?\s*(\d{2,4}[-/]\d{1,2}[-/]\d{2,4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.debug(f"Matched fecha_emision with pattern: {pattern}")
                return match.group(1).strip()

        return None
