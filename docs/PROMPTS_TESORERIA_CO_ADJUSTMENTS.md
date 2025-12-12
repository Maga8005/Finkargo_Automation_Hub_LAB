# Implementation Prompts - Tesorería Colombia Payment Application Adjustments

Use these prompts sequentially to implement the required adjustments. **Execute in order from Prompt 1 to Prompt 7.**

---

## Prompt 1: Fix Exchange Rate Logic for Manual Payments

**Priority:** HIGH (Foundational - affects other calculations)

```
In the Tesorería Colombia payment application module, adjust the exchange rate (`exchangerate`) logic in `backend/src/core/servicios/payment_template_service.py`.

**Current Behavior:** The exchange rate from the "Tasa de cambio de FK/en línea" column is applied to ALL payments.

**Required Behavior:**
1. When `Médio de pago` = "Manual" (case-insensitive check): Set `exchangerate = None` (leave blank)
2. When `Médio de pago` contains "pago en l" (for "Pago en línea"): Keep the current exchange rate logic

**Reason:** When payments are manual, NetSuite automatically applies the TRM (Tasa Representativa del Mercado) from Banco de la República. We should not override this by providing an exchange rate.

**Implementation:**
1. In the `_process_row()` method, after extracting `medio_pago` and `exchangerate_raw`
2. Add a check: if `medio_pago` is "Manual" (case-insensitive), set `exchangerate = None`
3. Only keep the exchange rate value when the payment is "Pago en línea"

**Files to modify:**
- `backend/src/core/servicios/payment_template_service.py` - `_process_row()` method

**Test cases:**
- Manual payment in COP → exchangerate should be None/blank
- Manual payment in USD → exchangerate should be None/blank
- Pago en línea in COP → exchangerate should be (tasa_fincargo - spread)
- Pago en línea in USD → exchangerate should be tasa_fincargo (no adjustment)
```(done)

---

## Prompt 2: Add Comprehensive Logging for Debugging

**Priority:** HIGH (Helps debug subsequent changes)

```
In the Tesorería Colombia payment application module, add comprehensive logging to help debug spread and exchange rate calculations in `backend/src/core/servicios/payment_template_service.py`.

**Add logging for:**

1. **Payment type detection:**
   ```python
   logger.info(f"Payment type: medio_pago='{medio_pago}', is_pago_en_linea={is_pago_en_linea}, is_manual={is_manual}")
   ```

2. **Exchange rate decisions:**
   ```python
   logger.info(f"Exchange rate decision: medio_pago='{medio_pago}', currency='{currency}', exchangerate_applied={exchangerate}")
   ```

3. **Spread calculations:**
   ```python
   logger.info(f"Spread calculation: payment_ref='{payment_ref}', total_pagado_usd={total_pagado_usd}, spread_value={spread_value}, spread_pa={spread_pa}, spread_fk={spread_fk}")
   ```

4. **AR account selection:**
   ```python
   logger.info(f"AR account: concept='{concept_type}', is_nt={is_nt}, is_recomprada={is_recomprada}, ar_account={ar_account}")
   ```

5. **Separate SPREAD line decisions:**
   ```python
   logger.info(f"Separate SPREAD line: should_create={should_create_separate_spread_line}, medio_pago='{medio_pago}', concepts={list(processed_concepts.keys())}")
   ```

6. **Payment grouping:**
   ```python
   logger.info(f"Payment group: ref='{payment_ref}', group_total_usd={group_total_usd}, rows_in_group={rows_count}")
   ```

**Implementation:**
1. Add INFO level logs for key decisions
2. Add DEBUG level logs for detailed calculations
3. Ensure logs include enough context to trace issues
4. Consider adding a summary log at the end of conversion with statistics

**Files to modify:**
- `backend/src/core/servicios/payment_template_service.py`
```(DONE)

---

