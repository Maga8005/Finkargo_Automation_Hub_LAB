"""
LandingAI Contract Parser Service - Extracts broker contract data using AI.

This service uses LandingAI's ADE (Agentic Document Extraction) API to extract structured data
from broker contracts, including scanned/image-based PDFs that cannot be processed with text extraction.
"""
import httpx
import json
import logging
from typing import Optional

from src.config.settings import get_settings
from src.interface.alianzas_dtos import BrokerContractData, ExtractionMethod

logger = logging.getLogger(__name__)


# Broker Contract Extraction Schema for LandingAI ADE Extract API
BROKER_CONTRACT_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "nombre_broker": {
            "type": "string",
            "description": "Nombre o razón social del broker/aliado comercial que aparece en el contrato"
        },
        "porcentaje_comision_apertura": {
            "type": "number",
            "description": (
                "Porcentaje de la comisión de apertura que corresponde al broker "
                "(ej: 60 para 60%, 80 para 80%). Buscar frases como 'Bono equivalente al X%' "
                "o 'X% de la comisión de apertura'"
            )
        },
        "porcentaje_comision_operativa": {
            "type": "number",
            "description": (
                "Porcentaje sobre operaciones/desembolsos mensuales "
                "(ej: 0.10 para 0.10%, 0.15 para 0.15%). "
                "Buscar frases como 'comisión operativa' o 'por cada desembolso'"
            )
        },
        "fecha_contrato": {
            "type": "string",
            "description": "Fecha de firma del contrato en formato DD/MM/YYYY"
        },
        "vigencia_meses": {
            "type": "integer",
            "description": "Vigencia del contrato en meses (ej: 12, 24)"
        },
        "rfc_broker": {
            "type": "string",
            "description": "RFC del broker para facturación (formato: XXXX######XXX)"
        },
        "cuenta_bancaria": {
            "type": "string",
            "description": "Número de cuenta CLABE para depósitos (18 dígitos)"
        },
        "banco": {
            "type": "string",
            "description": "Nombre de la institución bancaria"
        }
    },
    "required": [
        "porcentaje_comision_apertura",
        "porcentaje_comision_operativa"
    ]
}


