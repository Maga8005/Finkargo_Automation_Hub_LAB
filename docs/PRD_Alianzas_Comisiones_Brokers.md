# PRD: Módulo Alianzas - Cálculo de Comisiones de Brokers

## Información del Documento

| Campo | Valor |
|-------|-------|
| **Versión** | 1.0 |
| **Fecha** | 2025-12-10 |
| **Autor** | Daniel Restrepo (Engineering) |
| **Stakeholders** | Enrique Roman Macias, Liria Flores Ferrando |
| **Estado** | Draft |

---

## 1. Resumen Ejecutivo

### 1.1 Problema
El equipo de Alianzas actualmente realiza el cálculo de comisiones de brokers de forma manual utilizando múltiples fuentes de información dispersas (contratos en Google Drive, plataforma Jarvis, estados de cuenta, tipo de cambio del Banco de México). Este proceso es:
- **Propenso a errores**: requiere consultar información cliente por cliente
- **Tiempo-intensivo**: implica revisar contratos individuales para extraer condiciones
- **Difícil de escalar**: con el crecimiento del programa de brokers, el proceso se vuelve insostenible

### 1.2 Solución Propuesta
Desarrollar un módulo de **Alianzas** dentro del Finkargo Automation Hub que automatice:
1. Extracción de condiciones comerciales desde contratos de brokers (PDF/DOCX)
2. Consolidación de información de comisiones por cliente desde la plataforma
3. Cálculo automático de comisiones de apertura y operativas
4. Conversión a pesos mexicanos usando tipo de cambio oficial
5. Generación de reportes mensuales de pago a brokers

### 1.3 Impacto Esperado
- Reducción del 80% en tiempo de cálculo de comisiones
- Eliminación de errores manuales en el proceso
- Visibilidad en tiempo real del estado de comisiones
- Base para futura integración con Finecto (portal de brokers)

---

## 2. Contexto del Negocio

### 2.1 Programa de Brokers
Finkargo trabaja con diferentes tipos de aliados comerciales:
- **Master Brokers**: Empresas con red de sub-brokers
- **Brokers Independientes**: Consultores individuales
- **Aliados Logísticos**: Freight forwarders, marketplaces de entregas
- **Empresas de Consultoría**: Firmas que refieren clientes corporativos

### 2.2 Tipos de Comisiones
| Tipo | Descripción | Base de Cálculo |
|------|-------------|-----------------|
| **Comisión de Apertura** | Pago único al activar un cliente nuevo | % sobre la comisión de apertura cobrada al cliente |
| **Comisión Operativa** | Pago recurrente por operaciones del cliente | % sobre el monto desembolsado mensualmente |

### 2.3 Reglas de Negocio Críticas
1. **Condición de pago**: Solo se paga al broker si el cliente ha pagado (mínimo 50%)
2. **Corte mensual**: Las comisiones se calculan y pagan mensualmente
3. **Incrementos de línea**: Aplican comisiones reducidas sobre el incremento
4. **Moneda**: Contratos en USD, pagos a brokers en MXN

---

## 3. Fuentes de Información

### 3.1 Base Brokers (Google Drive)
**Ubicación**: Carpeta "Expediente de Brokers" compartida
**Contenido por broker**:
- Acta constitutiva
- Opinión de cumplimiento
- Identificación del representante
- Carátula de estado de cuenta bancaria
- **Contrato firmado** (con anexo de condiciones comerciales)

**Datos a extraer del contrato**:
| Campo | Ejemplo | Ubicación en Documento |
|-------|---------|------------------------|
| % Comisión Apertura (broker) | 60%, 80% | Anexo - "Bono equivalente al X%" |
| % Comisión Operativa | 0.10% | Anexo - "Porcentaje operativa" |
| Vigencia del contrato | 12 meses | Cláusula de vigencia |

**Versiones de contrato identificadas**:
- Versión Marzo 2024: Anexo con formato tabla
- Versión Actual: Formato actualizado

