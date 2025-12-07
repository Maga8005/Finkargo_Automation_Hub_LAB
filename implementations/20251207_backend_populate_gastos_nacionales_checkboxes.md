# Implementation: Populate Gastos Nacionales de Importación Checkboxes

## Date
2025-12-07

## Summary
Implemented automatic checkbox population for the "Gastos Nacionales de Importación" table in Solicitud de Desembolso documents. The checkboxes are now automatically checked based on the acreedor (creditor) names in the Anexo I table items.

## Changes Made

### 1. Added Keyword Mapping Constants (`document_service.py`)
- **GASTOS_CATEGORY_KEYWORDS**: Maps 5 expense categories to keyword lists:
  - `tributos_aduaneros`: tributo, arancel, dian, aduanero, aduana
  - `servicios_aduanales`: impuesto, entidad de pago, pago de impuestos, servicio aduanal
  - `logisticos`: logístic, logistic, operador logístico
  - `transporte`: transporte, transportador, flete, envío, envio, carga
  - `almacenamiento`: almacén, almacen, almacenamiento, bodega, storage, depósito, deposito

- **GASTOS_CHECKBOX_INDICES**: Maps categories to cell indices in the nested table (0-4)

### 2. Implemented Helper Methods (`document_service.py`)
- **`_determine_gastos_categories(anexo_items)`**: Analyzes acreedor fields to determine which expense categories should be checked. Uses case-insensitive keyword matching.

- **`_populate_gastos_checkboxes(doc, categories)`**: Updates the checkbox XML elements in the Word document. Uses Word 2010 namespace (`w14`) to modify `<w14:checked w14:val="0|1"/>` elements.

### 3. Integrated into Document Generation
- Updated `generate_solicitud_desembolso_document()` to call the new methods after populating the Anexo I table

### 4. Added Unit Tests (`test_document_service.py`)
- 9 new tests for gastos categories functionality:
  - `test_determine_gastos_categories_impuestos`
  - `test_determine_gastos_categories_transporte`
  - `test_determine_gastos_categories_logisticos`
  - `test_determine_gastos_categories_multiple`
  - `test_determine_gastos_categories_empty`
  - `test_determine_gastos_categories_no_match`
  - `test_determine_gastos_categories_case_insensitive`
  - `test_gastos_category_keywords_defined`
  - `test_gastos_checkbox_indices_defined`

## Files Changed

| File | Description |
|------|-------------|
| `backend/src/core/servicios/document_service.py` | Added constants, 2 helper methods, integrated checkbox population (+105 lines) |
| `backend/tests/test_document_service.py` | Added 9 new unit tests (+83 lines) |

## git diff --stat
```
backend/src/core/servicios/document_service.py | 313 ++++++++++++++++++++-----
backend/tests/test_document_service.py         |  84 ++++++-
 2 files changed, ~330 insertions(+), ~65 deletions(-)
```

## Validation Results

All validation commands passed:

- `cd backend && python -m pytest` - **36/36 tests passed**
- `cd backend && ruff check src/` - **All checks passed**
- `cd frontend && npm run lint` - **Passed**
- `cd frontend && npx tsc --noEmit` - **Passed**
- `cd frontend && npm run build` - **Built successfully**

## Technical Details

### Checkbox XML Structure
The checkboxes in the Word template use Word 2010 extensions (`w14` namespace):
```xml
<w:sdt>
  <w:sdtPr>
    <w14:checkbox>
      <w14:checked w14:val="0"/>  <!-- 0=unchecked, 1=checked -->
    </w14:checkbox>
  </w:sdtPr>
</w:sdt>
```

### Template Structure
- The checkbox table is nested inside: Table 0 → Row 3 → Cell 0 → Nested Table → Row 0
- 5 checkbox cells correspond to 5 expense categories

### Keyword Matching Logic
- Case-insensitive matching
- Searches for keywords anywhere in the acreedor field
- Multiple categories can be checked if multiple keywords match
- Example: "Entidad de pago de Impuestos" → checks "Gastos de Servicios Aduanales"

## Related Files

- Plan: `specs/issue-0-adw-0-sdlc_planner-populate-gastos-nacionales-checkboxes.md`
- Template: `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`
