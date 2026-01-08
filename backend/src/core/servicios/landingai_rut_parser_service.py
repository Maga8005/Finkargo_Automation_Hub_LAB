"""
LandingAI RUT Parser Service - Extracts custodian information from Colombian RUT documents using AI

This service uses LandingAI's ADE (Agentic Document Extraction) API to extract structured data
from RUT PDFs, including scanned/image-based documents that cannot be processed with text extraction.
"""
import httpx
import json
import logging
from typing import Optional

from src.config.settings import get_settings
from src.interface.legal_dtos import CustodianData

logger = logging.getLogger(__name__)


# RUT Extraction Schema for LandingAI ADE Extract API
RUT_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "nombre_operador_custodio": {
            "type": "string",
            "description": "Company legal name (Razón social) - field 35"
        },
        "ciudad_domicilio_custodio": {
            "type": "string",
            "description": "City/Municipality where company is located - field 40"
        },
        "nit_operador_custodio": {
            "type": "string",
            "description": "Tax ID with verification digit (NIT-DV format: 900989925-7) - fields 5 and 6"
        },
        "email_operador_custodio": {
            "type": "string",
            "description": "Company contact email - field 42"
        },
        "nombre_representante_legal_custodio": {
            "type": "string",
            "description": "Legal representative full name (first + last names) - fields 104-107"
        },
        "cc_representante_legal_custodio": {
            "type": "string",
            "description": "Legal representative ID number (cédula) - field 101"
        },
        "tipo_identificacion_representante_legal_custodio": {
            "type": "string",
            "description": "Legal representative ID type (CC, CE, Pasaporte) - field 100"
        }
    },
    "required": [
        "nombre_operador_custodio",
        "nit_operador_custodio",
        "nombre_representante_legal_custodio",
        "cc_representante_legal_custodio"
    ]
}


