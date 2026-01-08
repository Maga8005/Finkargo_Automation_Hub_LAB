# Feature Prompt: Exchange Declaration to Historial de Pagos Matching

## Overview

Implement a Treasury module feature that automatically matches Exchange Declarations (Declaraciones de Cambio) from a local folder structure to Historial de Pagos (Payment History) records. The matching uses fuzzy customer name matching, date tolerance (±7 days), and amount tolerance (±$2.00) to handle one-to-many payment-to-operation mappings.

## Current State

1. **Existing Directory Scanner**: The `feature-declarations-mapping` branch has a LocalDirectoryScanner that:
   - Scans the 3-level folder structure: Customer > Date > Amount > PDF
   - Extracts metadata from folder names (date, amount)
   - Optionally extracts declaration numbers from PDF content
   - Generates an inventory Excel file

2. **Existing Treasury Module**: The `/api/tesoreria` routes handle Historial de Pagos validation and NetSuite conversion

3. **Existing Components**:
   - `FKHistorialUploader.tsx` - File upload with drag & drop
   - `batch_processor_service.py` - Pipeline orchestration pattern
   - `customer_name_normalizer.py` - Name normalization logic
   - `folder_name_parser.py` - Date/amount parsing utilities

## Desired State

A complete workflow where:
1. User scans the declarations folder to create inventory (existing)
2. User uploads Historial de Pagos Excel file
3. System groups Historial rows by (customer, date) and sums capital
4. System matches payment groups to declarations with tolerance
5. User reviews matches, manually resolves conflicts
6. User downloads enriched Excel with "Declaracion de Cambio Numero" and "DC Nombre" columns populated

## Backend Requirements

### Services

1. **HistorialParserService** (`backend/src/core/servicios/treasury/historial_parser_service.py`):
   - Parse Historial de Pagos Excel (based on actual file structure)
   - Map column names: Cliente, Identificacion del cliente, Codigo de desembolso, Fecha de pago, Capital, etc.
   - Handle encoding issues (accented characters in column names)
   - Validate required columns (Cliente, Fecha de pago, Capital)
   - Extract and normalize dates (YYYY-MM-DD format from pandas)
   - Return list of HistorialRecord DTOs

2. **PaymentGroupAggregator** (`backend/src/core/servicios/treasury/payment_group_aggregator.py`):
   - Group HistorialRecords by (cliente_normalized, fecha_pago)
   - Sum Capital amounts per group
   - Track original row numbers for assignment
   - Return list of PaymentGroup DTOs

3. **DeclarationPaymentMatcher** (`backend/src/core/servicios/treasury/declaration_payment_matcher.py`):
   - Take inventory items and payment groups as input
   - Apply fuzzy customer matching (fuzz.ratio >= 85)
   - Apply date tolerance (configurable, default ±7 days)
   - Apply amount tolerance (configurable, default ±$2.00)
   - Calculate match confidence score (0-100)
   - Return MatchResult list with status: matched/partial/unmatched/conflict

4. **EnrichedExcelGenerator** (`backend/src/core/servicios/treasury/enriched_excel_generator.py`):
   - Take original Historial data and match results
   - Populate existing columns: "Declaracion de Cambio Numero", "DC Nombre"
   - Apply styling (Finkargo colors)
   - Create summary sheet with match statistics
   - Create unmatched records sheet

### Endpoints

Add to new file `backend/src/adapter/rest/treasury_matching_routes.py`:

```python
POST /api/treasury/declarations/match/upload-historial
# Upload Historial de Pagos Excel, returns parsed data + groups

POST /api/treasury/declarations/match/execute
# Body: { inventory_path: str, date_tolerance_days: int, amount_tolerance: float }
# Execute matching, returns MatchResult list

GET /api/treasury/declarations/match/results/{session_id}
# Get cached match results

POST /api/treasury/declarations/match/override
# Body: { payment_group_id: str, declaration_id: str }
# Manual override for a match

GET /api/treasury/declarations/match/download/{session_id}
# Download enriched Excel file
```

### DTOs

Add to `backend/src/interface/treasury_matching_dtos.py`:

