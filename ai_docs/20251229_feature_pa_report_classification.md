# Plan: PA Report Classification Feature for Finance Module

## Overview

Add a new "Reporte PA" (Patrimonio Autónomo Report) feature to the Finance module that:
1. Allows uploading and managing classification rules
2. Processes NetSuite movement files to generate cleaned and classified PA reports

## Requirements Summary

### Source Data
- **Input**: NetSuite "Movimiento Detallado por Cuenta" Excel file (~50k rows/month)
- **PA Account Catalog**: Excel file mapping which accounts belong to PA
- **Classification Rules**: Excel files defining how to categorize transactions

### Output Columns to Add
1. **PA** - Mark with 'X' for PA accounts
2. **Categoría** - Main category classification
3. **Subcategoría** - Sub-category classification
4. **Clasificación** - Detailed classification
5. **Nexo** - Link/connection field
6. **Comprobación saldos** - Balance verification
7. **Cuenta Homologación** - Homologation account number
8. **Nombre Homologación** - Homologation account name

### Processing Steps (from requirements)

**Step 1: Data Cleanup**
1. Filter rows where "Cuenta (línea)" matches PA accounts from catalog
2. Create new columns (PA, Categoría, Subcategoría, etc.)
3. Rename columns: "Saldo" → "Valor COP", "Importes moneda extranjera" → "Valor USD"
4. Fill "Cuenta Homologación" and "Nombre Homologación" from catalog mapping
5. Validate: Sum of Débito = Sum of Crédito (Valor COP should sum to 0)
6. Validate: USD values - Débito positive, Crédito negative, sum to 0
7. Export cleaned file for review

**Step 2: Classification**
1. Verify all "Cuenta Homologación" values are non-zero
2. Apply classification rules based on:
   - Column E: Tipo de transacción
   - Column F: Tipo de comprobante
   - Column G: Número de documento
   - Columns A/B: Número línea, Nombre línea
   - Column C: Fecha
3. Fill Categoría, Subcategoría, Clasificación, Nexo columns
4. Export final classified file

## Architecture

### Two Menu Items (Role-Based Access)

1. **"Reglas Clasificación PA"** (Admin only)
   - Upload PA Account Catalog
   - Upload Classification Rules
   - View/manage current rules

2. **"Reporte PA"** (Finance users)
   - Upload NetSuite movements file
   - Step 1: Generate cleaned report (with download)
   - Step 2: Generate classified report (final output)

## Technical Implementation

### Frontend Components

#### New Files to Create:
```
frontend/src/pages/finance/
├── ReportePA.tsx                    # Main page (2 tabs: Process, History)
└── ReglasClasificacionPA.tsx        # Rules management page

frontend/src/components/forms/
├── FKPAFileUploader.tsx             # NetSuite file upload component
├── FKPARulesUploader.tsx            # Rules upload component
├── FKPACleanedResults.tsx           # Cleaned data preview/download
├── FKPAClassifiedResults.tsx        # Final classified results
└── FKPARulesViewer.tsx              # View current rules

frontend/src/services/
└── financeServicePA.ts              # PA-specific API calls

frontend/src/types/
└── financePA.ts                     # PA-specific TypeScript types
```

#### Page Structure (ReportePA.tsx):
```
Tabs:
├── Tab 0: "Procesar Reporte"
│   ├── Step 1: Upload NetSuite file
│   ├── Step 2: Review cleaned data (with validation stats)
│   ├── Download Cleaned File button
│   ├── Step 3: Apply classification
│   └── Download Classified File button
└── Tab 1: "Historial"
    └── Processing history table
```

### Backend Components

#### New Files to Create:
```
backend/src/adapter/rest/
└── pa_routes.py                     # PA-specific API routes

backend/src/core/servicios/
├── pa_classification_service.py     # Main classification logic
├── pa_rules_service.py              # Rules management
└── pa_cleanup_service.py            # Data cleanup logic

backend/src/interface/
└── pa_dtos.py                       # PA-specific DTOs

backend/src/repositorio/
└── pa_rules_repository.py           # Rules storage (Supabase)
```

