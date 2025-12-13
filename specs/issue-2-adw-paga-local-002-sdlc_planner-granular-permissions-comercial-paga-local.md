# Feature: Granular Permissions for Commercial Team - Paga Local Only Access

## Feature Description
Implement a new granular role `comercial_paga_local` that grants Commercial team members limited access to create Paga Local Colombia contracts without exposing other Operations module features like Contratos Activos or Contratos Mexico. This feature introduces sub-module level permission control while leveraging the existing RBAC infrastructure.

## User Story
As a **Commercial team member** (role: comercial_paga_local)
I want to access **only the Paga Local Colombia** functionality
So that I can **create Paga Local contracts for clients without having access to other contract types or approval workflows**

## Problem Statement
The current permission system operates at the module level, where the `operations` role grants full access to the entire Operations module. This creates a problem for Commercial team users who need to create Paga Local contracts but should not have access to:
- Contratos Activos (Activos Colombia)
- Contratos Mexico
- Legal review queue (they cannot approve their own contracts)

There is no mechanism to grant partial access to specific sub-modules within Operations.

## Solution Statement
Implement a new `comercial_paga_local` role that:
1. Extends the existing RBAC system without breaking current role-based access
2. Grants access only to Paga Local Colombia endpoints (both backend and frontend)
3. Filters sidebar/navigation to show only permitted menu items
4. Prevents access to Contratos Activos, Contratos Mexico, and Legal review

The implementation leverages the existing `require_roles()` dependency factory pattern in the backend and `RoleProtectedRoute` component in the frontend.

## Access Control
- **Required Role(s)**: `comercial_paga_local`, `admin` (admin bypass always applies)
- **Backend Protection**: Create new RBAC dependency `require_paga_local_role` that accepts `['comercial_paga_local', 'operations']`
- **Frontend Protection**: Update `RoleProtectedRoute` on `/operations/paga-local-colombia` route to include `comercial_paga_local` role

## Relevant Files
Use these files to implement the feature:

### Backend Files
- `backend/src/interface/auth_dtos.py` - Add `comercial_paga_local` to role documentation string (line 22)
- `backend/src/adapter/rest/rbac_dependencies.py` - Add new RBAC dependency `require_paga_local_role` for Paga Local endpoints
- `backend/src/adapter/rest/operations_routes.py` - Update Paga Local endpoints to use new RBAC dependency (or keep using `require_operations_role` but add `comercial_paga_local` to the allowed roles list)

### Frontend Files
- `frontend/src/types/index.ts` - Add `comercial_paga_local` to `UserRole` type (lines 70-95)
- `frontend/src/components/ui/FKSidebar.tsx` - Update `hasAccessToDepartment()` function to handle new role (lines 132-151)
- `frontend/src/components/RoleProtectedRoute.tsx` - No changes needed (already supports role arrays)
- `frontend/src/App.tsx` - Update route protection for Paga Local route (line 84)

### Database Files
- `backend/database/` - Create migration to document the new role value (if using enum) or verify the role column accepts string values

### E2E Test Files
- `.claude/commands/test_e2e.md` - E2E test runner documentation
- `.claude/commands/e2e/test_login.md` - Example E2E test for reference

### New Files
- `.claude/commands/e2e/test_comercial_paga_local_permissions.md` - E2E test validating permission restrictions for the new role

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] **CRUD Operations (basic data management)** → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `user_profiles.role` | `string` | Direct column access | `userProfile.role === 'comercial_paga_local'` |
| `require_roles()` | `dict` | Returns user dict | `user['role']`, `user['id']` |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs - role is a string field, not a DB enum
- [ ] Will verify user_profiles.role column accepts new string value
- [ ] No template file needed (not document generation)
- [ ] Country-specific data handled - This is Colombia-specific only

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `userProfile.role` | `user_profiles.role` | `string` | Snake_case in both |
| `UserRole.COMERCIAL_PAGA_LOCAL` | `'comercial_paga_local'` | `string` | Constant mapping |

## Implementation Plan

### Phase 1: Foundation
- Add the new role to type definitions (TypeScript and Python documentation)
- Verify database accepts new role string value
- Create RBAC dependency for Paga Local endpoints

### Phase 2: Core Implementation
- Update backend RBAC to allow `comercial_paga_local` role on Paga Local endpoints
- Update frontend type definitions
- Update sidebar navigation filtering logic

### Phase 3: Integration
- Update route protection in App.tsx
- Restrict access to other Operations routes for `comercial_paga_local` users
- Test complete flow with new role

## Step by Step Tasks

### Task 1: Add `comercial_paga_local` to Frontend TypeScript Types

Update `frontend/src/types/index.ts`:
- Add `'comercial_paga_local'` to the `UserRole` type union (after line 81)
- Add `COMERCIAL_PAGA_LOCAL: 'comercial_paga_local' as const` to `UserRole` constant object (after line 94)

### Task 2: Update Backend Role Documentation

Update `backend/src/interface/auth_dtos.py`:
- Update the role field description string to include `comercial_paga_local` in the list of valid roles (line 22)

### Task 3: Create New RBAC Dependency for Paga Local

Update `backend/src/adapter/rest/rbac_dependencies.py`:
- Add new pre-configured dependency at the bottom:
```python
require_paga_local_role = require_roles(['operations', 'comercial_paga_local'])
```

