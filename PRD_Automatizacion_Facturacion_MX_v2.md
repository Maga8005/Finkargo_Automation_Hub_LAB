# PRD - Automatización de Descarga de Documentos de Facturación México

**Proyecto:** Hub de Automatización - Facturación MX  
**Tipo:** MVP de Automatización de Proceso  
**Owner:** Maria Alejandra Gaitán  
**Stakeholders:** Jonathan Medina, Johan Acevedo (Facturación MX)  
**Fecha Creación:** Noviembre 13, 2025  
**Última Actualización:** Noviembre 18, 2025 (Post Go/No-Go)  
**Status:** ✅ GO - En Desarrollo  
**Versión:** 2.0

---

## 📋 EXECUTIVE SUMMARY

**En una línea:** Automatizar la búsqueda y descarga de documentos fiscales (PDF/XML) por código de operación para reducir de 10 minutos a <1 minuto el tiempo de respuesta a clientes.

**Problema actual:** El equipo de facturación MX recibe solicitudes diarias de clientes pidiendo documentos de facturación por operación. Actualmente deben buscar manualmente cada UUID en MySuite, descargar archivos uno por uno, y armar un paquete para el cliente. Esto toma ~10 minutos por operación.

**Solución aprobada:** Una herramienta en el Hub de Servicios que permita buscar por código de operación o RFC y generar automáticamente un ZIP con todos los PDFs, XMLs y un Excel detallado de gastos.

**Decisión Go/No-Go:** ✅ **GO** - Reunión realizada el 18 de noviembre de 2025

---

## 🎯 CAMBIOS POST GO/NO-GO (v2.0)

### **Ajustes vs Propuesta Original:**

1. **Excel Detallado - 8 columnas (no 7):**
   - ✅ Agregado: Código de Operación (para cuando cliente solicita múltiples operaciones)
   - ❌ Removidos: Moneda, Tipo de Gasto clasificado, RFC, Razón Social
   - **Rationale:** Estos reportes son para el cliente solicitante (ya conoce su RFC)

2. **Estructura de Drive - Confirmada:**
   - Carpeta: "BASE DE DATOS FACTURAS CLIENTES"
   - Formato de mes: `01 ENERO`, `02 FEBRERO` (no `01_Enero`)
   - Cada mes contiene su propio Excel maestro
   - Archivos: `{uuid}.pdf` y `{uuid}.xml`

3. **Código de Operación:**
   - Se mantiene **manual** en Excel maestro (no extracción automática)
   - Rationale: Cambios históricos en facturación hacen difícil automatización

4. **Histórico Acumulativo:**
   - **Ideal:** Consultar Y reescribir archivo maestro en Drive (automático)
   - **Pendiente validar:** Permisos de Drive (lectura vs lectura+escritura)
   - **Plan B:** Carga manual mensual acumulativa si solo hay lectura

5. **Inicio de Desarrollo:**
   - ✅ Se puede arrancar SIN acceso a Drive (60% del MVP)
   - ⏳ Requiere Drive para: Conexión API, generación ZIP, testing

---

## 📊 ESTRUCTURA REAL DE GOOGLE DRIVE

### **Ubicación del Repositorio:**
```
Google Drive > Compartidos conmigo > BASE DE DATOS FACTURAS CLIENTES
```

### **Organización Confirmada:**

```
/BASE DE DATOS FACTURAS CLIENTES/
  /2025/
    /01 ENERO/
      - _DIN210108I3A-2025-01-EMITIDOS_EXCEPTO_NOMINA-1.xlsx
      - bad26a1c-0c72-4a07-a1af-b18b0f245853.pdf
      - bad26a1c-0c72-4a07-a1af-b18b0f245853.xml
      - 61848faa-86bf-4a1d-a8f8-2e32f7dc2733.pdf
      - 61848faa-86bf-4a1d-a8f8-2e32f7dc2733.xml
      ... (~500-1000 archivos por mes)
      
    /02 FEBRERO/
      - _DIN210108I3A-2025-02-EMITIDOS_EXCEPTO_NOMINA-1.xlsx
      - [PDFs y XMLs del mes]
      
    /03 MARZO/
      - _DIN210108I3A-2025-03-EMITIDOS_EXCEPTO_NOMINA-1.xlsx
      - [PDFs y XMLs del mes]
      
    /04 ABRIL/
    /05 MAYO/
    /06 JUNIO/
    ... (hasta /12 DICIEMBRE/)
    
  /2026/ (en el futuro)
    /01 ENERO/
    ...
```