class LandingAIRUTParserService:
    """
    Service for parsing Colombian RUT documents using LandingAI's ADE (Agentic Document Extraction) API.

    This service is intended for image-based/scanned RUT PDFs where text extraction fails.
    Processing takes 30-60 seconds per document.
    """

    def __init__(self):
        """Initialize LandingAI RUT parser service with API configuration."""
        settings = get_settings()
        self.api_key = settings.LANDINGAI_API_KEY
        self.parse_endpoint = settings.LANDINGAI_PARSE_ENDPOINT
        self.extract_endpoint = settings.LANDINGAI_EXTRACT_ENDPOINT
        self.timeout = 120  # 2 minutes timeout for API calls

        if not self.api_key:
            logger.warning("LANDINGAI_API_KEY is not configured. AI extraction will not work.")

    def parse_rut_pdf(self, pdf_bytes: bytes) -> CustodianData:
        """
        Parse RUT PDF and extract custodian data using LandingAI ADE API.

        Args:
            pdf_bytes: RUT PDF file content as bytes

        Returns:
            CustodianData: Extracted custodian information

        Raises:
            ValueError: If API key is not configured, API call fails, or required fields cannot be extracted
        """
        if not self.api_key:
            raise ValueError(
                "LANDINGAI_API_KEY is not configured. Please set the environment variable to use AI extraction."
            )

        logger.info("Starting LandingAI RUT extraction (AI-powered)")

        try:
            # Step 1: Parse document to markdown using ADE Parse API
            markdown = self._call_parse_api(pdf_bytes)
            logger.info(f"ADE Parse completed - {len(markdown)} characters of markdown")

            # Step 2: Extract structured data using ADE Extract API
            extraction = self._call_extract_api(markdown)
            logger.info(f"ADE Extract completed - {len(extraction)} fields extracted")

            # Step 3: Validate required fields are present
            if not self._validate_extraction(extraction):
                missing_fields = [
                    field for field in RUT_EXTRACTION_SCHEMA["required"]
                    if not extraction.get(field)
                ]
                raise ValueError(
                    f"AI extraction incomplete. Missing required fields: {', '.join(missing_fields)}"
                )

            # Step 4: Map to CustodianData model
            custodian_data = self._map_to_custodian_data(extraction)
            logger.info(f"LandingAI RUT extraction completed successfully for: {custodian_data.nombre_operador_custodio}")

            return custodian_data

        except httpx.TimeoutException:
            logger.error("LandingAI API timeout (exceeded 120 seconds)")
            raise ValueError(
                "AI extraction timeout. The document is taking too long to process. "
                "Please try again or use standard text extraction."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"LandingAI API HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                raise ValueError(
                    "Invalid LandingAI API key. Please check your LANDINGAI_API_KEY configuration."
                )
            elif e.response.status_code == 429:
                raise ValueError(
                    "LandingAI API rate limit exceeded. Please try again later."
                )
            else:
                raise ValueError(
                    f"LandingAI API error ({e.response.status_code}): {e.response.text}"
                )
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error during LandingAI RUT extraction: {e}", exc_info=True)
            raise ValueError(f"AI extraction failed: {str(e)}")

    def _call_parse_api(self, pdf_bytes: bytes) -> str:
        """
        Call LandingAI ADE Parse API to convert PDF to markdown.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            str: Markdown representation of the document

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        logger.debug(f"Calling ADE Parse API: {self.parse_endpoint}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        files = {
            "document": ("rut_document.pdf", pdf_bytes, "application/pdf")
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
            raise ValueError("ADE Parse API returned empty markdown")

        logger.debug(f"ADE Parse API returned {len(result.get('chunks', []))} chunks")
        return markdown

    def _call_extract_api(self, markdown: str) -> dict:
        """
        Call LandingAI ADE Extract API to extract structured data from markdown.

        Args:
            markdown: Document content in markdown format

        Returns:
            dict: Extracted data matching the RUT schema

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        logger.debug(f"Calling ADE Extract API: {self.extract_endpoint}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # ADE Extract expects form data, not JSON
        data = {
            "schema": json.dumps(RUT_EXTRACTION_SCHEMA),
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
                return result.get("extraction", {})

            response.raise_for_status()

        result = response.json()
        return result.get("extraction", {})

    def _validate_extraction(self, extraction: dict) -> bool:
        """
        Validate that all required fields are present in the extraction.

        Args:
            extraction: Extracted data dictionary

        Returns:
            bool: True if all required fields are present and non-empty
        """
        required_fields = RUT_EXTRACTION_SCHEMA["required"]

        for field in required_fields:
            value = extraction.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                logger.warning(f"Required field '{field}' is missing or empty")
                return False

        return True

    def _map_to_custodian_data(self, extraction: dict) -> CustodianData:
        """
        Map extracted data to CustodianData Pydantic model.

        Args:
            extraction: Extracted data dictionary from ADE Extract API

        Returns:
            CustodianData: Validated custodian data model

        Raises:
            ValueError: If data validation fails
        """
        # Clean and normalize extracted values
        def clean_value(value: Optional[str], default: str = "") -> str:
            if value is None:
                return default
            return str(value).strip()

        # Map ID type to abbreviation
        id_type = clean_value(extraction.get("tipo_identificacion_representante_legal_custodio"), "CC")
        id_type_abbrev = self._normalize_id_type(id_type)

        # Build custodian data
        data = {
            "nombre_operador_custodio": clean_value(extraction.get("nombre_operador_custodio")),
            "ciudad_domicilio_custodio": clean_value(
                extraction.get("ciudad_domicilio_custodio"),
                "Bogotá, D.C."  # Default to Bogotá if not extracted
            ),
            "nit_operador_custodio": clean_value(extraction.get("nit_operador_custodio")),
            "email_operador_custodio": clean_value(
                extraction.get("email_operador_custodio"),
                "no-email@placeholder.com"  # Placeholder if not extracted
            ).lower(),
            "nombre_representante_legal_custodio": clean_value(
                extraction.get("nombre_representante_legal_custodio")
            ),
            "cc_representante_legal_custodio": clean_value(
                extraction.get("cc_representante_legal_custodio")
            ),
            "tipo_identificacion_representante_legal_custodio": id_type_abbrev
        }

        logger.debug(f"Mapped extraction to CustodianData: {data}")

        # Create and validate Pydantic model
        try:
            return CustodianData(**data)
        except Exception as e:
            logger.error(f"Failed to create CustodianData: {e}")
            raise ValueError(f"Invalid extracted data: {str(e)}")

    def _normalize_id_type(self, id_type: str) -> str:
        """
        Normalize ID type to standard abbreviation.

        Args:
            id_type: ID type string from extraction

        Returns:
            str: Normalized abbreviation (CC, CE, Pasaporte)
        """
        id_type_lower = id_type.lower()

        # Map common variations to abbreviations
        if "cedula" in id_type_lower or "ciudadan" in id_type_lower:
            return "CC"
        elif "extranjer" in id_type_lower:
            return "CE"
        elif "pasaporte" in id_type_lower:
            return "Pasaporte"
        elif "tarjeta" in id_type_lower and "identidad" in id_type_lower:
            return "TI"
        elif id_type_lower in ["cc", "ce", "ti", "pasaporte"]:
            return id_type.upper() if len(id_type) <= 2 else id_type.title()

        # Default to CC (most common in Colombia)
        logger.warning(f"Unknown ID type '{id_type}', defaulting to CC")
        return "CC"
