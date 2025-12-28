# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Finkargo Automation Hub** is an enterprise automation platform for Finkargo's business operations, built with a monorepo structure containing React frontend and FastAPI backend. The system automates legal contract generation, operations workflows, and financial reporting for Colombian logistics operations.

**Production URLs:**
- Frontend: https://finkargo-automation-hub.vercel.app/
- Backend API: https://api-sandbox.finkargo.com.co/fkhub/

## Core Architecture Principles

**CRITICAL**: All code MUST follow Clean Architecture and SOLID principles. Never violate these - refactoring will be required if not followed.

### Clean Architecture Layers

```
Frontend:  pages/ → components/ → services/ → api/
           (UI)     (Reusable)   (Logic)    (HTTP)

Backend:   adapter/rest/ → core/servicios/ → repositorio/ → database
           (Controllers)   (Business Logic)  (Data Access)
```

## Technology Stack

### Frontend (Current Versions)
- **React**: 19.1.1 + **TypeScript**: 5.9.3
- **Build Tool**: Vite 7.1.7
- **UI Library**: Material-UI 7.3.4 (Finkargo branded)
- **Routing**: React Router 7.9.3
- **Forms**: react-hook-form 7.64.0 (mandatory)
- **HTTP**: Axios 1.12.2 with interceptors
- **Auth**: Supabase Client 2.58.0 (JWT-based)
- **Data Grid**: MUI Data Grid 7.29.11
- **Date Utils**: date-fns 4.1.0

### Backend (Current Versions)
- **Python**: 3.11.9-3.13.6 (Render uses 3.11.9)
- **FastAPI**: 0.104.1+
- **Server**: Uvicorn 0.24.0+
- **Validation**: Pydantic 2.5.2+
- **Database**: Supabase (PostgreSQL) via supabase-py 2.0.0+
- **ORM**: SQLAlchemy 2.0.23+ (minimal usage)
- **Migrations**: Alembic 1.12.1+
- **Document Processing**: PyMuPDF 1.23.0+, python-docx 1.0.0+
- **Data Processing**: Pandas 2.0.0+

### Infrastructure
- **Database**: PostgreSQL (Supabase) with Row Level Security
- **Auth**: Supabase Auth with JWT tokens
- **Storage**: Supabase Storage (PDFs, RUTs)
- **Frontend Hosting**: Vercel (auto-deploy from GitHub)
- **Backend Hosting**: Render (auto-deploy from GitHub)

## Development Commands

