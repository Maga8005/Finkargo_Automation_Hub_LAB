# Riesgos Module - Feature Prompts

These prompts are generated from the feedback meeting with Camila Perdomo (Mesa de Control) on December 29, 2025.

## Source Document

`Requirements_Meetings/Fraud Protection/Feedback Meetings/20251229 Feedback Camila Perdomo.txt`

## Execution Order

Execute these prompts in priority order using the `/feature` command:

### Priority 1 (High)

| ID | File | Description |
|----|------|-------------|
| BUG-001 | `BUG-001_email_extraction_errors.md` | Fix email domain extraction errors |
| ENH-001 | `ENH-001_discrepancy_validation_checkboxes.md` | Add individual discrepancy validation |

### Priority 2 (Medium)

| ID | File | Description |
|----|------|-------------|
| ENH-002 | `ENH-002_contador_revisor_fiscal_validation.md` | Add contador/revisor fiscal cross-validation |
| ENH-003 | `ENH-003_representative_signature_validation.md` | Add representative signature validation in financials |

## How to Use

Each prompt file contains:

1. **Full Issue JSON** - Detailed specification for the `/feature` command
2. **Quick Copy Command** - One-liner for quick execution

### Example Execution

```bash
# Generate a random ADW ID and execute
/feature 100 $(openssl rand -hex 4) '<issue_json>'

# Or with a specific issue number from GitHub
/feature 123 abc12345 '<issue_json>'
```

## Dependencies

### ENH-002 and ENH-003 Relationship

These two features can be combined into a single implementation since they both:
- Modify Estados Financieros extraction
- Add new cross-validation types
- Update the same UI components

Consider implementing them together to avoid duplicate work.

### BUG-001 Should Be First

BUG-001 (email extraction errors) should be fixed before implementing new extraction features, as it addresses fundamental extraction accuracy issues.

## Process Improvements (Not Code Features)

The following items from the meeting are process improvements, not code features:

- **PROC-001**: Email chain validation in credit committee workflow
- **PROC-002**: First operation email validation requirement

These require organizational process changes with Commercial team and Mesa de Control.

## Summary of All Requirements

| ID | Type | Priority | Status |
|----|------|----------|--------|
| BUG-001 | Bug Fix | High | Prompt Ready |
| ENH-001 | Enhancement | High | Prompt Ready |
| ENH-002 | Enhancement | Medium | Prompt Ready |
| ENH-003 | Enhancement | Medium | Prompt Ready |
| ENH-004 | Enhancement | Low | Not implemented (hide External Contacts tab) |
| PROC-001 | Process | High | Requires organizational change |
| PROC-002 | Process | Medium | Requires organizational change |

## Notes

- All prompts have been sanitized to remove special characters (accents) for shell compatibility
- The `/feature` command will generate the full spec documentation
- Each prompt contains both a detailed JSON and a quick copy command for convenience
