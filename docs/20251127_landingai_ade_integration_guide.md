# LandingAI ADE (Agentic Document Extraction) Integration Guide

This document explains how the Finkargo Pre-Approval system integrates with LandingAI's ADE APIs for intelligent document parsing and data extraction.

## Overview

LandingAI's **ADE (Agentic Document Extraction)** provides two main APIs:
1. **ADE Parse** - Converts documents (PDF/images) to structured markdown
2. **ADE Extract** - Extracts structured data from markdown using JSON schemas

The system uses a **3-tier extraction approach** with intelligent fallbacks for maximum reliability.

---

## Architecture: 3-Tier Extraction Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Upload                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 1: LandingAI ADE (Schema-Based AI)                        │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │  Document   │───▶│  ADE Parse   │───▶│  ADE Extract    │    │
│  │  (PDF/IMG)  │    │  (→Markdown) │    │  (+JSON Schema) │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                                  │
│  ✓ Most accurate          ✓ Format-agnostic                     │
│  ✓ Structured output      ✓ Schema-validated                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ If fails
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 2: GPT-4 Vision (Visual Document Understanding)           │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │  Document   │───▶│  PDF→Images  │───▶│  GPT-4 Vision   │    │
│  │  (PDF/IMG)  │    │  (base64)    │    │  (with prompt)  │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                                  │
│  ✓ Handles complex/scanned PDFs    ⚠ Higher cost ($0.10-$1.00) │
└─────────────────────────┬───────────────────────────────────────┘
                          │ If fails
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TIER 3: Pattern Matching (Regex-Based)                         │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │  Document   │───▶│  Text/Table  │───▶│  Regex Patterns │    │
│  │  (PDF)      │    │  Extraction  │    │  (domain-spec)  │    │
│  └─────────────┘    └──────────────┘    └─────────────────┘    │
│                                                                  │
│  ✓ Fast and free        ⚠ Limited accuracy for complex docs    │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Configuration

### Environment Variables

```bash
# LandingAI API Configuration
LANDINGAI_API_KEY=your_api_key_here
LANDINGAI_PARSE_ENDPOINT=https://api.va.landing.ai/v1/ade/parse
LANDINGAI_EXTRACT_ENDPOINT=https://api.va.landing.ai/v1/ade/extract
```

### Python Settings

```python
# backend/src/config/settings.py
class Settings(BaseSettings):
    landingai_api_key: str = Field(default="", env="LANDINGAI_API_KEY")
    landingai_parse_endpoint: str = Field(
        default="https://api.va.landing.ai/v1/ade/parse",
        env="LANDINGAI_PARSE_ENDPOINT"
    )
    landingai_extract_endpoint: str = Field(
        default="https://api.va.landing.ai/v1/ade/extract",
        env="LANDINGAI_EXTRACT_ENDPOINT"
    )
```

---

## API Reference

### 1. ADE Parse API

**Purpose**: Convert documents (PDF/images) to structured markdown.

**Endpoint**: `POST https://api.va.landing.ai/v1/ade/parse`

**Request**:
```python
import requests

headers = {
    "Authorization": f"Bearer {LANDINGAI_API_KEY}"
}

# For PDF documents
with open("document.pdf", "rb") as f:
    files = {
        "document": ("document.pdf", f, "application/pdf")
    }
    response = requests.post(
        "https://api.va.landing.ai/v1/ade/parse",
        headers=headers,
        files=files,
        timeout=120
    )

# For images (PNG/JPEG)
with open("document.png", "rb") as f:
    files = {
        "document": ("document.png", f, "image/png")  # or "image/jpeg"
    }
    response = requests.post(
        "https://api.va.landing.ai/v1/ade/parse",
        headers=headers,
        files=files,
        timeout=120
    )
```

**Response**:
```json
{
    "markdown": "# Document Title\n\nContent converted to markdown...\n\n| Column1 | Column2 |\n|---------|---------|...",
    "chunks": [
        {
            "type": "text",
            "markdown": "# Document Title\n\nSome text content...",
            "bbox": [0, 0, 100, 50],
            "index": 0
        },
        {
            "type": "table",
            "markdown": "| Header1 | Header2 |\n|---------|---------|...",
            "bbox": [0, 50, 100, 200],
            "index": 1
        }
    ]
}
```

**Content Types Supported**:
- `application/pdf` - PDF documents
- `image/png` - PNG images
- `image/jpeg` - JPEG images

---

### 2. ADE Extract API

**Purpose**: Extract structured data from markdown using a JSON schema.

**Endpoint**: `POST https://api.va.landing.ai/v1/ade/extract`