### **Características Clave:**

**Naming Conventions:**
- **Carpetas de mes:** `01 ENERO`, `02 FEBRERO`, `03 MARZO`, etc.
  - Formato: `{número_mes} {MES_MAYÚSCULAS}`
  - El número ayuda al ordenamiento automático
  
- **Excel maestro:** `_DIN210108I3A-{año}-{mes}-EMITIDOS_EXCEPTO_NOMINA-1.xlsx`
  - Ejemplo: `_DIN210108I3A-2025-01-EMITIDOS_EXCEPTO_NOMINA-1.xlsx`
  - Uno por mes, dentro de su carpeta correspondiente
  
- **Archivos PDF/XML:** `{uuid}.pdf` y `{uuid}.xml`
  - Ejemplo: `bad26a1c-0c72-4a07-a1af-b18b0f245853.pdf`
  - UUID sin guiones adicionales ni sufijos

**Ventajas de esta estructura:**
- ✅ Performance óptimo (carpetas de ~500-1000 archivos)
- ✅ Fácil navegación manual para el equipo
- ✅ Escalable a 5-10 años
- ✅ Cada mes autocontenido (Excel + archivos)
- ✅ Búsqueda dirigida por mes (más rápida)

---

## 🎨 USER STORIES - ACTUALIZADAS

### **US-1: Carga de Excel Maestro** (Must-Have)
**Como** usuario de facturación MX  
**Quiero** cargar el Excel maestro mensual  
**Para** que la herramienta tenga la base de datos de facturas actualizada

**Criterios de aceptación:**
- [ ] Puedo arrastrar y soltar un archivo .xlsx
- [ ] El sistema valida columnas requeridas: UUID, CODIGO DE OPERACIÓN, Fecha emision, Conceptos, RFC receptor, Razon receptor, Tipo, SubTotal, IVA Trasladado, Total, Moneda
- [ ] Muestra mensaje de éxito con # de facturas cargadas
- [ ] Si el archivo es inválido, muestra error específico
- [ ] El Excel cargado reemplaza el anterior (no se acumulan)

**Cambio vs v1.0:** Ahora el usuario sube el Excel a la aplicación (no se lee automáticamente de Drive)

---

### **US-2: Búsqueda por Código de Operación** (Must-Have)
**Como** usuario de facturación MX  
**Quiero** buscar documentos por código de operación (ej: `MX:BSM210224366:1:6:PAG`)  
**Para** obtener todas las facturas relacionadas a esa operación en segundos

**Criterios de aceptación:**
- [ ] Puedo ingresar un código de operación completo
- [ ] El sistema busca en el Excel maestro cargado
- [ ] Muestra lista de facturas encontradas con: UUID, Código Operación, Tipo, Fecha, Concepto, Subtotal, IVA, Total
- [ ] Si no encuentra resultados, muestra mensaje claro

---

### **US-3: Búsqueda por RFC** (Must-Have)
**Como** usuario de facturación MX  
**Quiero** buscar documentos por RFC del cliente (ej: `BSM210224366`)  
**Para** obtener todas las operaciones de ese cliente cuando no tengo el código exacto

**Criterios de aceptación:**
- [ ] Puedo ingresar un RFC
- [ ] El sistema busca todas las facturas de ese RFC
- [ ] Muestra lista agrupada por código de operación
- [ ] Puedo seleccionar una o varias facturas para descargar

---

### **US-4: Filtro por Rango de Fechas** (Must-Have)
**Como** usuario de facturación MX  
**Quiero** filtrar resultados por rango de fechas  
**Para** limitar la búsqueda a un periodo específico (ej: Q3 2025)

