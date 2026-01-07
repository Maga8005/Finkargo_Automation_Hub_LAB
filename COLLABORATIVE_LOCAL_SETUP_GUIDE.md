# Guía: Configuración de Ambiente Local para Desarrollo Colaborativo

**Propósito:** Guía paso a paso para configurar un ambiente de desarrollo local cuando trabajas colaborativamente en un proyecto existente.

**Audiencia:** Desarrolladores que se unen a un proyecto Finkargo existente

**Tiempo Estimado:** 1-2 horas

---

## 📋 Tabla de Contenidos

1. [Conceptos Fundamentales](#conceptos-fundamentales)
2. [Pre-requisitos](#pre-requisitos)
3. [Paso a Paso: Configuración Inicial](#paso-a-paso-configuración-inicial)
4. [Solución de Problemas Comunes](#solución-de-problemas-comunes)
5. [Mejores Prácticas](#mejores-prácticas)
6. [Flujo de Trabajo Diario](#flujo-de-trabajo-diario)

---

## Conceptos Fundamentales

### ¿Por Qué Necesito Mi Propio Ambiente?

Cuando trabajas colaborativamente en un proyecto, es **fundamental** que cada desarrollador tenga su propio ambiente de desarrollo independiente. Aquí está el por qué:

#### ❌ Problema: Compartir Base de Datos de Desarrollo
```
Desarrollador A                  Desarrollador B
      ↓                                ↓
      └────────► Supabase Dev ◄────────┘
                (compartida)

Problemas:
- A ejecuta migración que rompe el schema
- B pierde datos de prueba
- Conflictos en desarrollo
- No se puede experimentar libremente
```

#### ✅ Solución: Ambientes Independientes
```
Desarrollador A          Desarrollador B
      ↓                        ↓
  Supabase A              Supabase B
  (aislado)               (aislado)
      ↓                        ↓
      └─────► Git Repo ◄───────┘
           (código compartido)
```

**Ventajas:**
- ✅ Libertad para experimentar sin romper nada
- ✅ No afectas el trabajo de otros desarrolladores
- ✅ Puedes crear/borrar datos de prueba libremente
- ✅ Debugging más fácil (sabes que el problema es tuyo)
- ✅ Puedes resetear tu ambiente cuando quieras

---

## Pre-requisitos

### 1. Software Requerido

#### Node.js (Frontend)
```bash
# Verificar versión instalada
node --version

# Requerido: v18.x o superior
# Recomendado: v20.x
```

**Instalación:** https://nodejs.org/en/download/

#### Python (Backend)
```bash
# Verificar versión instalada
python --version

# Requerido: 3.11.x
# Compatible: 3.13.x (aunque puede haber advertencias)
```

**Instalación:** https://www.python.org/downloads/

#### Git
```bash
# Verificar instalación
git --version
```

**Instalación:** https://git-scm.com/downloads

#### Editor de Código
- **Recomendado:** Visual Studio Code
- **Alternativas:** WebStorm, PyCharm, Cursor

### 2. Cuentas Requeridas

| Servicio | Propósito | URL | Plan |
|----------|-----------|-----|------|
| **Supabase** | Base de datos y autenticación | https://supabase.com | Free |
| **GitHub** | Control de versiones | https://github.com | Free |
| **Vercel** (Opcional) | Preview deployments | https://vercel.com | Free |
| **Render** (Opcional) | Backend hosting | https://render.com | Free |

---

## Paso a Paso: Configuración Inicial

### Fase 1: Clonar el Repositorio

#### 1.1. Obtener Acceso al Repositorio

Solicita al líder del equipo:
- Acceso al repositorio en GitHub
- Permisos de escritura (para crear ramas)
- Link al repositorio

#### 1.2. Clonar Localmente

```bash
# Navegar a tu carpeta de proyectos
cd C:\Users\tu-usuario\proyectos

# Clonar el repositorio
git clone https://github.com/organizacion/nombre-proyecto.git

# Entrar al directorio
cd nombre-proyecto

# Verificar que clonó correctamente
ls -la
```

**Verificación:** Deberías ver carpetas como `backend/`, `frontend/`, `README.md`, etc.

---

### Fase 2: Crear Tu Propio Supabase

#### 2.1. Crear Proyecto en Supabase

1. **Ir a:** https://supabase.com
2. **Registrarse/Login** con GitHub (recomendado) o email
3. **Click en:** "New Project"
4. **Completar formulario:**
   - **Name:** `nombre-proyecto-tu-nombre` (ej: `finkargo-hub-maria`)
   - **Database Password:** Genera una contraseña segura
   - 📋 **IMPORTANTE:** Copia esta contraseña inmediatamente y guárdala en un lugar seguro
   - **Region:** South America (São Paulo) - más cercano a Colombia
   - **Pricing Plan:** Free
5. **Click:** "Create new project"
6. **Esperar 1-2 minutos** mientras se crea

#### 2.2. Obtener Credenciales

Una vez creado el proyecto:

**A. Project URL y API Keys**

1. Ve a **Settings** (⚙️ en sidebar)
2. Click en **API**
3. Copia y guarda:

```
📋 Project URL:
https://xxxxxxxxxx.supabase.co

📋 anon public (API Key):
eyJhbGc...

📋 service_role secret:
eyJhbGc...
```

**B. JWT Secret**

En la misma página, baja hasta **JWT Settings**:

```
📋 JWT Secret:
tu-jwt-secret-aqui
```

**C. Connection String**

1. Ve a **Settings** → **Database**
2. En "Connection string", selecciona **URI**
3. Copia el string:

```
📋 Database URL:
postgresql://postgres:[YOUR-PASSWORD]@...
```

4. **Reemplaza `[YOUR-PASSWORD]`** con la contraseña que generaste en el paso 2.1

**📝 Nota:** Guarda todas estas credenciales en un archivo temporal (las usarás pronto).

---

### Fase 3: Ejecutar Migraciones de Base de Datos

#### 3.1. Identificar Migraciones del Proyecto

```bash
# Ver las migraciones disponibles
ls backend/database/

# Deberías ver archivos como:
# - schema.sql (esquema base)
# - migration_*.sql (migraciones adicionales)
# - README.md (instrucciones)
```

#### 3.2. Leer el README

```bash
# Ver las instrucciones
cat backend/database/README.md
```

Este archivo te dirá el **orden** en que debes ejecutar las migraciones.

#### 3.3. Ejecutar Schema Base

1. **Abrir Supabase SQL Editor:**
   - En tu proyecto Supabase
   - Click en **SQL Editor** (icono 📝)
   - Click en **+ New query**

2. **Copiar contenido de `schema.sql`:**
   ```bash
   # Abrir el archivo en tu editor
   code backend/database/schema.sql

   # O ver en terminal
   cat backend/database/schema.sql
   ```

3. **Pegar en SQL Editor** y click **Run**

4. **Verificar que funcionó:**
   ```sql
   -- Copiar y ejecutar esto
   SELECT tablename
   FROM pg_tables
   WHERE schemaname = 'public';
   ```

   Deberías ver las tablas creadas.

#### 3.4. Ejecutar Migraciones Adicionales

Repite el proceso anterior para cada migración adicional **en orden**:

Orden típico:
1. `schema.sql` (base)
2. `migration_create_user_profiles.sql`
3. `migration_add_legal_operations_roles.sql`
4. Otras migraciones según el README

**⚠️ IMPORTANTE:** Ejecuta las migraciones en el orden especificado en el README.

---

### Fase 4: Configurar Variables de Entorno

#### 4.1. Backend

```bash
# Navegar a backend
cd backend

# Copiar el template
cp .env.example .env

# Editar con tu editor favorito
code .env
# o
nano .env
# o
notepad .env
```

**Reemplazar estas líneas con tus credenciales de Supabase:**

```bash
# Supabase Configuration
SUPABASE_URL=https://tu-project-id.supabase.co
SUPABASE_ANON_KEY=tu-anon-key-aqui
SUPABASE_SERVICE_KEY=tu-service-key-aqui
SUPABASE_JWT_SECRET=tu-jwt-secret-aqui

# Database (con tu contraseña)
DATABASE_URL=postgresql://postgres:TU-PASSWORD@...

# Security - Generar nuevo SECRET_KEY
SECRET_KEY=ejecuta-el-comando-de-abajo
```

**Generar SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copia el resultado y pégalo en `SECRET_KEY=`.

**Las demás líneas** (DEBUG, CORS_ORIGINS, etc.) puedes dejarlas como están para desarrollo local.

#### 4.2. Frontend

```bash
# Navegar a frontend
cd frontend

# Copiar el template
cp .env.example .env

# Editar
code .env
```

**Reemplazar:**

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://tu-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key-aqui

# API Configuration (dejar como está para local)
VITE_API_URL=http://localhost:8000/api
```

**Las demás líneas** puedes dejarlas como están.

**⚠️ CRÍTICO:**
- Nunca subas los archivos `.env` a Git
- Verifica que `.env` esté en `.gitignore`
- No compartas tus credenciales de Supabase

---

### Fase 5: Instalar Dependencias

#### 5.1. Backend (Python)

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate

# Verificar que está activado (deberías ver (venv) en el prompt)

# Instalar dependencias
pip install -r requirements.txt

# Esperar 2-5 minutos mientras instala
```

**Verificación:**
```bash
# Deberías ver FastAPI instalado
pip list | grep fastapi
```

#### 5.2. Frontend (Node.js)

```bash
cd frontend

# Instalar dependencias
npm install

# Esperar 1-3 minutos mientras instala
```

**Verificación:**
```bash
# Deberías ver node_modules creado
ls -la | grep node_modules
```

---

### Fase 6: Crear Tu Usuario

#### 6.1. Crear Usuario en Supabase Auth

1. **Ve a tu proyecto en Supabase**
2. **Click en Authentication** (👤 en sidebar)
3. **Click en "Add user" → "Create new user"**
4. **Completar:**
   - Email: `tu-email@finkargo.com`
   - Password: Tu contraseña (guárdala)
   - ✅ **Auto Confirm User** - IMPORTANTE: activar
5. **Click "Create user"**
6. **Copiar el User ID** (UUID) que aparece

#### 6.2. Crear Perfil de Usuario

En **SQL Editor**, ejecuta (reemplaza `YOUR-USER-ID` y tu nombre):

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
    'YOUR-USER-ID-AQUI',
    'Tu Nombre Completo',
    'admin',
    true,
    ARRAY['legal', 'operations', 'finance', 'hr', 'technology', 'sales', 'customer-service', 'collections'],
    NOW()
);
```

**Verificar:**
```sql
SELECT * FROM user_profiles WHERE id = 'YOUR-USER-ID-AQUI';
```

Deberías ver tu perfil.

---

### Fase 7: Iniciar Servidores

#### 7.1. Backend

**Terminal 1:**
```bash
cd backend

# Activar entorno virtual (si no está activado)
venv\Scripts\activate

# Iniciar servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Deberías ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verificar:**
- Abre navegador: http://localhost:8000/docs
- Deberías ver la documentación de la API (Swagger UI)

#### 7.2. Frontend

**Terminal 2 (nueva terminal):**
```bash
cd frontend

# Iniciar servidor
npm run dev
```

**Deberías ver:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

**Verificar:**
- Abre navegador: http://localhost:5173
- Deberías ver la página de login

---

### Fase 8: Primer Login

1. **Ve a:** http://localhost:5173
2. **Ingresa credenciales:**
   - Email: El que creaste en Fase 6.1
   - Password: Tu contraseña
3. **Click "Iniciar Sesión"**
4. **Deberías ver:**
   - Dashboard principal
   - Sidebar con departamentos
   - Tu nombre en la esquina superior derecha

**🎉 ¡Éxito! Tu ambiente está funcionando.**

---

## Solución de Problemas Comunes

### Problema 1: Frontend Se Queda "Cargando..."

**Síntomas:**
- Spinner infinito con mensaje "Cargando..."
- No hay errores en consola

**Causa:** Browser cache con credenciales antiguas

**Solución:**
```
1. Presionar F12 (abrir DevTools)
2. Ir a tab "Application"
3. Sidebar → "Local Storage" → localhost:5173
4. Click derecho → "Clear"
5. Recargar página (F5)
```

**Alternativa:** Abrir en modo incógnito (Ctrl+Shift+N)

---

### Problema 2: Sidebar Sin Departamentos

**Síntomas:**
- Login exitoso
- Dashboard carga
- Sidebar muestra "DEPARTAMENTOS" pero vacío

**Causa:** Falta perfil en `user_profiles`

**Diagnóstico:**
```sql
-- Verificar si existe tu perfil
SELECT * FROM user_profiles WHERE id = 'tu-user-id';
```

**Si no existe:**
```sql
-- Crear perfil (ver Fase 6.2)
INSERT INTO user_profiles ...
```

**Si existe pero sidebar vacío:**
```sql
-- Verificar RLS
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
-- Recargar página
-- Si funciona, el problema es RLS
```

**Solución RLS:**
```sql
-- Re-habilitar con política permisiva
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read profiles"
ON user_profiles
FOR SELECT
TO authenticated
USING (true);
```

---

### Problema 3: Error "Port 5173 is already in use"

**Causa:** Ya hay un proceso usando el puerto

**Solución en Windows:**
```bash
# Encontrar el proceso
netstat -ano | findstr :5173

# Matar el proceso (reemplaza PID)
taskkill /PID numero-del-pid /F
```

**Solución en Mac/Linux:**
```bash
# Encontrar el proceso
lsof -i :5173

# Matar el proceso
kill -9 PID
```

**Alternativa:** Usar otro puerto
```bash
# En frontend
npm run dev -- --port 5174
```

---

### Problema 4: Error "Module not found"

**Causa:** Dependencias no instaladas o corruptas

**Solución Backend:**
```bash
cd backend
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Solución Frontend:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

### Problema 5: Error de Conexión a Supabase

**Síntomas:**
```
Error: Failed to fetch
NetworkError when attempting to fetch resource
```

**Diagnóstico:**
```bash
# Verificar variables de entorno
# Backend:
cd backend && cat .env | grep SUPABASE_URL

# Frontend:
cd frontend && cat .env | grep VITE_SUPABASE_URL
```

**Verificar:**
- ✅ Las URLs son correctas (sin espacios)
- ✅ Las API keys son completas (sin cortes)
- ✅ El proyecto de Supabase está activo (no pausado)

**Solución:** Reemplazar credenciales con las correctas y reiniciar servidores.

---

### Problema 6: CORS Errors

**Síntomas:**
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**Causa:** Backend no permite peticiones desde frontend

**Solución:**
```bash
# Verificar CORS_ORIGINS en backend/.env
CORS_ORIGINS=["http://localhost:5173"]

# Reiniciar backend
Ctrl+C en terminal del backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Mejores Prácticas

### 1. Workflow Git

#### Nunca Trabajes en `main` o `master`

```bash
# ❌ MAL
git checkout main
# ... hacer cambios ...
git commit -m "cambios"

# ✅ BIEN
git checkout -b feature-mi-funcionalidad
# ... hacer cambios ...
git commit -m "feat: descripción de mi funcionalidad"
```

#### Nombres de Ramas

**Formato:** `tipo-descripcion-breve`

**Tipos:**
- `feature-*` - Nueva funcionalidad
- `fix-*` - Corrección de bug
- `refactor-*` - Refactorización
- `docs-*` - Documentación
- `test-*` - Tests

**Ejemplos:**
```bash
feature-user-registration
fix-login-validation
refactor-auth-service
docs-api-endpoints
```

#### Commits

**Formato:** `tipo: descripción breve`

**Tipos:**
- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `refactor:` - Refactorización
- `docs:` - Documentación
- `test:` - Tests
- `chore:` - Tareas de mantenimiento

**Ejemplos:**
```bash
git commit -m "feat: add user profile page"
git commit -m "fix: correct validation in login form"
git commit -m "docs: update README with setup instructions"
```

---

### 2. Manejo de Migraciones

#### Nunca Modifiques Migraciones Existentes

```bash
# ❌ MAL
# Editar backend/database/migration_xxx.sql

# ✅ BIEN
# Crear nueva migración
backend/database/migration_add_new_field.sql
```

#### Documenta Tus Migraciones

```sql
-- Migration: Add email verification field
-- Date: 2025-11-11
-- Author: Maria Gaitan
-- Description: Adds email_verified field to user_profiles

ALTER TABLE user_profiles
ADD COLUMN email_verified BOOLEAN DEFAULT false;
```

#### Comparte Migraciones con el Equipo

```bash
# 1. Crear migración
# 2. Probar en tu DB local
# 3. Commit a Git
git add backend/database/migration_*.sql
git commit -m "feat: add email verification migration"

# 4. Notificar al equipo
# "Nueva migración disponible: migration_xxx.sql"
```

---

### 3. Seguridad

#### Nunca Subas Credenciales

```bash
# Verificar antes de cada commit
git status

# Si ves .env listado:
# ❌ NO HAGAS git add .env

# Verificar .gitignore
cat .gitignore | grep .env
# Debería mostrar:
# .env
# *.env
```

#### Rotar Credenciales si se Exponen

Si accidentalmente subes credenciales:

1. **Remover del historial:**
```bash
git filter-branch --force --index-filter \
"git rm --cached --ignore-unmatch backend/.env" \
--prune-empty --tag-name-filter cat -- --all
```

2. **Regenerar credenciales en Supabase:**
   - Settings → API → "Reset API Key"
   - Database → Reset password

3. **Notificar al equipo**

---

### 4. Sincronización con el Equipo

#### Pull Frecuentemente

```bash
# Al inicio del día
git checkout main
git pull origin main

# Antes de crear nueva rama
git pull origin main
git checkout -b feature-nueva

# Antes de hacer merge
git checkout main
git pull origin main
git merge feature-nueva
```

#### Comunicar Cambios Importantes

**Cuándo notificar:**
- Cambios en schema de DB
- Nuevas variables de entorno requeridas
- Cambios en dependencias (package.json, requirements.txt)
- Cambios en configuración (CORS, API endpoints)

**Cómo notificar:**
- Mensaje en Slack/Teams
- Pull Request description
- Session notes
- README updates

---

### 5. Debugging

#### Logs Estructurados

**Backend:**
```python
import logging

logger = logging.getLogger(__name__)

# En tu código
logger.info(f"User {user_id} logged in")
logger.error(f"Failed to fetch profile: {error}")
```

**Frontend:**
```typescript
// Usar prefijos para filtrar
console.log('[AuthContext] Initializing...');
console.error('[API] Failed to fetch:', error);
```

#### Browser DevTools

**Network Tab:**
- Filtrar por `localhost:8000` para ver API calls
- Click en request → ver Response
- Verificar Status Codes (200, 401, 500, etc.)

**Console Tab:**
- Filtrar por texto: `[AuthContext]`
- Ver errores en rojo
- Expandir objetos para inspeccionar

**Application Tab:**
- Local Storage → ver tokens guardados
- Session Storage → ver datos de sesión
- Cookies → ver cookies de Supabase

---

## Flujo de Trabajo Diario

### Inicio del Día

```bash
# 1. Actualizar código
cd /ruta/al/proyecto
git checkout main
git pull origin main

# 2. Verificar si hay nuevas migraciones
git log --oneline backend/database/

# Si hay migraciones nuevas:
# - Abrir Supabase SQL Editor
# - Ejecutar nuevas migraciones

# 3. Verificar si hay nuevas dependencias
git log --oneline package.json requirements.txt

# Si hay cambios:
cd backend && pip install -r requirements.txt
cd frontend && npm install

# 4. Iniciar servidores
# Terminal 1:
cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2:
cd frontend && npm run dev
```

---

### Durante el Desarrollo

```bash
# 1. Crear rama para tu feature
git checkout -b feature-mi-funcionalidad

# 2. Hacer cambios
# ... editar archivos ...

# 3. Probar localmente
# - Verificar en navegador
# - Ver logs en terminales
# - Testear funcionalidad

# 4. Commit frecuente
git add .
git commit -m "feat: add user search functionality"

# 5. Push al remoto
git push origin feature-mi-funcionalidad
```

---

### Fin del Día

```bash
# 1. Commit cambios pendientes
git status
git add .
git commit -m "wip: work in progress on feature X"

# 2. Push al remoto (backup)
git push origin feature-mi-funcionalidad

# 3. Cerrar servidores
# Ctrl+C en ambas terminales

# 4. (Opcional) Documentar progreso
# Actualizar session notes o README
```

---

### Al Completar Feature

```bash
# 1. Asegurarse que todo funciona
npm run build  # en frontend (verificar que compila)
# Probar funcionalidad end-to-end

# 2. Commit final
git add .
git commit -m "feat: complete user search feature"

# 3. Push y crear Pull Request
git push origin feature-mi-funcionalidad

# 4. Ir a GitHub y crear PR
# - Base: main
# - Compare: feature-mi-funcionalidad
# - Descripción detallada
# - Screenshots si aplica

# 5. Solicitar review del equipo

# 6. Después de merge:
git checkout main
git pull origin main
git branch -d feature-mi-funcionalidad
```

---

## Checklist de Configuración Completa

Usa este checklist para verificar que tu ambiente está listo:

### Setup Inicial
- [ ] Node.js instalado y verificado
- [ ] Python instalado y verificado
- [ ] Git instalado y configurado
- [ ] Repositorio clonado localmente
- [ ] Cuenta de Supabase creada

### Supabase
- [ ] Proyecto creado en Supabase
- [ ] Credenciales copiadas y guardadas
- [ ] Schema base ejecutado (schema.sql)
- [ ] Migraciones adicionales ejecutadas
- [ ] Usuario creado en auth.users
- [ ] Perfil creado en user_profiles
- [ ] RLS policies configuradas

### Variables de Entorno
- [ ] backend/.env creado y configurado
- [ ] frontend/.env creado y configurado
- [ ] SECRET_KEY generado
- [ ] Credenciales de Supabase copiadas
- [ ] .env NO está en Git (verificar .gitignore)

### Dependencias
- [ ] Python venv creado
- [ ] requirements.txt instalados
- [ ] node_modules instalados
- [ ] Sin errores de instalación

### Servidores
- [ ] Backend arranca sin errores (localhost:8000)
- [ ] Frontend arranca sin errores (localhost:5173)
- [ ] API Docs accesible (/docs)
- [ ] Health endpoint responde (/api/health)

### Funcionalidad
- [ ] Puedes hacer login
- [ ] Dashboard carga correctamente
- [ ] Sidebar muestra departamentos
- [ ] Puedes navegar entre secciones
- [ ] No hay errores en consola
- [ ] API calls funcionan (Network tab)

### Git
- [ ] Rama main actualizada
- [ ] Puedes crear ramas nuevas
- [ ] Puedes hacer commits
- [ ] Puedes hacer push al remoto

---

## Recursos Adicionales

### Documentación del Proyecto
- `README.md` - Introducción al proyecto
- `CLAUDE.md` - Instrucciones para Claude Code
- `backend/database/README.md` - Setup de base de datos
- `*_SESSION_NOTES_*.md` - Notas de sesiones anteriores

### Documentación Externa
- **FastAPI:** https://fastapi.tiangolo.com
- **React:** https://react.dev
- **Supabase:** https://supabase.com/docs
- **Material-UI:** https://mui.com
- **TypeScript:** https://www.typescriptlang.org/docs
- **Python Type Hints:** https://docs.python.org/3/library/typing.html

### Herramientas Útiles
- **DB Client:** DBeaver, pgAdmin (para explorar la DB)
- **API Testing:** Postman, Insomnia
- **Git GUI:** GitKraken, SourceTree (si prefieres GUI)
- **Terminal:** Windows Terminal, iTerm2

---

## Próximos Pasos

Después de completar esta guía:

1. **Familiarízate con el código:**
   - Explora la estructura de carpetas
   - Lee los archivos principales
   - Entiende el flujo de datos

2. **Haz un feature pequeño:**
   - Empieza con algo simple
   - Sigue el workflow Git
   - Pide review del equipo

3. **Documenta lo aprendido:**
   - Actualiza esta guía si encuentras issues
   - Comparte tips con el equipo
   - Crea session notes de tus features

4. **Comunícate con el equipo:**
   - Pregunta cuando tengas dudas
   - Comparte lo que aprendes
   - Participa en code reviews

---

## Soporte

Si encuentras problemas que no están cubiertos en esta guía:

1. **Buscar en session notes anteriores**
   - Revisar archivos `2025*_SESSION_NOTES_*.md`
   - Buscar por palabra clave (Ctrl+F)

2. **Preguntar al equipo**
   - Slack/Teams
   - Daily standup
   - Pair programming session

3. **Documentar la solución**
   - Agregar a esta guía
   - Crear session note
   - Actualizar README

---

**Versión:** 1.0
**Última Actualización:** November 11, 2025
**Mantenido por:** Equipo Finkargo Dev
**Próxima Revisión:** Cuando se integre nuevo stack/servicio
