# Feature: LLM-Powered Email Extraction for Riesgos Module

## Feature Description

This feature implements OpenAI GPT-4o powered entity extraction in the Riesgos (Risk/Fraud Detection) module. When enabled via a configurable database setting, AI extraction replaces the existing regex-based extraction for:
- Company names
- NITs (Colombian tax IDs)
- Representative names
- Email domains

The AI extraction provides:
- Better context understanding to distinguish actual company names vs. generic references
- Handling of varied email formats (forwards, replies, signatures)
- Reduced false positives by understanding Spanish business terminology
- Graceful fallback to regex extraction when OpenAI API fails

## User Story

As a Risk Analyst
I want to use AI-powered entity extraction from email chains
So that I can reduce false positives and get more accurate fraud detection results when validating email correspondence against document-extracted data

## Problem Statement

The current email chain validation system uses regex patterns to extract entities from email text. These patterns produce false positives because:

1. **Company name regex** captures any capitalized phrase ending with legal suffix (S.A.S., LTDA, etc.)
2. **Representative name extraction** captures text after keywords but can extract wrong phrases
3. **Email formats vary significantly** - informal emails, forwarded threads, signatures all have different structures

## Solution Statement

Implement OpenAI GPT-4o with structured JSON output to intelligently extract entities from email text. The solution includes:

1. **Database toggle**: A `risk_settings` table to enable/disable AI extraction per-environment
2. **OpenAI extraction service**: New service that calls GPT-4o with a structured prompt
3. **Fallback mechanism**: Automatic fallback to regex if OpenAI fails
4. **Tracking**: Store `extraction_method` in parsed_data and `ai_assisted` in validation_result
5. **Settings API**: Endpoints to view and update the AI extraction toggle

## Access Control

- Required Role(s): `admin`, `risk_manager` for updating settings; `risk_analyst` for viewing settings
- Backend Protection: Use `require_roles(['admin', 'risk_manager'])` from `rbac_dependencies.py` for PUT endpoint
- Frontend Protection: Not applicable for this feature (backend-only toggle, no UI component needed initially)

## Relevant Files

### Backend - Core Services
- `backend/src/core/servicios/risk/email_chain_parser_service.py` - Modify to support AI extraction mode with fallback to regex
- `backend/src/core/servicios/risk/email_chain_service.py` - Modify to inject settings repository and check AI extraction setting
- `backend/src/core/servicios/risk/normalization_service.py` - Reference for understanding existing normalization patterns

### Backend - Repository Layer
- `backend/src/repositorio/risk_repository.py` - Reference for repository patterns (contains EmailChainRepository)

### Backend - API Layer
- `backend/src/adapter/rest/risk_routes.py` - Add settings endpoints and update service factory
- `backend/src/adapter/rest/rbac_dependencies.py` - Reference for role-based access control

### Backend - DTOs
- `backend/src/interface/risk_dtos.py` - Add AI extraction fields to ExtractedMentions and EmailChainValidationResult DTOs

### Backend - Configuration
- `backend/src/config/settings.py` - Add OpenAI configuration variables
- `backend/requirements.txt` - Add openai dependency

### Database
- `backend/database/` - Location for migration file

### E2E Testing
- `.claude/commands/test_e2e.md` - Reference for E2E test structure
- `.claude/commands/e2e/test_email_chain_validation.md` - Existing email chain E2E test to extend

### New Files

- `backend/database/migration_add_risk_settings.sql` - Database migration for risk_settings table
- `backend/src/repositorio/risk_settings_repository.py` - Repository for risk_settings CRUD operations
- `backend/src/core/servicios/risk/openai_extraction_service.py` - OpenAI GPT-4o extraction service
- `.claude/commands/e2e/test_llm_email_extraction.md` - E2E test for AI extraction feature

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| risk_settings_repo.get_setting() | Optional[dict] | data['setting_value'] | Not data.setting_value |
| risk_settings_repo.get_all_settings() | List[dict] | data[0]['setting_key'] | Iterate as list of dicts |
| risk_settings_repo.update_setting() | Optional[dict] | data['setting_value'] | Returns updated dict |
| risk_settings_repo.is_ai_extraction_enabled() | bool | Direct return | True/False |
| email_chain_repo.get_by_id() | Optional[dict] | data['parsed_data'] | Access as dict |
| email_chain_repo.update() | Optional[dict] | data['validation_result'] | Access as dict |

### F. External API Contract (Integration only)

| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| OpenAI Chat Completions | POST | Bearer Token (OPENAI_API_KEY) | JSON | JSON |

**OpenAI Request Structure:**
```python
{
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    "max_tokens": 2000,
    "temperature": 0.1,
    "response_format": {"type": "json_object"}
}
```

**Expected OpenAI Response:**
```json
{
    "company_names": ["AZELIS COLOMBIA S.A.S."],
    "nits": ["830027231-3"],
    "representative_names": ["Juan Carlos Perez"],
    "domains": ["azelis.com.co"]
}
```