### Frontend Development

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Development server (http://localhost:5175)
npm run dev

# Production build
npm run build  # Runs: tsc -b && vite build

# Lint code
npm run lint

# Preview production build
npm run preview
```

**Important Frontend Notes:**
- Dev server runs on port 5175 (strict)
- Path alias: `@/` → `src/`
- HMR (Hot Module Replacement) enabled
- Output directory: `dist/`

### Backend Development

```bash
# Navigate to backend
cd backend

# Create virtual environment (first time)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Development server (http://localhost:8003)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8003

# Production server (Render command)
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Important Backend Notes:**
- API routes prefixed with `/api`
- Auto-generated docs at `/docs` (Swagger UI)
- Health check endpoint: `/api/health`
- Backend runs on port 8003

### Testing Commands

**Backend Testing:**
```bash
cd backend
pytest tests/
```

**Current Testing State:**
- Backend: pytest configured, minimal test coverage
- Frontend: No testing framework configured yet
- Test file exists: `backend/test_document_generation.py`
- Need to expand coverage for services and API endpoints

## Project Structure

### Frontend Structure

```
frontend/src/
├── api/clients/              # Axios HTTP clients with auth interceptors
├── components/
│   ├── forms/                # FK-prefixed form components
│   │   ├── FKContractRequest.tsx
│   │   ├── FKClientDataImport.tsx
│   │   └── FKReviewQueue.tsx
│   ├── ui/                   # FK-prefixed reusable UI
│   │   ├── FKMainLayout.tsx
│   │   ├── FKSidebar.tsx
│   │   └── FKTopNavbar.tsx
│   ├── declaraciones/        # Module-specific components
│   ├── ProtectedRoute.tsx    # Authentication guard
│   └── RoleProtectedRoute.tsx # Authorization guard
├── contexts/
│   └── AuthContext.tsx       # Global auth state (Context API)
├── hooks/
│   └── useAuth.ts            # Authentication hook
├── pages/
│   ├── legal/                # Legal module pages
│   ├── operations/           # Operations module pages
│   ├── finance/              # Finance module pages
│   ├── LoginPage.tsx
│   └── HomePage.tsx
├── services/                 # Business logic services
│   ├── supabase.ts
│   ├── legalService.ts
│   └── operationsService.ts
├── types/                    # TypeScript types
│   ├── index.ts              # Core types
│   └── legal.ts              # Legal-specific types
├── theme/
│   └── theme.ts              # Finkargo brand theme
└── App.tsx                   # Root component with routing
```

### Backend Structure

```
backend/src/
├── adapter/rest/             # FastAPI routes (API layer)
│   ├── legal_routes.py       # Legal department endpoints
│   ├── operations_routes.py  # Operations endpoints
│   ├── auth_routes.py        # Authentication endpoints
│   ├── dependencies.py       # Dependency injection
│   └── rbac_dependencies.py  # Role-based access control
├── core/servicios/           # Business logic (Core layer)
│   ├── contract_service.py   # Contract generation logic
│   ├── document_service.py   # Document processing
│   ├── csv_template_mapper.py # CSV to template mapping
│   └── rut_parser_service.py # Tax ID parsing
├── repositorio/              # Data access (Repository layer)
│   ├── contract_repository.py # Contract CRUD
│   ├── client_repository.py   # Client data access
│   └── template_repository.py # Template management
├── interface/                # DTOs (Data Transfer Objects)
│   ├── legal_dtos.py
│   └── auth_dtos.py
├── config/                   # Configuration
│   ├── settings.py           # Pydantic settings
│   └── supabase_config.py    # Supabase client init
└── models/                   # SQLAlchemy models (minimal)
```

## Code Standards (Non-Negotiable)

### TypeScript Standards
- **Component Naming**: Business/form components MUST use `FK` prefix (e.g., `FKContractForm.tsx`)
- **Type Coverage**: 100% TypeScript, NO `any` types in production
- **Imports**: Use `@/` alias for absolute imports
- **File Naming**: PascalCase for components, camelCase for utilities

### Python Standards
- **Type Hints**: Required on all functions
- **Docstrings**: Required for all public APIs
- **Clean Architecture**: Strict layer separation (adapter → core → repositorio)
- **Error Handling**: Structured exceptions with proper HTTP status codes

### Component Standards
- **Forms**: Always use react-hook-form with Material-UI
- **State**: Context API for global, useState for local, useReducer for complex
- **API Calls**: Use service layer, never direct axios in components
- **Auth**: Use `useAuth()` hook, `ProtectedRoute` and `RoleProtectedRoute` components

## API Endpoints

### Base URLs
- **Development**: `http://localhost:8003/api`
- **Production**: `https://api-sandbox.finkargo.com.co/fkhub`

### Authentication Headers
All API requests to the production endpoint must include:
- `x-api-key`: Required API key for Finkargo API Gateway
- `Authorization`: Bearer token from Supabase authentication (for user-specific requests)

### Key Endpoints

**Health & Utils:**
- `GET /api/health` - Health check
- `GET /api/departments` - Department list
- `GET /api/debug/cors` - CORS debug info

**Authentication** (`auth_routes.py`):
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Current user profile

**Legal Module** (`legal_routes.py`):
- `GET /api/legal/clients` - List clients
- `GET /api/legal/clients/search?nit=<NIT>` - Search by tax ID
- `POST /api/legal/clients/import` - Import from CSV/Excel
- `POST /api/legal/contracts/generate` - Generate contract
- `GET /api/legal/contracts/{id}` - Contract details
- `PUT /api/legal/contracts/{id}/review` - Review (approve/reject)
- `GET /api/legal/contracts/pending-review` - Pending queue
- `GET /api/legal/contracts` - History with filters
- `GET /api/legal/contracts/stats` - Statistics
- `GET /api/legal/templates/active` - Active template

**Operations Module** (`operations_routes.py`):
- `GET /api/operations/dashboard` - Dashboard data
- `GET /api/operations/imports` - Import history
- `POST /api/operations/imports/validate` - Validate import

**API Documentation:**
- Swagger UI: http://localhost:8003/docs
- Auto-generated from FastAPI
- Interactive testing available

## Authentication & Authorization

### Authentication Flow (Supabase JWT)

```
1. User logs in via LoginPage
2. Calls supabase.auth.signInWithPassword()
3. Supabase returns JWT token + user object
4. Token auto-stored in localStorage
5. AuthContext fetches user_profiles from database
6. App renders with user context
```

### Frontend Auth Pattern

**Global Auth State:**
```typescript
// AuthContext provides:
interface AuthContextType {
  user: User | null;
  session: Session | null;
  userProfile: UserProfile | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
}
```

**Route Protection:**
```typescript
// Authentication required:
<ProtectedRoute>
  <DashboardPage />
</ProtectedRoute>

// Specific role(s) required:
<RoleProtectedRoute allowedRoles={['admin', 'legal']}>
  <LegalDashboard />
</RoleProtectedRoute>
```

### Backend Auth Pattern

**JWT Validation:**
```python
# dependencies.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate JWT and return user data"""
    token = credentials.credentials
    user = supabase_client.get_user_from_token(token)
    return user
```

**RBAC (Role-Based Access Control):**
```python
# rbac_dependencies.py
from rbac_dependencies import require_roles

@router.post("/contracts/generate")
async def generate_contract(
    current_user: dict = Depends(require_roles(['admin', 'legal']))
):
    # Only admins and legal users can access
    pass
```

**Available Roles:**
- `admin` - Full system access
- `legal` - Legal contract management
- `operations` - Operations workflows
- `mesa_control` - Control desk
- `commercial` - Sales operations
- `analyst` - Data analysis
- `manager` - Department supervision
- `user` - Basic authenticated user
- `cliente` - External client (limited access)

## Database

### Schema Location
`backend/database/` contains all SQL migrations and schema definitions.

### Core Tables

**Authentication:**
- `auth.users` (Supabase built-in)
- `user_profiles` - Extended user data with roles

**Legal Contracts:**
- `clients` - Imported client data (NIT, company info)
- `contract_templates` - Versioned templates
- `contract_generations` - Audit trail
- `contract_id_sequence` - Sequential ID generator (ACT-2025-001)
- `data_imports` - CSV/Excel import history

### Migration Workflow

**Apply migrations in order:**
1. `schema.sql` - Base schema
2. `migration_create_user_profiles.sql` - User profiles
3. `migration_add_legal_operations_roles.sql` - Roles
4. `migration_add_user_type.sql` - User types
5. `migration_add_contract_fields.sql` - Contract fields
6. `migration_add_otrosi_support.sql` - "Otrosi" type
7. `migration_add_inventario_bodega_support.sql` - Inventory type
8. `migration_add_approved_document_url.sql` - Document storage
9. `migration_allow_null_audit_fields.sql` - Audit flexibility
10. `migration_fix_user_profiles_rls.sql` - RLS fixes

**How to apply:**
1. Open Supabase SQL Editor
2. Execute migrations sequentially
3. Verify with: `SELECT tablename FROM pg_tables WHERE schemaname = 'public';`

### Row Level Security (RLS)

All tables have RLS enabled:
- Authenticated users can read most data
- Role-based write permissions
- Service role (backend) bypasses RLS

**Example Policy:**
```sql
CREATE POLICY "Authenticated users can read clients"
ON clients FOR SELECT
TO authenticated
USING (true);
```

## Finkargo Design System

### Color Palette

```css
/* Primary Colors */
--primary-darkest: #050A53;
--primary-dark: #0C147B;
--primary-main: #3C47D3;
--primary-light: #77A1E2;

/* Coral/CTA Colors */
--coral-main: #EB8774;
--coral-light: #F19F90;

/* Status Colors */
--success-bg: #E0F7E6;
--success-main: #2CA14D;
--error-bg: #FFE4E4;
--error-main: #CC071E;

/* Neutral Colors */
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-300: #D1D5DB;
--gray-400: #9CA3AF;
--gray-500: #6B7280;
--gray-600: #4B5563;
--gray-700: #374151;
--gray-800: #1F2937;
--gray-900: #111827;
```

### Component Specifications

- **Buttons**:
  - Large: 52px height, 8px border-radius
  - Medium: 44px height, 8px border-radius
  - Small: 36px height, 8px border-radius
- **Cards**: 8px border-radius, 24px padding
- **Inputs**: 48px height, 8px border-radius
- **Typography**: Epilogue font (400, 500, 600, 700)

### Responsive Breakpoints

```typescript
// MUI theme breakpoints
const breakpoints = {
  mobile: 0,      // 0px - 719px
  tablet: 720,    // 720px - 1023px
  desktop: 1024,  // 1024px+
};
```

## Environment Variables

### Frontend (.env)

```bash
# Supabase
VITE_SUPABASE_URL=https://[project-id].supabase.co
VITE_SUPABASE_ANON_KEY=[anon-key]

# API (Finkargo Production API)
VITE_API_URL=https://api-sandbox.finkargo.com.co/fkhub
VITE_API_KEY=pk_prod_PO1DbQCi8Z0TSiHHTCNtkA
VITE_API_TIMEOUT=30000

# App Settings
VITE_APP_NAME=Finkargo Automation Hub
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEBUG=false

# File Upload
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png,.xlsx,.xls

# Localization
VITE_DEFAULT_LOCALE=es-MX
VITE_DEFAULT_CURRENCY=MXN
```

### Backend (.env)

```bash
# App Settings
DEBUG=true
APP_NAME=Finkargo Automation Hub
PYTHON_VERSION=3.11.9  # CRITICAL for Render deployment

# Supabase
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_ANON_KEY=[anon-key]
SUPABASE_SERVICE_KEY=[service-key]
SUPABASE_JWT_SECRET=[jwt-secret]

# Security
SECRET_KEY=[generate-secret-key]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (MUST be JSON array format!)
CORS_ORIGINS=["http://localhost:5175","https://finkargo-automation-hub.vercel.app","https://*.vercel.app"]

# Database
DATABASE_URL=postgresql://[connection-string]

# File Upload
MAX_UPLOAD_SIZE=10485760
SUPPORTED_FILE_TYPES=[".pdf",".jpg",".jpeg",".png",".xlsx",".xls"]
```

## Deployment Configuration

### Vercel (Frontend)

**Configuration in `frontend/vercel.json`:**
```json
{
  "version": 2,
  "name": "finkargo-automation-hub",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**Vercel Dashboard Settings:**
- Root Directory: `frontend`
- Framework Preset: Vite
- Node Version: 18.x or 20.x
- Environment Variables: Set all `VITE_*` variables

### Render (Backend)

**Service Settings:**
- Environment: Python 3
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**CRITICAL Environment Variables:**
- `PYTHON_VERSION=3.11.9` - Required! (runtime.txt ignored with Root Directory)
- `CORS_ORIGINS` - MUST be JSON array: `["url1","url2"]`, NOT comma-separated

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature-description

# 2. Develop and test locally
npm run dev  # frontend
python -m uvicorn main:app --reload  # backend

# 3. Commit with conventional commits
git commit -m "feat: add new feature"
# Prefixes: feat, fix, docs, refactor, test, chore

# 4. Push to GitHub
git push origin feature-description

# 5. Auto-deploy
# - Vercel creates preview URL for frontend
# - Render deploys backend (if configured)

# 6. Merge to master for production deployment
```

## Common Deployment Issues

### Issue 1: Python Version Incompatibility
**Error**: Package build failures with Python 3.13
**Solution**: Set `PYTHON_VERSION=3.11.9` in Render environment variables

### Issue 2: CORS Errors
**Error**: "No 'Access-Control-Allow-Origin' header"
**Solution**:
- Ensure `CORS_ORIGINS` is JSON array format: `["url1","url2"]`
- Include Vercel preview pattern: `https://*.vercel.app`

### Issue 3: Vercel Build Path Errors
**Error**: "cd: frontend: No such file or directory"
**Solution**: When Root Directory is set, don't use `cd` in vercel.json

### Issue 4: Missing Dependencies
**Error**: ModuleNotFoundError during startup
**Solution**: Do comprehensive import analysis, add all packages to requirements.txt

### Issue 5: API URL Typo
**Error**: API calls going to wrong path
**Solution**: Verify `VITE_API_URL` ends with `/api` (NOT `/ap`)

## Language Guidelines

- **UI Text**: Spanish (all user-facing content)
- **Code**: English (variables, functions, comments)
- **Documentation**: Spanish for user docs, English for technical docs
- **Git Commits**: English (conventional format)

## Documentation Files

### Primary Docs (Project Root)
- `CLAUDE.md` - This file (Claude Code guidance)
- `TECHNICAL_INTEGRATION_BLUEPRINT.md` - Comprehensive integration guide
- `COLLABORATIVE_LOCAL_SETUP_GUIDE.md` - Developer onboarding
- `PROGRESS.md` - Development status tracker
- `SUPABASE_AUTH_DOCUMENTATION.md` - Auth deep-dive

### Implementation Notes
- `implementations/` - Feature implementation docs
- Format: `YYYYMMDD_feature_name.md`
- Recent: TypeScript fixes, missing dependencies, contract types

### Backend Guides
- `backend/CSV_IMPORT_GUIDE.md` - CSV/Excel import
- `backend/DEPLOYMENT_PDF_SETUP.md` - PDF generation setup
- `backend/OPERATIONS_WORKFLOW_GUIDE.md` - Operations module
- `backend/database/README.md` - Database setup

## Quick Reference

### Most Common Commands

```bash
# Start development
cd frontend && npm run dev  # Terminal 1
cd backend && python -m uvicorn main:app --reload  # Terminal 2

# Access points
# Frontend: http://localhost:5175
# Backend API: http://localhost:8003/api
# API Docs: http://localhost:8003/docs

# Build production
cd frontend && npm run build  # Creates dist/
```

### Key File Locations

**Frontend:**
- Routes: `frontend/src/App.tsx`
- Auth: `frontend/src/contexts/AuthContext.tsx`
- Theme: `frontend/src/theme/theme.ts`
- Services: `frontend/src/services/`

**Backend:**
- Main app: `backend/main.py`
- Routes: `backend/src/adapter/rest/`
- Services: `backend/src/core/servicios/`
- Repos: `backend/src/repositorio/`

**Database:**
- Migrations: `backend/database/migration_*.sql`
- Schema: `backend/database/schema.sql`

### Common Patterns

**Creating a New Form Component:**
```typescript
// frontend/src/components/forms/FKMyForm.tsx
import { useForm } from 'react-hook-form';
import { TextField, Button } from '@mui/material';

export const FKMyForm: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    // Call service layer
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <TextField
        {...register('fieldName', { required: 'Required' })}
        error={!!errors.fieldName}
        helperText={errors.fieldName?.message}
      />
      <Button type="submit">Submit</Button>
    </form>
  );
};
```

**Creating a Protected Route:**
```typescript
// In App.tsx
<Route path="/admin" element={
  <RoleProtectedRoute allowedRoles={['admin']}>
    <AdminPage />
  </RoleProtectedRoute>
} />
```

**Adding a Backend Endpoint:**
```python
# backend/src/adapter/rest/my_routes.py
from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..rbac_dependencies import require_roles

router = APIRouter(prefix="/api/my-module", tags=["My Module"])

@router.get("/data")
async def get_data(
    current_user: dict = Depends(require_roles(['admin', 'user']))
):
    """Get data - requires admin or user role"""
    # Call service layer
    return {"data": "example"}
```

## Notes for Claude Code

When working with this codebase:

1. **Architecture**: Follow Clean Architecture strictly (adapter → core → repositorio)
2. **Component Naming**: MUST use FK prefix for business/form components
3. **Type Safety**: NO `any` types - 100% TypeScript coverage required
4. **Environment Variables**:
   - Frontend: All prefixed with `VITE_`
   - Backend: `PYTHON_VERSION=3.11.9` is CRITICAL for Render
   - CORS MUST be JSON array format
5. **Deployment**:
   - Vercel for frontend (Root Directory: `frontend`)
   - Render for backend (Root Directory: `backend`)
   - Feature branch workflow with auto-deploy
6. **Testing**: Test locally before deploying (both servers running)
7. **Documentation**: Document major changes in `implementations/YYYYMMDD_feature.md`
8. **Logging**: Add logging to debug errors (as noted in project instructions)
9. **Forms**: ALWAYS use react-hook-form with Material-UI integration
10. **State**: Context API for global state, NOT Redux

This codebase is production-ready and battle-tested. Follow these patterns for consistent, maintainable code.
