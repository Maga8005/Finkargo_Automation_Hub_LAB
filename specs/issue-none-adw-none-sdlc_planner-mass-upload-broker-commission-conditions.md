# Chore: Mass Upload Broker Commission Conditions from Google Sheets

## Chore Description
Implement a mass upload feature for broker commission conditions to establish a starting point with all the conditions already extracted from signed contracts that are being kept in Google Sheets. This will allow the Alianzas team to bulk import broker data (name, type, commission percentages, RFC, bank account, contract dates, etc.) from a CSV/Excel file exported from Google Sheets, rather than entering each broker manually or one-by-one through contract extraction.

The feature will follow the existing CSV import pattern used in the Legal module for client imports, adapting it for the broker commission conditions use case with proper validation, error handling, and upsert logic.

## Relevant Files
Use these files to resolve the chore:

**Backend - Routes & API:**
- `backend/src/adapter/rest/alianzas_routes.py` - Main alianzas API routes file where the new import endpoint will be added. Currently has broker CRUD and contract extraction endpoints.

**Backend - Services (Business Logic):**
- `backend/src/core/servicios/broker_service.py` - Broker service with business logic, will need new bulk import method
- `backend/src/core/servicios/csv_template_mapper.py` - Reference implementation for CSV column mapping pattern (legal module)

**Backend - Repository (Data Access):**
- `backend/src/repositorio/broker_repository.py` - Broker database operations, will need new `bulk_upsert` method

**Backend - DTOs:**
- `backend/src/interface/alianzas_dtos.py` - Alianzas DTOs including `BrokerCreate`, `BrokerResponse`, etc. Will need new import-related DTOs

**Backend - Reference Files:**
- `backend/src/adapter/rest/legal_routes.py` - Reference implementation for CSV import endpoint (lines 236-327)
- `backend/src/repositorio/client_repository.py` - Reference implementation for `bulk_upsert` method

**Frontend - Pages:**
- `frontend/src/pages/alianzas/BrokersPage.tsx` - Broker management page where import UI will be added

**Frontend - Services:**
- `frontend/src/services/alianzasService.ts` - Frontend API client service for alianzas module

**Frontend - Types:**
- `frontend/src/types/alianzas.ts` - TypeScript types for alianzas module

### New Files
- `backend/src/core/servicios/broker_csv_mapper.py` - New CSV template mapper service for broker imports (following csv_template_mapper.py pattern)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Broker CSV Mapper Service
- Create `backend/src/core/servicios/broker_csv_mapper.py` following the pattern from `csv_template_mapper.py`
- Define column mappings for Google Sheets export format:
  - Map expected column names from Google Sheets to database fields
  - Support columns: `nombre`, `tipo_broker`, `master_broker_nombre` (to resolve to ID), `porcentaje_apertura`, `porcentaje_operativa`, `cuenta_bancaria`, `banco`, `rfc`, `fecha_contrato`, `vigencia_contrato`, `estado`, `link_expediente`, `notas`
- Implement `detect_template_type()` method for template detection
- Implement `map_columns()` method for column mapping
- Define required fields: `nombre`, `tipo_broker`, `porcentaje_apertura` (at minimum)
- Implement `_validate_required_fields()` method
- Implement `_apply_default_values()` method (e.g., estado='activo', porcentaje_operativa=0)
- Add `get_template_info()` method for template documentation

### Step 2: Add Bulk Import DTOs to alianzas_dtos.py
- Add `BrokerBulkImportRow` DTO for representing a single row from CSV
- Add `BrokerBulkImportResult` DTO with fields:
  - `total_processed: int`
  - `successful: int`
  - `failed: int`
  - `created: int` (new brokers)
  - `updated: int` (existing brokers updated)
  - `errors: List[str]`
  - `import_id: str`
- Add `BrokerImportError` DTO with `row_number`, `broker_nombre`, `error_message` fields

### Step 3: Add bulk_upsert Method to Broker Repository
- Add `bulk_upsert()` method to `backend/src/repositorio/broker_repository.py`
- Follow pattern from `client_repository.py` `bulk_upsert` method
- Implement upsert logic:
  - Check if broker exists by `nombre` (unique identifier for brokers)
  - If exists, update the record
  - If not exists, create new record
