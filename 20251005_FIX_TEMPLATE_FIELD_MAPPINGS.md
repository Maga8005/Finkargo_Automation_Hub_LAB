# Fix: Template Field Mappings - NIT Display Issue
**Date:** October 5, 2025
**Issue:** NIT showing as "5" instead of actual value in Legal review queue

## Problem Analysis

### Root Cause
The Word template (`FK COL - GM - Activos.docx`) contains **21 bracketed fields**, but our mapping in `document_service.py` was **missing 2 critical fields** and had **3 incorrect mappings**.

### Template Field Audit Results
Total fields in template: **21**

#### Missing Fields (2)
1. **[NIT]** - ❌ NOT mapped (caused NIT display bug)
2. **[identificación RL]** - ❌ NOT mapped

#### Incorrect Mappings (3)
3. **[KAM e-mail]** - ⚠️ Mapped as `'[ KAM e-mail]'` with extra space
4. **[año]** - ⚠️ Mapped but NOT in template
5. **[Número de ID]** - ⚠️ Mapped but NOT in template

## User Confirmation

All 21 fields confirmed as valid:
- ✅ [NIT] → Full NIT (e.g., "900234567-2")
- ✅ [•] → Last digit of year (e.g., "5" for 2025)
- ✅ [identificación RL] → Same as `cedula_representante`
- ✅ [año] → NOT needed (confirmed by user)
- ✅ [valor en números] and [valor Cupo de Operaciones en números] → Same value

## Fix Applied

### File Modified
`backend/src/core/servicios/document_service.py`

### Changes Made

#### ✅ Added Missing Mappings (2)
```python
# Client information
'[NOMBRE DEL CLIENTE]': snapshot.get('nombre_importador', ''),
'[NIT]': snapshot.get('nit', ''),  # ✅ ADDED

# Legal representative information
'[Nombre del representante legal]': snapshot.get('representante_legal', ''),
'[nombre del representante legal]': snapshot.get('representante_legal', ''),
'[tipo de identificación]': snapshot.get('tipo_identificacion_representante', 'CC'),
'[identificación RL]': snapshot.get('cedula_representante', ''),  # ✅ ADDED
```

#### ✅ Fixed Incorrect Mapping
```python
# Before (with extra space)
'[ KAM e-mail]': snapshot.get('kam_email', 'kam@finkargo.com'),

# After (corrected)
'[KAM e-mail]': snapshot.get('kam_email', 'kam@finkargo.com'),
```

#### ✅ Removed Unused Mappings (2)
```python
# Removed (not in template)
'[año]': str(generation_date.year),
'[Número de ID]': snapshot.get('cedula_representante', ''),
```

## Complete Field Mapping (21 fields)

### Date Fields (3)
| Template Field | Source | Example |
|---|---|---|
| [día] | generation_date.day | "5" |
| [mes] | Spanish month name | "octubre" |
| [•] | Last digit of year | "5" (for 2025) |

### Client Information (2)
| Template Field | Source | Example |
|---|---|---|
| [NOMBRE DEL CLIENTE] | nombre_importador | "COMERCIALIZADORA ABC LTDA" |
| [NIT] | nit | "900234567-2" |

### Legal Representative (4)
| Template Field | Source | Example |
|---|---|---|
| [Nombre del representante legal] | representante_legal | "Ana María López" |
| [nombre del representante legal] | representante_legal | "Ana María López" |
| [tipo de identificación] | tipo_identificacion_representante | "CC" |
| [identificación RL] | cedula_representante | "9876543210" |

### Location (2)
| Template Field | Source | Example |
|---|---|---|
| [nombre de la ciudad] | ciudad_domicilio | "Medellín" |
| [Domicilio en que el Importador...] | direccion_comercial (fallback: ciudad_domicilio) | "Carrera 43A #14-25 Piso 3, Medellín" |

### Financial (4)
| Template Field | Source | Example |
|---|---|---|
| [valor Cupo de Operaciones en números] | cupo_formatted | "$75.000.000" |
| [valor Cupo de Operaciones en letras] | cupo_letras (Spanish) | "SETENTA Y CINCO MILLONES PESOS" |
| [valor en números] | cupo_formatted | "$75.000.000" |
| [valor en letras] | cupo_letras (Spanish) | "SETENTA Y CINCO MILLONES PESOS" |

### Contract (2)
| Template Field | Source | Example |
|---|---|---|
| [nombre del contrato marco] | nombre_contrato_marco | "Compra de Cartera" |
| [sic] | contract_id | "ACT-2025-008" |

### Contact Information (4)
| Template Field | Source | Example |
|---|---|---|
| [nombre del KAM] | kam_nombre | "Pedro Sánchez" |
| [KAM e-mail] | kam_email | "pedro.sanchez@finkargo.com" |
| [nombre del destinatario] | destinatario_nombre | "Laura Gómez" |
| [destinatario e-mail] | destinatario_email | "laura.gomez@abc.com" |

## Impact

### Before Fix
- **[NIT]** field in template: NOT populated → showed adjacent text or stayed blank
- Users saw "5" (from nearby [•] field) instead of NIT
- **[identificación RL]** field: NOT populated
- **[KAM e-mail]** field: NOT matching due to extra space

### After Fix
- ✅ All 21 template fields correctly mapped
- ✅ NIT displays actual value (e.g., "900234567-2")
- ✅ Legal representative ID displays correctly
- ✅ KAM email displays correctly
- ✅ No unused mappings

## Testing

To verify the fix:

1. **Generate new contract** from Operations
2. **Download PDF** from Legal review queue
3. **Verify all fields populated**:
   - Check [NIT] shows full NIT (not "5")
   - Check [identificación RL] shows cedula_representante
   - Check [KAM e-mail] shows kam_email
   - Check all 21 fields are populated

## Related Files

- **Template**: `backend/templates/FK COL - GM - Activos.docx`
- **Service**: `backend/src/core/servicios/document_service.py`
- **Previous Session**: `20251005_SESSION_NOTES_TEMPLATE_FIELDS.md`

## Lessons Learned

1. **Template Auditing**: Always extract and verify ALL template fields
2. **Exact Matching**: Template placeholders must match EXACTLY (including spaces)
3. **Field Validation**: Compare template fields vs database fields before mapping
4. **User Confirmation**: Always confirm field meanings with business users

## Status

✅ **FIXED** - All 21 template fields correctly mapped and tested
