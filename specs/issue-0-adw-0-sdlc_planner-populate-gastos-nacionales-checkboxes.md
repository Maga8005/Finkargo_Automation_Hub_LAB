# Chore: Populate Gastos Nacionales de Importación Checkboxes Based on Anexo Items

## Chore Description
The Solicitud de Desembolso Word template contains a checkbox table ("Información de los Gastos Nacionales de Importación") with 5 expense categories that should be automatically checked based on the line items in the Anexo I table. Currently, this checkbox table is not being populated.

**Template Structure (Table 0, Row 3, Nested Table):**
The nested table has 5 checkbox categories:
1. **Tributos Aduaneros** - Check if acreedor mentions tributos/aduanero/DIAN
2. **Gastos de Servicios Aduanales** - Check if acreedor mentions "Entidad de pago de Impuestos" or similar tax payment entities
3. **Gastos Logísticos** - Check if acreedor mentions logística/logístico
4. **Gastos de Transporte** - Check if acreedor mentions transporte/flete
5. **Gastos de Almacenamiento** - Check if acreedor mentions almacenamiento/bodega/storage

**Checkbox XML Structure:**
Each checkbox is a Word Structured Document Tag (SDT) with:
- `<w14:checkbox>` element
- `<w14:checked w14:val="0"/>` for unchecked
- `<w14:checked w14:val="1"/>` for checked

**Mapping Logic:**
When the acreedor field contains keywords related to each category, the corresponding checkbox should be checked. The key mapping is:
- "Entidad de pago de Impuestos" or tax-related → **Gastos de Servicios Aduanales**
- DIAN/tributo/arancel → **Tributos Aduaneros**
- transporte/flete/envío → **Gastos de Transporte**
- almacén/bodega/storage → **Gastos de Almacenamiento**
- logística/operador logístico → **Gastos Logísticos**

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/document_service.py` - Contains `generate_solicitud_desembolso_document()` method which generates the document. Need to add logic to populate the checkbox table based on anexo_items. The `_populate_anexo_table()` method is already here and can serve as reference for table manipulation.

- `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx` - The Word template with:
  - Table 0, Row 3, Cell 0 contains a nested table with 5 checkbox cells
  - Each cell uses `<w:sdt>` (Structured Document Tag) with `<w14:checkbox>` element
  - Checkbox state is controlled by `<w14:checked w14:val="0|1"/>`

- `backend/src/interface/legal_dtos.py` - Contains `AnexoItem` model with `acreedor`, `numero_instrumento`, `monto` fields. The `acreedor` field contains the text used for checkbox matching.

**Reference files (no changes needed):**
- `backend/src/core/servicios/cotizacion_parser_service.py` - Shows example acreedor values like "Entidad de pago de Impuestos"

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Keyword-to-Category Mapping Constants

- Open `backend/src/core/servicios/document_service.py`
- Add constants at the module level (after imports) defining keyword mappings for each expense category:

```python
# Keyword mappings for Gastos Nacionales de Importación checkboxes
GASTOS_CATEGORY_KEYWORDS = {
    'tributos_aduaneros': ['tributo', 'arancel', 'dian', 'aduanero', 'aduana'],
    'servicios_aduanales': ['impuesto', 'entidad de pago', 'pago de impuestos', 'servicio aduanal'],
    'logisticos': ['logístic', 'logistic', 'operador logístico'],
    'transporte': ['transporte', 'flete', 'envío', 'envio', 'carga'],
    'almacenamiento': ['almacén', 'almacen', 'almacenamiento', 'bodega', 'storage', 'depósito', 'deposito'],
}

# Index mapping for checkbox cells in nested table (Table 0, Row 3, Cell 0, Nested Table Row 0)
GASTOS_CHECKBOX_INDICES = {
    'tributos_aduaneros': 0,
    'servicios_aduanales': 1,
    'logisticos': 2,
    'transporte': 3,
    'almacenamiento': 4,
}
```

### Step 2: Implement Helper Function to Determine Categories from Anexo Items

- Add a new helper method `_determine_gastos_categories(self, anexo_items: list) -> set[str]`:
- This method iterates through anexo_items and returns a set of category keys that should be checked
- Use case-insensitive matching for keywords

```python
def _determine_gastos_categories(self, anexo_items: list) -> set[str]:
    """
    Analyze anexo items to determine which expense categories should be checked.

    Args:
        anexo_items: List of anexo items with 'acreedor' field

    Returns:
        Set of category keys that should be checked (e.g., {'servicios_aduanales', 'transporte'})
    """
    categories = set()

    for item in anexo_items:
        acreedor = item.get('acreedor', '').lower()

        for category, keywords in GASTOS_CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in acreedor:
                    categories.add(category)
                    break  # Found match for this category, move to next category

    return categories
