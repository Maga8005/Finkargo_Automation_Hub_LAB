# Chore: Improve Declaration-Historial Matching Algorithm

## Chore Description

Investigate and improve the matching between Historial de Pagos and Inventario de Declaraciones. Currently, the matching algorithm achieves only 9 matches with the KIM SAS test files, but there are records that should match by date and amount that are not being matched.

### Root Cause Analysis

After thorough investigation of the example files (`00.KIM SAS HISTORIAL DE PAGOS.xlsx` and `00.KIM SAS DECLARACIONES MAPPING.xlsx`), the following issues were identified:

**Issue 1: Payment Group Aggregation vs Individual Matching**
The current algorithm groups payment records by (customer, date) and sums their capital amounts before matching. This creates a fundamental mismatch:

- **Historial (2025-09-03)**: Records are grouped → $14,000 (sum of $1,000 + $13,000)
- **Declarations (2025-09-03)**: Individual entries → $1,000.00 AND $13,000.00

The algorithm tries to match $14,000 against $1,000 or $13,000 - neither matches within tolerance.

**Issue 2: One-to-One vs Many-to-Many Matching**
The current design assumes:
- One PaymentGroup → One Declaration (1:1 matching)

But the actual business requirement is:
- Multiple individual payments → Multiple individual declarations (N:N matching per date)

**Issue 3: Date Tolerance May Mask Exact Matches**
Some dates that should match exactly don't align because:
- Historial date: `2025-03-28` vs Declaration date: `2025-03-31` (3 days apart)
- Historial date: `2025-03-19` vs Declaration date: `2025-03-21` (2 days apart)

The date tolerance helps here, but the grouping issue prevents matching.

**Issue 4: Amount Format Not a Problem (Confirmed)**
The `Amount Folder` column uses European format (1.000,00) with periods for thousands and commas for decimals. However, the system already uses the `Parsed Amount` column which is in US format ($1,000.00) and parsed correctly. This is NOT causing the mismatch.

### Proposed Solution

Implement **Individual Record Matching** mode:
1. Add a configuration option to match individual records instead of grouped payments
2. Match each historial record (by capital amount) to a declaration (by amount)
3. Support matching multiple records on the same date to multiple declarations
4. Maintain backward compatibility with grouped matching mode

This will increase matches from 9 to potentially 16+ for the KIM SAS test case.

## Relevant Files

Use these files to resolve the chore:

### Backend Files (Core Logic)

- `backend/src/core/servicios/treasury/payment_group_aggregator.py` - Groups payment records by customer+date. Need to add option to skip grouping for individual record matching mode.

- `backend/src/core/servicios/treasury/declaration_payment_matcher.py` - Main matching algorithm. Need to add support for matching individual records against declarations with proper N:N matching on same-date records.

- `backend/src/interface/treasury_matching_dtos.py` - DTOs for the matching feature. Need to update `MatchConfig` to include new matching mode option, and potentially add new DTOs for individual record results.

- `backend/src/adapter/rest/treasury_matching_routes.py` - API endpoints for matching workflow. Need to pass the new configuration options through and potentially modify how results are structured.

- `backend/src/core/servicios/treasury/historial_parser_service.py` - Parses the Excel file. May need minor updates to expose individual records directly.

- `backend/src/core/servicios/treasury/enriched_excel_generator.py` - Generates output Excel. Need to update to populate declaration columns at the individual record level instead of group level.

### Frontend Files (UI Updates)

- `frontend/src/components/treasury/FKMatchingConfigForm.tsx` - Configuration form. Need to add toggle for individual vs grouped matching mode.

- `frontend/src/types/treasuryMatching.ts` - TypeScript types. Need to update MatchConfig interface to include new options.

- `frontend/src/pages/treasury/HistorialMatchingPage.tsx` - Main page. Minor updates for handling new matching mode.

- `frontend/src/components/treasury/FKMatchResultsTable.tsx` - Results display. May need updates to display individual record matches vs group matches.

### New Files

None required - all changes will be modifications to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update DTOs with New Matching Mode Configuration

- Add `match_mode` field to `MatchConfig` in `backend/src/interface/treasury_matching_dtos.py`:
  - Type: `Literal["grouped", "individual"]`
  - Default: `"grouped"` (backward compatible)