#### Database Tables:
```sql
-- PA Classification Rules (stored in Supabase)
CREATE TABLE pa_account_catalog (
    id UUID PRIMARY KEY,
    cuenta_finkargo VARCHAR(50) NOT NULL,
    cuenta_homologacion VARCHAR(50) NOT NULL,
    nombre_homologacion VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pa_classification_rules (
    id UUID PRIMARY KEY,
    rule_type VARCHAR(50) NOT NULL,  -- 'categoria', 'subcategoria', 'clasificacion', 'nexo'
    tipo_transaccion VARCHAR(100),
    tipo_comprobante VARCHAR(100),
    condition_field VARCHAR(100),
    condition_value VARCHAR(255),
    result_value VARCHAR(255) NOT NULL,
    priority INT DEFAULT 0,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pa_processing_history (
    id UUID PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    total_rows INT,
    pa_rows INT,
    cleaned_file_url TEXT,
    classified_file_url TEXT,
    validation_stats JSONB,
    status VARCHAR(50),
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

```python
router = APIRouter(prefix="/api/finance/pa", tags=["Finance - Reporte PA"])

# Rules Management (Admin)
@router.post("/rules/catalog/upload")      # Upload PA account catalog
@router.get("/rules/catalog")              # Get current catalog
@router.post("/rules/classification/upload") # Upload classification rules
@router.get("/rules/classification")       # Get current rules

# Report Processing (Finance users)
@router.post("/process/upload")            # Upload NetSuite file, return session_id
@router.post("/process/{session_id}/clean") # Generate cleaned file
@router.get("/process/{session_id}/clean/download") # Download cleaned file
@router.post("/process/{session_id}/classify") # Apply classification rules
@router.get("/process/{session_id}/classify/download") # Download classified file
@router.get("/process/{session_id}/stats")  # Get processing stats

# History
@router.get("/history")                    # Get processing history
```

### Classification Rules Engine

```python
class PAClassificationEngine:
    """Engine to apply classification rules to PA records."""

    def __init__(self, rules: List[PAClassificationRule]):
        self.rules = self._organize_rules(rules)

    def classify_record(self, record: Dict) -> Dict:
        """Apply all rules to classify a single record."""
        result = {
            'categoria': None,
            'subcategoria': None,
            'clasificacion': None,
            'nexo': None
        }

        # Apply rules in priority order
        for rule_type in ['categoria', 'subcategoria', 'clasificacion', 'nexo']:
            result[rule_type] = self._apply_rules(record, rule_type)

        return result

    def _apply_rules(self, record: Dict, rule_type: str) -> str:
        """Apply rules of a specific type to find matching classification."""
        for rule in self.rules.get(rule_type, []):
            if self._rule_matches(record, rule):
                return rule.result_value
        return None

    def _rule_matches(self, record: Dict, rule: PAClassificationRule) -> bool:
        """Check if a rule matches the record."""
        # Match on tipo_transaccion, tipo_comprobante, and custom conditions
        if rule.tipo_transaccion and record.get('tipo_transaccion') != rule.tipo_transaccion:
            return False
        if rule.tipo_comprobante and record.get('tipo_comprobante') != rule.tipo_comprobante:
            return False
        if rule.condition_field and rule.condition_value:
            if record.get(rule.condition_field) != rule.condition_value:
                return False
        return True
