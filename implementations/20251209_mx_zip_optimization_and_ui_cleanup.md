# Sesión de Desarrollo: Optimización ZIP MX y Limpieza de UI

**Fecha:** 2025-12-09
**Módulo:** Reportería Automática MX (Facturación México)
**Desarrollador:** Claude Code + María Gaitán

---

## Resumen Ejecutivo

Esta sesión abordó dos objetivos principales:
1. **Optimizar las descargas de archivos ZIP** que contenían PDFs/XMLs de facturas mexicanas
2. **Simplificar la interfaz de usuario** eliminando funcionalidad redundante

---

## Problema 1: Timeout en Descargas ZIP Grandes

### Síntoma
El usuario reportó que las descargas ZIP de ~338 registros tardaban aproximadamente 25 minutos y el frontend se desconectaba antes de recibir el archivo, mostrando error de timeout.

### Causa Raíz
1. **Timeout del frontend muy corto**: El timeout de axios estaba configurado en 10 minutos (600,000ms), insuficiente para descargas grandes
2. **Cache miss masivo**: Cada búsqueda de archivo PDF/XML requería una llamada individual a Google Drive API
3. **Sin pre-caching**: No existía forma de pre-poblar el cache antes de descargas grandes

### Solución Implementada

#### 1. Aumento de Timeout en Frontend
**Archivo:** `frontend/src/services/financeServiceMX.ts`

```typescript
// Antes: timeout: 600000 (10 min)
// Después:
export const downloadFilteredMXZip = async (request: MXFilterRequest): Promise<Blob> => {
  const response = await apiClient.post(
    `${BASE_URL}/mx/filter/download-zip`,
    request,
    {
      responseType: 'blob',
      timeout: 1800000, // 30 minutes for large ZIP files
    }
  );
  return response.data;
};
```

#### 2. Sistema de Pre-Cache Optimizado
**Archivo:** `backend/src/core/servicios/google_drive_service.py`

Se implementó el método `precache_drive_file_ids()` con una estrategia optimizada:

```python
def precache_drive_file_ids(self, uuids: List[str], country: str = "MX") -> Dict[str, int]:
    """
    OPTIMIZADO: Lista todos los archivos del Drive una sola vez
    y hace el match en memoria (segundos en lugar de horas).
    """
    # 1. Verificar cuáles ya están en cache (Supabase)
    existing_cache = cache_repo.get_bulk_file_ids(uuids, country)

    # 2. Listar TODOS los archivos del Drive en UNA llamada
    all_drive_files = self._list_all_drive_files()

    # 3. Crear índice O(1) por nombre de archivo
    file_index = {f['name'].lower(): f for f in all_drive_files}

    # 4. Match UUIDs con archivos en memoria (instantáneo)
    for uuid in uuids_to_search:
        for ext in ['pdf', 'xml']:
            filename = f"{uuid}.{ext}".lower()
            if filename in file_index:
                all_files_to_cache.append({...})

    # 5. Guardar en cache en batch
    cache_repo.cache_bulk_file_ids(all_files_to_cache, country)
```

**Ventaja:** En lugar de hacer N×2 llamadas a Drive API (una por cada PDF/XML), ahora hace:
- 1 llamada para listar todos los archivos
- Match en memoria O(1) por archivo
- 1 operación batch para guardar en Supabase

#### 3. Endpoint de Pre-Cache
**Archivo:** `backend/src/adapter/rest/finance_routes.py`

```python
@router.post("/mx/precache-drive-files")
async def precache_drive_files_mx(current_user: dict = Depends(get_current_user)):
    filter_service = get_filter_service_mx()
    all_records = filter_service.get_all_records()  # Nuevo método
    uuids = [r.uuid for r in all_records if r.uuid]

    drive_service = get_drive_service()
    stats = drive_service.precache_drive_file_ids(uuids, country="MX")

    return {"success": True, "stats": stats}
```

#### 4. Método `get_all_records()` en Filter Service
**Archivo:** `backend/src/core/servicios/filter_service_mx.py`

```python
def get_all_records(self) -> List[MXFilteredRecord]:
    """
    Get all records from the MX master Excel (no filtering).
    Used for precaching Drive file IDs.
    """
    df = self._load_excel_from_drive()
    records = self._df_to_records(df)
    return records
```

---

## Problema 2: Botón de Pre-Cache para Usuarios No Técnicos

### Síntoma
El usuario indicó: "El precache lo va a tener que hacer un usuario que no es técnico en la vida real"

### Solución
Se agregó un botón en la UI con ayuda contextual.

**Archivo:** `frontend/src/components/forms/FKMXFilterPanel.tsx`

```tsx
// Estado para precache
const [isPrecaching, setIsPrecaching] = useState(false);
const [precacheMessage, setPrecacheMessage] = useState<string | null>(null);

// Handler
const handlePrecache = async () => {
  setIsPrecaching(true);
  const result = await precacheDriveFilesMX();
  if (result.success) {
    setPrecacheMessage(
      `Cache optimizado: ${result.stats.cached} archivos nuevos,
       ${result.stats.already_cached} ya en cache`
    );
  }
  setIsPrecaching(false);
};

// UI - Botón con tooltip explicativo
<Tooltip title="⚡ Optimizar cache: Ejecutar 1 vez antes de descargar ZIPs.
                 Tarda ~5 min pero acelera todas las descargas futuras.">
  <IconButton onClick={handlePrecache} disabled={isPrecaching}>
    {isPrecaching ? <CircularProgress size={20} /> : <SpeedIcon />}
  </IconButton>
</Tooltip>

// Tip contextual visible
<Typography variant="caption" color="text.secondary">
  💡 <strong>Tip:</strong> Usa el ícono de velocidad (⚡) una vez antes de
  descargar ZIPs grandes para acelerar la descarga.
</Typography>
```

