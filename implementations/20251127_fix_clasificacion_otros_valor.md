# Fix Clasificación Columna "Otros Valor" - Reportería Colombia

**Fecha:** 2025-11-27
**Módulo:** Finance - Reportería Automática Colombia
**Archivos modificados:**
- `frontend/src/pages/finance/ReporteriaAutomaticaCO.tsx`
- `backend/src/core/servicios/file_processor_co.py`
- `backend/config/colombia/classification_rules.json`

---

## Problema

La columna "Otros Valor" en los reportes generados (tanto Costos Fijos como Mandato) mostraba **todos los valores de las facturas**, cuando solo debería mostrar los valores de registros explícitamente clasificados con categoría "otros" en el archivo `product_classification.json`.

## Causa Raíz

1. **Clasificación fallback incorrecta**: Cuando un código de producto no se encontraba en el JSON de clasificación, el sistema asignaba automáticamente la categoría `OTROS`, lo que causaba que todos los valores fueran a esa columna.

2. **Eliminación de reglas de keywords**: Al eliminar `clasificacion_conceptos` del archivo `classification_rules.json`, el fallback por palabras clave dejó de funcionar y todos los registros sin código de producto reconocido iban a "otros".

3. **Lógica de asignación de valores**: El código asignaba valores a "Otros Valor" incluso cuando la categoría no estaba definida.

---

## Cambios Realizados

### 1. Frontend - `ReporteriaAutomaticaCO.tsx`

**Eliminado:** Sección de instrucciones que aparecía después de cargar los archivos.

```tsx
// ELIMINADO: Bloque "Help Section" con instrucciones de usuario
{!result && !isProcessing && (
  <Grid item xs={12}>
    <Card variant="outlined">
      {/* Instrucciones... */}
    </Card>
  </Grid>
)}
```

**Corregido:** Error de sintaxis en línea 157 - código duplicado con sintaxis incorrecta de MUI Grid.

---

### 2. Backend - `classification_rules.json`

**Eliminado:** Toda la sección `clasificacion_conceptos` con reglas de palabras clave.

**Agregado:** Nueva regla para prefijo `NCIT`:

```json
{
  "tipo_factura_por_prefijo": {
    "NCIT": {
      "tipo": "Mandato",
      "hoja_destino": "Relación facturas mandato"
    }
  }
}
```

---

### 3. Backend - `file_processor_co.py`

#### 3.1 Nuevo método `_extract_product_code()`

Extrae el código numérico del producto de diversos formatos:

```python
def _extract_product_code(self, codigo_producto: str) -> Optional[str]:
    """
    Handles formats like:
    - "101" -> "101"
    - "101 - Interes corriente" -> "101"
    - " 101 " -> "101"
    """
    if not codigo_producto:
        return None

    codigo_str = str(codigo_producto).strip()
    match = re.search(r'(\d+)', codigo_str)
    if match:
        return match.group(1)
    return None
```

#### 3.2 Clasificación mejorada con logging

- Si el código no está en el JSON y no hay reglas de keywords, la categoría queda como `None` (no como "otros")
- Logging detallado para diagnóstico:
  - Muestra de códigos de producto crudos vs extraídos
  - Distribución por categoría
  - Códigos no clasificados

```python
# Categoría None para registros sin clasificar
record.categoria = None  # En lugar de ProductCategory.OTROS
```

#### 3.3 Asignación explícita de valores por categoría

**Hoja Costos Fijos:**
```python
if record.categoria == ProductCategory.COSTOS_FIJOS:
    valores["Valor Costos Fijos"] = record.valor_netsuite
elif record.categoria == ProductCategory.SEGURO_IVA:
    valores["Seguro + Iva"] = record.valor_netsuite
elif record.categoria == ProductCategory.INTERESES_CORRIENTE:
    valores["Int. Corriente Facturado FK"] = record.valor_netsuite
elif record.categoria == ProductCategory.INTERESES_MORA:
    valores["Int. Mora Facturado FK"] = record.valor_netsuite
elif record.categoria == ProductCategory.OTROS:
    # SOLO si explícitamente clasificado como "otros"
    valores["Otros Valor"] = record.valor_netsuite
```

**Hoja Mandato:**
```python
if record.categoria == ProductCategory.INTERESES_CORRIENTE:
    valores["Interes Corriente Facturado"] = record.valor_netsuite
elif record.categoria == ProductCategory.INTERESES_MORA:
    valores["Interes Mora Facturado Mandato"] = record.valor_netsuite
elif record.categoria == ProductCategory.OTROS:
    # SOLO si explícitamente clasificado como "otros"
    valores["Otros Valor"] = record.valor_netsuite
```

---

## Resultado Esperado

1. **Columna "Otros Valor"** solo muestra valores de registros con códigos de producto clasificados explícitamente como `"categoria": "otros"` en `product_classification.json`

2. **Registros sin clasificar** (códigos no reconocidos) no aportan valores a ninguna columna específica

3. **Logs de diagnóstico** permiten identificar códigos de producto faltantes para agregar al JSON

---

## Códigos de Producto con Categoría "otros"

Según `product_classification.json`:
- 302, 303, 307, 308, 310, 311, 312, 313, 315, 401, 403, 406, 500

---

## Próximos Pasos

1. Revisar logs del backend al procesar archivos para identificar códigos no clasificados
2. Agregar códigos faltantes a `product_classification.json` con sus categorías correctas
3. Validar que el reporte generado tenga valores solo en las columnas correspondientes a cada categoría
