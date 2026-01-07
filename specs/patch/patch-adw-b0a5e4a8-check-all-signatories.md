# Patch: Check All Signatories for Contador/Revisor Fiscal Validation

## Metadata
adw_id: `b0a5e4a8`
review_change_request: `the extraction is now working, obtaining the contador value. However, it is only comparing to one of the signatories. It should check all the signatories in the financial statements to make sure that the Contador or Revisar Fiscal are present as signatories. Currently, the app appears to be checking against only one signatory. In the case of Multivalsas, there two signatories, the Representante Legal and the Contador. The system raised an alert because the contador was not present because it only checked against the first signatory. If the logic checked both, it would see that the Contador is present.`

## Issue Summary
**Original Spec:** `specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md`
**Issue:** The validation logic only checks a single signatory (either `auditor_name` or `signatory_name`) against registered contador/revisor fiscal. Financial statements often have multiple signatories (e.g., Representante Legal AND Contador), but the current logic only validates the first one, causing false positives.
**Solution:** Update the extraction schema to support multiple signatories as an array (`signatories`) and modify the validation logic to check ALL signatories to see if ANY of them matches the registered contador/revisor fiscal.

## Files to Modify

1. `backend/src/core/servicios/risk/document_extraction_service.py` - Update FINANCIAL_STATEMENT schemas to support multiple signatories
2. `backend/src/core/servicios/risk/cross_validation_service.py` - Update `_validate_contador_revisor_fiscal()` to check all signatories

## Implementation Steps

### Step 1: Update Financial Statement Extraction Schemas
- Open `backend/src/core/servicios/risk/document_extraction_service.py`
- Add a new `signatories` array field to both `FINANCIAL_STATEMENT_CURRENT` and `FINANCIAL_STATEMENT_PRIOR` schemas
- Each signatory in the array should have: `name`, `id`, `role`
- Keep the existing single fields (`signatory_name`, `signatory_id`, `signatory_role`, `auditor_name`, `auditor_license`) for backwards compatibility

Schema changes for both FINANCIAL_STATEMENT_CURRENT (line ~21) and FINANCIAL_STATEMENT_PRIOR (line ~42):
```python
"signatories": {
    "type": ["array", "null"],
    "description": "List of all signatories who signed the financial statement (Representante Legal, Contador, Revisor Fiscal, etc.)",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of the signatory"},
            "id": {"type": ["string", "null"], "description": "ID/cedula of the signatory"},
            "role": {"type": ["string", "null"], "description": "Role of the signatory (Representante Legal, Contador, Revisor Fiscal, etc.)"}
        },
        "required": ["name"]
    }
},
```

### Step 2: Update Cross-Validation Logic to Check All Signatories
- Open `backend/src/core/servicios/risk/cross_validation_service.py`
- Modify the `_validate_contador_revisor_fiscal()` method (starting at line ~995)
- Change the logic to:
  1. Build a list of all signatories from both the array field AND legacy single fields
  2. Check if ANY signatory matches the registered contador/revisor fiscal
  3. Only flag a HIGH severity alert if NONE of the signatories match

Key changes in `_validate_contador_revisor_fiscal()`:

1. After extracting `signatory_name`, `signatory_id`, `auditor_name` (line ~1067-1070), add:
```python
# Build list of all signatories to check
signatories_to_check = []

# Get signatories array if available (new schema)
signatories_array = fs_data.get('signatories', []) or []
for sig in signatories_array:
    if sig.get('name'):
        signatories_to_check.append({
            'name': sig.get('name', ''),
            'id': sig.get('id', ''),
            'role': sig.get('role', '')
        })

# Also add legacy single fields if not already in the list (backwards compatibility)
if signatory_name and not any(s['name'] == signatory_name for s in signatories_to_check):
    signatories_to_check.append({
        'name': signatory_name,
        'id': signatory_id,
        'role': fs_data.get('signatory_role', '')
    })
if auditor_name and not any(s['name'] == auditor_name for s in signatories_to_check):
    signatories_to_check.append({
        'name': auditor_name,
        'id': '',
        'role': 'Contador/Auditor'
    })
```

2. Replace the single-person validation logic (lines ~1084-1119) with loop over all signatories:
```python
# Skip if no signatories to check
if not signatories_to_check:
    continue

# Check if ANY signatory matches contador or revisor fiscal
matched_signatory = None
matched_role = None
matched_source = None

for sig in signatories_to_check:
    normalized_person = self.normalizer.normalize_person_name(sig['name'])
    normalized_person_id = self._normalize_id(sig['id']) if sig['id'] else ''

    # Check against each registered professional
    if normalized_contador and self._names_match(normalized_person, normalized_contador):
        matched_signatory = sig
        matched_role = "contador"
        matched_source = contador_source
        break
    elif normalized_revisor and self._names_match(normalized_person, normalized_revisor):
        matched_signatory = sig
        matched_role = "revisor fiscal"
        matched_source = revisor_source
        break
    elif normalized_revisor_suplente and self._names_match(normalized_person, normalized_revisor_suplente):
        matched_signatory = sig
        matched_role = "revisor fiscal suplente"
        matched_source = "RUT"
        break
```

3. Update the result generation to use the new matched_signatory info or report that no signatory matched

### Step 3: Update Values Found Structure
- Update the `values_found` dictionary to include all signatories checked
- This provides transparency in the UI about which signatories were analyzed

## Validation

Execute every command to validate the patch is complete with zero regressions.

```bash
# 1. Backend syntax check
cd backend && python -m py_compile src/main.py

# 2. Backend linting
cd backend && ./venv/bin/ruff check src/

# 3. Backend tests
cd backend && python -m pytest tests/test_fraud_detection_service.py -v --tb=short

# 4. All backend tests
cd backend && python -m pytest -v --tb=short

# 5. Frontend linting
cd frontend && npm run lint

# 6. TypeScript type check
cd frontend && npx tsc --noEmit

# 7. Frontend build
cd frontend && npm run build
```

## Patch Scope
**Lines of code to change:** ~60-80 lines (schema update + validation logic refactor)
**Risk level:** medium (modifying core validation logic, but backwards compatible with legacy fields)
**Testing required:** Test with financial statements that have multiple signatories (like Multivalsas case with Representante Legal + Contador)
