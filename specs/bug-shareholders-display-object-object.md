# Bug Plan: Shareholders Display Shows [object Object]

**Date**: 2025-12-22
**Module**: Risk / Fraud Detection / Document Extraction
**Severity**: Medium
**Type**: UI Display Bug

## Bug Description

When extracting the composicion accionaria data using the risk module documents feature, the shareholders field displays as:
```
shareholders: [object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object]
```

Instead of showing the actual shareholder names and details.

## Root Cause Analysis

### Primary Issue Location
**File**: `frontend/src/components/risk/FKDocumentUploader.tsx`
**Line**: 239

```typescript
const renderExtractedData = (data: Record<string, unknown>) => {
  const displayFields = Object.entries(data).slice(0, 6);
  return (
    <Box sx={{ mt: 1, pl: 2 }}>
      {displayFields.map(([key, value]) => (
        <Typography key={key} variant="caption" display="block" color="text.secondary">
          <strong>{key.replace(/_/g, ' ')}:</strong> {String(value) || 'N/A'}  // <-- BUG
        </Typography>
      ))}
    </Box>
  );
};
```

The `String(value)` call on line 239 converts JavaScript arrays and objects to their string representation. For arrays of objects like shareholders, this results in `[object Object],[object Object]...` because:
1. `String([{name: "John"}, {name: "Jane"}])` calls `.toString()` on the array
2. Array's `.toString()` joins elements with commas
3. Each object element's `.toString()` returns `[object Object]`

### Secondary Issue Location
**File**: `frontend/src/components/risk/FKCrossValidationResults.tsx`
**Line**: 157

```typescript
<Typography variant="body2" sx={{ fontWeight: 500 }}>
  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
</Typography>
```

This component attempts to handle objects with `JSON.stringify()`, but the output is raw JSON which is not user-friendly for display.

### Data Structure Reference
**File**: `backend/src/core/servicios/risk/document_extraction_service.py`

The `shareholders` field schema shows it's an array of objects:
```python
"shareholders": {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "id_number": {"type": ["string", "null"]},
            "shares": {"type": ["number", "null"]},
            "percentage": {"type": ["number", "null"]},
            "is_legal_representative": {"type": ["boolean", "null"]}
        }
    }
}
```

## Implementation Plan

### Task 1: Create Value Formatter Utility Function
**File**: `frontend/src/components/risk/FKDocumentUploader.tsx`

Add a utility function to format different value types for display:

```typescript
// Format value for display based on type
const formatValueForDisplay = (value: unknown): string => {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return 'N/A';
    }
    // Check if array of objects (like shareholders)
    if (typeof value[0] === 'object' && value[0] !== null) {
      return value.map((item, idx) => {
        // Try to get a meaningful name/identifier from the object
        const name = item.name || item.nombre || item.razon_social || `Item ${idx + 1}`;
        const percentage = item.percentage || item.porcentaje;
        if (percentage !== undefined) {
          return `${name} (${percentage}%)`;
        }
        return name;
      }).join(', ');
    }
    // Array of primitives
    return value.join(', ');
  }

  if (typeof value === 'object') {
    // Single object - extract key info
    const obj = value as Record<string, unknown>;
    const name = obj.name || obj.nombre || obj.razon_social;
    if (name) {
      return String(name);
    }
    return JSON.stringify(value);
  }

  return String(value);
};
```

### Task 2: Update renderExtractedData in FKDocumentUploader
**File**: `frontend/src/components/risk/FKDocumentUploader.tsx`
**Line**: 232-249

Replace the current `renderExtractedData` function:

```typescript
// Render extracted data preview
const renderExtractedData = (data: Record<string, unknown>) => {
  const displayFields = Object.entries(data).slice(0, 6);

  return (
    <Box sx={{ mt: 1, pl: 2 }}>
      {displayFields.map(([key, value]) => (
        <Typography key={key} variant="caption" display="block" color="text.secondary">
          <strong>{key.replace(/_/g, ' ')}:</strong> {formatValueForDisplay(value)}
        </Typography>
      ))}
      {Object.keys(data).length > 6 && (
        <Typography variant="caption" color="text.secondary">
          ... y {Object.keys(data).length - 6} campos más
        </Typography>
      )}
    </Box>
  );
};
```

### Task 3: Update Value Display in FKCrossValidationResults
**File**: `frontend/src/components/risk/FKCrossValidationResults.tsx`
**Line**: 136-166

Add the same formatter utility and update `renderValuesComparison`:

```typescript
// Format value for display based on type
const formatValueForDisplay = (value: unknown): string => {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return 'N/A';
    }
    if (typeof value[0] === 'object' && value[0] !== null) {
      return value.map((item, idx) => {
        const name = item.name || item.nombre || item.razon_social || `Item ${idx + 1}`;
        const percentage = item.percentage || item.porcentaje;
        if (percentage !== undefined) {
          return `${name} (${percentage}%)`;
        }
        return name;
      }).join(', ');
    }
    return value.join(', ');
  }

  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    const name = obj.name || obj.nombre || obj.razon_social;
    if (name) {
      return String(name);
    }
    return JSON.stringify(value);
  }

  return String(value);
};

// Update the TableCell to use formatter
<TableCell>
  <Typography variant="body2" sx={{ fontWeight: 500 }}>
    {formatValueForDisplay(value)}
  </Typography>
</TableCell>
```

### Task 4: Optional - Extract Shared Utility
**File**: `frontend/src/utils/formatters.ts` (new file, optional)

If the formatter is needed in more places, extract to a shared utility:

```typescript
/**
 * Format extracted document values for display
 * Handles arrays, objects, and primitives appropriately
 */
export const formatExtractedValue = (value: unknown): string => {
  // Implementation as above
};
```

Then import in both components.

## Testing Checklist

1. [ ] Upload a composicion accionaria document with multiple shareholders
2. [ ] Verify shareholders display as "Name 1 (X%), Name 2 (Y%), ..." in document preview
3. [ ] Run cross-validation and verify shareholder data displays correctly in results
4. [ ] Test with other document types (financial statements, RUT, cedula) to ensure no regressions
5. [ ] Test edge cases: empty arrays, null values, single shareholder
6. [ ] Run ESLint to ensure no unused imports or type errors

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/components/risk/FKDocumentUploader.tsx` | Modify | Add formatter, update renderExtractedData |
| `frontend/src/components/risk/FKCrossValidationResults.tsx` | Modify | Add formatter, update renderValuesComparison |
| `frontend/src/utils/formatters.ts` | Create (optional) | Shared formatter utility |

## Estimated Impact

- **Risk**: Low - UI-only change, no backend modifications
- **Scope**: 2 component files
- **Testing**: Manual verification with document uploads

## Notes

- The formatter should handle both English (`name`, `percentage`) and Spanish (`nombre`, `porcentaje`) field names since documents may use either
- Consider truncating very long shareholder lists with "... and X more" for better UX
- Future enhancement: Add tooltip or modal to show full shareholder details on click
