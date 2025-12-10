# Feature: Banxico USD/MXN Exchange Rate Integration

## Feature Description
Implement integration with Banco de México (Banxico) public API to fetch official USD/MXN FIX exchange rates for commission calculations in the Alianzas module. The service will provide real-time and historical exchange rate data with caching to minimize API calls and fallback logic for weekends/holidays when rates are not published.

## User Story
As an **alianzas** team member
I want to fetch the official USD/MXN exchange rate from Banxico
So that I can accurately calculate broker commissions in MXN based on current or historical exchange rates

## Problem Statement
The Alianzas module needs to calculate commissions in MXN for broker payments. Currently, there is no automated way to fetch the official exchange rate from Banco de México, requiring manual entry or external lookups. This slows down commission processing and introduces potential for human error.

## Solution Statement
Create a `BanxicoService` that integrates with Banxico's public SIE API to fetch the USD/MXN FIX exchange rate (series SF43718). The service will:
1. Fetch current and historical exchange rates via REST API
2. Cache responses to reduce API calls
3. Handle weekends/holidays by falling back to previous business days
4. Expose endpoints in the Alianzas API for frontend consumption
5. Display exchange rate in commission calculation UI

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: Use `require_alianzas_role` from `rbac_dependencies.py` (already configured with admin bypass)
- Frontend Protection: Routes within `/alianzas/*` are already protected

## Relevant Files
Use these files to implement the feature:

**Backend - API Layer:**
- `backend/src/adapter/rest/alianzas_routes.py` - Add new endpoints for exchange rate retrieval (already has broker endpoints, add tipo-cambio endpoints)
- `backend/src/adapter/rest/rbac_dependencies.py` - Reference for `require_alianzas_role` dependency

**Backend - Service Layer:**
- `backend/src/core/servicios/google_drive_service.py` - Reference pattern for external API integration service with caching
- `backend/src/core/servicios/broker_service.py` - Reference for service patterns in alianzas module

**Backend - DTOs:**
- `backend/src/interface/alianzas_dtos.py` - Add new DTOs for exchange rate responses

**Backend - Dependencies:**
- `backend/requirements.txt` - httpx already present (version >=0.24.1)

**Frontend - Service Layer:**
- `frontend/src/services/alianzasService.ts` - Add new API functions for exchange rate

**Frontend - Types:**
- `frontend/src/types/alianzas.ts` - Add TypeScript interfaces for exchange rate responses

**Testing:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Reference E2E test format

### New Files
- `backend/src/core/servicios/banxico_service.py` - New service for Banxico API integration
- `backend/tests/test_banxico_service.py` - Unit tests for Banxico service with mocked API responses
- `.claude/commands/e2e/test_banxico_exchange_rate.md` - E2E test for exchange rate functionality

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
N/A - This is an API integration feature.

### B. Excel Column Mapping (Excel Processing only)
N/A - This is an API integration feature.

### C. File Format Specification (Import/Export only)
N/A - This is an API integration feature.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| BanxicoService.get_tipo_cambio() | Decimal | async method returns Decimal | `tc = await service.get_tipo_cambio(date(2025, 1, 10))` |
| BanxicoService.get_tipo_cambio_actual() | Decimal | async method returns Decimal | `tc = await service.get_tipo_cambio_actual()` |

### E. Database Dependencies Checklist (Document/CRUD only)
N/A - No database changes required. This feature fetches data from external API only.

### F. External API Contract (Integration only)

**Banxico SIE API Documentation:**
- Base URL: `https://www.banxico.org.mx/SieAPIRest/service/v1/series/`
- Authentication: None required for public series (token optional for higher rate limits)
- Series ID: `SF43718` (Tipo de cambio pesos por dólar E.U.A. FIX)

| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| `/series/{serieId}/datos/{fechaInicio}/{fechaFin}` | GET | None | URL params (ISO dates) | JSON |

**Example Request:**
```
GET https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/2025-01-10/2025-01-10
```

**Example Response:**
```json
{
  "bmx": {
    "series": [
      {
        "idSerie": "SF43718",
        "titulo": "Tipo de cambio pesos por dólar E.U.A. Tipo de cambio para solventar obligaciones denominadas en moneda extranjera Fecha de determinación (FIX)",
        "datos": [
          {
            "fecha": "10/01/2025",
            "dato": "20.4523"
          }
        ]
      }
    ]
  }
}
```

