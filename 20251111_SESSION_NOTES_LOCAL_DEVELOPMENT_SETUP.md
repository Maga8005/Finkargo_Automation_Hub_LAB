# Session Notes: Local Development Environment Setup

**Date**: November 11, 2025
**Project**: Finkargo Automation Hub
**Developer**: Maria Gaitan
**Type**: Initial Setup - Collaborative Development Environment
**Status**: ✅ Complete - Development Environment Functional

---

## Executive Summary

Successfully configured a complete local development environment for collaborative work on the Finkargo Automation Hub. This session established an independent Supabase instance, replicated the database schema, configured all environment variables, and resolved authentication and authorization issues. The developer now has a fully functional local environment that mirrors production architecture without affecting the main team's database.

**Key Achievement**: Zero-to-running development environment in a single session with full understanding of the architecture and deployment flow.

---

## Session Objectives

### Primary Goals
1. ✅ Set up local development environment (frontend + backend)
2. ✅ Create independent Supabase project for development
3. ✅ Replicate database schema and authentication
4. ✅ Configure environment variables
5. ✅ Resolve deployment-related issues
6. ✅ Establish collaborative workflow understanding

### Learning Outcomes
- Understanding of full-stack architecture
- Supabase configuration and RLS policies
- Environment variable management
- Troubleshooting browser caching issues
- Database migrations workflow
- Collaborative development best practices

---

## Technical Setup Completed

### 1. Prerequisites Verification

**System Requirements:**
- ✅ Node.js v20.19.4 (meets ≥18.x requirement)
- ✅ Python 3.13.6 (project recommends 3.11.9, but compatible)
- ✅ PostgreSQL via Supabase (cloud-hosted)

### 2. Supabase Project Configuration

**Created Independent Development Instance:**
- Project Name: `finkargo-automation-dev`
- Region: South America (São Paulo)
- Plan: Free tier
- Purpose: Isolated development environment

**Credentials Obtained:**
```
- SUPABASE_URL: https://qsvjeuzbmoyhfvqqrebd.supabase.co
- SUPABASE_ANON_KEY: [configured]
- SUPABASE_SERVICE_KEY: [configured]
- SUPABASE_JWT_SECRET: [configured]
- DATABASE_URL: [configured with connection string]
```

### 3. Database Schema Setup

**Migrations Executed:**

**Step 1: Base Schema** (`schema.sql`)
- Created 5 core tables:
  - `clients` - Client data from platform exports
  - `contract_templates` - Contract template versions
  - `contract_generations` - Audit trail of generated contracts
  - `contract_id_sequence` - Sequential contract ID generator
  - `data_imports` - History of CSV/Excel imports
- Created functions:
  - `generate_contract_id()` - Format: ACT-YYYY-NNN
  - `update_updated_at_column()` - Auto-update timestamps
- Configured Row Level Security (RLS) policies
- Inserted sample data (2 test clients)

**Step 2: User Profiles Table**
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_modules TEXT[]
);
```

**Step 3: RLS Policies Configuration**
- Initially faced authentication issues with restrictive policies
- Solution: Adjusted policies to allow authenticated users to read all profiles
- Maintained security with role-based update permissions

### 4. Environment Configuration

**Backend (.env):**
```bash
DEBUG=true
APP_NAME=Finkargo Automation Hub
PYTHON_VERSION=3.11.9

# Supabase Configuration
SUPABASE_URL=https://qsvjeuzbmoyhfvqqrebd.supabase.co
SUPABASE_ANON_KEY=[configured]
SUPABASE_SERVICE_KEY=[configured]
SUPABASE_JWT_SECRET=[configured]

# Security
SECRET_KEY=DdqXusv6SWQliWL6oGbgX-hsvYLxGuTxXdqm-gv2kMo
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5173"]

# Database
DATABASE_URL=postgresql://[connection-string]

# File Upload
MAX_UPLOAD_SIZE=10485760
SUPPORTED_FILE_TYPES=[".pdf",".jpg",".jpeg",".png",".xlsx",".xls"]
```

**Frontend (.env):**
```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://qsvjeuzbmoyhfvqqrebd.supabase.co
VITE_SUPABASE_ANON_KEY=[configured]

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

### 5. Dependencies Installation

