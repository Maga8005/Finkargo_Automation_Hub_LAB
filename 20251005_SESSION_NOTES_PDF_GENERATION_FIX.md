# Session Notes: PDF Generation and Template Field Population Fixes
**Date:** October 5, 2025
**Session Focus:** Fixing PDF download errors, empty search functionality, and template field mapping issues

## Summary

This session focused on fixing critical bugs in the contract generation system:
1. Fixed PDF/DOCX download failures due to None values in data snapshots
2. Added empty search capability in Operations contract request
3. Updated number-to-words format for Spanish currency
4. Explored PDF template approach (ultimately reverted to Word template)
5. Preserved all fixes while maintaining Word template workflow

## Issues Fixed

### 1. PDF Download Error: "TypeError: replace() argument 2 must be str, not None"

**Problem:**
- PDF and DOCX downloads were failing with 500 errors
- Error: `TypeError: replace() argument 2 must be str, not None`
- Template field replacement was receiving None values instead of empty strings

**Root Cause:**
- Some fields in data snapshots were explicitly `None`
- Using `snapshot.get('field', '')` returns empty string as default, but if field exists with `None` value, it returns `None`

**Solution:**
Created a `safe_get()` helper function in `document_service.py`:

```python
def safe_get(d: dict, key: str, default: str = '') -> str:
    """Get value from dict and ensure it's a string"""
    value = d.get(key, default)
    return str(value) if value is not None else default
```

Updated all field mappings to use `safe_get()`:
```python
'[NOMBRE DEL CLIENTE]': safe_get(snapshot, 'nombre_importador'),
'[NIT]': safe_get(snapshot, 'nit'),
# ... all other fields
```

**Files Modified:**
- `backend/src/core/servicios/document_service.py`

### 2. Empty Search in Operations Contract Request

**Problem:**
- Users had to type a search query to see clients
- No way to browse all available clients
- Search button was disabled when field was empty

**Solution:**
- Removed validation requiring search query
- Changed backend to accept empty/undefined query parameter
- Updated help text to indicate empty search is allowed
- Enabled search button at all times

**Changes:**
```typescript
// Before
if (!searchQuery.trim()) {
  setError('Por favor ingrese un NIT o nombre para buscar');
  return;
}

// After
const results = await legalService.searchClients({
  query: searchQuery.trim() || undefined
});
```

**Files Modified:**
- `frontend/src/components/forms/FKContractRequest.tsx`

**UX Improvement:**
- Help text: "Busque por NIT o nombre del importador. Deje vacío para ver todos los clientes."

### 3. Number-to-Words Format Change

**Problem:**
- Template field `[valor Cupo de Operaciones en letras]` was outputting "CINCUENTA MILLONES PESOS"
- But the word "pesos" already follows this field in the template
- This created: "CINCUENTA MILLONES PESOS pesos" (redundant)

**Solution:**
Changed suffix from "PESOS" to "DE":
```python
# Before
result = " ".join(parts) + " pesos"

# After
result = " ".join(parts) + " de"
```

**Output:**
- Before: "CINCUENTA MILLONES PESOS"
- After: "CINCUENTA MILLONES DE"
- In context: "CINCUENTA MILLONES DE pesos" ✓

**Files Modified:**
- `backend/src/core/servicios/document_service.py` (line 245)

### 4. Enhanced Logging for Debugging

**Added comprehensive logging to troubleshoot PDF generation:**

```python
logger.info(f"Starting PDF generation for contract {contract_id}")
logger.info(f"PDF generated successfully for contract {contract_id}")
logger.error(f"Unexpected error in PDF download: {str(e)}", exc_info=True)
```

**Files Modified:**
- `backend/src/adapter/rest/legal_routes.py`

## Exploration: PDF Template Approach

### Initial Attempt

We explored using a PDF template directly to avoid Word numbering issues:

**Approach Tried:**
1. Used PyMuPDF (fitz) to search and replace text in PDF
2. Drew white rectangles to cover placeholders
3. Inserted replacement text at same position

**Code Added:**
- `generate_contract_pdf_from_template()` method in `document_service.py`
- PDF text search and replacement using PyMuPDF

**Why It Failed:**
- PDF text is absolutely positioned (not flowing like Word)
- Replacement text had different lengths than placeholders
- White rectangles overlapped static text
- No good way to reflow text in PDF

**Outcome:**
- ✅ Preserved numbering perfectly
- ❌ Text overlapped and covered static content
- **Decision:** Reverted to Word template approach

### Final Solution

**Reverted to Word template workflow:**
```python
# Generate DOCX from Word template
docx_bytes = await self.generate_contract_document(contract_id)

# Convert to PDF using LibreOffice
pdf_bytes = self.document_service.convert_to_pdf(docx_bytes)
```

