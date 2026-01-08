# Implementation: Colombia Manual COP Payment Spread Calculation

**Date:** 2025-12-11
**Module:** Tesorería Colombia
**Feature:** Manual COP Payment Spread with TRM Integration

## Summary

Implemented spread calculation for Manual COP payments in Colombia using the official TRM (Tasa Representativa del Mercado) from Banco de la República.

## Changes Made

### New Files Created

1. **`backend/src/core/servicios/trm_service.py`** (165 lines)
   - TRM service with API integration to Datos Abiertos Colombia
   - In-memory caching (1-hour TTL) to reduce API calls
   - Automatic lookback for weekends/holidays (up to 5 days)
   - Graceful error handling for API failures

2. **`backend/tests/test_trm_service.py`** (202 lines)
   - 14 unit tests covering:
     - Successful TRM fetch
     - Caching behavior
     - Cache expiration
     - Weekend/holiday lookback
     - API timeout handling
     - API error handling
     - Invalid response handling

### Modified Files

1. **`backend/src/core/servicios/payment_template_service.py`** (+80 lines)
   - Added import for `trm_service`
   - Added `_calculate_manual_cop_spread()` helper method
   - Modified `_process_row()` to:
     - Detect Manual COP payments
     - Fetch TRM for payment date
     - Calculate spread: `(Tasa Fincargo - TRM) × Total Pagado USD`
     - Route spread to PA or FK column based on NT flag

2. **`backend/tests/test_payment_template_service.py`** (+620 lines)
   - Added `TestManualCOPSpreadCalculation` class (8 tests)
   - Added `TestManualCOPSpreadIntegration` class (9 tests)
   - Updated existing tests to reflect new Manual USD behavior (no spread)

## Spread Calculation Logic

### Manual COP Payments
- **Formula:** `(Tasa de cambio de FK/en línea - TRM) × Total pagado [USD]`
- **Column Routing:**
  - NT contains "NT" (cedida, not recomprada) → **Spread PA**
  - NT empty/other → **Spread FK**

### Manual USD Payments
- **No spread** (spread only calculated for COP currency)

### Pago en línea Payments
- **Unchanged:** Uses original formula `Spread × Total pagado [USD]`
- **Column Routing:** Same NT flag logic

## Test Coverage

- **TRM Service:** 14 tests (100% pass)
- **Payment Template Service:** 68 tests (100% pass)
- **Total:** 82 tests passing

## Discrepancies Found and Resolved

1. **Initial implementation routed Manual COP spread only to Spread PA**
   - **Resolution:** Corrected to use NT flag for PA/FK routing (same as Pago en línea)

2. **Existing tests expected spread for Manual USD payments**
   - **Resolution:** Updated tests to reflect new behavior (Manual USD = no spread)

3. **Tests mixing payment types and currencies**
   - **Resolution:** Changed tests that need spread behavior to use "Pago en línea" instead of "Manual"

## Git Diff Stats

```
backend/src/core/servicios/trm_service.py          | 165 lines (new)
backend/src/core/servicios/payment_template_service.py | +80 lines
backend/tests/test_trm_service.py                  | 202 lines (new)
backend/tests/test_payment_template_service.py     | +620 lines
```

**Total:** ~1,067 lines added/modified

## API Integration

- **TRM API:** `https://www.datos.gov.co/resource/32sa-8pi3.json`
- **Timeout:** 5 seconds
- **Cache TTL:** 1 hour
- **Lookback:** Up to 5 days for weekends/holidays
