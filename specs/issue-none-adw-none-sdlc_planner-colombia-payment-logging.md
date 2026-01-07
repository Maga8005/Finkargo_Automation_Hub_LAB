# Feature: Comprehensive Logging for Colombia Payment Template Service

## Feature Description
Add comprehensive INFO and DEBUG level logging to the Colombia Tesorería payment application module (`PaymentTemplateService`) to help debug spread and exchange rate calculations. This enhancement will provide visibility into key decision points such as payment type detection, exchange rate adjustments, spread calculations, AR account selection, separate SPREAD line decisions, and payment grouping logic.

## User Story
As a developer/support engineer
I want comprehensive logging in the payment template conversion service
So that I can debug spread and exchange rate calculation issues effectively without needing to add ad-hoc logging statements each time an issue arises

## Problem Statement
The current `PaymentTemplateService` has limited logging which makes it difficult to debug issues related to:
- Payment type detection (Manual vs Pago en línea)
- Exchange rate decisions and adjustments
- Spread calculations and assignment to PA/FK columns
- AR account selection based on concept type and NT flag
- Decisions about creating separate SPREAD lines for capital-only payments
- Payment grouping logic and reference generation

When issues occur with payment conversions, developers must add temporary logging, reproduce the issue, and then remove the logging. This is inefficient and error-prone.

## Solution Statement
Add structured, comprehensive logging throughout the `PaymentTemplateService._process_row()` and related methods:
1. INFO level logs for key business decisions that affect output
2. DEBUG level logs for detailed calculations and intermediate values
3. Summary statistics at conversion completion
4. Consistent log format with context (payment_ref, customer_id, etc.) for traceability

## Access Control
- Required Role(s): N/A (backend-only change, no UI impact)
- Backend Protection: N/A (logging does not expose any new endpoints)
- Frontend Protection: N/A (no frontend changes)

## Relevant Files
Use these files to implement the feature:

- `backend/src/core/servicios/payment_template_service.py` - Main file to modify, contains the `PaymentTemplateService` class with `_process_row()`, `_process_concepts()`, and other methods that need enhanced logging
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Reference for understanding AR account lookups and column mappings (read-only, no changes needed)

### New Files
No new files needed. This is a modification to an existing service.

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
N/A - Not a document generation feature.

### B. Excel Column Mapping (Excel Processing only)
**Existing Source Excel Structure (reference only, no changes):**
| Column Name (exact) | Internal Name | Logging Relevance |
|--------------------|---------------|-------------------|
| Médio de pago | medio_pago | Payment type detection |
| Tasa de cambio de FK/en línea | exchangerate | Exchange rate decisions |
| Spread | spread | Spread calculations |
| Total pagado [USD] | total_pagado_usd | Spread amount calculation |
| NT | nt_flag | Spread routing (PA vs FK) |
| Cuenta Remitente | cuenta_remitente | Payment grouping, account lookup |

**Catalog Dependencies:**
- [x] AR account mappings documented (in `payment_catalogs.py`)
- [x] Country-specific variations identified (CO vs MX)

### C. File Format Specification (Import/Export only)
N/A - Not adding new import/export functionality.

### D. Data Contract Verification (ALL features)
No data contract changes - this is a logging enhancement only.

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| N/A | N/A | N/A | No repository calls added |

### E. Database Dependencies Checklist (Document/CRUD only)
N/A - No database changes required.

### F. External API Contract (Integration only)
N/A - No external API integration.

### G. Query Specification (Reporting only)
N/A - Not a reporting feature.

### Interface Mapping (Frontend ↔ Backend)
N/A - No frontend changes, backend logging only.

## Implementation Plan
### Phase 1: Foundation
- Review existing logging patterns in the file
- Ensure logger is properly configured at module level (already exists)
- No database or DTO changes needed

### Phase 2: Core Implementation
Add logging to the following areas in `payment_template_service.py`:

1. **Payment type detection** - Log medio_pago classification
2. **Exchange rate decisions** - Log when rate is adjusted or cleared
3. **Spread calculations** - Log spread value, PA/FK routing, calculated amounts
4. **AR account selection** - Log concept type and resulting account
5. **Separate SPREAD line decisions** - Log capital-only detection
6. **Payment grouping** - Log group statistics

### Phase 3: Integration
- Add conversion summary log with statistics
- Ensure logs are consistent and traceable
- Test with sample files to verify log output

## Step by Step Tasks

### Step 1: Review existing logging in payment_template_service.py
- Read the current file to understand existing logger usage
- Note the current DEBUG level logs at lines: 413-416, 421-423, 456-459, 463, 483-486, 740-745
- Note the current INFO log at line 674 for MORATORIOS debug

