# Validate Implementation Plan

Validate an implementation plan before execution to catch common issues that lead to bugs.

## Variables
plan_file: $ARGUMENTS

## Instructions

Read the plan file and validate it against the following checklist. First identify the feature category, then apply the relevant validations.

## Step 1: Identify Feature Category

Read the plan and determine which category applies:
- **Document Generation** - Contracts, PDFs, Word templates
- **Excel Processing** - Payment conversion, invoice processing, data consolidation
- **Data Import/Export** - CSV import, ZIP download, file uploads
- **API Integration** - Google Drive sync, external services
- **Reporting** - Finance reports, audit history, data queries
- **CRUD Operations** - Client management, template CRUD

## Step 2: Apply Category-Specific Validation

### A. Document Generation Validation

If the plan involves Word document generation:
1. **Run the placeholder extraction script** on the template mentioned in the plan:
   ```python
   cd backend && python -c "
   from docx import Document
   import re
   doc = Document('templates/TEMPLATE_NAME.docx')
   placeholders = set()
   for para in doc.paragraphs:
       found = re.findall(r'\[[^\]]+\]', para.text)
       placeholders.update(found)
   for table in doc.tables:
       for row in table.rows:
           for cell in row.cells:
               found = re.findall(r'\[[^\]]+\]', cell.text)
               placeholders.update(found)
   for p in sorted(placeholders):
       print(p)
   "
   ```
2. **Compare extracted placeholders** with those listed in the plan
3. **Check database dependencies**:
   - Verify `contract_templates` record exists or migration is included
   - Verify enum exists in DTOs or task to add it is included

### B. Excel Processing Validation

If the plan involves Excel file processing:
1. **Verify column mapping completeness**:
   - All source columns documented with exact names?
   - Output columns documented?
   - Data transformation rules specified?
2. **Check catalog dependencies**:
   - AR account mappings needed? Documented?
   - Country variations (CO vs MX) handled?
3. **Verify existing pattern adherence**:
   - Does the plan reference similar existing services?
   - Are patterns from `PaymentTemplateService`, `ExcelValidationService` followed?

### C. Data Import/Export Validation

If the plan involves file import/export:
1. **Verify file format specifications**:
   - Supported formats documented?
   - Size limits specified?
   - Required headers listed?
2. **Check field mapping completeness**:
   - All source fields mapped?
   - Data type conversions specified?
   - Validation rules documented?
3. **Verify error handling**:
   - Invalid row handling specified?
   - Error message format defined?

### D. API Integration Validation

If the plan involves external API integration:
1. **Verify API contract documentation**:
   - Endpoint URLs documented?
   - Authentication method specified?
   - Request/response formats defined?
2. **Check error handling strategy**:
   - Retry logic defined?
   - Timeout handling specified?
   - Fallback behavior documented?

### E. Reporting Validation

If the plan involves data queries/reports:
1. **Verify query documentation**:
   - Filter parameters documented?
   - Pagination needs specified?
   - Sort options defined?
2. **Check performance considerations**:
   - Expected data volume noted?
   - Indexing needs identified?

## Step 3: Universal Validations (ALL Categories)

### Data Contract Validation
1. **Check repository methods** mentioned in the plan:
   - Verify return types (dict vs object)
   - Verify access patterns match return types
2. **Check TypeScript interfaces** in the plan:
   - Verify they use snake_case (not camelCase) to match API responses
   - Compare with existing similar interfaces in `frontend/src/types/`

### Plan Completeness Validation
1. **Check New Files section:**
   - All files mentioned in tasks should be listed
   - All migration files should be listed
2. **Check Validation Commands:**
   - Should include pytest, ruff, lint, tsc, and build commands
   - Should include E2E test execution if UI feature
3. **Check Step by Step Tasks:**
   - Should end with validation commands execution
   - Should include database migration if new records needed

### Consistency Validation
1. **Field naming consistency:**
   - Backend fields should use snake_case
   - Frontend fields should use snake_case (matching API response)
2. **Import path consistency:**
   - Verify import paths match actual file structure

## Report Format

Return a validation report in this format:

```json
{
  "plan_file": "path/to/plan.md",
  "feature_category": "document_generation | excel_processing | import_export | api_integration | reporting | crud",
  "validation_status": "PASS | FAIL | WARNINGS",
  "issues_found": [
    {
      "category": "template_placeholders | excel_columns | data_contract | database_dependencies | completeness | consistency",
      "severity": "critical | warning",
      "description": "Description of the issue",
      "recommendation": "How to fix the issue"
    }
  ],
  "category_specific_validation": {
    "document_generation": {
      "placeholders_extracted": ["[Placeholder 1]"],
      "placeholders_in_plan": ["[Placeholder 1]"],
      "missing_from_plan": [],
      "extra_in_plan": []
    },
    "excel_processing": {
      "source_columns_documented": true,
      "output_columns_documented": true,
      "catalog_dependencies_identified": true
    }
  },
  "summary": "Brief summary of validation results"
}
```

## Plan File
Read and validate the following plan file: `$ARGUMENTS`

## Output

Return ONLY the JSON validation report. Do not include any additional text or markdown formatting.