**Criterios de aceptación:**
- [ ] Puedo ingresar fecha inicial y fecha final (opcional)
- [ ] Si no ingreso fechas, busca en todo el Excel cargado
- [ ] El filtro se aplica sobre los resultados de código de operación o RFC

---

### **US-5: Generación de ZIP con Documentos** (Must-Have)
**Como** usuario de facturación MX  
**Quiero** que el sistema genere automáticamente un ZIP con todos los documentos  
**Para** enviarlo directamente al cliente sin procesamiento manual

**Criterios de aceptación:**
- [ ] El ZIP contiene todos los PDFs encontrados
- [ ] El ZIP contiene todos los XMLs encontrados
- [ ] El ZIP contiene un Excel detallado de gastos
- [ ] Los archivos mantienen su nombre original (UUID)
- [ ] El ZIP se llama: `Facturacion_{RFC}_{YYYYMMDD}.zip`
- [ ] La descarga inicia automáticamente al hacer clic en botón

---

### **US-6: Excel Detallado de Gastos** (Must-Have) - **ACTUALIZADO**
**Como** usuario de facturación MX  
**Quiero** que el ZIP incluya un Excel con el detalle de gastos  
**Para** que el cliente tenga un resumen claro de sus facturas

**Criterios de aceptación:**
- [ ] Excel se llama `Detalle_Gastos_{RFC}_{YYYYMMDD}.xlsx`
- [ ] Contiene **8 columnas** (actualizado):
  1. UUID
  2. **Código de Operación** ← **NUEVO**
  3. Tipo (Ingreso/Egreso)
  4. Fecha Emisión
  5. Concepto
  6. Subtotal
  7. IVA
  8. Total
- [ ] Incluye fila de TOTAL al final
- [ ] Formato: Montos con 2 decimales, fechas en formato DD/MM/YYYY

**Cambio vs v1.0:**
- ✅ **Agregado:** Código de Operación (columna 2)
- ❌ **Removidos:** Moneda, RFC, Razón Social, Tipo de Gasto clasificado

**Rationale:** 
- Código de Operación permite al cliente identificar facturas cuando solicita múltiples operaciones
- RFC/Razón Social innecesarios porque el reporte es para el cliente solicitante
- Moneda innecesaria si todas las facturas están en la misma moneda (USD)

---

### **US-7: Conexión a Google Drive** (Must-Have)
**Como** sistema  
**Quiero** acceder a la carpeta de Google Drive donde están los archivos  
**Para** buscar y copiar los archivos XML/PDF por UUID

**Criterios de aceptación:**
- [ ] Conexión a carpeta "BASE DE DATOS FACTURAS CLIENTES" configurada
- [ ] El sistema puede leer la estructura: /2025/01 ENERO/, /2025/02 FEBRERO/, etc.
- [ ] Busca archivos por UUID en la carpeta del mes correspondiente
- [ ] Si UUID no existe, marca como "No disponible"

**Cambio vs v1.0:** Path real del Drive confirmado

---

### **US-8: Búsqueda Optimizada por Mes** (Must-Have) - **NUEVO**
**Como** sistema  
**Quiero** buscar archivos primero en la carpeta del mes correspondiente  
**Para** optimizar performance y reducir tiempo de búsqueda

**Criterios de aceptación:**
- [ ] Sistema extrae mes de la fecha de emisión de cada factura
- [ ] Busca archivos en carpeta `/2025/{mes_número} {MES}/`
- [ ] Si no encuentra, hace fallback a búsqueda en otros meses
- [ ] Logs indican en qué carpeta encontró (o no) cada archivo

**Ejemplo:**
- Factura con fecha `2025-03-15` → Busca en `/2025/03 MARZO/`
- Si no encuentra → Busca en `/2025/02 FEBRERO/` y `/2025/04 ABRIL/` (meses adyacentes)

---

## 🔧 TECHNICAL REQUIREMENTS - ACTUALIZADOS

### **Arquitectura de la Solución**