```

## Classification Engine Algorithm

```python
class PAClassificationEngine:
    """
    Engine to classify PA records based on uploaded rules.
    """

    def classify_record(self, record: Dict, rules: PAAllRules) -> Dict:
        """
        Apply all classification rules to a single record.

        Args:
            record: Dict with source columns (A-Z)
            rules: PAAllRules containing all rule tables

        Returns:
            Dict with output columns (AA-AH)
        """
        cuenta_numero = record.get('cuenta_linea_numero')
        cuenta_nombre = record.get('cuenta_linea_nombre')
        tipo_transaccion = record.get('tipo_transaccion')
        tipo_comprobante = record.get('tipo_comprobante')
        numero_documento = record.get('numero_documento')
        fecha = record.get('fecha')

        # 1. Get homologation from account catalog
        catalog_entry = rules.get_catalog_entry(cuenta_numero)
        cuenta_homologacion = catalog_entry.cuenta_homologacion if catalog_entry else None
        nombre_homologacion = catalog_entry.nombre_homologacion if catalog_entry else None

        # 2. Find matching main classification rule
        main_rule = rules.find_classification_rule(
            tipo_transaccion, tipo_comprobante, numero_documento
        )

        categoria = main_rule.categoria if main_rule else None

        # 3. Determine subcategoria (with date logic if needed)
        if main_rule and main_rule.subcategoria_usa_fecha:
            subcategoria = self._apply_date_logic(fecha, main_rule.subcategoria_base)
        else:
            subcategoria = main_rule.subcategoria_base if main_rule else None

        # 4. Determine clasificacion (hierarchical check)
        clasificacion = self._determine_clasificacion(
            cuenta_nombre, categoria, rules, main_rule
        )

        # 5. Determine nexo from nexo rules
        nexo = rules.find_nexo(cuenta_nombre)
        if not nexo and main_rule and main_rule.nexo_fijo:
            nexo = main_rule.nexo_fijo

        # 6. Determine comprobacion_saldos
        comprobacion_saldos = self._determine_comprobacion_saldos(
            cuenta_numero, main_rule
        )

        # 7. Apply special homologation override (Acreedores Fiduciarios)
        if cuenta_homologacion == '3505' and categoria in ['Cesiones', 'Sustituciones', 'DisaumAporte']:
            cuenta_homologacion = '35051500101001'

        return {
            'pa': 'X',
            'categoria': categoria,
            'subcategoria': subcategoria,
            'clasificacion': clasificacion,
            'nexo': nexo,
            'comprobacion_saldos': comprobacion_saldos,
            'cuenta_homologacion': cuenta_homologacion,
            'nombre_homologacion': nombre_homologacion
        }

    def _apply_date_logic(self, fecha: date, base: str) -> str:
        """Apply date-based subcategoria logic."""
        is_first_day = fecha.day == 1
        if is_first_day:
            return "Reversión mes Ant." if base != "Recaudos en tránsito" else "Legalizacion Recaudos en Transito mes Ant."
        return "Del mes" if base != "Recaudos en tránsito" else "Recaudos en tránsito del mes"

    def _determine_clasificacion(self, cuenta_nombre, categoria, rules, main_rule) -> str:
        """Hierarchical clasificacion determination."""
        # Check account name keywords first
        if "No Realizada" in cuenta_nombre:
            return "No Realizada"
        if "Realizada" in cuenta_nombre:
            return "Realizada"

        # Check specific account rules
        clasificacion_rule = rules.find_clasificacion_cuenta_rule(cuenta_nombre, categoria)
        if clasificacion_rule:
            return clasificacion_rule.clasificacion

        # Fall back to main rule
        return main_rule.clasificacion_base if main_rule else None

    def _determine_comprobacion_saldos(self, cuenta_numero, main_rule) -> str:
        """Determine comprobacion_saldos value."""
        cartera_pa_accounts = ['13050530', '13050590', '13700530', '13809530', '13809531']
        if cuenta_numero in cartera_pa_accounts:
            return 'Cartera PA'
        return main_rule.comprobacion_saldos if main_rule else None
