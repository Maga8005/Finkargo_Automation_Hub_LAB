# Implementación: Historial de Reportes y Exportación CSV

**Fecha:** 2025-11-28
**Módulo:** Finance - Reportería Automática CO/MX
**Estado:** En progreso (bug pendiente en exportación CSV)

---

## Resumen

Esta sesión se enfocó en mejorar el sistema de historial de reportes financieros, incluyendo:
1. Corrección del registro de historial para descargas desde filtros
2. Corrección del resumen de estadísticas en la tabla de historial
3. Implementación de exportación a CSV del historial
4. Mejoras en el manejo de errores y logging

---

## Cambios Realizados

### 1. Registro de Historial para Descargas de Filtros

**Problema:** Cuando un usuario hacía una consulta con filtros y descargaba el reporte (Excel o ZIP), no se registraba en el historial de reportes.

**Solución:** Se agregaron llamadas a `record_finance_report()` en los 4 endpoints de descarga filtrada:

#### Backend - `finance_routes.py`

**Endpoints modificados:**
- `POST /api/finance/co/filter/download` - Descarga Excel filtrado CO
- `POST /api/finance/co/filter/download-zip` - Descarga ZIP filtrado CO
- `POST /api/finance/mx/filter/download` - Descarga Excel filtrado MX
- `POST /api/finance/mx/filter/download-zip` - Descarga ZIP filtrado MX

**Código agregado en cada endpoint:**
```python
# Record in history
await record_finance_report(
    country="CO",  # o "MX"
    report_type="consulta",  # o "zip_download"
    stats={
        "total_records": response.total_records,
        "sheets_searched": response.sheets_searched,  # Solo CO
        # MX incluye: total_amount, total_subtotal, total_iva
    },
    user_id=user_id,
    user_email=user_email,
    filters_applied={
        "nit": request.nit,  # CO
        "rfc": request.rfc,  # MX
        "operaciones": request.operaciones,
        "fecha_inicio": request.fecha_inicio,
        "fecha_fin": request.fecha_fin,
        "hoja": request.hoja,  # Solo CO
    },
    file_name=filename,
    status="completed"
)
```

---

### 2. Corrección de SupabaseClient

**Problema:** Error `'SupabaseClient' object has no attribute 'table'` al intentar registrar reportes.

**Causa:** La función `get_report_repository()` pasaba el objeto wrapper `SupabaseClient` en lugar del cliente real de Supabase.

**Solución:**
```python
# Antes (incorrecto)
def get_report_repository() -> FinanceReportRepository:
    supabase = get_supabase_client()
    return get_finance_report_repository(supabase)  # Pasaba el wrapper

# Después (correcto)
def get_report_repository() -> FinanceReportRepository:
    supabase = get_supabase_client()
    # Use admin_client to access the actual Supabase Client with .table() and .rpc() methods
    return get_finance_report_repository(supabase.admin_client)
```

---

### 3. Corrección del Resumen de Estadísticas

**Problema:** La columna "Resumen" en la tabla de historial mostraba "0 registros" para reportes de tipo `consulta` y `zip_download`.

**Causa:** El código buscaba campos incorrectos (`total_consolidated`, `total_invoices`) cuando los reportes de filtro usan `total_records`.

**Solución:**
```python
# En el endpoint GET /history
if report_type in ('consulta', 'zip_download'):
    # Filter/query reports use total_records
    total = stats.get('total_records', 0)
    stats_summary = f"{total} registros"
elif report.get('country') == 'CO':
    # CO facturacion reports
    total = stats.get('total_consolidated', stats.get('total_records', 0))
    stats_summary = f"{total} registros"
else:
    # MX facturacion reports
    total = stats.get('total_invoices', stats.get('total_records', 0))
    stats_summary = f"{total} facturas"
```

---

### 4. Implementación de Exportación CSV

#### Backend - Nuevo endpoint

**Archivo:** `backend/src/adapter/rest/finance_routes.py`

```python
@router.get(
    "/history/export/csv",
    summary="Export finance history to CSV",
    description="Download finance report history as CSV file with optional filters"
)
async def export_finance_history_csv(
    country: Optional[str] = None,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user)
):
```

**Características:**
- Filtros opcionales por país, tipo, estado y rango de fechas
- Límite de 10,000 registros
- Codificación UTF-8-sig para compatibilidad con Excel
- Columnas: ID Reporte, País, Tipo, Estado, Registros, Usuario, Archivo, Drive, Filtros Aplicados, Fecha Generación, Fecha Creación

#### Frontend - Servicio

**Archivo:** `frontend/src/services/financeHistoryService.ts`

```typescript
export const exportFinanceHistoryCSV = async (
  filters?: FinanceHistoryFilter
): Promise<Blob> => {
  const params = new URLSearchParams();
  if (filters?.country) params.append('country', filters.country);
  if (filters?.report_type) params.append('report_type', filters.report_type);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);

  const queryString = params.toString();
  const url = `/finance/history/export/csv${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get(url, {
    responseType: 'blob',
    timeout: 60000,
  });

  return response.data;
};