## Prompt 3: Fix Separate SPREAD Line Logic (Capital-Only Pago en Línea) - PAYMENT GROUP LEVEL

**Priority:** HIGH (Most visible bug fix)

```
In the Tesorería Colombia payment application module, fix the logic that creates separate SPREAD lines in `backend/src/core/servicios/payment_template_service.py`.

**CRITICAL CLARIFICATION:** The decision to create a separate SPREAD line must be made at the **PAYMENT GROUP LEVEL** (all rows with the same `payment_ref`), NOT at the individual row level.

**Current Behavior:**
- A separate SPREAD row is being created for ALL payments
- The check is done per-row, not per-payment-group
- This causes incorrect behavior when a payment has multiple input rows

**Required Behavior:**
1. **Group all input rows by `payment_ref`** first
2. **Aggregate ALL concepts across the entire payment group**
3. Only create a separate SPREAD row when ALL of these conditions are met FOR THE ENTIRE PAYMENT GROUP:
   - Payment method (`Médio de pago`) is "Pago en línea" (case-insensitive, contains "pago en l")
   - **Across ALL rows in the payment group**, the ONLY non-zero concept is CAPITAL
   - Country is Colombia
4. If ANY row in the payment group has a non-CAPITAL concept (INTERESES, COSTOS_FIJOS, MORATORIOS, SEGUROS, etc.), the spread must go into the Spread PA/FK/Supra columns on a COP row, NOT a separate line

**Key Scenario:**
```
Payment Group "CLIENT123|20241204|COP|60100001091|4350.5":
  Input Row 1: CAPITAL = 200 (this row only has CAPITAL)
  Input Row 2: INTERESES = 50, COSTOS_FIJOS = 30 (no CAPITAL)

  COMBINED concepts for payment group: CAPITAL, INTERESES, COSTOS_FIJOS
  → NOT capital-only → spread goes to COLUMNS, not separate line
  → Place spread on INTERESES or COSTOS_FIJOS row (first non-CAPITAL COP row)