```

## Implementation Phases

### Phase 1: Database & DTOs (Backend Foundation)
**Files to create:**
- `backend/database/migration_pa_classification.sql` - Create all 4 PA tables + history
- `backend/src/interface/pa_dtos.py` - All DTOs (requests, responses, records)

**Migration includes:**
- `pa_account_catalog` - Account mapping
- `pa_classification_rules` - Main rules
- `pa_clasificacion_cuenta_rules` - Account name → classification
- `pa_nexo_rules` - Account name → nexo
- `pa_processing_history` - Audit trail

### Phase 2: Rules Management (Backend)
**Files to create:**
- `backend/src/repositorio/pa_rules_repository.py` - CRUD for all rule tables
- `backend/src/core/servicios/pa_rules_service.py` - Upload Excel, parse, store rules
- `backend/src/adapter/rest/pa_routes.py` - Rules endpoints

**Endpoints:**
```
POST /api/finance/pa/rules/catalog/upload     - Upload account catalog Excel
GET  /api/finance/pa/rules/catalog            - Get current catalog
POST /api/finance/pa/rules/classification/upload - Upload classification rules Excel
GET  /api/finance/pa/rules/classification     - Get current rules
POST /api/finance/pa/rules/nexo/upload        - Upload nexo rules Excel
GET  /api/finance/pa/rules/nexo               - Get nexo rules
```

### Phase 3: Report Processing (Backend)
**Files to create:**
- `backend/src/core/servicios/pa_cleanup_service.py` - Step 1: Filter & clean
- `backend/src/core/servicios/pa_classification_engine.py` - Classification logic
- `backend/src/core/servicios/pa_report_service.py` - Orchestrates full flow

**Processing endpoints:**
```
POST /api/finance/pa/process/upload           - Upload NetSuite file, return session_id
GET  /api/finance/pa/process/{id}/clean       - Get cleaned data preview
GET  /api/finance/pa/process/{id}/clean/download - Download cleaned Excel
POST /api/finance/pa/process/{id}/classify    - Run classification
GET  /api/finance/pa/process/{id}/classify/download - Download classified Excel
GET  /api/finance/pa/process/{id}/stats       - Get validation stats
```

### Phase 4: Frontend - Types & Services
**Files to create:**
- `frontend/src/types/financePA.ts` - TypeScript interfaces
- `frontend/src/services/financeServicePA.ts` - API client functions

### Phase 5: Frontend - Rules Management Page
**Files to create:**
- `frontend/src/components/forms/FKPARulesUploader.tsx` - Multi-file rule uploader
- `frontend/src/components/forms/FKPARulesViewer.tsx` - View current rules
- `frontend/src/pages/finance/ReglasClasificacionPA.tsx` - Rules admin page

### Phase 6: Frontend - Report Processing Page
**Files to create:**
- `frontend/src/components/forms/FKPAFileUploader.tsx` - NetSuite file uploader
- `frontend/src/components/forms/FKPACleanedResults.tsx` - Step 1 results display
- `frontend/src/components/forms/FKPAClassifiedResults.tsx` - Step 2 results display
- `frontend/src/pages/finance/ReportePA.tsx` - Main processing page

### Phase 7: Integration & Routing
**Files to modify:**
- `frontend/src/App.tsx` - Add routes
- `frontend/src/components/ui/FKSidebar.tsx` - Add menu items
- `frontend/src/types/index.ts` - Add FINANCE_ADMIN role
- `backend/main.py` - Register pa_routes router
- `backend/database/migration_add_finance_admin_role.sql` - New role

## Key Files to Modify

### Frontend
- `frontend/src/App.tsx` - Add new routes
- `frontend/src/components/ui/FKSidebar.tsx` - Add menu items
- `frontend/src/types/index.ts` - Add new role if needed

### Backend
- `backend/main.py` - Register new router
- `backend/src/adapter/rest/__init__.py` - Export new router

## Validation Requirements

1. **Balance Validation (Cleanup)**:
   - Sum of Débito column = Sum of Crédito column
   - Valor COP sums to 0
   - Valor USD sums to 0 (when filtered by USD currency)

2. **Classification Validation**:
   - All records must have Cuenta Homologación != 0
   - Warn on unclassified records

## Design Decisions (User Confirmed)

1. **Rules Storage**: Supabase Database
   - Rules are parsed from uploaded Excel files and stored as database records
   - Enables querying, versioning, and validation
   - Original Excel kept for reference

2. **Access Control**: New FINANCE_ADMIN role
   - FINANCE_ADMIN: Can upload/modify classification rules
   - FINANCE: Can only process reports (upload movements, generate reports)
   - ADMIN: Full access to both

3. **Re-classification**: No, always fresh processing
   - Each upload is independent
   - To re-classify, user must upload the source file again
   - No need to store source files long-term

4. **Processing Flow**: Two-step with review
   - Step 1: Upload NetSuite file → Clean & Filter PA accounts → Download cleaned file for review
   - Step 2: Click "Classify" → Apply rules → Download final classified file
   - Allows validation of balances between steps

## New User Role

Add new role `FINANCE_ADMIN` to the UserRole enum:

```typescript
// frontend/src/types/index.ts
export enum UserRole {
  // ... existing roles
  FINANCE_ADMIN = 'finance_admin',  // NEW: Can manage PA classification rules
}
```

```sql
-- Database migration
-- Add finance_admin to allowed roles
```

## Complete Rules Structure (Analyzed from CSV files)

### Source File Columns (NetSuite - Columns A-Z)
```
A: Cuenta (línea): Número       - Account number (key for PA filtering)
B: Cuenta (línea): Nombre       - Account name (used for classification rules)
C: Fecha                        - Date (used for subcategory logic)
D: Fecha de creación            - Creation date
E: Tipo de Transacción          - Transaction type (key for rules)
F: Tipo de comprobante          - Document type (key for rules)
G: Número de documento          - Document number (pattern matching)
H-N: Various columns            - Entity, notes, etc.
O: Débito                       - Debit amount
P: Crédito                      - Credit amount
Q: Saldo                        - Balance (rename to "Valor COP")
R: Código de Desembolso
S: Moneda: Nombre               - Currency name
T: Tipo de cambio               - Exchange rate
U: Importe (moneda extranjera)  - Foreign amount (rename to "Valor USD")
V-Z: Additional columns
```

### Output Columns to Add (AA-AH)
```
AA: PA                    - Always "X" for PA accounts
AB: Categoria             - From main classification rules
AC: Subcategoría          - From rules + date logic
AD: Clasificación         - Realizada/No Realizada/Recaudo rules
AE: Nexo                  - From nexo mapping rules
AF: Comprobación saldos   - "Cartera PA" for specific accounts
AG: Cuenta Homologación   - From account catalog mapping
AH: Nombre Homologación   - From account catalog mapping
```

### Rule Type 1: Account Catalog (PA Account Filter + Homologation)
**Table: `pa_account_catalog`**
```sql
CREATE TABLE pa_account_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cuenta_finkargo VARCHAR(20) NOT NULL UNIQUE,  -- e.g., "11100530"
    cuenta_auxiliar VARCHAR(255),                  -- Full account name
    cuenta_homologacion VARCHAR(20) NOT NULL,      -- e.g., "13020500101001"
    nombre_homologacion VARCHAR(255) NOT NULL,     -- e.g., "ENCARGO Cta #1250001972"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```
**Usage:**
1. Filter source data: Keep only rows where `Cuenta (línea): Número` exists in `cuenta_finkargo`
2. Map columns AG/AH from matching catalog entry

### Rule Type 2: Main Classification Rules (Categoria + Subcategoria base)
**Table: `pa_classification_rules`**
```sql
CREATE TABLE pa_classification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_transaccion VARCHAR(100),        -- "Asiento", "Factura de venta", etc.
    tipo_comprobante VARCHAR(100),        -- "Ajustes Contables", "Provisión Ingresos"
    numero_documento_patron VARCHAR(50),  -- Pattern like "GBA", "PPR", "TBA" or NULL
    categoria VARCHAR(100) NOT NULL,      -- Output: "Ajuste Cartera", "Provisión Ingresos"
    subcategoria_base VARCHAR(100),       -- Base value or rule indicator
    subcategoria_usa_fecha BOOLEAN DEFAULT FALSE,  -- If true, apply date logic
    clasificacion_base VARCHAR(100),      -- Base classification or NULL
    clasificacion_usa_cuenta BOOLEAN DEFAULT FALSE, -- If true, check account name
    nexo_fijo VARCHAR(10),               -- Fixed nexo value if applicable
    comprobacion_saldos VARCHAR(50),     -- "Cartera PA" for specific rules
    observacion TEXT,                     -- Notes/comments
    prioridad INT DEFAULT 0,              -- Higher = evaluated first
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Sample Rules (from CSV):**
| tipo_transaccion | tipo_comprobante | categoria | subcategoria_base | subcategoria_usa_fecha |
|-----------------|------------------|-----------|-------------------|------------------------|
| Asiento | Provisión Ingresos | Provisión Ingresos | - | false |
| Asiento | Ajustes Contables | Ajuste Cartera | | false |
| Asiento | Ajuste Cartera | Ajuste Cartera | | false |
| Asiento | Deterioro PA | Deterioro | Del mes | false |
| Revaluación de moneda | | Diferencia en cambio | | true |
| Factura de venta | | Facturación | Factura de Venta | false |
| Asiento | Recaudo en Tránsito | Recaudo | * | true |
| Asiento | Pago Cliente | Recaudo | Cartera | false |

