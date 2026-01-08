# Patch: Fix external contact domain validation datetime serialization

## Metadata
adw_id: `ec3ddef`
review_change_request: `The risk module has a feature for external contacts revision. When attempting to validate email address domains using this feature, the system throws an error 500 (Internal Server Error).`

## Issue Summary
**Original Spec:** specs/issue-36-adw-ec3ddef5-sdlc_planner-fraud-risk-module-fixes.md
**Issue:** External contact domain validation fails with HTTP 500 error when validating email domains. The error occurs in `external_contact_service.py` at line 206 where `validation_result.model_dump()` is called. When Pydantic's `model_dump()` is called without `mode='json'`, datetime objects (like `domain_creation_date`) remain as Python datetime objects, which cannot be properly serialized by the Supabase client when storing in a JSON column.
**Solution:** Change `model_dump()` to `model_dump(mode='json')` to ensure datetime values are serialized as ISO format strings before being stored in the database.

## Files to Modify

- `backend/src/core/servicios/risk/external_contact_service.py` - Fix datetime serialization in `validate_email` method

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix datetime serialization in external_contact_service.py
- Locate line 206 in `backend/src/core/servicios/risk/external_contact_service.py`
- Change `validation_result.model_dump()` to `validation_result.model_dump(mode='json')`
- This ensures that `domain_creation_date` (datetime) is serialized as an ISO format string

```python
# Before
'validation_result': validation_result.model_dump(),

# After
'validation_result': validation_result.model_dump(mode='json'),
```

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Python Syntax Check**
   ```bash
   cd backend && python -m py_compile src/core/servicios/risk/external_contact_service.py
   ```

2. **Backend Code Quality Check**
   ```bash
   cd backend && ./venv/bin/ruff check src/
   ```

3. **All Backend Tests**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

4. **Frontend TypeScript Check**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

5. **Frontend Build**
   ```bash
   cd frontend && npm run build
   ```

## Patch Scope
**Lines of code to change:** 1
**Risk level:** low
**Testing required:** Verify external contact domain validation via UI works without 500 error; automated backend tests pass
