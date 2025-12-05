# Sesión 2025-11-24: Implementación Reportería Automática Colombia

## Contexto de la Sesión

Esta sesión fue una continuación del trabajo en Facturación MX (México) para implementar la funcionalidad completa de **Reportería Automática Colombia (CO)**. La funcionalidad permite procesar 4 archivos Excel (2 de Netsuite y 2 de Noova) para generar un reporte consolidado con 2 hojas.

## Stack Tecnológico

- **Frontend**: React 18 + TypeScript + Material-UI
- **Backend**: FastAPI + Python 3.11
- **Procesamiento**: Pandas + Openpyxl
- **Arquitectura**: Clean Architecture con separación adapter/core/interface

## Objetivos Cumplidos

### 1. Implementación Base CO
✅ Migración de lógica desde proyecto Streamlit a React + FastAPI
✅ Creación de DTOs completos para operaciones CO
✅ Servicio de procesamiento con LEFT JOIN y clasificación
✅ 3 endpoints API (upload, download, delete session)
✅ Componente uploader de 4 archivos
✅ Página principal de Reportería CO
✅ Servicio frontend para llamadas API

### 2. Archivos por Parejas
✅ Lógica flexible: se pueden subir 4 archivos o solo parejas
✅ Validación: al menos una pareja completa requerida
✅ Parejas:
  - **Pareja 1**: Netsuite Facturas + Noova Facturas
  - **Pareja 2**: Netsuite NC + Noova NC

### 3. UI en 2 Columnas
✅ Diseño visual separado por categoría:
  - **Columna Izquierda**: Facturas (azul primary)
  - **Columna Derecha**: Notas de Crédito (coral secondary)
✅ Indicadores visuales de archivos cargados
✅ Validación en tiempo real de parejas completas

### 4. Estructura de Columnas Simplificada
✅ **Hoja Costos Fijos** (12 columnas):
  1. Codigo del desembolso
  2. Valor Costos Fijos
  3. Seguro + Iva
  4. Int. Corriente Facturado FK
  5. Int. Mora Facturado FK
  6. (-) Retencion en la Fuente
  7. Valor Neto Facturado
  8. Fecha Facturacion
  9. # Factura
  10. Moneda
  11. Nit
  12. **Otros Valor** (última columna)

✅ **Hoja Mandato** (10 columnas):
  1. Codigo del desembolso
  2. Mes facturacion
  3. Interes Corriente Facturado
  4. Interes Mora Facturado Mandato
  5. Valor Neto Facturado
  6. Fecha Factura
  7. # Factura
  8. Moneda
  9. Nit
  10. **Otros Valor** (última columna)

### 5. Columna "Otros Valor"
✅ Agregada como última columna en ambas hojas
✅ Captura valores de productos con categoría "otros"
✅ Incluida en cálculo de Valor Neto Facturado

## Problemas Resueltos

### Problema 1: Error 422 - Unprocessable Content
**Causa**: El servicio frontend enviaba archivos `undefined` al FormData
**Solución**:
- Actualizado `COFileSet` interface con archivos opcionales
- Modificado `processCOFiles()` para solo agregar archivos que existan
```typescript
if (files.netsuite) {
  formData.append('netsuite', files.netsuite);
}
```

### Problema 2: Registros ITPA no se guardaban en hoja Mandato
**Causa**: El método `_extract_prefix()` solo funcionaba con formato `ITPA-12345` (con guión)
**Realidad**: Los archivos reales usan formato `ITPA27212` (sin guión)
**Solución**:
- Actualizado método para extraer letras antes del primer dígito
- Ahora soporta ambos formatos:
  - Con guión: `ITPA-12345` → `ITPA`
  - Sin guión: `ITPA27212` → `ITPA`

```python
def _extract_prefix(self, numero_factura: str) -> Optional[str]:
    if not numero_factura:
        return None

    # First try splitting by dash (if present)
    if "-" in numero_factura:
        parts = numero_factura.split("-")
        return parts[0].upper() if parts else None

    # If no dash, extract letters before first digit
    prefix = ""
    for char in numero_factura:
        if char.isalpha():
            prefix += char
        elif char.isdigit():
            break

    return prefix.upper() if prefix else None
```

