# Patch: Add Contador/Revisor Fiscal Extraction from RUT Document

## Metadata
adw_id: `b0a5e4a8`
review_change_request: `The app is extracting the revisor fiscal/contador from the certificado de existencia. It may be it is not listed there in many cases. Hence, the app should look for revisor fiscal and contador in the RUT document. The related information is in fields 152 and 153 for last names, 154 and 155 for names for contador last names and names. The contador ID number is in field 149. For Revisor Fiscal Principal the ID number is in field 125 last names in fields 128 and 129, names in 130 and 131. For revisor fiscal suplente, ID is on field 137 while last names are in fields 140 and 141 while names are in fields 142 and 143. For multivalvulas RUT, the revisor fiscal fields are blank while the contador fields have information.`

## Issue Summary
**Original Spec:** specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md
**Issue:** The current implementation extracts contador/revisor fiscal data ONLY from Certificado de Existencia. However, in many cases this information is not listed there (e.g., IMPORTADORA MULTIVALVULAS S.A.S.). The RUT document contains this information in specific fields.
**Solution:** Update the RUT extraction schema to include contador/revisor fiscal fields and modify the cross-validation service to use RUT data as a fallback when Certificado de Existencia lacks this information.

## RUT Field Mapping (Colombian RUT Structure)

### Contador (Accountant) - Section on Page 3/4
| Field | Description |
|-------|-------------|
| 149 | Contador ID number (cédula) |
| 152 | Contador primer apellido (first last name) |
| 153 | Contador segundo apellido (second last name) |
| 154 | Contador primer nombre (first name) |
| 155 | Contador otros nombres (other names) |

### Revisor Fiscal Principal - Section on Page 3/4
| Field | Description |
|-------|-------------|
| 125 | Revisor Fiscal Principal ID number (cédula) |
| 128 | Revisor Fiscal Principal primer apellido |
| 129 | Revisor Fiscal Principal segundo apellido |
| 130 | Revisor Fiscal Principal primer nombre |
| 131 | Revisor Fiscal Principal otros nombres |

### Revisor Fiscal Suplente - Section on Page 3/4
| Field | Description |
|-------|-------------|
| 137 | Revisor Fiscal Suplente ID number (cédula) |
| 140 | Revisor Fiscal Suplente primer apellido |
| 141 | Revisor Fiscal Suplente segundo apellido |
| 142 | Revisor Fiscal Suplente primer nombre |
| 143 | Revisor Fiscal Suplente otros nombres |

## Files to Modify

1. `backend/src/core/servicios/risk/document_extraction_service.py` - Add contador/revisor fiscal fields to RUT extraction schema
2. `backend/src/core/servicios/risk/cross_validation_service.py` - Modify `_validate_contador_revisor_fiscal()` to use RUT as fallback source
3. `backend/tests/test_fraud_detection_service.py` - Add test cases for RUT-based contador/revisor fiscal validation

## Implementation Steps

### Step 1: Update RUT Extraction Schema
- Open `backend/src/core/servicios/risk/document_extraction_service.py`
- Find the `DocumentType.RUT` schema (around line 108)
- Add the following new fields to the properties:

```python
"contador_name": {"type": ["string", "null"], "description": "Full name of contador (accountant) constructed from fields 152-155: primer apellido, segundo apellido, primer nombre, otros nombres"},
"contador_cedula": {"type": ["string", "null"], "description": "Contador ID number from field 149"},
"contador_license": {"type": ["string", "null"], "description": "Contador professional license (tarjeta profesional) if available"},
"revisor_fiscal_principal_name": {"type": ["string", "null"], "description": "Full name of Revisor Fiscal Principal constructed from fields 128-131"},
"revisor_fiscal_principal_cedula": {"type": ["string", "null"], "description": "Revisor Fiscal Principal ID number from field 125"},
"revisor_fiscal_suplente_name": {"type": ["string", "null"], "description": "Full name of Revisor Fiscal Suplente constructed from fields 140-143"},
"revisor_fiscal_suplente_cedula": {"type": ["string", "null"], "description": "Revisor Fiscal Suplente ID number from field 137"},
```

### Step 2: Modify Cross-Validation to Use RUT as Fallback
- Open `backend/src/core/servicios/risk/cross_validation_service.py`
- Modify `_validate_contador_revisor_fiscal()` method (around line 995)
- Add RUT data extraction after getting Certificado de Existencia data:

```python
# Get RUT data as fallback source for contador/revisor fiscal
rut_data = extractions.get(DocumentType.RUT, {}) or {}

# Extract from Certificado first, fallback to RUT if empty
contador_name = cert_data.get('contador_name', '') or rut_data.get('contador_name', '')
contador_cedula = cert_data.get('contador_cedula', '') or rut_data.get('contador_cedula', '')

# For revisor fiscal, prefer principal from Certificado, fallback to RUT principal
revisor_fiscal_name = cert_data.get('revisor_fiscal_name', '') or rut_data.get('revisor_fiscal_principal_name', '')
revisor_fiscal_cedula = cert_data.get('revisor_fiscal_cedula', '') or rut_data.get('revisor_fiscal_principal_cedula', '')

# Also track if we have suplente info from RUT (for additional validation)
revisor_fiscal_suplente_name = rut_data.get('revisor_fiscal_suplente_name', '')
revisor_fiscal_suplente_cedula = rut_data.get('revisor_fiscal_suplente_cedula', '')
```

- Update the `documents_compared` list to include 'rut' when RUT data is used
- Modify `has_registered_professionals` check to account for RUT data source
- Update the validation results to indicate when RUT was used as the data source

### Step 3: Add Unit Tests for RUT-Based Validation
- Open `backend/tests/test_fraud_detection_service.py`
- Add new test cases:

```python
def test_contador_revisor_fiscal_from_rut_when_cert_empty():
    """Test that contador/revisor fiscal is extracted from RUT when Certificado has no data."""

def test_contador_revisor_fiscal_cert_takes_precedence_over_rut():
    """Test that Certificado data takes precedence when both sources have data."""

def test_contador_revisor_fiscal_revisor_suplente_validation():
    """Test that Revisor Fiscal Suplente from RUT is considered in validation."""
```

### Step 4: Update Validation Description Messages
- Modify the CrossValidationResult descriptions to indicate the data source:
  - "Firmante verificado como contador registrado (fuente: RUT)"
  - "Firmante verificado como revisor fiscal registrado (fuente: Certificado de Existencia)"

## Validation

Execute every command to validate the patch is complete with zero regressions:

```bash
# 1. Python Syntax Check
cd backend && python -m py_compile src/core/servicios/risk/document_extraction_service.py
cd backend && python -m py_compile src/core/servicios/risk/cross_validation_service.py

# 2. Backend Linting
cd backend && ./venv/bin/ruff check src/

# 3. Run all backend tests
cd backend && python -m pytest tests/test_fraud_detection_service.py -v

# 4. Frontend Linting (ensure types still work)
cd frontend && npm run lint

# 5. TypeScript Type Check
cd frontend && npx tsc --noEmit

# 6. Frontend Build
cd frontend && npm run build
```

## Patch Scope
**Lines of code to change:** ~80-100 lines
**Risk level:** low
**Testing required:** Unit tests for RUT fallback logic, verify existing Certificado-based validation still works
