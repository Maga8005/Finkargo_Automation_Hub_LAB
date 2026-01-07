# Chore: Colombia Manual Payment Exchange Rate Logic

## Chore Description
Adjust the exchange rate (`exchangerate`) logic in the Tesoreria Colombia payment application module. Currently, the exchange rate from the "Tasa de cambio de FK/en linea" column is applied to ALL payments regardless of payment method.

The business requirement is:
- **Manual payments**: Set `exchangerate = None` (leave blank). This allows NetSuite to automatically apply the TRM (Tasa Representativa del Mercado) from Banco de la Republica.
- **Pago en linea payments**: Keep the current exchange rate logic (apply the rate from the file, with spread adjustment for COP currency).

This change ensures that manual payments use the official government exchange rate rather than Finkargo's internal rate.

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/payment_template_service.py`** - Main file to modify. Contains the `_process_row()` method where exchange rate is extracted and processed. Lines 310-536 are the core processing logic. The exchange rate is currently extracted at lines 368-374 and adjusted at lines 401-416.

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** - Reference file (read-only). Contains column mappings including `medio_pago` at line 134 mapping to "Medio de pago" column.

- **`backend/tests/test_payment_template_service.py`** - Test file to update. Already contains tests for `_process_row()` and related methods. Will need new test cases for the Manual payment exchange rate behavior.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Understand the Current Exchange Rate Logic
1. In `payment_template_service.py`, the exchange rate flow is:
   - Line 369: Extract `exchangerate_raw` from optional columns (key `exchangerate` maps to "Tasa de cambio de FK/en linea")
   - Lines 370-374: Parse to float as `exchangerate`
   - Line 401: Extract `medio_pago` from optional columns
   - Lines 406-416: Adjust exchange rate for "Pago en linea" with COP currency by subtracting spread

### Step 2: Modify Exchange Rate Logic in `_process_row()` Method
Location: `backend/src/core/servicios/payment_template_service.py`, inside `_process_row()` method

**After line 416** (after the existing exchange rate adjustment block), add a new check:

```python
# Clear exchange rate for Manual payments - NetSuite will use TRM from Banco de la Republica
if medio_pago and medio_pago.lower() == "manual":
    exchangerate = None
    logger.debug(
        f"Cleared exchangerate for Manual payment - NetSuite will apply TRM"
    )
```

This check should be placed AFTER the "Pago en linea" adjustment logic so:
1. If "Pago en linea" in COP: rate is adjusted by spread, then kept
2. If "Manual": rate is cleared regardless of currency
3. If neither: rate is kept as-is from the file

**Important implementation notes:**
- Use case-insensitive check (`medio_pago.lower() == "manual"`) for consistency
- Check `medio_pago` is not None before calling `.lower()`
- Place this logic after line 416 but before line 419 (where `total_pagado_usd_raw` is extracted)

### Step 3: Add Unit Tests for Manual Payment Exchange Rate Behavior
Location: `backend/tests/test_payment_template_service.py`

Add a new test class after `TestSpreadAssignmentToNonCapital`:

```python
# ==================== Tests for Manual Payment Exchange Rate Behavior ====================

