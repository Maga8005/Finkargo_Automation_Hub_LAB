# Patch: Always Show Domain Validation Status in Email Chain

## Metadata
adw_id: `ec3ddef5`
review_change_request: `when validating emails from email chain, always check domain existence and age and show status, even if it does not raise an alert. If the domain checks out regarding existence and age, it can be shown in green status, not raising an alert`

## Issue Summary
**Original Spec:** specs/issue-36-adw-ec3ddef5-sdlc_planner-fraud-risk-module-fixes.md
**Issue:** The `_validate_domain_age` method in `email_chain_service.py` only returns a discrepancy object when the domain is problematic (doesn't exist, or is too new). When a domain is valid and aged appropriately, the method returns `None`, so no status is shown to the user. The request is to always display domain validation status, including a positive green status when the domain checks out.
**Solution:** Add a new INFO severity level to `DiscrepancySeverity` enum and modify `_validate_domain_age` to always return a discrepancy object - with INFO severity when the domain is valid (exists and age > 1 year), showing the validation results in green status.

## Files to Modify
Use these files to implement the patch:

- `backend/src/interface/risk_dtos.py` - Add `INFO` severity level to `DiscrepancySeverity` enum
- `backend/src/core/servicios/risk/email_chain_service.py` - Modify `_validate_domain_age` to always return domain status
- `frontend/src/types/risk.ts` - Add `info` severity to `DiscrepancySeverity` type and `DISCREPANCY_SEVERITY_CONFIG`
- `frontend/src/components/risk/FKEmailChainUploader.tsx` - Update rendering to show INFO severity discrepancies with green/success styling

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add INFO severity to backend DiscrepancySeverity enum
- Edit `backend/src/interface/risk_dtos.py`
- Add `INFO = "info"` to the `DiscrepancySeverity` enum (at the beginning, before LOW)

```python
class DiscrepancySeverity(str, Enum):
    """Severity level of cross-validation discrepancy"""
    INFO = "info"    # Add this line - informational, no issue detected
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### Step 2: Modify `_validate_domain_age` to always return status
- Edit `backend/src/core/servicios/risk/email_chain_service.py`
- Modify the `_validate_domain_age` method (lines 758-842)
- Instead of returning `None` for valid domains, return an INFO severity discrepancy with positive status information

At the end of the method (around line 841), instead of `return None`, add:

```python
        # Domain exists and is old enough - return positive status (INFO severity)
        return {
            'field': 'domain_age',
            'email_value': domain,
            'document_value': None,
            'severity': DiscrepancySeverity.INFO.value,
            'description': (
                f"Dominio '{domain}' verificado correctamente. "
                f"Existe y tiene {age_result.age_days if age_result.age_days else 'más de 1 año de'} días de antigüedad."
                if age_result.lookup_status == 'success' and age_result.age_days is not None
                else f"Dominio '{domain}' existe (DNS verificado). Antigüedad no disponible."
            ),
            'is_typosquatting': False,
            'similarity_score': None,
            'domain_age_days': age_result.age_days if age_result.lookup_status == 'success' else None,
            'domain_exists': True,
            'domain_creation_date': age_result.creation_date.isoformat() if age_result.creation_date else None,
            'domain_registrar': age_result.registrar if age_result.lookup_status == 'success' else None,
        }
```

### Step 3: Add INFO severity to frontend types
- Edit `frontend/src/types/risk.ts`
- Add `info` to the `DiscrepancySeverity` type union
- Add `info` configuration to `DISCREPANCY_SEVERITY_CONFIG`

Find and update the type:
```typescript
export type DiscrepancySeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';
```

Add to `DISCREPANCY_SEVERITY_CONFIG`:
```typescript
export const DISCREPANCY_SEVERITY_CONFIG: Record<DiscrepancySeverity, { label: string; color: 'success' | 'warning' | 'error' | 'default'; bgColor: string; textColor: string }> = {
  info: {
    label: 'Info',
    color: 'success',
    bgColor: '#E0F7E6',
    textColor: '#2CA14D',
  },
  low: {
    // ... existing
  },
  // ... rest
};
```

### Step 4: Update validation result counting logic
- Edit `backend/src/core/servicios/risk/email_chain_service.py`
- In the `validate_email_chain` method (around line 236), add counting for INFO severity
- Ensure INFO discrepancies don't affect the overall validation status negatively

Add info_count:
```python
info_count = sum(1 for d in discrepancies if d['severity'] == DiscrepancySeverity.INFO.value)
```

Update the validation_result dict to include info_count:
```python
validation_result = {
    'total_discrepancies': len(discrepancies),
    'info_count': info_count,
    'critical_count': critical_count,
    'high_count': high_count,
    'medium_count': medium_count,
    'low_count': low_count,
    'discrepancies': discrepancies,
    'summary': summary,
    'validated_at': datetime.now(timezone.utc).isoformat(),
}
```

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && ./venv/bin/ruff check src/` - Run backend linting
2. `cd backend && python -m pytest -v --tb=short` - Run backend tests
3. `cd frontend && npm run lint` - Run frontend linting
4. `cd frontend && npx tsc --noEmit` - Run TypeScript type check
5. `cd frontend && npm run build` - Run frontend build

## Patch Scope
**Lines of code to change:** ~40
**Risk level:** low
**Testing required:** Manual validation of email chain domain check displaying green status for valid domains