```python
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import date
from decimal import Decimal

class HistorialRecord(BaseModel):
    """Based on actual Historial de Pagos Excel structure (Diveco example)"""
    row_number: int
    cliente: str                           # "DIVECO SAS"
    cliente_normalized: str                # "DIVECO"
    identificacion_cliente: str            # "900799652"
    codigo_desembolso: str                 # "CO:900799652:1:3:PR01"
    codigo_recaudo: Optional[str]          # "CO:900799652:1:5:PR01:3:REC"
    numero_factura: Optional[str]          # "0"
    fecha_desembolso: date                 # "2023-11-20"
    fecha_vencimiento: date                # "2024-04-18"
    valor_desembolso: Decimal              # 21084.00
    estado_desembolso: str                 # "Recaudado"
    fecha_pago: date                       # KEY: "2024-01-22"
    total_pagado: Decimal                  # 45132640.00
    moneda: str                            # "COP" or "USD"
    medio_pago: str                        # "Manual" or "Pago en linea"
    tasa_cambio: Optional[Decimal]         # 3958.0000
    total_pagado_usd: Decimal              # 11402.89
    capital: Decimal                       # KEY: 10036.610
    declaracion_cambio_numero: Optional[str]  # OUTPUT: "28756"
    dc_nombre: Optional[str]               # OUTPUT: "DC 8.111,43.pdf"

class PaymentGroup(BaseModel):
    group_id: str
    customer_name: str
    customer_normalized: str
    payment_date: date
    total_capital: Decimal
    record_count: int
    record_row_numbers: List[int]

class DeclarationItem(BaseModel):
    declaration_id: str
    customer_name: str                     # From folder: "Diveco SAS"
    customer_normalized: str               # "DIVECO"
    declaration_date: date                 # From folder: "26-03-2025" or "20250326"
    amount: Decimal                        # From folder: "8.111,43" -> 8111.43
    declaration_number: Optional[str]      # From PDF: "28756"
    pdf_file_name: str                     # "DC 8.111,43.pdf"
    pdf_file_path: str                     # Full path

class MatchConfig(BaseModel):
    date_tolerance_days: int = 7
    amount_tolerance: Decimal = Decimal("2.00")
    customer_match_threshold: int = 85  # fuzz.ratio minimum

class MatchResult(BaseModel):
    payment_group: PaymentGroup
    matched_declaration: Optional[DeclarationItem]
    match_status: Literal['matched', 'partial', 'unmatched', 'conflict']
    match_confidence: float  # 0.0 to 1.0
    date_difference_days: Optional[int]
    amount_difference: Optional[Decimal]

class HistorialUploadResponse(BaseModel):
    success: bool
    session_id: str
    total_rows: int
    group_count: int
    groups: List[PaymentGroup]
    column_status: List[dict]  # Column validation status
    errors: List[dict]
```

## Frontend Requirements

### Pages

1. **HistorialMatchingPage** (`frontend/src/pages/treasury/HistorialMatchingPage.tsx`):
   - MUI Stepper with 4 steps:
     1. Upload Historial de Pagos
     2. Configure Matching Parameters
     3. Review Match Results
     4. Download Output
   - Uses react-hook-form for configuration
   - Shows progress indicators during processing

### Components

1. **FKHistorialMatchingUploader** (`frontend/src/components/treasury/FKHistorialMatchingUploader.tsx`):
   - Extends pattern from FKHistorialUploader
   - Shows column validation status (maps actual columns like "Fecha de pago", "Capital")
   - Shows parsed data preview (first 10 rows)
   - Shows grouping statistics

2. **FKMatchingConfigForm** (`frontend/src/components/treasury/FKMatchingConfigForm.tsx`):
   - Date tolerance slider (1-14 days, default: 7)
   - Amount tolerance slider ($0.50-$5.00, step: $0.50, default: $2.00)
   - Customer match strictness radio (Exact/Fuzzy)
   - "Use inventory from last scan" checkbox

3. **FKMatchResultsTable** (`frontend/src/components/treasury/FKMatchResultsTable.tsx`):
   - MUI DataGrid with match results
   - Status chip (green/yellow/red for matched/partial/unmatched)
   - Confidence percentage column
   - Expandable row to see grouped records
   - Filter by status
   - Sort by confidence/date/amount

4. **FKManualMatchDialog** (`frontend/src/components/treasury/FKManualMatchDialog.tsx`):
   - Modal dialog for manual matching
   - Shows unmatched payment group details
   - Dropdown of available declarations
   - Confirmation button

5. **FKMatchStatisticsCard** (`frontend/src/components/treasury/FKMatchStatisticsCard.tsx`):
   - Summary statistics: total groups, matched, partial, unmatched
   - Match rate percentage
   - Average confidence score

### Services

Add to `frontend/src/services/treasuryMatchingService.ts`:

```typescript
interface TreasuryMatchingService {
  uploadHistorial(file: File): Promise<HistorialUploadResponse>;
  executeMatching(config: MatchConfig): Promise<MatchResult[]>;
  getResults(sessionId: string): Promise<MatchResult[]>;
  overrideMatch(groupId: string, declarationId: string): Promise<void>;
  downloadEnrichedExcel(sessionId: string): Promise<Blob>;
}
```

### Types

Add to `frontend/src/types/treasuryMatching.ts`:

```typescript
/**
 * Based on actual Historial de Pagos Excel structure (Diveco example)
 */
interface HistorialRecord {
  rowNumber: number;
  cliente: string;                    // "DIVECO SAS"
  clienteNormalized: string;          // "DIVECO"
  identificacionCliente: string;      // "900799652"
  codigoDesembolso: string;           // "CO:900799652:1:3:PR01"
  codigoRecaudo?: string;
  numeroFactura?: string;
  fechaDesembolso: string;            // ISO date
  fechaVencimiento: string;           // ISO date
  valorDesembolso: number;            // 21084.00
  estadoDesembolso: string;           // "Recaudado"
  fechaPago: string;                  // KEY: ISO date
  totalPagado: number;
  moneda: string;                     // "COP" or "USD"
  medioPago: string;                  // "Manual" or "Pago en linea"
  tasaCambio?: number;
  totalPagadoUsd: number;
  capital: number;                    // KEY: 10036.610
  declaracionCambioNumero?: string;   // OUTPUT: "28756"
  dcNombre?: string;                  // OUTPUT: "DC 8.111,43.pdf"
}

interface PaymentGroup {
  groupId: string;
  customerName: string;
  customerNormalized: string;
  paymentDate: string;                // ISO date
  totalCapital: number;
  recordCount: number;
  recordRowNumbers: number[];
}

interface DeclarationItem {
  declarationId: string;
  customerName: string;               // From folder: "Diveco SAS"
  declarationDate: string;            // ISO date from folder
  amount: number;                     // 8111.43 (parsed from "8.111,43")
  declarationNumber?: string;         // From PDF: "28756"
  pdfFileName: string;                // "DC 8.111,43.pdf"
  pdfFilePath: string;
}

interface MatchResult {
  paymentGroup: PaymentGroup;
  matchedDeclaration?: DeclarationItem;
  matchStatus: 'matched' | 'partial' | 'unmatched' | 'conflict';
  matchConfidence: number;            // 0-1
  dateDifferenceDays?: number;
  amountDifference?: number;
}

interface MatchConfig {
  dateToleranceDays: number;          // Default: 7
  amountTolerance: number;            // Default: 2.00
  customerMatchThreshold: number;     // Default: 85
}

interface HistorialUploadResponse {
  success: boolean;
  sessionId: string;
  totalRows: number;
  groupCount: number;
  groups: PaymentGroup[];
  columnStatus: ColumnValidationStatus[];
  errors: ValidationError[];
}

interface ColumnValidationStatus {
  columnName: string;
  found: boolean;
  sourceColumn?: string;
}
```

## Files to Create/Modify

### Backend (Create)

1. `backend/src/core/servicios/treasury/__init__.py`
   - Module init file

2. `backend/src/core/servicios/treasury/historial_parser_service.py`
   - HistorialParserService class
   - Column mapping for actual Excel structure
   - Handle encoding (accented characters)

3. `backend/src/core/servicios/treasury/payment_group_aggregator.py`
   - PaymentGroupAggregator class
   - Grouping by (cliente_normalized, fecha_pago)

4. `backend/src/core/servicios/treasury/declaration_payment_matcher.py`
   - DeclarationPaymentMatcher class
   - Match scoring algorithm
   - Tolerance-based matching

5. `backend/src/core/servicios/treasury/enriched_excel_generator.py`
   - EnrichedExcelGenerator class
   - Populate "Declaracion de Cambio Numero" and "DC Nombre" columns

6. `backend/src/adapter/rest/treasury_matching_routes.py`
   - New router with matching endpoints

7. `backend/src/interface/treasury_matching_dtos.py`
   - All matching-related DTOs

### Backend (Modify)

1. `backend/main.py`
   - Add treasury_matching_routes router

2. `backend/requirements.txt`
   - Add: rapidfuzz (or fuzzywuzzy + python-Levenshtein)

### Frontend (Create)

1. `frontend/src/pages/treasury/HistorialMatchingPage.tsx`
   - Main matching workflow page

2. `frontend/src/components/treasury/FKHistorialMatchingUploader.tsx`
   - File upload component

3. `frontend/src/components/treasury/FKMatchingConfigForm.tsx`
   - Configuration form

4. `frontend/src/components/treasury/FKMatchResultsTable.tsx`
   - Results data grid

5. `frontend/src/components/treasury/FKManualMatchDialog.tsx`
   - Manual override modal

6. `frontend/src/components/treasury/FKMatchStatisticsCard.tsx`
   - Summary statistics

7. `frontend/src/services/treasuryMatchingService.ts`
   - API client service

8. `frontend/src/types/treasuryMatching.ts`
   - TypeScript types

### Frontend (Modify)

1. `frontend/src/App.tsx`
   - Add route for /treasury/declaration-matching

2. `frontend/src/components/ui/FKSidebar.tsx`
   - Add Treasury > Declaration Matching menu item (if not exists)

## Reference Files

### Sample Historial de Pagos
`Example FIles for Reqs/20251215 HISTORICO DE PAGOS DIVECO.xlsx`