```

**Implementation Approach:**

1. **Pre-processing Phase** (in `convert_to_netsuite_template()`):
   ```python
   # Group rows by payment_ref and collect ALL concepts across the group
   payment_group_info = {}
   for idx, row in df.iterrows():
       payment_ref = self._generate_payment_ref(...)
       if payment_ref not in payment_group_info:
           payment_group_info[payment_ref] = {
               'concepts': set(),
               'total_pagado_usd': 0,
               'medio_pago': None,
               'has_cop_non_capital_row': False
           }

       # Process concepts for this row and add to group
       row_concepts = self._process_concepts(row, country, ...)
       for concept_type, amount in row_concepts.items():
           if abs(amount) > 0.001:
               payment_group_info[payment_ref]['concepts'].add(concept_type)

       # Track if there's a COP row with non-CAPITAL concepts (for spread placement)
       currency = get_value("currency", ...)
       if currency == "COP" and any(c != "CAPITAL" for c in row_concepts.keys() if row_concepts[c] > 0):
           payment_group_info[payment_ref]['has_cop_non_capital_row'] = True

       # Sum total_pagado_usd
       payment_group_info[payment_ref]['total_pagado_usd'] += get_total_pagado_usd(row)

       # Store medio_pago (should be same for all rows in group)
       if not payment_group_info[payment_ref]['medio_pago']:
           payment_group_info[payment_ref]['medio_pago'] = get_medio_pago(row)
   ```

2. **Update `_is_capital_only_pago_en_linea()` to work with GROUP data:**
   ```python
   def _is_capital_only_pago_en_linea_for_group(
       self,
       medio_pago: Optional[str],
       group_concepts: Set[str],  # ALL concepts in the payment group
       country: str
   ) -> bool:
       """
       Check if the ENTIRE payment group is capital-only Pago en Linea.

       Args:
           medio_pago: Payment method for the group
           group_concepts: Set of ALL concept types with non-zero values across ALL rows in group
           country: Country code

       Returns:
           True only if ALL rows in the group only have CAPITAL concept
       """
       if country.lower() != "colombia":
           return False

       if not medio_pago or "pago en l" not in medio_pago.lower():
           return False

       # Check if CAPITAL is the ONLY concept across the entire group
       return group_concepts == {"CAPITAL"}
   ```

3. **Spread Placement Logic:**
   - If `_is_capital_only_pago_en_linea_for_group()` returns True → Create separate SPREAD line
   - Otherwise → Place spread in columns on the first COP row that has a non-CAPITAL concept

**Example Scenarios (PAYMENT GROUP LEVEL):**

| Payment Group | Row 1 Concepts | Row 2 Concepts | Combined Concepts | Pago en línea? | Separate SPREAD Line? |
|---------------|----------------|----------------|-------------------|----------------|----------------------|
| Group A | CAPITAL | (none) | {CAPITAL} | Yes | YES |
| Group B | CAPITAL | INTERESES | {CAPITAL, INTERESES} | Yes | NO → spread to INTERESES row |
| Group C | CAPITAL | CAPITAL, COSTOS_FIJOS | {CAPITAL, COSTOS_FIJOS} | Yes | NO → spread to COSTOS_FIJOS row |
| Group D | CAPITAL | CAPITAL | {CAPITAL} | No (Manual) | NO → spread to CAPITAL row |
| Group E | INTERESES | COSTOS_FIJOS | {INTERESES, COSTOS_FIJOS} | Yes | NO → spread to first row |

**Files to modify:**
- `backend/src/core/servicios/payment_template_service.py`:
  - Add pre-processing phase to collect group-level concept information
  - Rename/update `_is_capital_only_pago_en_linea()` to `_is_capital_only_pago_en_linea_for_group()`
  - Update `_process_row()` to receive group context and make decisions accordingly
  - Ensure spread is placed on a COP row when not creating separate line

**Testing:**
- Single-row payment with only CAPITAL, Pago en línea → Separate SPREAD line
- Two-row payment where Row 1 has CAPITAL, Row 2 has INTERESES, Pago en línea → Spread to INTERESES row columns
- Two-row payment where both rows have only CAPITAL, Pago en línea → Separate SPREAD line
- Any Manual payment → Spread to columns (never separate line)
``` (DONE)

---

## Prompt 4: Fix Multi-Row Spread Aggregation

**Priority:** HIGH (Critical for accuracy)

```
In the Tesorería Colombia payment application module, fix the spread calculation to aggregate across multiple rows that belong to the same payment in `backend/src/core/servicios/payment_template_service.py`.

**Current Behavior:**
- Each row is processed independently
- Spread is calculated per-row using that row's `Total Pagado [USD]`
- This causes incorrect spread when a single payment spans multiple rows (e.g., one row in USD, another in COP)

**Required Behavior:**
1. Group rows by `payment_ref` (the composite key: customer + date + currency + cuenta_remitente + exchangerate)
2. Sum `Total Pagado [USD]` across ALL rows in the same payment group
3. Calculate spread ONCE using the aggregated total
4. Apply the spread to only ONE output row (preferably the first non-CAPITAL concept row)

**Example:**
```
Payment Group "ABC|20241204|COP|60100001091|4350.5000":
  Row 1: Total Pagado USD = 50, CAPITAL = 200
  Row 2: Total Pagado USD = 500, INTERESES = 150, COSTOS_FIJOS = 50

  Aggregated Total Pagado USD = 550
  Spread = spread_rate × 550 = (should be calculated once)

  Output:
  - Row 1: CAPITAL, Spread PA/FK = None
  - Row 2: INTERESES, Spread PA/FK = calculated_spread
  - Row 3: COSTOS_FIJOS, Spread PA/FK = None