### Rule Type 3: Clasificación by Account Name (Realizada/No Realizada/Recaudo)
**Table: `pa_clasificacion_cuenta_rules`**
```sql
CREATE TABLE pa_clasificacion_cuenta_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    categoria_aplicable VARCHAR(100),     -- "Diferencia en cambio" or NULL for all
    cuenta_nombre_patron VARCHAR(255) NOT NULL,  -- Account name to match
    clasificacion VARCHAR(100) NOT NULL,  -- "Realizada", "No Realizada", "Recaudo Dolares", "Recaudo en Pesos"
    comentario TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Sample Rules:**
| categoria_aplicable | cuenta_nombre_patron | clasificacion |
|--------------------|---------------------|---------------|
| Diferencia en cambio | 53052520-Diferencia en cambio No Realizada | No Realizada |
| Diferencia en cambio | 42102016-Diferencia en cambio No Realizada | No Realizada |
| Diferencia en cambio | 53052517-Diferencia en cambio Realizada | Realizada |
| NULL | 11101030-Cuenta Compensación # 36449096 | Recaudo Dolares |
| NULL | 11100530-Cta Cte #1250001972 CITI | Recaudo en Pesos |

### Rule Type 4: Nexo Mapping Rules
**Table: `pa_nexo_rules`**
```sql
CREATE TABLE pa_nexo_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cuenta_nombre_patron VARCHAR(255) NOT NULL,  -- Account name to match
    nexo VARCHAR(10) NOT NULL,            -- "1", "2", "3", "4", "13"
    comentario TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Sample Rules:**
