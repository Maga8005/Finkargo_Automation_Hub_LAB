# Optimización de Cache de Drive - Colombia (CO)

## Resumen

Este documento describe la implementación del sistema de cache de archivos de Google Drive para el módulo de facturación de Colombia. El cache permite acelerar significativamente la generación de paquetes ZIP con PDFs de facturas.

## Arquitectura

### Diferencias con México (MX)

| Aspecto | México (MX) | Colombia (CO) |
|---------|-------------|---------------|
| **Identificador** | UUID (ej: `a1b2c3d4-e5f6-...`) | Número de factura (ej: `FE10555`, `ITGC846`) |
| **Tipos de archivo** | PDF + XML | Solo PDF |
| **Estructura de carpetas** | Carpeta base única | Año/Mes (ej: `2024/Enero`) |
| **Servicio de filtro** | `_records` (lista) | `_cached_data` (Dict de DataFrames) |

### Componentes Implementados

```
Backend:
├── src/core/servicios/google_drive_service_co.py
│   ├── _list_all_pdf_files()      # Lista todos los PDFs con paginación
│   └── precache_drive_file_ids()  # Pre-cachea IDs de archivos
│
├── src/adapter/rest/finance_routes.py
│   ├── POST /co/populate-drive-cache  # Poblar cache
│   └── GET /co/cache-stats            # Estadísticas del cache

Frontend:
├── src/services/financeServiceCO.ts
│   ├── populateDriveCacheCO()     # Llamar endpoint de cache
│   └── getDriveCacheStatsCO()     # Obtener estadísticas
│
├── src/components/forms/FKCOFilterResults.tsx
│   └── prop: cacheReady           # Controla botón ZIP
│
└── src/pages/finance/ReporteriaAutomaticaCO.tsx
    └── Flujo de 2 pasos en Tab "Cargar Archivos"
```

### Base de Datos (Supabase)

Tabla: `drive_file_cache`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | SERIAL | ID único |
| `uuid` | VARCHAR | Número de factura (FE10555) |
| `file_type` | VARCHAR | Tipo de archivo (`pdf`) |
| `drive_file_id` | VARCHAR | ID del archivo en Google Drive |
| `country` | VARCHAR | País (`CO`) |
| `created_at` | TIMESTAMP | Fecha de creación |

## Flujo de Uso

### Paso 1: Cargar Archivos Excel

1. Navegar a **Finanzas → Facturación CO → Tab "Cargar Archivos"**
2. Subir los archivos requeridos:
   - **Netsuite Facturas** (obligatorio para Par 1)
   - **Noova Facturas** (obligatorio para Par 1)
   - **Netsuite NC** (opcional, Par 2)
   - **Noova NC** (opcional, Par 2)
3. Click en **"Procesar Archivos"**
4. Esperar a que se genere el reporte consolidado

### Paso 2: Optimizar Cache de Drive

1. Una vez completado el Paso 1, se habilitará el **Paso 2**
2. Click en **"Optimizar Cache"**
3. El sistema:
   - Lee los números de factura del Excel maestro
   - Lista todos los PDFs en Google Drive
   - Asocia cada factura con su archivo PDF
   - Guarda la relación en Supabase
4. Ver estadísticas de cache:
   - **Total cacheados**: Número de archivos en cache
   - **PDFs**: Cantidad de PDFs encontrados
   - **No encontrados**: Facturas sin PDF en Drive

### Paso 3: Consultar y Descargar

1. Ir a **Tab "Consultar Datos"**
2. Aplicar filtros (NIT, operaciones, fechas)
3. Click en **"Consultar"**
4. En los resultados:
   - **"Descargar Excel"**: Solo reporte Excel
   - **"Descargar con PDFs (ZIP)"**: Excel + PDFs (requiere cache)

## Notas Importantes

### El Cache Depende de los Datos del Excel

⚠️ **IMPORTANTE**: El cache solo se genera para las facturas que existen en el archivo Excel maestro de Google Drive.

- Si el Excel solo tiene 1,000 registros, solo se cachearán esos 1,000 PDFs
- Para tener un cache completo, el Excel debe contener TODOS los registros históricos
- Contactar al equipo de facturación para obtener el Excel completo

