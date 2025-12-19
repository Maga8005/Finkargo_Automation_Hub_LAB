# PRD: Broker Contract Incentive Extraction

**Document Version:** 1.0
**Date:** 2024-12-16
**Department:** Alianzas (Alliances)
**Status:** Draft

---

## 1. Overview

### 1.1 Problem Statement
The Alianzas department needs to extract and consolidate economic incentive information from multiple broker contracts stored in a local directory structure. Currently, this information is manually reviewed from PDFs, which is time-consuming and error-prone.

### 1.2 Proposed Solution
Build a directory scanning and PDF extraction feature (similar to "Escaneo Directorio Local" in Tesoreria) that:
- Scans a directory containing broker folders
- Extracts incentive percentages from PDF contracts
- Identifies broker name and RFC from signature sections
- Outputs consolidated data to an Excel file

### 1.3 Business Value
- Reduce manual review time for broker contracts
- Centralize broker incentive data for easy reference
- Improve accuracy of incentive tracking
- Support compliance and auditing needs

---

## 2. Functional Requirements

### 2.1 Directory Structure Expected

```
2024/
├── 20240505 Sed Heretiz/
│   ├── contract.pdf
│   └── other_files...
├── 20240119 Simply Capital SAS/
│   ├── contract.pdf
│   └── other_files...
├── 20240227 Rodrigo Martinez/
│   ├── contract.pdf
│   └── other_files...
└── ...
```

**Folder Naming Convention:** `YYYYMMDD Broker Name` (8-digit date without dashes, followed by broker name).

### 2.2 Contract Types to Process

#### Type 1: "Bono" Contracts
- Located in **Anexo A** (Annex A)
- Section titled: "Especificación del Bono"
- Contains two incentive patterns:

| Incentive Type | Pattern to Match |
|----------------|------------------|
| Credit Line Bonus | "un bono equivalente al **X%** del monto colocado a/o cliente por concepto de bono de apertura" |
| Operations Bonus | "un bono equivalente al **X%**..." (different context, for eligible operations) |

#### Type 2: "Incentivos" Contracts (Older Style)
- Located in **Artículo 3** (Article 3)
- Pattern to match:
  - "Finkargo reconocerá un incentivo de **X%** sobre el monto de operaciones en el alta por cada nuevo cliente"

### 2.3 Data Extraction Requirements

| Field | Source | Notes |
|-------|--------|-------|
| Broker Name | Folder name | Extract from folder naming convention |
| RFC | Signature section | Below broker signature; may be absent |
| Signatory Name | Signature section | Name above/below signature line |
| Credit Line Incentive % | Contract body | From "bono de apertura" clause |
| Operations Incentive % | Contract body | From eligible operations clause |
| Contract Type | Contract body | "Bono" or "Incentivos" style |
| Contract Date | Folder name / Contract | From YYYYMMDD folder prefix or contract content |

### 2.4 Output Format (Excel)

**Columns:**
| Column | Description |
|--------|-------------|
| Broker Name | Name extracted from folder |
| RFC | Tax ID from signature section |
| Signatory Name | Name from signature section |
| Credit Line Incentive (%) | Percentage for credit line bonus |
| Operations Incentive (%) | Percentage for operations bonus |
| Contract Type | "Bono" or "Incentivos" |
| Source File | Path to the PDF processed |
| Extraction Date | Timestamp of extraction |
| Notes | Any warnings or partial extractions |

---

## 3. User Interface Requirements

### 3.1 Menu Location
- **Department:** Alianzas
- **Menu Item:** "Extracción Incentivos Brokers" (or similar)
- **Note:** Separate from Tesoreria's "Escaneo Directorio Local"

### 3.2 UI Components

#### 3.2.1 Directory Selection
- Directory path input field
- Browse button for folder selection
- Validation: Directory must exist and contain subfolders

#### 3.2.2 Scan Configuration
- Checkbox: Include subfolders recursively
- File type filter: PDF only (default)
- Preview of folders to be scanned (count)

