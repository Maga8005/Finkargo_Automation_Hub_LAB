# LLM-Powered Email Extraction for Riesgos Module

## Overview

This document describes the implementation of OpenAI GPT-4o powered entity extraction in the Riesgos (Risk/Fraud Detection) module. When enabled via a configurable setting, AI extraction replaces regex-based extraction for company names, NITs, representative names, and domains from email bodies.

## Problem Statement

The current email chain validation system uses regex patterns to extract entities from email text. These patterns produce false positives because:

1. **Company name regex** captures any capitalized phrase ending with legal suffix (S.A.S., LTDA, etc.)
2. **Representative name extraction** captures text after keywords but can extract wrong phrases
3. **Email formats vary significantly** - informal emails, forwarded threads, signatures all have different structures

## Solution

Use OpenAI GPT-4o with structured output to intelligently extract entities from email text. The LLM can:
- Understand context and distinguish between actual company names vs. generic references
- Handle varied email formats (forwards, replies, signatures)
- Reduce false positives by understanding Spanish business terminology

## Architecture

### Toggle Mechanism

A new `risk_settings` database table stores the configuration:

```sql
risk_settings (
    id UUID PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    value_type VARCHAR(20),  -- 'boolean', 'number', 'text', 'json'
    description TEXT,
    updated_at TIMESTAMPTZ,
    updated_by UUID REFERENCES user_profiles(id)
)
```

Default setting: `ai_email_extraction_enabled = false`

### Data Flow

```
1. User uploads email chain
2. System checks risk_settings.ai_email_extraction_enabled
3. If enabled:
   - Call OpenAI GPT-4o with email text
   - Parse structured JSON response
   - Set extraction_method = "ai"
4. If disabled or API fails:
   - Use regex extraction
   - Set extraction_method = "regex" or "regex_fallback"
5. Store extraction_method in parsed_data.mentions
6. During validation, propagate to validation_result.ai_assisted
```

### Tracking AI Usage

**In parsed_data (extraction phase):**
```json
{
  "messages": [...],
  "mentions": {
    "company_names": ["AZELIS COLOMBIA S.A.S."],
    "nits": ["830027231-3"],
    "representative_names": ["Juan Carlos Perez"],
    "domains": ["azelis.com.co"],
    "extraction_method": "ai"
  },
  "parse_errors": []
}
```

**In validation_result (validation phase):**
```json
{
  "total_discrepancies": 2,
  "discrepancies": [...],
  "summary": "...",
  "validated_at": "2025-12-28T...",
  "ai_assisted": true,
  "extraction_method": "ai"
}
```

## Implementation Details

### 1. Database Migration

**File:** `backend/database/migration_add_risk_settings.sql`

```sql
-- Migration: Add risk_settings table for module configuration
-- Date: 2025-12-28
-- Description: Creates key-value configuration table for risk module settings

CREATE TABLE IF NOT EXISTS risk_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    value_type VARCHAR(20) NOT NULL CHECK (value_type IN ('boolean', 'number', 'text', 'json')),
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES user_profiles(id)
);

-- Create index on setting_key for fast lookups
CREATE INDEX IF NOT EXISTS idx_risk_settings_key ON risk_settings(setting_key);

-- Enable RLS
ALTER TABLE risk_settings ENABLE ROW LEVEL SECURITY;

-- RLS: Authenticated users can read settings
CREATE POLICY "Authenticated users can read risk_settings"
ON risk_settings FOR SELECT
TO authenticated
USING (TRUE);

-- RLS: Authenticated users can update (role check enforced at API layer)
CREATE POLICY "Authenticated users can update risk_settings"
ON risk_settings FOR UPDATE
TO authenticated
USING (TRUE)
WITH CHECK (TRUE);

-- Service role full access
CREATE POLICY "Service role has full access to risk_settings"
ON risk_settings FOR ALL
TO service_role
USING (TRUE)
WITH CHECK (TRUE);

-- Insert default setting: AI email extraction disabled
INSERT INTO risk_settings (setting_key, setting_value, value_type, description)
VALUES (
    'ai_email_extraction_enabled',
    'false'::jsonb,
    'boolean',
    'When enabled, uses OpenAI GPT-4o for extracting entities from email bodies instead of regex patterns. Reduces false positives in company name and representative name detection.'
) ON CONFLICT (setting_key) DO NOTHING;

-- Comments
COMMENT ON TABLE risk_settings IS 'Key-value configuration settings for the risk/fraud detection module';
COMMENT ON COLUMN risk_settings.setting_key IS 'Unique identifier for the setting';
COMMENT ON COLUMN risk_settings.setting_value IS 'JSON value of the setting';
COMMENT ON COLUMN risk_settings.value_type IS 'Data type hint: boolean, number, text, json';
```