**Backend:**
```bash
cd backend
python -m venv venv
venv/Scripts/pip install -r requirements.txt
```

**Key Packages Installed:**
- FastAPI 0.121.1
- Uvicorn 0.38.0
- SQLAlchemy 2.0.44
- Supabase 2.24.0
- Pandas 2.3.3
- PyMuPDF 1.26.6
- Python-docx 1.2.0
- And 80+ dependencies total

**Frontend:**
- Already had `node_modules` installed
- Dependencies verified and working

### 6. Server Startup

**Backend Server:**
```bash
cd backend
venv/Scripts/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- Status: ✅ Running on http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

**Frontend Server:**
```bash
cd frontend
npm run dev
```
- Status: ✅ Running on http://localhost:5173
- Hot reload: Enabled
- Build time: ~2.3 seconds

---

## Issues Encountered and Solutions

### Issue 1: Frontend Loading Spinner Stuck

**Problem:**
- Frontend showed "Cargando... Si esto toma mucho tiempo intenta refrescar la página"
- No errors in console
- AuthContext initialization hanging

**Root Cause:**
- Chrome localStorage had cached data from previous Supabase configuration
- Old session tokens conflicting with new Supabase instance

**Solution:**
```
F12 → Application → Local Storage → localhost:5173 → Clear
```

**Learning:** Always clear browser storage when switching Supabase instances.

---

### Issue 2: Empty Sidebar (No Departments Showing)

**Problem:**
- User logged in successfully
- Dashboard loaded but sidebar showed "DEPARTAMENTOS" with no items
- API `/api/departments` returning 200 OK

**Root Cause:**
- User created in `auth.users` table
- Missing profile in `user_profiles` table
- Frontend `FKSidebar` component filters departments by user role
- `hasAccessToDepartment()` returned `false` when `userProfile` was `null`

**Diagnosis Steps:**
```javascript
// Code in FKSidebar.tsx lines 72-88
const hasAccessToDepartment = (departmentId: string): boolean => {
    if (!userProfile) return false;  // ← This was the issue
    // ... role-based logic
};
```

**Solution:**
1. Created `user_profiles` table with proper schema
2. Inserted user profile with role='admin'
3. Granted access to all modules

```sql
INSERT INTO user_profiles (
    id,
    full_name,
    role,
    is_active,
    assigned_modules,
    created_at
)
VALUES (
    '91ae00bc-acda-4f27-a52c-ffb3b61f3c54',
    'Maria Gaitan',
    'admin',
    true,
    ARRAY['legal', 'operations', 'finance', 'hr', 'technology', 'sales', 'customer-service', 'collections'],
    NOW()
);
```

---

### Issue 3: Row Level Security (RLS) Blocking Access

**Problem:**
- User profile existed in database
- AuthContext still couldn't fetch profile
- Console showed: `[AuthContext] Fetching profile for user: [uuid]` but no follow-up

**Root Cause:**
- Strict RLS policies preventing authenticated user from reading own profile
- Initial policy: `USING (auth.uid() = id)` was too restrictive during login flow

**Solution:**
```sql
-- Disable RLS temporarily to confirm diagnosis
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;

-- After confirmation, re-enable with corrected policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Create permissive policy for authenticated users
CREATE POLICY "Authenticated users can read profiles"
ON user_profiles
FOR SELECT
TO authenticated
USING (true);
```

**Learning:** RLS policies need careful design to work with authentication flows. Testing with RLS disabled can quickly identify permission issues.

---

## Architecture Understanding

### Application Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER                             │
│                                                              │
│  1. http://localhost:5173 (React App)                       │
│     └─ Login → Supabase Auth                                │
│     └─ API Calls → Backend                                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌──────────┐    ┌─────────────┐    ┌──────────────┐
│ Supabase │    │   Backend   │    │   Frontend   │
│  (Auth)  │◄───┤  localhost  │◄───┤  localhost   │
│          │    │    :8000    │    │    :5173     │
└────┬─────┘    └──────┬──────┘    └──────────────┘
     │                 │
     │                 │
     ▼                 ▼
┌──────────────────────────────┐
│   Supabase PostgreSQL        │
│   - auth.users               │
│   - user_profiles            │
│   - clients                  │
│   - contract_templates       │
│   - contract_generations     │
└──────────────────────────────┘
```

### Key Architectural Concepts Learned

