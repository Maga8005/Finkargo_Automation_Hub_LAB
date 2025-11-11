"""
RUT Parser Service - Extracts custodian information from Colombian RUT documents
"""
import fitz  # PyMuPDF
import logging
import re
from typing import Dict, Any, Optional

# Import CustodianData from legal_dtos to avoid duplicate class definitions
from src.interface.legal_dtos import CustodianData

logger = logging.getLogger(__name__)


# RUT Field Mapping Configuration
RUT_FIELD_MAPPING = {
    "NOMBRE_DEL_OPERADOR_CUSTODIO": {
        "field_number": "35",
        "field_name": "Razón social",
        "page": 1,
        "type": "text",
        "description": "Company legal name"
    },
    "CIUDAD_DOMICILIO": {
        "field_number": "40",
        "field_name": "Ciudad/Municipio",
        "page": 1,
        "type": "text",
        "description": "City/Municipality where company is located"
    },
    "NIT_OPERADOR_CUSTODIO": {
        "field_number": "5",
        "field_name": "Número de Identificación Tributaria (NIT)",
        "page": 1,
        "type": "nit",
        "includes_dv": True,
        "dv_field": "6",
        "description": "Tax identification number with verification digit"
    },
    "NOMBRE_REPRESENTANTE_LEGAL": {
        "field_numbers": ["104", "105", "106", "107"],
        "field_names": ["Primer apellido", "Segundo apellido", "Primer nombre", "Otros nombres"],
        "page": 3,
        "type": "full_name",
        "representation_type": "REPRS LEGAL PRIN",
        "description": "Legal representative full name (first rep listed)"
    },
    "EMAIL_OPERADOR_CUSTODIO": {
        "field_number": "42",
        "field_name": "Correo electrónico",
        "page": 1,
        "type": "email",
        "description": "Company contact email"
    },
    "CC_REPRESENTANTE_LEGAL": {
        "field_number": "101",
        "field_name": "Número de identificación",
        "page": 3,
        "type": "text",
        "representation_type": "REPRS LEGAL PRIN",
        "description": "Legal representative ID number (cedula)"
    }
}


