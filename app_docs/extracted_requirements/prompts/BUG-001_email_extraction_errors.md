# Feature Prompt: BUG-001 - Email Domain Extraction Errors

Use this prompt with the `/feature` command:

```
/feature <issue_number> <adw_id> '<issue_json>'
```

## Issue JSON

```json
{
  "title": "Fix email domain extraction errors in Riesgos module",
  "body": "## Problem Statement\n\nThe AI extraction (LandingAI) is making character-level mistakes when extracting email domains from documents, causing false positives in typosquatting detection and incorrect discrepancy alerts.\n\n## Reported Cases\n\n1. **Client: multivalsas** - Email multivazas@hotmail.com was extracted with Z instead of S\n2. **Client: Super Laminas Bogota** - Company suffix LTDA was extracted as LTD (missing A)\n\n## Expected Behavior\n\n- Email domains should be extracted accurately from documents\n- Common company suffixes (LTDA, SAS, SA, S.A.S., etc.) should be normalized\n- Extraction confidence scores should flag low-confidence extractions for manual review\n\n## Proposed Solution\n\n1. Add post-processing normalization for common Colombian company suffixes:\n   - LTD -> LTDA\n   - S.A.S -> SAS\n   - S.A. -> SA\n   - And similar variations\n\n2. Add fuzzy matching tolerance for email domain comparison:\n   - If Levenshtein distance is 1 character and its a vowel swap or common typo, flag as potential OCR error rather than fraud\n\n3. Add extraction confidence threshold:\n   - If extraction confidence < 0.85, flag for manual verification\n   - Display confidence score in UI for user awareness\n\n4. Consider using OpenAI extraction as fallback for low-confidence LandingAI extractions\n\n## Affected Files\n\n- backend/src/core/servicios/risk/document_extraction_service.py\n- backend/src/core/servicios/risk/cross_validation_service.py\n- backend/src/core/servicios/risk/normalization_service.py\n- frontend/src/components/risk/FKCrossValidationResults.tsx\n\n## Acceptance Criteria\n\n- Email domains extracted with greater than 95% accuracy\n- Common company suffix variations normalized (LTDA/LTD, SAS/S.A.S.)\n- Low confidence extractions flagged for manual review\n- Extraction confidence displayed in UI\n- Single character OCR errors do not trigger false positive fraud alerts\n\n## Priority\n\nHigh - Causing user confusion and false positive fraud alerts\n\n## Source\n\nFeedback meeting with Camila Perdomo (Mesa de Control) - December 29, 2025"
}
```

## Quick Copy Command

```bash
/feature 100 $(openssl rand -hex 4) '{"title":"Fix email domain extraction errors in Riesgos module","body":"## Problem Statement\n\nThe AI extraction (LandingAI) is making character-level mistakes when extracting email domains from documents, causing false positives in typosquatting detection.\n\n## Reported Cases\n\n1. Client: multivalsas - Email multivazas@hotmail.com extracted with Z instead of S\n2. Client: Super Laminas Bogota - Company suffix LTDA extracted as LTD (missing A)\n\n## Proposed Solution\n\n1. Add post-processing normalization for Colombian company suffixes (LTD->LTDA, S.A.S->SAS)\n2. Add fuzzy matching tolerance for single-character OCR errors\n3. Add extraction confidence threshold (less than 0.85 flags for manual review)\n4. Display confidence scores in UI\n\n## Affected Files\n\n- backend/src/core/servicios/risk/document_extraction_service.py\n- backend/src/core/servicios/risk/cross_validation_service.py\n- backend/src/core/servicios/risk/normalization_service.py\n\n## Acceptance Criteria\n\n- Email domains extracted with greater than 95% accuracy\n- Common suffix variations normalized\n- Low confidence extractions flagged\n- Single character OCR errors do not trigger fraud alerts"}'
```