**Error Handling Strategy:**
- Timeout: 30 seconds default, configurable via OPENAI_TIMEOUT
- Rate limiting: Fall back to regex extraction
- Invalid JSON response: Fall back to regex extraction
- Network errors: Fall back to regex extraction
- All fallbacks set `extraction_method: "regex_fallback"`

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| N/A | extraction_method | string | Values: "ai", "regex", "regex_fallback" |
| N/A | ai_assisted | boolean | True if extraction_method is "ai" or "regex_fallback" |
| setting_key | setting_key | string | e.g., "ai_email_extraction_enabled" |
| setting_value | setting_value | boolean (JSONB) | Stored as JSONB in database |
| value_type | value_type | string | "boolean", "number", "text", "json" |

## Implementation Plan

### Phase 1: Foundation

1. **Database Migration**
   - Create `risk_settings` table with UUID primary key
   - Add RLS policies for authenticated users
   - Insert default setting: `ai_email_extraction_enabled = false`

2. **OpenAI Configuration**
   - Add OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS, OPENAI_TIMEOUT to settings.py
   - Add openai>=1.0.0 to requirements.txt

3. **Risk Settings Repository**
   - Create repository with get_setting, get_all_settings, update_setting, is_ai_extraction_enabled methods

### Phase 2: Core Implementation

4. **OpenAI Extraction Service**
   - Create service with EXTRACTION_PROMPT template
   - Implement extract_entities method with structured output
   - Handle token limits (truncate at 15000 chars)
   - Implement is_available check for API key

5. **Email Chain Parser Service Updates**
   - Add use_ai_extraction parameter to __init__
   - Split _extract_mentions_from_body into:
     - _extract_mentions_with_ai (calls OpenAI service)
     - _extract_mentions_with_regex (existing logic)
   - Add extraction_method field to mentions dict

6. **Email Chain Service Updates**
   - Inject RiskSettingsRepository dependency
   - Add _get_parser_service helper to check settings
   - Update upload_email_chain to use dynamic parser
   - Update validate_email_chain to add ai_assisted field

### Phase 3: Integration

7. **API Endpoints**
   - Add get_settings_repo dependency factory
   - Update get_email_chain_service to inject settings_repo
   - Add GET /api/risk/settings endpoint
   - Add PUT /api/risk/settings/{key} endpoint

8. **DTO Updates**
   - Add extraction_method field to ExtractedMentions
   - Add ai_assisted and extraction_method fields to EmailChainValidationResult

## Step by Step Tasks

### 1. Create Database Migration File

- Create `backend/database/migration_add_risk_settings.sql`
- Include table creation with UUID, setting_key, setting_value (JSONB), value_type, description, updated_at, updated_by
- Add RLS policies for authenticated users
- Insert default setting `ai_email_extraction_enabled = false`
- Add index on setting_key for fast lookups

### 2. Add OpenAI Configuration to Settings

- Read `backend/src/config/settings.py`
- Add OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS, OPENAI_TIMEOUT fields
- Defaults: OPENAI_MODEL="gpt-4o", OPENAI_MAX_TOKENS=2000, OPENAI_TIMEOUT=30

### 3. Update Requirements

- Read `backend/requirements.txt`
- Add `openai>=1.0.0` dependency with comment

### 4. Create Risk Settings Repository

- Create `backend/src/repositorio/risk_settings_repository.py`
- Implement RiskSettingsRepository class with:
  - `__init__(self, supabase_client: Client)`
  - `async get_setting(self, key: str) -> Optional[dict]`
  - `async get_all_settings(self) -> List[dict]`
  - `async update_setting(self, key: str, value, user_id: Optional[str]) -> Optional[dict]`
  - `async is_ai_extraction_enabled(self) -> bool`
- Handle JSONB value serialization

### 5. Create OpenAI Extraction Service

- Create `backend/src/core/servicios/risk/openai_extraction_service.py`
- Implement OpenAIExtractionService class with:
  - EXTRACTION_PROMPT constant with entity extraction instructions
  - `__init__(self)` - Initialize OpenAI client from settings
  - `is_available(self) -> bool` - Check if API key is configured
  - `async extract_entities(self, email_text: str) -> dict` - Call OpenAI and parse response
- Handle text truncation (15000 chars max)
- Use response_format={"type": "json_object"} for structured output
- Validate returned structure matches expected format

### 6. Update Email Chain Parser Service

- Read `backend/src/core/servicios/risk/email_chain_parser_service.py`
- Add import for OpenAIExtractionService
- Modify `__init__` to accept `use_ai_extraction: bool = False`
- Initialize openai_service if use_ai_extraction is True
- Create `_extract_mentions_with_ai(self, body: str) -> dict` method
- Create `_extract_mentions_with_regex(self, body: str) -> dict` method (refactor existing logic)
- Modify `_extract_mentions_from_body` to dispatch to appropriate method
- Add `extraction_method` field to all returned mention dicts

### 7. Update Email Chain Service

