# Implementation: Update payment_ref Grouping Logic - Customer ID and Exchange Rate

**Date:** 2025-12-09
**Module:** Tesorería (Treasury)
**Feature:** Update payment_ref grouping to use customer ID and include exchange rate

## Summary

Updated the payment_ref grouping logic for both Colombia and Mexico to:
1. Use `customer_external_id` (Identificación del cliente) instead of `invoice_core_id` (Código de desembolso)
2. Include `exchangerate` (Tasa de cambio de FK/en línea) as part of the composite grouping key

## Changes Made

- **Updated `_generate_payment_ref()` method signature:**
  - Changed first parameter from `invoice_core_id: str` to `customer_external_id: str`
  - Added new parameter `exchangerate: Optional[str] = None`
  - Updated docstring to reflect new grouping logic

- **Updated `_generate_payment_ref()` method body:**
  - Changed component list to use `customer_external_id` instead of `invoice_core_id`
  - Added exchange rate to components list with 4 decimal place formatting for consistency
  - Updated debug logging to include the new parameters

- **Updated `convert_to_netsuite_template()` caller (~lines 241-256):**
  - Changed extraction from `invoice_core_id` to `customer_external_id`
  - Added extraction of `exchangerate_raw` from optional columns
  - Updated `_generate_payment_ref()` call with new parameters

- **Updated `_process_row()` caller (~lines 380-389):**
  - Updated `_generate_payment_ref()` call to use `customer_external_id` (already extracted)
  - Added `exchangerate_raw` (already extracted) to the method call

## Technical Details

### New Payment Reference Format

The generated `payment_ref` now uses the following format:

```
{customer_external_id}|{payment_date_YYYYMMDD}|{currency}|{cuenta_remitente}|{exchangerate}
```

For online payments without `cuenta_remitente`:
```
{customer_external_id}|{payment_date_YYYYMMDD}|{currency}|{exchangerate}
```

### Exchange Rate Handling

- Exchange rate is formatted to 4 decimal places for consistent grouping
- Handles None/empty values gracefully (not included if empty)
- Uses try/except to handle parsing errors

### Example Generated payment_refs

| Scenario | Generated payment_ref |
|----------|----------------------|
| Regular payment | `900123456\|20251209\|COP\|60100001091\|4250.5000` |
| Online payment COP | `900123456\|20251209\|COP\|4250.5000` |
| Payment without rate | `900123456\|20251209\|COP\|60100001091` |

## Discrepancies Found

**None.** The plan assumptions matched the actual codebase.

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 49 ++++++++++++++--------
 1 file changed, 32 insertions(+), 17 deletions(-)
```

## Validation Results

- ✅ Backend Python import check: OK
- ✅ All 47 backend tests pass
- ✅ Frontend linting: OK
- ✅ TypeScript type check: OK
- ✅ Frontend build: OK

## Business Impact

- Payments are now grouped by **customer** instead of disbursement code
- Different **exchange rates** will create separate payment groups
- This affects how spread and comision_banco values are assigned (first row of each group)
- Applies to both Colombia and Mexico payment templates