```

**Implementation Approach:**
1. **Pre-processing phase:** Before processing individual rows, group all rows by `payment_ref`
2. **Calculate aggregated values:** For each group, sum `Total Pagado [USD]`
3. **Processing phase:** When processing rows, use the aggregated total for spread calculation
4. **Track spread placement:** Ensure spread is only placed on one row per payment group

**Suggested code structure:**
```python
async def convert_to_netsuite_template(self, file, country):
    # ... load DataFrame ...

    # Phase 1: Pre-calculate payment group aggregates
    payment_group_totals = self._calculate_payment_group_totals(df, country, ...)

    # Phase 2: Process rows with group context
    for idx, row in df.iterrows():
        payment_ref = self._generate_payment_ref(...)
        group_total_usd = payment_group_totals.get(payment_ref, {}).get('total_pagado_usd', 0)
        # ... pass group_total_usd to _process_row() ...
```

**Files to modify:**
- `backend/src/core/servicios/payment_template_service.py`
  - Add `_calculate_payment_group_totals()` method
  - Modify `convert_to_netsuite_template()` to pre-calculate totals
  - Modify `_process_row()` to accept and use aggregated total
```(DONE)

---

## Prompt 5: Fix Spread Calculation for Manual COP Payments

**Priority:** HIGH (Depends on exchange rate logic from Prompt 1)

```
In the Tesorería Colombia payment application module, implement spread calculation for manual payments in COP in `backend/src/core/servicios/payment_template_service.py`.

**Current Behavior:** Spread is only calculated for "Pago en línea" payments.

**Required Behavior:**
1. Calculate spread for manual payments that are in COP (Colombian Pesos)
2. Formula: `Spread = (Tasa Fincargo - Tasa TRM) × Total Pagado USD`
3. Place the calculated spread in the "Spread PA" column (not FK or Supra)
4. Manual payments in USD should NOT have spread (they're pure USD transactions)

**Payment types and spread logic:**
| Payment Type | Currency | Spread Column | Calculation |
|--------------|----------|---------------|-------------|
| Pago en línea | Any | Spread FK or PA (based on NT) | spread_value × total_pagado_usd |
| Manual | COP | Spread PA | (tasa_fincargo - tasa_trm) × total_pagado_usd |
| Manual | USD | None | No spread calculation |

**Important Notes:**
- The `Tasa de cambio de FK/en línea` column contains the Fincargo rate
- For manual COP payments, we need to calculate the spread differently:
  - Currently: We need to determine how to get TRM (Banco de la República rate)
  - Option 1: Assume TRM is a fixed known value or lookup from another column
  - Option 2: Use an external API to fetch TRM for the payment date
  - **For now:** Document that TRM integration is pending. Use placeholder logic that can be updated later.

**Implementation in `_process_row()`:**
1. After determining `medio_pago`, check if it's "Manual" AND currency is "COP"
2. If true, calculate spread_pa using the formula above
3. Set spread_fk = None for manual payments
4. If `medio_pago` is "Manual" AND currency is "USD", set all spread values to None

**Files to modify:**
- `backend/src/core/servicios/payment_template_service.py`
- Consider adding a placeholder TRM lookup function or constant

**Note:** The TRM integration may be addressed in a separate task. For now, implement the structure and add a TODO comment for TRM lookup.
``` (DONE)

---

## Prompt 6: Improve Payment Reference Uniqueness - DO NOT RUN AS IT DOES NOT HELP THE UNDERLYING ISSUE

**Priority:** MEDIUM (Improvement, not critical)

