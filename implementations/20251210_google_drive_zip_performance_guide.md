# Guía de Performance: Consulta de Google Drive y Generación de ZIPs

**Fecha:** 2025-12-10
**Autor:** Claude Code
**Contexto:** Optimizaciones aplicadas a México (MX) y Colombia (CO)

---

## Resumen Ejecutivo

Este documento describe las mejores prácticas para consultar archivos de Google Drive y generar paquetes ZIP con excelente performance. Las optimizaciones fueron desarrolladas y probadas en producción para los módulos de facturación de México y Colombia.

**Resultado:** Descargas confiables sin timeouts, con tiempos predecibles y manejo robusto de errores.

---

## Arquitectura de la Solución

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO DE DESCARGA                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CACHE LOOKUP (Supabase)                                     │
│     ┌─────────────┐     ┌─────────────────┐                     │
│     │ Lista UUIDs │────▶│ get_bulk_file_ids│ ◀── UNA consulta   │
│     └─────────────┘     └─────────────────┘      (0.5s)         │
│                                │                                 │
│                                ▼                                 │
│  2. DESCARGA SECUENCIAL (1 hilo)                                │
│     ┌─────────────────────────────────────┐                     │
│     │ Para cada archivo:                  │                     │
│     │   - delay 0.5s                      │                     │
│     │   - download_file_with_retry()      │                     │
│     │   - timeout 90s por intento         │                     │
│     │   - max 3 intentos con backoff      │                     │
│     └─────────────────────────────────────┘                     │
│                                │                                 │
│                                ▼                                 │
│  3. GENERACIÓN ZIP                                              │
│     ┌─────────────────────────────────────┐                     │
│     │ Agregar archivos al ZIP conforme    │                     │
│     │ se descargan (streaming)            │                     │
│     └─────────────────────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuración Óptima

### 1. Constantes de Configuración

```python
# zip_generator_service.py

# CRÍTICO: Usar 1 hilo para evitar competencia de recursos
# Con múltiples hilos, los timeouts se disparan porque comparten el mismo
# límite de conexión/bandwidth hacia Google Drive
MAX_PARALLEL_DOWNLOADS = 1

# Delay entre descargas para evitar rate limiting
# Google Drive puede throttlear si recibe muchas requests seguidas
DOWNLOAD_DELAY_SECONDS = 0.5
```

### 2. Timeout HTTP (httplib2)

```python
# google_drive_service.py

import httplib2
from google_auth_httplib2 import AuthorizedHttp

def authenticate(self) -> Resource:
    # ... obtener credenciales ...

    # CRÍTICO: Timeout de 90 segundos
    # - Menor a 60s: Timeouts frecuentes en archivos grandes
    # - Mayor a 120s: Espera excesiva en archivos problemáticos
    http = httplib2.Http(timeout=90)
    authorized_http = AuthorizedHttp(creds, http=http)

    self.service = build("drive", "v3", http=authorized_http)
    return self.service
```

### 3. Método de Descarga con Retry

```python
def download_file_with_retry(
    self,
    file_id: str,
    file_name: str,
    max_retries: int = 2,
    max_total_time: int = 210
) -> Optional[bytes]:
    """
    Descarga con backoff exponencial.

    CONFIGURACIÓN ÓPTIMA:
    - Timeout por intento: 90s (httplib2)
    - Máximo 2 reintentos (total 3 intentos)
    - Tiempo total máximo: 210s (3.5 minutos)
    - Backoff: 3s, 6s entre intentos
    """
    start_time = time.time()

    for attempt in range(1, max_retries + 2):
        # Verificar tiempo total
        elapsed = time.time() - start_time
        if elapsed >= max_total_time:
            logger.warning(f"Tiempo límite excedido para {file_name}")
            break

        try:
            content = self.download_file(file_id)
            if content:
                if attempt > 1:
                    logger.info(f"Descarga exitosa en intento {attempt}")
                return content
            else:
                logger.warning(f"Intento {attempt}: descarga vacía")

        except Exception as e:
            logger.warning(f"Intento {attempt} error: {e}")

        # Backoff exponencial: 3s, 6s
        if attempt <= max_retries:
            remaining_time = max_total_time - (time.time() - start_time)
            if remaining_time < 30:
                logger.warning("Sin tiempo suficiente para reintentar")
                break

            wait_time = 3 * attempt
            logger.info(f"Esperando {wait_time}s antes de reintentar...")
            time.sleep(wait_time)

    logger.error(f"Descarga fallida para {file_name}")
    return None
```

