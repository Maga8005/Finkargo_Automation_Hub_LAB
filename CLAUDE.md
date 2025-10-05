# Finkargo Automation Hub - Project Template

## Project Overview
This template is based on the **Finkargo Pre-Approval System** architecture, UX/UI patterns, and deployment approach. Use this document to bootstrap a new Finkargo Automation Hub application with the same enterprise standards.

## Core Principles (Inherited from Base Template)
**CRITICAL**: All code MUST follow Clean Architecture and SOLID design principles. Never violate these principles - refactoring will be required if they are not followed.

## Technology Stack (Company Standard)

### Frontend
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0.8
- **Language**: TypeScript 5.2.2
- **UI Library**: Material-UI (MUI) v5
- **State Management**: useReducer for complex state, Context API for global state
- **Forms**: react-hook-form with Material-UI integration (mandatory)
- **HTTP Client**: Axios with interceptors
- **Authentication**: Supabase Auth with JWT
- **Routing**: React Router v6

### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11.9
- **Database**: PostgreSQL (via Supabase)
- **ORM**: SQLAlchemy 2.0.23
- **Migrations**: Alembic 1.12.1
- **Authentication**: Supabase + JWT with role-based access control
- **Validation**: Pydantic 2.5.2 with pydantic-settings 2.1.0

### Deployment Stack
- **Frontend Hosting**: Vercel.com
- **Backend Hosting**: Render.com
- **Database**: Supabase (PostgreSQL + Auth)
- **Version Control**: GitHub with feature branch workflow

## Enterprise Project Structure

### Frontend Architecture
```
frontend/
├── src/
│   ├── api/
│   │   └── clients/           # HTTP clients with interceptors
│   ├── components/
│   │   ├── forms/             # FK-prefixed form components
│   │   └── ui/                # FK-prefixed reusable components
│   ├── hooks/                 # Custom hooks (useAuth, useAPI, etc.)
│   ├── store/
│   │   └── reducers/          # useReducer implementations
│   ├── services/              # Business logic services
│   ├── types/                 # TypeScript interfaces and domain models
│   ├── utils/                 # Utility functions
│   ├── pages/                 # Application routes
│   └── App.tsx
├── public/
├── .env                       # Local environment variables
├── .env.example               # Template for environment variables
├── package.json
├── tsconfig.json
├── vite.config.ts
└── vercel.json                # Vercel deployment config
```

### Backend Architecture
```
backend/
├── src/
│   ├── adapter/
│   │   └── rest/              # FastAPI controllers and routes
│   ├── core/
│   │   └── servicios/         # Business logic services
│   ├── repositorio/           # Data access layer with docstrings
│   ├── interface/             # DTOs and contracts
│   ├── models/                # SQLAlchemy models
│   └── config/                # Application configuration
├── alembic/                   # Database migrations
├── .env                       # Local environment variables
├── .env.example               # Template for environment variables
├── requirements.txt
├── runtime.txt                # Python version (python-3.11.9)
└── main.py                    # FastAPI application entry
```

## Code Standards (Non-negotiable)

### TypeScript Standards
- **Component Naming**: All form/business components must start with FK prefix (e.g., `FKAutomationForm.tsx`)
- **Type Coverage**: 100% TypeScript coverage, no `any` types in production code
- **Imports**: Absolute imports from `@/` alias
- **File Naming**: PascalCase for components, camelCase for utilities

### Python Standards
- **Type Hints**: All functions must have type hints
- **Docstrings**: Comprehensive docstrings for all public APIs
- **Clean Architecture**: Clear separation of concerns (adapter → core → repositorio)
- **Error Handling**: Structured exceptions with proper HTTP status codes

### Component Standards
- **Forms**: Always use react-hook-form with Material-UI
- **API Calls**: Use custom hooks (useAPI, useQuery pattern)
- **State**: useReducer for complex state, useState for simple state
- **Error Boundaries**: Wrap major sections in error boundaries

## UI Design System (Finkargo Brand)

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
- **Typography**: Epilogue font (weights: 400, 500, 600, 700)

### Responsive Breakpoints
```typescript
// Use these breakpoints in MUI theme
const breakpoints = {
  mobile: 0,      // 0px - 719px
  tablet: 720,    // 720px - 1023px
  desktop: 1024,  // 1024px+
};
```

## Language Guidelines
- **UI Text**: Spanish (all user-facing content)
- **Code**: English (variables, functions, comments)
- **Documentation**: Spanish for user docs, English for technical docs
- **Git Commits**: English

## Environment Variables

