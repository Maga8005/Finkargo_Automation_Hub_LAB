# Instruccion de Mandato - Data Sources

## Overview

The **Instruccion de Mandato** (Instruction of Mandate) is a legal document generated as part of the Paga Local Colombia operation workflow. It authorizes Finkargo to transfer funds to National Expense Creditors (Acreedores de Gastos Nacionales) on behalf of the client. This document is generated alongside the "Solicitud de Desembolso" (Disbursement Request) for each disbursement operation.

**Template File:** `FK COL - Fin. COP - Mandato (IM).docx`
**Contract Type:** `pl_co_mandato_im` (for non-DIAN creditors requiring Bank Certificate)

> **Note:** DIAN-specific payments (`pl_co_dian_mandato_im`) will be implemented separately with a dedicated template. This document focuses on the non-DIAN implementation only.

## Data Sources Summary

| Source | Description |
|--------|-------------|
| Cotizacion PDF | Quote document containing disbursement number, dates, total amount, and Anexo I creditors list |
| Bank Certificate PDF | Bank certification document containing creditor's bank account information |
| Database (clients table) | Client data including legal representative name and ID |
| System Generated | Current date, document ID |

## Key Business Rules (from Transcript)

1. **Disbursement Number**: Same as the quote number (Numero de Cotizacion de Desembolso), copy-pasted from the Cotizacion PDF
2. **Contract Date (Fecha del contrato marco de mandato)**: Always the same as the Credit Contract date (same as Contrato de Credito)
3. **Amount**: Extracted from Cotizacion PDF - must be displayed in both letters (text) and numbers
4. **Creditor Information**: Extracted from Bank Certificate PDF (varies by creditor/bank)
5. **Multiple Creditors**: A single Instruccion de Mandato can have multiple creditors (up to 3)
6. **Bank Certificate Requirement**: Mesa de Control requires the bank certificate before releasing disbursement

> **Scope Note:** This implementation handles non-DIAN creditors only. DIAN payments (tax authority) will use a separate template with pre-filled static values (PCE payment method).

## Field Mapping by Source

### From Cotizacion PDF (Quotation)

| Field | Template Placeholder | Example Value | Extraction Notes |
|-------|---------------------|---------------|------------------|
| Numero de Cotizacion | `[Numero de cotizacion de desembolso]` | CO:900436389:1:2:DOM | Same format as Solicitud de Desembolso |
| Monto Total | `[monto a transferir en numeros]` | $739,860 | Sum of all Anexo I items |
| Monto en Letras | `[monto a transferir en letras]` | SETECIENTOS TREINTA Y NUEVE MIL OCHOCIENTOS SESENTA | Auto-generated from monto |
| Fecha del Contrato de Credito | `[dia de firma contrato mandato]`, `[mes de firma contrato mandato]`, `[ano de firma contrato mandato]` | 6, noviembre, 2025 | Extract from "Contrato de Credito en Pesos de fecha..." pattern |

### From Bank Certificate PDF (Certificado Bancario)

| Field | Template Placeholder | Example Value | Extraction Notes |
|-------|---------------------|---------------|------------------|
| Razon Social (Company Name) | `[...]` in nested table | CONSULADUANA & LOGISTICA SAS | Company name from certificate header |
| NIT | `[...]` in nested table | 901599856 | Tax ID from certificate |
| Banco | `[...]` in nested table | BANCOLOMBIA | Bank name extracted from certificate |
| Tipo de Cuenta | `[Ahorros \| Corriente]` in nested table | CUENTA DE AHORROS | Account type (Savings/Checking) |
| Numero de Cuenta | `[...]` in nested table | 77500002334 | Bank account number |

### From Database (clients table)

| Field | Table.Column | Template Placeholder | Notes |
|-------|--------------|---------------------|-------|
| Representante Legal | clients.representante_legal | `[Nombre del representante legal del Cliente]` | Legal representative name |
| Cedula Representante | clients.cedula_representante | `[numero ID representante legal]` | ID number of legal representative |

### System Generated

| Field | Logic | Template Placeholder | Notes |
|-------|-------|---------------------|-------|
| Fecha Actual | Current date at generation time | `[Fecha actual]` | Format: DD de MONTH de YYYY |
| Document ID | Auto-increment sequence | N/A (not in template) | For tracking purposes |

### DIAN-Specific Static Values (For Future Separate Implementation)

> **Out of Scope:** The following DIAN values are documented for reference only. DIAN payments will be implemented separately with contract type `pl_co_dian_mandato_im` and a dedicated template.

| Field | Static Value | Notes |
|-------|-------------|-------|
| Razon Social | DIAN | Direccion de Impuestos y Aduanas Nacionales |
| NIT | 800.197.268-4 | DIAN's official NIT |
| Banco | PSE/Recaudo Electronico | Electronic payment system |
| Tipo de Cuenta | PCE | Pago por Compensacion Electronica |
| Numero de Cuenta | N/A or reference number | Payment reference |

## Template Placeholders Summary

### Main Document Placeholders