### 2. Backend Configuration

**File:** `backend/src/config/settings.py`

Add after line 66 (before `class Config`):

```python
    # OpenAI Configuration (for AI-powered extraction)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TIMEOUT: int = 30  # seconds
```

### 3. Dependencies

**File:** `backend/requirements.txt`

Add:
```
# OpenAI for AI-powered extraction
openai>=1.0.0
```

### 4. Risk Settings Repository

**File:** `backend/src/repositorio/risk_settings_repository.py`

```python
"""
Risk Settings Repository - Database operations for risk module configuration
"""
from typing import Optional, List
from supabase import Client
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class RiskSettingsRepository:
    """Repository for risk_settings table operations"""

    def __init__(self, supabase_client: Client):
        self.db = supabase_client

    async def get_setting(self, key: str) -> Optional[dict]:
        """Get a setting by key"""
        response = self.db.table('risk_settings') \
            .select('*') \
            .eq('setting_key', key) \
            .execute()
        return response.data[0] if response.data else None

    async def get_all_settings(self) -> List[dict]:
        """Get all settings"""
        response = self.db.table('risk_settings') \
            .select('*') \
            .order('setting_key') \
            .execute()
        return response.data if response.data else []

    async def update_setting(
        self,
        key: str,
        value,
        user_id: Optional[str] = None
    ) -> Optional[dict]:
        """Update a setting value"""
        # Serialize value to JSONB-compatible format
        if isinstance(value, bool):
            json_value = value
        elif isinstance(value, (int, float)):
            json_value = value
        elif isinstance(value, str):
            json_value = json.dumps(value)
        else:
            json_value = value  # Already JSON-compatible

        updates = {
            'setting_value': json_value,
            'updated_at': datetime.utcnow().isoformat(),
        }
        if user_id:
            updates['updated_by'] = user_id

        response = self.db.table('risk_settings') \
            .update(updates) \
            .eq('setting_key', key) \
            .execute()

        return response.data[0] if response.data else None

    async def is_ai_extraction_enabled(self) -> bool:
        """Check if AI email extraction is enabled"""
        setting = await self.get_setting('ai_email_extraction_enabled')
        if not setting:
            return False
        value = setting.get('setting_value')
        if isinstance(value, bool):
            return value
        return value == True or value == 'true'
```

### 5. OpenAI Extraction Service

**File:** `backend/src/core/servicios/risk/openai_extraction_service.py`

