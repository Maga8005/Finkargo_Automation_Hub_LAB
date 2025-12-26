# E2E Test: Declaration Inventory Scanner Format Upload

Test that the Declaration Inventory upload accepts the new scanner output Excel format with English column names.

## User Story

As a Finkargo treasury user
I want to upload my automated scanner output Excel file as the declaration inventory
So that I can match declarations to payments without manually reformatting the Excel file

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with admin or tesoreria role
- Test file: `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/20251215 Diveco Test.xlsx`
- A valid Historial de Pagos Excel file for the initial upload

## Scanner Format Excel Columns

The scanner output file contains these columns:
| Column Name | Description | Example |
|-------------|-------------|---------|
| Customer Name | Customer/company name | DIVECO SAS |
| Date Folder | Date from folder (DD-MM-YYYY) | 01-07-2025 |
| Amount Folder | European format amount | 8.111,43 |
| PDF File Name | PDF filename | DC 4.862,00.pdf |
| PDF File Path | Full Windows path | (ignored) |
| Declaration Number | Numeric DC number | 81590 |
| Extraction Status | SUCCESS/PARTIAL/FAILED | SUCCESS |
| Extraction Error | Error message if failed | (empty) |
| Parsed Date | Clean date (YYYY-MM-DD) | 2025-07-01 |
| Parsed Amount | US format amount | $4,862.00 |

## Test Steps

### Step 1: Login and Navigate

1. Navigate to http://localhost:5173
2. Login with admin or tesoreria role user
3. Navigate to `/treasury/declaration-matching`
4. **Verify** page loads with file upload sections

### Step 2: Upload Historial de Pagos First

1. Upload a valid Historial de Pagos Excel file
2. **Verify** file parses successfully
3. **Verify** session ID is created
4. **Verify** declaration inventory upload section becomes active

### Step 3: Upload Scanner Format Declaration Inventory

1. Select the scanner output file `20251215 Diveco Test.xlsx`
2. **Verify** file uploads without errors
3. **Verify** declarations are parsed correctly
4. Take screenshot of upload success state

### Step 4: Verify Parsed Data

1. Proceed to matching step (or check API response)
2. **Verify** the following data transformations occurred:
   - `Customer Name` mapped correctly (should show DIVECO SAS)
   - Dates parsed from `Parsed Date` or `Date Folder` format
   - Amounts parsed from `Parsed Amount` (US format) or `Amount Folder` (European format)
   - Declaration numbers converted from float to integer string (81590.0 -> "81590")
   - Rows with NaN declaration numbers are skipped
3. **Verify** expected number of valid declarations (should be fewer than total rows due to NaN skips)

### Step 5: Verify European Amount Format Parsing

The file contains amounts in European format (dots for thousands, comma for decimal):
- `8.111,43` should parse to `8111.43`
- `4.862,00` should parse to `4862.00`
- `18.033,57` should parse to `18033.57`

**Verify** amounts display correctly in the declaration list.

### Step 6: Verify Date Format Parsing

The file may have dates in multiple formats:
- `Date Folder`: DD-MM-YYYY format (e.g., `01-07-2025`)
- `Parsed Date`: YYYY-MM-DD format (e.g., `2025-07-01`)

**Verify** the system prioritizes `Parsed Date` when available, falling back to `Date Folder`.

## Success Criteria

- [ ] Scanner format Excel file uploads without column validation errors
- [ ] `Customer Name` column maps to customer field
- [ ] `Date Folder` or `Parsed Date` column maps to date field
- [ ] `Amount Folder` or `Parsed Amount` column maps to amount field
- [ ] `Declaration Number` column maps to declaration number field
- [ ] `PDF File Name` column maps to PDF filename field
- [ ] European amount format (`8.111,43`) parses correctly to `8111.43`
- [ ] US amount format (`$4,862.00`) parses correctly to `4862.00`
- [ ] DD-MM-YYYY date format parses correctly
- [ ] Float declaration numbers convert to integers (`81590.0` -> `"81590"`)
- [ ] Rows with NaN declaration numbers are skipped (not causing errors)
- [ ] Backward compatibility: Spanish column names still work

## Error Scenarios

1. File with only English columns missing required fields -> Should show missing column error
2. File with invalid European format -> Should show amount parsing error for specific rows
3. File with all NaN declaration numbers -> Should show 0 declarations parsed (not crash)

## Expected Row Counts

For `20251215 Diveco Test.xlsx`:
- Total rows in Excel: ~9 rows
- Rows with valid Declaration Number: ~7-8 rows
- Rows with NaN (skipped): ~1-2 rows

## Screenshot Locations

1. After login on Declaration Matching page
2. After Historial upload success
3. After Declaration Inventory scanner format upload success
4. Declaration list showing parsed data

## Notes

- The system should prefer `Parsed Date` over `Date Folder` when both exist
- The system should prefer `Parsed Amount` over `Amount Folder` when both exist
- This allows cleaner data when the scanner provides both raw and parsed values