**Request**:
```python
import requests
import json

headers = {
    "Authorization": f"Bearer {LANDINGAI_API_KEY}"
}

# Define your extraction schema
extraction_schema = {
    "type": "object",
    "properties": {
        "company_name": {
            "type": "string",
            "description": "Name of the company"
        },
        "total_revenue": {
            "type": "number",
            "description": "Total revenue in USD"
        },
        "fiscal_year": {
            "type": "integer",
            "description": "Fiscal year of the report"
        }
    },
    "required": ["company_name", "total_revenue"]
}

# Send as form data (NOT JSON)
data = {
    "schema": json.dumps(extraction_schema),
    "markdown": markdown_from_parse_api
}

response = requests.post(
    "https://api.va.landing.ai/v1/ade/extract",
    headers=headers,
    data=data,  # Use data= for form encoding, NOT json=
    timeout=120
)
```

**Response (HTTP 200 - Full Success)**:
```json
{
    "extraction": {
        "company_name": "Acme Corporation",
        "total_revenue": 5610880.00,
        "fiscal_year": 2024
    }
}
```

**Response (HTTP 206 - Partial Success)**:
```json
{
    "extraction": {
        "company_name": "Acme Corporation",
        "total_revenue": 5610880.00,
        "fiscal_year": null
    },
    "metadata": {
        "schema_violation_error": "Field 'fiscal_year' could not be extracted"
    }
}
```

**HTTP Status Codes**:
| Code | Meaning | Action |
|------|---------|--------|
| 200 | Full success | Use extraction data directly |
| 206 | Partial success (schema deviation) | Data is usable, check nullable fields |
| 4xx | Client error | Check schema format and markdown |
| 5xx | Server error | Retry or fall back to TIER 2 |

**Important**: HTTP 206 is acceptable and common when optional/nullable fields cannot be extracted. The extraction data is still valid and usable.

---

## Implementation Examples

### Example 1: Financial Statement Extraction

```python
class ComprehensiveFinancialExtractionService:
    """Extract financial metrics from financial statements."""

    EXTRACTION_SCHEMA = {
        "type": "object",
        "properties": {
            # Income Statement (7 fields)
            "sales_revenue": {"type": "number", "description": "Total sales/revenue"},
            "cost_of_sales": {"type": "number", "description": "Cost of goods sold"},
            "gross_profit": {"type": "number", "description": "Gross profit"},
            "operating_expenses": {"type": "number", "description": "Operating expenses"},
            "operating_earnings": {"type": "number", "description": "Operating income/EBIT"},
            "financial_expenses": {"type": "number", "description": "Interest expenses"},
            "net_profit": {"type": "number", "description": "Net income"},

            # Balance Sheet - Assets (5 fields)
            "current_assets": {"type": "number"},
            "accounts_receivable": {"type": ["number", "null"]},
            "inventory": {"type": ["number", "null"]},
            "non_current_assets": {"type": ["number", "null"]},
            "total_assets": {"type": "number"},

            # Balance Sheet - Liabilities (6 fields)
            "current_liabilities": {"type": "number"},
            "accounts_payable": {"type": ["number", "null"]},
            "short_term_debt": {"type": ["number", "null"]},
            "non_current_liabilities": {"type": ["number", "null"]},
            "long_term_debt": {"type": ["number", "null"]},
            "total_liabilities": {"type": "number"},

            # Balance Sheet - Equity (3 fields)
            "share_capital": {"type": "number"},
            "retained_earnings": {"type": ["number", "null"]},
            "total_equity": {"type": "number"},

            # Metadata
            "currency": {"type": "string", "description": "Currency code (MXN, USD)"},
            "period": {"type": "string", "description": "Period description"},
            "year": {"type": "integer", "description": "Fiscal year"},
            "period_month": {"type": "integer", "description": "Month (1-12)"},
            "period_end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
        },
        "required": ["sales_revenue", "total_assets", "total_liabilities", "total_equity"]
    }

    def extract_from_pdf(self, pdf_path: str) -> dict:
        """
        Extract financial data using 3-tier approach.
        """
        # TIER 1: Try LandingAI ADE
        try:
            # Step 1: Parse document to markdown
            parse_response = self._call_landingai_parse_api(pdf_path)
            markdown = parse_response.get("markdown", "")

            # Step 2: Extract structured data
            extract_response = self._call_landingai_extract_api(markdown)
            extraction = extract_response.get("extraction", {})

            if self._validate_extraction(extraction):
                return {
                    "data": extraction,
                    "method": "ade_extract",
                    "tier": 1
                }
        except Exception as e:
            logger.warning(f"TIER 1 failed: {e}")

        # TIER 2: Try GPT-4 Vision
        try:
            result = self._extract_with_gpt4_vision(pdf_path)
            if result:
                return {
                    "data": result,
                    "method": "gpt4_vision",
                    "tier": 2
                }
        except Exception as e:
            logger.warning(f"TIER 2 failed: {e}")

        # TIER 3: Pattern matching
        try:
            result = self._extract_with_patterns(pdf_path)
            return {
                "data": result,
                "method": "pattern_matching",
                "tier": 3
            }
        except Exception as e:
            logger.error(f"All extraction tiers failed: {e}")
            return None
```