## Lógica de Procesamiento

### 1. Lectura de Archivos
- **Netsuite**: Extrae `numero_factura`, `moneda`, `valor`
- **Noova**: Extrae `fecha`, `numero_factura`, `nit`, `nombre_cliente`, `email`, `estado`, `envio`, `codigo_operacion`, `codigo_producto`, `concepto`

### 2. Consolidación (LEFT JOIN)
- **Base**: Noova (todos los registros preservados)
- **Join Key**: `numero_factura` (ej: `ITPA27212`, `FE11199`)
- **Enriquecimiento**: Agrega `moneda` y `valor` de Netsuite cuando hay match

### 3. Clasificación
**Método Primario**: Código de producto (146 códigos en `product_classification.json`)
- Mapea código → categoría (costos_fijos, seguro_iva, intereses_corriente, intereses_mora, otros)

**Método Secundario**: Keywords en concepto (fallback)

**Destino de Hoja**: Según prefijo de factura
- `ITPA` → Mandato
- `FE`, `NCFE`, `ITGC`, `GL` → Costos Fijos

### 4. Distribución de Valores
- Cada `valor_netsuite` va a UNA columna específica según categoría
- `Valor Neto Facturado` = suma de todas las columnas de valor

### 5. Generación Excel
- 2 hojas con formato y styling
- Headers con fondo azul y texto blanco
- Auto-ajuste de anchos de columna

## Archivos Creados/Modificados

### Backend
```
backend/
├── config/colombia/
│   ├── classification_rules.json (copiado)
│   ├── column_mapping.json (copiado)
│   └── product_classification.json (copiado)
├── src/
│   ├── interface/
│   │   └── finance_dtos_co.py (NUEVO - 287 líneas)
│   ├── core/servicios/
│   │   └── file_processor_co.py (NUEVO - 575 líneas)
│   └── adapter/rest/
│       └── finance_routes.py (MODIFICADO - agregados 3 endpoints CO)
└── main.py (MODIFICADO - logging nivel DEBUG)
```

### Frontend
```
frontend/src/
├── services/
│   └── financeServiceCO.ts (NUEVO - 113 líneas)
├── components/forms/
│   └── FKExcelUploaderCO.tsx (NUEVO - 463 líneas)
└── pages/finance/
    └── ReporteriaAutomaticaCO.tsx (MODIFICADO - 400 líneas)
```

## Endpoints API

### POST `/api/finance/co/process-files`
- **Descripción**: Procesa archivos CO y genera reporte
- **Parámetros**: 4 archivos Excel (opcionales, al menos 1 pareja requerida)
- **Response**: `COProcessingResponse` con estadísticas y session_id
- **Timeout**: 5 minutos

### GET `/api/finance/co/download/{session_id}`
- **Descripción**: Descarga reporte Excel generado
- **Response**: Blob de Excel
- **Headers**: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### DELETE `/api/finance/co/session/{session_id}`
- **Descripción**: Limpia datos de sesión del servidor
- **Response**: Mensaje de confirmación

## Configuración JSON

### classification_rules.json
Define reglas de clasificación:
- **Keywords**: Para clasificación por concepto (fallback)
- **Prefijos**: Mapeo de prefijo de factura → hoja destino
  - `ITPA` → "Relación facturas mandato"
  - `FE`, `NCFE`, `ITGC`, `GL` → "Relacion facturas Costos Fijos"

### product_classification.json
- **146 códigos de producto** mapeados a 5 categorías
- **Mapeo categoría → columna** para distribución de valores

### column_mapping.json
Mapeo de columnas Excel fuente → campos estandarizados

## Testing y Debugging

### Logging Agregado
- Nivel DEBUG habilitado en main.py
- Logs detallados en clasificación:
  - Prefix extraído por cada factura
  - Hoja destino asignada
  - Errores de mapeo