---

## Cache de File IDs (Supabase)

### Por qué es Crítico

Google Drive API es **muy lento** para buscar archivos por nombre (~2-5 segundos por búsqueda). Con 100 archivos, esto significa 200-500 segundos solo en búsquedas.

**Solución:** Cachear los `file_id` de Drive en Supabase.

### Tabla de Cache

```sql
-- migration_add_drive_file_cache.sql
CREATE TABLE IF NOT EXISTS drive_file_cache (
    id BIGSERIAL PRIMARY KEY,
    uuid VARCHAR(100) NOT NULL,
    file_type VARCHAR(10) NOT NULL,  -- 'pdf' o 'xml'
    drive_file_id VARCHAR(100) NOT NULL,
    drive_file_name VARCHAR(255),
    country VARCHAR(5) DEFAULT 'MX',
    file_size_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(uuid, file_type, country)
);

CREATE INDEX idx_drive_file_cache_uuid ON drive_file_cache(uuid);
CREATE INDEX idx_drive_file_cache_country ON drive_file_cache(country);
```

### Consulta Bulk Optimizada

```python
def get_bulk_file_ids(
    self,
    uuids: List[str],
    country: str = "MX"
) -> Dict[str, Dict[str, str]]:
    """
    Obtiene file IDs para múltiples UUIDs en UNA sola consulta.

    CRÍTICO: Usar batches de 200 UUIDs para evitar error de URL muy larga.
    """
    BATCH_SIZE = 200
    result: Dict[str, Dict[str, str]] = {}

    for i in range(0, len(uuids), BATCH_SIZE):
        batch = uuids[i:i + BATCH_SIZE]

        response = self.db.table(self.table_name)\
            .select('uuid, file_type, drive_file_id')\
            .in_('uuid', batch)\
            .eq('country', country)\
            .execute()

        for row in response.data or []:
            uuid = row['uuid']
            if uuid not in result:
                result[uuid] = {}
            result[uuid][row['file_type']] = row['drive_file_id']

    return result
```

---

## Flujo de Descarga Completo

```python
def _download_invoice_files_parallel(
    self,
    invoices: List[Dict],
    country: str = "MX"
) -> List[Dict]:
    """
    PASO 1: Pre-cargar TODOS los file_ids en UNA consulta
    PASO 2: Descargar secuencialmente con retry
    """

    # PASO 1: Bulk cache lookup (0.5s para 100+ UUIDs)
    file_id_cache: FileIdCache = {}
    cache_repo = _get_file_cache_repo()

    if cache_repo:
        uuids = [inv.get("uuid") for inv in invoices if inv.get("uuid")]
        file_id_cache = cache_repo.get_bulk_file_ids(uuids, country)
        logger.info(f"Cache: {len(file_id_cache)} UUIDs encontrados")

    # PASO 2: Descargar secuencialmente (1 hilo)
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
        future_to_invoice = {
            executor.submit(
                self._download_single_invoice,
                invoice,
                file_id_cache,
                country
            ): invoice
            for invoice in invoices
        }

        for future in as_completed(future_to_invoice):
            result = future.result()
            if result:
                download_results.append(result)

    return download_results


def _download_single_invoice(
    self,
    invoice: Dict,
    file_id_cache: Optional[FileIdCache],
    country: str
) -> Optional[Dict]:
    """
    Descarga archivos de UNA factura.
    """
    uuid = invoice.get("uuid")

    # Delay para evitar rate limiting
    time.sleep(DOWNLOAD_DELAY_SECONDS)

    pdf_content = None
    xml_content = None

    # Usar cache pre-cargado + retry
    if file_id_cache and uuid in file_id_cache:
        cached_ids = file_id_cache[uuid]

        if 'pdf' in cached_ids:
            pdf_content = self.drive_service.download_file_with_retry(
                file_id=cached_ids['pdf'],
                file_name=f"{uuid}.pdf",
                max_retries=2
            )

        if 'xml' in cached_ids:
            xml_content = self.drive_service.download_file_with_retry(
                file_id=cached_ids['xml'],
                file_name=f"{uuid}.xml",
                max_retries=2
            )

    return {
        "uuid": uuid,
        "pdf_content": pdf_content,
        "xml_content": xml_content,
        "pdf_found": pdf_content is not None,
        "xml_found": xml_content is not None,
    }
```