1. **Separation of Concerns:**
   - Frontend: UI/UX and state management
   - Backend: Business logic and data validation
   - Supabase: Authentication and data persistence

2. **Authentication Flow:**
   - User enters credentials → Frontend
   - Frontend calls `supabase.auth.signInWithPassword()`
   - Supabase validates and returns JWT token
   - Frontend stores token in localStorage
   - Backend validates token on each API request
   - User profile fetched from `user_profiles` table

3. **Role-Based Access Control (RBAC):**
   - User roles stored in `user_profiles.role`
   - Frontend components check role before rendering
   - Backend APIs validate role before processing
   - Sidebar departments filtered by user role

4. **Environment Variable Management:**
   - Backend uses `.env` loaded by `python-dotenv`
   - Frontend uses `.env` with `VITE_` prefix
   - Never commit `.env` files (use `.env.example`)
   - Different environments: local, dev, staging, prod

---

## Collaborative Development Workflow Established

### Development Best Practices

1. **Independent Development Databases:**
   - Each developer has own Supabase project
   - Prevents accidental data corruption
   - Freedom to experiment and break things
   - Easy to reset and start fresh

2. **Schema Migrations:**
   - All schema changes in SQL files (`backend/database/*.sql`)
   - Version controlled in Git
   - Can be replayed on any environment
   - Documentation included in migration files

3. **Feature Branch Workflow:**
   ```bash
   # Create feature branch
   git checkout -b feature-my-new-feature

   # Develop and test locally
   # Commit changes
   git add .
   git commit -m "feat: description of feature"

   # Push to remote
   git push origin feature-my-new-feature

   # Create Pull Request for review
   ```

4. **Environment Separation:**
   ```
   Development (Local):
   - Own Supabase project
   - localhost:8000 backend
   - localhost:5173 frontend

   Staging/Testing (Shared):
   - Shared dev Supabase
   - Render backend (dev)
   - Vercel preview deployment

   Production:
   - Production Supabase
   - Render backend (prod)
   - Vercel production deployment
   ```

---

## Knowledge Transfer

### Key Files and Their Purpose

**Configuration:**
- `backend/.env` - Backend environment variables
- `frontend/.env` - Frontend environment variables
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies

**Database:**
- `backend/database/schema.sql` - Base schema
- `backend/database/migration_*.sql` - Schema changes
- `backend/database/README.md` - Setup instructions

**Backend Core:**
- `backend/main.py` - FastAPI application entry point
- `backend/src/adapter/rest/` - API routes/controllers
- `backend/src/core/servicios/` - Business logic
- `backend/src/repositorio/` - Data access layer
- `backend/src/config/settings.py` - Configuration management

**Frontend Core:**
- `frontend/src/App.tsx` - Main application component
- `frontend/src/main.tsx` - React entry point
- `frontend/src/contexts/AuthContext.tsx` - Authentication state
- `frontend/src/services/supabase.ts` - Supabase client
- `frontend/src/components/ui/FKSidebar.tsx` - Navigation sidebar

### Common Commands

**Start Development:**
```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Database Operations:**
```bash
# Execute migration (in Supabase SQL Editor)
# Copy contents of migration file and run

# Verify tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

# Check user profile
SELECT * FROM user_profiles WHERE id = 'your-user-id';
```

**Troubleshooting:**
```bash
# Clear browser cache
F12 → Application → Local Storage → Clear

# Restart backend (if frozen)
Ctrl+C in terminal
Rerun: uvicorn main:app --reload

