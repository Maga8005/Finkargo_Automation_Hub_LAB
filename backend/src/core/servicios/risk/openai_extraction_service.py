"""
OpenAI Extraction Service - AI-powered entity extraction from email text

Uses OpenAI GPT-4o with structured JSON output to intelligently extract:
- Company names (Colombian business entities)
- NITs (Colombian tax IDs)
- Representative names (legal representatives, managers, directors)
- Email domains (corporate domains)
"""
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

# Maximum text length to send to OpenAI (roughly 15000 chars ~ 3750 tokens)
MAX_TEXT_LENGTH = 15000

# Prompt template for entity extraction
EXTRACTION_PROMPT = """Eres un asistente especializado en extraer información de negocios de correspondencia empresarial colombiana.

Analiza el siguiente texto de correo electrónico y extrae las siguientes entidades:

1. **company_names**: Nombres de empresas colombianas mencionadas. Incluye el sufijo legal (S.A.S., LTDA, S.A., etc.) si está presente. NO incluyas referencias genéricas como "la empresa", "nuestra compañía", etc.

2. **nits**: NITs colombianos (números de identificación tributaria). Formato: XXXXXXXXX-X o XXX.XXX.XXX-X. Devuelve en formato normalizado sin puntos ni espacios (ejemplo: 8300272313).

3. **representative_names**: Nombres de personas que son representantes legales, gerentes, directores, apoderados, presidentes o CEO. Solo incluye nombres de personas específicas, no títulos genéricos.

4. **domains**: Dominios de correo electrónico corporativos mencionados (ejemplo: "empresa.com.co"). NO incluyas dominios de proveedores gratuitos como gmail.com, hotmail.com, yahoo.com, outlook.com.

IMPORTANTE:
- Solo incluye entidades que estén claramente mencionadas en el texto
- NO inventes información que no esté presente
- Si no hay entidades de un tipo, devuelve un array vacío
- Los NITs deben ser números válidos de 9-10 dígitos + dígito de verificación
- Filtra números de celular colombianos (10 dígitos que empiezan con 3) de los NITs

Responde SOLO con un objeto JSON válido en este formato exacto:
{
    "company_names": ["nombre1", "nombre2"],
    "nits": ["1234567890", "9876543210"],
    "representative_names": ["Juan Pérez", "María García"],
    "domains": ["empresa.com.co", "cliente.co"]
}"""


class OpenAIExtractionService:
    """
    Service for AI-powered entity extraction from email text using OpenAI GPT-4o.

    Provides structured extraction of:
    - Company names
    - NITs (Colombian tax IDs)
    - Representative names
    - Corporate email domains
    """

    def __init__(self):
        """Initialize the OpenAI extraction service."""
        from src.config.settings import get_settings

        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        """
        Lazy initialization of OpenAI client.

        Returns:
            OpenAI client instance or None if not available
        """
        if self._client is not None:
            return self._client

        if not self.settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            return None

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.settings.OPENAI_API_KEY,
                timeout=self.settings.OPENAI_TIMEOUT
            )
            return self._client
        except ImportError:
            logger.error("openai package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None

    def is_available(self) -> bool:
        """
        Check if the OpenAI extraction service is available.

        Returns:
            bool: True if OpenAI API key is configured and client can be initialized
        """
        return self._get_client() is not None

    def extract_entities(self, email_text: str) -> Optional[dict]:
        """
        Extract entities from email text using OpenAI GPT-4o.

        Args:
            email_text: Raw email text content

        Returns:
            Optional[dict]: Extracted entities with structure:
                {
                    'company_names': List[str],
                    'nits': List[str],
                    'representative_names': List[str],
                    'domains': List[str]
                }
            Returns None if extraction fails
        """
        client = self._get_client()
        if client is None:
            logger.warning("OpenAI client not available")
            return None

        if not email_text or not email_text.strip():
            logger.debug("Empty email text provided")
            return {
                'company_names': [],
                'nits': [],
                'representative_names': [],
                'domains': []
            }

        # Truncate text if too long
        truncated_text = email_text[:MAX_TEXT_LENGTH]
        if len(email_text) > MAX_TEXT_LENGTH:
            logger.info(
                f"Truncated email text from {len(email_text)} to {MAX_TEXT_LENGTH} chars"
            )

        try:
            logger.info("Calling OpenAI for entity extraction")

            response = client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": truncated_text}
                ],
                max_tokens=self.settings.OPENAI_MAX_TOKENS,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            # Extract content from response
            content = response.choices[0].message.content

            if not content:
                logger.warning("Empty response from OpenAI")
                return None

            # Parse JSON response
            result = json.loads(content)

            # Validate structure
            validated = self._validate_response(result)

            logger.info(
                f"Extracted entities: {len(validated['company_names'])} companies, "
                f"{len(validated['nits'])} NITs, "
                f"{len(validated['representative_names'])} representatives, "
                f"{len(validated['domains'])} domains"
            )

            return validated

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}", exc_info=True)
            return None

    def _validate_response(self, response: dict) -> dict:
        """
        Validate and normalize the OpenAI response.

        Args:
            response: Raw response from OpenAI

        Returns:
            dict: Validated response with all expected fields
        """
        validated = {
            'company_names': [],
            'nits': [],
            'representative_names': [],
            'domains': []
        }

        # Validate company_names
        if isinstance(response.get('company_names'), list):
            validated['company_names'] = [
                str(name).strip()
                for name in response['company_names']
                if name and str(name).strip()
            ]

        # Validate and normalize NITs
        if isinstance(response.get('nits'), list):
            for nit in response['nits']:
                if nit:
                    # Normalize: remove dots, spaces, keep only digits and dash
                    normalized = str(nit).replace('.', '').replace(' ', '').strip()
                    # Remove trailing dash if present without verification digit
                    if normalized.endswith('-'):
                        normalized = normalized[:-1]
                    # Filter out obviously invalid NITs
                    if len(normalized.replace('-', '')) >= 9:
                        validated['nits'].append(normalized)

        # Validate representative_names
        if isinstance(response.get('representative_names'), list):
            validated['representative_names'] = [
                str(name).strip()
                for name in response['representative_names']
                if name and len(str(name).strip()) > 2
            ]

        # Validate domains
        if isinstance(response.get('domains'), list):
            validated['domains'] = [
                str(domain).lower().strip()
                for domain in response['domains']
                if domain and '.' in str(domain)
            ]

        return validated
