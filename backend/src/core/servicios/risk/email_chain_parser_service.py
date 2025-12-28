"""
Email Chain Parser Service - Parse email files and text to extract structured data

Supports:
- .eml files (RFC 5322 format)
- .msg files (Outlook format) - requires extract-msg library
- .pdf files (exported email correspondence) - requires PyMuPDF
- Raw text email content (copy-paste from email client)

Extraction Modes:
- AI extraction (OpenAI GPT-4o) - enabled via database setting
- Regex extraction - fallback or default mode
"""
import re
import logging
from email import policy
from email.parser import BytesParser, Parser
from email.utils import parseaddr, parsedate_to_datetime
from typing import List, Optional

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class EmailChainParserService:
    """
    Service for parsing email chains and extracting structured data.

    Extracts:
    - Sender information (email, name, domain)
    - Email headers (date, subject)
    - Body content analysis (company names, NITs, representative names)

    Supports two extraction modes:
    - AI extraction (OpenAI GPT-4o) - more accurate, handles varied formats
    - Regex extraction - fallback mode, uses pattern matching
    """

    def __init__(self, use_ai_extraction: bool = False):
        """
        Initialize the email chain parser service.

        Args:
            use_ai_extraction: If True, use OpenAI for entity extraction.
                               Falls back to regex if OpenAI fails.
        """
        self.use_ai_extraction = use_ai_extraction
        self._openai_service: Optional['OpenAIExtractionService'] = None

        if use_ai_extraction:
            try:
                from src.core.servicios.risk.openai_extraction_service import (
                    OpenAIExtractionService
                )
                self._openai_service = OpenAIExtractionService()
                if not self._openai_service.is_available():
                    logger.warning(
                        "OpenAI service not available, will use regex extraction"
                    )
                    self._openai_service = None
            except ImportError as e:
                logger.error(f"Failed to import OpenAI service: {e}")
                self._openai_service = None

    # Common Spanish keywords that precede representative names
    REP_KEYWORDS = [
        r'representante\s+legal',
        r'rep\.?\s*legal',
        r'gerente',
        r'gerente\s+general',
        r'director',
        r'director\s+general',
        r'apoderado',
        r'presidente',
        r'ceo',
    ]

    # Colombian NIT pattern: XXX.XXX.XXX-X or XXXXXXXXX-X or XXX-XXX-XXX-X
    NIT_PATTERN = r'\b(\d{3}\.?\d{3}\.?\d{3}[-\s]?\d|\d{9}[-\s]?\d)\b'

    # Colombian cellphone pattern: 10 digits starting with 3 (mobile prefixes 30x, 31x, 32x, 35x, 36x)
    # May have country code prefix: +57 or 57
    COLOMBIAN_CELLPHONE_PATTERN = r'(?:\+?57\s*)?(?:3[0-26-9]\d{8})\b'

    # Free email provider domains
    FREE_PROVIDERS = {
        'gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com',
        'yahoo.es', 'live.com', 'msn.com', 'icloud.com',
        'aol.com', 'protonmail.com', 'mail.com', 'zoho.com',
        'hotmail.es', 'outlook.es', 'gmail.co',
    }

    def parse_eml_file(self, file_content: bytes) -> dict:
        """
        Parse an .eml file and extract email data.

        Args:
            file_content: Raw bytes of the .eml file

        Returns:
            dict: Parsed email data with messages and mentions
        """
        logger.info("Parsing .eml file content")

        try:
            msg = BytesParser(policy=policy.default).parsebytes(file_content)
            return self._parse_email_message(msg)
        except Exception as e:
            logger.error(f"Error parsing .eml file: {e}", exc_info=True)
            return {
                'messages': [],
                'mentions': {
                    'company_names': [],
                    'nits': [],
                    'representative_names': [],
                    'domains': [],
                },
                'parse_errors': [f"Error al parsear archivo .eml: {str(e)}"],
            }

    def parse_msg_file(self, file_content: bytes) -> dict:
        """
        Parse an Outlook .msg file and extract email data.

        Args:
            file_content: Raw bytes of the .msg file

        Returns:
            dict: Parsed email data with messages and mentions
        """
        logger.info("Parsing .msg file content")

        try:
            # Try to import extract-msg
            try:
                import extract_msg
            except ImportError:
                logger.warning("extract-msg not installed, attempting basic parsing")
                return {
                    'messages': [],
                    'mentions': {
                        'company_names': [],
                        'nits': [],
                        'representative_names': [],
                        'domains': [],
                    },
                    'parse_errors': [
                        "La librería extract-msg no está instalada. "
                        "Por favor use formato .eml o pegue el texto del email."
                    ],
                }

            # Parse MSG file
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(delete=False, suffix='.msg') as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name

            try:
                msg = extract_msg.Message(tmp_path)

                # Extract sender info
                sender_email = msg.sender or ''
                sender_name = ''
                if '<' in sender_email:
                    sender_name, sender_email = parseaddr(sender_email)

                sender_domain = self._extract_domain(sender_email)

                # Extract body
                body = msg.body or ''
                body_excerpt = body[:2000] if body else ''

                # Build message dict
                message = {
                    'sender_email': sender_email.lower().strip() if sender_email else '',
                    'sender_name': sender_name.strip() if sender_name else None,
                    'sender_domain': sender_domain,
                    'date': msg.date.isoformat() if msg.date else None,
                    'subject': msg.subject,
                    'body_excerpt': body_excerpt,
                }

                msg.close()

                # Extract mentions from body
                mentions = self._extract_mentions_from_body(body)
                mentions['domains'].append(sender_domain) if sender_domain else None
                mentions['domains'] = list(set(mentions['domains']))

                return {
                    'messages': [message],
                    'mentions': mentions,
                    'parse_errors': [],
                }

            finally:
                os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Error parsing .msg file: {e}", exc_info=True)
            return {
                'messages': [],
                'mentions': {
                    'company_names': [],
                    'nits': [],
                    'representative_names': [],
                    'domains': [],
                },
                'parse_errors': [f"Error al parsear archivo .msg: {str(e)}"],
            }

    def parse_pdf_file(self, file_content: bytes) -> dict:
        """
        Parse a PDF file containing email correspondence and extract email data.

        Extracts text from all pages and passes it to parse_raw_text() for
        email pattern detection.

        Args:
            file_content: Raw bytes of the PDF file

        Returns:
            dict: Parsed email data with messages and mentions
        """
        logger.info("Parsing PDF file content")

        try:
            # Open PDF from bytes
            doc = fitz.open(stream=file_content, filetype="pdf")

            # Check if PDF is encrypted/password-protected
            if doc.is_encrypted:
                doc.close()
                return {
                    'messages': [],
                    'mentions': {
                        'company_names': [],
                        'nits': [],
                        'representative_names': [],
                        'domains': [],
                    },
                    'parse_errors': [
                        "El archivo PDF está protegido con contraseña. "
                        "Por favor proporcione un archivo sin protección."
                    ],
                }

            # Extract text from all pages
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)

            doc.close()

            # Check if any text was extracted
            full_text = '\n\n'.join(text_parts)
            if not full_text.strip():
                return {
                    'messages': [],
                    'mentions': {
                        'company_names': [],
                        'nits': [],
                        'representative_names': [],
                        'domains': [],
                    },
                    'parse_errors': [
                        "No se pudo extraer texto del archivo PDF. "
                        "El PDF puede contener solo imágenes (escaneos) "
                        "que no son compatibles con la extracción de texto."
                    ],
                }

            logger.info(f"Extracted {len(full_text)} characters from PDF")

            # Use the existing raw text parser for email pattern detection
            return self.parse_raw_text(full_text)

        except fitz.FileDataError:
            logger.error("Invalid PDF file format")
            return {
                'messages': [],
                'mentions': {
                    'company_names': [],
                    'nits': [],
                    'representative_names': [],
                    'domains': [],
                },
                'parse_errors': [
                    "El archivo PDF está corrupto o tiene un formato inválido."
                ],
            }
        except Exception as e:
            logger.error(f"Error parsing PDF file: {e}", exc_info=True)
            return {
                'messages': [],
                'mentions': {
                    'company_names': [],
                    'nits': [],
                    'representative_names': [],
                    'domains': [],
                },
                'parse_errors': [f"Error al parsear archivo PDF: {str(e)}"],
            }

    def parse_raw_text(self, text: str) -> dict:
        """
        Parse raw email text (copy-pasted from email client).

        Handles various formats:
        - Standard RFC 5322 headers
        - Outlook/Gmail forwarded email format
        - Simple header + body format

        Args:
            text: Raw email text content

        Returns:
            dict: Parsed email data with messages and mentions
        """
        logger.info("Parsing raw email text")

        if not text or not text.strip():
            return {
                'messages': [],
                'mentions': {
                    'company_names': [],
                    'nits': [],
                    'representative_names': [],
                    'domains': [],
                },
                'parse_errors': ['No se proporcionó contenido de email'],
            }

        try:
            # First, try parsing as standard RFC 5322 email
            try:
                msg = Parser(policy=policy.default).parsestr(text)
                if msg.get('From'):
                    return self._parse_email_message(msg)
            except Exception:
                pass

            # If that fails, try to extract headers manually
            messages = []
            errors = []
            all_bodies = []

            # Split by common email chain separators
            email_parts = self._split_email_chain(text)

            for part in email_parts:
                message = self._extract_headers_from_text(part)
                if message.get('sender_email'):
                    messages.append(message)
                    if message.get('body_excerpt'):
                        all_bodies.append(message['body_excerpt'])

            # If no messages found, try to find at least an email address
            if not messages:
                # Look for any email pattern
                email_match = re.search(r'[\w.+-]+@[\w.-]+\.\w+', text)
                if email_match:
                    email_addr = email_match.group().lower()
                    domain = self._extract_domain(email_addr)
                    messages.append({
                        'sender_email': email_addr,
                        'sender_name': None,
                        'sender_domain': domain,
                        'date': None,
                        'subject': None,
                        'body_excerpt': text[:2000],
                    })
                    all_bodies.append(text)
                else:
                    errors.append('No se encontró dirección de email en el texto')
                    all_bodies.append(text)

            # Extract mentions from all body content
            full_body = '\n'.join(all_bodies)
            mentions = self._extract_mentions_from_body(full_body)

            # Add sender domains to mentions
            for msg in messages:
                if msg.get('sender_domain'):
                    mentions['domains'].append(msg['sender_domain'])
            mentions['domains'] = list(set(mentions['domains']))

            return {
                'messages': messages,
                'mentions': mentions,
                'parse_errors': errors,
            }

        except Exception as e:
            logger.error(f"Error parsing raw text: {e}", exc_info=True)
            return {
                'messages': [],
                'mentions': {
                    'company_names': [],
                    'nits': [],
                    'representative_names': [],
                    'domains': [],
                },
                'parse_errors': [f"Error al parsear texto: {str(e)}"],
            }

    def _parse_email_message(self, msg) -> dict:
        """
        Parse a standard email.message.Message object.

        Args:
            msg: email.message.Message object

        Returns:
            dict: Parsed email data
        """
        messages = []
        all_bodies = []
        errors = []

        # Get sender info
        from_header = msg.get('From', '')
        sender_name, sender_email = parseaddr(from_header)
        sender_domain = self._extract_domain(sender_email)

        # Get date
        date_header = msg.get('Date')
        date_str = None
        if date_header:
            try:
                date_obj = parsedate_to_datetime(date_header)
                date_str = date_obj.isoformat()
            except Exception:
                pass

        # Get subject
        subject = msg.get('Subject', '')

        # Get body
        body = self._get_email_body(msg)
        body_excerpt = body[:2000] if body else ''
        all_bodies.append(body)

        message = {
            'sender_email': sender_email.lower().strip() if sender_email else '',
            'sender_name': sender_name.strip() if sender_name else None,
            'sender_domain': sender_domain,
            'date': date_str,
            'subject': subject,
            'body_excerpt': body_excerpt,
        }
        messages.append(message)

        # Extract mentions from body
        mentions = self._extract_mentions_from_body(body)
        if sender_domain:
            mentions['domains'].append(sender_domain)
        mentions['domains'] = list(set(mentions['domains']))

        return {
            'messages': messages,
            'mentions': mentions,
            'parse_errors': errors,
        }

    def _get_email_body(self, msg) -> str:
        """
        Extract body text from email message.

        Args:
            msg: email.message.Message object

        Returns:
            str: Email body text
        """
        body = ''

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body = payload.decode(charset, errors='replace')
                            break
                        except Exception:
                            body = payload.decode('utf-8', errors='replace')
                            break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    body = payload.decode(charset, errors='replace')
                except Exception:
                    body = payload.decode('utf-8', errors='replace')

        return body

    def _split_email_chain(self, text: str) -> List[str]:
        """
        Split email chain text into individual emails.

        Args:
            text: Full email chain text

        Returns:
            List[str]: Individual email parts
        """
        # Common email chain separators
        separators = [
            r'-{3,}.*?Original Message.*?-{3,}',
            r'_{3,}',
            r'De:.*?\nPara:',
            r'From:.*?\nTo:',
            r'El \d{1,2}/\d{1,2}/\d{2,4}.*?escribió:',
            r'On \d{1,2}/\d{1,2}/\d{2,4}.*?wrote:',
            r'Enviado:.*?\n',
            r'Sent:.*?\n',
        ]

        # Try each separator
        for sep in separators:
            parts = re.split(sep, text, flags=re.IGNORECASE | re.DOTALL)
            if len(parts) > 1:
                return [p.strip() for p in parts if p.strip()]

        # No separator found, return as single email
        return [text.strip()]

    def _extract_headers_from_text(self, text: str) -> dict:
        """
        Extract email headers from text.

        Args:
            text: Email text content

        Returns:
            dict: Extracted header data
        """
        message = {
            'sender_email': '',
            'sender_name': None,
            'sender_domain': '',
            'date': None,
            'subject': None,
            'body_excerpt': '',
        }

        # Try to find From header
        from_patterns = [
            r'From:\s*([^\n]+)',
            r'De:\s*([^\n]+)',
            r'Remitente:\s*([^\n]+)',
        ]

        for pattern in from_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                from_value = match.group(1).strip()
                name, email_addr = parseaddr(from_value)
                if not email_addr:
                    # Try to extract email from the value
                    email_match = re.search(r'[\w.+-]+@[\w.-]+\.\w+', from_value)
                    if email_match:
                        email_addr = email_match.group()
                        name = from_value.replace(email_addr, '').strip(' <>')

                message['sender_email'] = email_addr.lower().strip() if email_addr else ''
                message['sender_name'] = name.strip() if name else None
                message['sender_domain'] = self._extract_domain(email_addr)
                break

        # Try to find Date header
        date_patterns = [
            r'Date:\s*([^\n]+)',
            r'Fecha:\s*([^\n]+)',
            r'Enviado:\s*([^\n]+)',
            r'Sent:\s*([^\n]+)',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_value = match.group(1).strip()
                try:
                    # Try parsing common formats
                    date_obj = parsedate_to_datetime(date_value)
                    message['date'] = date_obj.isoformat()
                except Exception:
                    # Just store the raw value
                    message['date'] = date_value
                break

        # Try to find Subject header
        subject_patterns = [
            r'Subject:\s*([^\n]+)',
            r'Asunto:\s*([^\n]+)',
        ]

        for pattern in subject_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                message['subject'] = match.group(1).strip()
                break

        # Extract body (everything after headers)
        # Find where body starts (after blank line or first non-header content)
        header_end = 0
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if not line.strip():
                header_end = i + 1
                break
            # Check if line doesn't look like a header
            if not re.match(r'^[A-Za-z-]+:\s', line):
                header_end = i
                break

        body = '\n'.join(lines[header_end:]).strip()
        message['body_excerpt'] = body[:2000]

        return message

    def _extract_domain(self, email_addr: str) -> str:
        """
        Extract domain from email address.

        Args:
            email_addr: Email address

        Returns:
            str: Domain or empty string
        """
        if not email_addr or '@' not in email_addr:
            return ''
        try:
            return email_addr.split('@')[1].lower().strip()
        except (IndexError, AttributeError):
            return ''

    def _extract_mentions_from_body(self, body: str) -> dict:
        """
        Extract company names, NITs, and representative names from email body.

        Uses AI extraction if enabled and available, falls back to regex otherwise.

        Args:
            body: Email body text

        Returns:
            dict: Extracted mentions with extraction_method field
        """
        if not body:
            return {
                'company_names': [],
                'nits': [],
                'representative_names': [],
                'domains': [],
                'extraction_method': 'regex',
            }

        # Try AI extraction if enabled
        if self.use_ai_extraction and self._openai_service is not None:
            mentions = self._extract_mentions_with_ai(body)
            if mentions is not None:
                return mentions
            # AI extraction failed, fall back to regex
            logger.info("AI extraction failed, falling back to regex")
            mentions = self._extract_mentions_with_regex(body)
            mentions['extraction_method'] = 'regex_fallback'
            return mentions

        # Use regex extraction
        return self._extract_mentions_with_regex(body)

    def _extract_mentions_with_ai(self, body: str) -> Optional[dict]:
        """
        Extract mentions using OpenAI GPT-4o.

        Args:
            body: Email body text

        Returns:
            Optional[dict]: Extracted mentions or None if extraction fails
        """
        if self._openai_service is None:
            return None

        try:
            import asyncio

            # Run the async extraction
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self._openai_service.extract_entities(body)
                )
            finally:
                loop.close()

            if result is None:
                return None

            # Add extraction method
            result['extraction_method'] = 'ai'

            logger.info(
                f"AI extraction successful: {len(result.get('company_names', []))} companies, "
                f"{len(result.get('nits', []))} NITs"
            )

            return result

        except Exception as e:
            logger.error(f"AI extraction error: {e}", exc_info=True)
            return None

    def _extract_mentions_with_regex(self, body: str) -> dict:
        """
        Extract mentions using regex patterns.

        Args:
            body: Email body text

        Returns:
            dict: Extracted mentions
        """
        mentions = {
            'company_names': [],
            'nits': [],
            'representative_names': [],
            'domains': [],
            'extraction_method': 'regex',
        }

        if not body:
            return mentions

        # Extract NITs
        nit_matches = re.findall(self.NIT_PATTERN, body)
        for nit in nit_matches:
            # Normalize NIT format (remove dots and spaces)
            normalized = re.sub(r'[.\s]', '', nit)

            # Filter out Colombian cellphone numbers (10 digits starting with 3)
            # Cellphones look like NITs but have distinct patterns
            if self.is_colombian_cellphone(normalized):
                logger.debug(f"Filtered cellphone number from NIT matches: {normalized}")
                continue

            if normalized not in mentions['nits']:
                mentions['nits'].append(normalized)

        # Extract representative names
        for keyword in self.REP_KEYWORDS:
            pattern = rf'{keyword}[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)'
            matches = re.findall(pattern, body, re.IGNORECASE)
            for name in matches:
                name = name.strip()
                if len(name) > 3 and name not in mentions['representative_names']:
                    mentions['representative_names'].append(name)

        # Extract email domains from body
        email_matches = re.findall(r'[\w.+-]+@([\w.-]+\.\w+)', body, re.IGNORECASE)
        for domain in email_matches:
            domain = domain.lower()
            if domain not in mentions['domains'] and domain not in self.FREE_PROVIDERS:
                mentions['domains'].append(domain)

        # Extract potential company names (capitalized multi-word phrases)
        # Look for patterns like "de EMPRESA S.A.S" or "empresa AZELIS COLOMBIA"
        company_patterns = [
            r'\b([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s&]+(?:S\.?A\.?S\.?|S\.?A\.?|LTDA\.?|S\.?A\.?S|CORP\.?|INC\.?))\b',
            r'empresa[:\s]+([A-Za-záéíóúñÁÉÍÓÚÑ\s&]+)',
            r'compañía[:\s]+([A-Za-záéíóúñÁÉÍÓÚÑ\s&]+)',
        ]

        for pattern in company_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for name in matches:
                name = name.strip()
                if len(name) > 3 and name not in mentions['company_names']:
                    mentions['company_names'].append(name)

        return mentions

    def is_free_email_provider(self, domain: str) -> bool:
        """
        Check if domain is a free email provider.

        Args:
            domain: Email domain

        Returns:
            bool: True if free email provider
        """
        return domain.lower() in self.FREE_PROVIDERS

    def is_colombian_cellphone(self, number: str) -> bool:
        """
        Check if a number string is a Colombian cellphone number.

        Colombian cellphones:
        - 10 digits total
        - Start with 3 followed by 0, 1, 2, 5, or 6 (mobile prefixes)
        - May have +57 or 57 country code prefix

        Args:
            number: Normalized number string (digits only)

        Returns:
            bool: True if matches Colombian cellphone pattern
        """
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d]', '', number)

        # Check for country code prefix and remove it
        if digits_only.startswith('57') and len(digits_only) == 12:
            digits_only = digits_only[2:]

        # Must be exactly 10 digits
        if len(digits_only) != 10:
            return False

        # Must start with 3 followed by mobile prefix (0, 1, 2, 5, 6)
        # Mobile prefixes: 300-309, 310-319, 320-329, 350-359, 360-369
        if digits_only[0] == '3' and digits_only[1] in '01256':
            return True

        return False