#### 3.2.3 Progress Display
- Progress bar showing folders processed
- Current folder being processed
- Real-time log of extractions

#### 3.2.4 Results View
- Data grid showing extracted data
- Columns sortable and filterable
- Highlight rows with missing data (e.g., no RFC found)
- Export button for Excel download

### 3.3 Wireframe (Conceptual)

```
┌─────────────────────────────────────────────────────────────┐
│  Extracción Incentivos Brokers                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Directorio: [________________________] [Examinar...]       │
│                                                             │
│  ☑ Incluir subcarpetas                                      │
│                                                             │
│  Carpetas encontradas: 45                                   │
│                                                             │
│  [Iniciar Escaneo]                                          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Progreso: ████████████░░░░░░░░ 60% (27/45)                │
│  Procesando: 20240505 Sed Heretiz                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  │ Broker      │ RFC        │ Línea % │ Ops %  │ Tipo     │ │
│  ├─────────────┼────────────┼─────────┼────────┼──────────┤ │
│  │ Simply Cap  │ RFC123456  │ 0.80%   │ 0.07%  │ Bono     │ │
│  │ R. Martinez │ -          │ 0.75%   │ 0.05%  │ Incentiv │ │
│  │ ...         │ ...        │ ...     │ ...    │ ...      │ │
│                                                             │
│  [Exportar Excel]                         Total: 27 brokers │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Technical Requirements

### 4.1 Backend Services

#### 4.1.1 Directory Scanner Service
```python
# Location: backend/src/core/servicios/broker_contract_scanner.py

class BrokerContractScanner:
    def scan_directory(self, path: str) -> List[BrokerFolder]
    def find_contract_pdf(self, folder: BrokerFolder) -> Optional[str]
    def extract_broker_name(self, folder_name: str) -> str
```

#### 4.1.2 PDF Extraction Service
```python
# Location: backend/src/core/servicios/broker_incentive_extractor.py

class BrokerIncentiveExtractor:
    def extract_from_pdf(self, pdf_path: str) -> BrokerIncentiveData
    def identify_contract_type(self, text: str) -> ContractType
    def extract_credit_line_incentive(self, text: str) -> Optional[float]
    def extract_operations_incentive(self, text: str) -> Optional[float]
    def extract_signatory_info(self, text: str) -> SignatoryInfo
```

#### 4.1.3 Regex Patterns Required

```python
# Bono Contract - Credit Line
BONO_CREDIT_LINE_PATTERN = r"un bono (?:equivalente|que equivale) al?\s*([\d.,]+)\s*%?\s*(?:por ?ciento)?\s*del monto (?:colocado|a cliente).*bono de apertura"

# Bono Contract - Operations
BONO_OPERATIONS_PATTERN = r"un bono (?:equivalente|que equivale) al?\s*([\d.,]+)\s*%?\s*(?:por ?ciento)?.*operaciones elegibles"

# Incentivos Contract
INCENTIVOS_PATTERN = r"(?:Finkargo|finkargo)\s*reconocer[áa]\s*(?:un\s*)?incentivo\s*(?:de\s*)?([\d.,]+)\s*%"

# RFC Pattern
RFC_PATTERN = r"RFC[:\s]*([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})"

# Signatory Name (below signature line)
SIGNATORY_PATTERN = r"(?:Firma|firma)[:\s]*\n+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)"
```

### 4.2 API Endpoints

```
POST /api/alianzas/broker-contracts/scan
  Body: { "directory_path": string, "include_subfolders": boolean }
  Response: { "job_id": string, "folders_found": number }

GET /api/alianzas/broker-contracts/scan/{job_id}/status
  Response: { "status": string, "progress": number, "current_folder": string }

GET /api/alianzas/broker-contracts/scan/{job_id}/results
  Response: { "brokers": BrokerIncentiveData[], "errors": ExtractionError[] }

GET /api/alianzas/broker-contracts/export/{job_id}
  Response: Excel file download