```python
"""
OpenAI Extraction Service - LLM-powered entity extraction from email text

Uses GPT-4o with structured output to extract:
- Company names
- NITs (Colombian tax IDs)
- Representative names
- Email domains
"""
import logging
import json
from typing import Optional
from openai import OpenAI, OpenAIError
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAIExtractionService:
    """
    Service for extracting entities from email text using OpenAI GPT-4o.

    Replaces regex-based extraction when AI mode is enabled.
    Provides structured output matching the existing mentions format.
    """

    EXTRACTION_PROMPT = """You are an expert at extracting business entities from email correspondence in Spanish and English.

Analyze the following email text and extract:
1. **Company Names**: Any business/company names mentioned (e.g., "AZELIS COLOMBIA S.A.S.", "Finkargo", etc.)
2. **NITs**: Colombian tax identification numbers in any format (e.g., "830.027.231-3", "830027231", "901854687-2")
3. **Representative Names**: Names of legal representatives, gerentes, directors, CEOs mentioned
4. **Email Domains**: Corporate email domains found (exclude free providers like gmail.com, hotmail.com, outlook.com, yahoo.com)

Return a JSON object with exactly these keys:
{
  "company_names": ["Company Name 1", "Company Name 2"],
  "nits": ["830027231-3", "901854687-2"],
  "representative_names": ["Juan Carlos Perez", "Maria Garcia"],
  "domains": ["empresa.com.co", "azelis.com"]
}

Rules:
- Only include entities actually found in the text
- Normalize NITs by removing dots but keeping the check digit (e.g., "830.027.231-3" -> "830027231-3")
- For company names, include the legal suffix if present (S.A.S., LTDA, etc.)
- For domains, extract only the domain part (not full email addresses)
- Return empty arrays [] if no entities of that type are found
- Do NOT invent or hallucinate entities - only extract what is explicitly in the text

Email text to analyze:
---
{email_text}
---

Respond with ONLY the JSON object, no additional text."""

    def __init__(self):
        """Initialize OpenAI client with settings"""
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.timeout = settings.OPENAI_TIMEOUT

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured - AI extraction unavailable")

    def is_available(self) -> bool:
        """Check if OpenAI service is configured and available"""
        return self.client is not None and bool(self.api_key)

    async def extract_entities(self, email_text: str) -> dict:
        """
        Extract entities from email text using GPT-4o.

        Args:
            email_text: Raw email body text

        Returns:
            dict: Extracted entities matching the mentions structure:
                  {company_names, nits, representative_names, domains}

        Raises:
            OpenAIError: If API call fails
        """
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")

        if not email_text or not email_text.strip():
            return {
                'company_names': [],
                'nits': [],
                'representative_names': [],
                'domains': [],
            }

        # Truncate very long emails to stay within token limits
        max_chars = 15000  # Approximately 4K tokens
        truncated_text = email_text[:max_chars] if len(email_text) > max_chars else email_text

        try:
            logger.info(f"Calling OpenAI GPT-4o for entity extraction ({len(truncated_text)} chars)")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an entity extraction assistant. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": self.EXTRACTION_PROMPT.format(email_text=truncated_text)
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}  # Enforce JSON output
            )

            # Parse response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content}")

            result = json.loads(content)

            # Validate structure
            validated = {
                'company_names': result.get('company_names', []) or [],
                'nits': result.get('nits', []) or [],
                'representative_names': result.get('representative_names', []) or [],
                'domains': result.get('domains', []) or [],
            }

            # Ensure all values are lists
            for key in validated:
                if not isinstance(validated[key], list):
                    validated[key] = [validated[key]] if validated[key] else []

            logger.info(
                f"OpenAI extraction complete: "
                f"{len(validated['company_names'])} companies, "
                f"{len(validated['nits'])} NITs, "
                f"{len(validated['representative_names'])} reps, "
                f"{len(validated['domains'])} domains"
            )

            return validated

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI extraction: {e}", exc_info=True)
            raise
```

### 6. Email Chain Parser Service Updates

**File:** `backend/src/core/servicios/risk/email_chain_parser_service.py`

#### Add import at top:
```python
from src.core.servicios.risk.openai_extraction_service import OpenAIExtractionService
```

#### Modify `__init__` method:
```python
def __init__(self, use_ai_extraction: bool = False):
    """
    Initialize parser service.

    Args:
        use_ai_extraction: If True, use OpenAI for entity extraction instead of regex
    """
    self.use_ai_extraction = use_ai_extraction
    self.openai_service = None

    if use_ai_extraction:
        self.openai_service = OpenAIExtractionService()
        if not self.openai_service.is_available():
            logger.warning("AI extraction requested but OpenAI not available - falling back to regex")
            self.use_ai_extraction = False
```

