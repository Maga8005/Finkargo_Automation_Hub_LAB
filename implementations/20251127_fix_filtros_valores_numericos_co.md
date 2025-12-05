# Fix: Valores Numéricos en Filtros de Reportería CO

**Fecha:** 2025-11-27
**Feature:** Reportería Automática CO - Filtros y Consultas
**Estado:** En progreso - Pendiente de pruebas

---

## Resumen del Problema

Los valores numéricos (Costos Fijos, Interés Corriente, Interés Mora, Valor Neto, Otros) no aparecían en:
1. La previsualización de resultados en la interfaz
2. El Excel descargado con los datos filtrados

### Causa Raíz Identificada

**Problema de Leading Zeros en Códigos de Producto:**
- Los archivos de Noova tienen códigos de producto con ceros a la izquierda: `"0302"`, `"0101"`, etc.
- El archivo `product_classification.json` tiene los códigos SIN ceros: `"302"`, `"101"`, etc.
- Esto causaba que la clasificación fallara y los valores no se asignaran a las columnas correctas.

---

## Archivos Modificados

### 1. `backend/src/core/servicios/file_processor_co.py`

**Función `_extract_product_code()`** - Arreglada para remover leading zeros:

```python
def _extract_product_code(self, codigo_producto: str) -> Optional[str]:
    if not codigo_producto:
        return None
    codigo_str = str(codigo_producto).strip()
    match = re.search(r'(\d+)', codigo_str)
    if match:
        # Remove leading zeros by converting to int and back to string
        extracted = match.group(1)
        try:
            return str(int(extracted))  # "0302" -> "302"
        except ValueError:
            return extracted
    return None
```

**Logging agregado** para debug de:
- Muestra de códigos de producto (raw vs extracted)
- Distribución por categoría
- Cantidad de registros con valores asignados

### 2. `backend/src/core/servicios/filter_service_co.py`

**Cambios:**
- Removido `dtype=str` al leer Excel (preserva tipos numéricos)
- Mejorada función `safe_get()` para manejar valores numéricos correctamente
- Agregado logging extensivo para debug de valores

**Función `safe_get()` mejorada:**
```python
def safe_get(key: str, as_float: bool = False) -> Any:
    col_name = col_map.get(key)
    if not col_name or col_name not in row.index:
        return None
    val = row[col_name]
    if pd.isna(val):
        return None
    if as_float:
        try:
            if isinstance(val, (int, float)):
                result = float(val)
                return result if result != 0 else None  # None para 0s
            str_val = str(val).replace(",", "").strip()
            if str_val == "" or str_val == "0" or str_val == "0.0":
                return None
            return float(str_val)
        except (ValueError, TypeError):
            return None
    return str(val) if val else None
```

### 3. `backend/src/interface/finance_dtos_co.py`

**Cambio:** Removidos los `alias` de `COFilteredRecord` que causaban problemas de serialización.

**Antes:**
```python
valor_costos_fijos: Optional[float] = Field(None, alias="Valor Costos Fijos")
```

**Después:**
```python
valor_costos_fijos: Optional[float] = Field(None, description="Valor Costos Fijos")
```

### 4. `backend/src/core/servicios/excel_merge_service_co.py`

**Agregado:** Logging de debug para rastrear valores durante el merge:
- Cantidad de registros con valores asignados
- Muestras de valores (factura, categoría, valor)

---

## Pasos para Probar la Solución

### Paso 1: Reiniciar el Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 2: Limpiar el Cache de Filtros
Llamar al endpoint (desde Postman, curl, o la consola del navegador):
```
DELETE /api/finance/co/filter/cache
```

O esperar 5 minutos (TTL del cache).

### Paso 3: Re-procesar los Archivos
Volver a subir los 4 archivos Excel en la interfaz de Reportería Automática CO:
- Netsuite Facturas
- Netsuite NC (Notas de Crédito)
- Noova Facturas
- Noova NC

### Paso 4: Verificar en los Logs
Buscar en los logs del backend:

```
[convert_records_to_dicts] Sheet type: costos_fijos, Total records: X, Records with values: Y
[Costos Fijos Sheet] Total: X, con valor_netsuite: Y, con categoria: Z, con ambos (valor asignado): W
```

Si `W > 0`, los valores se están asignando correctamente.

### Paso 5: Probar el Filtrado
1. Ir a Reportería Automática CO
2. Seleccionar un NIT
3. Seleccionar operaciones
4. Hacer clic en "Consultar"
5. Verificar que los valores numéricos aparezcan en la tabla

---

## Logs de Debug Esperados

### Al procesar archivos (POST /api/finance/co/process-files):
```
Muestra de códigos de producto: ["raw='0302' -> extracted='302'", ...]
Distribución por categoría: {'intereses_corriente': 150, 'otros': 50, ...}
[convert_records_to_dicts] Sample values: ["factura=FE12345, categoria=intereses_corriente, valor=1500000.0"]
```

### Al filtrar (POST /api/finance/co/filter):
```
[Costos Fijos] Primera fila - Valor Costos Fijos: 1500000.0 (type: float)
[_df_to_records] Sheet 'Relacion facturas Costos Fijos' - Raw row sample:
  valor_costos_fijos (Valor Costos Fijos): 1500000.0 (type: float)
Sample record 1: valor_costos_fijos=1500000.0, int_corriente=None, valor_neto=1500000.0
```

---

## Archivos de Configuración Relacionados

### `backend/config/colombia/product_classification.json`
Mapeo de códigos de producto a categorías:
```json
{
  "clasificacion_productos": {
    "101": { "categoria": "intereses_corriente" },
    "102": { "categoria": "intereses_mora" },
    "103": { "categoria": "costos_fijos" },
    "302": { "categoria": "otros" },
    ...
  },
  "mapeo_categoria_columna": {
    "costos_fijos": "Valor Costos Fijos",
    "intereses_corriente": "Int. Corriente Facturado FK",
    ...
  }
}
```

### `backend/config/colombia/classification_rules.json`
Reglas para determinar hoja destino por prefijo de factura:
```json
{
  "tipo_factura_por_prefijo": {
    "FE": { "tipo": "Finkargo", "hoja_destino": "Relacion facturas Costos Fijos" },
    "ITPA": { "tipo": "Mandato", "hoja_destino": "Relación facturas mandato" },
    ...
  }
}
```

---

## Estado Actual

| Componente | Estado |
|------------|--------|
| Fix leading zeros | Implementado |
| Logging de debug | Implementado |
| Serialización DTO | Corregida |
| Pruebas con datos reales | Pendiente |

---

## Próximos Pasos (Mañana)

1. Ejecutar los pasos de prueba descritos arriba
2. Verificar los logs del backend para confirmar que los valores se están asignando
3. Si persiste el problema, revisar los logs detallados y ajustar según sea necesario
4. Una vez funcionando, remover o reducir el logging de debug

---

## Notas Técnicas

### Flujo de Datos

```
Archivos Excel (Netsuite + Noova)
         ↓
file_processor_co.py (consolidate + classify)
         ↓
excel_merge_service_co.py (merge con Drive)
         ↓
Google Drive (Excel maestro)
         ↓
filter_service_co.py (lee y filtra)
         ↓
Frontend (FKCOFilterResults.tsx)
```

### Puntos Críticos de Verificación

1. **Consolidación:** `valor_netsuite` debe estar presente (match por `numero_factura`)
2. **Clasificación:** `categoria` debe estar asignada (match de código de producto)
3. **Ambos requeridos:** Solo se asigna valor si AMBOS existen
4. **Lectura:** Pandas debe preservar tipos numéricos (no `dtype=str`)