# Reinstall dependencies (if broken)
pip install -r requirements.txt
npm install
```

---

## API Endpoints Available

### Health & Debug
- `GET /api/health` - Server health check
- `GET /api/debug/cors` - CORS configuration debug
- `GET /docs` - Swagger UI documentation
- `GET /openapi.json` - OpenAPI specification

### Core Features
- `GET /api/departments` - List all departments
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `GET /api/legal/*` - Legal department endpoints
- `GET /api/operations/*` - Operations department endpoints

---

## Success Metrics

### Setup Completion
- ✅ Backend running: http://localhost:8000
- ✅ Frontend running: http://localhost:5173
- ✅ Database connected and operational
- ✅ User authentication working
- ✅ Department navigation functional
- ✅ API integration working end-to-end

### Developer Readiness
- ✅ Full understanding of project structure
- ✅ Can start/stop services independently
- ✅ Knows how to troubleshoot common issues
- ✅ Understands collaborative workflow
- ✅ Ready to develop new features

---

## Next Steps for Developer

### Immediate Actions
1. **Create First Feature:**
   - Pick a department (Legal, Operations, etc.)
   - Create feature branch
   - Implement functionality
   - Test locally
   - Submit PR for review

2. **Explore Existing Features:**
   - Test Legal contract generation
   - Review Operations workflows
   - Understand data import process

3. **Documentation:**
   - Document any new features developed
   - Update session notes with findings
   - Share knowledge with team

### Learning Resources
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **React Docs:** https://react.dev
- **Supabase Docs:** https://supabase.com/docs
- **Material-UI:** https://mui.com/material-ui/getting-started/
- **Vercel Deployment:** https://vercel.com/docs
- **Render Deployment:** https://render.com/docs

---

## Team Coordination

### Communication Protocol
- Coordinate database schema changes before executing
- Share migration SQL files via Git
- Notify team before merging to main branch
- Document significant changes in session notes

### Code Review Checklist
- [ ] Code follows Clean Architecture principles
- [ ] TypeScript: No `any` types
- [ ] Python: Type hints and docstrings
- [ ] Tests written for business logic
- [ ] Environment variables documented
- [ ] Migration SQL files included (if schema changed)

---

## Session Timeline

| Time | Activity | Status |
|------|----------|--------|
| Start | Verify Node.js and Python versions | ✅ |
| +10min | Create Supabase project and get credentials | ✅ |
| +20min | Execute schema.sql migration | ✅ |
| +30min | Configure backend .env | ✅ |
| +35min | Configure frontend .env | ✅ |
| +40min | Install Python dependencies | ✅ |
| +50min | Start backend server | ✅ |
| +55min | Start frontend server | ✅ |
| +60min | Debug: Frontend loading spinner issue | ✅ |
| +70min | Debug: Empty sidebar issue | ✅ |
| +85min | Create user_profiles table | ✅ |
| +90min | Insert user profile record | ✅ |
| +100min | Debug: RLS permission issues | ✅ |
| +110min | Fix RLS policies | ✅ |
| +115min | Verify complete functionality | ✅ |

**Total Session Time:** ~2 hours
**Result:** Fully functional development environment

---

## Key Takeaways

1. **Independent Development Environments are Essential:**
   - Prevents conflicts between developers
   - Allows experimentation without fear
   - Easy to reset if something breaks

2. **Browser Caching Can Be Tricky:**
   - Always clear localStorage when switching configs
   - Use incognito mode for quick testing
   - Consider disabling cache during development

3. **RLS Policies Need Careful Design:**
   - Too restrictive = authentication breaks
   - Too permissive = security risks
   - Test with RLS disabled to isolate issues
   - Document policy intentions clearly

4. **Documentation is Critical:**
   - Session notes help teammates onboard faster
   - Migration files should be self-documenting
   - README files prevent common mistakes

5. **Supabase Makes Collaboration Easier:**
   - Free tier sufficient for development
   - Easy to create multiple projects
   - Built-in authentication reduces boilerplate
   - SQL Editor simplifies database management

---

## Conclusion

Successfully established a professional local development environment following industry best practices. The developer now has:

- Complete autonomy to develop features
- Understanding of the full-stack architecture
- Ability to troubleshoot common issues
- Knowledge of collaborative Git workflows
- Foundation to contribute effectively to the team

**Environment Status:** ✅ Production Ready
**Developer Status:** ✅ Ready to Code
**Next Milestone:** First Feature Implementation

---

## Appendix A: Quick Reference Commands

### Daily Startup
```bash
# Terminal 1 - Backend
cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### Shutdown
```
Ctrl+C in both terminals
```

### Reset Environment (if needed)
```bash
# Clear browser data
F12 → Application → Storage → Clear site data

# Restart servers
Ctrl+C in terminals
Re-run startup commands
```

### Access Points
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api
- API Docs: http://localhost:8000/docs
- Supabase: https://supabase.com/dashboard

---

**Document Version:** 1.0
**Last Updated:** November 11, 2025
**Author:** Claude Code Assistant
**Reviewed By:** Maria Gaitan