```
In the Tesorería Colombia payment application module, improve the `payment_ref` generation to better differentiate payments in `backend/src/core/servicios/payment_template_service.py`.

**Current Behavior:**
The `payment_ref` is generated from: customer_id + date + currency + cuenta_remitente + exchangerate

**Problem:**
Multiple payments from the same client on the same day with the same characteristics get grouped together incorrectly.

**Proposed Improvements:**

1. **Include `Código de desembolso` (invoice_core_id) in the payment_ref:**
   - This is unique per disbursement and can help differentiate payments
   - Update `_generate_payment_ref()` to include this field:
   ```python
   def _generate_payment_ref(
       self,
       customer_external_id: str,
       payment_date_raw: Optional[str],
       currency: str,
       cuenta_remitente: Optional[str],
       exchangerate: Optional[str] = None,
       invoice_core_id: Optional[str] = None  # NEW PARAMETER
   ) -> str:
   ```

2. **Consider including row-specific identifiers:**
   - If `Código de recaudo` is available and unique, include it
   - Or include a hash of other distinguishing fields

3. **Document the limitation:**
   - Add a comment explaining that true uniqueness depends on the source system providing unique códigos de recaudo
   - This is a known limitation (~3 month fix timeline from source system)

**Implementation:**
1. Modify `_generate_payment_ref()` to accept and include `invoice_core_id`
2. Update all calls to `_generate_payment_ref()` to pass the new parameter
3. Add defensive handling for cases where invoice_core_id might be empty

**Files to modify:**
- `backend/src/core/servicios/payment_template_service.py`
  - `_generate_payment_ref()` method
  - `_process_row()` method (update calls)
  - `convert_to_netsuite_template()` method (update calls in payment group tracking)

**Note:** This is a partial fix. Full resolution requires the source system to provide unique códigos de recaudo, which is expected in ~3 months.
```

---

## Prompt 7: Add Recompra (Repurchase) Logic for AR Accounts

**Priority:** MEDIUM (Requires business confirmation on column name)

```
In the Tesorería Colombia payment application module, add support for "recompra" (repurchased) operations that affect AR account selection in `backend/src/core/servicios/payment_template_service.py` and `backend/src/core/servicios/catalogs/payment_catalogs.py`.

**Context:**
- Operations can be "cedidas" (assigned) to Patrimonio Autónomo (marked with NT column)
- Cedidas operations may later be "recompradas" (repurchased) by Finlargo Colombia (COLUMN in input file is called "Recomprado")
- When recomprada, the AR accounts should revert to Fincargo Colombia accounts, not Patrimonio accounts

**Current Behavior:**
- If NT column has a value → uses Patrimonio AR accounts (304, 259, 310, 1474)
- If NT column is empty → uses Fincargo Colombia AR accounts (302, 258, 258, 1387)

**Required Behavior:**
- If NT column has value AND operation is NOT recomprada → Patrimonio AR accounts
- If NT column has value AND operation IS recomprada → Fincargo Colombia AR accounts
- If NT column is empty → Fincargo Colombia AR accounts

**AR Account Mapping:**
| Concept | Normal/Recomprada | Cedida (NT) Not Recomprada |
|---------|------------------|---------------------------|
| CAPITAL | 302 | 304 |
| INTERESES | 258 | 259 |
| MORATORIOS | 258 | 259 |
| COSTOS_FIJOS | 258 | 310 |
| SEGUROS | 1387 | 1474 |

**Implementation Steps:**

1. **Identify the recompra field:**
   - Column name is "Recomprado"
   - Add this column to `COLOMBIA_OPTIONAL_COLUMNS` in `payment_catalogs.py`:
     ```python
     "recompra": "[Recomprado]",  # Indicates if operation was repurchased
     ```

2. **Update `get_ar_account()` function** in `payment_catalogs.py`:
   ```python
   def get_ar_account(concept_type: str, country: str, is_nt: bool = False, is_recomprada: bool = False) -> Optional[int]:
       if country_lower == "colombia":
           if is_nt and not is_recomprada:
               return COLOMBIA_NT_AR_ACCOUNTS.get(concept_type)
           return COLOMBIA_AR_ACCOUNTS.get(concept_type)
   ```

3. **Extract recompra value** in `_process_row()`:
   ```python
   recompra_raw = get_value("recompra", optional_columns)
   is_recomprada = recompra_raw is not None and str(recompra_raw).strip().lower() in ['si', 'sí', 'yes', 'true', '1', 'recomprada']
   ```

4. **Pass is_recomprada to get_ar_account()** when looking up accounts

**Files to modify:**
- `backend/src/core/servicios/catalogs/payment_catalogs.py`
  - Add recompra column to COLOMBIA_OPTIONAL_COLUMNS
  - Update `get_ar_account()` signature and logic
- `backend/src/core/servicios/payment_template_service.py`
  - Extract recompra value in `_process_row()`
  - Pass is_recomprada flag to AR account lookup

**Note:** The exact column name for recompra needs to be confirmed with the business team. Use a placeholder name that can be easily updated.
``` (DONE)

