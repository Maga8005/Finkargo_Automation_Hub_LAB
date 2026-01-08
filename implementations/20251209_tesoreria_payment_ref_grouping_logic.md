# Implementation: Payment Ref Grouping Logic for Colombia Payments

**Date:** 2025-12-09
**Module:** Tesorería (Treasury)
**Feature:** Adjust payment_ref grouping logic for Colombia payment template conversion

## Summary

Implemented a new payment reference (`payment_ref`) generation logic for the Colombia payment template converter. The previous implementation read `payment_ref` directly from the "Código de recaudo" column in the source Excel file. The new implementation generates a composite `payment_ref` based on four grouping elements.

## Changes Made

- **Added `_generate_payment_ref()` helper method** - Generates composite payment reference from:
  1. `invoice_core_id` (Código de desembolso)
  2. `payment_date` (Fecha de pago) - formatted as YYYYMMDD
  3. `currency` (Moneda) - COP, USD, etc.
  4. `cuenta_remitente` (Cuenta Remitente) - optional for online payments

- **Added `_format_date_for_grouping()` helper method** - Formats dates consistently as YYYYMMDD for reliable grouping keys

- **Modified `_process_row()` method** - Replaced direct reading of `payment_ref` from source file with generated `payment_ref` using the new helper

- **Updated `convert_to_netsuite_template()` method** - Updated payment group tracking to use the generated `payment_ref` for determining first-row-in-group status (affects spread and comision_banco assignment)

## Technical Details

### Payment Reference Format

The generated `payment_ref` uses a pipe (`|`) separator:

```
{invoice_core_id}|{payment_date_YYYYMMDD}|{currency}|{cuenta_remitente}
```

For online payments where `cuenta_remitente` is empty:
```
{invoice_core_id}|{payment_date_YYYYMMDD}|{currency}
```

### Business Logic

- For regular payments: All four elements are combined
- For online payments ("Pago en línea"): No bank account is registered, so currency differentiates between:
  - COP payments going to the compensation account
  - USD/other currency payments going to different accounts

### Example Generated payment_refs

| Scenario | Generated payment_ref |
|----------|----------------------|
| Regular payment | `DES-2025-001\|20251209\|COP\|60100001091` |
| Online payment COP | `DES-2025-002\|20251209\|COP` |
| Online payment USD | `DES-2025-002\|20251209\|USD` |

## Discrepancies Found

None. The plan assumptions matched the actual codebase structure.

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 134 +++++++++++++++++++-
 1 file changed, 126 insertions(+), 8 deletions(-)
```

## Validation Results

- ✅ Backend Python import check: OK
- ✅ Backend tests: 47 passed, 0 failed
- ✅ Frontend linting: OK
- ✅ TypeScript type check: OK
- ✅ Frontend build: OK

## Notes

- The "Código de recaudo" column remains in `COLOMBIA_REQUIRED_COLUMNS` for backwards compatibility and auditing purposes, but its value is no longer used for the output `payment_ref`
- Debug logging was added to trace payment_ref generation for troubleshooting
- The new grouping logic applies to both Colombia and Mexico (the `_generate_payment_ref` method is called in `_process_row` which is used for both countries)