#### Replace `_extract_mentions_from_body` method:
```python
def _extract_mentions_from_body(self, body: str) -> dict:
    """
    Extract company names, NITs, and representative names from email body.

    Uses either AI (OpenAI GPT-4o) or regex extraction based on configuration.

    Args:
        body: Email body text

    Returns:
        dict: Extracted mentions with extraction_method indicator
    """
    if self.use_ai_extraction and self.openai_service:
        return self._extract_mentions_with_ai(body)
    else:
        return self._extract_mentions_with_regex(body)

def _extract_mentions_with_ai(self, body: str) -> dict:
    """
    Extract mentions using OpenAI GPT-4o.

    Falls back to regex if AI extraction fails.
    """
    try:
        import asyncio

        # Run async extraction (handle both sync and async contexts)
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.openai_service.extract_entities(body)
                )
                mentions = future.result(timeout=self.openai_service.timeout + 5)
        except RuntimeError:
            # No running loop, we can use asyncio.run directly
            mentions = asyncio.run(self.openai_service.extract_entities(body))

        mentions['extraction_method'] = 'ai'
        logger.info("Successfully extracted mentions using AI")
        return mentions

    except Exception as e:
        logger.warning(f"AI extraction failed, falling back to regex: {e}")
        mentions = self._extract_mentions_with_regex(body)
        mentions['extraction_method'] = 'regex_fallback'
        return mentions

def _extract_mentions_with_regex(self, body: str) -> dict:
    """
    Extract mentions using regex patterns (original implementation).
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

    # Extract NITs (existing logic)
    nit_matches = re.findall(self.NIT_PATTERN, body)
    for nit in nit_matches:
        normalized = re.sub(r'[.\s]', '', nit)
        if self.is_colombian_cellphone(normalized):
            continue
        if normalized not in mentions['nits']:
            mentions['nits'].append(normalized)

    # Extract representative names (existing logic)
    for keyword in self.REP_KEYWORDS:
        pattern = rf'{keyword}[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)'
        matches = re.findall(pattern, body, re.IGNORECASE)
        for name in matches:
            name = name.strip()
            if len(name) > 3 and name not in mentions['representative_names']:
                mentions['representative_names'].append(name)

    # Extract email domains (existing logic)
    email_matches = re.findall(r'[\w.+-]+@([\w.-]+\.\w+)', body, re.IGNORECASE)
    for domain in email_matches:
        domain = domain.lower()
        if domain not in mentions['domains'] and domain not in self.FREE_PROVIDERS:
            mentions['domains'].append(domain)

    # Extract company names (existing logic)
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
```

### 7. Email Chain Service Updates

**File:** `backend/src/core/servicios/risk/email_chain_service.py`

#### Add import:
```python
from src.repositorio.risk_settings_repository import RiskSettingsRepository
```

#### Modify `__init__`:
```python
def __init__(
    self,
    chain_repo: EmailChainRepository,
    assessment_repo: RiskAssessmentRepository,
    extraction_repo: DocumentExtractionRepository,
    settings_repo: Optional[RiskSettingsRepository] = None,
):
    """Initialize service with repository dependencies."""
    self.chain_repo = chain_repo
    self.assessment_repo = assessment_repo
    self.extraction_repo = extraction_repo
    self.settings_repo = settings_repo

    self.typosquatting_service = TyposquattingService()
    self.normalization_service = NormalizationService()
    self.domain_validator = DomainValidationService()

async def _get_parser_service(self) -> EmailChainParserService:
    """Get parser service with current AI extraction setting"""
    use_ai = False
    if self.settings_repo:
        use_ai = await self.settings_repo.is_ai_extraction_enabled()
    return EmailChainParserService(use_ai_extraction=use_ai)
```

#### Update `upload_email_chain` to use dynamic parser:
```python
# Replace: parser_service = EmailChainParserService()
# With:
parser_service = await self._get_parser_service()
```

#### Update `validate_email_chain` to add ai_assisted:
```python
# After building discrepancies list, before creating validation_result:
extraction_method = parsed_data.get('mentions', {}).get('extraction_method', 'regex')
ai_assisted = extraction_method in ('ai', 'regex_fallback')

validation_result = {
    'total_discrepancies': actual_discrepancy_count,
    'info_count': info_count,
    'critical_count': critical_count,
    'high_count': high_count,
    'medium_count': medium_count,
    'low_count': low_count,
    'discrepancies': discrepancies,
    'summary': summary,
    'validated_at': datetime.now(timezone.utc).isoformat(),
    'ai_assisted': ai_assisted,
    'extraction_method': extraction_method,
}
```

### 8. API Endpoints

**File:** `backend/src/adapter/rest/risk_routes.py`

#### Add import:
```python
from src.repositorio.risk_settings_repository import RiskSettingsRepository
```

#### Add dependency factory:
```python
def get_settings_repo():
    """Get risk settings repository"""
    supabase = get_supabase()
    return RiskSettingsRepository(supabase.admin_client)
```

#### Update `get_email_chain_service`:
```python
def get_email_chain_service():
    """Get email chain service"""
    return EmailChainService(
        chain_repo=get_email_chain_repo(),
        assessment_repo=get_risk_repo(),
        extraction_repo=get_extraction_repo(),
        settings_repo=get_settings_repo(),
    )
```

