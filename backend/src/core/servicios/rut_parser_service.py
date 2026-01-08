"""
RUT Parser Service - Extracts custodian information from Colombian RUT documents
"""
import fitz  # PyMuPDF
import logging
import re

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
    },
    "TIPO_IDENTIFICACION_REPRESENTANTE_LEGAL": {
        "field_number": "100",
        "field_name": "Tipo de documento",
        "page": 3,
        "type": "text",
        "representation_type": "REPRS LEGAL PRIN",
        "description": "Legal representative ID type (e.g., Cédula de Ciudadanía, Cédula de Extranjería)"
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

            # Extract legal representative ID type (field 100)
            extracted_data['tipo_identificacion_representante_legal_custodio'] = self._extract_legal_rep_id_type(page_3, page_3_text)

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
        Note: Different RUT formats may have company name in different locations
        """
        logger.debug("Extracting Razón social (field 35)")

        # Strategy 1: Search for pattern after field label (Format 1)
        pattern = r'35\.\s*Razón social\s*\n\s*(.+?)(?:\n|$)'
        match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)

        if match:
            razon_social = match.group(1).strip()
            # Validate it's not another field label
            if not re.match(r'^\d+\.', razon_social) and len(razon_social) > 3:
                logger.info(f"Extracted Razón social (pattern): {razon_social}")
                return razon_social

        # Strategy 2: Look in UBICACIÓN section (Format 2)
        # In some RUT formats, the company name appears in the data section after UBICACIÓN
        ubicacion_match = re.search(r'UBICACIÓN', page_text, re.IGNORECASE)
        if ubicacion_match:
            text_after_ubicacion = page_text[ubicacion_match.end():ubicacion_match.end() + 800]

            # Look for capitalized company name pattern (typically all caps, ends with S.A.S, LTDA, etc.)
            # Should appear before COLOMBIA
            company_pattern = r'\n\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.&\-]+(?:S\.A\.S|LTDA|S\.A\.|SAS|E\.U\.))\s*\n'
            company_match = re.search(company_pattern, text_after_ubicacion, re.IGNORECASE)

            if company_match:
                razon_social = company_match.group(1).strip()
                if len(razon_social) > 3:
                    logger.info(f"Extracted Razón social (UBICACIÓN): {razon_social}")
                    return razon_social

        # Strategy 3: Look for all-caps text lines that look like company names
        # Search for lines with all uppercase letters, possibly with S.A.S, LTDA, etc.
        lines = page_text.split('\n')
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Company name pattern: All caps, multiple words, ends with legal entity type
            if re.match(r'^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.&\-]{5,}(?:S\.A\.S|LTDA|S\.A\.|SAS|E\.U\.)$', line_stripped, re.IGNORECASE):
                # Verify it's not after irrelevant fields
                # Check if this appears in a reasonable location (not in signatures, etc.)
                context_before = ' '.join(lines[max(0, i-3):i])
                if 'UBICACIÓN' in context_before or 'IDENTIFICACIÓN' in context_before or '35' in context_before:
                    logger.info(f"Extracted Razón social (all-caps scan): {line_stripped}")
                    return line_stripped

        # Strategy 4: Line scan after field 35 label
        for i, line in enumerate(lines):
            if 'Razón social' in line or ('35.' in line and 'Raz' in line):
                # Check next few lines for company name
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    # Skip field labels and short lines
                    if re.match(r'^\d+\.', next_line):
                        continue
                    if len(next_line) < 4:
                        continue
                    # Skip common non-company text
                    if any(x in next_line.lower() for x in ['primer', 'segundo', 'apellido', 'nombre', 'tipo', 'documento']):
                        continue
                    # Valid company name candidate
                    if len(next_line) > 3 and any(c.isalpha() for c in next_line):
                        logger.info(f"Extracted Razón social (line scan): {next_line}")
                        return next_line

        raise ValueError("Could not extract Razón social (field 35)")

    def _extract_city(self, page, page_text: str) -> str:
        """
        Extract city from field 40 (Ciudad/Municipio)

        Located in UBICACIÓN section on page 1

        Structure varies by RUT format:
        Format 1:
            40. Ciudad/Municipio
            COLOMBIA
            1 6 9 Bolívar
            1 3 Cartagena
            0 0 1

        Format 2:
            COLOMBIA
            1 6 9
            Bogotá D.C.
            1 1
            Bogotá, D.C.
            0 0 1

        The city name may appear with comma (e.g., "Bogotá, D.C.")
        """
        logger.debug("Extracting Ciudad/Municipio (field 40)")

        # Strategy 1: Look for UBICACIÓN section and find city pattern with comma
        # Format: "Bogotá, D.C." or similar with comma
        ubicacion_match = re.search(r'UBICACIÓN', page_text, re.IGNORECASE)
        if ubicacion_match:
            text_after_ubicacion = page_text[ubicacion_match.end():ubicacion_match.end() + 800]

            # Look for city pattern with comma (e.g., "Bogotá, D.C.")
            city_comma_pattern = r'\n\s*([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ\s]+,\s*[A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ\.]+)\s*\n'
            city_comma_match = re.search(city_comma_pattern, text_after_ubicacion, re.IGNORECASE)

            if city_comma_match:
                city = city_comma_match.group(1).strip()
                logger.info(f"Extracted Ciudad/Municipio (comma format): {city}")
                return city

        # Strategy 2: Look for field 40, skip country and department lines, extract city
        # Pattern: Find "40. Ciudad/Municipio", skip 2 lines (COLOMBIA, department), capture city on 3rd line
        field_40_pattern = r'40\.\s*Ciudad/Municipio[^\n]*\n[^\n]*\n[^\n]*\n\s*\d+\s+\d+\s+([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ\s,\.]+?)(?:\s*\n|$)'
        field_40_match = re.search(field_40_pattern, page_text, re.IGNORECASE)

        if field_40_match:
            city = field_40_match.group(1).strip()
            # Clean up any trailing numbers or spaces
            city = re.sub(r'\s+\d+.*$', '', city).strip()
            if city and len(city) > 2:
                logger.info(f"Extracted Ciudad/Municipio (field 40 pattern): {city}")
                return city

        # Strategy 3: Line-by-line search in UBICACIÓN section
        # Look for city names after COLOMBIA line
        if ubicacion_match:
            text_after_ubicacion = page_text[ubicacion_match.end():ubicacion_match.end() + 800]
            lines = text_after_ubicacion.split('\n')

            colombia_found = False
            for i, line in enumerate(lines):
                line_stripped = line.strip()

                # Mark when we find COLOMBIA
                if 'COLOMBIA' in line_stripped.upper():
                    colombia_found = True
                    continue

                # After finding COLOMBIA, look for city pattern
                if colombia_found and line_stripped:
                    # Skip pure number lines
                    if re.match(r'^\d+(\s+\d+)*$', line_stripped):
                        continue

                    # Skip field labels
                    if re.match(r'^\d+\.', line_stripped):
                        break

                    # Look for city name with optional comma (e.g., "Bogotá, D.C." or "Cartagena")
                    city_match = re.match(r'^(?:\d+\s+\d+\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ\s,\.]+?)(?:\s*$|\s+\d)', line_stripped, re.IGNORECASE)
                    if city_match:
                        city = city_match.group(1).strip()

                        # Clean up trailing numbers
                        city = re.sub(r'\s+\d+.*$', '', city).strip()

                        # Skip if it looks like a department
                        if city.upper() in ['BOLÍVAR', 'BOLIVAR', 'ANTIOQUIA', 'CUNDINAMARCA', 'VALLE', 'ATLÁNTICO', 'ATLANTICO', 'BOGOTÁ D.C.']:
                            # Check if next line has actual city
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                next_city_match = re.match(r'^(?:\d+\s+\d+\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ\s,\.]+?)(?:\s*$|\s+\d)', next_line, re.IGNORECASE)
                                if next_city_match:
                                    city = next_city_match.group(1).strip()
                                    city = re.sub(r'\s+\d+.*$', '', city).strip()

                        if city and len(city) > 2:
                            logger.info(f"Extracted Ciudad/Municipio (UBICACIÓN line scan): {city}")
                            return city

        # Strategy 4: Look for UBICACIÓN section pattern matching
        # Find all city-like patterns (text with comma or capitalized)
        if ubicacion_match:
            text_after_ubicacion = page_text[ubicacion_match.end():ubicacion_match.end() + 800]

            # Pattern: digits + city name (with optional comma)
            city_lines = re.findall(r'(?:\d+\s+\d+\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ\s,\.]+?)(?:\s*\n|\s+\d)', text_after_ubicacion, re.IGNORECASE)

            # Filter out short matches and find city (should be after department)
            for city_candidate in city_lines:
                city_candidate = city_candidate.strip()
                # Valid city: more than 2 chars, has comma OR is capitalized properly
                if len(city_candidate) > 2:
                    # Prefer cities with commas (like "Bogotá, D.C.")
                    if ',' in city_candidate:
                        logger.info(f"Extracted Ciudad/Municipio (pattern with comma): {city_candidate}")
                        return city_candidate
                    # Or valid capitalized city names
                    if city_candidate.upper() not in ['COLOMBIA', 'BOLÍVAR', 'BOLIVAR', 'ANTIOQUIA']:
                        logger.info(f"Extracted Ciudad/Municipio (pattern): {city_candidate}")
                        return city_candidate

        raise ValueError("Could not extract Ciudad/Municipio (field 40)")

    def _extract_nit_with_dv(self, page, page_text: str) -> str:
        """
        Extract NIT with verification digit from fields 5 and 6

        Field 5: NIT digits (space-separated: "9 0 0 9 8 9 9 2 5" or newline-separated)
        Field 6: DV digit ("7")
        Returns formatted NIT: "900989925-7"
        """
        logger.debug("Extracting NIT with DV (fields 5 and 6)")

        nit_digits = None
        dv_digit = None

        # Strategy 1: Look for newline-separated digits (GAMALOG format)
        # Pattern: 9 digits on separate lines followed by DV digit
        # These appear after form number and before "Impuestos de" or similar
        lines = page_text.split('\n')
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Look for single digit that could start NIT sequence
            if line_stripped.isdigit() and len(line_stripped) == 1:
                # Check if we have 9 consecutive single-digit lines (NIT) + 1 (DV)
                digit_sequence = []
                for j in range(i, min(i + 12, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.isdigit() and len(next_line) == 1:
                        digit_sequence.append(next_line)
                    elif next_line == '':
                        continue  # Skip empty lines
                    else:
                        break

                # Valid NIT: 9 digits + 1 DV = 10 total
                if len(digit_sequence) >= 10:
                    potential_nit = ''.join(digit_sequence[:9])
                    potential_dv = digit_sequence[9]
                    # Validate: NIT should start with 8 or 9 for most Colombian companies
                    if potential_nit[0] in ['8', '9'] and len(potential_nit) == 9:
                        nit_digits = potential_nit
                        dv_digit = potential_dv
                        logger.debug(f"Extracted NIT (newline format): {nit_digits}-{dv_digit}")
                        break

        # Strategy 2: Search for NIT pattern: space-separated digits near field 5
        if not nit_digits:
            pattern = r'5\.\s*Número de Identificación Tributaria[^0-9]*?((?:\d\s+){8,}\d)'
            match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)

            if match:
                nit_raw = match.group(1).strip()
                # Remove all spaces to get digits
                nit_digits = re.sub(r'\s+', '', nit_raw)
                logger.debug(f"Extracted NIT digits (strategy 2): {nit_digits}")

        # Search for DV (field 6) if not found yet
        if not dv_digit:
            dv_pattern = r'6\.\s*DV[^0-9]*?(\d)'
            dv_match = re.search(dv_pattern, page_text, re.IGNORECASE)

            if dv_match:
                dv_digit = dv_match.group(1).strip()
                logger.debug(f"Extracted DV: {dv_digit}")

        # Strategy 3: Extract from formatted display (space-separated)
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

        Note: In some RUT formats (like GAMALOG), names appear in columnar format
        where multiple representatives' names are interleaved (e.g., GALVIS, NAVARRO, ROZO
        are first names of 3 different reps). We need to extract only the first rep's name parts.
        """
        logger.debug("Extracting legal representative name (fields 104-107)")

        # Find REPRS LEGAL PRIN section
        reprs_pattern = r'REPRS LEGAL PRIN'
        reprs_match = re.search(reprs_pattern, page_text, re.IGNORECASE)

        if not reprs_match:
            raise ValueError("Could not find REPRS LEGAL PRIN section")

        # Extract text after REPRS LEGAL PRIN (next 2000 chars to include name section)
        text_after_reprs = page_text[reprs_match.end():reprs_match.end() + 2000]
        lines = text_after_reprs.split('\n')

        name_parts = []

        # Strategy 1 (GAMALOG format): Find capitalized names appearing in columnar format
        # In this format, names appear on separate lines and we need every Nth name
        # The pattern is: first names of all reps, then second names of all reps, etc.
        # Count how many reps there are by looking for REPRS sections
        num_reps = 1  # At least 1 (REPRS LEGAL PRIN)
        if 'REPRS LEGAL SUPL' in text_after_reprs:
            num_reps += 1
        if 'APOD. ESPECIAL' in text_after_reprs:
            num_reps += 1
        if 'APOD. GENERAL' in text_after_reprs:
            num_reps += 1

        # Look for sequence of capitalized names (single words on their own lines)
        # These appear after the ID numbers section
        cap_name_lines = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Name must be all caps, letters only, 2-15 chars, and on its own line
            if (re.match(r'^[A-ZÁÉÍÓÚÑ]{2,15}$', line_stripped) and
                    line_stripped not in ['COLOMBIA', 'SI', 'NO', 'DV', 'NIT']):
                cap_name_lines.append((i, line_stripped))

        # If we found capitalized names in columnar format
        if len(cap_name_lines) >= num_reps * 2:  # At least 2 name parts per rep
            # Extract first rep's name parts (every num_reps-th name)
            # Names appear as: [rep1_apellido1, rep2_apellido1, rep3_apellido1, rep1_apellido2, ...]
            first_rep_names = []
            # Take the first name from each group of num_reps names
            for j in range(0, min(len(cap_name_lines), num_reps * 4), num_reps):
                if j < len(cap_name_lines):
                    first_rep_names.append(cap_name_lines[j][1])

            # Should have up to 4 parts (primer apellido, segundo apellido, primer nombre, otros nombres)
            if len(first_rep_names) >= 2:
                name_parts = first_rep_names[:4]
                full_name = ' '.join(name_parts)
                logger.info(f"Extracted legal representative name (columnar format, {num_reps} reps): {full_name}")
                return full_name

        # Strategy 2: Look for all 4 capitalized words in sequence on same line
        # Pattern: OLEA SALGADO LILIANA ISABEL
        cap_pattern = r'([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)'
        cap_match = re.search(cap_pattern, text_after_reprs)

        if cap_match:
            name_parts = [p.strip() for p in cap_match.groups() if p]
            # Make sure it's not from rep type labels
            combined = ' '.join(name_parts)
            if 'LEGAL' not in combined and 'ESPECIAL' not in combined:
                logger.info(f"Extracted legal representative name (4 parts): {combined}")
                return combined

        # Strategy 3: Look for at least 3 capitalized words
        cap_pattern_3 = r'([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)\s+([A-ZÁÉÍÓÚÑ]+)'
        cap_match_3 = re.search(cap_pattern_3, text_after_reprs)

        if cap_match_3:
            name_parts = [p.strip() for p in cap_match_3.groups() if p]
            combined = ' '.join(name_parts)
            if 'LEGAL' not in combined and 'ESPECIAL' not in combined:
                logger.info(f"Extracted legal representative name (3 parts): {combined}")
                return combined

        # Strategy 4: Search for fields 104-107 labels and extract text after them
        field_104_pattern = r'104\.\s*Primer apellido[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'
        field_105_pattern = r'105\.\s*Segundo apellido[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'
        field_106_pattern = r'106\.\s*Primer nombre[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'
        field_107_pattern = r'107\.\s*Otros nombres[^\n]*\n\s*([A-ZÁÉÍÓÚÑ]+)'

        name_parts = []
        for pattern in [field_104_pattern, field_105_pattern, field_106_pattern, field_107_pattern]:
            match = re.search(pattern, text_after_reprs, re.IGNORECASE)
            if match:
                name_parts.append(match.group(1).strip())

        if len(name_parts) >= 2:
            full_name = ' '.join(name_parts)
            logger.info(f"Extracted legal representative name (field labels): {full_name}")
            return full_name

        # Strategy 5: Look for name on single line after field labels
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

        Structure in RUT can vary:
        Format 1 (space-separated):
            Cédula de Ciudadaní 1 3
            3  3  1  0  1  5  5  1

        Format 2 (newline-separated, GAMALOG):
            Cédula de Ciudadaní
            1 3
            ...
            7
            3
            0
            9
            4
            0
            9
            7

        The ID number needs to be extracted as the first column of digits when multiple reps exist.
        """
        logger.debug("Extracting legal representative ID (field 101)")

        # Find REPRS LEGAL PRIN section
        reprs_pattern = r'REPRS LEGAL PRIN'
        reprs_match = re.search(reprs_pattern, page_text, re.IGNORECASE)

        if not reprs_match:
            raise ValueError("Could not find REPRS LEGAL PRIN section")

        # Extract text after REPRS LEGAL PRIN (next 1500 chars to include ID section)
        text_after_reprs = page_text[reprs_match.end():reprs_match.end() + 1500]
        lines = text_after_reprs.split('\n')

        # Count number of representatives (for columnar format)
        num_reps = 1
        if 'REPRS LEGAL SUPL' in text_after_reprs:
            num_reps += 1
        if 'APOD. ESPECIAL' in text_after_reprs:
            num_reps += 1
        if 'APOD. GENERAL' in text_after_reprs:
            num_reps += 1

        # Strategy 1 (GAMALOG format): Look for newline-separated single digits after "Cédula"
        # The ID digits appear as single digits on separate lines
        # IDs for multiple reps appear sequentially (not interleaved), separated by empty lines
        id_type_match = re.search(r'C[eé]dula\s+de\s+Ciudadan[íi]?', text_after_reprs, re.IGNORECASE)
        if id_type_match:
            # Find the start of single-digit lines after the ID type
            text_after_id_type = text_after_reprs[id_type_match.end():]
            id_lines = text_after_id_type.split('\n')

            # Collect sequences of single digit lines (each sequence is one ID)
            # IDs appear as: [ID1 digits] [empty lines] [ID2 digits] [empty lines] [ID3 digits]
            current_sequence = []
            all_sequences = []

            for i, line in enumerate(id_lines):
                line_stripped = line.strip()
                # Skip lines that are field codes like "1 3" or dates like "2 0 1 6 1 0 2 0"
                if re.match(r'^\d\s+\d(\s+\d)*$', line_stripped) and len(line_stripped) > 2:
                    continue
                # Single digit line
                if line_stripped.isdigit() and len(line_stripped) == 1:
                    current_sequence.append(line_stripped)
                elif line_stripped == '' and current_sequence:
                    # Empty line after digits - sequence might be ending
                    # Check if we have a complete ID (7-10 digits)
                    if len(current_sequence) >= 7:
                        all_sequences.append(current_sequence)
                        current_sequence = []
                elif line_stripped != '' and current_sequence:
                    # Non-digit, non-empty line - sequence ended
                    if len(current_sequence) >= 7:
                        all_sequences.append(current_sequence)
                    current_sequence = []

            # Don't forget the last sequence if not saved
            if current_sequence and len(current_sequence) >= 7:
                all_sequences.append(current_sequence)

            # First sequence is the first legal rep's ID
            if all_sequences:
                first_rep_digits = all_sequences[0]
                cedula = ''.join(first_rep_digits[:10])  # Max 10 digits
                if 7 <= len(cedula) <= 10:
                    logger.info(f"Extracted legal representative ID (newline sequential format): {cedula}")
                    return cedula

        # Strategy 2: Look for ID type text, then find space-separated digits on next line
        id_type_pattern = r'C[eé]dula\s+de\s+Ciudadan[íi]a?[^\n]*\n[ \t]*(\d(?:[ \t]+\d){6,9})(?=[ \t]*\n)'
        id_type_match = re.search(id_type_pattern, text_after_reprs, re.IGNORECASE)

        if id_type_match:
            cedula = re.sub(r'[ \t]+', '', id_type_match.group(1))
            if 7 <= len(cedula) <= 10:
                logger.info(f"Extracted legal representative ID (after ID type): {cedula}")
                return cedula

        # Strategy 3: Look for field 101 label, skip to after 102/103, find space-separated digits
        field_101_pattern = r'101\.\s*Número de identificación[^\n]*\n[^\n]*\n[^\n]*\n\s*(\d(?:\s+\d){6,10})'
        field_101_match = re.search(field_101_pattern, text_after_reprs, re.IGNORECASE)

        if field_101_match:
            cedula = re.sub(r'\s+', '', field_101_match.group(1))
            if 7 <= len(cedula) <= 11:
                logger.info(f"Extracted legal representative ID (field 101 pattern): {cedula}")
                return cedula

        # Strategy 4: Find space-separated digit sequences after ID type
        if id_type_match:
            text_after_id_type = text_after_reprs[id_type_match.end():]

            space_digits_pattern = r'^\s*(\d(?:\s+\d){6,10})\s*$'
            for line in text_after_id_type.split('\n')[:5]:
                line_match = re.match(space_digits_pattern, line)
                if line_match:
                    cedula = re.sub(r'\s+', '', line_match.group(1))
                    if 7 <= len(cedula) <= 11:
                        logger.info(f"Extracted legal representative ID (line after ID type): {cedula}")
                        return cedula

        # Strategy 5: Look for 7-10 space-separated digit sequences in lines
        for i, line in enumerate(lines):
            if re.match(r'^\s*\d\s+\d\s*\n', line):
                continue
            line_pattern = r'^\s*(\d(?:\s+\d){6,9})\s*$'
            line_match = re.match(line_pattern, line)
            if line_match:
                cedula = re.sub(r'\s+', '', line_match.group(1))
                if 7 <= len(cedula) <= 10:
                    if i > 2:
                        logger.info(f"Extracted legal representative ID (line scan): {cedula}")
                        return cedula

        # Log the text we're searching for debugging
        logger.debug(f"Text after REPRS LEGAL PRIN (first 500 chars): {text_after_reprs[:500]}")
        raise ValueError("Could not extract legal representative ID (field 101)")

    def _extract_legal_rep_id_type(self, page, page_text: str) -> str:
        """
        Extract legal representative ID type from field 100 (Tipo de documento)

        Returns abbreviated form: CC, CE, Pasaporte, etc.

        Structure in RUT:
        100. Tipo de documento
        101. Número de identificación
        102. DV 103. Número de tarjeta profesional
        Cédula de Ciudadaní 1 3

        The value for field 100 is on the line after fields 102/103
        """
        logger.debug("Extracting legal representative ID type (field 100)")

        # ID type mapping from full names to abbreviations
        ID_TYPE_MAPPING = {
            'Cédula de Ciudadanía': 'CC',
            'Cedula de Ciudadania': 'CC',
            'Cédula de Extranjería': 'CE',
            'Cedula de Extranjeria': 'CE',
            'Pasaporte': 'Pasaporte',
            'Tarjeta de Identidad': 'TI',
            'Registro Civil': 'RC',
            'NIT': 'NIT',
        }

        # Find REPRS LEGAL PRIN section
        reprs_pattern = r'REPRS LEGAL PRIN'
        reprs_match = re.search(reprs_pattern, page_text, re.IGNORECASE)

        if not reprs_match:
            raise ValueError("Could not find REPRS LEGAL PRIN section")

        # Extract text after REPRS LEGAL PRIN (next 1000 chars should be enough)
        text_after_reprs = page_text[reprs_match.end():reprs_match.end() + 1000]

        # Strategy 1: Look for field 100, skip to the line after 102/103, extract ID type text
        # Pattern: Find "100. Tipo de documento", skip past 101 and 102/103 lines, capture text (not numbers)
        type_pattern = r'100\.\s*Tipo de documento[^\n]*\n[^\n]*\n[^\n]*\n\s*([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)(?:\s+\d|\n|$)'
        type_match = re.search(type_pattern, text_after_reprs, re.IGNORECASE)

        if type_match:
            id_type_text = type_match.group(1).strip()
            # Remove any trailing numbers or whitespace
            id_type_text = re.sub(r'\s+\d.*$', '', id_type_text).strip()

            # Try to map to abbreviation (use fuzzy matching for encoding issues)
            for full_name, abbrev in ID_TYPE_MAPPING.items():
                # Normalize both strings for comparison (handle encoding issues)
                normalized_full = full_name.lower().replace('í', 'i').replace('é', 'e')
                normalized_text = id_type_text.lower().replace('í', 'i').replace('é', 'e')

                if normalized_full in normalized_text or normalized_text in normalized_full:
                    logger.info(f"Extracted legal representative ID type: {abbrev} (from: {id_type_text})")
                    return abbrev

            # If no mapping found but we have valid text, return it
            if id_type_text and len(id_type_text) > 3:
                logger.info(f"Extracted legal representative ID type (unmapped): {id_type_text}")
                return id_type_text

        # Strategy 2: Look for common ID type keywords directly (with normalization)
        for full_name, abbrev in ID_TYPE_MAPPING.items():
            normalized_full = full_name.lower().replace('í', 'i').replace('é', 'e')
            normalized_text = text_after_reprs.lower().replace('í', 'i').replace('é', 'e')
            if normalized_full in normalized_text:
                logger.info(f"Extracted legal representative ID type (keyword): {abbrev}")
                return abbrev

        # Strategy 3: Look for "Cédula" or "Cedula" pattern (most common)
        cedula_search = re.search(r'(C[eé]dula\s+de\s+Ciudadan[íi]a?)', text_after_reprs, re.IGNORECASE)
        if cedula_search:
            logger.info(f"Extracted legal representative ID type (pattern): CC (from: {cedula_search.group(1)})")
            return 'CC'

        # Default to CC (most common in Colombia)
        logger.warning("Could not extract ID type, defaulting to CC")
        return 'CC'