### Frontend (.env)
```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://[project-id].supabase.co
VITE_SUPABASE_ANON_KEY=[anon-key]

# API Configuration
VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000

# Application Settings
VITE_APP_NAME=Finkargo Automation Hub
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEBUG=false
VITE_ENABLE_ANALYTICS=false

# File Upload Settings
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png,.xlsx,.xls

# Localization
VITE_DEFAULT_LOCALE=es-MX
VITE_DEFAULT_CURRENCY=MXN
```

### Backend (.env)
```bash
# Application Settings
DEBUG=true
APP_NAME=Finkargo Automation Hub
PYTHON_VERSION=3.11.9

# Supabase Configuration
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_ANON_KEY=[anon-key]
SUPABASE_SERVICE_KEY=[service-key]
SUPABASE_JWT_SECRET=[jwt-secret]

# Security
SECRET_KEY=[generate-secret-key]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (JSON array format required!)
CORS_ORIGINS=["http://localhost:5173","https://your-app.vercel.app"]

# Database (provided by Supabase)
DATABASE_URL=postgresql://[connection-string]

# File Upload
MAX_UPLOAD_SIZE=10485760
SUPPORTED_FILE_TYPES=[".pdf",".jpg",".jpeg",".png",".xlsx",".xls"]

# External APIs (if needed)
# Add your automation service APIs here
```

## Deployment Configuration

### Vercel Configuration (vercel.json)
```json
{
  "version": 2,
  "name": "finkargo-automation-hub",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**Important Vercel Settings**:
- **Root Directory**: `frontend`
- **Framework Preset**: Vite
- **Node Version**: 18.x or 20.x
- **Environment Variables**: Set all `VITE_*` variables in Vercel dashboard

### Render Configuration

**Service Settings**:
- **Environment**: Python 3
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: Set `PYTHON_VERSION=3.11.9` in environment variables

**Critical Render Notes**:
- Use environment variable `PYTHON_VERSION=3.11.9` (runtime.txt is ignored with Root Directory setting)
- CORS_ORIGINS MUST be JSON array format: `["url1","url2"]`, NOT comma-separated string
- Include both production and preview Vercel URLs in CORS_ORIGINS

### GitHub Workflow
1. Create feature branch: `feature-[brief-description]`
2. Develop and test locally
3. Commit with descriptive messages
4. Push to GitHub
5. Vercel auto-deploys from feature branch
6. Render deploys from same branch (or configure separate branch)

## Required Dependencies

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "@mui/material": "^5.14.20",
    "@mui/icons-material": "^5.14.19",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0",
    "react-hook-form": "^7.49.2",
    "axios": "^1.6.2",
    "@supabase/supabase-js": "^2.39.0",
    "date-fns": "^3.0.6"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0"
  }
}
```

### Backend (requirements.txt)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pydantic==2.5.2
pydantic-settings==2.1.0
email-validator==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.24.1
pytest==7.4.3
pytest-asyncio==0.21.1
python-dotenv==1.0.0
supabase==2.3.0
gotrue==2.1.0
postgrest==0.13.0
realtime==1.0.2
storage3==0.6.1

# Add automation-specific packages here
# celery==5.3.4  # If using task queue
# redis==5.0.1   # If using Redis
```

## Development Workflow

### Initial Setup
```bash
# 1. Create project structure
mkdir finkargo-automation-hub && cd finkargo-automation-hub
mkdir frontend backend

# 2. Initialize frontend
cd frontend
npm create vite@latest . -- --template react-ts
npm install

# 3. Initialize backend
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Setup Supabase
# - Create new project at supabase.com
# - Copy connection details
# - Update .env files

# 5. Initialize Git
cd ..
git init
git checkout -b feature-initial-setup
```

### Local Development
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev

# Access app at http://localhost:5173
# API docs at http://localhost:8000/api/docs
```

## Deployment Steps

### Step 1: Deploy Backend to Render
1. Create new Web Service on Render
2. Connect GitHub repository
3. Configure:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables (PYTHON_VERSION=3.11.9 is critical!)
5. Deploy and verify at `https://your-service.onrender.com/api/health`

### Step 2: Deploy Frontend to Vercel
1. Import project on Vercel
2. Configure:
   - Root Directory: `frontend`
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
3. Set all `VITE_*` environment variables
4. Set `VITE_API_URL` to Render backend URL
5. Deploy and verify

### Step 3: Configure CORS
1. Go to Render → Environment Variables
2. Update `CORS_ORIGINS` to JSON array:
   ```json
   ["http://localhost:5173","https://your-app.vercel.app","https://*.vercel.app"]
   ```
3. Redeploy backend

### Step 4: Verify Deployment
- [ ] Frontend loads without errors
- [ ] Backend health check responds
- [ ] API calls succeed (no CORS errors)
- [ ] Authentication works
- [ ] Database operations work

## Common Deployment Issues & Solutions