### Example 2: Import Data Extraction

```python
class ImportExtractionService:
    """Extract import/trade data from documents."""

    EXTRACTION_SCHEMA = {
        "type": "object",
        "properties": {
            "imports_by_year": {
                "type": "array",
                "description": "Import data by year",
                "items": {
                    "type": "object",
                    "properties": {
                        "year": {"type": "integer"},
                        "total_fob_usd": {"type": "number"},
                        "operations": {"type": ["integer", "null"]},
                        "merchandise_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "value_usd": {"type": "number"}
                                }
                            }
                        }
                    },
                    "required": ["year", "total_fob_usd"]
                }
            },
            "variation_percentage": {"type": "number"},
            "origin_countries": {"type": "array", "items": {"type": "string"}},
            "suppliers": {"type": "array", "items": {"type": "string"}}
        }
    }
```

---

## Schema Design Best Practices

### 1. Use Nullable Types for Optional Fields

```python
# Good - allows null for optional fields
"accounts_receivable": {"type": ["number", "null"]}

# Also good - explicit nullable flag
"accounts_receivable": {"type": "number", "nullable": True}
```

### 2. Provide Clear Descriptions

```python
"total_fob_usd": {
    "type": "number",
    "description": "Total FOB (Free On Board) value in US Dollars"
}
```

### 3. Use Required Array Sparingly

Only mark fields as required if extraction should fail without them:

```python
{
    "properties": {...},
    "required": ["total_revenue", "year"]  # Minimum viable extraction
}
```

### 4. Handle Multi-Year Documents

```python
"imports_by_year": {
    "type": "array",
    "description": "Extract data for ALL available years",
    "items": {
        "type": "object",
        "properties": {
            "year": {"type": "integer"},
            "value": {"type": "number"}
        }
    }
}
```

---

## Validation Patterns

### Financial Data Validation

```python
def _validate_extraction(self, data: dict) -> bool:
    """Validate extracted financial data."""
    errors = []

    # 1. Check minimum field coverage
    income_fields = ['sales_revenue', 'cost_of_sales', 'gross_profit',
                     'operating_expenses', 'operating_earnings',
                     'financial_expenses', 'net_profit']
    income_count = sum(1 for f in income_fields if data.get(f) is not None)
    if income_count < 5:
        errors.append(f"Income statement: only {income_count}/7 fields")

    # 2. Check accounting equation (±5% tolerance)
    assets = data.get('total_assets', 0)
    liabilities = data.get('total_liabilities', 0)
    equity = data.get('total_equity', 0)

    if assets > 0:
        expected = liabilities + equity
        diff_pct = abs(assets - expected) / assets * 100
        if diff_pct > 5:
            errors.append(f"Accounting equation off by {diff_pct:.1f}%")

    # 3. Check income statement math
    sales = data.get('sales_revenue', 0)
    cogs = data.get('cost_of_sales', 0)
    gross = data.get('gross_profit', 0)

    if sales > 0 and cogs > 0 and gross > 0:
        expected_gross = sales - cogs
        diff_pct = abs(gross - expected_gross) / sales * 100
        if diff_pct > 5:
            errors.append(f"Gross profit calculation off by {diff_pct:.1f}%")

    return len(errors) == 0, errors
```

---

## Error Handling

### Handle API Errors Gracefully

```python
def _call_landingai_extract_api(self, markdown: str) -> dict:
    response = requests.post(
        self.extract_endpoint,
        headers={"Authorization": f"Bearer {self.api_key}"},
        data={
            "schema": json.dumps(self.schema),
            "markdown": markdown
        },
        timeout=120
    )

    # Accept both 200 and 206 (partial content)
    if response.status_code == 206:
        result = response.json()
        logger.warning(f"Partial extraction: {result.get('metadata', {})}")
        return result  # Data is still usable

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    return response.json()
```

---

## Performance Characteristics

| Tier | Method | Speed | Cost | Accuracy |
|------|--------|-------|------|----------|
| 1 | ADE Parse + Extract | 20-40s | $0.30-$4.00/doc | Highest |
| 2 | GPT-4 Vision | 3-5s/page | $0.10-$1.00/doc | High |
| 3 | Pattern Matching | 1-2s | Free | Medium |