### 3.2 Plataforma Jarvis (Gestión de Cuentas)
**Datos disponibles por cliente**:
| Campo | Descripción |
|-------|-------------|
| Línea de crédito aprobada | Monto en USD |
| Comisión de apertura (%) | % negociado por cliente |
| Etiqueta "Cliente por Broker" | Vincula cliente con broker |
| Broker asignado | Nombre del broker referidor |

**Reporte sugerido**: Data Customer Resume

### 3.3 Estado de Cuenta (Plataforma)
**Datos a verificar**:
| Campo | Uso |
|-------|-----|
| Pago de comisión de apertura | ¿Cliente pagó? (total/parcial) |
| Operaciones del mes | Monto desembolsado acumulado |
| Estado de cartera | ¿Cliente al corriente? (no en paro) |

### 3.4 Tipo de Cambio - Banco de México
**URL**: https://www.banxico.org.mx/tipcamb/tipCamMIAction.do
**Dato**: Tipo de cambio FIX del día de corte

---

## 4. Especificación Funcional

### 4.1 Módulo: Alianzas

#### 4.1.1 Menú de Navegación
```
Alianzas
├── Comisiones Brokers
│   ├── Cálculo Mensual
│   ├── Historial de Pagos
│   └── Configuración
└── (Futuro) Portal Broker
```

#### 4.1.2 Roles y Permisos
| Rol | Permisos |
|-----|----------|
| `admin` | Acceso completo |
| `alianzas` | CRUD comisiones, generar reportes |
| `operations` | Solo lectura |

### 4.2 Feature: Tabla Maestra de Brokers

**Propósito**: Mantener catálogo centralizado de brokers con sus condiciones comerciales

**Campos de la tabla**:
| Campo | Tipo | Descripción | Fuente |
|-------|------|-------------|--------|
| `id` | UUID | Identificador único | Auto-generado |
| `nombre_broker` | String | Nombre o razón social | Base Brokers |
| `tipo_broker` | Enum | master_broker, independiente, aliado_logistico, consultoria | Manual |
| `master_broker_id` | UUID | Referencia a master broker (si aplica) | Manual |
| `porcentaje_apertura` | Decimal | % sobre comisión de apertura (ej: 60%) | Contrato |
| `porcentaje_operativa` | Decimal | % sobre operaciones (ej: 0.10%) | Contrato |
| `cuenta_bancaria` | String | Cuenta para depósitos | Documentos |
| `banco` | String | Institución bancaria | Documentos |
| `rfc` | String | RFC del broker | Documentos |
| `fecha_contrato` | Date | Fecha de firma | Contrato |
| `vigencia_contrato` | Date | Fecha de expiración | Contrato |
| `estado` | Enum | activo, inactivo, pendiente | Manual |
| `link_expediente` | URL | Link a carpeta en Drive | Base Brokers |
| `created_at` | Timestamp | Fecha de creación | Auto |
| `updated_at` | Timestamp | Última actualización | Auto |

**Funcionalidades**:
1. **Importación masiva de contratos**: Subir PDFs/DOCXs y extraer condiciones automáticamente
2. **CRUD manual**: Crear, editar, desactivar brokers
3. **Búsqueda y filtros**: Por nombre, tipo, estado
4. **Exportación**: Excel con catálogo completo

### 4.3 Feature: Cálculo de Comisiones Mensual

**Propósito**: Generar el cálculo de comisiones a pagar por corte mensual

#### 4.3.1 Flujo del Proceso