- Read `backend/src/core/servicios/risk/email_chain_service.py`
- Add import for RiskSettingsRepository
- Add Optional[RiskSettingsRepository] to `__init__` parameters
- Create `async _get_parser_service(self) -> EmailChainParserService` helper
- Update `upload_email_chain` to use `await self._get_parser_service()`
- Update `validate_email_chain` to:
  - Extract extraction_method from parsed_data.mentions
  - Calculate ai_assisted boolean
  - Add ai_assisted and extraction_method to validation_result dict

### 8. Update DTOs for AI Extraction Fields

- Read `backend/src/interface/risk_dtos.py`
- Add `extraction_method: Optional[str]` to ExtractedMentions class
- Add `ai_assisted: Optional[bool]` to EmailChainValidationResult class
- Add `extraction_method: Optional[str]` to EmailChainValidationResult class
- Add `info_count: int = 0` if not already present

### 9. Add Settings Endpoints to Risk Routes

- Read `backend/src/adapter/rest/risk_routes.py`
- Add import for RiskSettingsRepository
- Add `get_settings_repo()` dependency factory
- Update `get_email_chain_service()` to inject settings_repo
- Add GET `/settings` endpoint (roles: admin, risk_manager, risk_analyst)
- Add PUT `/settings/{key}` endpoint (roles: admin, risk_manager)
- Include proper error handling for not found settings

### 10. Create E2E Test File

- Read `.claude/commands/test_e2e.md` for test structure
- Read `.claude/commands/e2e/test_email_chain_validation.md` for existing email test
- Create `.claude/commands/e2e/test_llm_email_extraction.md` with:
  - Test setting toggle via API
  - Test email extraction with AI enabled
  - Test fallback to regex when AI fails
  - Verify extraction_method tracking
  - Verify ai_assisted field in validation_result

### 11. Run Validation Commands

- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests

- Test OpenAIExtractionService.extract_entities with mock OpenAI responses
- Test OpenAIExtractionService.is_available returns False when no API key
- Test RiskSettingsRepository.is_ai_extraction_enabled with various JSONB values
- Test EmailChainParserService._extract_mentions_with_regex preserves existing behavior
- Test fallback from AI to regex when exception occurs

### Edge Cases

- Empty email text - should return empty arrays
- Very long email text (>15000 chars) - should truncate
- Invalid JSON response from OpenAI - should fall back to regex
- OpenAI timeout - should fall back to regex
- Missing OPENAI_API_KEY - AI service unavailable, use regex
- Malformed NIT values - should handle gracefully
- Email with no entities - should return empty arrays with extraction_method set

## Acceptance Criteria

1. **Toggle Mechanism**: AI extraction can be enabled/disabled via `risk_settings` table
2. **AI Extraction**: When enabled, OpenAI GPT-4o extracts entities from email text
3. **Fallback**: When AI fails, system falls back to regex with `extraction_method: "regex_fallback"`
4. **Tracking**: `extraction_method` is stored in `parsed_data.mentions`
5. **Validation Tracking**: `ai_assisted` and `extraction_method` are stored in `validation_result`
6. **Settings API**: GET /api/risk/settings lists all settings
7. **Settings Update**: PUT /api/risk/settings/{key} updates setting value
8. **Role Protection**: Only admin/risk_manager can update settings
9. **Zero Regressions**: Existing email chain validation continues to work

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Backend linting
cd backend && ruff check src/

# Frontend linting (should have no changes, but verify)
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build

# Manual API validation (requires running server)
# 1. Run database migration in Supabase SQL Editor
# 2. Start backend server: cd backend && python -m uvicorn main:app --reload --port 8003
# 3. Test settings endpoint: curl http://localhost:8003/api/risk/settings
# 4. Test update endpoint: curl -X PUT "http://localhost:8003/api/risk/settings/ai_email_extraction_enabled?value=true"
```

Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_llm_email_extraction.md` to validate the AI extraction functionality works end-to-end.

## Notes

### Dependencies to Add
- `openai>=1.0.0` to `backend/requirements.txt`

### Environment Variables Required
```bash
# Add to backend/.env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o  # Optional, defaults to gpt-4o
OPENAI_MAX_TOKENS=2000  # Optional
OPENAI_TIMEOUT=30  # Optional, seconds
```

### Cost Considerations
- GPT-4o pricing: ~$2.50/1M input tokens, ~$10.00/1M output tokens
- Typical email: 500-2000 tokens input, ~100 tokens output
- Estimated cost per email: ~$0.002-0.005

### Migration Sequence
1. Apply database migration in Supabase SQL Editor
2. Add openai dependency and install
3. Deploy backend changes
4. Enable AI extraction via API when ready

### Future Enhancements
- Frontend settings panel for toggling AI extraction
- Cost tracking per email/day
- Prompt optimization based on extraction accuracy metrics

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness

**API Integration:**
- [x] External API contract documented (OpenAI Chat Completions)
- [x] Auth method specified (Bearer Token via OPENAI_API_KEY)
- [x] Error/retry strategy defined (fallback to regex)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [ ] Country-specific variations handled (CO vs MX) if applicable - N/A for this feature

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
