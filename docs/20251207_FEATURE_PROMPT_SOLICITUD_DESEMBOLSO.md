# Feature Prompt: Solicitud de Desembolso Implementation

> **Purpose**: This document contains the feature prompt(s) to be used with the `/feature` slash command to implement the "Solicitud de Desembolso" document generation for Paga Local Colombia operations.

---

## Background Context

Based on the transcript with Sofia Tobon (`docs/20251207 TRANSCRIPT SOLICITUD DE DESEMBOLSO.txt`), the Solicitud de Desembolso is an operation-level document that:

1. Is filled using data from a "Cotizacion" (quote) document from HubSpot
2. Contains specific fields that differ from standard contract requests
3. Includes an "Anexo 1" table that lists payment recipients (acreedores)
4. Supports multiple "acreedores de gastos nacionales" per operation

### Key Fields from Transcript

| Field | Source | Notes |
|-------|--------|-------|
| Numero de Solicitud Desembolso | Cotizacion | Quote number from HubSpot |
| Fecha | Current date | Date of the operation |
| Consecutivo Contrato de Credito | Derived | Format: `1-{NIT}-1-DM-DOM` |
| NIT | Client data | From client search |
| Fecha Firma Contrato Credito | Cotizacion | Date when credit contract was signed |
| Monto | Cotizacion | Amount in COP |
| Dias | Cotizacion/Fixed | Typically 120 days |
| Acreedor(es) Gastos Nacionales | Cotizacion/User input | DIAN, Agencia de Aduanas, Agente de Carga, etc. |

### Acreedor Rules (from transcript)

| Keyword in Cotizacion | Acreedor Type |
|----------------------|---------------|
| DIAN | Tributos aduaneros |
| Agencia de aduanas | Agencia de aduanas |
| Agente de carga | Gastos logisticos, Gastos de transporte |
| Agencia logistica | Gastos logisticos |

**Note**: Multiple acreedores can exist in a single operation.

---

## Feature Prompt #1: Core Implementation

Use this prompt with `/feature` to implement the main functionality:

```
Feature: Implement Solicitud de Desembolso Document Generation for Paga Local Colombia

## Overview
Implement the complete Solicitud de Desembolso document generation flow for Paga Local Colombia operations. This is an operation-level document (contract type: `pl_co_solicitud_desembolso`) that requires specific data fields beyond the standard client lookup.

## Current State
- Contract type `pl_co_solicitud_desembolso` exists in the system with prefix `PLSD-`
- UI tab exists in `FKPagaLocalCODocumentosOperacion.tsx` but uses the generic `FKPagaLocalCOContractRequest` component
- No Word template exists in `backend/templates/`
- No handler in `document_service.py` for this contract type

## Requirements

### 1. Backend Template & Handler
Create a Word template `FK COL paga local - Solicitud de Desembolso.docx` with placeholders:
- `{{numero_solicitud_desembolso}}` - Quote number
- `{{fecha}}` - Current date (formatted: "DD de MONTH de YYYY")
- `{{consecutivo_contrato_credito}}` - Format: 1-{NIT}-1-DM-DOM
- `{{nit}}` - Client NIT
- `{{nombre_importador}}` - Client name
- `{{representante_legal}}` - Legal representative
- `{{cedula_representante}}` - Representative ID
- `{{fecha_contrato_credito}}` - Credit contract signature date
- `{{monto}}` - Amount in COP (formatted with thousands separator)
- `{{monto_letras}}` - Amount in words (Spanish)
- `{{dias}}` - Number of days (typically 120)
- `{{acreedores_gastos_nacionales}}` - Comma-separated list of creditor types

Add handler `generate_solicitud_desembolso_document()` in `document_service.py`.

### 2. Backend DTOs
Extend `ContractGenerationRequest` in `legal_dtos.py` with optional fields:
- `numero_solicitud_desembolso: Optional[str]` - Quote number
- `fecha_contrato_credito: Optional[str]` - Credit contract date
- `monto: Optional[Decimal]` - Amount
- `dias: Optional[int]` - Days (default 120)
- `acreedores_gastos_nacionales: Optional[List[str]]` - List of creditor types

### 3. Frontend Component
Create `FKSolicitudDesembolsoRequest.tsx` with:
- Client search (existing pattern)
- Form fields using react-hook-form:
  - Numero de Solicitud Desembolso (text input, required)
  - Fecha del Contrato de Credito (date picker, required)
  - Monto (currency input, required)
  - Dias (number input, default 120)
  - Acreedores de Gastos Nacionales (multi-select checkboxes):
    - Tributos aduaneros (DIAN)
    - Agencia de aduanas
    - Gastos logisticos
    - Gastos de transporte
    - Otros (with text input)
- Preview section showing all data before submission

### 4. Integration
- Update `FKPagaLocalCODocumentosOperacion.tsx` to use the new specialized component for the Solicitud Desembolso tab instead of generic `FKPagaLocalCOContractRequest`
- Update `operationsService.ts` to handle the extended request data

### 5. Acreedor Catalog
Create a catalog/constants file for acreedor types that can be extended:
```typescript
export const ACREEDORES_GASTOS_NACIONALES = [
  { id: 'tributos_aduaneros', label: 'Tributos aduaneros (DIAN)', keyword: 'DIAN' },
  { id: 'agencia_aduanas', label: 'Agencia de aduanas', keyword: 'agencia de aduanas' },
  { id: 'gastos_logisticos', label: 'Gastos logisticos', keyword: 'agente de carga' },
  { id: 'gastos_transporte', label: 'Gastos de transporte', keyword: 'transporte' },
  { id: 'otros', label: 'Otros', keyword: null },
];
```

## Acceptance Criteria
1. Operations user can request a Solicitud de Desembolso with all required fields
2. Generated document contains all populated placeholders
3. Document is sent to Legal review queue with status `under_review`
4. Legal can approve/reject with the standard workflow
5. Approved PDF is downloadable from Contratos Aprobados tab
6. Multiple acreedores can be selected per document

## Technical Notes
- Follow existing patterns in `document_service.py` for template generation
- Use `_prepare_solicitud_desembolso_replacements()` method for field mapping
- Number-to-words conversion for monto_letras (use existing pattern or add helper)
- Date formatting should match Colombian format (e.g., "30 de octubre de 2025")
```