---

## Precache de File IDs

Para descargas muy grandes, se recomienda ejecutar un precache antes:

```python
def precache_drive_file_ids(
    self,
    uuids: List[str],
    country: str = "MX"
) -> Dict[str, int]:
    """
    OPTIMIZADO: Lista TODOS los archivos del Drive una sola vez
    y hace el match en memoria.

    Tiempo: ~2-5 minutos para miles de archivos
    vs horas si se busca uno por uno.
    """

    # 1. Verificar cuáles ya están en cache
    existing_cache = cache_repo.get_bulk_file_ids(uuids, country)
    uuids_to_search = [u for u in uuids if u not in existing_cache]

    # 2. Listar TODOS los archivos del Drive (1 operación)
    all_drive_files = self._list_all_drive_files()

    # 3. Crear índice por nombre para búsqueda O(1)
    file_index = {f['name'].lower(): f for f in all_drive_files}

    # 4. Match en memoria (instantáneo)
    files_to_cache = []
    for uuid in uuids_to_search:
        for ext in ['pdf', 'xml']:
            filename = f"{uuid}.{ext}".lower()
            if filename in file_index:
                files_to_cache.append({
                    'uuid': uuid,
                    'file_type': ext,
                    'drive_file_id': file_index[filename]['id']
                })

    # 5. Guardar en cache (bulk upsert)
    cache_repo.cache_bulk_file_ids(files_to_cache, country)

    return stats
```

---

## Tabla de Configuración Recomendada

| Parámetro | Valor | Razón |
|-----------|-------|-------|
| `MAX_PARALLEL_DOWNLOADS` | `1` | Evita competencia de recursos y timeouts |
| `DOWNLOAD_DELAY_SECONDS` | `0.5` | Evita rate limiting de Google Drive |
| `httplib2 timeout` | `90s` | Balance entre espera y archivos grandes |
| `max_retries` | `2` | 3 intentos totales, suficiente para errores transitorios |
| `max_total_time` | `210s` | 3.5 minutos máximo por archivo |
| `backoff` | `3s, 6s` | Exponencial suave, permite recuperación |
| `BATCH_SIZE` (cache lookup) | `200` | Evita error de URL muy larga en Supabase |

---

## Errores Comunes y Soluciones

### 1. Timeouts Frecuentes con Múltiples Hilos

**Síntoma:** Con 4+ hilos, algunos archivos siempre fallan.

**Causa:** Los hilos compiten por el mismo bandwidth/conexión.

**Solución:** Usar 1 hilo (secuencial).

```python
MAX_PARALLEL_DOWNLOADS = 1
```

### 2. Rate Limiting de Google Drive

**Síntoma:** Errores 403 o 429 después de muchas requests.

**Causa:** Demasiadas requests en poco tiempo.

**Solución:** Agregar delay entre descargas.

```python
time.sleep(0.5)  # Antes de cada descarga
```

### 3. Archivos que Nunca Descargan

**Síntoma:** Un archivo específico siempre falla (ej: FE5526.pdf).

**Causa:** Problema en Google Drive (archivo corrupto, permisos, cold storage).

**Solución:** El sistema lo marca como "no encontrado" y continúa con los demás.

### 4. Búsquedas Lentas (minutos por archivo)

**Síntoma:** Buscar archivos por nombre toma 2-5s cada uno.

**Causa:** Google Drive API es lento para búsquedas.

**Solución:** Cachear file_ids en Supabase.

```python
# Una consulta bulk en lugar de N consultas individuales
file_id_cache = cache_repo.get_bulk_file_ids(uuids, country)
```

---

## Checklist para Nuevos Desarrollos

- [ ] Usar `MAX_PARALLEL_DOWNLOADS = 1` (secuencial)
- [ ] Agregar `DOWNLOAD_DELAY_SECONDS = 0.5`
- [ ] Configurar `httplib2.Http(timeout=90)`
- [ ] Implementar `download_file_with_retry()` con backoff
- [ ] Crear tabla `drive_file_cache` en Supabase
- [ ] Usar `get_bulk_file_ids()` antes de descargar
- [ ] Implementar endpoint de precache para descargas grandes
- [ ] Manejar archivos no encontrados sin bloquear el proceso
- [ ] Generar archivo `PDFs_no_encontrados.txt` en el ZIP

