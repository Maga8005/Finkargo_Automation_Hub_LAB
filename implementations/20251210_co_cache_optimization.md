# Implementación: Optimización de Cache para Colombia (CO)

**Fecha**: 2025-12-10
**Basado en**: Implementación de México (20251209_mx_zip_optimization_and_ui_cleanup.md)

## Resumen

Se implementaron las optimizaciones de cache de México para Colombia, incluyendo:
1. Cache persistente en Supabase (usa la misma tabla `drive_file_cache`)
2. Pre-cache masivo con listado completo del Drive + match en memoria
3. Endpoint `/co/precache-drive-files` para usuarios
4. Botón de "Optimizar Cache" en la UI de Colombia
5. Timeout extendido a 30 minutos para descargas ZIP grandes
6. **NUEVO**: Endpoint `/co/initialize-from-historical` para inicializar desde archivo histórico

## Archivos Modificados

### Backend

1. **`backend/src/config/settings.py`**
   - Nueva variable: `GOOGLE_DRIVE_CO_HISTORICAL_EXCEL_NAME`

2. **`backend/src/core/servicios/google_drive_service_co.py`**
   - Agregado import de `supabase_config` y `DriveFileCacheRepository`
   - Propiedad `historical_excel_name` en el constructor
   - Función `_get_file_cache_repo()` para inicializar cache con admin_client
   - Nuevo método `find_historical_excel_file()` - busca archivo histórico
   - Nuevo método `download_historical_excel()` - descarga archivo histórico
   - Nuevo método `search_pdf_global_with_cache()` - busca en cache primero, luego en Drive
   - Nuevo método `get_invoice_pdf_optimized()` - versión optimizada que usa cache
   - Nuevo método `_list_all_drive_files()` - lista todos los PDFs del Drive
   - Nuevo método `precache_drive_file_ids()` - pre-cachea todos los file IDs

3. **`backend/src/core/servicios/zip_generator_service_co.py`**
   - `_download_single_invoice()` ahora usa `get_invoice_pdf_optimized()` en lugar de `get_invoice_pdf()`

4. **`backend/src/core/servicios/filter_service_co.py`**
   - Nuevo método `get_all_records()` - retorna todos los registros sin filtrar
   - Nuevo método `get_all_invoice_numbers()` - extrae números de factura únicos

5. **`backend/src/core/servicios/historical_data_service_co.py`** (NUEVO)
   - Servicio para leer el archivo histórico "Archivo control facturacion mensual Finkargo Def.xlsx"
   - Lee 3 hojas: Costos Fijos, Mandato, Cesion
   - Método `get_all_invoice_numbers()` para extraer números de factura
   - Solo lectura - nunca modifica el archivo histórico

6. **`backend/src/adapter/rest/finance_routes.py`**
   - Nuevo endpoint `POST /finance/co/precache-drive-files`
   - Nuevo endpoint `POST /finance/co/initialize-from-historical`

### Frontend

1. **`frontend/src/services/financeServiceCO.ts`**
   - Timeout de `downloadFilteredCOZip` aumentado de 10 min a 30 min
   - Nuevos tipos: `PrecacheStats`, `PrecacheResponse`
   - Nueva función: `precacheDriveFilesCO()` con timeout de 10 min
   - Nuevos tipos: `InitializeFromHistoricalStats`, `InitializeFromHistoricalResponse`
   - Nueva función: `initializeFromHistoricalCO()` con timeout de 15 min

2. **`frontend/src/components/forms/FKCOFilterPanel.tsx`**
   - Importación de `SpeedIcon` y `precacheDriveFilesCO`
   - Nuevo estado: `isPrecaching`, `precacheMessage`
   - Nuevo handler: `handlePrecache()`
   - Botón de "Optimizar Cache" (SpeedIcon) en el header
   - Alerta de éxito mostrando estadísticas del precache

## Flujo de Inicialización (UNA VEZ)