```
┌─────────────────┐
│  Hub Servicios  │
│  (React/Vue)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │
│  (FastAPI)      │
└────────┬────────┘
         │
         ├──────────► Google Drive API (carpeta compartida)
         │            Path: "BASE DE DATOS FACTURAS CLIENTES"
         │
         └──────────► Pandas (procesar Excel maestro)
```

### **Stack Tecnológico Confirmado**

**Frontend:**
- React (integrado en Hub de Servicios existente)
- Tailwind CSS (si es lo que usa el Hub)
- Axios para llamadas API
- React Dropzone (drag & drop de Excel)

**Backend:**
- Python 3.11+
- FastAPI (recomendado por facilidad con Excel y Drive API)
- Pandas para procesamiento de Excel
- Google Drive API v3
- python-docx / openpyxl para Excel detallado
- ZipFile library para generación de ZIPs

**Almacenamiento:**
- Google Drive (repositorio de archivos)
- En memoria: Excel maestro cargado (durante sesión)
- No hay base de datos persistente en MVP

---

### **APIs Requeridas**

#### **POST /api/upload-excel**
**Descripción:** Carga y valida Excel maestro

**Input:**
```json
{
  "file": "multipart/form-data"
}
```

**Output:**
```json
{
  "status": "success",
  "facturas_count": 891,
  "mensaje": "Excel cargado exitosamente con 891 facturas"
}
```

**Validaciones:**
- Formato: .xlsx o .xls
- Columnas requeridas: UUID, CODIGO DE OPERACIÓN, Fecha emision, Conceptos, RFC receptor, Razon receptor, Tipo, SubTotal, IVA Trasladado, Total, Moneda
- Al menos 1 fila de datos
- UUIDs válidos (formato UUID)

---

#### **POST /api/search**
**Descripción:** Busca facturas por filtros

**Input:**
```json
{
  "codigo_operacion": "MX:BSM210224366:1:6:PAG",  // opcional
  "rfc": "BSM210224366",                          // opcional
  "fecha_inicio": "2025-01-01",                   // opcional
  "fecha_fin": "2025-12-31"                       // opcional
}
```

**Output:**
```json
{
  "facturas": [
    {
      "uuid": "f6ba4a44-ea71-4263-86f2-2b1687eefe14",
      "codigo_operacion": "MX:BSM210224366:1:6:PAG",
      "tipo": "Ingreso",
      "fecha": "2025-10-01",
      "concepto": "INTERESES POR PRESTAMO OTORGADO...",
      "subtotal": 100.00,
      "iva": 16.00,
      "total": 116.00,
      "rfc": "BSM210224366",
      "razon_social": "BIKE SP MEXICO",
      "mes": "10",  // para búsqueda en Drive
      "año": "2025"
    }
  ],
  "total_encontradas": 5
}
```

**Validaciones:**
- Al menos un filtro presente (código_operacion O rfc)
- Si hay fechas: fecha_inicio <= fecha_fin
- Si no hay Excel cargado: Error 400

---

#### **POST /api/generate-zip**
**Descripción:** Genera ZIP con PDFs, XMLs y Excel detallado

**Input:**
```json
{
  "uuids": [
    {
      "uuid": "f6ba4a44-ea71-4263-86f2-2b1687eefe14",
      "fecha": "2025-10-01",
      "mes": "10",
      "año": "2025"
    }
  ],
  "rfc": "BSM210224366"
}
```

**Output:**
```json
{
  "download_url": "/api/download-zip/{zip_id}",
  "zip_filename": "Facturacion_BSM210224366_20251118.zip",
  "archivos_incluidos": {
    "pdfs": 5,
    "xmls": 5,
    "excel": 1
  },
  "archivos_faltantes": [
    "4e68fe3a-0b8a-4d26-b040-273604c28915.pdf"
  ]
}
```

**Lógica:**
1. Por cada UUID:
   - Extraer mes/año de la fecha
   - Buscar en `/2025/{mes} {MES_NOMBRE}/`
   - Buscar `{uuid}.pdf` y `{uuid}.xml`
   - Si no encuentra, marcar como "No disponible"