#### Add settings endpoints:
```python
# ==================== Settings Endpoints ====================

@router.get("/settings")
async def get_risk_settings(
    current_user: dict = Depends(require_roles(['admin', 'risk_manager', 'risk_analyst']))
):
    """
    Get all risk module settings.
    Requires admin, risk_manager, or risk_analyst role.
    """
    logger.info("Getting risk settings")

    repo = get_settings_repo()
    settings = await repo.get_all_settings()

    return {
        "settings": [
            {
                "key": s['setting_key'],
                "value": s['setting_value'],
                "type": s['value_type'],
                "description": s.get('description'),
                "updated_at": s.get('updated_at'),
            }
            for s in settings
        ]
    }


@router.put("/settings/{key}")
async def update_risk_setting(
    key: str,
    value: bool,
    current_user: dict = Depends(require_roles(['admin', 'risk_manager']))
):
    """
    Update a risk module setting.
    Only admin or risk_manager can update settings.
    """
    logger.info(f"Updating risk setting: {key} = {value}")

    user_id = current_user.get('id')

    repo = get_settings_repo()

    # Verify setting exists
    existing = await repo.get_setting(key)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    # Update setting
    updated = await repo.update_setting(key, value, user_id)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update setting"
        )

    logger.info(f"Setting '{key}' updated to {value} by user {user_id}")

    return {
        "key": updated['setting_key'],
        "value": updated['setting_value'],
        "updated_at": updated['updated_at'],
        "updated_by": updated.get('updated_by'),
    }
```

## API Reference

### Settings Endpoints

| Endpoint | Method | Roles | Description |
|----------|--------|-------|-------------|
| `/api/risk/settings` | GET | admin, risk_manager, risk_analyst | List all settings |
| `/api/risk/settings/{key}` | PUT | admin, risk_manager | Update a setting |

### Response Examples

**GET /api/risk/settings:**
```json
{
  "settings": [
    {
      "key": "ai_email_extraction_enabled",
      "value": false,
      "type": "boolean",
      "description": "When enabled, uses OpenAI GPT-4o for extracting entities...",
      "updated_at": "2025-12-28T10:00:00Z"
    }
  ]
}
```

**PUT /api/risk/settings/ai_email_extraction_enabled:**
```json
{
  "key": "ai_email_extraction_enabled",
  "value": true,
  "updated_at": "2025-12-28T10:05:00Z",
  "updated_by": "user-uuid-here"
}
```

## Cost Considerations

Using GPT-4o for extraction:
- **Input**: ~$2.50 per 1M tokens
- **Output**: ~$10.00 per 1M tokens
- **Typical email**: 500-2000 tokens input, ~100 tokens output
- **Estimated cost per email**: ~$0.002-0.005

## Fallback Behavior

When AI extraction is enabled but fails:
1. Log warning with error details
2. Fall back to regex extraction
3. Set `extraction_method: "regex_fallback"`
4. Set `ai_assisted: false` in validation_result

Fallback triggers include:
- OpenAI API timeout
- Rate limiting
- Invalid JSON response
- Network errors

## Testing Checklist

- [ ] AI extraction returns correct entities for sample emails
- [ ] Toggle enables/disables AI extraction
- [ ] Fallback to regex works when OpenAI API fails
- [ ] `extraction_method` tracked in `parsed_data.mentions`
- [ ] `ai_assisted` tracked in `validation_result`
- [ ] Only admin/risk_manager can update settings
- [ ] Settings persist across requests

## Environment Variables

Ensure these are set in `backend/.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o  # Optional, defaults to gpt-4o
```

## Migration Sequence

1. Run database migration in Supabase SQL Editor
2. Add `openai>=1.0.0` to requirements.txt
3. Install dependencies: `pip install -r requirements.txt`
4. Add OpenAI settings to `settings.py`
5. Create `risk_settings_repository.py`
6. Create `openai_extraction_service.py`
7. Update `email_chain_parser_service.py`
8. Update `email_chain_service.py`
9. Add endpoints to `risk_routes.py`
10. Restart backend server
11. Enable AI extraction via API: `PUT /api/risk/settings/ai_email_extraction_enabled` with `value: true`