```
┌─────────────────────────────────────────────────────────────────┐
│                    CÁLCULO DE COMISIONES                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Seleccionar período (mes/año)                               │
│  2. Cargar datos de plataforma (clientes por broker)            │
│  3. Verificar estados de cuenta (pagos de clientes)             │
│  4. Aplicar condiciones de contrato (% broker)                  │
│  5. Obtener tipo de cambio del período                          │
│  6. Calcular montos en USD y MXN                                │
│  7. Generar reporte para revisión                               │
│  8. Aprobar y exportar para pago                                │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 Interfaz de Usuario

**Pantalla: Cálculo Mensual**

```
┌─────────────────────────────────────────────────────────────────┐
│ CÁLCULO DE COMISIONES - BROKERS                                 │
├─────────────────────────────────────────────────────────────────┤
│ Período: [Noviembre ▼] [2024 ▼]    [Calcular Comisiones]       │
│ Tipo de Cambio: $18.30 MXN/USD     Fecha: 30/11/2024           │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Cliente        │ Broker         │ Tipo    │ USD    │ MXN    │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Aceites        │ Fernando       │ Apertura│ $3,600 │ $65,880│ │
│ │ Nutrimich      │ Medina         │ Operativa│ $160  │ $2,928 │ │
│ │                │                │ TOTAL   │ $3,760 │ $68,808│ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Aluminios      │ Federico       │ Apertura│ $6,000 │$109,800│ │
│ │ Extruidos      │ Aguirre        │ Operativa│ $500  │ $9,150 │ │
│ │                │                │ TOTAL   │ $6,500 │$118,950│ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ RESUMEN POR BROKER:                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Broker           │ Clientes │ Total USD │ Total MXN        │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Fernando Medina  │ 3        │ $5,240    │ $95,892          │ │
│ │ Federico Aguirre │ 5        │ $12,800   │ $234,240         │ │
│ │ ...              │ ...      │ ...       │ ...              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [Exportar Excel]  [Exportar PDF]  [Aprobar y Programar Pagos]  │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.3.3 Fórmulas de Cálculo

**Comisión de Apertura**:
```
monto_comision_apertura = linea_credito × (porcentaje_comision_cliente / 100)
pago_broker_apertura = monto_comision_apertura × (porcentaje_broker / 100)
```

**Ejemplo**:
- Línea de crédito: $1,000,000 USD
- Comisión cliente: 1%
- Monto comisión: $10,000 USD
- % Broker: 60%
- **Pago broker**: $6,000 USD

**Comisión Operativa**:
```
pago_broker_operativa = operaciones_mes × (porcentaje_operativa / 100)
```

**Ejemplo**:
- Operaciones del mes: $600,000 USD
- % Operativa: 0.10%
- **Pago broker**: $600 USD

**Conversión a MXN**:
```
monto_mxn = monto_usd × tipo_cambio_banxico
```

#### 4.3.4 Validaciones y Reglas

| Regla | Descripción | Acción |
|-------|-------------|--------|
| Cliente debe haber pagado | Mínimo 50% de comisión de apertura | Bloquear si no pagó |
| Cliente al corriente | No debe estar en paro de cartera | Advertencia |
| Contrato vigente | Broker debe tener contrato activo | Bloquear si expirado |
| Operaciones verificadas | Desembolsos deben estar confirmados | Validar contra estado de cuenta |

### 4.4 Feature: Extracción Automática de Contratos

**Propósito**: Extraer condiciones comerciales de contratos PDF/DOCX automáticamente

#### 4.4.1 Métodos de Extracción

El sistema ofrece **dos métodos de extracción** para adaptarse a diferentes tipos de documentos:

| Método | Descripción | Casos de Uso | Tiempo |
|--------|-------------|--------------|--------|
| **Extracción por Patrones (Regex)** | Extracción basada en texto usando expresiones regulares | Contratos DOCX o PDFs con texto seleccionable | < 5 segundos |
| **Extracción con IA (LandingAI)** | Extracción inteligente usando LandingAI ADE API | Contratos escaneados, imágenes, PDFs sin texto extraíble | 30-60 segundos |

#### 4.4.2 Proceso de Extracción

