# CSV Import Guide - Client Data for Contract Generation

## Overview
This guide explains how to prepare and import client data for automated contract generation.

## CSV File Format

### Required Columns (Must be present)
1. **nit** - Client Tax ID (e.g., "900123456-1")
2. **nombre_importador** - Client/Importer company name
3. **representante_legal** - Legal representative full name
4. **cedula_representante** - Representative ID number
5. **ciudad_domicilio** - City of domicile
6. **cupo_plataforma** - Credit limit amount (numeric, no currency symbols)

### Optional Columns (For complete contract population)
7. **direccion_comercial** - Full business address
8. **tipo_identificacion_representante** - ID type (CC, NIT, CE, etc.) - defaults to "CC"
9. **nombre_contrato_marco** - Framework contract name - defaults to "Compra de Cartera"
10. **kam_nombre** - Key Account Manager name
11. **kam_email** - Key Account Manager email
12. **destinatario_nombre** - Notification recipient name
13. **destinatario_email** - Notification recipient email

## Field Descriptions

### Client Information
- **nit**: Colombian tax identification number with verification digit
  - Example: `900123456-1`

- **nombre_importador**: Legal name of the importing company
  - Example: `IMPORTADORA EJEMPLO S.A.S.`

- **representante_legal**: Full name of legal representative
  - Example: `Juan Pérez García`

- **cedula_representante**: ID number of legal representative
  - Example: `1234567890`

- **tipo_identificacion_representante**: Type of ID document
  - Options: `CC` (Cédula de Ciudadanía), `NIT`, `CE` (Cédula de Extranjería), `Pasaporte`
  - Default: `CC`

### Location Information
- **ciudad_domicilio**: City where company is domiciled
  - Example: `Bogotá`

- **direccion_comercial**: Complete business address
  - Example: `Calle 100 #15-20 Oficina 501, Bogotá D.C.`
  - If not provided, `ciudad_domicilio` will be used in contract

### Financial Information
- **cupo_plataforma**: Credit limit on platform (numeric only)
  - Example: `50000000` (for $50,000,000 COP)
  - Do NOT include currency symbols or decimal points
  - Will be formatted automatically in contract

### Contract Information
- **nombre_contrato_marco**: Name of framework contract
  - Example: `Compra de Cartera`, `Factoring Internacional`
  - Default: `Compra de Cartera`

### Contact Information
- **kam_nombre**: Key Account Manager full name
  - Example: `María Rodríguez`

- **kam_email**: KAM email address
  - Example: `maria.rodriguez@finkargo.com`

- **destinatario_nombre**: Notification recipient name (different from KAM)
  - Example: `Carlos Méndez`

- **destinatario_email**: Notification recipient email
  - Example: `carlos.mendez@ejemplo.com`

## File Encoding
- **Encoding**: UTF-8, Latin-1, Windows-1252, or ISO-8859-1
- The system will automatically detect encoding
- For Spanish characters (á, é, í, ó, ú, ñ), UTF-8 is recommended

## Example CSV File

```csv
nit,nombre_importador,representante_legal,cedula_representante,ciudad_domicilio,cupo_plataforma,direccion_comercial,tipo_identificacion_representante,nombre_contrato_marco,kam_nombre,kam_email,destinatario_nombre,destinatario_email
900123456-1,IMPORTADORA EJEMPLO S.A.S.,Juan Pérez García,1234567890,Bogotá,50000000,"Calle 100 #15-20 Oficina 501, Bogotá D.C.",CC,Compra de Cartera,María Rodríguez,maria.rodriguez@finkargo.com,Carlos Méndez,carlos.mendez@ejemplo.com
900234567-2,COMERCIALIZADORA ABC LTDA,Ana María López,9876543210,Medellín,75000000,"Carrera 43A #14-25 Piso 3, Medellín",CC,Compra de Cartera,Pedro Sánchez,pedro.sanchez@finkargo.com,Laura Gómez,laura.gomez@abc.com
```

## Template File
A template CSV file is available at: `backend/templates/plantilla_importacion_clientes.csv`

## Import Process

1. **Prepare CSV file** with required and optional columns
2. **Go to Legal Dashboard** → "Importar Datos" tab
3. **Upload CSV or Excel file**
4. **Review import results**:
   - Total processed
   - Successful imports
   - Failed imports with error messages

## Validation Rules

### Required Field Validation
- **nit**: Minimum 5 characters, maximum 20 characters
- **nombre_importador**: Cannot be empty
- **representante_legal**: Cannot be empty
- **cedula_representante**: Cannot be empty
- **ciudad_domicilio**: Cannot be empty
- **cupo_plataforma**: Must be greater than 0

### Optional Field Validation
- **kam_email**, **destinatario_email**: Must be valid email format (if provided)
- **tipo_identificacion_representante**: Maximum 10 characters

## Contract Template Mapping

When a contract is generated, the following fields are populated in the Word template:

| CSV Column | Template Field |
|---|---|
| (Generation date) | `[día]`, `[mes]`, `[año]`, `[•]` |
| nombre_importador | `[NOMBRE DEL CLIENTE]` |
| representante_legal | `[nombre del representante legal]` |
| cedula_representante | `[Número de ID]` |
| tipo_identificacion_representante | `[tipo de identificación]` |
| ciudad_domicilio | `[nombre de la ciudad]` |
| direccion_comercial | `[Domicilio en que el Importador adelanta sus actividades comerciales]` |
| cupo_plataforma | `[valor Cupo de Operaciones en números]`, `[valor Cupo de Operaciones en letras]` |
| nombre_contrato_marco | `[nombre del contrato marco]` |
| kam_nombre | `[nombre del KAM]` |
| kam_email | `[ KAM e-mail]` |
| destinatario_nombre | `[nombre del destinatario]` |
| destinatario_email | `[destinatario e-mail]` |
| (Contract ID) | `[sic]` |

## Common Issues & Solutions

### Issue: "Missing required columns"
**Solution**: Ensure all 6 required columns are present with exact spelling

### Issue: "Encoding errors with Spanish characters"
**Solution**: Save CSV as UTF-8 encoding

### Issue: "Invalid cupo_plataforma value"
**Solution**: Ensure value is numeric only, no commas or currency symbols

### Issue: "Some rows failed to import"
**Solution**: Check the error log in import results for specific row issues

## Best Practices

1. **Test with small file first**: Import 2-3 records to verify format
2. **Keep backup**: Save original CSV before making changes
3. **Validate data**: Check for typos in NITs, emails, etc.
4. **Use template**: Start with the provided template file
5. **Complete optional fields**: Include all optional fields for complete contract population

## Support

For issues or questions about CSV import, please refer to:
- Session notes: `20251005_SESSION_NOTES_WORKFLOW_REFACTOR.md`
- Database migration: `backend/database/migration_add_contract_fields.sql`
