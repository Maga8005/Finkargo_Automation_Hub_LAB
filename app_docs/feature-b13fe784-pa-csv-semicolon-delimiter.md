# PA Accounts CSV Semicolon Delimiter Fix

**ADW ID:** b13fe784
**Date:** 2026-01-01
**Specification:** specs/issue-69-adw-b13fe784-sdlc_planner-pa-accounts-csv-semicolon-delimiter.md

## Overview

Fixed the PA Report CSV upload feature to properly handle semicolon-delimited CSV files with Latin-1 encoding (common in European/Latin regions). Previously, uploading files like `MovimientoDetallado NOV_25.csv` would fail with "No se encontraron registros que coincidan con cuentas PA del catálogo" even when valid PA accounts existed.

## What Was Built

- Improved CSV encoding detection with Latin-1 priority for semicolon-delimited files
- Column name normalization to handle whitespace variations and aliases
- Account number normalization to handle float-to-string conversion issues
- Enhanced error messages distinguishing between empty catalog vs no matches
- Debug logging for CSV parsing and account matching
- Comprehensive unit test suite for CSV parsing scenarios
- Support for "Cuenta FK" column variation in catalog uploads

## Technical Implementation

### Files Modified

- `backend/src/core/servicios/pa_report_service.py`: Main CSV parsing logic with improved encoding detection, column normalization, and error messages
- `backend/src/core/servicios/pa_rules_service.py`: Added "Cuenta FK" column mapping for catalog uploads
- `backend/src/repositorio/pa_rules_repository.py`: Added debug logging for catalog account retrieval
- `backend/tests/test_pa_report_service.py`: New comprehensive test suite for CSV parsing

### Key Changes

- **Encoding Priority**: Semicolon-delimited CSVs now try Latin-1 encoding first (`["latin-1", "iso-8859-1", "utf-8", "utf-8-sig"]`), while comma-delimited CSVs keep UTF-8 priority
- **Pre-validation**: Added 1000-byte sample decoding before pandas processing to catch encoding issues early
- **Column Aliases**: New `COLUMN_ALIASES` dictionary maps variations like "Tipo  de Transacción" (double space) and "Nota" (singular) to canonical names
- **Account Normalization**: `_normalize_account_number()` method handles float `.0` suffix and NaN values from pandas parsing
- **Descriptive Errors**: Error messages now show file account count vs catalog count to help diagnose matching issues

## How to Use

1. Navigate to **Finance → Reporte PA**
2. First upload the PA account catalog file (e.g., `Catálogo de Cuenta.xlsx`)
3. Upload the movements CSV file (e.g., `MovimientoDetallado NOV_25.csv`)
4. The system will:
   - Auto-detect semicolon delimiter
   - Apply Latin-1 encoding for semicolon files
   - Skip title rows and find the header row
   - Normalize column names and account numbers
   - Match accounts against the catalog
5. If no matches found, the error message will show account counts to help diagnose

## Configuration

No additional configuration required. The encoding detection is automatic based on delimiter:

| Delimiter | Encoding Priority |
|-----------|-------------------|
| `;` (semicolon) | Latin-1 → ISO-8859-1 → UTF-8 → UTF-8-sig |
| `,` (comma) | UTF-8 → UTF-8-sig → Latin-1 → ISO-8859-1 |

## Testing

Run the backend tests for PA report service:

```bash
cd backend && python -m pytest tests/test_pa_report_service.py -v
```

Test coverage includes:
- Delimiter detection (comma vs semicolon)
- Header row detection (with/without title rows)
- UTF-8 and Latin-1 encoding parsing
- Column renaming and validation
- Empty catalog error handling
- No matches error handling
- Successful account matching

## Notes

- The fix handles files with up to 6 title rows before the actual header (common in NetSuite exports)
- Column name matching is case-sensitive but whitespace-normalized
- Account numbers are compared as strings after normalization
- The catalog must be uploaded before processing movements files