---

## Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| `google_drive_service.py` | Servicio MX con timeout y retry |
| `google_drive_service_co.py` | Servicio CO con timeout y retry |
| `zip_generator_service.py` | Generador ZIP MX con 1 hilo |
| `zip_generator_service_co.py` | Generador ZIP CO con streaming |
| `drive_file_cache_repository.py` | Repository para cache de file IDs |
| `migration_add_drive_file_cache.sql` | Migración de tabla de cache |

---

## Métricas de Performance

### Antes de Optimizaciones
- 16 PDFs: ~6 minutos, varios archivos no encontrados
- Timeouts frecuentes con 4+ hilos
- Archivos aleatorios fallaban en cada ejecución

### Después de Optimizaciones
- 16 PDFs: ~2-3 minutos, todos los archivos encontrados
- Sin timeouts con 1 hilo
- Resultados consistentes en cada ejecución

---

## Implementación Completa

### 1. Migración de Base de Datos

Archivo: `backend/database/migration_add_drive_file_cache.sql`

```sql
-- ============================================================================
-- Migration: Add Drive File Cache Table
-- Purpose: Cache Google Drive file IDs to avoid expensive search operations
-- ============================================================================

-- Create drive_file_cache table
CREATE TABLE IF NOT EXISTS drive_file_cache (
    id BIGSERIAL PRIMARY KEY,
    uuid VARCHAR(100) NOT NULL,
    file_type VARCHAR(10) NOT NULL,  -- 'pdf' or 'xml'
    drive_file_id VARCHAR(100) NOT NULL,
    drive_file_name VARCHAR(255),
    country VARCHAR(5) DEFAULT 'MX',
    file_size_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one file per uuid+type+country
    UNIQUE(uuid, file_type, country)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_drive_file_cache_uuid ON drive_file_cache(uuid);
CREATE INDEX IF NOT EXISTS idx_drive_file_cache_country ON drive_file_cache(country);
CREATE INDEX IF NOT EXISTS idx_drive_file_cache_file_type ON drive_file_cache(file_type);

-- Enable RLS
ALTER TABLE drive_file_cache ENABLE ROW LEVEL SECURITY;

-- Policy: Service role has full access (for backend operations)
CREATE POLICY "Service role full access on drive_file_cache"
ON drive_file_cache
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Authenticated users can read (for debugging/stats)
CREATE POLICY "Authenticated users can read drive_file_cache"
ON drive_file_cache
FOR SELECT
TO authenticated
USING (true);

-- Comment on table
COMMENT ON TABLE drive_file_cache IS 'Cache of Google Drive file IDs to avoid expensive search-by-name operations';
```

### 2. Repository de Cache

Archivo: `backend/src/repositorio/drive_file_cache_repository.py`