```
┌─────────────────────────────────────────────────────────────────┐
│                 EXTRACCIÓN DE CONTRATOS                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Subir archivo(s) de contrato (PDF/DOCX)                     │
│  2. Seleccionar método de extracción:                           │
│     ☐ Extracción estándar (Regex/Texto)                        │
│     ☐ Extracción con IA (LandingAI) - Para escaneados          │
│  3. Sistema procesa el documento                                │
│  4. Presenta datos extraídos para validación                    │
│  5. Usuario confirma o corrige                                  │
│  6. Datos se guardan en tabla maestra                          │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.4.3 Extracción Estándar (Regex/Texto)

Para contratos DOCX o PDFs con texto seleccionable, se utilizan patrones específicos por versión:

**Versión Marzo 2024**:
```
Patrón Apertura: "Bono equivalente al (\d+)%"
Patrón Operativa: "(\d+\.?\d*)%.*operativa"
```

**Versión Actual**:
```
Patrón Apertura: "(\d+)% de la comisión de apertura"
Patrón Operativa: "(\d+\.?\d*)%.*por operación"
```

#### 4.4.4 Extracción con IA (LandingAI ADE)

Para contratos escaneados o PDFs basados en imágenes donde la extracción de texto falla, se utiliza **LandingAI's Agentic Document Extraction (ADE)** API.

**Proceso de dos pasos**:
1. **ADE Parse API**: Convierte el PDF/imagen a formato Markdown estructurado
2. **ADE Extract API**: Extrae datos específicos usando un schema JSON predefinido

**Schema de Extracción para Contratos de Broker**:
```json
{
    "type": "object",
    "properties": {
        "nombre_broker": {
            "type": "string",
            "description": "Nombre o razón social del broker/aliado comercial"
        },
        "porcentaje_comision_apertura": {
            "type": "number",
            "description": "Porcentaje de la comisión de apertura que corresponde al broker (ej: 60, 80)"
        },
        "porcentaje_comision_operativa": {
            "type": "number",
            "description": "Porcentaje sobre operaciones/desembolsos mensuales (ej: 0.10, 0.15)"
        },
        "fecha_contrato": {
            "type": "string",
            "description": "Fecha de firma del contrato (formato DD/MM/YYYY)"
        },
        "vigencia_meses": {
            "type": "integer",
            "description": "Vigencia del contrato en meses (ej: 12, 24)"
        },
        "rfc_broker": {
            "type": "string",
            "description": "RFC del broker para facturación"
        },
        "cuenta_bancaria": {
            "type": "string",
            "description": "Número de cuenta CLABE para depósitos"
        },
        "banco": {
            "type": "string",
            "description": "Nombre de la institución bancaria"
        }
    },
    "required": [
        "nombre_broker",
        "porcentaje_comision_apertura",
        "porcentaje_comision_operativa"
    ]
}
```

**Configuración requerida**:
- Variable de entorno: `LANDINGAI_API_KEY`
- Endpoints configurados en `settings.py`:
  - `LANDINGAI_PARSE_ENDPOINT`: Para conversión PDF → Markdown
  - `LANDINGAI_EXTRACT_ENDPOINT`: Para extracción estructurada

**Manejo de errores**:
| Error | Causa | Acción |
|-------|-------|--------|
| Timeout (>120s) | Documento muy grande o complejo | Reintentar o usar extracción manual |
| HTTP 401 | API key inválida | Verificar configuración |
| HTTP 429 | Rate limit excedido | Esperar y reintentar |
| Campos faltantes | IA no pudo identificar valores | Revisión manual por usuario |

#### 4.4.5 Interfaz de Usuario - Upload de Contratos

```
┌─────────────────────────────────────────────────────────────────┐
│ EXTRACCIÓN DE CONDICIONES - CONTRATO BROKER                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Subir Contrato:  [Seleccionar archivo...]  contrato.pdf       │
│                                                                 │
│  Método de Extracción:                                         │
│  ○ Extracción Estándar (Recomendado para DOCX/PDF con texto)   │
│  ○ Extracción con IA (Para documentos escaneados)              │
│     ⚠️ Proceso más lento (30-60 segundos)                       │
│                                                                 │
│                            [Extraer Datos]                      │
├─────────────────────────────────────────────────────────────────┤
│ DATOS EXTRAÍDOS (verificar antes de guardar):                   │
│                                                                 │
│  Nombre Broker:        [Federico Aguirre          ]            │
│  % Comisión Apertura:  [60          ] %                        │
│  % Comisión Operativa: [0.10        ] %                        │
│  Fecha Contrato:       [15/03/2024  ]                          │
│  Vigencia:             [12          ] meses                    │
│  RFC:                  [GAAF850312XXX]                         │
│  Cuenta CLABE:         [012180001234567890]                    │
│  Banco:                [BBVA                ]                  │
│                                                                 │
│  ✓ Datos extraídos exitosamente                                │
│                                                                 │
│         [Cancelar]                    [Guardar en Catálogo]    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 Feature: Historial de Pagos

