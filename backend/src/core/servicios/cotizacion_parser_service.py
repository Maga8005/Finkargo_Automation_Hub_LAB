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

    def _parse_cop_amount(self, amount_str: str) -> Optional[Decimal]:
        """
        Parse Colombian peso amount from PDF text.

        Handles formats like:
        - " COP                              407.001,00 "
        - "COP 290.000,00"
        - "407.001,00"
        - "-" (empty/zero)

        Colombian format uses:
        - Period (.) as thousands separator
        - Comma (,) as decimal separator

        Returns:
            Decimal amount or None if invalid/empty
        """
        if not amount_str:
            return None

        # Strip whitespace and COP prefix
        cleaned = amount_str.strip()
        cleaned = re.sub(r'^COP\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()

        # Handle empty amounts (shown as "-" in the PDF)
        if cleaned == '-' or cleaned == '':
            return None

        # Remove thousands separators (periods) and convert decimal separator (comma) to period
        # Format: 407.001,00 -> 407001.00
        # First, remove all periods (thousands separators)
        cleaned = cleaned.replace('.', '')
        # Then convert comma to period (decimal separator)
        cleaned = cleaned.replace(',', '.')

        try:
            amount = Decimal(cleaned)
            # Validate reasonable amount (> 0, < 1 trillion)
            if amount > 0 and amount < 1_000_000_000_000:
                return amount
            return None
        except Exception as e:
            logger.warning(f"Could not parse COP amount '{amount_str}': {e}")
            return None

    def _extract_anexo_table(self, text: str) -> list[AnexoItem]:
        """
        Extract Anexo I table data from PDF.

        Expected columns: Acreedor, No. Instrumento, Monto

        PyMuPDF extracts table cells on separate lines. The PDF structure is:
        - Table header: "Acreedor del Gasto Nacional de Importación"
        - Data rows (3 lines each): acreedor, numero_instrumento, monto
        - Empty rows: "0", "0  COP -"
        - Total row: " COP 739.860,00 "
        - Footer: "ANEXO I"

        We parse from the table header UNTIL we hit "ANEXO I" or end of document.
        """
        anexo_items = []

        # Find the table header row - this marks the start of the Anexo I table
        header_pattern = r'Acreedor del Gasto Nacional de Importaci[oó]n'
        header_match = re.search(header_pattern, text, re.IGNORECASE)

        if not header_match:
            logger.warning("Could not find Anexo I table header in PDF")
            return anexo_items

        # Get text from header to end, then find where ANEXO I appears (as footer)
        table_start = header_match.start()
        table_text = text[table_start:]

        # Find where "ANEXO I" appears (as the table footer/title at the end)
        anexo_footer = re.search(r'\bANEXO\s+I\s*$', table_text, re.IGNORECASE | re.MULTILINE)
        if anexo_footer:
            table_text = table_text[:anexo_footer.start()]

        logger.info(f"Found Anexo I table header at position {table_start}")

        # Split into lines and clean
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]

        logger.debug(f"Processing {len(lines)} lines in Anexo I table")

        # Skip header lines (first 3 lines are the column headers)
        # "Acreedor del Gasto Nacional de Importación."
        # "No. de Instrumento de Pago"
        # "Monto del Instrumento de Pago (COP$)"
        i = 0
        header_keywords = ['Acreedor', 'No. de Instrumento', 'Monto del Instrumento', 'Instrumento de Pago']
        while i < len(lines) and any(keyword in lines[i] for keyword in header_keywords):
            i += 1

        # Now process data rows
        # Table structure (each data row spans 3 lines):
        # Line N: "Entidad de pago de Impuestos" (acreedor - text with letters)
        # Line N+1: "1003887257" (numero_instrumento - digits only)
        # Line N+2: " COP 407.001,00 " (monto - COP amount)
        #
        # Empty rows have structure:
        # Line N: "0" (acreedor = 0)
        # Line N+1: "0  COP -" (combined instrumento + monto, both zero/empty)

        while i < len(lines):
            line1 = lines[i]

            # Stop if we hit a total line (COP without preceding acreedor pattern)
            if line1.strip().startswith('COP') or (line1.strip().startswith(' COP') and 'Entidad' not in line1):
                logger.debug(f"Reached total line at index {i}: '{line1}'")
                break

            # Skip empty/placeholder rows (where acreedor is "0")
            if line1 == "0":
                i += 1
                # Next line should be "0  COP -" (combined), skip it too
                if i < len(lines) and lines[i].startswith("0"):
                    i += 1
                continue

            # Check if this looks like a valid acreedor (contains letters, not just digits/symbols)
            is_valid_acreedor = bool(re.search(r'[A-Za-zÁÉÍÓÚáéíóúñÑ]', line1))

            if not is_valid_acreedor:
                i += 1
                continue

            # Get next two lines for instrumento and monto
            if i + 2 >= len(lines):
                break

            line2 = lines[i + 1]
            line3 = lines[i + 2]

            # Check if line2 looks like an instrument number (only digits)
            is_valid_instrumento = bool(re.match(r'^\d+$', line2))

            # Check if line3 contains COP amount
            has_cop_amount = 'COP' in line3

            if is_valid_instrumento and has_cop_amount:
                acreedor = line1.strip()
                numero_instrumento = line2.strip()
                monto = self._parse_cop_amount(line3)

                if monto is not None:
                    try:
                        item = AnexoItem(
                            acreedor=acreedor,
                            numero_instrumento=numero_instrumento,
                            monto=monto
                        )
                        anexo_items.append(item)
                        logger.debug(f"Extracted anexo item: {acreedor} | {numero_instrumento} | {monto}")
                    except Exception as e:
                        logger.warning(f"Failed to create AnexoItem: {e}")

                i += 3  # Move to next row group
            else:
                i += 1  # Move to next line if pattern doesn't match

        logger.info(f"Extracted {len(anexo_items)} anexo items from ANEXO I table")
        if anexo_items:
            total = sum(item.monto for item in anexo_items)
            logger.info(f"Total amount from extracted items: {total} COP")

        return anexo_items