### Task 4: Update Paga Local Backend Endpoints to Accept New Role

Update `backend/src/adapter/rest/operations_routes.py`:
- Import the new `require_paga_local_role` dependency
- Replace `require_operations_role` with `require_paga_local_role` on these Paga Local-related endpoints:
  - `/contracts/solicitud-desembolso/parse-cotizacion` (line 184)
  - `/contracts/solicitud-desembolso/generate` (line 251)
  - `/contracts/instruccion-mandato/parse-cotizacion` (line 594)
  - `/contracts/instruccion-mandato/parse-bank-certificate` (line 658)
  - `/contracts/instruccion-mandato/generate` (line 727)
  - `/contracts/dian-mandato/parse-cotizacion` (line 838)
  - `/contracts/dian-mandato/generate` (line 900)
  - The approved contracts download endpoints should also be accessible for `comercial_paga_local` to view their submitted contracts (after approval)

### Task 5: Update Frontend Sidebar Navigation

Update `frontend/src/components/ui/FKSidebar.tsx`:
- Modify the `hasAccessToDepartment()` function to handle the new role
- Add logic: `comercial_paga_local` role should have access to `operations` department
- The sidebar will show Operations department, but route-level protection will limit actual access

### Task 6: Update Route Protection in App.tsx

Update `frontend/src/App.tsx`:
- Add `RoleProtectedRoute` to the Paga Local Colombia route (line 84)
- Allowed roles: `['operations', 'comercial_paga_local']`
- Ensure Contratos Colombia and Contratos Mexico routes have explicit `operations` only protection

### Task 7: Add RoleProtectedRoute to Contratos Colombia Route

Update `frontend/src/App.tsx`:
- Wrap `/operations/contratos-colombia` with `RoleProtectedRoute` allowing only `['operations']`
- This prevents `comercial_paga_local` users from accessing Contratos Activos

### Task 8: Add RoleProtectedRoute to Contratos Mexico Route

Update `frontend/src/App.tsx`:
- Wrap `/operations/contratos-mexico` with `RoleProtectedRoute` allowing only `['operations']`
- This prevents `comercial_paga_local` users from accessing Contratos Mexico

### Task 9: Create E2E Test for Granular Permissions

Create `.claude/commands/e2e/test_comercial_paga_local_permissions.md`:
- Test that a user with `comercial_paga_local` role:
  1. Can access Paga Local Colombia page
  2. Cannot access Contratos Colombia page (should see "Acceso Denegado")
  3. Cannot access Contratos Mexico page (should see "Acceso Denegado")
  4. Cannot access Legal dashboard
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for format reference

### Task 10: Run Validation Commands

Execute all validation commands to ensure zero regressions:
- Backend tests
- Backend linting
- Frontend linting
- TypeScript type check
- Frontend build

## Testing Strategy

### Unit Tests
- **Backend**: Test `require_paga_local_role` dependency returns 403 for unauthorized roles
- **Backend**: Test that `comercial_paga_local` user can access Paga Local endpoints
- **Frontend**: No new unit tests needed (leveraging existing RoleProtectedRoute tests)

### Edge Cases
1. **Admin bypass**: Admin users should still access all routes
2. **Role transition**: User changing from `operations` to `comercial_paga_local` should lose Contratos access
3. **Direct URL access**: `comercial_paga_local` user typing `/operations/contratos-colombia` directly should see "Acceso Denegado"
4. **API direct access**: Backend should return 403 for unauthorized API calls

## Acceptance Criteria
- [ ] New `comercial_paga_local` role exists in TypeScript types (`UserRole`)
- [ ] New `comercial_paga_local` role documented in backend DTOs
- [ ] Users with `comercial_paga_local` role can access Paga Local Colombia page
- [ ] Users with `comercial_paga_local` role can call Paga Local API endpoints
- [ ] Users with `comercial_paga_local` role see "Acceso Denegado" when accessing Contratos Colombia
- [ ] Users with `comercial_paga_local` role see "Acceso Denegado" when accessing Contratos Mexico
- [ ] Users with `comercial_paga_local` role cannot access Legal dashboard
- [ ] Admin users retain full access to all Operations routes
- [ ] Existing `operations` role users retain full Operations access
- [ ] Sidebar shows Operations department for `comercial_paga_local` users
- [ ] All validation commands pass with zero errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend tests
cd backend && python -m pytest

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

After creating E2E test file:
- Read `.claude/commands/test_e2e.md`
- Execute `.claude/commands/e2e/test_comercial_paga_local_permissions.md` to validate permissions

## Notes

### No Database Migration Required
The `user_profiles.role` column is a string/text field (not an enum), so new role values are automatically accepted. A database migration is NOT required.

### Backward Compatibility
- Existing `operations` role users are unaffected
- All existing routes continue to work
- Admin bypass behavior is preserved

### Future Extensions
This pattern can be extended for other granular roles:
- `comercial_activos`: Access only to Contratos Activos
- `comercial_mexico`: Access only to Contratos Mexico
- Each sub-module can have its own specific role as needed

### Role Assignment
Users must be assigned the `comercial_paga_local` role in the `user_profiles` table. This is typically done by an admin through:
1. Supabase dashboard (direct database edit)
2. Future: Admin user management interface

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (Task 9)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] No country-specific variations needed (CO-only feature)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (Task 9)