2. Generar Excel detallado con 8 columnas
3. Comprimir todo en ZIP
4. Guardar temporalmente y retornar URL de descarga

---

### **Google Drive API - Especificaciones**

**Autenticación:**
- Service Account con credenciales JSON
- Scope: `https://www.googleapis.com/auth/drive.readonly`

**Estructura de búsqueda:**
```python
def buscar_archivo_en_drive(uuid, fecha_emision):
    """
    Busca archivo por UUID en la carpeta del mes correspondiente
    """
    # Extraer mes y año de fecha_emision
    mes = fecha_emision.strftime('%m')  # "01", "02", etc.
    año = fecha_emision.strftime('%Y')  # "2025"
    mes_nombre = fecha_emision.strftime('%B').upper()  # "ENERO"
    
    # Path: /BASE DE DATOS FACTURAS CLIENTES/2025/01 ENERO/
    carpeta_mes = f"{año}/{mes} {mes_nombre}"
    
    # Buscar uuid.pdf y uuid.xml
    pdf = drive_service.buscar(carpeta_mes, f"{uuid}.pdf")
    xml = drive_service.buscar(carpeta_mes, f"{uuid}.xml")
    
    return {'pdf': pdf, 'xml': xml}
```

**Optimización - Smart Search:**
1. Buscar primero en carpeta del mes correspondiente
2. Si no encuentra, buscar en meses adyacentes (±1 mes)
3. Como último recurso, búsqueda recursiva en todo 2025

**Rate Limits:**
- Google Drive API: 1000 requests/100 seconds per user
- Estrategia: Batch requests cuando sea posible

---

## 📊 MVP SCOPE - MoSCoW (ACTUALIZADO)

### **MUST HAVE (MVP Core)** ✅

1. ✅ Carga de Excel maestro con validación
2. ✅ Búsqueda por código de operación
3. ✅ Búsqueda por RFC
4. ✅ Filtro por rango de fechas
5. ✅ Búsqueda optimizada por mes en Drive
6. ✅ Generación de ZIP con PDFs y XMLs
7. ✅ Generación de Excel detallado de gastos (**8 columnas**)
8. ✅ Conexión a Google Drive (carpeta "BASE DE DATOS FACTURAS CLIENTES")
9. ✅ Manejo de archivos faltantes (indicador de estado)
10. ✅ Descarga de ZIP generado

### **SHOULD HAVE (Post-MVP, Week 4-5)** 🟡

1. 🟡 Búsqueda por múltiples códigos de operación a la vez (batch)
2. 🟡 Historial de búsquedas recientes
3. 🟡 Preview de facturas antes de generar ZIP
4. 🟡 Reescritura automática de Excel maestro en Drive (si hay permisos)
5. 🟡 Notificaciones por email cuando ZIP está listo

### **COULD HAVE (Future/V2)** 🔵

1. 🔵 Acceso directo de clientes a la herramienta (Fase 2)
2. 🔵 Extracción automática de código de operación del concepto
3. 🔵 Caché de búsquedas frecuentes
4. 🔵 Dashboard de métricas de uso
5. 🔵 Exportar resultados a otros formatos

### **WON'T HAVE (Out of Scope)** ❌

1. ❌ Integración directa con MySuite/OneFactor API
2. ❌ Integración con Netsuite para extraer Excel automáticamente
3. ❌ Base de datos persistente (usar Excel como fuente)
4. ❌ Timbrado o emisión de facturas
5. ❌ Edición de datos fiscales
6. ❌ App móvil nativa

---

## 🎯 SUCCESS CRITERIA (ACTUALIZADOS)

### **Métricas Cuantitativas**

1. **Tiempo de Respuesta**
   - Actual: ~10 minutos por operación
   - Target: <1 minuto (90% reducción)
   - Medición: Tiempo desde búsqueda hasta descarga de ZIP

2. **Adopción**
   - Target: 100% del equipo MX usando la herramienta en Week 2
   - Medición: # de búsquedas por semana vs solicitudes de clientes

3. **Precisión**
   - Target: 0 errores de archivos faltantes/incorrectos en 2 semanas
   - Medición: # de quejas de clientes por documentos incorrectos