---

## Feature Prompt #2: Number to Words Utility (if needed)

If the number-to-words conversion doesn't exist, use this prompt:

```
Feature: Add Spanish Number-to-Words Utility for Colombian Currency

## Overview
Add a utility function to convert numeric amounts to Spanish words for legal documents. This is needed for the "monto_letras" field in Solicitud de Desembolso documents.

## Requirements
Create `backend/src/core/servicios/utils/number_to_words.py` with:
- Function `number_to_words_spanish(amount: Decimal) -> str`
- Support for Colombian Pesos (COP)
- Handle amounts up to billions
- Output format: "CIEN MILLONES DE PESOS M/CTE" or "CIEN MILLONES QUINIENTOS MIL PESOS M/CTE"
- All uppercase for legal documents

## Example
- Input: 100000000
- Output: "CIEN MILLONES DE PESOS M/CTE"

- Input: 150500000
- Output: "CIENTO CINCUENTA MILLONES QUINIENTOS MIL PESOS M/CTE"

## Technical Notes
- Use the `num2words` library (add to requirements.txt) with lang='es'
- Add "PESOS M/CTE" suffix for Colombian currency
- Handle edge cases: zero, negative amounts, decimals (round to whole numbers)
```

---

## Feature Prompt #3: Anexo 1 Table Support (Future Enhancement)

This is for a future enhancement to support the Anexo 1 table attachment:

```
Feature: Add Anexo 1 PDF Attachment Support for Solicitud de Desembolso

## Overview
Allow users to upload the "Anexo 1" PDF table from the Cotizacion document and attach it to the generated Solicitud de Desembolso.

## Requirements
1. Add file upload field to `FKSolicitudDesembolsoRequest.tsx` for Anexo 1 PDF
2. Store uploaded PDF in Supabase Storage
3. When generating final PDF:
   - Generate Solicitud de Desembolso pages
   - Append Anexo 1 PDF pages at the end
4. Use PyMuPDF (fitz) to merge PDFs in backend

## Technical Notes
- Maximum file size: 5MB
- Accepted formats: PDF only
- Storage path: `solicitud-desembolso/{contract_id}/anexo1.pdf`
- Final merged PDF stored at: `solicitud-desembolso/{contract_id}/final.pdf`
```

---

## Implementation Order

1. **Start with Feature Prompt #1** - This is the core implementation
2. **Feature Prompt #2** - Only if number-to-words conversion is not already available
3. **Feature Prompt #3** - Future enhancement, not required for MVP

---

## Files to Reference

When implementing, these existing files serve as patterns:

| Purpose | Reference File |
|---------|---------------|
| Contract request form pattern | `frontend/src/components/forms/FKPagaLocalCOContractRequest.tsx` |
| Document generation patterns | `backend/src/core/servicios/document_service.py` |
| DTOs for contract generation | `backend/src/interface/legal_dtos.py` |
| Operations service | `frontend/src/services/operationsService.ts` |
| Contract types | `frontend/src/types/legal.ts` |
| Existing Paga Local templates | `backend/templates/FK COL paga local - *.docx` |

---

## Word Template Structure

The Solicitud de Desembolso Word template should follow this general structure:

```
SOLICITUD DE DESEMBOLSO No. {{numero_solicitud_desembolso}}

Fecha: {{fecha}}

Por medio de la presente, {{nombre_importador}}, identificada con NIT {{nit}},
representada legalmente por {{representante_legal}}, identificado con
{{tipo_identificacion_representante}} No. {{cedula_representante}}, en calidad
de DEUDOR, solicita a FINKARGO S.A.S. el desembolso de la suma de
{{monto}} ({{monto_letras}}) para el pago de {{acreedores_gastos_nacionales}}.

Esta solicitud se realiza en el marco del Contrato de Credito No.
{{consecutivo_contrato_credito}} firmado el {{fecha_contrato_credito}}.

Plazo: {{dias}} dias.

[Signature blocks]

ANEXO 1
[Table of payments - to be attached from Cotizacion PDF]
```

**Note**: The actual template should be created based on the official Finkargo format. The structure above is a guide based on the transcript.