---

## Complete Working Example

```python
import os
import json
import requests
import logging

logger = logging.getLogger(__name__)


class DocumentExtractionService:
    """
    Generic document extraction service using LandingAI ADE.

    Usage:
        service = DocumentExtractionService(
            api_key=os.getenv("LANDINGAI_API_KEY"),
            extraction_schema=YOUR_SCHEMA
        )
        result = service.extract_from_document("path/to/document.pdf")
    """

    PARSE_ENDPOINT = "https://api.va.landing.ai/v1/ade/parse"
    EXTRACT_ENDPOINT = "https://api.va.landing.ai/v1/ade/extract"

    def __init__(self, api_key: str, extraction_schema: dict):
        self.api_key = api_key
        self.extraction_schema = extraction_schema
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def extract_from_document(self, file_path: str) -> dict:
        """
        Extract structured data from a document.

        Args:
            file_path: Path to PDF or image file

        Returns:
            Extracted data matching the schema
        """
        # Step 1: Determine content type
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"
        }
        content_type = content_types.get(ext, "application/pdf")

        # Step 2: Parse document to markdown
        logger.info(f"[ADE PARSE] Processing {file_path}")
        with open(file_path, "rb") as f:
            files = {"document": (os.path.basename(file_path), f, content_type)}
            response = requests.post(
                self.PARSE_ENDPOINT,
                headers=self.headers,
                files=files,
                timeout=120
            )

        if response.status_code != 200:
            raise Exception(f"Parse failed: {response.status_code} - {response.text}")

        parse_result = response.json()
        markdown = parse_result.get("markdown", "")
        chunks = parse_result.get("chunks", [])

        logger.info(f"[ADE PARSE] Success - {len(chunks)} chunks, {len(markdown)} chars")

        # Step 3: Extract structured data
        logger.info("[ADE EXTRACT] Extracting structured data")
        data = {
            "schema": json.dumps(self.extraction_schema),
            "markdown": markdown
        }

        response = requests.post(
            self.EXTRACT_ENDPOINT,
            headers=self.headers,
            data=data,
            timeout=120
        )

        if response.status_code not in [200, 206]:
            raise Exception(f"Extract failed: {response.status_code} - {response.text}")

        extract_result = response.json()

        if response.status_code == 206:
            logger.warning(f"[ADE EXTRACT] Partial success (HTTP 206)")

        extraction = extract_result.get("extraction", {})
        logger.info(f"[ADE EXTRACT] Success - {len(extraction)} fields extracted")

        return {
            "extraction": extraction,
            "markdown": markdown,
            "chunks": chunks,
            "status": "partial" if response.status_code == 206 else "complete"
        }


# Usage example
if __name__ == "__main__":
    # Define your extraction schema
    invoice_schema = {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "invoice_date": {"type": "string"},
            "vendor_name": {"type": "string"},
            "total_amount": {"type": "number"},
            "currency": {"type": "string"},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "total": {"type": "number"}
                    }
                }
            }
        },
        "required": ["invoice_number", "total_amount"]
    }

    # Create service and extract
    service = DocumentExtractionService(
        api_key=os.getenv("LANDINGAI_API_KEY"),
        extraction_schema=invoice_schema
    )

    result = service.extract_from_document("invoice.pdf")
    print(json.dumps(result["extraction"], indent=2))
```

---

## Key Files in This Codebase

| File | Description |
|------|-------------|
| `backend/src/core/servicios/comprehensive_financial_extraction_service.py` | Financial statement extraction (1277 lines) |
| `backend/src/core/servicios/import_extraction_service.py` | Import data extraction (845 lines) |
| `backend/src/core/servicios/period_extraction_service.py` | Period/date extraction (1093 lines) |
| `backend/src/interface/dtos/comprehensive_financial_metrics_dto.py` | Financial metrics DTO |
| `backend/src/interface/import_dto.py` | Import data DTO |
| `backend/src/config/settings.py` | API configuration |

---

## Summary

1. **ADE Parse** converts documents to markdown (preserves tables, structure)
2. **ADE Extract** uses JSON schema to extract structured data from markdown
3. **HTTP 206** is acceptable - indicates partial success with nullable fields
4. **3-tier fallback** ensures reliability (ADE → GPT-4 Vision → Pattern Matching)
5. **Validate extraction** to catch accounting/logical errors
6. **Cache results** to avoid re-extraction costs

For questions or issues, refer to the LandingAI documentation or the implementation files listed above.
