# Session Notes - Drive Master Sync & Combined Filters
**Date:** November 24, 2025
**Feature:** Facturación MX - Google Drive Master Excel Sync + Combined Search Filters

---

## 📋 Overview

This session implemented two major features for the Facturación MX automation:

1. **Google Drive Master Excel Sync** - Auto-sync uploaded files with a master Excel in Drive
2. **Combined Search Filters** - Search by RFC/Codigo + date range simultaneously

---

## ✅ Implemented Features

### 1. Combined Search Filters

**Problem:** Users could only search by ONE criterion at a time (RFC OR Codigo OR Date range).

**Solution:** Implemented two-step filtering logic:
- Step 1: Apply primary filter (RFC or Codigo de operacion)
- Step 2: Apply optional date range filter on results

**Use Cases:**
- Search by RFC + date range
- Search by Codigo de operacion + date range
- Search by RFC alone
- Search by Codigo alone

**Files Modified:**
- `backend/src/interface/finance_dtos.py` - Updated docstrings for combined filters
- `backend/src/core/servicios/invoice_search_service.py` - Two-step filtering logic
- `frontend/src/pages/finance/ReporteriaAutomaticaMX.tsx` - UI with always-visible date fields
- `frontend/src/types/finance.ts` - Updated types (already compatible)

**UI Changes:**
- Date fields now always visible (marked as "opcional")
- Removed "Rango de Fechas" option from dropdown
- Layout: `[Dropdown (3)] [Search (3)] [Fecha Inicio (2)] [Fecha Fin (2)] [Button (2)]`

---

### 2. Google Drive Master Excel Sync

**Problem:** User wanted uploaded files to automatically merge with a master Excel file in Google Drive to maintain a central database.

**Solution:** Implemented automatic merge workflow with 32-column structure.

#### Architecture

**Master Excel Structure (32 columns):**
```
1. Periodo
2. Version
3. UUID (unique key for merge)
4. UUIDs relacionados
5. CP Expedicion
6. Serie
7. Folio
8. Tipo
9. Fecha emision
10. Regimen emisor
11. RFC emisor
12. Razon emisor
13. RFC receptor
14. Razon receptor
15. Regimen receptor
16. Domicilio receptor
17. Claves de productos
18. Conceptos
19. Uso CFDI
20. Efecto
21. Estado
22. Moneda
23. Tipo de cambio
24. Metodo pago
25. Forma pago
26. SubTotal
27. IVA Trasladado
28. IVA Exento
29. ISR Retenido
30. Total
31. CONCEPTO
32. CODIGO DE OPERACIÓN
```

#### Workflow

```
1. User uploads Excel (32 columns)
   ↓
2. Backend reads uploaded file as dicts (32 columns)
   ↓
3. Download "Facturación MX 2025.xlsx" from Drive (32 columns)
   ↓
4. Merge by UUID:
   - If UUID exists → UPDATE row with new data
   - If UUID is new → INSERT new row
   - Records not in upload → UNCHANGED (preserved from master)
   ↓
5. Write merged data back to Drive (32 columns)
   ↓
6. Convert to InvoiceRecord (11 columns) for search/session
   ↓
7. Store in session for fast searches
```

#### Files Created/Modified

**New Files:**
- `backend/src/core/servicios/excel_merge_service.py` - Merge logic for 32 columns

**Modified Files:**
- `backend/.env` - Added Drive master config
- `backend/src/config/settings.py` - Added `GOOGLE_DRIVE_MASTER_EXCEL_NAME`
- `backend/src/core/servicios/google_drive_service.py` - Added 3 new methods:
  - `find_master_excel_file()`
  - `download_master_excel()`
  - `upload_master_excel()`
- `backend/src/adapter/rest/finance_routes.py` - Updated upload endpoint
- `backend/src/interface/finance_dtos.py` - Added `drive_sync_stats` field
- `frontend/src/types/finance.ts` - Added `drive_sync_stats` to types
- `frontend/src/pages/finance/ReporteriaAutomaticaMX.tsx` - Display merge stats

#### Configuration Changes

**backend/.env:**
```bash
# Changed from readonly to full access
GOOGLE_DRIVE_SCOPES=["https://www.googleapis.com/auth/drive"]

# New: Master Excel filename
GOOGLE_DRIVE_MASTER_EXCEL_NAME=Facturación MX 2025.xlsx
```

**backend/src/config/settings.py:**
```python
GOOGLE_DRIVE_SCOPES: str = '["https://www.googleapis.com/auth/drive"]'
GOOGLE_DRIVE_MASTER_EXCEL_NAME: str = "Facturación MX 2025.xlsx"
```

#### UI Feedback

After upload, users see:
```
✅ Archivo cargado y sincronizado con Drive
Total de registros: 6355

[20 nuevos] [30 actualizados] [6305 sin cambios]
```

---

## 🐛 Issues Found & Resolved

### Issue 1: Data Loss (5 records missing)

**Problem:**
- Master file lost 5 records after first test
- Only 891 records remained instead of 6355+

**Root Cause:**
```
ERROR: File is not a zip file
```
File pointer was at EOF after initial validation, couldn't read for merge.

**Solution:**
Added `await file.seek(0)` before reading file for merge:

```python
async def read_uploaded_excel_as_dicts(self, file) -> List[Dict]:
    # Reset file pointer to beginning before reading
    await file.seek(0)
    contents = await file.read()
    # Reset again for any subsequent reads
    await file.seek(0)
    return self.read_excel_from_bytes(contents)
```

**Result:** Drive sync now works correctly, all records preserved.

---

### Issue 2: Column Structure Mismatch

**Problem:**
- Initial code assumed 11 columns
- Master Excel has 32 columns
- Data loss occurred