4. **Performance de Búsqueda**
   - Target: <5 segundos para búsqueda de 10 facturas
   - Medición: Logs de tiempo de respuesta del API

### **Métricas Cualitativas**

1. **Satisfacción del Usuario**
   - Survey post-uso (Week 3): "¿Qué tan satisfecho estás?" → Target: 4/5 estrellas
   - Feedback directo de Jonathan y Johan

2. **Calidad del Output**
   - Clientes confirman que documentos son correctos y completos
   - Excel detallado es claro y útil (8 columnas acordadas)

---

## 📅 TIMELINE ACTUALIZADO (3-4 Semanas)

### **Week 1: Setup + Build Core (Nov 18-24)**

**Lunes-Martes (Nov 18-19):**
- ✅ Reunión Go/No-Go completada
- ✅ PRD actualizado
- [ ] Setup proyecto y repositorio
- [ ] Backend: Carga y validación de Excel
- [ ] Frontend: Componente de upload

**Miércoles-Jueves (Nov 20-21):**
- [ ] Backend: Lógica de búsqueda completa
- [ ] Frontend: Formulario de búsqueda + tabla resultados
- [ ] Testing unitario de búsqueda

**Viernes (Nov 22):**
- [ ] Integración frontend-backend (sin Drive)
- [ ] Alpha testing interno (carga Excel, búsqueda funciona)
- [ ] **BLOCKER CHECK:** Acceso a Drive disponible?

---

### **Week 2: Conexión Drive + Generación ZIP (Nov 25-Dec 1)**

**Lunes (Nov 25):**
- [ ] Conectar Google Drive API
- [ ] Implementar búsqueda optimizada por mes
- [ ] Testing de lectura de archivos por UUID

**Martes-Miércoles (Nov 26-27):**
- [ ] Implementar generación de Excel detallado (8 columnas)
- [ ] Implementar generación de ZIP
- [ ] Testing end-to-end completo

**Jueves (Nov 28):**
- [ ] Bug fixes críticos
- [ ] Preparar demo
- [ ] Documentación básica de usuario

**Viernes (Nov 29):**
- [ ] Buffer / ajustes finales

---

### **Week 3: Demo + Beta Testing (Dec 2-8)**

**Lunes (Dec 2):**
- [ ] **DEMO con Johan y Jonathan** 🎉
- [ ] Recoger feedback
- [ ] Definir ajustes críticos

**Martes-Jueves (Dec 3-5):**
- [ ] Implementar ajustes del demo
- [ ] Beta testing con 5 solicitudes reales
- [ ] Documentación técnica para handoff

**Viernes (Dec 6):**
- [ ] Validación final con stakeholders
- [ ] Preparar handoff

---

### **Week 4: Handoff (Dec 9-13)**

**Lunes-Martes (Dec 9-10):**
- [ ] Completar documentación técnica
- [ ] README, architecture diagram, API docs
- [ ] Video tutorial para usuarios

**Miércoles (Dec 11):**
- [ ] **Handoff meeting con Tech** (1 hora)
- [ ] Q&A session
- [ ] Transferencia de conocimiento

**Jueves-Viernes (Dec 12-13):**
- [ ] Soporte post-handoff
- [ ] Resolver dudas del equipo Tech
- [ ] **PROJECT COMPLETE** ✅

---

## 🚨 BLOCKERS Y MITIGACIONES

### **BLOCKER #1 - Acceso a Drive (CRÍTICO - RESUELTO)**
**Status:** ✅ Resuelto - Acceso confirmado  
**Path:** "BASE DE DATOS FACTURAS CLIENTES"  
**Estructura:** Validada (carpetas por mes)

---

### **BLOCKER #2 - Permisos de Drive (PENDIENTE VALIDAR)**
**Status:** ⏳ Por validar cuando se conecte API  
**Owner:** María Alejandra  
**Impacto:** Define si podemos implementar histórico acumulativo automático

**Escenarios:**