### Issue 1: Python Version Incompatibility
**Error**: Package build failures with Python 3.13
**Solution**: Add `PYTHON_VERSION=3.11.9` environment variable in Render

### Issue 2: CORS Errors
**Error**: "No 'Access-Control-Allow-Origin' header"
**Solution**:
- Ensure CORS_ORIGINS is JSON array format (NOT comma-separated)
- Include Vercel preview URLs pattern: `https://*.vercel.app`

### Issue 3: Vercel Build Path Errors
**Error**: "cd: frontend: No such file or directory"
**Solution**: When Root Directory is set, don't use `cd` commands in vercel.json

### Issue 4: Missing Dependencies
**Error**: ModuleNotFoundError during backend startup
**Solution**: Do comprehensive import analysis and add all packages to requirements.txt

### Issue 5: Vercel API URL Typo
**Error**: API calls going to wrong path
**Solution**: Double-check `VITE_API_URL` in Vercel environment variables (common typo: `/ap` instead of `/api`)

## Quality Checklist

### Code Quality
- [ ] TypeScript: No `any` types, 100% type coverage
- [ ] Python: Type hints on all functions, comprehensive docstrings
- [ ] Clean Architecture: Proper separation of concerns
- [ ] Error Handling: Structured exceptions with appropriate HTTP codes
- [ ] Testing: Unit tests for business logic

### Security
- [ ] JWT authentication properly configured
- [ ] CORS properly restricted
- [ ] Environment variables not committed
- [ ] SQL injection prevention (use SQLAlchemy parameterized queries)
- [ ] Input validation with Pydantic

### Performance
- [ ] API response times < 500ms for standard queries
- [ ] Proper database indexing
- [ ] Frontend bundle size optimized
- [ ] Images optimized and lazy-loaded

### UX/UI
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Loading states for all async operations
- [ ] Error messages in Spanish, user-friendly
- [ ] Accessibility standards (WCAG AA)
- [ ] Consistent with Finkargo design system

## Support Resources

### Documentation
- **Vercel Docs**: https://vercel.com/docs
- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev
- **Supabase Docs**: https://supabase.com/docs

### Reference Implementation
- **Source Repository**: `DR-Danke/02-ob-preaprobados-mx`
- **Deployment Notes**: See session notes files in repo
  - `20251004_SESSION_NOTES_RENDER_DEPLOYMENT.md`
  - `20251004_SESSION_NOTES_VERCEL_DEPLOYMENT.md`

## Project-Specific Instructions

### Automation Hub Features (Define Your Own)
Replace this section with your specific automation features:

1. **Core Functionality**:
   - [ ] Define automation workflows
   - [ ] Define data sources
   - [ ] Define integration points

2. **User Roles** (adapt as needed):
   - Admin: Full system access
   - Manager: Create and manage automations
   - User: Execute and view automations
   - API: Programmatic access

3. **Data Models**:
   - [ ] Define your domain entities
   - [ ] Create SQLAlchemy models
   - [ ] Generate Alembic migrations

4. **API Endpoints**:
   - [ ] List your required endpoints
   - [ ] Define request/response schemas
   - [ ] Implement with FastAPI

5. **UI Pages**:
   - [ ] Dashboard
   - [ ] Automation management
   - [ ] Execution history
   - [ ] Settings

## Getting Started Checklist

When starting a new Finkargo Automation Hub project:

1. [ ] Copy this template to new project root as `CLAUDE.md`
2. [ ] Create GitHub repository
3. [ ] Set up Supabase project
4. [ ] Define specific automation features (replace section above)
5. [ ] Create frontend from Vite React-TS template
6. [ ] Set up FastAPI backend structure
7. [ ] Configure environment variables
8. [ ] Implement authentication
9. [ ] Create initial database models
10. [ ] Build core automation features
11. [ ] Deploy to Render (backend)
12. [ ] Deploy to Vercel (frontend)
13. [ ] Configure CORS
14. [ ] End-to-end testing
15. [ ] Document deployment in session notes

## Notes for Claude Code

When using this template:

1. **Architecture**: Follow Clean Architecture strictly
2. **Component Naming**: Always use FK prefix for form/business components
3. **Type Safety**: No `any` types, proper TypeScript throughout
4. **Environment Variables**:
   - Frontend: VITE_ prefix
   - Backend: PYTHON_VERSION=3.11.9 is critical for Render
   - CORS must be JSON array format
5. **Deployment**:
   - Vercel for frontend (set Root Directory to `frontend`)
   - Render for backend (set Root Directory to `backend`)
   - Use feature branch workflow
6. **Testing**: Test locally before deploying
7. **Documentation**: Document all deployment steps in session notes with date-first naming

This template is battle-tested and production-ready. Follow it closely for a smooth development and deployment experience.
- add logging to debug errors