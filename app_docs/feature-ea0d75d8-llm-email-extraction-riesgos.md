# LLM-Powered Email Extraction for Riesgos Module

**ADW ID:** ea0d75d8
**Date:** 2025-12-28
**Specification:** specs/issue-50-adw-ea0d75d8-sdlc_planner-llm-email-extraction-riesgos.md

## Overview

This feature implements OpenAI GPT-4o powered entity extraction in the Riesgos (Risk/Fraud Detection) module. When enabled via a database toggle, AI extraction replaces regex-based extraction for company names, NITs, representative names, and email domains from email chains, providing better accuracy and reduced false positives.

## What Was Built

- **OpenAI Extraction Service**: New service using GPT-4o with structured JSON output for intelligent entity extraction
- **Risk Settings Repository**: Database layer for managing configurable risk module settings
- **Settings API Endpoints**: REST endpoints to view and update AI extraction toggle
- **Parser Service Updates**: Modified to support dual extraction modes (AI vs regex) with automatic fallback
- **Extraction Tracking**: Added `extraction_method` and `ai_assisted` fields to track how entities were extracted
- **Database Migration**: New `risk_settings` table for storing module configuration

## Technical Implementation

### Files Modified

- `backend/src/adapter/rest/risk_routes.py`: Added settings endpoints (GET/PUT `/api/risk/settings`) and updated service factory
- `backend/src/core/servicios/risk/email_chain_parser_service.py`: Added AI extraction mode with fallback to regex
- `backend/src/core/servicios/risk/email_chain_service.py`: Injected settings repository and added AI extraction tracking
- `backend/src/interface/risk_dtos.py`: Added `extraction_method` and `ai_assisted` fields to DTOs
- `backend/src/config/settings.py`: Added OpenAI configuration variables
- `backend/requirements.txt`: Added `openai>=1.0.0` dependency

### New Files

- `backend/src/core/servicios/risk/openai_extraction_service.py`: OpenAI GPT-4o extraction service
- `backend/src/repositorio/risk_settings_repository.py`: Repository for risk settings CRUD
- `backend/database/migration_add_risk_settings.sql`: Database migration for risk_settings table
- `.claude/commands/e2e/test_llm_email_extraction.md`: E2E test for AI extraction feature

### Key Changes

- **Dual Extraction Modes**: Parser service now supports `use_ai_extraction` parameter to choose between AI and regex extraction
- **Automatic Fallback**: When AI extraction fails (timeout, API error, invalid response), system automatically falls back to regex with `extraction_method: "regex_fallback"`
- **Role-Based Settings Access**: GET settings requires `risk_analyst`, `risk_manager`, or `admin`; PUT requires `risk_manager` or `admin`
- **Text Truncation**: AI service truncates email text to 15,000 characters (~3,750 tokens) to stay within limits
- **Extraction Tracking**: Validation results now include `extraction_method` ("ai", "regex", "regex_fallback") and `ai_assisted` boolean

## How to Use

1. **Apply Database Migration**:
   - Execute `backend/database/migration_add_risk_settings.sql` in Supabase SQL Editor
   - This creates the `risk_settings` table with default `ai_email_extraction_enabled = false`

2. **Configure Environment**:
   ```bash
   # Add to backend/.env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   OPENAI_MODEL=gpt-4o              # Optional, defaults to gpt-4o
   OPENAI_MAX_TOKENS=2000           # Optional
   OPENAI_TIMEOUT=30                # Optional, seconds
   ```

3. **Enable AI Extraction**:
   ```bash
   # Via API (requires risk_manager or admin role)
   curl -X PUT "http://localhost:8003/api/risk/settings/ai_email_extraction_enabled?value=true" \
     -H "Authorization: Bearer <token>"
   ```

4. **View Current Settings**:
   ```bash
   curl "http://localhost:8003/api/risk/settings" \
     -H "Authorization: Bearer <token>"
   ```

5. **Upload Email Chains**: When AI extraction is enabled, email chain uploads will automatically use GPT-4o for entity extraction

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENAI_API_KEY` | None | Required for AI extraction |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `OPENAI_MAX_TOKENS` | `2000` | Max tokens for response |
| `OPENAI_TIMEOUT` | `30` | Request timeout in seconds |

| Database Setting | Default | Description |
|------------------|---------|-------------|
| `ai_email_extraction_enabled` | `false` | Toggle AI extraction on/off |

## Testing

1. **Backend Tests**:
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

2. **E2E Test**:
   Run `.claude/commands/e2e/test_llm_email_extraction.md` to validate:
   - Settings toggle via API
   - AI extraction with enabled setting
   - Fallback to regex when AI fails
   - Extraction method tracking in results

3. **Manual API Validation**:
   ```bash
   # Start server
   cd backend && python -m uvicorn main:app --reload --port 8003

   # Test settings endpoint
   curl http://localhost:8003/api/risk/settings
   ```

## Notes

### Cost Considerations
- GPT-4o pricing: ~$2.50/1M input tokens, ~$10.00/1M output tokens
- Typical email: 500-2000 tokens input, ~100 tokens output
- Estimated cost per email: ~$0.002-0.005

### Extraction Method Values
- `ai`: Extraction performed successfully using OpenAI GPT-4o
- `regex`: Standard regex-based extraction (AI disabled or unavailable)
- `regex_fallback`: AI extraction attempted but failed, fell back to regex

### API Endpoints Added
- `GET /api/risk/settings`: List all risk settings (risk_analyst, risk_manager, admin)
- `GET /api/risk/settings/{key}`: Get specific setting value
- `PUT /api/risk/settings/{key}?value=<bool>`: Update setting (risk_manager, admin only)

### Future Enhancements
- Frontend settings panel for toggling AI extraction
- Cost tracking per email/day
- Prompt optimization based on extraction accuracy metrics
