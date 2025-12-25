"""
Document Extraction Service - AI-powered extraction from fraud detection documents

Uses LandingAI's ADE (Agentic Document Extraction) API to extract structured data
from various document types for cross-validation fraud detection.
"""
import httpx
import json
import logging
from typing import Dict, Any
from decimal import Decimal

from src.config.settings import get_settings
from src.interface.risk_dtos import DocumentType, ExtractionStatus

logger = logging.getLogger(__name__)


# Document-specific extraction schemas for LandingAI ADE
EXTRACTION_SCHEMAS = {
    DocumentType.FINANCIAL_STATEMENT_CURRENT: {
        "type": "object",
        "properties": {
            "company_name": {"type": "string", "description": "Company legal name (Razón social)"},
            "nit": {"type": "string", "description": "Tax ID with verification digit (NIT-DV)"},
            "fiscal_year": {"type": "integer", "description": "Fiscal year of the statement"},
            "period_end_date": {"type": ["string", "null"], "description": "Period end date (YYYY-MM-DD)"},
            "auditor_name": {"type": ["string", "null"], "description": "Auditor/accountant name"},
            "auditor_license": {"type": ["string", "null"], "description": "Professional license number"},
            "total_assets": {"type": ["number", "null"], "description": "Total assets value"},
            "total_liabilities": {"type": ["number", "null"], "description": "Total liabilities value"},
            "total_equity": {"type": ["number", "null"], "description": "Total equity value"},
            "net_income": {"type": ["number", "null"], "description": "Net income/profit"},
            "revenue": {"type": ["number", "null"], "description": "Total revenue/sales"},
            "signatory_name": {"type": ["string", "null"], "description": "Name of person who signed"},
            "signatory_id": {"type": ["string", "null"], "description": "ID of signatory"},
            "signatory_role": {"type": ["string", "null"], "description": "Role of signatory"}
        },
        "required": ["company_name", "nit", "fiscal_year"]
    },

    DocumentType.FINANCIAL_STATEMENT_PRIOR: {
        "type": "object",
        "properties": {
            "company_name": {"type": "string", "description": "Company legal name (Razón social)"},
            "nit": {"type": "string", "description": "Tax ID with verification digit (NIT-DV)"},
            "fiscal_year": {"type": "integer", "description": "Fiscal year of the statement"},
            "period_end_date": {"type": ["string", "null"], "description": "Period end date (YYYY-MM-DD)"},
            "auditor_name": {"type": ["string", "null"], "description": "Auditor/accountant name"},
            "auditor_license": {"type": ["string", "null"], "description": "Professional license number"},
            "total_assets": {"type": ["number", "null"], "description": "Total assets value"},
            "total_liabilities": {"type": ["number", "null"], "description": "Total liabilities value"},
            "total_equity": {"type": ["number", "null"], "description": "Total equity value"},
            "net_income": {"type": ["number", "null"], "description": "Net income/profit"},
            "revenue": {"type": ["number", "null"], "description": "Total revenue/sales"},
            "signatory_name": {"type": ["string", "null"], "description": "Name of person who signed"},
            "signatory_id": {"type": ["string", "null"], "description": "ID of signatory"},
            "signatory_role": {"type": ["string", "null"], "description": "Role of signatory"}
        },
        "required": ["company_name", "nit", "fiscal_year"]
    },

    DocumentType.CEDULA: {
        "type": "object",
        "properties": {
            "full_name": {"type": "string", "description": "Full name as appears on ID"},
            "first_names": {"type": ["string", "null"], "description": "First and middle names"},
            "last_names": {"type": ["string", "null"], "description": "Surnames"},
            "document_number": {"type": "string", "description": "ID number (Cedula number)"},
            "document_type": {"type": "string", "description": "Document type (CC, CE, Pasaporte)"},
            "birth_date": {"type": ["string", "null"], "description": "Date of birth"},
            "birth_place": {"type": ["string", "null"], "description": "Place of birth"},
            "issue_date": {"type": ["string", "null"], "description": "ID issue date"},
            "issue_place": {"type": ["string", "null"], "description": "ID issue location"},
            "gender": {"type": ["string", "null"], "description": "Gender (M/F)"},
            "blood_type": {"type": ["string", "null"], "description": "Blood type if visible"}
        },
        "required": ["full_name", "document_number", "document_type"]
    },

    DocumentType.COMPOSICION_ACCIONARIA: {
        "type": "object",
        "properties": {
            "company_name": {"type": "string", "description": "Company legal name"},
            "nit": {"type": "string", "description": "Company NIT"},
            "document_date": {"type": ["string", "null"], "description": "Date of the document"},
            "total_shares": {"type": ["number", "null"], "description": "Total number of shares"},
            "share_value": {"type": ["number", "null"], "description": "Nominal value per share"},
            "shareholders": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "id_number": {"type": ["string", "null"]},
                        "shares": {"type": ["number", "null"]},
                        "percentage": {"type": ["number", "null"]},
                        "is_legal_representative": {"type": ["boolean", "null"]}
                    }
                }
            },
            "majority_shareholder_name": {"type": ["string", "null"], "description": "Name of majority shareholder"},
            "majority_shareholder_percentage": {"type": ["number", "null"], "description": "Percentage of majority shareholder"}
        },
        "required": ["company_name", "nit"]
    },

    DocumentType.RUT: {
        "type": "object",
        "properties": {
            "company_name": {"type": "string", "description": "Company legal name (field 35)"},
            "nit": {"type": "string", "description": "NIT with verification digit. Field 5 contains the 9-digit NIT number (labeled '5. Número de Identificación Tributaria (NIT)'). Immediately after field 5, there is a small field labeled '6.DV' containing a single digit which is the verification digit (dígito de verificación). Extract as 'XXXXXXXXX-D' format where D is the digit from field 6.DV. For example, if NIT is 830027231 and 6.DV is 3, return '830027231-3'."},
            "city": {"type": ["string", "null"], "description": "City/Municipality (field 40)"},
            "address": {"type": ["string", "null"], "description": "Registered address"},
            "email": {"type": ["string", "null"], "description": "Contact email (field 42)"},
            "phone": {"type": ["string", "null"], "description": "Contact phone"},
            "economic_activity": {"type": ["string", "null"], "description": "Economic activity code"},
            "legal_representative_name": {"type": "string", "description": "Legal rep full name (fields 104-107) - Principal representative"},
            "legal_representative_id": {"type": "string", "description": "Legal rep ID number (field 101) - Principal representative"},
            "legal_representative_id_type": {"type": ["string", "null"], "description": "Legal rep ID type (field 100)"},
            "legal_representatives": {
                "type": "array",
                "description": "ALL legal representatives from the Representación section. Colombian RUTs can have multiple representatives: REPRS LEGAL PRIN (principal) and REPRS LEGAL SUPL (suplente/alternate). Extract ALL of them.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Full name of the representative (fields 104-107)"},
                        "id_number": {"type": "string", "description": "Cedula/ID number of the representative (field 101)"},
                        "id_type": {"type": ["string", "null"], "description": "Document type (CC, CE, Pasaporte) - field 100"},
                        "role": {"type": "string", "description": "Role: 'principal' for REPRS LEGAL PRIN, 'suplente' for REPRS LEGAL SUPL"},
                        "representation_type": {"type": ["string", "null"], "description": "Raw representation type code from RUT (e.g., REPRS LEGAL PRIN, REPRS LEGAL SUPL)"}
                    },
                    "required": ["name", "id_number", "role"]
                }
            },
            "registration_date": {"type": ["string", "null"], "description": "RUT registration date"},
            "last_update_date": {"type": ["string", "null"], "description": "Last RUT update date"}
        },
        "required": ["company_name", "nit", "legal_representative_name", "legal_representative_id"]
    },

    DocumentType.CERTIFICADO_EXISTENCIA: {
        "type": "object",
        "properties": {
            "company_name": {"type": "string", "description": "Company legal name"},
            "nit": {"type": "string", "description": "NIT with verification digit"},
            "entity_type": {"type": ["string", "null"], "description": "Legal entity type (S.A.S., S.A., LTDA)"},
            "registration_number": {"type": ["string", "null"], "description": "Chamber of commerce registration"},
            "constitution_date": {"type": ["string", "null"], "description": "Date company was constituted"},
            "registered_capital": {"type": ["number", "null"], "description": "Registered capital"},
            "legal_representative_name": {"type": "string", "description": "Legal representative name - Principal representative"},
            "legal_representative_id": {"type": "string", "description": "Legal representative ID number - Principal representative"},
            "legal_representative_id_type": {"type": ["string", "null"], "description": "Legal rep ID type"},
            "legal_representative_authority": {"type": ["string", "null"], "description": "Authority limits"},
            "legal_representatives": {
                "type": "array",
                "description": "ALL legal representatives from the REPRESENTANTES LEGALES section. Extract both principal and suplente/alternate representatives. Look for markers like <principal> or <suplente> in the document.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Full name of the representative"},
                        "id_number": {"type": "string", "description": "Cedula/ID number of the representative"},
                        "id_type": {"type": ["string", "null"], "description": "Document type (CC, CE, Pasaporte)"},
                        "role": {"type": "string", "description": "Role: 'principal' or 'suplente' based on section headers or markers in the document"},
                        "authority": {"type": ["string", "null"], "description": "Authority limits for this representative"}
                    },
                    "required": ["name", "id_number", "role"]
                }
            },
            "registered_address": {"type": ["string", "null"], "description": "Company registered address"},
            "city": {"type": ["string", "null"], "description": "City of registration"},
            "certificate_date": {"type": ["string", "null"], "description": "Certificate issue date"},
            "expiry_date": {"type": ["string", "null"], "description": "Certificate expiry date"},
            "chamber_of_commerce": {"type": ["string", "null"], "description": "Issuing chamber of commerce"},
            "board_members": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "id_number": {"type": ["string", "null"]},
                        "position": {"type": ["string", "null"]}
                    }
                }
            }
        },
        "required": ["company_name", "nit", "legal_representative_name", "legal_representative_id"]
    }
}


