# Implementation: Fix RUT Parser for GAMALOG S.A.S Format

**Date:** 2025-11-28
**Module:** Backend / Core Services
**Type:** Bug Fix

## Summary

Fixed the RUT parser service (`rut_parser_service.py`) to correctly extract custodian information from GAMALOG S.A.S RUT document format. The parser was returning incorrect values for NIT, Legal Representative name, and Legal Representative ID due to the unique columnar/newline-separated data layout in this RUT format.

## Problem

The GAMALOG RUT document has a different text extraction structure than other RUT formats:

- **NIT digits** appear as individual newline-separated single digits instead of space-separated on one line
- **Legal Representative names** appear in a columnar format where multiple representatives' name parts are interleaved
- **Legal Representative IDs** appear as sequential groups of single digits separated by empty lines

### Previous (Incorrect) Results:
- NIT: `123456789-1` (wrong - was picking up unrelated digits)
- Legal Rep Name: `GALVIS NAVARRO ROZO FRANCO` (wrong - was mixing names from 3 different reps)
- Legal Rep ID: `20161020` (wrong - was picking up date field)

### Expected (Correct) Results:
- NIT: `900026089-2`
- Legal Rep Name: `GALVIS FRANCO GABRIEL IGNACIO`
- Legal Rep ID: `73094097`

## Changes Made

### 1. Updated NIT Extraction (`_extract_nit_with_dv`)

Added Strategy 1 for newline-separated digits:
- Scans for sequences of single-digit lines
- Validates NIT starts with 8 or 9 (Colombian company NITs)
- Extracts 9 NIT digits + 1 DV digit

### 2. Updated Legal Rep Name Extraction (`_extract_legal_rep_name`)

Added Strategy 1 for columnar format:
- Detects number of representatives by counting REPRS LEGAL PRIN, REPRS LEGAL SUPL, APOD. ESPECIAL
- Finds capitalized names appearing as single words on separate lines
- Extracts first representative's name by taking every Nth name from the interleaved sequence

### 3. Updated Legal Rep ID Extraction (`_extract_legal_rep_id`)

Added Strategy 1 for sequential newline format:
- Identifies single-digit lines after "Cédula de Ciudadaní"
- Groups consecutive single digits into ID sequences (separated by empty lines)
- Returns the first sequence as the primary legal rep's ID

## Files Changed

| File | Changes |
|------|---------|
| `backend/src/core/servicios/rut_parser_service.py` | +193 / -65 lines |

### New Files Created

| File | Purpose |
|------|---------|
| `backend/tests/__init__.py` | Tests package init |
| `backend/tests/test_rut_parser_service.py` | Unit tests for RUT parser |

## Testing

### Unit Tests (7 tests, all passing)

```bash
cd backend && pytest tests/test_rut_parser_service.py -v
```

- `test_parse_gamalog_rut_all_fields` - Validates all 6 extracted fields
- `test_parse_gamalog_rut_nit_extraction` - Validates NIT format
- `test_parse_gamalog_rut_legal_rep_id_extraction` - Validates ID extraction
- `test_parse_gamalog_rut_legal_rep_name_extraction` - Validates name has 4 parts
- `test_parse_invalid_pdf_raises_error` - Error handling test
- `test_parse_empty_pdf_raises_error` - Error handling test
- `test_custodian_data_model_validation` - Validates CustodianData model

### Manual Validation

```bash
cd backend && python3 -c "
from src.core.servicios.rut_parser_service import RUTParserService
with open('../Example FIles for Reqs/4 RUT COMPLETO 30 07 2024.pdf', 'rb') as f:
    result = RUTParserService().parse_rut_pdf(f.read())
    print('NIT:', result.nit_operador_custodio)  # 900026089-2
    print('Name:', result.nombre_representante_legal_custodio)  # GALVIS FRANCO GABRIEL IGNACIO
    print('ID:', result.cc_representante_legal_custodio)  # 73094097
"
```

## Backward Compatibility

The implementation maintains backward compatibility:
- New extraction strategies are added as Strategy 1 (highest priority)
- Existing strategies remain as fallbacks (Strategy 2-5)
- Other RUT formats continue to work with existing extraction logic

## Acceptance Criteria Met

- [x] NIT Extraction: Parser correctly extracts `900026089-2` from GAMALOG RUT
- [x] Legal Rep Name: Parser correctly extracts `GALVIS FRANCO GABRIEL IGNACIO`
- [x] Legal Rep ID: Parser correctly extracts `73094097`
- [x] Company Name: Parser correctly extracts `GAMALOG S.A.S`
- [x] City: Parser correctly extracts `Bogotá, D.C.`
- [x] Email: Parser correctly extracts `gerencia.logistica@redgama.com`
- [x] Unit Tests: All 7 RUT parser tests pass

## Technical Notes

### GAMALOG RUT Document Structure

The GAMALOG RUT is a 7-page DIAN document with columnar data layout:

**Page 1 (NIT, Company Info):**
```
9    <- NIT digit 1
0    <- NIT digit 2
0    <- NIT digit 3
...
2    <- DV digit
```

**Page 3 (Legal Representatives):**
```
REPRS LEGAL PRIN
REPRS LEGAL SUPL
APOD. ESPECIAL

7    <- Rep1 ID digit 1
3    <- Rep1 ID digit 2
...
7    <- Rep2 ID digit 1
...
GALVIS    <- Rep1 Apellido1
NAVARRO   <- Rep2 Apellido1
ROZO      <- Rep3 Apellido1
FRANCO    <- Rep1 Apellido2
...
```

The key insight was recognizing that:
1. Single digits appear on individual lines (not space-separated)
2. With multiple representatives, data is interleaved in columns
3. IDs are sequential blocks, names are interleaved by position
