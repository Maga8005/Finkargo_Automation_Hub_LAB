# Prime
> Execute the following sections to understand the Finkargo Automation Hub codebase then summarize your understanding.

## Run
git ls-files

## Read
README.md
docs/finkargo_automation_hub.md (if exists)

## Understand Architecture

### Backend (FastAPI + Python)
- `backend/src/adapter/rest/` - API routes (controllers)
- `backend/src/core/servicios/` - Business logic services
- `backend/src/repositorio/` - Data access layer
- `backend/src/interface/` - DTOs
- `backend/src/models/` - SQLAlchemy models

### Frontend (React + TypeScript + Vite)
- `frontend/src/pages/` - Route pages (legal/, operations/, finance/)
- `frontend/src/components/` - UI components (FK-prefixed)
- `frontend/src/services/` - API service layer
- `frontend/src/contexts/` - React Context providers (AuthContext)
- `frontend/src/types/` - TypeScript types

### Key Modules
1. **Legal** - Contract review and approval workflows
2. **Operations** - Contract requests and document management
3. **Finance** - Mexico invoicing automation with Excel/Google Drive

### Authentication
- Supabase Auth with JWT tokens
- Role-based access control (admin, legal, operations, etc.)
- AuthContext provides global auth state

## Summarize
Provide a brief summary of:
- The application's purpose
- Key modules and their functions
- Technology stack
- Authentication approach