---

## Problema 3: Error `AttributeError: 'MXFilterService' object has no attribute 'get_all_records'`

### Síntoma
Al hacer clic en el botón de optimizar cache, el backend retornaba error 500.

### Causa
El método `get_all_records()` no existía en `MXFilterService`. El endpoint lo llamaba pero nunca se implementó.

### Solución
Se agregó el método al servicio (ver sección anterior).

---

## Problema 4: Limpieza de UI - Tab "Cargar Archivos" Redundante

### Contexto
La página tenía 4 tabs:
1. **Consultar** - Filtrar desde archivo maestro en Drive
2. **Cargar Archivos** - Upload de Excel individual (REDUNDANTE)
3. **Facturas + Complementos** - Upload combinado de facturas y complementos
4. **Historial** - Ver reportes generados

El Tab 2 (Cargar Archivos) era redundante porque el Tab 3 (Facturas + Complementos) lo reemplazaba con mejor funcionalidad.

### Cambios Realizados
**Archivo:** `frontend/src/pages/finance/ReporteriaAutomaticaMX.tsx`

1. **Eliminación de imports no usados:**
```typescript
// Eliminado:
import FKExcelUploader from '../../components/forms/FKExcelUploader';
import type { ExcelValidationResponse, InvoiceRecord, ... } from '../../types/finance';

// Se mantiene:
import FKCombinedExcelUploader from '../../components/forms/FKCombinedExcelUploader';
```

2. **Eliminación de estado del Upload tab:**
```typescript
// Eliminado (~25 líneas de estado):
const [sessionId, setSessionId] = useState<string | null>(null);
const [uploadedData, setUploadedData] = useState<InvoiceRecord[]>([]);
const [sessionStats, setSessionStats] = useState<SessionStats | null>(null);
const [searchType, setSearchType] = useState<SearchType>('codigo_operacion');
// ... etc
```

3. **Eliminación de handlers (~165 líneas):**
- `handleUploadSuccess`
- `handleUploadError`
- `handleSearch`
- `handleReset`
- `handleGenerateZip`
- `formatCurrency`, `formatDate`, `tableData`, `displayData`

4. **Eliminación del TabPanel completo (~320 líneas de JSX)**

5. **Actualización de índices de tabs:**
```typescript
// Antes: 4 tabs (0, 1, 2, 3)
// Después: 3 tabs (0, 1, 2)

<Tab label="Consultar" id="mx-tab-0" />           // Sin cambios
<Tab label="Facturas + Complementos" id="mx-tab-1" />  // Era index=2
<Tab label="Historial" id="mx-tab-2" />           // Era index=3
```

### Resultado
- **Reducción de ~550 líneas de código**
- **UI más simple y clara** con solo 3 tabs
- **Sin funcionalidad duplicada**

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `frontend/src/services/financeServiceMX.ts` | Timeout 30min, función `precacheDriveFilesMX()` |
| `frontend/src/components/forms/FKMXFilterPanel.tsx` | Botón SpeedIcon, estado precache, tooltips |
| `backend/src/adapter/rest/finance_routes.py` | Endpoint `/mx/precache-drive-files` |
| `backend/src/core/servicios/filter_service_mx.py` | Método `get_all_records()` |
| `backend/src/core/servicios/google_drive_service.py` | Método `precache_drive_file_ids()`, `_list_all_drive_files()` |
| `frontend/src/pages/finance/ReporteriaAutomaticaMX.tsx` | Eliminación tab "Cargar Archivos", limpieza código |

---

## Base de Datos

### Tabla `drive_file_cache` (Supabase)
**Archivo de migración:** `backend/database/migration_add_drive_file_cache.sql`

```sql
CREATE TABLE drive_file_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    uuid VARCHAR(100) NOT NULL,           -- UUID del documento
    file_type VARCHAR(10) NOT NULL,       -- 'pdf' o 'xml'
    drive_file_id VARCHAR(100) NOT NULL,  -- ID en Google Drive
    drive_file_name VARCHAR(255),
    country VARCHAR(10) DEFAULT 'MX',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_uuid_file_type UNIQUE (uuid, file_type, country)
);
```

---

## Métricas de Rendimiento (Estimadas)

| Escenario | Antes | Después |
|-----------|-------|---------|
| Primera descarga ZIP 338 records | ~25 min | ~25 min (sin cache) |
| Descarga ZIP después de precache | ~25 min | ~5-8 min |
| Precache inicial | N/A | ~5 min (una vez) |
| Cache hit rate después de precache | 0% | ~95%+ |

---

## Próximos Pasos Recomendados

1. **Ejecutar precache automáticamente** después de subir nuevos archivos en "Facturas + Complementos"
2. **Agregar indicador de progreso** durante la descarga ZIP
3. **Considerar descarga en background** con notificación cuando termine
4. **Programar precache nocturno** vía cron job para mantener cache actualizado

---

## Comandos Útiles

```bash
# Compilar frontend
cd frontend && npm run build

# Ejecutar backend local
cd backend && python -m uvicorn main:app --reload --port 8000

# Ejecutar precache manualmente (browser console)
await fetch('/api/finance/mx/precache-drive-files', {
  method: 'POST',
  headers: {'Authorization': 'Bearer <token>'}
}).then(r => r.json())
```