- Logs de separación por hoja:
  - Cantidad de registros por hoja
  - Muestras de facturas en Mandato
  - Advertencia si Mandato está vacío con lista de prefixes encontrados

### Formato de Logs
```
2025-11-24 22:25:28 - src.core.servicios.file_processor_co - DEBUG - Factura ITPA27212: prefix=ITPA, hoja_destino='Relación facturas mandato'
2025-11-24 22:25:28 - src.core.servicios.file_processor_co - INFO - Separación por hoja: 150 Costos Fijos, 89 Mandato
```

## Próximos Pasos (Fase 2)

### Pendientes para Futura Implementación
- [ ] Integración con Google Drive (similar a MX)
- [ ] Upload automático de reportes generados
- [ ] Sincronización con archivo Master
- [ ] Historial de procesamiento
- [ ] Validación avanzada de archivos
- [ ] Manejo de errores más robusto

## Comandos de Desarrollo

### Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### Acceso
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health

## Lecciones Aprendidas

### 1. Formatos de Datos Reales vs Documentación
**Aprendizaje**: Siempre verificar formato real de datos en producción
- Documentación asumía formato `ITPA-12345` (con guión)
- Datos reales usan formato `ITPA27212` (sin guión)
- **Solución**: Implementar parseo flexible que soporte ambos formatos

### 2. Validación de Archivos Opcionales
**Aprendizaje**: FormData no debe contener valores `undefined`
- FastAPI rechaza con 422 si se envían archivos undefined
- **Solución**: Validar archivos antes de agregarlos al FormData

### 3. Logging es Crítico
**Aprendizaje**: Logs detallados facilitan debugging de lógica de negocio
- Sin logs era imposible ver por qué ITPA iba a Costos Fijos
- Con DEBUG logs se identificó inmediatamente el problema del prefix

### 4. Clean Architecture Facilita Testing
**Aprendizaje**: Separación clara de capas permite debugging eficiente
- DTOs bien definidos facilitan validación
- Servicios independientes permiten testing aislado
- Configuración en JSON permite ajustes sin cambiar código

## Notas de Configuración

### Archivos de Configuración Críticos
1. **classification_rules.json**: Determina routing de facturas a hojas
2. **product_classification.json**: Clasificación de 146 códigos
3. **column_mapping.json**: Mapeo de columnas Excel

### Cambios de Configuración Requieren
- ✅ NO requieren cambio de código
- ✅ NO requieren redeploy
- ⚠️ Requieren reinicio de servidor (para recargar JSON)

## Métricas de Implementación

- **Líneas de Código Backend**: ~1,437 líneas
- **Líneas de Código Frontend**: ~976 líneas
- **Archivos Nuevos**: 5
- **Archivos Modificados**: 3
- **Tiempo de Desarrollo**: ~3 horas
- **Iteraciones de Ajuste**: 6
- **Problemas Críticos Resueltos**: 2

## Estado Final

✅ **Funcionalidad Completa** - Fase 1 (Upload → Process → Generate) implementada y funcionando
✅ **Testing Exitoso** - Probado con archivos reales de producción
✅ **Bugs Críticos Resueltos** - Prefix extraction y archivos opcionales
✅ **Documentación Completa** - DTOs, servicios y endpoints documentados
✅ **Logging Implementado** - Debug logs para troubleshooting

## Referencias

### Documentación Externa
- Streamlit Original: `C:\Users\maria.gaitan\mvp_worspace\projects\Facturacion\facturacion-finkargo`
- Sesión Streamlit: `docs/sesion_2025-10-22.md`

### Archivos de Sesión Relacionados
- `20251119_SESSION_NOTES_FACTURACION_MX_UI_LAYOUT.md` (Facturación MX)
- `20251120_SESSION_NOTES_FACTURACION_MX_ZIP_GENERATION.md` (ZIP MX)

---

**Fecha**: 2025-11-24
**Duración**: ~3 horas
**Status**: ✅ Completado - Fase 1 funcional y probada