**Propósito**: Consultar histórico de comisiones pagadas por broker

**Campos del historial**:
| Campo | Descripción |
|-------|-------------|
| Período | Mes/Año del corte |
| Broker | Nombre del broker |
| Total USD | Monto total en dólares |
| Total MXN | Monto total en pesos |
| Tipo de cambio | TC usado para conversión |
| Fecha de pago | Cuándo se realizó el pago |
| Estado | programado, pagado, pendiente |
| Comprobante | Link a comprobante de pago |

---

## 5. Modelo de Datos

### 5.1 Nuevas Tablas

```sql
-- Tabla maestra de brokers
CREATE TABLE brokers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    tipo_broker VARCHAR(50) NOT NULL, -- master_broker, independiente, aliado_logistico, consultoria
    master_broker_id UUID REFERENCES brokers(id),
    porcentaje_apertura DECIMAL(5,2), -- ej: 60.00
    porcentaje_operativa DECIMAL(5,3), -- ej: 0.100
    cuenta_bancaria VARCHAR(50),
    banco VARCHAR(100),
    rfc VARCHAR(20),
    fecha_contrato DATE,
    vigencia_contrato DATE,
    estado VARCHAR(20) DEFAULT 'activo', -- activo, inactivo, pendiente
    link_expediente TEXT,
    notas TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Tabla de comisiones calculadas
CREATE TABLE broker_comisiones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    broker_id UUID REFERENCES brokers(id) NOT NULL,
    periodo_mes INTEGER NOT NULL, -- 1-12
    periodo_anio INTEGER NOT NULL,
    cliente_nombre VARCHAR(255),
    cliente_nit VARCHAR(50),
    tipo_comision VARCHAR(20) NOT NULL, -- apertura, operativa
    linea_credito DECIMAL(15,2),
    porcentaje_comision_cliente DECIMAL(5,2),
    monto_comision_cliente DECIMAL(15,2),
    porcentaje_broker DECIMAL(5,3),
    monto_broker_usd DECIMAL(15,2),
    operaciones_mes DECIMAL(15,2),
    tipo_cambio DECIMAL(10,4),
    monto_broker_mxn DECIMAL(15,2),
    cliente_pago_pct DECIMAL(5,2), -- % que pagó el cliente
    estado VARCHAR(20) DEFAULT 'calculado', -- calculado, aprobado, pagado
    notas TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Tabla de pagos a brokers
CREATE TABLE broker_pagos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    broker_id UUID REFERENCES brokers(id) NOT NULL,
    periodo_mes INTEGER NOT NULL,
    periodo_anio INTEGER NOT NULL,
    total_usd DECIMAL(15,2) NOT NULL,
    total_mxn DECIMAL(15,2) NOT NULL,
    tipo_cambio DECIMAL(10,4) NOT NULL,
    fecha_programada DATE,
    fecha_pago DATE,
    estado VARCHAR(20) DEFAULT 'pendiente', -- pendiente, programado, pagado
    comprobante_url TEXT,
    factura_broker_url TEXT,
    notas TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    approved_by UUID REFERENCES auth.users(id)
);

-- Índices
CREATE INDEX idx_brokers_estado ON brokers(estado);
CREATE INDEX idx_broker_comisiones_periodo ON broker_comisiones(periodo_anio, periodo_mes);
CREATE INDEX idx_broker_comisiones_broker ON broker_comisiones(broker_id);
CREATE INDEX idx_broker_pagos_broker ON broker_pagos(broker_id);
CREATE INDEX idx_broker_pagos_estado ON broker_pagos(estado);
```