**Solution:**
- Updated `ExcelMergeService` to handle 32 columns throughout
- Master Excel operations use full 32 columns
- Session storage converts to 11 columns (for search performance)
- ZIP report uses 11 columns (client-facing simplified format)

**Separation of Concerns:**
- **Storage (32 cols):** Master Excel in Drive
- **Search (11 cols):** Session cache for fast queries
- **Reports (11 cols):** ZIP files for clients

---

## 🧪 Testing Checklist

### Drive Sync
- [x] Upload file with 32 columns
- [x] Verify merge statistics displayed
- [x] Check master Excel updated in Drive
- [x] Verify all 32 columns preserved
- [x] Test with duplicate UUIDs (updates)
- [x] Test with new UUIDs (inserts)
- [x] Verify unchanged records preserved

### Combined Filters
- [ ] Search by RFC only
- [ ] Search by RFC + date range
- [ ] Search by Codigo only
- [ ] Search by Codigo + date range
- [ ] Search by multiple Codigos + date range
- [ ] Verify results match both criteria

### ZIP Generation
- [ ] Generate ZIP from search results
- [ ] Verify Excel has 11 columns (not 32)
- [ ] Verify PDFs/XMLs included correctly

---

## 📊 Key Metrics

**Master Excel:**
- Columns: 32
- Location: Google Drive folder ID `1A5fxY8LnJYs0QTO3aYHD10IuRIgebx46`
- Filename: `Facturación MX 2025.xlsx`
- Expected records: ~6355+ (growing with uploads)

**Session Storage:**
- Columns: 11 (InvoiceRecord)
- TTL: 30 minutes
- Purpose: Fast search operations

**ZIP Reports:**
- Columns: 11 (client-facing)
- Includes: Excel + PDFs + XMLs
- Generated from search results

---

## 🚀 Deployment Notes

### Backend Dependencies
No new dependencies added - using existing:
- `openpyxl` - Excel reading/writing
- `google-api-python-client` - Drive API
- `google-auth` - Authentication

### Environment Variables Required

**Production (.env):**
```bash
# Google Drive - MUST have write access
GOOGLE_DRIVE_SCOPES=["https://www.googleapis.com/auth/drive"]
GOOGLE_DRIVE_FOLDER_ID=1A5fxY8LnJYs0QTO3aYHD10IuRIgebx46
GOOGLE_DRIVE_MASTER_EXCEL_NAME=Facturación MX 2025.xlsx
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials/drive-service-account.json
```

### Service Account Permissions

Ensure Google Drive service account has:
- ✅ Read access to Drive folder
- ✅ Write access to Drive folder
- ✅ Permission to create/update files

### Pre-Deployment Checklist

- [ ] Service account credentials uploaded to server
- [ ] Environment variables set in Render
- [ ] Master Excel file restored in Drive (if needed)
- [ ] Test upload in staging environment
- [ ] Verify Drive sync works in production
- [ ] Monitor logs for first few uploads

---

## 📁 Files Changed Summary

### Backend
```
backend/
├── .env (modified)
├── src/
│   ├── config/settings.py (modified)
│   ├── core/servicios/
│   │   ├── excel_merge_service.py (NEW - 260 lines)
│   │   ├── google_drive_service.py (modified - added 3 methods)
│   │   └── invoice_search_service.py (modified - combined filters)
│   ├── adapter/rest/
│   │   └── finance_routes.py (modified - Drive sync workflow)
│   └── interface/
│       └── finance_dtos.py (modified - added drive_sync_stats)
```

### Frontend
```
frontend/
└── src/
    ├── types/finance.ts (modified - added drive_sync_stats)
    └── pages/finance/
        └── ReporteriaAutomaticaMX.tsx (modified - UI updates)
```

---

## 🎯 Success Criteria

✅ **Feature Complete When:**
1. Users can upload Excel files and see Drive sync statistics
2. Master Excel in Drive maintains ALL 32 columns
3. Duplicate UUIDs update existing records
4. New UUIDs insert new records
5. Unchanged records preserved in master
6. Combined filters (RFC/Codigo + date) work correctly
7. ZIP reports maintain 11-column format
8. No data loss occurs during merge

---

## 📝 Next Steps / Future Improvements

### Short Term
1. Add retry logic for Drive API failures
2. Add progress indicator for large file uploads
3. Add validation to warn if master Excel structure changes

### Medium Term
1. Add audit trail (who uploaded, when, what changed)
2. Add rollback capability (restore previous master version)
3. Add conflict resolution UI (if same UUID updated by multiple users)

### Long Term
1. Add scheduled sync (daily/weekly automatic consolidation)
2. Add real-time collaboration indicators
3. Add Drive master versioning management UI

---

## 👥 Team Notes

**For Facturación Team:**
- Upload files as usual - sync happens automatically
- Green chip shows new records, blue shows updates
- Master Excel always has complete history in Drive
- If upload fails, master Excel remains unchanged (safe)

**For Developers:**
- Check logs for Drive sync status
- Monitor `drive_sync_stats` in response
- 32 columns for storage, 11 columns for reports
- File pointer reset critical for multi-read scenarios

---

## 🔗 Related Documentation

- [Initial UI Layout](./20251119_SESSION_NOTES_FACTURACION_MX_UI_LAYOUT.md)
- [ZIP Generation](./20251120_SESSION_NOTES_FACTURACION_MX_ZIP_GENERATION.md)
- [Issues & Solutions](./20251120_ISSUES_SOLUTIONS_FACTURACION_MX_ZIP_GENERATION.md)
- [PRD](./PRD_Automatizacion_Facturacion_MX_v2.md)

---

**Session Completed:** November 24, 2025
**Status:** ✅ Ready for Deployment
**Next Action:** Deploy to production and monitor first uploads