| Placeholder | Description | Source |
|-------------|-------------|--------|
| `[Fecha actual]` | Current date | System Generated |
| `[Numero de cotizacion de desembolso]` | Disbursement quote number | Cotizacion PDF |
| `[dia de firma contrato mandato]` | Day of contract signing | Cotizacion PDF (same as credit contract) |
| `[mes de firma contrato mandato]` | Month of contract signing | Cotizacion PDF |
| `[ano de firma contrato mandato]` | Year of contract signing | Cotizacion PDF |
| `[monto a transferir en letras]` | Amount in words (Spanish) | Derived from Cotizacion PDF |
| `[monto a transferir en numeros]` | Amount in numbers | Cotizacion PDF |
| `[Nombre del representante legal del Cliente]` | Legal representative name | Database or Cotizacion PDF |
| `[numero ID representante legal]` | Legal representative ID | Database or Cotizacion PDF |

### Nested Table (Creditor Information) - Row Structure

The template contains a nested table for creditor information with the following structure:

| Column | Placeholder | Source |
|--------|-------------|--------|
| Razon social | `[...]` | Bank Certificate PDF |
| NIT (si aplica) | `[...]` | Bank Certificate PDF |
| Banco | `[...]` | Bank Certificate PDF |
| Tipo de Cuenta | `[Ahorros \| Corriente]` | Bank Certificate PDF |
| Numero de Cuenta | `[...]` | Bank Certificate PDF |

**Note:** Template has 3 data rows available for multiple creditors.

## Implementation Approach: Separate Templates (Chosen)

Based on stakeholder requirements, DIAN and non-DIAN creditors will be handled as **separate implementations**:

| Contract Type | Template | Creditor Type | Input Required |
|---------------|----------|---------------|----------------|
| `pl_co_mandato_im` | `FK COL - Fin. COP - Mandato (IM).docx` | Non-DIAN (banks, agents, etc.) | Cotizacion PDF + Bank Certificate PDF |
| `pl_co_dian_mandato_im` | *Separate template TBD* | DIAN (tax authority) | Cotizacion PDF only (static values) |

**This Document Scope:** `pl_co_mandato_im` (non-DIAN) implementation only.

**Benefits of Separate Templates:**
- Simpler logic per implementation
- Clear separation of concerns
- Easier to maintain and test independently
- Different UI flows (Bank Certificate required vs not required)

## File Processing Requirements

### Cotizacion PDF Parser (Existing)
- Reuse `CotizacionParserService` from `cotizacion_parser_service.py`
- Already extracts: numero_cotizacion, fecha_contrato_credito, anexo_items

### Bank Certificate PDF Parser (New)
Required extraction patterns by bank:

**Bancolombia Format:**
```
BANCOLOMBIA S.A. se permite informar que [COMPANY_NAME] identificado(a) con
NIT [NIT], a la fecha de expedicion...

| Producto | No. Producto | Fecha Apertura | Estado |
| CUENTA DE AHORROS | 77500002334 | 2022/06/03 | ACTIVA |
```

**Extraction Regex Patterns:**
- Company Name: `informar que (.+?) identificado`
- NIT: `NIT (\d+)`
- Bank: Extract from header/logo or document title
- Account Type: `(CUENTA DE AHORROS|CUENTA CORRIENTE)`
- Account Number: `\d{10,}` in the product table

## Data Flow Diagram

```
                    +------------------+
                    |  Cotizacion PDF  |
                    +--------+---------+
                             |
           Extract: numero_cotizacion, fecha_contrato,
                    monto_total, anexo_items (creditors)
                             |
                             v
+------------------+    +----+----+    +--------------------+
| Bank Certificate |    |         |    | Database (clients) |
|       PDF        +--->| Service +<---+                    |
+------------------+    |  Layer  |    +--------------------+
                        |         |
Extract: razon_social,  |         |  Get: representante_legal,
nit, banco, tipo_cuenta,|         |       cedula_representante
numero_cuenta           |         |
                        +----+----+
                             |
                             v
                    +--------+--------+
                    |  DocumentService |
                    | (Template Fill)  |
                    +---------+--------+
                              |
                              v
                    +---------+--------+
                    | Instruccion de   |
                    | Mandato (DOCX)   |
                    +------------------+
```

## Edge Cases and Validation

1. **Missing Bank Certificate**: Bank Certificate is REQUIRED for this implementation - block generation if not provided
2. **Multiple Creditors**: Support up to 3 creditors (template limit)
3. **Amount Validation**: Ensure monto in Instruccion de Mandato matches Cotizacion total
4. **Date Consistency**: Fecha del contrato mandato MUST equal fecha del contrato de credito
5. **ID Type Detection**: Detect C.C. vs C.E. from certificate or database
6. **Bank Format Variations**: Handle different bank certificate formats (Bancolombia, BBVA, etc.)

## References

- **Transcript**: `docs/20251207A TRANSCRIPT INSTRUCCION DE MANDATO.txt`
- **Template**: `backend/templates/FK COL - Fin. COP - Mandato (IM).docx`
- **Example Cotizacion**: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
- **Example Bank Certificate**: `Example FIles for Reqs/certificado bancario.pdf`
- **Existing Parser**: `backend/src/core/servicios/cotizacion_parser_service.py`
- **Document Service**: `backend/src/core/servicios/document_service.py`
- **Legal DTOs**: `backend/src/interface/legal_dtos.py`