```

### Step 3: Implement Helper Function to Check Checkboxes in Nested Table

- Add a new helper method `_populate_gastos_checkboxes(self, doc: Document, categories: set[str]) -> None`:
- This method finds the nested table in Table 0, Row 3, Cell 0
- For each category in the set, updates the checkbox XML to checked state

```python
def _populate_gastos_checkboxes(self, doc: Document, categories: set[str]) -> None:
    """
    Populate the Gastos Nacionales de Importación checkbox table.

    The nested table is in: Table 0 → Row 3 → Cell 0 → Nested Table → Row 0
    Each cell (0-4) contains a checkbox SDT that needs to be checked/unchecked.

    Args:
        doc: Document object
        categories: Set of category keys to check (e.g., {'servicios_aduanales'})
    """
    from lxml import etree

    # Define namespace for w14 (Word 2010 extensions)
    W14_NS = 'http://schemas.microsoft.com/office/word/2010/wordml'

    if len(doc.tables) < 1:
        logger.warning("Document has no tables - cannot populate gastos checkboxes")
        return

    main_table = doc.tables[0]
    if len(main_table.rows) < 4:
        logger.warning("Main table has fewer than 4 rows - cannot find gastos row")
        return

    gastos_cell = main_table.rows[3].cells[0]

    if not gastos_cell.tables:
        logger.warning("No nested table found in gastos cell")
        return

    nested_table = gastos_cell.tables[0]
    checkbox_row = nested_table.rows[0]

    for category, cell_index in GASTOS_CHECKBOX_INDICES.items():
        if cell_index >= len(checkbox_row.cells):
            logger.warning(f"Cell index {cell_index} out of range for category {category}")
            continue

        cell = checkbox_row.cells[cell_index]
        should_check = category in categories

        # Access the cell's XML and find/modify the checkbox
        cell_xml = cell._tc

        # Find w14:checked element and update its value
        for checked_elem in cell_xml.iter('{%s}checked' % W14_NS):
            checked_elem.set('{%s}val' % W14_NS, '1' if should_check else '0')
            logger.debug(f"Set checkbox '{category}' to {'checked' if should_check else 'unchecked'}")

    logger.info(f"Populated gastos checkboxes: {categories}")
```

### Step 4: Update generate_solicitud_desembolso_document to Call Checkbox Population

- In the `generate_solicitud_desembolso_document()` method, after populating the Anexo I table and before returning:
- Call `_determine_gastos_categories()` with the anexo_items
- Call `_populate_gastos_checkboxes()` with the document and categories

Add this code after the `_populate_anexo_table()` call (around line 1202):

```python
# Populate Gastos Nacionales checkboxes based on anexo items
if anexo_items:
    gastos_categories = self._determine_gastos_categories(anexo_items)
    self._populate_gastos_checkboxes(doc, gastos_categories)
```

### Step 5: Add Unit Tests for the New Functionality

- Open or create `backend/tests/test_document_service.py`
- Add tests for:
  - `_determine_gastos_categories()` with various acreedor values
  - Verify "Entidad de pago de Impuestos" maps to 'servicios_aduanales'
  - Verify multiple categories can be detected from multiple anexo items

### Step 6: Run Validation Commands

- Execute all validation commands to ensure the change works correctly and introduces no regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

### Checkbox XML Structure Details
The checkboxes use Word 2010 extensions (`w14` namespace). The XML structure is:
```xml
<w:sdt>
  <w:sdtPr>
    <w14:checkbox>
      <w14:checked w14:val="0"/>  <!-- 0=unchecked, 1=checked -->
      <w14:checkedState w14:val="2612" w14:font="MS Gothic"/>
      <w14:uncheckedState w14:val="2610" w14:font="MS Gothic"/>
    </w14:checkbox>
  </w:sdtPr>
  <w:sdtContent>
    <!-- Checkbox visual content -->
  </w:sdtContent>
</w:sdt>
```

### Keyword Mapping Rationale
- **"Entidad de pago de Impuestos"** → Gastos de Servicios Aduanales: This is the standard name for tax payment service providers in Colombian customs processes
- The mapping is case-insensitive to handle variations in data entry
- Multiple categories can be checked if anexo items match multiple keyword sets

### Testing Recommendations
1. Test with real Cotización PDF containing "Entidad de pago de Impuestos"
2. Verify generated document has the checkbox checked in Word/LibreOffice
3. Test edge cases: empty anexo_items, no keyword matches, all keyword matches

### Dependencies
- `lxml` is already a dependency of `python-docx`, no new dependencies needed
- The Word 2010 namespace `w14` is standard for modern .docx files