class DocumentExtractionService:
    """
    Service for extracting structured data from fraud detection documents.

    Uses LandingAI's ADE (Agentic Document Extraction) API to process:
    - Financial Statements (current and prior year)
    - Cedula (Legal Representative ID)
    - Composicion Accionaria (Shareholder Composition)
    - RUT (Tax Registration)
    - Certificado de Existencia (Certificate of Existence)

    Processing takes 30-60 seconds per document.
    """

    def __init__(self):
        """Initialize document extraction service with API configuration."""
        settings = get_settings()
        self.api_key = settings.LANDINGAI_API_KEY
        self.parse_endpoint = settings.LANDINGAI_PARSE_ENDPOINT
        self.extract_endpoint = settings.LANDINGAI_EXTRACT_ENDPOINT
        self.timeout = 120  # 2 minutes timeout for API calls

        if not self.api_key:
            logger.warning("LANDINGAI_API_KEY is not configured. AI extraction will not work.")

    async def extract_document(
        self,
        document_type: DocumentType,
        file_bytes: bytes,
        filename: str = "document.pdf"
    ) -> Dict[str, Any]:
        """
        Extract structured data from a document using LandingAI ADE API.

        Args:
            document_type: Type of document to extract
            file_bytes: Document file content as bytes
            filename: Original filename (for logging)

        Returns:
            dict: Extraction result with status, data, and confidence

        Raises:
            ValueError: If API key is not configured or extraction fails
        """
        if not self.api_key:
            raise ValueError(
                "LANDINGAI_API_KEY is not configured. Please set the environment variable."
            )

        logger.info(f"Starting LandingAI extraction for {document_type.value}: {filename}")

        try:
            # Step 1: Parse document to markdown
            markdown = await self._call_parse_api(file_bytes, filename)
            logger.info(f"Parse completed - {len(markdown)} characters of markdown")

            # Step 2: Get schema for document type
            schema = EXTRACTION_SCHEMAS.get(document_type)
            if not schema:
                raise ValueError(f"No schema defined for document type: {document_type.value}")

            # Step 3: Extract structured data
            extraction, confidence = await self._call_extract_api(markdown, schema)
            logger.info(f"Extraction completed - {len(extraction)} fields extracted")

            # Step 4: Validate required fields
            validation_result = self._validate_extraction(document_type, extraction)

            return {
                "status": ExtractionStatus.COMPLETED.value if validation_result["valid"] else ExtractionStatus.COMPLETED.value,
                "extracted_data": extraction,
                "confidence": confidence,
                "missing_fields": validation_result.get("missing_fields", []),
                "errors": None
            }

        except httpx.TimeoutException:
            logger.error(f"LandingAI API timeout for {filename}")
            return {
                "status": ExtractionStatus.FAILED.value,
                "extracted_data": None,
                "confidence": None,
                "errors": ["Extraction timeout. The document took too long to process."]
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"LandingAI API HTTP error: {e.response.status_code}")
            error_message = self._handle_http_error(e)
            return {
                "status": ExtractionStatus.FAILED.value,
                "extracted_data": None,
                "confidence": None,
                "errors": [error_message]
            }
        except ValueError as e:
            logger.error(f"Extraction validation error: {e}")
            return {
                "status": ExtractionStatus.FAILED.value,
                "extracted_data": None,
                "confidence": None,
                "errors": [str(e)]
            }
        except Exception as e:
            logger.error(f"Unexpected extraction error: {e}", exc_info=True)
            return {
                "status": ExtractionStatus.FAILED.value,
                "extracted_data": None,
                "confidence": None,
                "errors": [f"Extraction failed: {str(e)}"]
            }

    async def _call_parse_api(self, file_bytes: bytes, filename: str) -> str:
        """
        Call LandingAI ADE Parse API to convert document to markdown.

        Args:
            file_bytes: Document file content
            filename: Original filename

        Returns:
            str: Markdown representation of the document

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        logger.debug(f"Calling ADE Parse API: {self.parse_endpoint}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # Determine content type from filename
        content_type = "application/pdf"
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            content_type = "image/png" if filename.lower().endswith('.png') else "image/jpeg"

        files = {
            "document": (filename, file_bytes, content_type)
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
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

    async def _call_extract_api(self, markdown: str, schema: dict) -> tuple:
        """
        Call LandingAI ADE Extract API to extract structured data.

        Args:
            markdown: Document content in markdown format
            schema: JSON schema for extraction

        Returns:
            tuple: (extraction dict, confidence score)

        Raises:
            httpx.HTTPStatusError: If API call fails
        """
        logger.debug(f"Calling ADE Extract API: {self.extract_endpoint}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "schema": json.dumps(schema),
            "markdown": markdown
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.extract_endpoint,
                headers=headers,
                data=data
            )

            # Accept both 200 (full success) and 206 (partial success)
            if response.status_code == 206:
                logger.warning("ADE Extract API returned partial success (HTTP 206)")
                result = response.json()
                metadata = result.get("metadata", {})
                if metadata:
                    logger.warning(f"Schema deviation: {metadata}")
                extraction = result.get("extraction", {})
                # Partial extraction has lower confidence
                return extraction, Decimal("0.7")

            response.raise_for_status()

        result = response.json()
        extraction = result.get("extraction", {})

        # Full success has high confidence
        return extraction, Decimal("0.95")

    def _validate_extraction(self, document_type: DocumentType, extraction: dict) -> dict:
        """
        Validate that required fields are present in the extraction.

        Args:
            document_type: Type of document
            extraction: Extracted data dictionary

        Returns:
            dict: Validation result with valid flag and missing fields
        """
        schema = EXTRACTION_SCHEMAS.get(document_type, {})
        required_fields = schema.get("required", [])

        missing_fields = []
        for field in required_fields:
            value = extraction.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)

        return {
            "valid": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> str:
        """Convert HTTP errors to user-friendly messages."""
        status_code = error.response.status_code

        if status_code == 401:
            return "Invalid LandingAI API key. Please check configuration."
        elif status_code == 429:
            return "LandingAI API rate limit exceeded. Please try again later."
        elif status_code >= 500:
            return f"LandingAI server error ({status_code}). Please try again."
        else:
            return f"LandingAI API error ({status_code}): {error.response.text[:200]}"

    def get_document_type_info(self, document_type: DocumentType) -> dict:
        """
        Get information about a document type including accepted formats and max size.

        Args:
            document_type: Document type enum value

        Returns:
            dict: Document type information
        """
        info = {
            DocumentType.FINANCIAL_STATEMENT_CURRENT: {
                "label": "Estados Financieros (Año Actual)",
                "accepted_formats": ["pdf"],
                "max_size_mb": 50,
                "required_fields": ["company_name", "nit", "fiscal_year"]
            },
            DocumentType.FINANCIAL_STATEMENT_PRIOR: {
                "label": "Estados Financieros (Año Anterior)",
                "accepted_formats": ["pdf"],
                "max_size_mb": 50,
                "required_fields": ["company_name", "nit", "fiscal_year"]
            },
            DocumentType.CEDULA: {
                "label": "Cédula del Representante Legal",
                "accepted_formats": ["pdf", "png", "jpg", "jpeg"],
                "max_size_mb": 5,
                "required_fields": ["full_name", "document_number", "document_type"]
            },
            DocumentType.COMPOSICION_ACCIONARIA: {
                "label": "Composición Accionaria",
                "accepted_formats": ["pdf"],
                "max_size_mb": 10,
                "required_fields": ["company_name", "nit"]
            },
            DocumentType.RUT: {
                "label": "RUT",
                "accepted_formats": ["pdf", "png"],
                "max_size_mb": 5,
                "required_fields": ["company_name", "nit", "legal_representative_name", "legal_representative_id"]
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                "label": "Certificado de Existencia",
                "accepted_formats": ["pdf"],
                "max_size_mb": 50,
                "required_fields": ["company_name", "nit", "legal_representative_name", "legal_representative_id"]
            }
        }
        return info.get(document_type, {})