---

## Execution Summary

| Order | Prompt | Description | Priority |
|-------|--------|-------------|----------|
| 1 | Exchange Rate Logic | Set `exchangerate = None` for Manual payments | HIGH |
| 2 | Comprehensive Logging | Add debugging logs for all key decisions | HIGH |
| 3 | Separate SPREAD Line (Group Level) | Fix capital-only check at payment group level | HIGH |
| 4 | Multi-Row Aggregation | Sum Total Pagado USD across payment group | HIGH |
| 5 | Manual COP Spread | Calculate spread for manual COP payments | HIGH |
| 6 | Payment Ref Uniqueness | Include invoice_core_id in payment_ref | MEDIUM |
| 7 | Recompra AR Accounts | Handle repurchased operations for AR accounts | MEDIUM |

---

## Testing Checklist

After implementing all changes, test with the following scenarios:

### Exchange Rate Tests
- [ ] Manual payment in COP → exchangerate should be None/blank
- [ ] Manual payment in USD → exchangerate should be None/blank
- [ ] Pago en línea in COP → exchangerate should be (tasa_fincargo - spread)
- [ ] Pago en línea in USD → exchangerate should be tasa_fincargo (no adjustment)

### Spread Calculation Tests
- [ ] Manual, COP → Spread PA calculated, Spread FK = None
- [ ] Manual, USD → No spread (all None)
- [ ] Pago en línea → Spread FK or PA based on NT column

### Separate SPREAD Line Tests (PAYMENT GROUP LEVEL)
- [ ] Single-row payment, CAPITAL only, Pago en línea → Separate SPREAD line
- [ ] Single-row payment, CAPITAL + INTERESES, Pago en línea → Spread in columns on INTERESES row
- [ ] **Multi-row payment: Row 1 has CAPITAL only, Row 2 has INTERESES** → Spread in columns on INTERESES row (NOT separate line)
- [ ] **Multi-row payment: Both rows have only CAPITAL, Pago en línea** → Separate SPREAD line
- [ ] **Multi-row payment: Row 1 has CAPITAL, Row 2 has CAPITAL + COSTOS_FIJOS** → Spread in columns on COSTOS_FIJOS row
- [ ] Any Manual payment (even CAPITAL only) → Spread in columns (never separate line for Manual)

### Multi-Row Aggregation Tests
- [ ] Two-row payment (same payment_ref) → Total Pagado USD summed across both rows
- [ ] Spread calculated once on aggregated total, placed on ONE output row only
- [ ] Spread placed on first non-CAPITAL COP row when available

### AR Account Tests
- [ ] Normal operation (no NT) → Fincargo Colombia accounts (302, 258, 1387)
- [ ] Cedida (NT) not recomprada → Patrimonio AR accounts (304, 259, 310, 1474)
- [ ] Cedida (NT) recomprada → Fincargo Colombia AR accounts (302, 258, 1387)

### Payment Reference Tests
- [ ] Multiple payments same client same day with different rates → Different payment_refs
- [ ] Multiple payments same client same day with same characteristics → Known limitation (same payment_ref)
