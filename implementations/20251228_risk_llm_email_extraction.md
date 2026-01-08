# Implementation Report: LLM Email Extraction for Riesgos Module

**Date:** 2025-12-28
**Feature:** Issue #50 - ADW LLM Email Extraction for Riesgos Module
**Branch:** feature-issue-50-adw-ea0d75d8-llm-email-extraction-riesgos

## Summary

Implemented AI-powered entity extraction from email chains in the Fraud Risk (Riesgos) module using OpenAI GPT-4o. This provides more accurate extraction of company names, NITs, representative names, and corporate email domains compared to regex-based extraction.

## Changes Implemented

### Backend

- **Database Migration** (`backend/database/migration_add_risk_settings.sql`)
  - Created `risk_settings` table for configurable module settings
  - Added default setting `ai_email_extraction_enabled` (default: false)
  - Row Level Security policies applied

- **Configuration** (`backend/src/config/settings.py`)
  - Added OpenAI configuration settings:
    - `OPENAI_API_KEY`: API key for authentication
    - `OPENAI_MODEL`: Model to use (default: gpt-4o)
    - `OPENAI_MAX_TOKENS`: Max response tokens (default: 2000)
    - `OPENAI_TIMEOUT`: Request timeout in seconds (default: 30)

- **Dependencies** (`backend/requirements.txt`)
  - Added `openai>=1.0.0` for OpenAI API access

- **New Repository** (`backend/src/repositorio/risk_settings_repository.py`)
  - CRUD operations for risk settings
  - Helper method `is_ai_extraction_enabled()` for toggle check

- **New Service** (`backend/src/core/servicios/risk/openai_extraction_service.py`)
  - `OpenAIExtractionService` class for AI-powered extraction
  - Spanish prompt optimized for Colombian business context
  - JSON response format with structured output
  - Validation and normalization of extracted entities

- **Updated Service** (`backend/src/core/servicios/risk/email_chain_parser_service.py`)
  - Added constructor parameter `use_ai_extraction`
  - New `_extract_mentions_with_ai()` method
  - Refactored `_extract_mentions_with_regex()` method
  - Fallback logic: AI → regex_fallback if AI fails

- **Updated Service** (`backend/src/core/servicios/risk/email_chain_service.py`)
  - Added `settings_repo` dependency injection
  - Dynamic parser service creation based on database setting
  - Added `extraction_method` and `ai_assisted` to validation results

- **Updated DTOs** (`backend/src/interface/risk_dtos.py`)
  - `ExtractedMentions`: Added `extraction_method` field
  - `EmailChainValidationResult`: Added `extraction_method`, `ai_assisted`, `info_count` fields

- **API Endpoints** (`backend/src/adapter/rest/risk_routes.py`)
  - `GET /api/risk/settings` - List all settings
  - `GET /api/risk/settings/{key}` - Get specific setting
  - `PUT /api/risk/settings/{key}` - Update setting (admin/risk_manager only)
  - Updated helper functions for AI extraction fields in responses

### E2E Test

- **Test File** (`.claude/commands/e2e/test_llm_email_extraction.md`)
  - Comprehensive test coverage for:
    - Settings API endpoints
    - AI extraction toggle
    - Email upload with AI extraction
    - Validation results with AI metadata
    - Entity extraction quality comparison
    - Role-based access control

## Discrepancies Found

**None.** The plan accurately reflected the codebase structure and no corrections were needed.

## Git Statistics

```
 backend/requirements.txt                           |   3 +
 backend/src/adapter/rest/risk_routes.py            |  96 +++++++++++++
 backend/src/config/settings.py                     |   6 ++
 .../servicios/risk/email_chain_parser_service.py   | 115 +++++++++++++
 .../src/core/servicios/risk/email_chain_service.py |  46 ++++++
 backend/src/interface/risk_dtos.py                 |  13 +++
 6 files changed, 273 insertions(+), 6 deletions(-)

 New files:
 backend/database/migration_add_risk_settings.sql   |  68 lines
 backend/src/core/servicios/risk/openai_extraction_service.py | 238 lines
 backend/src/repositorio/risk_settings_repository.py | 153 lines

 Total: 9 files, ~732 lines added
```

## Pre-requisites Before Use

1. Apply database migration:
   - Run `migration_add_risk_settings.sql` in Supabase SQL Editor

2. Configure OpenAI API:
   - Set `OPENAI_API_KEY` in `backend/.env`

3. Enable AI extraction:
   - Call `PUT /api/risk/settings/ai_email_extraction_enabled?value=true`
   - Or update database directly

## Architecture Notes

- **Clean Architecture**: Service layer isolation maintained
- **Dependency Injection**: Settings repository injected into EmailChainService
- **Fallback Design**: AI extraction falls back to regex if:
  - OpenAI API key not configured
  - OpenAI API call fails
  - OpenAI package not installed
- **Cost Control**: AI extraction disabled by default, admin toggle required