### 5.2 Row Level Security

```sql
-- RLS para brokers
ALTER TABLE brokers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read brokers"
ON brokers FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Alianzas and admin can manage brokers"
ON brokers FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('admin', 'alianzas')
    )
);
```

---

## 6. Arquitectura Técnica

### 6.1 Backend (FastAPI)

**Nuevos archivos**:
```
backend/src/
├── adapter/rest/
│   └── alianzas_routes.py                    # Endpoints del módulo
├── core/servicios/
│   ├── broker_service.py                     # Lógica de negocio brokers
│   ├── comision_service.py                   # Cálculo de comisiones
│   ├── contract_extractor_service.py         # Extracción estándar (Regex/Texto)
│   ├── landingai_contract_parser_service.py  # Extracción con IA (LandingAI ADE)
│   └── banxico_service.py                    # Tipo de cambio Banxico
├── repositorio/
│   └── broker_repository.py                  # Acceso a datos brokers
└── interface/
    └── alianzas_dtos.py                      # DTOs del módulo
```

**Servicios de Extracción de Contratos**:

| Servicio | Descripción | Patrón |
|----------|-------------|--------|
| `contract_extractor_service.py` | Extracción basada en texto/regex para DOCX y PDFs con texto | Similar a `cotizacion_parser_service.py` |
| `landingai_contract_parser_service.py` | Extracción con IA para documentos escaneados | Basado en `landingai_rut_parser_service.py` |

**Integración con LandingAI existente**:
- Reutiliza la configuración existente de `LANDINGAI_API_KEY` en `settings.py`
- Usa los mismos endpoints `LANDINGAI_PARSE_ENDPOINT` y `LANDINGAI_EXTRACT_ENDPOINT`
- Sigue el mismo patrón de dos pasos (Parse → Extract) del servicio RUT

**Endpoints principales**:
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/alianzas/brokers` | Listar brokers |
| POST | `/api/alianzas/brokers` | Crear broker |
| PUT | `/api/alianzas/brokers/{id}` | Actualizar broker |
| POST | `/api/alianzas/brokers/extract-contract` | Extraer datos de contrato (estándar) |
| POST | `/api/alianzas/brokers/extract-contract-ai` | Extraer datos con LandingAI (IA) |
| GET | `/api/alianzas/comisiones` | Listar comisiones por período |
| POST | `/api/alianzas/comisiones/calcular` | Calcular comisiones del mes |
| POST | `/api/alianzas/comisiones/aprobar` | Aprobar comisiones |
| GET | `/api/alianzas/pagos` | Historial de pagos |
| GET | `/api/alianzas/tipo-cambio` | Obtener TC de Banxico |

**Detalle endpoint extracción con IA**:
```python
@router.post("/brokers/extract-contract-ai")
async def extract_contract_ai(
    contract_file: UploadFile = File(..., description="Contrato PDF del broker"),
    current_user: dict = Depends(require_alianzas_role)
) -> BrokerContractData:
    """
    Extrae condiciones comerciales de un contrato de broker usando LandingAI ADE.

    Recomendado para:
    - Contratos escaneados (imagen)
    - PDFs sin texto seleccionable
    - Documentos con formato no estándar

    Tiempo de procesamiento: 30-60 segundos
    """