- Add a new `IndividualMatchResult` DTO or extend `MatchResult` to support individual record results:
  - Should reference `HistorialRecord` instead of just `PaymentGroup`
  - Include row number for Excel output mapping

### Step 2: Update Payment Group Aggregator

- Modify `payment_group_aggregator.py` to support an optional `skip_aggregation` mode
- When `match_mode="individual"`, return each record as its own "group" with `record_count=1`
- This allows the existing matcher to work with individual records without major refactoring

### Step 3: Implement Individual Record Matching in Matcher

- Update `declaration_payment_matcher.py` to handle individual matching mode:
  - When `match_mode="individual"`, match records by individual `capital` amount instead of `total_capital`
  - Implement N:N matching for same-date records: use Hungarian algorithm or greedy best-match assignment
  - Ensure declarations are only used once (already handled by `used_declarations` set)
- Key change: Instead of matching group total ($14,000) to declaration ($1,000), match individual record ($1,000) to declaration ($1,000)

### Step 4: Update API Routes

- Modify `treasury_matching_routes.py` to:
  - Accept new `match_mode` parameter in configuration
  - Pass configuration to aggregator and matcher
  - Handle results appropriately for both modes

### Step 5: Update Enriched Excel Generator

- Modify `enriched_excel_generator.py` to:
  - Populate declaration columns at the individual row level (using `row_number` from `HistorialRecord`)
  - Handle both grouped and individual modes for output generation

### Step 6: Update Frontend Configuration Form

- Add radio button or toggle in `FKMatchingConfigForm.tsx` for matching mode:
  - "Agrupado (por fecha)" - Grouped mode (default)
  - "Individual (por registro)" - Individual mode
- Update `MatchConfig` type in `frontend/src/types/treasuryMatching.ts`
- Add tooltip explaining when to use each mode

### Step 7: Update Frontend Results Display (Optional Enhancement)

- Update `FKMatchResultsTable.tsx` to display:
  - For grouped mode: Show group with record count
  - For individual mode: Show each record row number
- This helps users understand which specific rows matched

### Step 8: Testing and Validation

- Test with KIM SAS example files:
  - Grouped mode: Should still produce 9 matches (backward compatible)
  - Individual mode: Should produce 16+ matches
- Verify the enriched Excel output has declaration columns populated correctly
- Ensure no regressions in existing functionality

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

### Expected Match Improvements

With individual matching mode, the following additional matches should be achieved for KIM SAS:

| Date | Historial Capital | Declaration Amount | Currently Matches? | Will Match? |
|------|-------------------|-------------------|-------------------|-------------|
| 2025-09-03 | $1,000.00 | $1,000.00 | ❌ (grouped as $14k) | ✅ |
| 2025-09-03 | $13,000.00 | $13,000.00 | ❌ (grouped as $14k) | ✅ |
| 2025-11-10 | $5,101.41 | $5,101.41 | ❌ (grouped as $17k) | ✅ |
| 2025-11-10 | $2,500.00 | $2,500.00 | ❌ (grouped as $17k) | ✅ |
| 2025-11-10 | $2,000.00 | $2,000.00 | ❌ (grouped as $17k) | ✅ |
| 2025-11-10 | $5,000.50 | $5,000.50 | ❌ (grouped as $17k) | ✅ |
| 2025-11-10 | $1,500.60 | $1,500.60 | ❌ (grouped as $17k) | ✅ |
| 2025-11-10 | $999.50 | $999.50 | ❌ (grouped as $17k) | ✅ |

### Backward Compatibility

The default matching mode (`grouped`) ensures existing behavior is preserved. Users must explicitly select individual mode for the new matching behavior.

### Date Tolerance Still Important

Even with individual matching, date tolerance is still valuable for cases where:
- Payment date differs slightly from declaration date (e.g., weekends, processing delays)
- The `Parsed Date` from scanner differs from actual payment date

The current default of 7 days tolerance should be maintained.

### Future Enhancement Consideration

Consider adding a "hybrid" mode that:
1. First tries exact individual matching (date + amount within tolerance)
2. Falls back to grouped matching for remaining unmatched records
3. This could maximize matches while handling edge cases