```python
"""
Drive File Cache Repository - Database operations for caching Google Drive file IDs.
"""

from typing import Optional, Dict, List
from supabase import Client
import logging

logger = logging.getLogger(__name__)


class DriveFileCacheRepository:
    """Repository for drive file cache operations."""

    def __init__(self, supabase_client: Client):
        self.db = supabase_client
        self.table_name = "drive_file_cache"

    def get_file_id(
        self,
        uuid: str,
        file_type: str,
        country: str = "MX"
    ) -> Optional[str]:
        """Get cached Drive file ID for a UUID and file type."""
        try:
            response = self.db.table(self.table_name)\
                .select('drive_file_id')\
                .eq('uuid', uuid)\
                .eq('file_type', file_type)\
                .eq('country', country)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['drive_file_id']
            return None

        except Exception as e:
            logger.warning(f"Error getting cached file ID for {uuid}.{file_type}: {e}")
            return None

    def cache_file_id(
        self,
        uuid: str,
        file_type: str,
        drive_file_id: str,
        drive_file_name: Optional[str] = None,
        country: str = "MX"
    ) -> bool:
        """Cache a Drive file ID for a UUID."""
        try:
            data = {
                'uuid': uuid,
                'file_type': file_type,
                'drive_file_id': drive_file_id,
                'country': country
            }
            if drive_file_name:
                data['drive_file_name'] = drive_file_name

            # Upsert: insert or update if exists
            self.db.table(self.table_name)\
                .upsert(data, on_conflict='uuid,file_type,country')\
                .execute()

            return True

        except Exception as e:
            logger.warning(f"Error caching file ID for {uuid}.{file_type}: {e}")
            return False

    def get_bulk_file_ids(
        self,
        uuids: List[str],
        country: str = "MX"
    ) -> Dict[str, Dict[str, str]]:
        """
        Get cached file IDs for multiple UUIDs using batched queries.

        Returns:
            Dict mapping UUID to {file_type: drive_file_id}.
        """
        if not uuids:
            return {}

        BATCH_SIZE = 200  # Avoid URL too long error
        result: Dict[str, Dict[str, str]] = {}

        for i in range(0, len(uuids), BATCH_SIZE):
            batch = uuids[i:i + BATCH_SIZE]
            try:
                response = self.db.table(self.table_name)\
                    .select('uuid, file_type, drive_file_id')\
                    .in_('uuid', batch)\
                    .eq('country', country)\
                    .execute()

                for row in response.data or []:
                    uuid = row['uuid']
                    if uuid not in result:
                        result[uuid] = {}
                    result[uuid][row['file_type']] = row['drive_file_id']

            except Exception as e:
                logger.warning(f"Error getting batch: {e}")

        return result

    def cache_bulk_file_ids(
        self,
        files: List[Dict],
        country: str = "MX"
    ) -> int:
        """Cache multiple file IDs using batched upserts."""
        if not files:
            return 0

        BATCH_SIZE = 500
        total_cached = 0

        all_records = []
        for f in files:
            record = {
                'uuid': f['uuid'],
                'file_type': f['file_type'],
                'drive_file_id': f['drive_file_id'],
                'country': country
            }
            if f.get('drive_file_name'):
                record['drive_file_name'] = f['drive_file_name']
            all_records.append(record)

        for i in range(0, len(all_records), BATCH_SIZE):
            batch = all_records[i:i + BATCH_SIZE]
            try:
                self.db.table(self.table_name)\
                    .upsert(batch, on_conflict='uuid,file_type,country')\
                    .execute()
                total_cached += len(batch)
            except Exception as e:
                logger.warning(f"Error caching batch: {e}")

        return total_cached
```

### 3. Endpoint de Precache (Backend)

Archivo: `backend/src/adapter/rest/finance_routes.py`

```python
@router.post("/co/precache-drive-files")
async def precache_drive_files_co():
    """
    Pre-populate the Drive file cache for CO invoices.

    OPTIMIZADO: Lista TODOS los archivos del Drive una sola vez
    y hace el match en memoria (segundos en lugar de horas).

    Recomendado ejecutar antes de descargar ZIPs grandes.
    """
    try:
        drive_service = get_drive_service_co()
        filter_service = get_filter_service_co()

        # Get all invoice numbers from master Excel
        logger.info("Loading invoice numbers from master Excel...")
        all_data = filter_service.get_all_data()

        invoice_numbers = set()
        for row in all_data:
            if row.get("numero_factura"):
                invoice_numbers.add(str(row["numero_factura"]).strip())

        logger.info(f"Found {len(invoice_numbers)} unique invoice numbers")

        # Precache file IDs
        stats = drive_service.precache_drive_file_ids(
            uuids=list(invoice_numbers),
            country="CO"
        )

        return {
            "success": True,
            "message": f"Cache optimizado: {stats['cached']} archivos nuevos",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error in precache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Servicio Frontend

Archivo: `frontend/src/services/financeServiceCO.ts`

```typescript
// ============================================================================
// Cache Optimization Functions
// ============================================================================

export interface PrecacheStats {
  total: number;
  cached: number;
  not_found: number;
  already_cached: number;
}

export interface PrecacheResponse {
  success: boolean;
  message: string;
  stats: PrecacheStats;
}

/**
 * Pre-populate the Drive file cache for CO invoices.
 *
 * This dramatically speeds up ZIP downloads by:
 * 1. Listing all PDF files from Drive in one API call
 * 2. Matching invoice numbers in memory
 * 3. Storing file IDs in Supabase cache
 *
 * Recommended to run once before downloading large ZIPs.
 */