class RUTParserService:
    """Service for parsing Colombian RUT (Registro Único Tributario) documents"""

    def __init__(self):
        """Initialize RUT parser service"""
        self.field_mapping = RUT_FIELD_MAPPING

    def parse_rut_pdf(self, pdf_bytes: bytes) -> CustodianData:
        """
        Parse RUT PDF and extract custodian data

        Args:
            pdf_bytes: RUT PDF file content as bytes

        Returns:
            CustodianData: Extracted custodian information

        Raises:
            ValueError: If PDF is invalid or required fields cannot be extracted
        """
        try:
            # Open PDF document
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            if len(doc) < 3:
                raise ValueError("Invalid RUT document: Expected at least 3 pages")

            logger.info(f"Parsing RUT document with {len(doc)} pages")

            # Extract all required fields
            extracted_data = {}

            # Page 1 fields: Company name, city, NIT, email
            page_1 = doc[0]  # Page 1 (0-indexed)
            page_1_text = page_1.get_text()

            # Extract company name (field 35 - Razón social)
            extracted_data['nombre_operador_custodio'] = self._extract_razon_social(page_1, page_1_text)

            # Extract city (field 40 - Ciudad/Municipio)
            extracted_data['ciudad_domicilio_custodio'] = self._extract_city(page_1, page_1_text)

            # Extract NIT with DV (fields 5 and 6)
            extracted_data['nit_operador_custodio'] = self._extract_nit_with_dv(page_1, page_1_text)

            # Extract email (field 42 - Correo electrónico)
            extracted_data['email_operador_custodio'] = self._extract_email(page_1, page_1_text)

            # Page 3 fields: Legal representative info
            page_3 = doc[2]  # Page 3 (0-indexed)
            page_3_text = page_3.get_text()

            # Extract legal representative full name (fields 104-107)
            extracted_data['nombre_representante_legal_custodio'] = self._extract_legal_rep_name(page_3, page_3_text)

            # Extract legal representative ID (field 101)
            extracted_data['cc_representante_legal_custodio'] = self._extract_legal_rep_id(page_3, page_3_text)

            # Close document
            doc.close()

            # Validate all fields are present
            for key, value in extracted_data.items():
                if not value or value.strip() == '':
                    raise ValueError(f"Required field '{key}' is empty or could not be extracted")

            logger.info("RUT parsing completed successfully")
            logger.debug(f"Extracted data: {extracted_data}")

            # Create and validate CustodianData model
            custodian_data = CustodianData(**extracted_data)
            return custodian_data

        except fitz.FileDataError as e:
            logger.error(f"Invalid PDF file: {e}")
            raise ValueError(f"Invalid PDF file format: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing RUT document: {e}", exc_info=True)
            raise ValueError(f"Error parsing RUT document: {str(e)}")

    def _extract_razon_social(self, page, page_text: str) -> str:
        """
        Extract company name from field 35 (Razón social)

        The field appears after "35. Razón social" label on page 1
        """
        logger.debug("Extracting Razón social (field 35)")

        # Method 1: Search for pattern after field label
        pattern = r'35\.\s*Razón social\s*\n\s*(.+?)(?:\n|$)'
        match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)

        if match:
            razon_social = match.group(1).strip()
            logger.info(f"Extracted Razón social: {razon_social}")
            return razon_social

        # Method 2: Look for text after "Razón social" label
        lines = page_text.split('\n')
        for i, line in enumerate(lines):
            if 'Razón social' in line or '35.' in line:
                # Check next few lines for company name
                for j in range(i, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not any(x in next_line.lower() for x in ['razón', 'social', '35', '36']):
                        if len(next_line) > 3:  # Valid company name
                            logger.info(f"Extracted Razón social (method 2): {next_line}")
                            return next_line

        raise ValueError("Could not extract Razón social (field 35)")

    def _extract_city(self, page, page_text: str) -> str:
        """
        Extract city from field 40 (Ciudad/Municipio)

        Located in UBICACIÓN section on page 1
        """
        logger.debug("Extracting Ciudad/Municipio (field 40)")

        # Strategy 1: Look for UBICACIÓN section and then find city
        ubicacion_match = re.search(r'UBICACIÓN', page_text, re.IGNORECASE)

        if ubicacion_match:
            # Get text after UBICACIÓN (next 500 chars)
            text_after_ubicacion = page_text[ubicacion_match.end():ubicacion_match.end() + 500]

            # Look for field 40 pattern
            city_pattern = r'40\.\s*Ciudad/Municipio[^a-zA-Z]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s+\d+\s+\d+\s+\d+|\n|$)'
            city_match = re.search(city_pattern, text_after_ubicacion, re.IGNORECASE)

            if city_match:
                city = city_match.group(1).strip()
                # Remove trailing numbers and clean up
                city = re.sub(r'\s+\d+\s*$', '', city)
                city = re.sub(r'\s{2,}', ' ', city)  # Remove multiple spaces
                # Remove country name if present
                if 'COLOMBIA' in city.upper():
                    # City should be the word after country name
                    parts = city.split()
                    # Filter out COLOMBIA and numbers
                    city_parts = [p for p in parts if p.upper() not in ['COLOMBIA', 'COL'] and not p.isdigit()]
                    if city_parts:
                        city = ' '.join(city_parts)
                logger.info(f"Extracted Ciudad/Municipio: {city}")
                return city

        # Strategy 2: Search for field 40 label anywhere
        pattern = r'40\.\s*Ciudad/Municipio[^a-zA-Z]*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)'
        match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)

        if match:
            city = match.group(1).strip()
            # Clean up
            city = re.sub(r'\s+\d+\s*$', '', city)
            city = re.sub(r'\s{2,}', ' ', city)
            # Remove COLOMBIA if present
            city = re.sub(r'\bCOLOMBIA\b', '', city, flags=re.IGNORECASE).strip()
            if city and len(city) > 2:
                logger.info(f"Extracted Ciudad/Municipio (method 2): {city}")
                return city

        # Strategy 3: Look in lines after field 40 or Ciudad/Municipio
        lines = page_text.split('\n')
        for i, line in enumerate(lines):
            if 'Ciudad/Municipio' in line or '40.' in line:
                # Check next few lines for city name
                for j in range(i, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    # Skip lines with field labels or numbers
                    if next_line and not any(x in next_line.lower() for x in ['ciudad', 'municipio', '40.', '41.']):
                        # Valid city name (letters and spaces only, more than 2 chars)
                        if re.match(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+$', next_line) and len(next_line) > 2:
                            city = next_line
                            # Remove COLOMBIA if present
                            city = re.sub(r'\bCOLOMBIA\b', '', city, flags=re.IGNORECASE).strip()
                            if city:
                                logger.info(f"Extracted Ciudad/Municipio (line scan): {city}")
                                return city

        raise ValueError("Could not extract Ciudad/Municipio (field 40)")

    def _extract_nit_with_dv(self, page, page_text: str) -> str:
        """
        Extract NIT with verification digit from fields 5 and 6

        Field 5: NIT digits (space-separated: "9 0 0 9 8 9 9 2 5")
        Field 6: DV digit ("7")
        Returns formatted NIT: "900989925-7"
        """
        logger.debug("Extracting NIT with DV (fields 5 and 6)")

        # Search for NIT pattern: space-separated digits near field 5
        # Pattern: sequence of single digits separated by spaces
        pattern = r'5\.\s*Número de Identificación Tributaria[^0-9]*?((?:\d\s+){8,}\d)'
        match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)

        nit_digits = None
        dv_digit = None

        if match:
            nit_raw = match.group(1).strip()
            # Remove all spaces to get digits
            nit_digits = re.sub(r'\s+', '', nit_raw)
            logger.debug(f"Extracted NIT digits: {nit_digits}")

        # Search for DV (field 6)
        dv_pattern = r'6\.\s*DV[^0-9]*?(\d)'
        dv_match = re.search(dv_pattern, page_text, re.IGNORECASE)

        if dv_match:
            dv_digit = dv_match.group(1).strip()
            logger.debug(f"Extracted DV: {dv_digit}")

        # Alternative: Extract from formatted display
        if not nit_digits or not dv_digit:
            # Look for pattern like "9 0 0 9 8 9 9 2 5 7" in the text
            alt_pattern = r'((?:\d\s+){8,}\d)\s+(\d)'
            alt_matches = re.findall(alt_pattern, page_text)

            for nit_raw, dv_raw in alt_matches:
                nit_test = re.sub(r'\s+', '', nit_raw.strip())
                if len(nit_test) >= 8:  # Valid NIT length
                    nit_digits = nit_test
                    dv_digit = dv_raw.strip()
                    logger.debug(f"Extracted NIT (alt): {nit_digits}-{dv_digit}")
                    break

        if not nit_digits:
            raise ValueError("Could not extract NIT (field 5)")

        if not dv_digit:
            raise ValueError("Could not extract DV (field 6)")

        # Format as "NIT-DV"
        formatted_nit = f"{nit_digits}-{dv_digit}"
        logger.info(f"Extracted NIT with DV: {formatted_nit}")
        return formatted_nit

    def _extract_email(self, page, page_text: str) -> str:
        """
        Extract email from field 42 (Correo electrónico)

        Located in UBICACIÓN section on page 1
        """
        logger.debug("Extracting Correo electrónico (field 42)")

        # Method 1: Search for email pattern (standard email regex)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, page_text)

        if emails:
            # Return first valid email found
            email = emails[0].strip().lower()
            logger.info(f"Extracted email: {email}")
            return email

        # Method 2: Look for field 42 label
        pattern = r'42\.\s*Correo electrónico\s*\n\s*(.+?)(?:\n|$)'
        match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)

        if match:
            email = match.group(1).strip().lower()
            if '@' in email:
                logger.info(f"Extracted email (method 2): {email}")
                return email

        raise ValueError("Could not extract Correo electrónico (field 42)")

    def _extract_legal_rep_name(self, page, page_text: str) -> str:
        """
        Extract legal representative full name from fields 104-107

        Fields:
        - 104: Primer apellido
        - 105: Segundo apellido
        - 106: Primer nombre
        - 107: Otros nombres

        Only extract from first "REPRS LEGAL PRIN" section
        """
        logger.debug("Extracting legal representative name (fields 104-107)")

        # Find REPRS LEGAL PRIN section
        reprs_pattern = r'REPRS LEGAL PRIN'
        reprs_match = re.search(reprs_pattern, page_text, re.IGNORECASE)

        if not reprs_match:
            raise ValueError("Could not find REPRS LEGAL PRIN section")

        # Extract text after REPRS LEGAL PRIN (next 1000 chars should be enough)
        text_after_reprs = page_text[reprs_match.end():reprs_match.end() + 1000]
        lines = text_after_reprs.split('\n')

        name_parts = []

        # Strategy 1: Look for all 4 capitalized words in sequence
        # Pattern: OLEA SALGADO LILIANA ISABEL
        cap_pattern = r'([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)'
        cap_match = re.search(cap_pattern, text_after_reprs)

        if cap_match:
            name_parts = [p.strip() for p in cap_match.groups() if p]
            logger.info(f"Extracted legal representative name (4 parts): {' '.join(name_parts)}")
            return ' '.join(name_parts)

        # Strategy 2: Look for at least 3 capitalized words
        cap_pattern_3 = r'([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)'
        cap_match_3 = re.search(cap_pattern_3, text_after_reprs)

        if cap_match_3:
            name_parts = [p.strip() for p in cap_match_3.groups() if p]
            logger.info(f"Extracted legal representative name (3 parts): {' '.join(name_parts)}")
            return ' '.join(name_parts)

        # Strategy 3: Search for fields 104-107 labels and extract text after them
        field_104_pattern = r'104\.\s*Primer apellido[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'
        field_105_pattern = r'105\.\s*Segundo apellido[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'
        field_106_pattern = r'106\.\s*Primer nombre[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'
        field_107_pattern = r'107\.\s*Otros nombres[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'

        for pattern in [field_104_pattern, field_105_pattern, field_106_pattern, field_107_pattern]:
            match = re.search(pattern, text_after_reprs, re.IGNORECASE)
            if match:
                name_parts.append(match.group(1).strip())

        if len(name_parts) >= 2:
            full_name = ' '.join(name_parts)
            logger.info(f"Extracted legal representative name (field labels): {full_name}")
            return full_name

        # Strategy 4: Look for name on single line after field labels
        for i, line in enumerate(lines[:20]):
            # Check if line contains all uppercase letters and spaces only (name format)
            if re.match(r'^[A-ZÁÉÍÓÚÑ\s]+$', line.strip(), re.IGNORECASE) and len(line.strip()) > 10:
                # Split into parts
                parts = line.strip().split()
                if 2 <= len(parts) <= 4:
                    # Valid name with 2-4 parts
                    name_parts = parts
                    break

        if len(name_parts) >= 2:
            full_name = ' '.join(name_parts)
            logger.info(f"Extracted legal representative name (line scan): {full_name}")
            return full_name

        # Log debug info
        logger.debug(f"Text after REPRS LEGAL PRIN (first 500 chars): {text_after_reprs[:500]}")
        raise ValueError("Could not extract legal representative name (fields 104-107)")

    def _extract_legal_rep_id(self, page, page_text: str) -> str:
        """
        Extract legal representative ID number from field 101

        Located in first REPRS LEGAL PRIN section
        """
        logger.debug("Extracting legal representative ID (field 101)")

        # Find REPRS LEGAL PRIN section
        reprs_pattern = r'REPRS LEGAL PRIN'
        reprs_match = re.search(reprs_pattern, page_text, re.IGNORECASE)

        if not reprs_match:
            raise ValueError("Could not find REPRS LEGAL PRIN section")

        # Extract text after REPRS LEGAL PRIN (next 1000 chars should be enough)
        text_after_reprs = page_text[reprs_match.end():reprs_match.end() + 1000]

        # Strategy 1: Look for "Cédula de Ciudadaní" or similar followed by digits
        cedula_pattern = r'Cédula\s+de\s+Ciudadan[íi][^0-9]*?(\d[\s\d]{8,15})'
        cedula_match = re.search(cedula_pattern, text_after_reprs, re.IGNORECASE)

        if cedula_match:
            # Remove spaces from digit sequence
            cedula = re.sub(r'\s+', '', cedula_match.group(1))
            if len(cedula) >= 7:
                logger.info(f"Extracted legal representative ID (cedula pattern): {cedula}")
                return cedula

        # Strategy 2: Search for field 101 label followed by ID number
        id_pattern = r'101\.\s*Número de identificación[^0-9]*?(\d[\s\d]{7,15})'
        id_match = re.search(id_pattern, text_after_reprs, re.IGNORECASE)

        if id_match:
            # Remove spaces from digit sequence
            cedula = re.sub(r'\s+', '', id_match.group(1))
            if len(cedula) >= 7:
                logger.info(f"Extracted legal representative ID (field 101): {cedula}")
                return cedula

        # Strategy 3: Look for space-separated digit patterns (like NIT format)
        # Pattern: 1 3 3 3 1 0 1 5 5 1 (10 digits with spaces)
        space_digits_pattern = r'(\d(?:\s+\d){7,10})'
        space_matches = re.findall(space_digits_pattern, text_after_reprs)

        for match in space_matches:
            # Remove spaces
            cedula = re.sub(r'\s+', '', match)
            # Valid cedula length: 7-11 digits
            if 7 <= len(cedula) <= 11:
                logger.info(f"Extracted legal representative ID (space-separated): {cedula}")
                return cedula

        # Strategy 4: Look for any 7-11 digit sequence after "101"
        alt_pattern = r'101[^0-9]{0,100}(\d{7,11})'
        alt_match = re.search(alt_pattern, text_after_reprs)

        if alt_match:
            cedula = alt_match.group(1).strip()
            logger.info(f"Extracted legal representative ID (alt): {cedula}")
            return cedula

        # Log the text we're searching for debugging
        logger.debug(f"Text after REPRS LEGAL PRIN (first 500 chars): {text_after_reprs[:500]}")
        raise ValueError("Could not extract legal representative ID (field 101)")