**Error Handling Strategy:**
- **No data for date**: Banxico doesn't publish rates on weekends/holidays. Fallback to previous 5 business days.
- **Timeout**: 30 second timeout, return user-friendly error message.
- **API unavailable**: Log error, return message suggesting manual entry fallback.
- **Rate limiting**: Cache successful responses to minimize API calls.

### G. Query Specification (Reporting only)
N/A - This is an API integration feature.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| tipo_cambio | tipo_cambio | number | Exchange rate as float |
| fecha | fecha | string | ISO date string (YYYY-MM-DD) |
| fuente | fuente | string | Data source description |

## Implementation Plan

### Phase 1: Foundation
- Create `BanxicoService` class with core API integration logic
- Add httpx async client for API calls
- Implement in-memory caching for exchange rates
- Add error handling for API timeouts and missing data
- Create DTOs for exchange rate responses

### Phase 2: Core Implementation
- Add backend API endpoints (`/tipo-cambio` and `/tipo-cambio/{fecha}`)
- Add frontend service functions
- Add TypeScript interfaces
- Write unit tests with mocked API responses

### Phase 3: Integration
- Verify endpoints work with existing Alianzas role protection
- Create E2E test to validate full flow
- Test weekend/holiday fallback logic

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format
- Create `.claude/commands/e2e/test_banxico_exchange_rate.md` with:
  - User story for fetching exchange rate
  - Test steps to navigate to Alianzas section (requires auth)
  - Verify exchange rate is displayed
  - Test historical date lookup if UI supports it
  - Screenshot requirements

### 2. Create Backend DTOs
- Add to `backend/src/interface/alianzas_dtos.py`:
  - `TipoCambioResponse` DTO with fields: `tipo_cambio: float`, `fecha: str`, `fuente: str`

### 3. Create BanxicoService
- Create `backend/src/core/servicios/banxico_service.py`:
  - Class `BanxicoService` with:
    - `BASE_URL = 'https://www.banxico.org.mx/SieAPIRest/service/v1/series/'`
    - `SERIE_TC_FIX = 'SF43718'`
    - `timeout = 30` (seconds)
    - `_cache: dict` for in-memory caching by date
  - Methods:
    - `async def get_tipo_cambio(self, fecha: date) -> Decimal` - Get rate for specific date with caching
    - `async def get_tipo_cambio_actual(self) -> Decimal` - Get most recent rate (fallback up to 5 days)
    - `async def _fetch_from_api(self, fecha: date) -> Decimal` - Internal method to call Banxico API
  - Use `httpx.AsyncClient` for async HTTP calls
  - Parse JSON response and extract rate from `bmx.series[0].datos[0].dato`
  - Raise `ValueError` if no data available for date

### 4. Add Backend API Endpoints
- Add to `backend/src/adapter/rest/alianzas_routes.py`:
  - Import `BanxicoService`, `Path`, `date` from datetime
  - Add dependency function `get_banxico_service() -> BanxicoService`
  - Add endpoint `GET /api/alianzas/tipo-cambio`:
    - Protected with `require_alianzas_role`
    - Returns `TipoCambioResponse` with current exchange rate
  - Add endpoint `GET /api/alianzas/tipo-cambio/{fecha}`:
    - `fecha: date` as path parameter
    - Protected with `require_alianzas_role`
    - Returns `TipoCambioResponse` for specific date
  - Handle errors with appropriate HTTP status codes (400 for invalid date, 500 for API errors)

### 5. Add Frontend TypeScript Types
- Add to `frontend/src/types/alianzas.ts`:
  - `TipoCambioResponse` interface matching backend DTO

### 6. Add Frontend Service Functions
- Add to `frontend/src/services/alianzasService.ts`:
  - `getTipoCambioActual(): Promise<TipoCambioResponse>` - Fetch current rate
  - `getTipoCambioFecha(fecha: string): Promise<TipoCambioResponse>` - Fetch rate by date