class TestManualPaymentExchangeRate:
    """Tests for exchange rate clearing on Manual payments."""

    def test_manual_payment_cop_has_no_exchange_rate(self, service):
        """Manual payment in COP should have exchangerate = None."""
        row_data = {
            "Cliente": "Test Client",
            "Identificacion del cliente": "123456789",
            "Codigo de desembolso": "CO:900759388:1:14:PAG",
            "Codigo de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Medio de pago": "Manual",
            "Tasa de cambio de FK/en linea": 3854.70815,  # Should be ignored
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantias": 0,
            "IVA Fondo de garantias": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        assert len(result) >= 1
        assert result[0]["exchangerate"] is None

    def test_manual_payment_usd_has_no_exchange_rate(self, service):
        """Manual payment in USD should have exchangerate = None."""
        row_data = {
            "Cliente": "Test Client",
            "Identificacion del cliente": "123456789",
            "Codigo de desembolso": "CO:900759388:1:15:PAG",
            "Codigo de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Medio de pago": "Manual",
            "Tasa de cambio de FK/en linea": 3854.70815,  # Should be ignored
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantias": 0,
            "IVA Fondo de garantias": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        assert len(result) >= 1
        assert result[0]["exchangerate"] is None

    def test_pago_en_linea_cop_has_adjusted_exchange_rate(self, service):
        """Pago en linea in COP should have exchangerate = (tasa_fincargo - spread)."""
        row_data = {
            "Cliente": "Test Client",
            "Identificacion del cliente": "123456789",
            "Codigo de desembolso": "CO:900759388:1:16:PAG",
            "Codigo de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Medio de pago": "Pago en linea",
            "Tasa de cambio de FK/en linea": 3854.70815,
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantias": 0,
            "IVA Fondo de garantias": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        assert len(result) >= 1
        # Expected: 3854.70815 - 10 = 3844.70815
        assert result[0]["exchangerate"] == pytest.approx(3844.70815, rel=1e-4)

    def test_pago_en_linea_usd_has_unadjusted_exchange_rate(self, service):
        """Pago en linea in USD should have exchangerate = tasa_fincargo (no adjustment)."""
        row_data = {
            "Cliente": "Test Client",
            "Identificacion del cliente": "123456789",
            "Codigo de desembolso": "CO:900759388:1:17:PAG",
            "Codigo de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Medio de pago": "Pago en linea",
            "Tasa de cambio de FK/en linea": 3854.70815,
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantias": 0,
            "IVA Fondo de garantias": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        assert len(result) >= 1
        # Expected: 3854.70815 (no adjustment for USD)
        assert result[0]["exchangerate"] == pytest.approx(3854.70815, rel=1e-4)

    def test_manual_payment_case_insensitive(self, service):
        """Manual payment detection should be case-insensitive."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        for manual_variant in ["Manual", "MANUAL", "manual", "MaNuAl"]:
            row_data = {
                "Cliente": "Test Client",
                "Identificacion del cliente": "123456789",
                "Codigo de desembolso": "CO:900759388:1:18:PAG",
                "Codigo de recaudo": "REC-001",
                "Fecha de pago": "2025-12-01",
                "Moneda": "COP",
                "Capital": 1000.00,
                "Banco remitente": "Test Bank",
                "Medio de pago": manual_variant,
                "Tasa de cambio de FK/en linea": 3854.70815,
                "Spread": 10,
                "Total pagado [USD]": 1000,
                "NT": "",
                "4x1000": 0,
                "Fondo de garantias": 0,
                "IVA Fondo de garantias": 0,
                "Seguro + IVA": 0,
                "Intereses Corrientes": 0,
                "Cuenta Remitente": "60100001091",
            }

            row = pd.Series(row_data)
            df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

            assert result[0]["exchangerate"] is None, f"Failed for variant: {manual_variant}"
```

### Step 4: Verify Existing Tests Still Pass
The existing tests in `test_payment_template_service.py` should continue to pass because:
- Tests for "Pago en linea" behavior don't set `medio_pago` to "Manual"
- The `test_manual_payment_capital_only_no_spread_row` test at line 361 tests Manual payment behavior for spread, not exchange rate

However, review `test_manual_payment_capital_only_no_spread_row` - it currently expects spread to be populated but doesn't check exchange rate. The new logic will set `exchangerate = None` for this test case, which is correct behavior and shouldn't break the test since it doesn't assert on `exchangerate`.

### Step 5: Run Validation Commands

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. **Why place the Manual check AFTER the Pago en linea adjustment?**
   - The current code structure extracts and adjusts exchange rate in sequence
   - By placing the Manual check after the Pago en linea adjustment, we ensure:
     - Pago en linea payments keep their adjusted rate
     - Manual payments have rate cleared regardless of any prior adjustments
   - This is simpler than restructuring the logic with if/elif

2. **Column name encoding:**
   - The source file uses "Medio de pago" with accented 'e' in "Medio"
   - The catalog already handles this correctly at line 134

3. **Test data considerations:**
   - Tests use simplified column names without accents for ease of writing
   - The `df_columns_normalized` mapping handles case-insensitive matching

4. **Edge cases handled:**
   - `medio_pago` is None: No change to exchange rate
   - `medio_pago` is empty string: No change (won't match "manual")
   - Case variations of "Manual": Handled by `.lower()` comparison

5. **No frontend changes required:**
   - This is purely backend business logic
   - The output Excel template format remains unchanged
   - The `exchangerate` column will simply be blank for Manual payments