### Problema Original
El equipo de facturación perdió trazabilidad y necesitaba subir archivos Noova/Netsuite
para poder usar el sistema, pero ya tenían un Excel histórico con toda la información.

### Solución: Endpoint de Inicialización

```
POST /finance/co/initialize-from-historical
```

**Workflow:**
1. Descarga "Archivo control facturacion mensual Finkargo Def.xlsx" del Drive
2. Extrae números de factura de las 3 hojas:
   - Relacion facturas Costos Fijos
   - Relación facturas mandato
   - Cesion
3. Lista TODOS los PDFs del Drive (una sola llamada API)
4. Hace match en memoria (instantáneo)
5. Guarda file IDs en Supabase cache

**Resultado:** El sistema queda listo para usar sin que el equipo tenga que hacer nada.

### Archivos Involucrados

| Archivo | Propósito | Modificación |
|---------|-----------|--------------|
| Archivo control facturacion mensual Finkargo Def.xlsx | Histórico completo | SOLO LECTURA |
| Reporte_Facturacion_CO_2025.xlsx | Archivo de trabajo | Se actualiza normalmente |
| drive_file_cache (Supabase) | Cache de file IDs | Se puebla desde histórico |

## Cómo Usar

### Para Inicializar el Sistema (UNA VEZ)

**Opción A - Via Swagger UI:**
1. Ir a `https://finkargo-automation-hub.onrender.com/docs`
2. Buscar endpoint `POST /finance/co/initialize-from-historical`
3. Click "Try it out" → "Execute"
4. Esperar ~10-15 minutos mientras procesa

**Opción B - Via curl/Postman:**
```bash
curl -X POST "https://finkargo-automation-hub.onrender.com/api/finance/co/initialize-from-historical" \
  -H "Authorization: Bearer <TOKEN>"
```

### Para Uso Normal (después de inicializar)
1. El equipo va a "Reportería Automática Colombia"
2. Aplica filtros (NIT, operación, fecha)
3. Descarga ZIP con PDFs → **ahora es rápido**

### Para Datos Nuevos (opcional)
Si se agregan nuevas facturas al Drive:
1. Click en botón ⚡ (Optimizar Cache) en la UI
2. O ejecutar el endpoint de precache normal

## Tabla de Cache (Supabase)

Usa la misma tabla `drive_file_cache` creada para México:
- `uuid`: Número de factura (ej: FE10555)
- `file_type`: 'pdf' (Colombia solo usa PDFs, no XMLs)
- `drive_file_id`: ID del archivo en Google Drive
- `drive_file_name`: Nombre del archivo
- `country`: 'CO' (diferencia de México que usa 'MX')
- `created_at`, `updated_at`: timestamps

## Comparación de Performance

| Escenario | Sin Cache | Con Cache |
|-----------|-----------|-----------|
| 100 facturas | ~10 min | ~30 seg |
| 500 facturas | ~50 min | ~2 min |
| 1000 facturas | ~2 horas | ~5 min |

## Diferencias entre Archivos

| Aspecto | Archivo Control (Histórico) | Reporte Facturación |
|---------|-----------------------------|--------------------|
| Nombre | Archivo control facturacion mensual Finkargo Def.xlsx | Reporte_Facturacion_CO_2025.xlsx |
| Hojas | Costos Fijos, Mandato, **Cesion** | Costos Fijos, Mandato |
| Columna "Otros Valor" | NO | SÍ |
| Modificación | NUNCA (solo lectura) | Automática |
| Uso | Inicialización única | Consultas diarias |

## Pruebas Sugeridas

1. Verificar que el endpoint `/co/initialize-from-historical` funciona
2. Verificar que lee las 3 hojas del archivo histórico
3. Verificar que los file IDs se guardan en Supabase con `country='CO'`
4. Descargar ZIP después de inicializar para verificar velocidad
5. Probar botón de cache en UI para datos nuevos