### Facturas No Encontradas

Cuando aparecen facturas "no encontradas" puede deberse a:

1. **El PDF no existe en Drive**: La factura está en el Excel pero su PDF no se ha subido
2. **Nombre diferente**: El PDF tiene un nombre que no coincide con el número de factura
3. **Ubicación incorrecta**: El PDF está en una carpeta diferente a la esperada

### Regenerar el Cache

Si se agregan nuevos archivos a Drive:

1. El cache existente se preserva (`already_cached`)
2. Solo se procesan las facturas nuevas
3. Ejecutar "Optimizar Cache" nuevamente para incluir los nuevos archivos

## Troubleshooting

### Error: "Cache no configurado"

**Síntoma**: El botón "Descargar con PDFs (ZIP)" está deshabilitado

**Solución**:
1. Verificar que se hayan cargado archivos en el Paso 1
2. Ejecutar "Optimizar Cache" en el Paso 2
3. Esperar a que el proceso termine

### Error: "AttributeError: '_records'"

**Causa**: Incompatibilidad con la estructura del servicio CO

**Solución**: Este error fue corregido. El servicio CO usa `_cached_data` (diccionario de DataFrames) en lugar de `_records`.

### Pocos Archivos Cacheados

**Síntoma**: Se cachean menos archivos de los esperados

**Causa**: El Excel maestro tiene registros limitados

**Solución**:
1. Obtener el Excel completo del equipo de facturación
2. Subir el archivo a Google Drive (reemplazando el actual)
3. Ejecutar "Optimizar Cache" nuevamente

### ZIP Vacío o Incompleto

**Síntoma**: El ZIP descargado no tiene todos los PDFs

**Causas posibles**:
1. Facturas sin PDF en Drive
2. Cache desactualizado
3. Nombres de archivo no coincidentes

**Solución**:
1. Verificar que los PDFs existan en Drive
2. Ejecutar "Optimizar Cache" para actualizar
3. Revisar nomenclatura de archivos

## Endpoints API

### POST /api/finance/co/populate-drive-cache

Pobla el cache de archivos de Drive para Colombia.

**Request**: Ningún body requerido

**Response**:
```json
{
  "success": true,
  "message": "Cache poblado exitosamente",
  "stats": {
    "total": 1006,
    "cached": 1000,
    "not_found": 6,
    "already_cached": 0
  }
}
```

### GET /api/finance/co/cache-stats

Obtiene estadísticas del cache de Colombia.

**Response**:
```json
{
  "success": true,
  "country": "CO",
  "total_cached": 1000,
  "pdf_count": 1000,
  "xml_count": 0,
  "cache_ready": true,
  "message": "Cache CO tiene 1000 archivos (1000 PDFs)"
}
```

## Código Clave

### Extracción de Números de Factura

```python
# En finance_routes.py
data_dict = filter_service._load_excel_from_drive()
for sheet_name, df in data_dict.items():
    if "# Factura" in df.columns:
        factura_values = df["# Factura"].dropna().astype(str)
        invoice_numbers.update(factura_values.tolist())
```

### Matching de Archivos

```python
# En google_drive_service_co.py
def precache_drive_file_ids(self, invoice_numbers, country="CO"):
    # 1. Listar TODOS los PDFs de Drive
    all_files = self._list_all_pdf_files()

    # 2. Crear índice por número de factura
    pdf_index = {}
    for f in all_files:
        base_name = f["name"].replace(".pdf", "").replace(".PDF", "")
        pdf_index[base_name.upper()] = f["id"]

    # 3. Buscar cada factura en el índice (O(1))
    for inv_num in invoice_numbers:
        key = inv_num.upper()
        if key in pdf_index:
            # Guardar en cache
```

## Próximos Pasos

1. **Obtener Excel Completo**: Contactar al equipo de facturación para obtener el archivo con todos los registros históricos

2. **Subir a Drive**: Reemplazar el Excel actual con la versión completa

3. **Repoblar Cache**: Ejecutar "Optimizar Cache" para indexar todos los PDFs

4. **Monitorear**: Verificar estadísticas de cache regularmente

---

*Documentación creada: 2025-12-07*
*Versión: 1.0*
