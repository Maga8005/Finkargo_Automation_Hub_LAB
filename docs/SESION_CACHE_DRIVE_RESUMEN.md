# Resumen de Sesión: Optimización de Cache de Google Drive

**Fecha:** 5 de Diciembre 2025
**Módulo:** Reportería Automática MX (Finance)
**Objetivo:** Optimizar la generación de ZIPs pre-cacheando IDs de archivos de Google Drive

---

## 🎯 Problema Original

La generación de ZIPs con PDFs y XMLs desde Google Drive era muy lenta:
- **191+ segundos** para descargar 10 facturas
- Cada descarga requería buscar el archivo en Drive por nombre (operación costosa)
- Con 6000+ registros, el proceso era inviable

---

## 🏗️ Solución Implementada

### Arquitectura de Cache

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API    │────▶│   Supabase DB   │
│   (Botón Cache) │     │ /populate-cache  │     │ drive_file_cache│
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Google Drive    │
                        │  (Búsqueda IDs)  │
                        └──────────────────┘
```

### Flujo de Cache
1. Usuario hace clic en "Poblar Cache"
2. Backend lee el Excel maestro y extrae UUIDs
3. Para cada UUID, busca PDF/XML en Google Drive
4. Guarda los file_ids en tabla `drive_file_cache` de Supabase
5. Futuras descargas usan el cache (sin buscar en Drive)

---

## 📁 Archivos Modificados/Creados

### Backend

| Archivo | Descripción |
|---------|-------------|
| `backend/src/repositorio/drive_file_cache_repository.py` | Repositorio para operaciones CRUD del cache con Supabase. Incluye procesamiento por lotes (batch) para evitar errores de URL muy larga. |
| `backend/src/adapter/rest/finance_routes.py` | Endpoint `/populate-drive-cache` que ejecuta el proceso de pre-cache |

### Frontend

| Archivo | Descripción |
|---------|-------------|
| `frontend/src/services/financeServiceMX.ts` | Función `populateDriveCache()` con timeout de 10 minutos (600000ms) |
| `frontend/src/pages/finance/ReporteriaAutomaticaMX.tsx` | UI del botón "Poblar Cache" y manejo de estados |

---

## 🔧 Detalles Técnicos

### Procesamiento por Lotes (Batching)

Para evitar el error **"URL component 'query' too long"**:

```python
# drive_file_cache_repository.py

# Consultas: lotes de 200 UUIDs
BATCH_SIZE = 200  # ~36 chars por UUID = ~7200 chars (seguro para URL)

# Inserciones: lotes de 500 registros
BATCH_SIZE = 500  # Evita request body too large
```

### Timeouts Configurados

| Componente | Timeout | Razón |
|------------|---------|-------|
| `apiClient.ts` (default) | 30,000ms | Operaciones normales |
| `populateDriveCache()` | 600,000ms (10 min) | Cache de 6000+ registros |
| `downloadFilteredMXZip()` | 600,000ms (10 min) | Descarga de múltiples PDFs |

### Tabla de Base de Datos

```sql
-- Tabla: drive_file_cache
CREATE TABLE drive_file_cache (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL,
    file_type VARCHAR(10) NOT NULL,  -- 'pdf' o 'xml'
    drive_file_id VARCHAR(255) NOT NULL,
    drive_file_name VARCHAR(255),
    country VARCHAR(2) DEFAULT 'MX',
    file_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(uuid, file_type, country)
);
```

---

## ⚠️ Estado Actual - PENDIENTE

### Lo que funciona ✅
- UI del botón "Poblar Cache" implementada
- Endpoint `/populate-drive-cache` creado
- Repositorio con batching para queries e inserts
- Timeout extendido en frontend (10 minutos)

### Lo que NO funciona ❌
1. **Datos NO se están insertando en Supabase**
   - El proceso inicia (logs muestran "Starting precache for 6356 UUIDs...")
   - Pero no hay confirmación de inserción en la tabla

2. **Proceso no visible en terminal**
   - El backend parece iniciar pero no continúa
   - Posible problema en `google_drive_service.py` (función `precache_drive_file_ids`)

---

## 🔍 Próximos Pasos para Investigar

### 1. Revisar función de precache en Google Drive Service
```bash
# Buscar el archivo y función
grep -r "precache_drive_file_ids" backend/src/
```

### 2. Verificar que el servicio llame al repositorio
- La función debe llamar a `cache_repo.cache_bulk_file_ids()`
- Agregar más logs para trazar el flujo

### 3. Verificar políticas RLS de Supabase
```sql
-- Verificar que permite inserts
SELECT * FROM pg_policies WHERE tablename = 'drive_file_cache';
```

### 4. Probar inserción manual
```python
# Test directo en Python
from repositorio.drive_file_cache_repository import DriveFileCacheRepository
repo = DriveFileCacheRepository(supabase_client)
result = repo.cache_file_id("test-uuid", "pdf", "test-drive-id", country="MX")
print(f"Insert result: {result}")
```

### 5. Agregar logging detallado
```python
# En la función precache_drive_file_ids
logger.info(f"Step 1: Reading Excel...")
logger.info(f"Step 2: Found {len(uuids)} UUIDs")
logger.info(f"Step 3: Searching Drive for each UUID...")
logger.info(f"Step 4: Calling cache_bulk_file_ids with {len(files)} files")
logger.info(f"Step 5: Cache result: {cached_count}")
```

---

## 📊 Métricas Esperadas

| Escenario | Sin Cache | Con Cache |
|-----------|-----------|-----------|
| Búsqueda por UUID | 2-5 seg/archivo | 0.01 seg/archivo |
| ZIP de 10 facturas | 191+ seg | ~20 seg |
| ZIP de 100 facturas | 30+ min | ~2 min |

---

## 🗂️ Archivos de Referencia

- **Repositorio Cache:** [drive_file_cache_repository.py](../backend/src/repositorio/drive_file_cache_repository.py)
- **Service Frontend MX:** [financeServiceMX.ts](../frontend/src/services/financeServiceMX.ts)
- **Página MX:** [ReporteriaAutomaticaMX.tsx](../frontend/src/pages/finance/ReporteriaAutomaticaMX.tsx)
- **API Routes:** [finance_routes.py](../backend/src/adapter/rest/finance_routes.py)

---

## 📝 Notas Finales

El trabajo de infraestructura está completo:
- ✅ Tabla de cache en Supabase
- ✅ Repositorio con operaciones batch
- ✅ Endpoint de API
- ✅ UI con botón y estados
- ✅ Timeouts configurados

**Falta depurar:** Por qué el proceso de precache no está insertando datos en Supabase. El problema está entre el endpoint y la función `precache_drive_file_ids` en el servicio de Google Drive.

---

*Documento generado: 5 de Diciembre 2025*