| cuenta_nombre_patron | nexo |
|---------------------|------|
| 53052519-Diferencia en cambio Realizada (Otros Act. | 1 |
| 42102019-Diferencia en cambio Realizada(Otros Activ | 1 |
| 53052521-Diferencia en cambio Realizada (Pasivos Ext | 2 |
| 42102016-Diferencia en cambio No Realizada(1305 | 3 |
| 53052522-Diferencia en cambio No Realizada (Pasivos | 4 |

### Special Business Rules (Hardcoded Logic)

1. **Subcategoría Date Logic:**
   - If `subcategoria_usa_fecha = true`:
     - `Fecha` is 1st day of month → "Reversión mes Ant." or "Legalizacion Recaudos en Transito mes Ant."
     - `Fecha` is NOT 1st day → "Del mes" or "Recaudos en tránsito del mes"

2. **Comprobación Saldos = "Cartera PA":**
   - Apply when `Cuenta (línea): Número` is one of: 13050530, 13050590, 13700530, 13809530, 13809531

3. **Special Cuenta Homologación for Acreedores Fiduciarios:**
   - If homologacion from catalog = "3505" AND clasificación is "Cesiones", "Sustituciones", or "DisaumAporte"
   - Then override to: cuenta_homologacion = "35051500101001"

4. **Clasificación Hierarchy:**
   - First check: Account name contains "No Realizada" or "Realizada"
   - Then check: Specific account rules (Recaudo Dolares/Pesos)
   - Finally: Category-based default

---

*This plan follows the existing Finance module patterns from ReporteriaAutomaticaCO/MX*