```

### 4.3 Data Models

```python
class ContractType(Enum):
    BONO = "bono"
    INCENTIVOS = "incentivos"
    UNKNOWN = "unknown"

class SignatoryInfo(BaseModel):
    name: Optional[str]
    rfc: Optional[str]

class BrokerIncentiveData(BaseModel):
    broker_name: str
    folder_path: str
    pdf_path: Optional[str]
    contract_type: ContractType
    credit_line_incentive_pct: Optional[float]
    operations_incentive_pct: Optional[float]
    signatory: SignatoryInfo
    extraction_date: datetime
    warnings: List[str]
```

### 4.4 Frontend Components

| Component | Location | Purpose |
|-----------|----------|---------|
| FKBrokerContractScanner | components/alianzas/ | Main scanner page |
| FKDirectoryInput | components/ui/ | Directory selection with validation |
| FKScanProgress | components/alianzas/ | Progress display component |
| FKBrokerResultsGrid | components/alianzas/ | Results data grid |

### 4.5 Dependencies
- **PyMuPDF (fitz):** PDF text extraction (already in project)
- **pandas:** Excel generation (already in project)
- **openpyxl:** Excel file writing (may need to add)

---

## 5. Edge Cases & Error Handling

### 5.1 Expected Edge Cases

| Case | Handling |
|------|----------|
| No PDF in folder | Log warning, include in results with null values |
| Multiple PDFs in folder | Process first matching contract, log others |
| Missing RFC in signature | Set RFC to null, include signatory name |
| Incentive not found | Set to null, add warning message |
| Unrecognized contract type | Mark as "unknown", attempt extraction anyway |
| Corrupted PDF | Log error, skip folder, continue processing |
| Empty folder | Skip, do not include in results |
| Special characters in folder name | Handle UTF-8 encoding properly |

### 5.2 Validation Rules

- Directory path must exist and be readable
- At least one subfolder must be present
- PDF files must be valid and readable
- Percentage values must be between 0 and 100

---

## 6. Security Considerations

- **File Access:** Only allow access to designated directories
- **Path Traversal:** Sanitize directory paths to prevent traversal attacks
- **File Size Limits:** Set maximum PDF size for processing (e.g., 50MB)
- **RBAC:** Restrict feature to users with `alianzas` or `admin` roles

---

## 7. Testing Requirements

### 7.1 Unit Tests
- Regex pattern matching for each contract type
- Folder name parsing
- Excel generation

### 7.2 Integration Tests
- Full scan workflow with sample directory
- API endpoint responses
- Error handling scenarios

### 7.3 Test Data
- Use `Example Files for Reqs/2024` directory for testing
- Create mock contracts for edge cases

---

## 8. Success Metrics

| Metric | Target |
|--------|--------|
| Extraction Accuracy | > 95% for well-formatted contracts |
| Processing Speed | < 2 seconds per PDF |
| User Adoption | Used by Alianzas team within 1 week of release |

---

## 9. Future Enhancements (Out of Scope)

- Automatic contract classification using ML
- Integration with broker database
- Historical tracking of incentive changes
- Batch processing scheduling
- Email notifications on completion

---

## 10. Appendix

### 10.1 Sample Contract Text Patterns

**Bono Contract Example:**
```
ANEXO A - ESPECIFICACIÓN DEL BONO

El presente anexo establece las condiciones del bono acordado:

1. Un bono equivalente al 0.80% del monto colocado a cliente por concepto
   de bono de apertura (línea de crédito).

2. Un bono equivalente al 0.07% del monto de operaciones elegibles realizadas
   por el cliente.
```

**Incentivos Contract Example:**
```
ARTÍCULO 3. INCENTIVOS

Finkargo reconocerá un incentivo de 0.07% sobre el monto de operaciones
en el alta por cada nuevo cliente referido por el BROKER.
```

### 10.2 References

- Tesoreria "Escaneo Directorio Local" implementation
- Example contracts in: `Example Files for Reqs/2024/`

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-16 | Claude AI | Initial draft from transcript |