**Si permisos = Solo Lectura:**
- ✅ Usuario sube Excel maestro mensual (acumulativo)
- ✅ Sistema consulta PDFs/XMLs en Drive
- ❌ NO puede actualizar histórico automáticamente

**Si permisos = Lectura + Escritura:**
- ✅ Usuario sube Excel maestro mensual (acumulativo)
- ✅ Sistema consulta PDFs/XMLs en Drive
- ✅ Sistema puede actualizar/reescribir archivo maestro en Drive
- ✅ Posibilidad de mantener histórico sincronizado (post-MVP)

**Mitigación:** Implementar ambos flujos, activar según permisos disponibles

---

### **BLOCKER #3 - Naming Inconsistencies**
**Riesgo:** Archivos en Drive no sigan naming convention (UUID exacto)  
**Probabilidad:** Baja  
**Mitigación:**
- Validación durante testing con data real
- Implementar búsqueda fuzzy si hay variaciones menores
- Logs detallados para identificar archivos no encontrados

---

## 🧪 TESTING STRATEGY (ACTUALIZADA)

### **Alpha Testing (Week 2 - Nov 25-29)**

**Objetivos:**
- Validar que la herramienta funciona end-to-end
- Identificar bugs críticos antes del demo

**Casos de Prueba:**

1. **Carga de Excel:**
   - [ ] Excel válido con todas las columnas
   - [ ] Excel sin columna requerida
   - [ ] Excel vacío
   - [ ] Archivo que no es Excel

2. **Búsqueda:**
   - [ ] Por código de operación (1 factura)
   - [ ] Por código de operación (5+ facturas)
   - [ ] Por RFC (múltiples operaciones)
   - [ ] Por RFC + rango de fechas
   - [ ] Sin resultados
   - [ ] Sin Excel cargado (debe dar error)

3. **Generación de ZIP:**
   - [ ] 1 factura (2 archivos: PDF + XML)
   - [ ] 5 facturas (10 archivos + Excel)
   - [ ] Factura con archivo faltante (debe marcar)
   - [ ] Validar Excel detallado tiene 8 columnas correctas

4. **Performance:**
   - [ ] Búsqueda de 10 facturas: <5 segundos
   - [ ] Generación de ZIP con 10 facturas: <30 segundos

**Testers:** María Alejandra (autotesting)  
**Success Criteria:** 0 bugs P0 (críticos que impiden usar la herramienta)

---

### **Demo Testing (Dec 2 - Con Johan y Jonathan)**

**Escenarios Reales:**
1. **Caso 1:** Cliente pide facturas de una operación específica
   - Código de operación conocido
   - Generar ZIP y validar contenido

2. **Caso 2:** Cliente pide facturas de Q3 2025
   - Buscar por RFC + rango de fechas (Jul-Sep)
   - Validar que filtre correctamente

3. **Caso 3:** Cliente pide facturas de múltiples operaciones
   - Buscar cada código por separado (o batch si está implementado)
   - Generar ZIP consolidado

**Success Criteria:**
- Johan y Jonathan pueden usar la herramienta sin ayuda
- Logran generar ZIPs correctos en <2 minutos
- El Excel detallado es claro y útil

---

### **Beta Testing (Week 3 - Dec 3-5)**

**Escenario:** 5 solicitudes reales de clientes durante 3 días

**Proceso:**
1. Johan/Jonathan reciben solicitud de cliente
2. Usan la herramienta para generar ZIP
3. Documentan: tiempo, issues, feedback
4. Comparan con proceso manual (¿qué fue mejor/peor?)

**Success Criteria:**
- 5/5 solicitudes resueltas con la herramienta
- Tiempo promedio <2 minutos (vs 10 minutos manual)
- 0 documentos faltantes o incorrectos
- Johan y Jonathan confirman que es más rápido

---

## 🤝 HANDOFF REQUIREMENTS

### **Documentación Requerida**

**1. Technical Documentation:**
- [ ] README.md con setup instructions
- [ ] Architecture diagram (Mermaid o Draw.io)
- [ ] API documentation (endpoints, schemas, examples)
- [ ] Google Drive setup guide (service account, permisos)
- [ ] Environment variables guide (.env.example explicado)

