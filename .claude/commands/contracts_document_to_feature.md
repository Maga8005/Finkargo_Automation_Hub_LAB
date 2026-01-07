# Contracts Document to Feature

Generate a complete implementation prompt for a new contract document type by analyzing the transcript, template, and example input file.

## Arguments
- `transcript_path`: Path to the transcript file (conversation explaining how the document is filled)
- `template_path`: Path to the Word template (.docx) with placeholders
- `example_file_path`: Path to an example input file (PDF/Excel) used to fill the template

## Usage
```
/contracts_document_to_feature <transcript_path> <template_path> <example_file_path>
```

## Workflow

Execute the following phases in order:

### Phase 1: Requirements Gathering

1. **Read the transcript** at `$ARGUMENTS[0]`
   - Identify all fields mentioned
   - Document business rules and conditions
   - Note data sources mentioned (external systems, databases, user input)
   - Capture any formulas or derivation logic

2. **Create Data Sources Document**
   - Create `docs/{YYYYMMDD}_{DOCUMENT_NAME}_DATA_SOURCES.md`
   - Organize fields by source: Database, External Document, System Generated, User Input, Derived
   - Document any mapping rules (e.g., keyword → value mappings)

### Phase 2: Technical Analysis

3. **Analyze the Word template** at `$ARGUMENTS[1]`
   - Use python-docx to extract all text content
   - Identify all placeholders (typically in `[brackets]` or `{{curly braces}}`)
   - Document table structures that need dynamic population
   - Note any repeated placeholders

4. **Analyze the example input file** at `$ARGUMENTS[2]`
   - For PDF: Use PyMuPDF (fitz) to extract text and identify data locations by page
   - For Excel: Use pandas to identify columns and data structure
   - Map extracted data to template placeholders
   - Document the file structure for parsing logic

5. **Review existing codebase patterns**
   - Check `backend/src/core/servicios/document_service.py` for similar handlers
   - Check `frontend/src/components/forms/` for similar form patterns
   - Check `backend/src/interface/legal_dtos.py` for existing DTOs
   - Identify the contract type enum value (e.g., `pl_co_solicitud_desembolso`)

### Phase 3: Implementation Planning

6. **Create Field Mapping Matrix**
   Document the complete mapping:
   ```
   | UI Field | Template Placeholder | Data Source | Extraction Logic |
   |----------|---------------------|--------------|------------------|
   ```

7. **Generate Implementation Prompt**
   Create `docs/{YYYYMMDD}_FEATURE_PROMPT_{DOCUMENT_NAME}_IMPLEMENTATION.md` with:

   - **Template Analysis Section**: All placeholders identified
   - **Example File Analysis Section**: Extracted data points and locations
   - **Feature Prompt Section**: Complete prompt for `/feature` command including:
     - Overview and current state
     - Backend requirements (parser service, DTOs, document handler, API endpoints)
     - Frontend requirements (form component, types, service methods)
     - Data flow diagram
     - Acceptance criteria
     - Files to create/modify

## Output Format

The command produces two documents:

### 1. Data Sources Document
```markdown
# {Document Name} - Data Sources

## Overview
{Description of the document and its purpose}

## Data Sources Summary
| Source | Description |
|--------|-------------|

## Field Mapping by Source
### From {External Document}
| Field | Example | Notes |

### From Database
| Field | Table.Column | Notes |

### System Generated
| Field | Logic | Notes |

### User Input
| Field | Input Type | Default |
```

### 2. Implementation Prompt Document
```markdown
# Feature Prompt: {Document Name} - Full Implementation

## Template Analysis
### Placeholders Identified
| Placeholder | Description | Source |

## Example File Analysis
### Extracted Data Points
| Field | Value in Example | Location |

## Feature Prompt for `/feature` Command
{Complete feature specification following the format in .claude/commands/feature.md}

## Data Flow Diagram
{ASCII diagram showing data flow}

## References
- Template: {path}
- Example: {path}
- Transcript: {path}
- Contract Type: {enum value}
- ID Prefix: {prefix}
```

## Example

```bash
/contracts_document_to_feature "docs/20251207 TRANSCRIPT SOLICITUD DE DESEMBOLSO.txt" "backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx" "Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf"
```

## Notes

- Always commit both generated documents to the repository
- Use feature branches for the documentation (e.g., `feature/{document-name}-documentation`)
- The implementation prompt can be used directly with the `/feature` command
- For complex documents with multiple input sources, create separate analysis sections for each
