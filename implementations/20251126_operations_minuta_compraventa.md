# Minuta Compraventa Automation Implementation

**Date:** 2025-11-26
**Module:** Operations
**Feature:** Minuta Compraventa (Bolivian Real Estate Sales Contract) Automation

## Summary

Implemented a new contract type "Minuta Compraventa" for Bolivian real estate sales contracts. The feature enables Operations team members to generate contracts by uploading three PDF documents (Cédula de Identidad, Folio Real Departamento, Folio Real Parqueo) and providing form data (prices, tax information, signature date).

## Changes Made

### Backend

- **Database Migration** (`backend/database/migration_add_minuta_compraventa_support.sql`)
  - Added new contract template for `minuta_compraventa`
  - Updated `generate_contract_id()` function to support `MIN-YYYY-NNN` format
  - Initialized sequence for contract ID generation

- **DTOs** (`backend/src/interface/legal_dtos.py`)
  - Added `MINUTA_COMPRAVENTA` to `ContractType` enum
  - Created `BuyerData`, `PropertyData`, `MinutaFormData` DTOs for parsing
  - Created `MinutaDataSnapshot` for contract data storage
  - Created `MinutaContractRequest` for API validation

- **MinutaParserService** (`backend/src/core/servicios/minuta_parser_service.py`)
  - New service for parsing Bolivian documents using PyMuPDF
  - `parse_cedula_pdf()` - Extracts buyer data from Cédula de Identidad
  - `parse_folio_real_pdf()` - Extracts property data from Folio Real documents
  - Regex-based text extraction for matricula, superficie, CI number, etc.

- **DocumentService** (`backend/src/core/servicios/document_service.py`)
  - Added `generate_minuta_compraventa_document()` method
  - Added `_prepare_minuta_replacements()` helper for template placeholders
  - Updated routing logic in `generate_contract_document()`

- **Operations Routes** (`backend/src/adapter/rest/operations_routes.py`)
  - New endpoint `POST /api/operations/contracts/generate-minuta`
  - Multi-file upload support (3 PDF documents)
  - Form data handling for prices, dates, tax info
  - Number-to-words conversion for price in Spanish

### Frontend

- **Types** (`frontend/src/types/legal.ts`)
  - Added `minuta_compraventa` to `ContractGenerationRequest`
  - New interfaces: `MinutaFormData`, `MinutaContractRequest`

- **Operations Service** (`frontend/src/services/operationsService.ts`)
  - New method `requestMinutaCompraventaGeneration()` with multi-file upload

- **FKMinutaCompraventaRequest** (`frontend/src/components/forms/FKMinutaCompraventaRequest.tsx`)
  - New component with three file upload inputs
  - Form fields for prices (USD), tax years, signature date
  - File validation (PDF only, 5MB limit)
  - Form validation before submission

- **OperationsDashboard** (`frontend/src/pages/operations/OperationsDashboard.tsx`)
  - Added new "Solicitar Minuta Compraventa" tab with Gavel icon
  - Updated tab indices for Approved Contracts (now index 4)

- **Badge Helpers** (FKReviewQueue.tsx, FKApprovedContracts.tsx)
  - Added `minuta_compraventa` case with secondary color
  - Added filter checkbox in FKApprovedContracts

## API Endpoint

```
POST /api/operations/contracts/generate-minuta
Content-Type: multipart/form-data

Files:
- cedula_file: PDF (Cédula de Identidad)
- departamento_file: PDF (Folio Real Departamento)
- parqueo_file: PDF (Folio Real Parqueo)

Form Fields:
- precio_total: string (e.g., "3,021,000.00")
- precio_departamento: string (e.g., "2,865,735.68")
- precio_parqueo: string (e.g., "155,264.32")
- gestion_impbi_pagado: string (e.g., "2024")
- gestion_impbi_comprador: string (e.g., "2025")
- dia_firma: string (e.g., "15")
- mes_firma: string (e.g., "diciembre")
- anio_firma: string (e.g., "2025")

Response: ContractGenerationResponse (201 Created)
```

## Contract ID Format

- Prefix: `MIN`
- Format: `MIN-YYYY-NNN`
- Example: `MIN-2025-001`

## Template Placeholders

The DOCX template uses bracket placeholders:
- `[NOMBRE_COMPRADOR]`, `[CI_COMPRADOR]`, `[DOMICILIO_COMPRADOR]`, `[ZONA_COMPRADOR]`, `[CIUDAD_COMPRADOR]`
- `[NUMERO_DEPTO]`, `[MATRICULA_DEPTO]`, `[SUPERFICIE_DEPTO]`, `[PISO_DEPTO]`
- `[NUMERO_PARQUEO]`, `[MATRICULA_PARQUEO]`, `[SUPERFICIE_PARQUEO]`, `[NIVEL_PARQUEO]`
- `[PRECIO_TOTAL]`, `[PRECIO_LETRAS]`, `[PRECIO_DEPTO]`, `[PRECIO_PARQUEO]`
- `[GESTION_IMPBI_PAGADO]`, `[GESTION_IMPBI_COMPRADOR]`
- `[DIA_FIRMA]`, `[MES_FIRMA]`, `[ANIO_FIRMA]`

## Testing

- Frontend build: ✅ Successful
- Lint check: ✅ No new errors in modified/created files

## Git Statistics

```
 backend/database/migration_add_minuta_compraventa_support.sql   | 134 +++++++
 backend/src/adapter/rest/operations_routes.py                   | 236 +++++++++++
 backend/src/core/servicios/document_service.py                  | 129 +++++++
 backend/src/core/servicios/minuta_parser_service.py             | 413 ++++++++++++++++++
 backend/src/interface/legal_dtos.py                             |  86 +++++
 frontend/src/components/forms/FKApprovedContracts.tsx           |  15 +
 frontend/src/components/forms/FKMinutaCompraventaRequest.tsx    | 426 ++++++++++++++++++++
 frontend/src/components/forms/FKReviewQueue.tsx                 |   6 +
 frontend/src/pages/operations/OperationsDashboard.tsx           |  24 ++
 frontend/src/services/operationsService.ts                      |  41 ++
 frontend/src/types/legal.ts                                     |  21 +-

Total: ~1,535 lines added across 12 files
```

## Deployment Notes

1. Run the database migration on Supabase before deploying
2. Ensure the template file `Minuta Compraventa GT.docx` is in `backend/templates/`
3. The frontend will auto-deploy via Vercel
4. Backend will auto-deploy via Render

## Future Enhancements

- Improve PDF parsing accuracy with OCR fallback
- Add manual data entry fallback if parsing fails
- Support for additional property types beyond Departamento/Parqueo