- Handle master_broker_id resolution (lookup master broker by name if `master_broker_nombre` provided)
- Track created vs updated counts
- Collect and return errors for invalid rows without failing entire import
- Add proper logging for debugging

### Step 4: Add Bulk Import Methods to Broker Service
- Add `bulk_import_from_csv()` method to `backend/src/core/servicios/broker_service.py`
- Implement validation logic for each row:
  - Validate `tipo_broker` is valid enum value
  - Validate percentages are between 0-100
  - Validate RFC format if provided
  - Validate dates if provided
- Handle master_broker_nombre to master_broker_id resolution
- Call repository `bulk_upsert` method
- Return `BrokerBulkImportResult` with summary statistics

### Step 5: Add Import Endpoints to Alianzas Routes
- Add `GET /api/alianzas/brokers/import/template-info` endpoint:
  - Returns information about expected CSV format
  - Uses `BrokerCSVMapper.get_template_info()`
- Add `GET /api/alianzas/brokers/import/template` endpoint:
  - Returns downloadable CSV template with headers and example row
  - Streaming response with proper Content-Disposition header
- Add `POST /api/alianzas/brokers/import` endpoint:
  - Accept file upload (CSV or Excel)
  - Use pandas to read file with encoding fallbacks
  - Use `BrokerCSVMapper` to map columns
  - Call `BrokerService.bulk_import_from_csv()`
  - Return `BrokerBulkImportResult`
  - Require alianzas role

### Step 6: Add Frontend TypeScript Types
- Add to `frontend/src/types/alianzas.ts`:
  - `BrokerBulkImportResult` interface
  - `BrokerImportError` interface
  - `BrokerTemplateInfo` interface

### Step 7: Add Frontend Service Methods
- Add to `frontend/src/services/alianzasService.ts`:
  - `getBrokerImportTemplateInfo(): Promise<BrokerTemplateInfo>`
  - `downloadBrokerImportTemplate(): Promise<Blob>`
  - `importBrokersFromFile(file: File): Promise<BrokerBulkImportResult>`

### Step 8: Add Import UI to BrokersPage
- Add "Import from CSV" button next to existing "Add Broker" button
- Create import dialog/modal with:
  - File dropzone accepting .csv, .xlsx, .xls files
  - "Download Template" link
  - Template format information display
  - Import progress indicator
  - Results display (successful, failed, errors list)
- Show success/error toast notifications
- Refresh broker list after successful import

### Step 9: Run Validation Commands
- Run all validation commands to ensure zero regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

### Google Sheets Export Format
The expected Google Sheets export should have columns like:
- `Nombre Broker` - Broker name (required)
- `Tipo` - Broker type: master_broker, independiente, aliado_logistico, consultoria (required)
- `Master Broker` - Name of master broker (optional, for sub-brokers)
- `% Apertura` - Opening commission percentage (required)
- `% Operativa` - Operational commission percentage (optional, default 0)
- `Cuenta Bancaria` - Bank account CLABE (optional)
- `Banco` - Bank name (optional)
- `RFC` - Mexican tax ID (optional)
- `Fecha Contrato` - Contract start date YYYY-MM-DD (optional)
- `Vigencia Contrato` - Contract end date YYYY-MM-DD (optional)
- `Estado` - Status: activo, inactivo, pendiente (optional, default activo)
- `Link Expediente` - Documentation URL (optional)
- `Notas` - Additional notes (optional)

### Upsert Logic
- Brokers are uniquely identified by `nombre` field
- If a broker with the same name exists, update it with new values
- If broker doesn't exist, create new record
- Master broker resolution: If `Master Broker` column provided, look up the master broker by name and set `master_broker_id`

### Error Handling
- Invalid rows should be skipped but logged in errors array
- Import should not fail completely due to single row errors
- Provide clear error messages with row number and broker name

### Security Considerations
- File size limit: 10MB maximum
- Only allow .csv, .xlsx, .xls file extensions
- Require alianzas or admin role for import
- Sanitize all input data before database operations