export const triggerCSVDownload = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
  window.URL.revokeObjectURL(url);
};
```

#### Frontend - Componente

**Archivo:** `frontend/src/components/forms/FKFinanceHistory.tsx`

```typescript
// Estado
const [exporting, setExporting] = useState(false);

// Handler
const handleExportCSV = async () => {
  setExporting(true);
  setError(null);

  try {
    const filters: FinanceHistoryFilter = {};
    if (filterCountry) filters.country = filterCountry;
    if (filterType) filters.report_type = filterType;
    if (filterStatus) filters.status = filterStatus;
    if (dateFrom) filters.date_from = dateFrom;
    if (dateTo) filters.date_to = dateTo;

    const blob = await exportFinanceHistoryCSV(filters);

    const timestamp = new Date().toISOString().slice(0, 10);
    const countrySuffix = filterCountry ? `_${filterCountry}` : '';
    const filename = `Historial_Reportes${countrySuffix}_${timestamp}.csv`;

    triggerCSVDownload(blob, filename);
  } catch (err) {
    // Error handling...
  } finally {
    setExporting(false);
  }
};

// Botón en UI
<Button
  variant="outlined"
  size="small"
  startIcon={exporting ? <CircularProgress size={16} /> : <DownloadIcon />}
  onClick={handleExportCSV}
  disabled={loading || exporting || total === 0}
>
  {exporting ? 'Exportando...' : 'Exportar CSV'}
</Button>
```

---

### 5. Migración de Base de Datos

**Archivo:** `backend/database/migration_add_email_to_finance_reports.sql`

```sql
-- Migration: Add generated_by_email column to finance_reports table
-- Date: 2024-11-28
-- Description: Adds email column for tracking who generated the report

ALTER TABLE finance_reports
ADD COLUMN IF NOT EXISTS generated_by_email VARCHAR(255);

COMMENT ON COLUMN finance_reports.generated_by_email IS 'Email of the user who generated the report';
```

---

## Bug Pendiente

### Error 400 al Exportar CSV

**Síntoma:** Al hacer clic en "Exportar CSV" con filtro de país (ej: `country=CO`), retorna HTTP 400.

**Log del servidor:**
```
INFO: 127.0.0.1:50968 - "GET /api/finance/history/export/csv?country=CO HTTP/1.1" 400 Bad Request
```

**Diagnóstico en progreso:**
- Se agregó logging mejorado para identificar el problema exacto
- Se mejoró el manejo de conversión de strings a enums
- Se normalizan strings vacíos a `None`

**Código actualizado para debugging:**
```python
logger.info(f"CSV export raw params - country: '{country}', report_type: '{report_type}', status: '{status}'")

# Normalize empty strings to None
country_val = country.strip() if country else None

# Convert to enums with explicit error handling
if country_val:
    try:
        country_enum = ReportCountry(country_val)
    except ValueError as e:
        logger.error(f"Invalid country value '{country_val}': {e}")
        raise ValueError(f"País inválido: '{country_val}'. Use 'CO' o 'MX'")
```

**Próximos pasos:**
1. Revisar logs del servidor para ver el error exacto
2. Verificar que los valores de enum coincidan exactamente
3. Posible problema con la validación de Pydantic o el orden de rutas en FastAPI

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `backend/src/adapter/rest/finance_routes.py` | Registro de historial en descargas, fix SupabaseClient, endpoint CSV |
| `backend/src/interface/finance_history_dtos.py` | Ya existía, sin cambios |
| `backend/src/repositorio/finance_report_repository.py` | Ya existía, sin cambios |
| `backend/database/migration_add_email_to_finance_reports.sql` | Nueva migración |
| `frontend/src/services/financeHistoryService.ts` | Funciones de exportación CSV |
| `frontend/src/components/forms/FKFinanceHistory.tsx` | Botón y lógica de exportación |
| `frontend/src/pages/finance/ReporteriaAutomaticaCO.tsx` | Layout simplificado (sin card placeholder) |

---

## Pruebas Realizadas

- [x] Historial muestra reportes de consulta/filtro después de descargar
- [x] Columna "Resumen" muestra conteo correcto de registros
- [x] Botón "Exportar CSV" aparece en la interfaz
- [ ] Exportación CSV funciona correctamente (bug 400 pendiente)

---

## Notas Técnicas

### Tipos de Reporte
- `facturacion`: Upload y procesamiento de archivos Excel
- `consulta`: Consulta/filtro de datos existentes (descarga Excel)
- `zip_download`: Descarga con PDFs incluidos

### Estructura de Stats por Tipo
```json
// consulta / zip_download
{
  "total_records": 150,
  "sheets_searched": ["COSTOS FIJOS", "MANDATO"]  // Solo CO
}

// facturacion CO
{
  "total_consolidated": 200,
  "total_records_noova": 100,
  "total_records_netsuite": 100
}

// facturacion MX
{
  "total_invoices": 50,
  "matched_pdfs": 45
}
```
