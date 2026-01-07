# Solicitud de Desembolso - Data Sources

> **Source**: Transcript with Sofia Tobon (2025-12-07)
> **Related**: `docs/20251207 TRANSCRIPT SOLICITUD DE DESEMBOLSO.txt`

---

## Overview

The Solicitud de Desembolso document is filled using data from multiple sources. This document maps each field to its data source for implementation purposes.

---

## Data Sources Summary

| Source | Description |
|--------|-------------|
| **Cotizacion** | Quote document from HubSpot containing operation details |
| **Current Date** | System-generated date when creating the document |
| **Derived Formula** | Calculated based on client data and business rules |
| **Client Data** | From the `clients` table in the database |

---

## Field Mapping by Source

### From Cotizacion (HubSpot Quote)

| Field | Spanish Name | Example | Notes |
|-------|--------------|---------|-------|
| Quote Number | Numero de cotizacion desembolso | `COT-2025-001` | Unique identifier from HubSpot |
| Credit Contract Date | Fecha del contrato de credito | `30 de octubre de 2025` | Date when credit contract was signed |
| Amount | Monto | `$100,000,000` | Disbursement amount in COP |
| Days | Dias | `120` | Payment term (typically 120 days) |
| Legal Representative | Representante legal | `Juan Perez` | Name of legal representative |
| National Expense Creditors | Acreedor(es) de gastos nacionales | `DIAN` | Found in Anexo section |
| Anexo 1 Table | Anexo 1 | (table) | Payment breakdown - copied directly |

### NOT from Cotizacion

| Field | Spanish Name | Source | Notes |
|-------|--------------|--------|-------|
| Request Date | Fecha de la solicitud | **Current Date** | Date when creating the document |
| Credit Contract ID | Consecutivo del contrato de credito | **Derived Formula** | See formula below |
| Client NIT | NIT | **Client Data** | Also appears in Cotizacion |

---

## Consecutivo del Contrato de Credito Formula

### Format
```
{sequence}-{NIT}-{contract_number}-DM-DOM
```

### Components

| Component | Description | Example |
|-----------|-------------|---------|
| `sequence` | Usually `1` | `1` |
| `NIT` | Client's tax ID | `900123456` |
| `contract_number` | Contract sequence (`1`, `2`, etc.) | `1` |
| `DM-DOM` | Fixed suffix (always present) | `DM-DOM` |

### Example
```
1-900123456-1-DM-DOM
```

### Transcript Quote
> "Siempre va a ser el NIT, siempre es el NIT, siempre es el, a veces es el 1 dependiendo del contrato en el que vayas, el 2 pues eso ya lo puedo ajustar yo a mano dado el caso y siempre es DM, DOM al final"

---

## Acreedor de Gastos Nacionales Mapping

The Cotizacion's Anexo section contains keywords that map to creditor types:

| Keyword in Cotizacion | Creditor Type | Spanish Label |
|-----------------------|---------------|---------------|
| `DIAN` | Tax/Customs duties | Tributos aduaneros |
| `Agencia de aduanas` | Customs agency | Agencia de aduanas |
| `Agente de carga` | Freight agent | Gastos logisticos |
| `Agente de carga` | Freight agent | Gastos de transporte |
| `Agencia logistica` | Logistics agency | Gastos logisticos |

### Multiple Creditors

A single operation can have **multiple creditors**. From the transcript:

> "a veces pueden ir multiples, o sea puede en una sola operacion... puede existir que se vaya a pagar a la DIAN... y puede existir que se vaya a pagar a un agente de carga"

---

## Cotizacion Document Structure

Sofia confirmed the Cotizacion format is **always identical**:

> "Siempre es identico, lo unico que varia son estos datos"

### Key Locations in Cotizacion

| Data | Location |
|------|----------|
| Quote number | Header area |
| Contract date | Header area |
| Amount (Monto) | Appears multiple times |
| Days | Body section |
| Representative data | Body section |
| Acreedor keywords | Anexo 1 section (bottom) |
| Anexo 1 table | Last section |

---

## Anexo 1 Handling

The Anexo 1 table is **copied directly** from the Cotizacion to the final document:

> "este anexo 1 que se va a tener que copy pastear en el otro documento"

> "esta tabla que les estoy resaltando aqui, es exactamente esta misma tabla"

### Current Process (Manual)
1. Extract Anexo 1 table from Cotizacion PDF
2. Append to generated Solicitud de Desembolso
3. Final document includes both sections

### Future Automation
Consider implementing PDF upload and merge functionality to automate Anexo 1 attachment.

---

## Implementation Considerations

### Required User Inputs (Not in System)

Since the Cotizacion is an external document (HubSpot), the following must be entered manually by the user:

1. **Numero de cotizacion desembolso** - Text input
2. **Fecha del contrato de credito** - Date picker
3. **Monto** - Currency input
4. **Dias** - Number input (default: 120)
5. **Acreedores** - Multi-select checkboxes

### Auto-Populated from System

1. **Fecha de la solicitud** - Current date
2. **Consecutivo del contrato de credito** - Generated from formula
3. **NIT** - From client search
4. **Nombre importador** - From client data
5. **Representante legal** - From client data
6. **Cedula representante** - From client data

---

## References

- Transcript: `docs/20251207 TRANSCRIPT SOLICITUD DE DESEMBOLSO.txt`
- Feature Prompt: `docs/20251207_FEATURE_PROMPT_SOLICITUD_DESEMBOLSO.md`
- Contract Type: `pl_co_solicitud_desembolso`
- ID Prefix: `PLSD-`