class LandingAIContractParserService:
    """
    Service for parsing broker contracts using LandingAI's ADE (Agentic Document Extraction) API.

    This service is intended for scanned/image-based PDFs where text extraction fails.
    Processing takes 30-60 seconds per document.
    """

    def __init__(self) -> None:
        """Initialize LandingAI contract parser service with API configuration."""
        settings = get_settings()
        self.api_key = settings.LANDINGAI_API_KEY
        self.parse_endpoint = settings.LANDINGAI_PARSE_ENDPOINT
        self.extract_endpoint = settings.LANDINGAI_EXTRACT_ENDPOINT
        self.timeout = 120  # 2 minutes timeout for API calls

        if not self.api_key:
            logger.warning(
                "LANDINGAI_API_KEY is not configured. AI contract extraction will not work."
            )

    def parse_contract_pdf(self, pdf_bytes: bytes) -> BrokerContractData:
        """
        Parse broker contract PDF and extract data using LandingAI ADE API.

        Args:
            pdf_bytes: Contract PDF file content as bytes

        Returns:
            BrokerContractData: Extracted contract information

        Raises:
            ValueError: If API key is not configured, API call fails, or extraction fails
        """
        if not self.api_key:
            raise ValueError(
                "LANDINGAI_API_KEY is not configured. "
                "Please set the environment variable to use AI extraction."
            )

        logger.info("Starting LandingAI contract extraction (AI-powered)")

        try:
            # Step 1: Parse document to markdown using ADE Parse API
            markdown = self._call_parse_api(pdf_bytes)
            logger.info(f"ADE Parse completed - {len(markdown)} characters of markdown")

            # Step 2: Extract structured data using ADE Extract API
            extraction, is_partial = self._call_extract_api(markdown)
            logger.info(
                f"ADE Extract completed - {len(extraction)} fields extracted "
                f"(partial: {is_partial})"
            )

            # Step 3: Calculate confidence based on fields found
            confidence = self._calculate_confidence(extraction, is_partial)
            logger.info(f"Extraction confidence: {confidence:.2f}")

            # Step 4: Map to BrokerContractData model
            contract_data = self._map_to_contract_data(extraction, markdown, confidence)
            logger.info(
                f"LandingAI contract extraction completed. "
                f"Broker: {contract_data.nombre_broker or 'N/A'}"
            )

            return contract_data

        except httpx.TimeoutException:
            logger.error("LandingAI API timeout (exceeded 120 seconds)")
            raise ValueError(
                "La extracción IA está tomando demasiado tiempo. "
                "El documento está tardando mucho en procesarse. "
                "Por favor intente de nuevo."
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"LandingAI API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            if e.response.status_code == 401:
                raise ValueError(
                    "API key de IA no válida. Contacte al administrador."
                )
            elif e.response.status_code == 429:
                raise ValueError(
                    "Límite de peticiones de IA excedido. Intente en unos minutos."
                )
            else:
                raise ValueError(
                    f"Error de API LandingAI ({e.response.status_code}): {e.response.text}"
                )
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during LandingAI contract extraction: {e}",
                exc_info=True
            )
            raise ValueError(f"Error en extracción IA: {str(e)}")

    def _call_parse_api(self, pdf_bytes: bytes) -> str:
        """
        Call LandingAI ADE Parse API to convert PDF to markdown.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            str: Markdown representation of the document

        Raises:
            httpx.HTTPStatusError: If API call fails
            ValueError: If empty markdown returned
        """
        logger.debug(f"Calling ADE Parse API: {self.parse_endpoint}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        files = {
            "document": ("contract_document.pdf", pdf_bytes, "application/pdf")
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self.parse_endpoint,
                headers=headers,
                files=files
            )
            response.raise_for_status()

        result = response.json()
        markdown = result.get("markdown", "")

        if not markdown:
            raise ValueError(
                "El documento no contiene texto extraíble. "
                "Verifique que sea un PDF válido."
            )

        logger.debug(f"ADE Parse API returned {len(result.get('chunks', []))} chunks")
        return markdown

    def _call_extract_api(self, markdown: str) -> tuple[dict, bool]:
        """
        Call LandingAI ADE Extract API to extract structured data from markdown.

        Args:
            markdown: Document content in markdown format

        Returns:
            tuple[dict, bool]: Extracted data and whether it was a partial success (HTTP 206)

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        logger.debug(f"Calling ADE Extract API: {self.extract_endpoint}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # ADE Extract expects form data, not JSON
        data = {
            "schema": json.dumps(BROKER_CONTRACT_EXTRACTION_SCHEMA),
            "markdown": markdown
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self.extract_endpoint,
                headers=headers,
                data=data  # Use data= for form encoding
            )

            # Accept both 200 (full success) and 206 (partial success)
            if response.status_code == 206:
                logger.warning("ADE Extract API returned partial success (HTTP 206)")
                result = response.json()
                metadata = result.get("metadata", {})
                if metadata:
                    logger.warning(f"Schema deviation: {metadata}")
                return result.get("extraction", {}), True

            response.raise_for_status()

        result = response.json()
        return result.get("extraction", {}), False

    def _calculate_confidence(self, extraction: dict, is_partial: bool) -> float:
        """
        Calculate confidence score based on extracted fields.

        Args:
            extraction: Extracted data dictionary
            is_partial: Whether extraction was partial (HTTP 206)

        Returns:
            float: Confidence score between 0 and 1
        """
        # Required fields check (40% weight)
        required_fields = BROKER_CONTRACT_EXTRACTION_SCHEMA["required"]
        required_found = sum(
            1 for field in required_fields
            if extraction.get(field) is not None
        )
        required_score = required_found / len(required_fields) * 0.4

        # Optional fields check (40% weight)
        all_fields = list(BROKER_CONTRACT_EXTRACTION_SCHEMA["properties"].keys())
        optional_fields = [f for f in all_fields if f not in required_fields]
        optional_found = sum(
            1 for field in optional_fields
            if extraction.get(field) is not None
        )
        optional_score = (
            optional_found / len(optional_fields) * 0.4 if optional_fields else 0.4
        )

        # Partial penalty (20% weight)
        partial_score = 0.0 if is_partial else 0.2

        total = required_score + optional_score + partial_score
        return round(total, 2)

    def _map_to_contract_data(
        self,
        extraction: dict,
        markdown: str,
        confidence: float
    ) -> BrokerContractData:
        """
        Map extracted data to BrokerContractData Pydantic model.

        Args:
            extraction: Extracted data dictionary from ADE Extract API
            markdown: Raw markdown for preview
            confidence: Calculated confidence score

        Returns:
            BrokerContractData: Validated contract data model

        Raises:
            ValueError: If data validation fails
        """
        # Clean and normalize extracted values
        def clean_string(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            cleaned = str(value).strip()
            return cleaned if cleaned else None

        def clean_number(value: Optional[float | int | str]) -> Optional[float]:
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        def clean_integer(value: Optional[int | str]) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        # Parse date from various formats to ISO
        def parse_date(value: Optional[str]) -> Optional[str]:
            if not value:
                return None
            value = str(value).strip()

            # Try DD/MM/YYYY format
            import re
            match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", value)
            if match:
                day, month, year = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            # Try YYYY-MM-DD format (already ISO)
            if re.match(r"\d{4}-\d{2}-\d{2}", value):
                return value

            return None

        # Build contract data
        data = {
            "nombre_broker": clean_string(extraction.get("nombre_broker")),
            "porcentaje_comision_apertura": clean_number(
                extraction.get("porcentaje_comision_apertura")
            ),
            "porcentaje_comision_operativa": clean_number(
                extraction.get("porcentaje_comision_operativa")
            ),
            "fecha_contrato": parse_date(extraction.get("fecha_contrato")),
            "vigencia_meses": clean_integer(extraction.get("vigencia_meses")),
            "rfc_broker": clean_string(extraction.get("rfc_broker")),
            "cuenta_bancaria": clean_string(extraction.get("cuenta_bancaria")),
            "banco": clean_string(extraction.get("banco")),
            "extraction_method": ExtractionMethod.AI,
            "extraction_confidence": confidence,
            "raw_text_preview": markdown[:500] if markdown else None,
        }

        logger.debug(f"Mapped extraction to BrokerContractData: {data}")

        # Create and validate Pydantic model
        try:
            return BrokerContractData(**data)
        except Exception as e:
            logger.error(f"Failed to create BrokerContractData: {e}")
            raise ValueError(f"Datos extraídos inválidos: {str(e)}")
