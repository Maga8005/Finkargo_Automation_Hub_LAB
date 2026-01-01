# Implement the following plan
Follow the `Instructions` to implement the `Plan` then `Report` the completed work.

## Instructions
- Read the plan thoroughly before writing any code
- Identify the **Feature Category** from the plan's Pre-Implementation Verification section
- Execute the relevant `Pre-Implementation Verification` steps below based on category
- Implement the plan step by step, following the order specified
- If any assumption in the plan is incorrect, STOP and document the discrepancy before continuing

## Pre-Implementation Verification

Before writing ANY code, verify assumptions based on the feature category:

### For ALL Features: Data Contract Verification
Before using repository methods, check their return types:
- Look at the method signature and return type hints
- Check if it returns `dict` or a model object
- Use `['key']` for dicts, `.attribute` for objects

Verify the plan's TypeScript interfaces match the actual API response format:
- This project uses **snake_case** in both backend Pydantic models AND frontend TypeScript
- If the plan specifies camelCase in TypeScript, correct it to snake_case

### A. Document Generation Features
If the plan involves Word document generation:
```python
cd backend && python -c "
from docx import Document
import re
doc = Document('templates/YOUR_TEMPLATE.docx')
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
**Compare output with placeholders in the plan.** If they don't match, update the implementation to use EXACT placeholder strings from the template.

Verify database records:
- Check `contract_templates` table has the required record
- If missing, create the migration FIRST before other implementation

### B. Excel Processing Features
If the plan involves Excel file processing:
1. **Verify source Excel columns** exist with exact names specified in the plan
2. **Check existing similar services** for patterns:
   - `PaymentTemplateService` for payment conversions
   - `ExcelValidationService` for upload validation
   - `ExcelMergeService` for data consolidation
3. **Verify catalog data** exists:
   - AR account mappings
   - Product classifications
   - Country-specific variations (CO vs MX)

### C. Data Import/Export Features
If the plan involves file import/export:
1. **Verify file format validation** matches plan specifications
2. **Check field mapping** matches actual source file structure
3. **Verify error handling** approach matches existing patterns

### D. API Integration Features
If the plan involves external API integration:
1. **Verify API endpoints** are accessible
2. **Check authentication** method and credentials
3. **Test error scenarios** before full implementation

### E. Reporting Features
If the plan involves data queries/reports:
1. **Verify query parameters** match existing patterns
2. **Check pagination** implementation matches frontend expectations
3. **Verify filter parameters** are correctly typed

### F. Enum and Field Access Verification (ALL Features)

**CRITICAL:** These bugs pass linting but cause runtime errors masked as CORS issues.

Before using enums or permission checks:

1. **Enum Member Case (Python)**:
   - Python enums use **UPPERCASE** member names: `Status.PENDING`
   - NOT lowercase: `Status.pending` (WRONG - causes AttributeError!)
   - The **value** is lowercase, the **member name** is UPPERCASE
   - Example: `EmailChainValidationStatus.PENDING` (correct)
   - Example: `EmailChainValidationStatus.pending` (WRONG!)

2. **Role vs UserType Field (Frontend/TypeScript)**:
   - `userProfile.role` = 'admin', 'risk_manager', 'mesa_control', 'legal', 'operations', 'analyst'
   - `userProfile.user_type` = 'funcionario' or 'cliente' ONLY
   - For permission checks, ALWAYS use `.role`, NEVER `.user_type`
   - Example: `['admin', 'risk_manager'].includes(userProfile.role)` (correct)
   - Example: `['admin', 'risk_manager'].includes(userProfile.user_type)` (WRONG - always false!)

3. **Post-Implementation Verification**:
   ```bash
   # Check for lowercase enum member access
   git diff --cached | grep -E "(Status|Type)\.[a-z]+" && echo "WARN: lowercase enum member?"

   # Check for user_type in role checks
   git diff --cached | grep "user_type.*includes" && echo "WARN: user_type for role check?"
   ```

4. **Test New Endpoints**:
   Before committing, verify new endpoints don't return 500:
   ```bash
   # Start backend and test endpoint
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/your/new/endpoint
   # Must return 2xx or expected 4xx, NOT 500
   ```

## Handling Discrepancies

If you discover the plan has incorrect assumptions:
1. **Document the discrepancy** clearly
2. **Update the approach** to match reality
3. **Continue with corrected implementation**
4. **Note the correction in the Report** section

Common discrepancies to watch for:
- Template placeholders don't match plan (case, spacing, format)
- Excel column names don't match plan (accents, capitalization)
- Repository returns dict but plan assumes object (or vice versa)
- Database records missing that plan assumed existed
- Country-specific variations not handled (CO vs MX)

## Plan
$ARGUMENTS

## Report
- Summarize the work you've just done in a concise bullet point list.
- **List any discrepancies found** between the plan and reality, and how you resolved them
- Report the files and total lines changed with `git diff --stat`
- Write report in the `implementations/*.md` file. Name it appropriately based on the `Report`. Use the naming convention [year][month][day]_[module]_[name]