### Step 2: Add payment type detection logging
Add INFO level log in `_process_row()` after extracting `medio_pago`:
```python
# Determine payment type classification
is_pago_en_linea = medio_pago and "pago en l" in medio_pago.lower()
is_manual = medio_pago and medio_pago.lower() == "manual"
logger.info(
    f"Payment type: customer={customer_external_id}, "
    f"medio_pago='{medio_pago}', is_pago_en_linea={is_pago_en_linea}, "
    f"is_manual={is_manual}"
)
```

### Step 3: Add exchange rate decision logging
Add INFO level log when exchange rate is adjusted or cleared:
```python
logger.info(
    f"Exchange rate decision: customer={customer_external_id}, "
    f"medio_pago='{medio_pago}', currency='{currency}', "
    f"original_rate={original_exchangerate}, applied_rate={exchangerate}, "
    f"adjustment_reason={'spread_subtraction' if adjusted else 'manual_cleared' if is_manual else 'none'}"
)
```

### Step 4: Add spread calculation logging
Add INFO level log after spread routing decision:
```python
logger.info(
    f"Spread calculation: customer={customer_external_id}, "
    f"payment_ref='{payment_ref}', total_pagado_usd={total_pagado_usd}, "
    f"spread_value={spread_value}, is_nt_spread={is_nt_spread}, "
    f"spread_pa={spread_pa}, spread_fk={spread_fk}"
)
```

### Step 5: Add AR account selection logging
Add DEBUG level log in the concept processing loop:
```python
logger.debug(
    f"AR account: customer={customer_external_id}, "
    f"concept='{concept_type}', is_nt={is_nt}, ar_account={ar_account}"
)
```

### Step 6: Add separate SPREAD line decision logging
Add INFO level log when determining if a separate SPREAD row should be created:
```python
logger.info(
    f"Separate SPREAD line: customer={customer_external_id}, "
    f"should_create={should_create_separate_spread_line}, "
    f"medio_pago='{medio_pago}', concepts={list(processed_concepts.keys())}"
)
```

### Step 7: Add payment grouping logging
Add INFO level log when processing payment groups:
```python
logger.info(
    f"Payment group: customer={customer_external_id}, "
    f"ref='{payment_ref}', is_first_in_group={is_first_row_in_group}, "
    f"currency='{currency}', cuenta_remitente='{cuenta_remitente}'"
)
```

### Step 8: Add conversion summary logging
Add summary statistics at the end of `convert_to_netsuite_template()`:
```python
logger.info(
    f"Conversion summary: country={country}, "
    f"source_rows={len(df)}, output_rows={len(output_rows)}, "
    f"payment_groups={len(payment_groups_seen)}, "
    f"skipped={skipped_rows}, errors={errors_count}, "
    f"concepts_breakdown={concepts_breakdown}"
)
```

### Step 9: Run validation commands
Execute all validation commands to ensure no regressions.

## Testing Strategy
### Unit Tests
- No new unit tests needed for logging (logging is typically not unit tested)
- Existing tests in `backend/tests/test_payment_template_service.py` should pass unchanged

### Edge Cases
- Empty medio_pago values
- None values for spread, exchange rate
- Zero total_pagado_usd
- Manual payment type handling
- NT flag edge cases

## Acceptance Criteria
1. Payment type detection is logged at INFO level with medio_pago, is_pago_en_linea, is_manual
2. Exchange rate decisions are logged at INFO level with original and applied rates
3. Spread calculations are logged at INFO level with spread value, PA/FK routing, amounts
4. AR account selection is logged at DEBUG level with concept type, NT flag, account
5. Separate SPREAD line decisions are logged at INFO level with reasoning
6. Payment grouping is logged at INFO level with group reference and statistics
7. Conversion summary is logged at INFO level with aggregate statistics
8. All existing tests pass without modification
9. Log messages include customer_external_id or payment_ref for traceability
10. No new errors or warnings in backend linting

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/test_payment_template_service.py -v` - Run payment template service tests
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting (no frontend changes expected)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check (no frontend changes expected)
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- Logging level hierarchy: INFO for key business decisions, DEBUG for detailed calculations
- Existing DEBUG logs should remain unchanged
- Log messages should be concise but contain enough context for debugging
- Consider log volume in production - INFO logs will be captured, DEBUG requires configuration
- The existing MORATORIOS debug log at line 674 uses INFO level (can be left as-is or changed to DEBUG)
- All log messages should include a unique identifier (customer_external_id or payment_ref) for log correlation
- Future enhancement: Consider structured logging (JSON format) for better log analysis

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section (none needed)
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (if UI feature) - N/A, backend-only
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented (if applicable) - N/A, no changes
- [x] Data transformation rules specified (1:1 or 1:N) - N/A, no changes
- [x] Catalog/lookup dependencies identified

### Consistency (ALL features)
- [x] Data types match between frontend and backend - N/A
- [x] Field naming conventions use snake_case consistently - N/A
- [x] Access patterns (dict vs object) verified for repository methods - N/A
- [x] Country-specific variations handled (CO vs MX) if applicable - Logging applies to both

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature) - N/A, backend-only