```

### 6.2 Frontend (React)

**Nuevos archivos**:
```
frontend/src/
├── pages/
│   └── alianzas/
│       ├── AlianzasDashboard.tsx       # Dashboard principal
│       ├── BrokersList.tsx             # Lista de brokers
│       ├── BrokerDetail.tsx            # Detalle/edición broker
│       ├── ComisionesCalculo.tsx       # Cálculo mensual
│       └── PagosHistorial.tsx          # Historial de pagos
├── components/
│   └── alianzas/
│       ├── FKBrokerForm.tsx            # Formulario de broker
│       ├── FKContractUpload.tsx        # Upload de contratos con selector de método
│       ├── FKComisionesTable.tsx       # Tabla de comisiones
│       └── FKPagosTable.tsx            # Tabla de pagos
└── services/
    └── alianzasService.ts              # Llamadas API (incluye extractContractAI)
```

**Componente FKContractUpload - Props**:
```typescript
interface FKContractUploadProps {
  onExtracted: (data: BrokerContractData) => void;
  onError: (error: string) => void;
}

// Métodos de extracción disponibles
type ExtractionMethod = 'standard' | 'ai';

// Estados durante extracción AI
type AIExtractionStatus = 'idle' | 'uploading' | 'parsing' | 'extracting' | 'complete' | 'error';
```

**Servicio alianzasService.ts**:
```typescript
// Extracción estándar (regex/texto)
export const extractContract = async (file: File): Promise<BrokerContractData> => {
  const formData = new FormData();
  formData.append('contract_file', file);
  const response = await apiClient.post('/alianzas/brokers/extract-contract', formData);
  return response.data;
};

// Extracción con IA (LandingAI)
export const extractContractAI = async (file: File): Promise<BrokerContractData> => {
  const formData = new FormData();
  formData.append('contract_file', file);
  // Timeout más largo para procesamiento AI (2 minutos)
  const response = await apiClient.post('/alianzas/brokers/extract-contract-ai', formData, {
    timeout: 120000
  });
  return response.data;
};
```

### 6.3 Integración con Banxico

**Servicio de tipo de cambio**:
```python
# backend/src/core/servicios/banxico_service.py
class BanxicoService:
    """Obtiene tipo de cambio FIX del Banco de México"""

    BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/"
    SERIE_TC = "SF43718"  # Serie del tipo de cambio FIX

    async def get_tipo_cambio(self, fecha: date) -> Decimal:
        """Obtiene el tipo de cambio para una fecha específica"""
        pass

    async def get_tipo_cambio_actual(self) -> Decimal:
        """Obtiene el tipo de cambio más reciente"""
        pass
