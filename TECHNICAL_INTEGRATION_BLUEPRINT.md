# Blueprint Técnico: Guía de Integración de Funcionalidades

**Propósito:** Documento técnico para integrar funcionalidades externas al Finkargo Automation Hub

**Audiencia:** Desarrolladores que quieren migrar/adaptar funcionalidades existentes

**Última Actualización:** November 11, 2025

---

## 📋 Tabla de Contenidos

1. [Stack Tecnológico](#1-stack-tecnológico)
2. [Esquema de Base de Datos](#2-esquema-de-base-de-datos)
3. [Sistema de Autenticación y Autorización](#3-sistema-de-autenticación-y-autorización)
4. [Estructura de Módulos y Componentes](#4-estructura-de-módulos-y-componentes)
5. [APIs Disponibles](#5-apis-disponibles)
6. [Patrones de Diseño](#6-patrones-de-diseño)
7. [Configuración de Ambientes](#7-configuración-de-ambientes)
8. [Checklist de Integración](#8-checklist-de-integración)

---

## 1. Stack Tecnológico

### Frontend

| Tecnología | Versión | Propósito | Docs |
|------------|---------|-----------|------|
| **React** | 19.1.1 | UI Framework | https://react.dev |
| **TypeScript** | 5.9.3 | Type Safety | https://typescriptlang.org |
| **Vite** | 7.1.7 | Build Tool | https://vitejs.dev |
| **Material-UI** | 7.3.4 | Component Library | https://mui.com |
| **React Router** | 7.9.3 | Routing | https://reactrouter.com |
| **React Hook Form** | 7.64.0 | Form Management | https://react-hook-form.com |
| **Axios** | 1.12.2 | HTTP Client | https://axios-http.com |
| **Date-fns** | 4.1.0 | Date Utilities | https://date-fns.org |
| **Supabase Client** | 2.58.0 | Auth & DB Client | https://supabase.com/docs |

**Instalación:**
```bash
cd frontend
npm install
```

---

### Backend

| Tecnología | Versión | Propósito | Docs |
|------------|---------|-----------|------|
| **Python** | 3.11.9-3.13.6 | Language | https://python.org |
| **FastAPI** | 0.121.1 | API Framework | https://fastapi.tiangolo.com |
| **Uvicorn** | 0.38.0 | ASGI Server | https://uvicorn.org |
| **Pydantic** | 2.12.4 | Data Validation | https://docs.pydantic.dev |
| **SQLAlchemy** | 2.0.44 | ORM | https://sqlalchemy.org |
| **Alembic** | 1.17.1 | Migrations | https://alembic.sqlalchemy.org |
| **Supabase Python** | 2.24.0 | Auth & DB | https://supabase.com/docs/reference/python |
| **Pandas** | 2.3.3 | Data Processing | https://pandas.pydata.org |
| **PyMuPDF** | 1.26.6 | PDF Generation | https://pymupdf.readthedocs.io |
| **python-docx** | 1.2.0 | DOCX Processing | https://python-docx.readthedocs.io |

**Instalación:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

### Base de Datos

| Servicio | Versión | Propósito | Docs |
|----------|---------|-----------|------|
| **Supabase** | Cloud | Database + Auth | https://supabase.com |
| **PostgreSQL** | 15+ | Relational DB | https://postgresql.org |
| **pgcrypto** | Extension | Encryption | Included |
| **uuid-ossp** | Extension | UUID Generation | Included |

---

### Infraestructura

| Servicio | Propósito | URL |
|----------|-----------|-----|
| **Vercel** | Frontend Hosting | https://vercel.com |
| **Render** | Backend Hosting | https://render.com |
| **Supabase** | Database + Auth | https://supabase.com |
| **GitHub** | Version Control | https://github.com |

---

## 2. Esquema de Base de Datos

### 2.1. Diagrama Entidad-Relación

```
┌─────────────────────┐
│    auth.users       │  (Supabase Auth - Built-in)
│                     │
│ - id (UUID) PK      │
│ - email             │
│ - encrypted_password│
│ - email_confirmed_at│
│ - created_at        │
└──────────┬──────────┘
           │
           │ 1:1
           ↓
┌─────────────────────────────────┐
│    user_profiles                │
│                                 │
│ - id (UUID) PK FK → auth.users │
│ - full_name                     │
│ - role (TEXT)                   │
│ - is_active (BOOLEAN)           │
│ - assigned_modules (TEXT[])     │
│ - last_login (TIMESTAMPTZ)      │
│ - created_at                    │
│ - updated_at                    │
└────────────┬────────────────────┘
             │
             │ 1:N
             ↓
┌──────────────────────────────────┐
│    clients                        │
│                                   │
│ - id (UUID) PK                   │
│ - nit (VARCHAR) UNIQUE           │
│ - nombre_importador              │
│ - representante_legal            │
│ - cedula_representante           │
│ - ciudad_domicilio               │
│ - cupo_plataforma (DECIMAL)      │
│ - is_active                      │
│ - imported_by FK → auth.users    │
│ - created_at                     │
│ - updated_at                     │
│ - notes                          │
└────────────┬─────────────────────┘
             │
             │ 1:N
             ↓
┌──────────────────────────────────────┐
│    contract_generations              │
│                                      │
│ - id (UUID) PK                       │
│ - contract_id (VARCHAR) UNIQUE       │
│ - client_nit (VARCHAR)               │
│ - client_id FK → clients             │
│ - status (ENUM)                      │
│ - generated_by FK → auth.users       │
│ - reviewed_by FK → auth.users        │
│ - pdf_url                            │
│ - pdf_storage_path                   │
│ - template_id FK → contract_templates│
│ - template_version                   │
│ - data_snapshot (JSONB)              │
│ - generated_at                       │
│ - reviewed_at                        │
│ - created_at                         │
│ - updated_at                         │
└──────────────────────────────────────┘
             ↑
             │ N:1
             │
┌──────────────────────────────────┐
│    contract_templates             │
│                                   │
│ - id (UUID) PK                   │
│ - version (VARCHAR)              │
│ - contract_type (VARCHAR)        │
│ - template_content (TEXT)        │
│ - active (BOOLEAN)               │
│ - created_by FK → auth.users     │
│ - created_at                     │
│ - notes                          │
│                                  │
│ UNIQUE(contract_type, version)  │
└──────────────────────────────────┘


┌──────────────────────────────────┐
│    data_imports                   │
│                                   │
│ - id (UUID) PK                   │
│ - file_name                      │
│ - file_size                      │
│ - total_rows                     │
│ - successful_rows                │
│ - failed_rows                    │
│ - error_log (JSONB)              │
│ - status (ENUM)                  │
│ - imported_by FK → auth.users    │
│ - imported_at                    │
└──────────────────────────────────┘


┌──────────────────────────────────┐
│    contract_id_sequence           │
│                                   │
│ - id (UUID) PK                   │
│ - year (INTEGER) UNIQUE          │
│ - last_sequence (INTEGER)        │
└──────────────────────────────────┘
```

---

### 2.2. Tabla `auth.users` (Supabase Built-in)

**Propósito:** Gestión de autenticación de usuarios

| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| `id` | UUID | PK | Identificador único del usuario |
| `email` | VARCHAR | UNIQUE, NOT NULL | Email para login |
| `encrypted_password` | TEXT | NOT NULL | Password hasheado (bcrypt) |
| `email_confirmed_at` | TIMESTAMPTZ | NULL | Fecha de confirmación de email |
| `created_at` | TIMESTAMPTZ | NOT NULL | Fecha de creación |
| `raw_app_meta_data` | JSONB | NULL | Metadata de la aplicación |
| `raw_user_meta_data` | JSONB | NULL | Metadata del usuario |
| `role` | TEXT | NOT NULL | Rol de Supabase (authenticated) |

**RLS:** Gestionado automáticamente por Supabase Auth

---

### 2.3. Tabla `user_profiles`

**Propósito:** Perfiles de usuario con roles y permisos de la aplicación

| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| `id` | UUID | PK, FK → auth.users | ID del usuario (mismo que auth.users) |
| `full_name` | TEXT | NOT NULL | Nombre completo del usuario |
| `role` | TEXT | NOT NULL | Rol empresarial (admin, legal, operations, etc.) |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Estado activo del usuario |
| `assigned_modules` | TEXT[] | NULL | Array de módulos asignados |
| `last_login` | TIMESTAMPTZ | NULL | Última sesión del usuario |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Última actualización |

**Índices:**
```sql
CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_user_profiles_is_active ON user_profiles(is_active);
```

**RLS Policies:**
- ✅ Usuarios autenticados pueden leer todos los perfiles
- ✅ Usuarios pueden actualizar su propio perfil
- ✅ Admins pueden actualizar cualquier perfil
- ✅ Service role tiene acceso completo

**Trigger:**
```sql
CREATE TRIGGER trigger_update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_updated_at();
```

---

### 2.4. Tabla `clients`

**Propósito:** Almacenar datos de clientes importados

| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| `id` | UUID | PK | Identificador único |
| `nit` | VARCHAR(20) | UNIQUE, NOT NULL | NIT del cliente |
| `nombre_importador` | VARCHAR(255) | NOT NULL | Nombre del cliente |
| `representante_legal` | VARCHAR(255) | NOT NULL | Representante legal |
| `cedula_representante` | VARCHAR(50) | NOT NULL | Cédula del representante |
| `ciudad_domicilio` | VARCHAR(100) | NOT NULL | Ciudad |
| `cupo_plataforma` | DECIMAL(15,2) | NOT NULL | Cupo asignado |
| `is_active` | BOOLEAN | DEFAULT TRUE | Estado activo |
| `imported_by` | UUID | FK → auth.users | Quién importó |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Última actualización |
| `notes` | TEXT | NULL | Notas adicionales |

**Índices:**
```sql
CREATE INDEX idx_clients_nit ON clients(nit);
CREATE INDEX idx_clients_nombre ON clients(nombre_importador);
CREATE INDEX idx_clients_active ON clients(is_active);
```

**RLS Policies:**
- ✅ Usuarios autenticados pueden leer
- ✅ Operations y Legal pueden insertar/actualizar

---

### 2.5. Tabla `contract_templates`

**Propósito:** Versiones de plantillas de contratos

| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| `id` | UUID | PK | Identificador único |
| `version` | VARCHAR(20) | NOT NULL | Versión (ej: 1.0.0) |
| `contract_type` | VARCHAR(50) | DEFAULT 'activos' | Tipo de contrato |
| `template_content` | TEXT | NOT NULL | Contenido de la plantilla |
| `active` | BOOLEAN | DEFAULT FALSE | Template activo |
| `created_by` | UUID | FK → auth.users | Quién creó |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Fecha de creación |
| `notes` | TEXT | NULL | Notas de la versión |

**Restricciones:**
```sql
UNIQUE(contract_type, version)

-- Solo un template activo por tipo
CREATE UNIQUE INDEX idx_one_active_template
ON contract_templates(contract_type)
WHERE active = TRUE;
```

**RLS Policies:**
- ✅ Usuarios autenticados pueden leer
- ✅ Legal puede gestionar (crear/actualizar)

---

### 2.6. Tabla `contract_generations`

**Propósito:** Audit trail de contratos generados

| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| `id` | UUID | PK | Identificador único |
| `contract_id` | VARCHAR(50) | UNIQUE, NOT NULL | ID del contrato (ACT-2025-001) |
| `client_nit` | VARCHAR(20) | NOT NULL | NIT del cliente |
| `client_id` | UUID | FK → clients | Referencia al cliente |
| `status` | VARCHAR(50) | DEFAULT 'generated' | Estado del contrato |
| `generated_by` | UUID | FK → auth.users, NOT NULL | Quién generó |
| `generated_at` | TIMESTAMPTZ | DEFAULT NOW() | Fecha de generación |
| `reviewed_by` | UUID | FK → auth.users | Quién revisó |
| `reviewed_at` | TIMESTAMPTZ | NULL | Fecha de revisión |
| `review_notes` | TEXT | NULL | Notas de revisión |
| `pdf_url` | TEXT | NULL | URL pública del PDF |
| `pdf_storage_path` | TEXT | NULL | Path en storage |
| `template_id` | UUID | FK → contract_templates | Template usado |
| `template_version` | VARCHAR(20) | NULL | Versión del template |
| `data_snapshot` | JSONB | NOT NULL | Snapshot de datos usado |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Última actualización |

**Estados Válidos:**
```sql
CHECK (status IN ('generated', 'under_review', 'approved', 'rejected'))
```

**Índices:**
```sql
CREATE INDEX idx_contract_gen_status ON contract_generations(status);
CREATE INDEX idx_contract_gen_client ON contract_generations(client_nit);
CREATE INDEX idx_contract_gen_date ON contract_generations(generated_at DESC);
CREATE INDEX idx_contract_gen_contract_id ON contract_generations(contract_id);
```

**RLS Policies:**
- ✅ Usuarios autenticados pueden leer
- ✅ Operations y Legal pueden crear
- ✅ Legal puede actualizar (review)

---

### 2.7. Tabla `data_imports`

**Propósito:** Historial de importaciones CSV/Excel

| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| `id` | UUID | PK | Identificador único |
| `file_name` | VARCHAR(255) | NOT NULL | Nombre del archivo |
| `file_size` | INTEGER | NULL | Tamaño en bytes |
| `total_rows` | INTEGER | NULL | Total de filas procesadas |
| `successful_rows` | INTEGER | NULL | Filas exitosas |
| `failed_rows` | INTEGER | NULL | Filas fallidas |
| `error_log` | JSONB | NULL | Log de errores |
| `status` | VARCHAR(50) | DEFAULT 'processing' | Estado de la importación |
| `imported_by` | UUID | FK → auth.users | Quién importó |
| `imported_at` | TIMESTAMPTZ | DEFAULT NOW() | Fecha de importación |

**Estados Válidos:**
```sql
CHECK (status IN ('processing', 'completed', 'failed'))
```

---

### 2.8. Tabla `contract_id_sequence`

**Propósito:** Generador de IDs secuenciales de contratos por año

| Campo | Tipo | Restricción | Descripción |
|-------|------|-------------|-------------|
| `id` | UUID | PK | Identificador único |
| `year` | INTEGER | UNIQUE, NOT NULL | Año |
| `last_sequence` | INTEGER | DEFAULT 0 | Último número usado |

**Función Asociada:**
```sql
CREATE OR REPLACE FUNCTION generate_contract_id()
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    new_contract_id VARCHAR(50);
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    INSERT INTO contract_id_sequence (year, last_sequence)
    VALUES (current_year, 1)
    ON CONFLICT (year)
    DO UPDATE SET last_sequence = contract_id_sequence.last_sequence + 1
    RETURNING last_sequence INTO next_sequence;

    new_contract_id := 'ACT-' || current_year || '-' || LPAD(next_sequence::TEXT, 3, '0');

    RETURN new_contract_id;
END;
$$ LANGUAGE plpgsql;
```

**Uso:**
```sql
SELECT generate_contract_id();
-- Retorna: ACT-2025-001
```

---

### 2.9. Funciones de Base de Datos

#### Actualizar `updated_at` Automáticamente

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Aplicada a:**
- `clients`
- `contract_generations`
- `user_profiles`

---

## 3. Sistema de Autenticación y Autorización

### 3.1. Arquitectura de Auth

```
┌─────────────────────────────────────────────┐
│           FRONTEND (React)                   │
│                                              │
│  1. User Login                               │
│     └→ supabase.auth.signInWithPassword()   │
│                                              │
│  2. Token Storage                            │
│     └→ localStorage (automatic)              │
│                                              │
│  3. Protected Routes                         │
│     └→ Check isAuthenticated                │
└──────────────────┬──────────────────────────┘
                   │
                   │ JWT Token
                   │
┌──────────────────▼──────────────────────────┐
│          SUPABASE AUTH                       │
│                                              │
│  - Validates credentials                     │
│  - Generates JWT token                       │
│  - Manages refresh tokens                    │
│  - Row Level Security enforcement            │
└──────────────────┬──────────────────────────┘
                   │
                   │ Validated Token
                   │
┌──────────────────▼──────────────────────────┐
│           BACKEND (FastAPI)                  │
│                                              │
│  1. Verify JWT                               │
│  2. Extract user_id                          │
│  3. Fetch user_profile                       │
│  4. Check role permissions                   │
│  5. Process request                          │
└──────────────────────────────────────────────┘
```

---

### 3.2. Flujo de Autenticación

#### Paso 1: Login

**Frontend (`AuthContext.tsx`):**
```typescript
const signIn = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) throw error;

  // Token automáticamente almacenado en localStorage
  return data;
};
```

**Supabase:**
- Valida credenciales contra `auth.users`
- Genera JWT token con claims:
  ```json
  {
    "sub": "user-uuid",
    "email": "user@example.com",
    "role": "authenticated",
    "iat": 1699999999,
    "exp": 1699999999
  }
  ```

---

#### Paso 2: Fetch User Profile

**Frontend (`AuthContext.tsx`):**
```typescript
const fetchUserProfile = async (userId: string) => {
  const { data, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', userId)
    .single();

  if (error) throw error;

  setUserProfile(data);
};
```

---

#### Paso 3: Validación en Backend

**Backend (`dependencies.py`):**
```python
async def get_current_user(
    authorization: str = Header(None)
) -> dict:
    """Validate JWT and return user data"""

    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, "Missing or invalid token")

    token = authorization.replace('Bearer ', '')

    # Verify JWT with Supabase
    user = supabase.auth.get_user(token)

    if not user:
        raise HTTPException(401, "Invalid token")

    # Fetch user profile
    profile = await get_user_profile(user.id)

    return {
        "user_id": user.id,
        "email": user.email,
        "profile": profile
    }
```

---

### 3.3. Sistema de Roles (RBAC)

#### Roles Disponibles

| Rol | Permisos | Módulos Asignables |
|-----|----------|-------------------|
| `admin` | Acceso total a todos los módulos | Todos |
| `legal` | Gestión de contratos legales | legal |
| `operations` | Gestión de operaciones | operations |
| `commercial` | Gestión comercial | sales |
| `analyst` | Análisis de datos | finance, sales |
| `manager` | Supervisión | Múltiples |
| `user` | Lectura básica | Limitado |

#### Verificación de Rol en Frontend

**Componente `RoleProtectedRoute`:**
```typescript
interface RoleProtectedRouteProps {
  allowedRoles: UserRole[];
  children: ReactNode;
}

const RoleProtectedRoute: React.FC<RoleProtectedRouteProps> = ({
  allowedRoles,
  children
}) => {
  const { userProfile } = useAuth();

  if (!userProfile) {
    return <Navigate to="/login" />;
  }

  if (!allowedRoles.includes(userProfile.role)) {
    return <UnauthorizedPage />;
  }

  return <>{children}</>;
};
```

**Uso:**
```typescript
<Route
  path="department/legal"
  element={
    <RoleProtectedRoute allowedRoles={['admin', 'legal']}>
      <LegalDashboard />
    </RoleProtectedRoute>
  }
/>
```

---

#### Verificación de Rol en Backend

**Dependency (`rbac_dependencies.py`):**
```python
def require_roles(allowed_roles: List[str]):
    """Decorator to check user role"""

    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ):
        user_role = current_user['profile']['role']

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' not authorized"
            )

        return current_user

    return role_checker
```

**Uso:**
```python
@router.post("/contracts/generate")
async def generate_contract(
    request: ContractGenerationRequest,
    current_user: dict = Depends(require_roles(['admin', 'legal', 'operations']))
):
    # Solo admins, legal y operations pueden generar contratos
    pass
```

---

### 3.4. Row Level Security (RLS)

**Políticas Activas:**

#### user_profiles
```sql
-- Lectura: Todos los autenticados
CREATE POLICY "Authenticated users can read profiles"
ON user_profiles FOR SELECT
TO authenticated
USING (true);

-- Actualización: Solo propio perfil
CREATE POLICY "Users can update own profile"
ON user_profiles FOR UPDATE
TO authenticated
USING (auth.uid() = id);

-- Actualización: Admins pueden todo
CREATE POLICY "Admins can update any profile"
ON user_profiles FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role = 'admin'
    )
);
```

#### clients
```sql
-- Lectura: Todos los autenticados
CREATE POLICY "Allow authenticated users to read clients"
ON clients FOR SELECT
TO authenticated
USING (true);

-- Inserción/Actualización: Operations y Legal
CREATE POLICY "Allow operations and legal to insert clients"
ON clients FOR INSERT
TO authenticated
WITH CHECK (true);
```

---

## 4. Estructura de Módulos y Componentes

### 4.1. Arquitectura Frontend

```
frontend/src/
│
├── api/                    # HTTP Clients
│   └── clients/
│       ├── apiClient.ts    # Axios instance configurado
│       └── authInterceptor.ts
│
├── components/             # Componentes reutilizables
│   ├── forms/              # Componentes de formularios (FK prefijo)
│   │   ├── FKClientForm.tsx
│   │   └── FKContractForm.tsx
│   │
│   ├── ui/                 # Componentes UI base (FK prefijo)
│   │   ├── FKMainLayout.tsx
│   │   ├── FKTopNavbar.tsx
│   │   ├── FKSidebar.tsx
│   │   ├── FKLoadingSpinner.tsx
│   │   └── FKErrorBoundary.tsx
│   │
│   ├── ProtectedRoute.tsx  # HOC para rutas autenticadas
│   └── RoleProtectedRoute.tsx  # HOC para rutas con roles
│
├── contexts/               # React Contexts
│   └── AuthContext.tsx     # Estado global de autenticación
│
├── hooks/                  # Custom React Hooks
│   ├── useAuth.ts          # Hook de autenticación
│   ├── useAPI.ts           # Hook para llamadas API
│   └── useDebounce.ts      # Hook de debounce
│
├── pages/                  # Páginas de la aplicación
│   ├── HomePage.tsx        # Dashboard principal
│   ├── LoginPage.tsx       # Página de login
│   ├── DepartmentPage.tsx  # Página genérica de departamento
│   │
│   ├── legal/              # Módulo Legal
│   │   ├── LegalDashboard.tsx
│   │   ├── ContractGenerator.tsx
│   │   └── ContractReview.tsx
│   │
│   └── operations/         # Módulo Operations
│       └── OperationsDashboard.tsx
│
├── services/               # Servicios de negocio
│   ├── supabase.ts         # Cliente Supabase
│   ├── departmentService.ts # Servicio de departamentos
│   └── contractService.ts  # Servicio de contratos
│
├── theme/                  # Material-UI Theme
│   └── theme.ts            # Configuración de colores Finkargo
│
├── types/                  # TypeScript Types
│   └── index.ts            # Tipos compartidos
│
├── utils/                  # Utilidades
│   ├── formatters.ts       # Formateo de datos
│   └── validators.ts       # Validaciones
│
├── App.tsx                 # Componente principal
├── main.tsx                # Entry point
└── index.css               # Estilos globales
```

---

### 4.2. Arquitectura Backend (Clean Architecture)

```
backend/src/
│
├── adapter/                # Adapters (REST, GraphQL, etc.)
│   └── rest/               # REST Controllers
│       ├── auth_routes.py          # Endpoints de autenticación
│       ├── legal_routes.py         # Endpoints de Legal
│       ├── operations_routes.py    # Endpoints de Operations
│       ├── dependencies.py         # Dependencias FastAPI
│       └── rbac_dependencies.py    # RBAC decorators
│
├── core/                   # Business Logic
│   └── servicios/          # Services (Domain Logic)
│       ├── contract_service.py     # Lógica de contratos
│       ├── client_service.py       # Lógica de clientes
│       └── template_service.py     # Lógica de templates
│
├── repositorio/            # Data Access Layer
│   ├── contract_repository.py      # CRUD de contratos
│   ├── client_repository.py        # CRUD de clientes
│   └── template_repository.py      # CRUD de templates
│
├── interface/              # DTOs and Contracts
│   ├── requests.py         # Request DTOs (Pydantic)
│   └── responses.py        # Response DTOs (Pydantic)
│
├── models/                 # SQLAlchemy Models
│   └── legal_models.py     # Modelos de Legal
│
└── config/                 # Configuration
    └── settings.py         # Environment config (Pydantic Settings)
```

**Flujo de Datos:**

```
Request → Adapter (REST Controller)
           ↓
      Core (Service)
           ↓
      Repositorio (Data Access)
           ↓
      Database
```

---

### 4.3. Convenciones de Naming

#### Frontend Components

**Componentes de Negocio/Formularios:**
- Prefijo `FK`
- PascalCase
- Ejemplos: `FKClientForm`, `FKContractGenerator`, `FKUserProfile`

**Componentes UI Base:**
- Prefijo `FK`
- PascalCase
- Ejemplos: `FKButton`, `FKCard`, `FKModal`

**Páginas:**
- Sin prefijo
- PascalCase + `Page` suffix
- Ejemplos: `LoginPage`, `DashboardPage`, `LegalDashboard`

**Custom Hooks:**
- Prefijo `use`
- camelCase
- Ejemplos: `useAuth`, `useAPI`, `useDebounce`

---

#### Backend Modules

**Services:**
- snake_case
- `_service` suffix
- Ejemplos: `contract_service.py`, `client_service.py`

**Repositories:**
- snake_case
- `_repository` suffix
- Ejemplos: `contract_repository.py`, `client_repository.py`

**Routes:**
- snake_case
- `_routes` suffix
- Ejemplos: `legal_routes.py`, `auth_routes.py`

**DTOs:**
- PascalCase
- `Request`/`Response` suffix
- Ejemplos: `ContractGenerationRequest`, `ClientResponse`

---

## 5. APIs Disponibles

### 5.1. Endpoints de Autenticación

**Base URL:** `/api/auth`

| Método | Endpoint | Descripción | Auth | Roles |
|--------|----------|-------------|------|-------|
| POST | `/login` | Login de usuario | No | - |
| POST | `/register` | Registro de usuario | No | - |
| POST | `/logout` | Logout de usuario | Sí | Todos |
| GET | `/me` | Obtener perfil actual | Sí | Todos |
| PUT | `/me` | Actualizar perfil actual | Sí | Todos |

#### POST `/api/auth/login`

**Request:**
```json
{
  "email": "user@finkargo.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@finkargo.com"
  },
  "session": {
    "access_token": "jwt-token",
    "refresh_token": "refresh-token",
    "expires_at": 1699999999
  },
  "profile": {
    "full_name": "Usuario Test",
    "role": "admin",
    "assigned_modules": ["legal", "operations"]
  }
}
```

---

### 5.2. Endpoints de Core

**Base URL:** `/api`

| Método | Endpoint | Descripción | Auth | Roles |
|--------|----------|-------------|------|-------|
| GET | `/health` | Health check | No | - |
| GET | `/departments` | Lista de departamentos | Sí | Todos |
| GET | `/debug/cors` | Debug CORS config | No | - |

---

### 5.3. Endpoints de Legal

**Base URL:** `/api/legal`

| Método | Endpoint | Descripción | Auth | Roles |
|--------|----------|-------------|------|-------|
| GET | `/clients` | Lista de clientes | Sí | admin, legal, operations |
| GET | `/clients/search` | Buscar cliente por NIT | Sí | admin, legal, operations |
| POST | `/clients/import` | Importar clientes CSV | Sí | admin, legal, operations |
| GET | `/contracts` | Lista de contratos | Sí | admin, legal, operations |
| POST | `/contracts/generate` | Generar contrato | Sí | admin, legal, operations |
| PUT | `/contracts/{id}/review` | Revisar contrato | Sí | admin, legal |
| GET | `/contracts/{id}/download` | Descargar PDF | Sí | admin, legal, operations |
| GET | `/templates` | Lista de templates | Sí | admin, legal |
| POST | `/templates` | Subir template | Sí | admin, legal |

#### POST `/api/legal/contracts/generate`

**Request:**
```json
{
  "client_nit": "900123456-1",
  "contract_type": "activos",
  "additional_data": {
    "custom_field": "value"
  }
}
```

**Response (200):**
```json
{
  "contract_id": "ACT-2025-001",
  "client_nit": "900123456-1",
  "status": "generated",
  "pdf_url": "https://storage.supabase.co/...",
  "generated_at": "2025-11-11T10:00:00Z",
  "generated_by": "uuid"
}
```

---

### 5.4. Endpoints de Operations

**Base URL:** `/api/operations`

| Método | Endpoint | Descripción | Auth | Roles |
|--------|----------|-------------|------|-------|
| GET | `/dashboard` | Dashboard de operaciones | Sí | admin, operations |
| GET | `/imports` | Historial de importaciones | Sí | admin, operations |
| POST | `/imports/validate` | Validar archivo antes de importar | Sí | admin, operations |

---

### 5.5. Códigos de Estado HTTP

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Request exitoso |
| 201 | Created | Recurso creado exitosamente |
| 400 | Bad Request | Datos inválidos |
| 401 | Unauthorized | No autenticado |
| 403 | Forbidden | No autorizado (rol insuficiente) |
| 404 | Not Found | Recurso no encontrado |
| 422 | Unprocessable Entity | Validación Pydantic falló |
| 500 | Internal Server Error | Error del servidor |

---

### 5.6. Estructura de Error

**Response de Error:**
```json
{
  "detail": "Error message here",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-11-11T10:00:00Z"
}
```

---

## 6. Patrones de Diseño

### 6.1. Clean Architecture

**Principio:** Separación de responsabilidades en capas

```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│      (Adapter/REST Controllers)         │
│                                         │
│  - Recibe HTTP requests                 │
│  - Valida inputs (Pydantic)             │
│  - Llama a Service Layer                │
│  - Retorna HTTP responses               │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│          BUSINESS LAYER                 │
│         (Core/Services)                 │
│                                         │
│  - Lógica de negocio                    │
│  - Validaciones de dominio              │
│  - Orquestación de operaciones          │
│  - No conoce detalles de persistencia   │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│         DATA ACCESS LAYER               │
│        (Repositorio/Repository)         │
│                                         │
│  - CRUD operations                      │
│  - Queries a la base de datos           │
│  - Mapeo de modelos                     │
│  - Transacciones                        │
└─────────────────────────────────────────┘
```

**Ejemplo:**

```python
# adapter/rest/legal_routes.py
@router.post("/contracts/generate")
async def generate_contract(
    request: ContractGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    # Adapter Layer: Recibe request HTTP
    contract = await contract_service.generate_contract(
        request, current_user['user_id']
    )
    return contract

# core/servicios/contract_service.py
async def generate_contract(
    request: ContractGenerationRequest,
    user_id: str
) -> Contract:
    # Business Layer: Lógica de negocio
    client = await client_repository.get_by_nit(request.client_nit)
    template = await template_repository.get_active(request.contract_type)

    contract_id = generate_contract_id()
    pdf = generate_pdf(template, client)

    contract = await contract_repository.create({
        'contract_id': contract_id,
        'client_id': client.id,
        'generated_by': user_id,
        'pdf_url': pdf_url
    })

    return contract

# repositorio/contract_repository.py
async def create(data: dict) -> Contract:
    # Data Access Layer: Persistencia
    result = await supabase.table('contract_generations').insert(data).execute()
    return result.data
```

---

### 6.2. Repository Pattern

**Propósito:** Abstraer acceso a datos

```python
# repositorio/base_repository.py
class BaseRepository:
    def __init__(self, table_name: str):
        self.table = supabase.table(table_name)

    async def get_all(self):
        return await self.table.select('*').execute()

    async def get_by_id(self, id: str):
        return await self.table.select('*').eq('id', id).single().execute()

    async def create(self, data: dict):
        return await self.table.insert(data).execute()

    async def update(self, id: str, data: dict):
        return await self.table.update(data).eq('id', id).execute()

    async def delete(self, id: str):
        return await self.table.delete().eq('id', id).execute()

# repositorio/client_repository.py
class ClientRepository(BaseRepository):
    def __init__(self):
        super().__init__('clients')

    async def get_by_nit(self, nit: str):
        return await self.table.select('*').eq('nit', nit).single().execute()

    async def search(self, query: str):
        return await self.table.select('*').ilike('nombre_importador', f'%{query}%').execute()
```

---

### 6.3. Dependency Injection (FastAPI)

**Propósito:** Inyectar dependencias en endpoints

```python
# adapter/rest/dependencies.py
async def get_current_user(
    authorization: str = Header(None)
) -> dict:
    # Validar JWT y retornar usuario
    pass

async def require_role(allowed_roles: List[str]):
    def dependency(current_user: dict = Depends(get_current_user)):
        if current_user['profile']['role'] not in allowed_roles:
            raise HTTPException(403)
        return current_user
    return Depends(dependency)

# Uso en endpoint
@router.post("/contracts/generate")
async def generate_contract(
    request: ContractGenerationRequest,
    current_user: dict = Depends(require_role(['admin', 'legal']))
):
    # current_user ya está validado y autorizado
    pass
```

---

### 6.4. Context API (React)

**Propósito:** Estado global sin prop drilling

```typescript
// contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  session: Session | null;
  userProfile: UserProfile | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  userProfile: null,
  loading: true,
  signIn: async () => {},
  signOut: async () => {},
  isAuthenticated: false,
});

export const AuthProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // ... lógica de auth ...

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// hooks/useAuth.ts
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

---

### 6.5. Custom Hooks Pattern

**Propósito:** Reutilizar lógica de componentes

```typescript
// hooks/useAPI.ts
export const useAPI = <T,>(
  endpoint: string,
  options?: RequestInit
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(endpoint, options);
        const json = await response.json();
        setData(json);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint]);

  return { data, loading, error };
};

// Uso en componente
const MyComponent = () => {
  const { data, loading, error } = useAPI<Client[]>('/api/legal/clients');

  if (loading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return (
    <div>
      {data.map(client => <ClientCard key={client.id} client={client} />)}
    </div>
  );
};
```

---

### 6.6. HOC (Higher-Order Component)

**Propósito:** Añadir funcionalidad a componentes

```typescript
// components/ProtectedRoute.tsx
const ProtectedRoute: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Uso
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <DashboardPage />
    </ProtectedRoute>
  }
/>
```

---

## 7. Configuración de Ambientes

### 7.1. Ambientes Disponibles

| Ambiente | Propósito | URL | Branch Git |
|----------|-----------|-----|------------|
| **Local** | Desarrollo individual | localhost:5173 / localhost:8000 | feature/* |
| **Development** | Testing de integración | dev.finkargo.com | develop |
| **Staging** | Pre-producción | staging.finkargo.com | release/* |
| **Production** | Producción | app.finkargo.com | main |

---

### 7.2. Variables de Entorno por Ambiente

#### Backend

**Local (`backend/.env`):**
```bash
DEBUG=true
APP_NAME=Finkargo Automation Hub
PYTHON_VERSION=3.11.9

SUPABASE_URL=https://your-dev-project.supabase.co
SUPABASE_ANON_KEY=your-dev-anon-key
SUPABASE_SERVICE_KEY=your-dev-service-key
SUPABASE_JWT_SECRET=your-dev-jwt-secret

SECRET_KEY=your-local-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=["http://localhost:5173"]

DATABASE_URL=postgresql://your-dev-connection-string

MAX_UPLOAD_SIZE=10485760
SUPPORTED_FILE_TYPES=[".pdf",".jpg",".jpeg",".png",".xlsx",".xls"]
```

**Production (Environment Variables en Render):**
```bash
DEBUG=false
APP_NAME=Finkargo Automation Hub
PYTHON_VERSION=3.11.9

SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_ANON_KEY=your-prod-anon-key
SUPABASE_SERVICE_KEY=your-prod-service-key
SUPABASE_JWT_SECRET=your-prod-jwt-secret

SECRET_KEY=your-prod-secret-key-very-secure
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=["https://app.finkargo.com","https://*.vercel.app"]

DATABASE_URL=postgresql://your-prod-connection-string

MAX_UPLOAD_SIZE=10485760
SUPPORTED_FILE_TYPES=[".pdf",".jpg",".jpeg",".png",".xlsx",".xls"]
```

---

#### Frontend

**Local (`frontend/.env`):**
```bash
VITE_SUPABASE_URL=https://your-dev-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-dev-anon-key

VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000

VITE_APP_NAME=Finkargo Automation Hub
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEBUG=true
VITE_ENABLE_ANALYTICS=false

VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png,.xlsx,.xls

VITE_DEFAULT_LOCALE=es-MX
VITE_DEFAULT_CURRENCY=MXN
```

**Production (Environment Variables en Vercel):**
```bash
VITE_SUPABASE_URL=https://your-prod-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-prod-anon-key

VITE_API_URL=https://api.finkargo.com/api
VITE_API_TIMEOUT=30000

VITE_APP_NAME=Finkargo Automation Hub
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEBUG=false
VITE_ENABLE_ANALYTICS=true

VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png,.xlsx,.xls

VITE_DEFAULT_LOCALE=es-MX
VITE_DEFAULT_CURRENCY=MXN
```

---

### 7.3. Estructura de Proyectos Supabase

| Ambiente | Proyecto Supabase | Propósito |
|----------|------------------|-----------|
| Local | `finkargo-hub-your-name` | Individual por desarrollador |
| Development | `finkargo-hub-dev` | Compartido por el equipo |
| Staging | `finkargo-hub-staging` | Pre-producción |
| Production | `finkargo-hub-prod` | Producción |

---

### 7.4. Deployment Pipelines

#### Frontend (Vercel)

```
┌──────────────────┐
│  Git Push        │
│  to feature/*    │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Vercel          │
│  Auto Deploy     │
│  Preview URL     │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Manual Merge    │
│  to main         │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Vercel          │
│  Production      │
│  Deploy          │
└──────────────────┘
```

**Configuración (`vercel.json`):**
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

---

#### Backend (Render)

```
┌──────────────────┐
│  Git Push        │
│  to main         │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Render          │
│  Auto Build      │
│  pip install     │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Render          │
│  Deploy          │
│  uvicorn start   │
└──────────────────┘
```

**Configuración:**
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:** Configuradas en Render Dashboard

---

## 8. Checklist de Integración

### 8.1. Análisis de Tu Funcionalidad

Antes de integrar, responde estas preguntas:

**Funcionalidad:**
- [ ] ¿Qué hace tu funcionalidad?
- [ ] ¿Qué problema resuelve?
- [ ] ¿Qué departamento(s) la usará(n)?
- [ ] ¿Qué roles necesitan acceso?

**Datos:**
- [ ] ¿Qué tablas necesitas?
- [ ] ¿Qué campos tienen las tablas?
- [ ] ¿Qué relaciones hay entre tablas?
- [ ] ¿Necesitas datos de tablas existentes?

**Lógica de Negocio:**
- [ ] ¿Qué validaciones necesitas?
- [ ] ¿Qué cálculos se requieren?
- [ ] ¿Hay flujos de aprobación?
- [ ] ¿Necesitas notificaciones?

**Archivos:**
- [ ] ¿Subes archivos?
- [ ] ¿Generas archivos (PDF, Excel)?
- [ ] ¿Qué tipos de archivos permites?
- [ ] ¿Dónde se almacenan?

---

### 8.2. Paso 1: Diseño de Base de Datos

#### 1.1. Crear Migración SQL

```sql
-- backend/database/migration_add_[feature_name].sql
-- Migration: Add [Feature Name] Support
-- Date: 2025-11-XX
-- Author: Tu Nombre
-- Description: [Descripción de lo que agrega]

-- Crear tabla principal
CREATE TABLE IF NOT EXISTS tu_tabla (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,

    -- Relaciones
    user_id UUID REFERENCES auth.users(id),

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Índices
CREATE INDEX idx_tu_tabla_nombre ON tu_tabla(nombre);

-- RLS Policies
ALTER TABLE tu_tabla ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read"
ON tu_tabla FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can create their own"
ON tu_tabla FOR INSERT
TO authenticated
WITH CHECK (created_by = auth.uid());
```

#### 1.2. Ejecutar en Supabase

1. Ir a SQL Editor
2. Copiar migración
3. Ejecutar
4. Verificar tablas creadas

---

### 8.3. Paso 2: Backend Implementation

#### 2.1. Crear DTOs

```python
# backend/src/interface/tu_feature_dtos.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TuFeatureRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class TuFeatureResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str]
    created_at: datetime
    created_by: str
```

#### 2.2. Crear Repository

```python
# backend/src/repositorio/tu_feature_repository.py
from typing import List, Optional

class TuFeatureRepository:
    def __init__(self):
        self.table = supabase.table('tu_tabla')

    async def get_all(self) -> List[dict]:
        result = await self.table.select('*').execute()
        return result.data

    async def get_by_id(self, id: str) -> Optional[dict]:
        result = await self.table.select('*').eq('id', id).single().execute()
        return result.data

    async def create(self, data: dict) -> dict:
        result = await self.table.insert(data).execute()
        return result.data[0]

    async def update(self, id: str, data: dict) -> dict:
        result = await self.table.update(data).eq('id', id).execute()
        return result.data[0]

    async def delete(self, id: str):
        await self.table.delete().eq('id', id).execute()
```

#### 2.3. Crear Service

```python
# backend/src/core/servicios/tu_feature_service.py
class TuFeatureService:
    def __init__(self):
        self.repository = TuFeatureRepository()

    async def create_item(self, request: TuFeatureRequest, user_id: str):
        # Validaciones de negocio
        if not request.nombre:
            raise ValueError("Nombre es requerido")

        # Crear en base de datos
        data = {
            'nombre': request.nombre,
            'descripcion': request.descripcion,
            'created_by': user_id
        }

        item = await self.repository.create(data)
        return item

    async def get_items(self, user_id: str, role: str):
        # Lógica según rol
        items = await self.repository.get_all()

        # Filtrar según rol si es necesario
        if role != 'admin':
            items = [item for item in items if item['created_by'] == user_id]

        return items
```

#### 2.4. Crear Routes

```python
# backend/src/adapter/rest/tu_feature_routes.py
from fastapi import APIRouter, Depends
from typing import List

router = APIRouter(prefix="/api/tu-feature", tags=["Tu Feature"])
service = TuFeatureService()

@router.get("/", response_model=List[TuFeatureResponse])
async def get_items(
    current_user: dict = Depends(get_current_user)
):
    """Obtener todos los items"""
    items = await service.get_items(
        current_user['user_id'],
        current_user['profile']['role']
    )
    return items

@router.post("/", response_model=TuFeatureResponse, status_code=201)
async def create_item(
    request: TuFeatureRequest,
    current_user: dict = Depends(require_roles(['admin', 'tu_rol']))
):
    """Crear nuevo item"""
    item = await service.create_item(request, current_user['user_id'])
    return item

@router.get("/{id}", response_model=TuFeatureResponse)
async def get_item(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener item por ID"""
    item = await service.get_item_by_id(id)
    if not item:
        raise HTTPException(404, "Item no encontrado")
    return item
```

#### 2.5. Registrar Router

```python
# backend/main.py
from src.adapter.rest import tu_feature_routes

app.include_router(tu_feature_routes.router)
```

---

### 8.4. Paso 3: Frontend Implementation

#### 3.1. Crear Types

```typescript
// frontend/src/types/tuFeature.ts
export interface TuFeature {
  id: string;
  nombre: string;
  descripcion?: string;
  created_at: string;
  created_by: string;
}

export interface TuFeatureRequest {
  nombre: string;
  descripcion?: string;
}
```

#### 3.2. Crear Service

```typescript
// frontend/src/services/tuFeatureService.ts
import { apiClient } from '../api/clients/apiClient';
import type { TuFeature, TuFeatureRequest } from '../types/tuFeature';

export const tuFeatureService = {
  async getAll(): Promise<TuFeature[]> {
    const response = await apiClient.get('/tu-feature');
    return response.data;
  },

  async getById(id: string): Promise<TuFeature> {
    const response = await apiClient.get(`/tu-feature/${id}`);
    return response.data;
  },

  async create(data: TuFeatureRequest): Promise<TuFeature> {
    const response = await apiClient.post('/tu-feature', data);
    return response.data;
  },

  async update(id: string, data: Partial<TuFeatureRequest>): Promise<TuFeature> {
    const response = await apiClient.put(`/tu-feature/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/tu-feature/${id}`);
  }
};
```

#### 3.3. Crear Form Component

```typescript
// frontend/src/components/forms/FKTuFeatureForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { TextField, Button, Box } from '@mui/material';
import type { TuFeatureRequest } from '../../types/tuFeature';

interface FKTuFeatureFormProps {
  onSubmit: (data: TuFeatureRequest) => Promise<void>;
  initialData?: TuFeatureRequest;
}

export const FKTuFeatureForm: React.FC<FKTuFeatureFormProps> = ({
  onSubmit,
  initialData
}) => {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<TuFeatureRequest>({
    defaultValues: initialData
  });

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)}>
      <TextField
        label="Nombre"
        fullWidth
        margin="normal"
        {...register('nombre', { required: 'Nombre es requerido' })}
        error={!!errors.nombre}
        helperText={errors.nombre?.message}
      />

      <TextField
        label="Descripción"
        fullWidth
        margin="normal"
        multiline
        rows={4}
        {...register('descripcion')}
      />

      <Button
        type="submit"
        variant="contained"
        disabled={isSubmitting}
        sx={{ mt: 2 }}
      >
        {isSubmitting ? 'Guardando...' : 'Guardar'}
      </Button>
    </Box>
  );
};
```

#### 3.4. Crear Dashboard/Page

```typescript
// frontend/src/pages/tu-departamento/TuFeatureDashboard.tsx
import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress
} from '@mui/material';
import { FKTuFeatureForm } from '../../components/forms/FKTuFeatureForm';
import { tuFeatureService } from '../../services/tuFeatureService';
import type { TuFeature, TuFeatureRequest } from '../../types/tuFeature';

export const TuFeatureDashboard: React.FC = () => {
  const [items, setItems] = useState<TuFeature[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      const data = await tuFeatureService.getAll();
      setItems(data);
    } catch (error) {
      console.error('Error loading items:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data: TuFeatureRequest) => {
    try {
      await tuFeatureService.create(data);
      setShowForm(false);
      loadItems(); // Recargar lista
    } catch (error) {
      console.error('Error creating item:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Tu Feature Dashboard</Typography>
        <Button
          variant="contained"
          onClick={() => setShowForm(true)}
        >
          Crear Nuevo
        </Button>
      </Box>

      {showForm && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <FKTuFeatureForm onSubmit={handleCreate} />
          </CardContent>
        </Card>
      )}

      {items.map(item => (
        <Card key={item.id} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6">{item.nombre}</Typography>
            <Typography color="text.secondary">{item.descripcion}</Typography>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};
```

#### 3.5. Agregar Ruta

```typescript
// frontend/src/App.tsx
import { TuFeatureDashboard } from './pages/tu-departamento/TuFeatureDashboard';

<Route
  path="department/tu-departamento"
  element={
    <RoleProtectedRoute allowedRoles={['admin', 'tu_rol']}>
      <TuFeatureDashboard />
    </RoleProtectedRoute>
  }
/>
```

---

### 8.5. Paso 4: Testing

#### Backend Testing

```python
# backend/tests/test_tu_feature.py
import pytest
from src.core.servicios.tu_feature_service import TuFeatureService

@pytest.fixture
def service():
    return TuFeatureService()

async def test_create_item(service):
    request = TuFeatureRequest(
        nombre="Test Item",
        descripcion="Test Description"
    )

    item = await service.create_item(request, "user-id")

    assert item['nombre'] == "Test Item"
    assert item['descripcion'] == "Test Description"

async def test_get_items(service):
    items = await service.get_items("user-id", "admin")

    assert isinstance(items, list)
```

**Ejecutar:**
```bash
cd backend
pytest tests/
```

---

#### Frontend Testing

```typescript
// frontend/src/services/__tests__/tuFeatureService.test.ts
import { tuFeatureService } from '../tuFeatureService';

describe('TuFeatureService', () => {
  it('should fetch all items', async () => {
    const items = await tuFeatureService.getAll();
    expect(Array.isArray(items)).toBe(true);
  });

  it('should create item', async () => {
    const data = {
      nombre: 'Test Item',
      descripcion: 'Test Description'
    };

    const item = await tuFeatureService.create(data);
    expect(item.nombre).toBe('Test Item');
  });
});
```

**Ejecutar:**
```bash
cd frontend
npm test
```

---

### 8.6. Paso 5: Documentación

#### 5.1. Crear Implementation Doc

```markdown
# Implementation: [Feature Name]

**Date:** 2025-11-XX
**Developer:** Tu Nombre
**Status:** ✅ Complete

## Overview
Descripción de la funcionalidad.

## Database Changes
- Nueva tabla: `tu_tabla`
- Campos principales: ...

## API Endpoints
- GET `/api/tu-feature` - Lista de items
- POST `/api/tu-feature` - Crear item
- GET `/api/tu-feature/{id}` - Obtener por ID

## Frontend Components
- `FKTuFeatureForm` - Formulario
- `TuFeatureDashboard` - Dashboard principal

## Testing
- Unit tests: backend/tests/test_tu_feature.py
- Integration tests: frontend/src/services/__tests__/

## Deployment
- Migración ejecutada en: Local, Dev, Staging, Prod
- Feature deployado en: Vercel, Render

## Known Issues
- Ninguno

## Future Improvements
- [ ] Agregar filtros
- [ ] Agregar paginación
```

#### 5.2. Actualizar CLAUDE.md

Agregar tu módulo a la documentación del proyecto.

---

## Conclusión

Este blueprint te proporciona toda la información técnica necesaria para integrar funcionalidades externas al Finkargo Automation Hub:

✅ **Stack Tecnológico** - Versiones exactas y compatibilidad
✅ **Esquema de BD** - Tablas, relaciones, RLS policies
✅ **Autenticación/Autorización** - Flujos completos con ejemplos
✅ **Estructura de Módulos** - Clean Architecture aplicada
✅ **APIs Disponibles** - Endpoints documentados con ejemplos
✅ **Patrones de Diseño** - Patrones usados en el proyecto
✅ **Configuración de Ambientes** - Local, Dev, Staging, Prod
✅ **Checklist de Integración** - Paso a paso completo

**Próximos Pasos:**
1. Analizar tu funcionalidad con el checklist
2. Diseñar el schema de BD
3. Implementar backend siguiendo los patrones
4. Implementar frontend con los componentes base
5. Testear end-to-end
6. Documentar la implementación

---

**Versión:** 1.0
**Última Actualización:** November 11, 2025
**Mantenido por:** Equipo Finkargo Dev