export const precacheDriveFilesCO = async (): Promise<PrecacheResponse> => {
  const response = await apiClient.post<PrecacheResponse>(
    '/finance/co/precache-drive-files',
    {},
    {
      // Allow longer timeout for precache operation (10 minutes)
      timeout: 600000,
    }
  );
  return response.data;
};
```

### 5. Componente UI con Botón de Optimización

Archivo: `frontend/src/components/forms/FKCOFilterPanel.tsx`

```tsx
import {
  Speed as SpeedIcon,
} from '@mui/icons-material';
import {
  precacheDriveFilesCO,
  type PrecacheResponse,
} from '../../services/financeServiceCO';

// En el componente:
const [isPrecaching, setIsPrecaching] = useState(false);
const [precacheMessage, setPrecacheMessage] = useState<string | null>(null);

const handlePrecache = async () => {
  setIsPrecaching(true);
  setPrecacheMessage(null);
  setError(null);

  try {
    const result: PrecacheResponse = await precacheDriveFilesCO();
    if (result.success) {
      setPrecacheMessage(
        `Cache optimizado: ${result.stats.cached} archivos nuevos, ` +
        `${result.stats.already_cached} ya en cache, ` +
        `${result.stats.not_found} no encontrados`
      );
    } else {
      setError(result.message || 'Error al optimizar cache');
    }
  } catch (err) {
    console.error('Error during precache:', err);
    setError('Error al optimizar cache de archivos');
  } finally {
    setIsPrecaching(false);
  }
};

// En el JSX (header del panel de filtros):
<Box display="flex" alignItems="center" gap={1}>
  <Tooltip title="⚡ Optimizar cache: Ejecutar 1 vez antes de descargar ZIPs grandes. Tarda ~5 min pero acelera todas las descargas futuras.">
    <IconButton
      size="small"
      onClick={handlePrecache}
      disabled={isPrecaching}
      color="secondary"
    >
      {isPrecaching ? <CircularProgress size={20} /> : <SpeedIcon />}
    </IconButton>
  </Tooltip>
</Box>

{/* Mensaje de éxito */}
{precacheMessage && (
  <Alert severity="success" onClose={() => setPrecacheMessage(null)}>
    {precacheMessage}
  </Alert>
)}
```

---

## Estructura de Archivos Completa

```
backend/
├── database/
│   └── migration_add_drive_file_cache.sql    # Migración de tabla
├── src/
│   ├── adapter/rest/
│   │   └── finance_routes.py                  # Endpoint /precache-drive-files
│   ├── core/servicios/
│   │   ├── google_drive_service.py            # Servicio MX con timeout/retry
│   │   ├── google_drive_service_co.py         # Servicio CO con timeout/retry
│   │   ├── zip_generator_service.py           # Generador ZIP MX (1 hilo)
│   │   └── zip_generator_service_co.py        # Generador ZIP CO (streaming)
│   └── repositorio/
│       └── drive_file_cache_repository.py     # Repository de cache

frontend/
└── src/
    ├── components/forms/
    │   ├── FKMXFilterPanel.tsx                # Panel MX con botón ⚡
    │   └── FKCOFilterPanel.tsx                # Panel CO con botón ⚡
    └── services/
        ├── financeService.ts                  # Servicio MX con precache
        └── financeServiceCO.ts                # Servicio CO con precache
```

---

## Flujo de Usuario Recomendado

1. **Primera vez o después de agregar muchas facturas:**
   - Click en botón ⚡ "Optimizar cache"
   - Esperar ~5 minutos (una sola vez)
   - Mensaje: "Cache optimizado: X archivos nuevos"

2. **Descargas posteriores:**
   - Filtrar facturas normalmente
   - Click en "Descargar ZIP"
   - Descarga rápida (~2-3 min para 16 PDFs)

3. **Sin cache:**
   - Cada archivo requiere búsqueda en Drive (~2-5s)
   - 100 archivos = 200-500 segundos solo en búsquedas

4. **Con cache:**
   - Una consulta bulk a Supabase (~0.5s)
   - Solo tiempo de descarga

---

## Contacto

Para dudas sobre esta implementación, consultar:
- Código fuente en `backend/src/core/servicios/`
- Historial de conversación del 2025-12-10