**2. User Documentation:**
- [ ] User guide para equipo de Facturación MX
- [ ] Video tutorial (5-10 min) mostrando flujo completo
- [ ] FAQ con errores comunes y soluciones
- [ ] Troubleshooting guide

**3. Code Quality:**
- [ ] Repositorio en GitHub/GitLab con acceso para Tech
- [ ] Tests unitarios (coverage >70%)
- [ ] Code comments y docstrings
- [ ] .gitignore y .env.example

**4. Deployment:**
- [ ] Backend deployado en servidor de producción
- [ ] Frontend integrado en Hub de Servicios
- [ ] Google Drive service account configurado
- [ ] Logs y monitoring básico configurados

---

### **Handoff Meeting Agenda (1 hora)**

**Bloque 1 (15 min): Demo Funcional**
- María Alejandra demuestra herramienta completa
- Johan/Jonathan validan que cumple requirements

**Bloque 2 (20 min): Walkthrough Técnico**
- Arquitectura y decisiones técnicas
- Estructura de código
- Google Drive API integration
- Variables de ambiente

**Bloque 3 (15 min): Q&A**
- Tech hace preguntas técnicas
- Aclaración de dudas
- Revisión de documentación

**Bloque 4 (10 min): Next Steps**
- Plan de soporte post-handoff
- Ownership transfer
- Cronograma de mejoras futuras (should-have)

---

## 📊 APÉNDICE: ESTRUCTURA DETALLADA DEL EXCEL DETALLADO

### **Columnas del Excel (8 total):**

| # | Columna | Tipo | Ejemplo | Fuente (Excel Maestro) |
|---|---------|------|---------|------------------------|
| 1 | UUID | Text | f6ba4a44-ea71-4263-86f2-2b1687eefe14 | UUID |
| 2 | Código de Operación | Text | MX:BSM210224366:1:6:PAG | CODIGO DE OPERACIÓN |
| 3 | Tipo | Text | Ingreso / Egreso | Tipo |
| 4 | Fecha Emisión | Date | 01/10/2025 | Fecha emision |
| 5 | Concepto | Text | INTERESES POR PRESTAMO OTORGADO... | Conceptos |
| 6 | Subtotal | Number | 100.00 | SubTotal |
| 7 | IVA | Number | 16.00 | IVA Trasladado |
| 8 | Total | Number | 116.00 | Total |

### **Fila de Totales:**
- Última fila del Excel
- Columna Concepto: "TOTAL"
- Columnas Subtotal, IVA, Total: Suma de todas las filas

### **Formato:**
- Encabezados: Negrita, fondo gris claro
- Montos: 2 decimales, formato `#,##0.00`
- Fechas: Formato `DD/MM/YYYY`
- Tipo: Badge visual (verde para Ingreso, rojo para Egreso) - opcional en Excel

---

## 📞 CONTACTS

**Product Owner:** Maria Alejandra Gaitán - maria.gaitan@finkargo.com  
**Primary Users:** Jonathan Medina - jonathan.medina@finkargo.com, Johan Acevedo - johan.acevedo@finkargo.com  
**Tech Lead:** [TBD - asignar cuando se haga handoff]

---

## 📝 CHANGELOG

**v2.0 (Nov 18, 2025):**
- ✅ Reunión Go/No-Go completada - Decisión: GO
- ✅ Estructura de Drive confirmada (carpeta "BASE DE DATOS FACTURAS CLIENTES")
- ✅ Excel detallado actualizado a 8 columnas (agregado Código de Operación)
- ✅ Naming conventions documentadas
- ✅ Timeline ajustado (arranque Nov 18)
- ✅ Búsqueda optimizada por mes agregada
- ✅ Permisos de Drive identificados como blocker a validar

**v1.0 (Nov 13, 2025):**
- Versión inicial del PRD pre-Go/No-Go

---

**Versión:** 2.0  
**Última Actualización:** Noviembre 18, 2025  
**Siguiente Revisión:** Post-Demo (Dec 2, 2025)  
**Status:** ✅ GO - En Desarrollo Activo
