"""
Cotización Parser Service - Extracts data from Cotización PDF documents
"""
import fitz  # PyMuPDF
import logging
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional

from src.interface.legal_dtos import CotizacionData, AnexoItem

logger = logging.getLogger(__name__)


# Spanish month mapping
SPANISH_MONTHS = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12
}


class CotizacionParserService:
    """Service for parsing Cotización PDF documents for Solicitud de Desembolso"""

    def __init__(self):
        """Initialize Cotización parser service"""
        pass

    def parse_cotizacion(self, pdf_bytes: bytes) -> CotizacionData:
        """
        Parse Cotización PDF and extract disbursement request data

        Args:
            pdf_bytes: Cotización PDF file content as bytes

        Returns:
            CotizacionData: Extracted cotización information

        Raises:
            ValueError: If PDF is invalid or critical fields cannot be extracted
        """
        try:
            # Open PDF document
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            if len(doc) < 1:
                raise ValueError("Invalid Cotización document: PDF has no pages")

            logger.info(f"Parsing Cotización document with {len(doc)} pages")

            # Extract text from all pages
            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                full_text += page.get_text() + "\n"

            # Extract all fields
            numero_cotizacion = self._extract_numero_cotizacion(full_text)
            fecha_cotizacion = self._extract_fecha_cotizacion(full_text)
            fecha_contrato_credito = self._extract_fecha_contrato_credito(full_text)
            representante_legal = self._extract_representante_legal(full_text)
            tipo_id_representante = self._extract_tipo_id_representante(full_text)
            numero_id_representante = self._extract_numero_id_representante(full_text)
            anexo_items = self._extract_anexo_table(full_text)

            # Calculate total from anexo items
            monto_total = sum(item.monto for item in anexo_items) if anexo_items else Decimal('0')

            # Close document
            doc.close()

            # Validate critical fields
            if not numero_cotizacion:
                raise ValueError("Could not extract numero_cotizacion (critical field)")

            if not anexo_items:
                logger.warning("No anexo items extracted - table may be empty or malformed")

            if monto_total <= 0:
                logger.warning(f"Monto total is {monto_total} - expected positive value")

            logger.info("Cotización parsing completed successfully")
            logger.debug(f"Extracted numero_cotizacion: {numero_cotizacion}")
            logger.debug(f"Extracted {len(anexo_items)} anexo items, total: {monto_total}")

            # Create and return CotizacionData model
            cotizacion_data = CotizacionData(
                numero_cotizacion=numero_cotizacion,
                fecha_cotizacion=fecha_cotizacion,
                fecha_contrato_credito=fecha_contrato_credito,
                representante_legal=representante_legal,
                tipo_id_representante=tipo_id_representante,
                numero_id_representante=numero_id_representante,
                anexo_items=anexo_items,
                monto_total=monto_total
            )
            return cotizacion_data

        except fitz.FileDataError as e:
            logger.error(f"Invalid PDF file: {e}")
            raise ValueError(f"Invalid PDF file: {e}")
        except Exception as e:
            logger.error(f"Error parsing Cotización PDF: {e}")
            raise ValueError(f"Error parsing Cotización PDF: {e}")

    def _extract_numero_cotizacion(self, text: str) -> str:
        """
        Extract quote number from PDF
        Expected format: CO:{NIT}:{sequence}:{type}:DOM
        Example: CO:900436389:1:2:DOM
        """
        # Pattern: CO followed by digits separated by colons, ending with DOM
        pattern = r'CO:\d+:\d+:\d+:DOM'
        match = re.search(pattern, text)

        if match:
            numero = match.group(0)
            logger.debug(f"Extracted numero_cotizacion: {numero}")
            return numero

        # Fallback: look for "Cotización" or "cotización" followed by number
        pattern_fallback = r'[Cc]otizaci[oó]n\s*[Nn][oú]\.?\s*[:=]?\s*([\w\-:]+)'
        match_fallback = re.search(pattern_fallback, text)
        if match_fallback:
            numero = match_fallback.group(1).strip()
            logger.debug(f"Extracted numero_cotizacion (fallback): {numero}")
            return numero

        logger.warning("Could not extract numero_cotizacion")
        return ""

    def _extract_fecha_cotizacion(self, text: str) -> Optional[str]:
        """
        Extract quote date from PDF
        Expected format: "DD de MONTH de YYYY" (Spanish)
        Example: "10 de noviembre de 2025"
        """
        return self._parse_spanish_date(text, context="cotización")

    def _extract_fecha_contrato_credito(self, text: str) -> Optional[str]:
        """
        Extract credit contract date from PDF
        Expected format: "DD de MONTH de YYYY" (Spanish)
        """
        return self._parse_spanish_date(text, context="contrato")

    def _parse_spanish_date(self, text: str, context: str = "") -> Optional[str]:
        """
        Parse Spanish date format: "DD de MONTH de YYYY"
        Returns ISO format date string: "YYYY-MM-DD"
        """
        # Pattern: day (1-2 digits) de month (word) de year (4 digits)
        pattern = r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            day_str = match.group(1)
            month_str = match.group(2).lower()
            year_str = match.group(3)

            # Convert month name to number
            month_num = SPANISH_MONTHS.get(month_str)

            if month_num:
                try:
                    # Validate and create date
                    date_obj = datetime(int(year_str), month_num, int(day_str))
                    date_iso = date_obj.strftime('%Y-%m-%d')
                    logger.debug(f"Extracted date ({context}): {date_iso}")
                    return date_iso
                except ValueError as e:
                    logger.warning(f"Invalid date values: day={day_str}, month={month_str}, year={year_str}: {e}")
                    continue

        logger.warning(f"Could not extract Spanish date for context: {context}")
        return None

    def _extract_representante_legal(self, text: str) -> Optional[str]:
        """
        Extract legal representative name from PDF
        Typically found in structured sections of the document
        """
        # Pattern: "Representante Legal:" followed by name
        pattern = r'[Rr]epresentante\s+[Ll]egal\s*[:=]?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)'
        match = re.search(pattern, text)

        if match:
            name = match.group(1).strip()
            logger.debug(f"Extracted representante_legal: {name}")
            return name

        # Fallback: Look for patterns like "Nombre: [Name]" in page 2 area
        pattern_fallback = r'[Nn]ombre\s*[:=]\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)'
        match_fallback = re.search(pattern_fallback, text)
        if match_fallback:
            name = match_fallback.group(1).strip()
            logger.debug(f"Extracted representante_legal (fallback): {name}")
            return name

        logger.warning("Could not extract representante_legal")
        return None

    def _extract_tipo_id_representante(self, text: str) -> Optional[str]:
        """
        Extract representative ID type from PDF
        Expected: C.C., C.E., NIT, etc.
        """
        # Pattern: Common ID types
        pattern = r'\b(C\.C\.|C\.E\.|NIT|Pasaporte|T\.I\.)\b'
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            tipo = match.group(1).upper()
            logger.debug(f"Extracted tipo_id_representante: {tipo}")
            return tipo

        logger.warning("Could not extract tipo_id_representante")
        return None

    def _extract_numero_id_representante(self, text: str) -> Optional[str]:
        """
        Extract representative ID number from PDF
        Typically follows tipo_id_representante
        """
        # Pattern: ID type followed by number
        pattern = r'(?:C\.C\.|C\.E\.|NIT|Pasaporte|T\.I\.)\s*[:\.]?\s*([\d\.\-]+)'
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            numero = match.group(1).strip()
            logger.debug(f"Extracted numero_id_representante: {numero}")
            return numero

        logger.warning("Could not extract numero_id_representante")
        return None

    def _extract_anexo_table(self, text: str) -> list[AnexoItem]:
        """
        Extract Anexo I table data from PDF
        Expected columns: Acreedor, No. Instrumento, Monto

        This is a simplified extraction - may need refinement based on actual PDF structure
        """
        anexo_items = []

        # Look for "Anexo I" section
        anexo_pattern = r'Anexo\s+I'
        anexo_match = re.search(anexo_pattern, text, re.IGNORECASE)

        if not anexo_match:
            logger.warning("Could not find 'Anexo I' section in PDF")
            return anexo_items

        # Get text after Anexo I heading
        anexo_start = anexo_match.end()
        anexo_text = text[anexo_start:anexo_start + 5000]  # Extract next ~5000 chars

        # Pattern: Extract table rows (simplified - assumes specific structure)
        # Looking for lines with: text, number, currency amount
        # Example: "Entidad de pago de Impuestos    1003887257    $407,001.00"

        # Split into lines
        lines = anexo_text.split('\n')

        for line in lines:
            # Skip empty lines or header lines
            if not line.strip() or 'Acreedor' in line or 'Total' in line.lower():
                continue

            # Try to extract: acreedor (text), numero_instrumento (digits), monto (currency)
            # Pattern: text followed by digits followed by currency
            row_pattern = r'([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s+(\d+)\s+\$?\s?([\d,\.]+)'
            row_match = re.search(row_pattern, line)

            if row_match:
                acreedor = row_match.group(1).strip()
                numero_instrumento = row_match.group(2).strip()
                monto_str = row_match.group(3).strip()

                # Clean monto: remove commas, convert to Decimal
                monto_clean = monto_str.replace(',', '').replace('.', '')

                try:
                    # Parse as integer (Colombian peso format: no decimals in practice)
                    monto = Decimal(monto_clean)

                    # Validate reasonable amount (> 0, < 1 billion)
                    if 0 < monto < 1_000_000_000:
                        item = AnexoItem(
                            acreedor=acreedor,
                            numero_instrumento=numero_instrumento,
                            monto=monto
                        )
                        anexo_items.append(item)
                        logger.debug(f"Extracted anexo item: {acreedor} - {monto}")
                except (ValueError, Exception) as e:
                    logger.warning(f"Could not parse anexo row: {line} - {e}")
                    continue

        logger.info(f"Extracted {len(anexo_items)} anexo items from table")
        return anexo_items