```

---

## 7. Plan de Implementación

### Fase 1: Fundamentos (Sprint 1)
- [ ] Crear estructura de base de datos (tablas, RLS)
- [ ] Implementar endpoints CRUD de brokers
- [ ] Crear UI de lista y formulario de brokers
- [ ] Agregar rol `alianzas` al sistema

### Fase 2: Extracción de Contratos (Sprint 2)
- [ ] Desarrollar servicio de extracción estándar (Regex/Texto) para PDF/DOCX
- [ ] Crear patrones para versiones de contrato conocidas (Marzo 2024, Actual)
- [ ] Desarrollar servicio de extracción con IA (`landingai_contract_parser_service.py`)
  - [ ] Definir schema JSON para contratos de broker
  - [ ] Implementar llamadas a ADE Parse y Extract APIs
  - [ ] Mapear respuesta a DTOs de broker
- [ ] Implementar UI de carga con selector de método (estándar vs IA)
- [ ] Importación masiva de contratos existentes

### Fase 3: Cálculo de Comisiones (Sprint 3)
- [ ] Integrar con API de Banxico para tipo de cambio
- [ ] Desarrollar lógica de cálculo de comisiones
- [ ] Crear interfaz de cálculo mensual
- [ ] Implementar validaciones de negocio

### Fase 4: Reportes y Aprobación (Sprint 4)
- [ ] Generar exportación a Excel
- [ ] Flujo de aprobación de comisiones
- [ ] Historial de pagos
- [ ] Dashboard de métricas

### Fase 5 (Futura): Portal Broker
- [ ] Integración con Finecto
- [ ] Autogestión de facturas por broker
- [ ] Visibilidad de estado de pagos

---

## 8. Métricas de Éxito

| Métrica | Baseline Actual | Objetivo |
|---------|-----------------|----------|
| Tiempo de cálculo mensual | 4-6 horas | < 30 minutos |
| Errores en cálculos | ~5% | < 1% |
| Consultas de brokers | Diarias | Autoservicio (Fase 5) |
| Tiempo de extracción de contrato | 15 min/contrato | < 2 min/contrato |

---

## 9. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Contratos con formato no estandarizado | Alta | Medio | Extracción semi-automática con validación manual |
| API Banxico no disponible | Baja | Alto | Caché de tipos de cambio + entrada manual |
| Datos incompletos en plataforma | Media | Alto | Validaciones y alertas en el proceso |
| Resistencia al cambio | Media | Medio | Capacitación y período de transición |

---

## 10. Dependencias

### 10.1 Internas
- Acceso a carpeta de expedientes de brokers (Google Drive)
- Reporte "Data Customer Resume" de Jarvis
- Acceso a estados de cuenta de clientes

### 10.2 Externas
- API de tipo de cambio del Banco de México
- **LandingAI ADE API** (ya configurada para RUT extraction)
  - `LANDINGAI_API_KEY` - Clave API existente
  - `LANDINGAI_PARSE_ENDPOINT` - Endpoint de parsing
  - `LANDINGAI_EXTRACT_ENDPOINT` - Endpoint de extracción
- (Futura) API de Finecto para portal de brokers

---

## 11. Anexos

### 11.1 Ejemplo de Cálculo Completo

**Cliente**: Aceites Nutrimich
**Broker**: Fernando Medina
**Período**: Noviembre 2024

| Concepto | Valor |
|----------|-------|
| Línea de crédito | $200,000 USD |
| Comisión apertura (cliente) | 3% |
| Monto comisión apertura | $6,000 USD |
| % Broker (contrato) | 60% |
| Pago broker apertura | $3,600 USD |
| Operaciones del mes | $160,050 USD |
| % Operativa (contrato) | 0.10% |
| Pago broker operativa | $160.05 USD |
| **Total USD** | **$3,760.05** |
| Tipo de cambio | 18.30 |
| **Total MXN** | **$68,808.92** |

### 11.2 Estructura de Carpeta de Expedientes

```
Expediente de Brokers/
├── Agencia Creativa Cuarto Estudio/
│   ├── Acta Constitutiva.pdf
│   ├── Opinion de Cumplimiento.pdf
│   ├── Identificacion.pdf
│   ├── Caratula Estado de Cuenta.pdf
│   └── Contrato/
│       └── Contrato_Broker_2024.pdf
├── Edgar Garza/
│   └── ...
└── Federico Aguirre/
    └── ...
```

### 11.3 Formato de Condiciones en Contrato

**Versión Marzo 2024 (Anexo)**:
```
ANEXO DE CONDICIONES COMERCIALES

Bono equivalente al 60% calculado sobre el monto cobrado a cada
nuevo cliente por concepto de comisión de apertura.

Comisión operativa: 0.10% sobre cada desembolso realizado.
```

---

## 12. Aprobaciones

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| Product Owner | Enrique Roman | | |
| Tech Lead | Daniel Restrepo | | |
| Stakeholder | Liria Flores | | |

---

*Documento generado automáticamente desde transcript de reunión del equipo de Alianzas.*