**Actual Columns (20 columns):**
1. Cliente
2. Identificacion del cliente
3. Codigo de desembolso
4. Codigo de recaudo
5. Numero de factura
6. Fecha de desembolso
7. Fecha de vencimiento
8. Valor del desembolso
9. Estado del desembolso
10. Fecha de pago (KEY)
11. Total pagado
12. Moneda
13. Medio de pago
14. Tasa de cambio de FK/en linea
15. Total pagado [USD]
16. Capital (KEY)
17. Declaracion de Cambio Numero (OUTPUT)
18. DC Nombre (OUTPUT)
19. DIM
20. Factura Final

### Sample Declaration Folder Structure

**Production (FINKARGO DCS) - DD-MM-YYYY format:**
```
Exchange Declarations and Legalization Process/FINKARGO DCS/
├── Diveco SAS/
│   ├── 26-03-2025/
│   │   └── 8.111,43/
│   │       └── DC 8.111,43.pdf
│   ├── 04-04-2025/
│   │   └── 4.776,52/
│   │       └── DC 4.776,52.pdf
│   └── ...
├── LONA GROUP SAS/
│   └── ...
└── (170+ customer folders)
```

**Alternative (Example Files) - YYYYMMDD format:**
```
Example FIles for Reqs/Diveco SAS/
├── 20250326/
│   └── 8.111,43/
│       └── DC 8.111,43.pdf
├── 20250404/
│   └── 4.776,52/
│       └── DC 4.776,52.pdf
└── ...
```

### Sample PDF Content (Declaration Number Extraction)

From `DC 8.111,43.pdf`:
```
Formulario No. 1
Declaración de Cambio por Importaciones de Bienes

II. IDENTIFICACIÓN DE LA DECLARACIÓN
2. Nit del I.M.C.  3. Fecha AAAA-MM-DD  4. Número
860051135          2025-03-26          28756
```

**Regex for extraction:**
```python
r'4\.\s*N[úu]mero\s*[\n\r\s]*(\d+)'  # Extracts "28756"
```

## Acceptance Criteria

1. [ ] User can upload Historial de Pagos Excel and see validation results
2. [ ] System correctly identifies all 20 columns from actual file
3. [ ] System groups rows by (cliente, fecha_pago) and sums Capital
4. [ ] User can configure date tolerance (1-14 days) via slider
5. [ ] User can configure amount tolerance ($0.50-$5.00) via slider
6. [ ] Matching finds correct declarations within tolerance
7. [ ] Results show match status with confidence scores
8. [ ] User can manually override/assign matches
9. [ ] Downloaded Excel has "Declaracion de Cambio Numero" and "DC Nombre" columns populated
10. [ ] Match rate exceeds 85% on Diveco test data

## Technical Notes

### Reuse from feature-declarations-mapping branch

1. **LocalDirectoryScanner**: Use inventory from existing scan
2. **folder_name_parser.py**: Reuse `parse_date_from_folder_name()` - extend for YYYYMMDD format
3. **customer_name_normalizer.py**: Reuse normalization logic
4. **LocalPDFExtractor**: Reuse declaration number extraction patterns

### Colombian Format Considerations

1. **Dates in folders**:
   - DD-MM-YYYY (e.g., "26-03-2025") - Primary format in FINKARGO DCS
   - YYYYMMDD (e.g., "20250326") - Alternative format in example files
2. **Amounts**: European format with periods for thousands, commas for decimals (e.g., "8.111,43")
3. **Declaration numbers**: Simple numeric (e.g., "28756")

### Matching Algorithm Priority

1. **Customer name match first** (filter to candidates)
2. **Date proximity** (within tolerance)
3. **Amount proximity** (within tolerance)
4. **Confidence scoring** combines all three

### Error Handling

1. Log all matching operations
2. Never fail silently - always surface errors to UI
3. Allow partial success (some matches, some unmatched)
4. Provide detailed error messages in Spanish

### Column Name Mapping (Handle Variations)

```python
COLUMN_MAPPINGS = {
    'cliente': ['Cliente', 'CLIENTE', 'client', 'Cliente (Razón Social)'],
    'fecha_pago': ['Fecha de pago', 'Fecha Pago', 'FechaPago', 'Fecha Aplicacion'],
    'capital': ['Capital', 'CAPITAL', 'Monto Capital'],
    'identificacion_cliente': ['Identificacion del cliente', 'NIT', 'Identificación'],
    'declaracion_cambio_numero': ['Declaracion de Cambio Numero', 'Declaración de Cambio Número', 'DC Numero'],
    'dc_nombre': ['DC Nombre', 'Nombre DC', 'PDF Nombre'],
}
```

---

*Prompt Generated: 2025-12-15*
*Version: 1.1*
*For use with /feature command*