**Numbering Fix (Manual):**
- User to manually convert auto-numbering to static text in Word template
- One-time fix: Remove auto-numbering, type section numbers manually
- Example: Change auto "1.01" → manual "Sección 9.01"

**Benefits:**
- All template field replacements work correctly
- No None value errors
- Clean, readable PDFs
- Only requires one-time manual template fix

## Files Changed

### Backend
1. **`backend/src/core/servicios/document_service.py`**
   - Added `safe_get()` helper function
   - Updated all field mappings to use `safe_get()`
   - Changed number-to-words suffix: "PESOS" → "DE"
   - Added PDF template method (explored, not used in production)
   - Added PyMuPDF and PyPDF2 imports

2. **`backend/src/adapter/rest/legal_routes.py`**
   - Added detailed logging to PDF/DOCX download endpoints
   - Error logging with stack traces

3. **`backend/src/core/servicios/contract_service.py`**
   - Temporarily changed to PDF template (reverted)
   - Back to Word → PDF workflow

### Frontend
1. **`frontend/src/components/forms/FKContractRequest.tsx`**
   - Removed search query validation
   - Enabled empty search
   - Updated help text
   - Search button always enabled

## Current State

### What's Working ✅
- All 21 template fields correctly mapped
- PDF/DOCX downloads work without errors
- None values handled safely
- Empty search in Operations
- Number-to-words format correct ("DE" instead of "PESOS")
- All previous features intact:
  - Contract generation
  - Legal review workflow
  - Operations approved contracts
  - CSV import
  - Database migrations ready

### Known Issue ⚠️
- **Word template auto-numbering** resets in some sections
- **Fix Required:** User must manually convert auto-numbering to static text
- **Impact:** One-time manual edit to Word template
- **Workaround:** Already working, just needs manual template cleanup

## Testing Performed

1. ✅ PDF download from Legal review queue
2. ✅ DOCX download from Legal review queue
3. ✅ Empty search in Operations contract request
4. ✅ Contract generation with all fields populated
5. ✅ None value handling in data snapshot
6. ✅ Number-to-words Spanish format
7. ✅ Server reload and error logging

## Next Steps

### Immediate (User Action Required)
1. **Fix Word template numbering:**
   - Open `backend/templates/FK COL - GM - Activos.docx`
   - For each auto-numbered section (Sección X.XX):
     - Right-click → Numbering → None
     - Manually type the section number
   - Save template
   - Test contract generation

### Future Enhancements
1. Run database migration: `migration_add_contract_fields.sql`
2. Import clients with all 13 columns (including KAM fields)
3. Test new contracts with complete field population
4. Consider full Spanish number-to-words library for decimal support

## Technical Notes

### Safe Value Handling Pattern
```python
# Always use safe_get for data snapshot fields
def safe_get(d: dict, key: str, default: str = '') -> str:
    value = d.get(key, default)
    return str(value) if value is not None else default
```

### Why PDF Template Didn't Work
- PDFs store text as absolute positions (x, y coordinates)
- Replacing text requires:
  1. Finding exact position
  2. Calculating exact width needed
  3. Covering old text + space for new text
  4. Preventing overlap with surrounding text
- **Problem:** Variable-length replacements don't fit fixed spaces
- **Solution:** Use flowing text (Word) instead of absolute positioning (PDF)

### Why Word Template Works
- Text flows and reflows automatically
- Placeholders can be any length
- Replacements adjust surrounding text
- Only issue: Auto-numbering (manually fixable)

## Dependencies

### Python Packages
- `python-docx`: Word document processing
- `PyMuPDF` (fitz): PDF reading (explored for template approach)
- `PyPDF2`: PDF manipulation (added but not actively used)

### System Dependencies
- LibreOffice: DOCX → PDF conversion (already installed)

## Lessons Learned

1. **PDF text replacement is complex:** Absolute positioning makes variable-length replacements difficult
2. **Word templates are more flexible:** Flowing text handles variable-length content naturally
3. **Safe value handling is critical:** Always guard against None values from database
4. **One-time manual fixes are acceptable:** Converting auto-numbering to static text is reasonable tradeoff
5. **Detailed logging is essential:** Helped quickly identify None value issue

## Related Documentation
- `20251005_FIX_TEMPLATE_FIELD_MAPPINGS.md` - Previous session notes
- `20251005_SESSION_NOTES_TEMPLATE_FIELDS.md` - Template field population
- `backend/CSV_IMPORT_GUIDE.md` - CSV import instructions
- `backend/database/migration_add_contract_fields.sql` - Database migration

## Status

✅ **Complete** - All features working, pending manual Word template numbering fix

**Deployment Ready:** Yes (after user fixes template numbering)

---

**Session Duration:** ~3 hours
**Issues Resolved:** 3 critical bugs
**Approaches Explored:** 2 (PDF template, Word template)
**Final Solution:** Word template with manual numbering fix
**Production Ready:** Yes