### 7. Create Unit Tests
- Create `backend/tests/test_banxico_service.py`:
  - Test `get_tipo_cambio` with mocked successful response
  - Test `get_tipo_cambio` with mocked no-data response (ValueError)
  - Test `get_tipo_cambio_actual` with fallback logic
  - Test caching behavior (second call doesn't hit API)
  - Test timeout handling
  - Use `pytest` and `pytest-asyncio` for async tests
  - Use `unittest.mock` or `respx` to mock httpx calls

### 8. Run Validation Commands
- Execute all validation commands listed below to verify the implementation works correctly

## Testing Strategy

### Unit Tests
- `backend/tests/test_banxico_service.py`:
  - `test_get_tipo_cambio_success` - Mock API returns valid rate
  - `test_get_tipo_cambio_no_data` - Mock API returns empty datos array
  - `test_get_tipo_cambio_cached` - Verify cache is used on second call
  - `test_get_tipo_cambio_actual_fallback` - Test weekend fallback (mocks multiple calls)
  - `test_get_tipo_cambio_timeout` - Mock timeout exception
  - `test_api_response_parsing` - Test edge cases in JSON parsing

### Edge Cases
- Weekend dates (no exchange rate published) - should fall back to Friday
- Mexican holidays (no exchange rate published) - should fall back to previous business day
- Future dates - API may not have data
- Very old dates - verify API supports historical data
- Invalid date format in path parameter
- API timeout after 30 seconds
- API returns malformed JSON
- Network connectivity issues
- Empty response from API

## Acceptance Criteria
- [x] Can fetch current exchange rate from Banxico API
- [x] Can fetch historical exchange rate by specific date
- [x] Handles weekends/holidays gracefully (falls back to previous business day up to 5 days)
- [x] Responses are cached to reduce API calls (in-memory cache by date)
- [x] API errors return user-friendly messages in Spanish
- [x] Exchange rate endpoints are protected by alianzas role
- [x] Unit tests pass with mocked API responses
- [x] TypeScript types match backend DTOs
- [x] Frontend service functions work correctly

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# 1. Run backend unit tests (including new Banxico tests)
cd backend && python -m pytest tests/test_banxico_service.py -v

# 2. Run all backend tests to ensure no regressions
cd backend && python -m pytest

# 3. Run backend linting
cd backend && ruff check src/

# 4. Run frontend linting
cd frontend && npm run lint

# 5. Run TypeScript type check
cd frontend && npx tsc --noEmit

# 6. Run frontend build to validate production compilation
cd frontend && npm run build

# 7. Test API endpoint manually (requires backend running)
curl -X GET "http://localhost:8000/api/alianzas/tipo-cambio" \
  -H "Authorization: Bearer <valid_jwt_token>" \
  -H "Content-Type: application/json"

# 8. Test historical date endpoint
curl -X GET "http://localhost:8000/api/alianzas/tipo-cambio/2025-01-10" \
  -H "Authorization: Bearer <valid_jwt_token>" \
  -H "Content-Type: application/json"
```

**E2E Test Validation:**
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_banxico_exchange_rate.md` to validate this functionality works end-to-end.

## Notes

### Dependencies
- `httpx>=0.24.1` - Already in requirements.txt, no new dependencies needed

### Future Considerations
- **Optional API Token**: Banxico offers API tokens for higher rate limits. Consider adding `BANXICO_API_TOKEN` environment variable for production use.
- **Persistent Cache**: Current implementation uses in-memory cache which resets on server restart. Consider Redis/database cache for production.
- **Exchange Rate History Table**: Future feature could store fetched rates in database for reporting/audit purposes.
- **Multiple Series Support**: Banxico has other series (e.g., DOF rates). Service could be extended to support multiple series.
- **Rate Refresh**: Consider adding a background task to refresh today's rate periodically.

### Banxico API Notes
- The FIX exchange rate (SF43718) is published daily around 12:00 PM Mexico City time
- No rate is published on weekends or Mexican bank holidays
- API is publicly accessible without authentication
- Response dates are in DD/MM/YYYY format in the JSON, convert to ISO format for consistency

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no DB changes)
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**API Integration:**
- [x] External API contract documented (Section F)
- [x] Auth method specified (None required for public series)
- [x] Error/retry strategy defined (fallback to previous days, timeout handling)

### Consistency (ALL features)
- [x] Data types match between frontend and backend (number for tipo_cambio, string for fecha/fuente)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified (async methods returning Decimal)
- [x] Country-specific variations handled (MX only feature, no CO variation needed)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
