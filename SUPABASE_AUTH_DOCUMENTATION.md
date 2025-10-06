# Supabase Authentication Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Frontend Implementation](#frontend-implementation)
3. [Backend Implementation](#backend-implementation)
4. [Authentication Flow](#authentication-flow)
5. [Session Management](#session-management)
6. [Protected Routes](#protected-routes)
7. [User Profile Management](#user-profile-management)
8. [Security Considerations](#security-considerations)
9. [Common Operations](#common-operations)

---

## Architecture Overview

This application uses **Supabase Auth** as the primary authentication system. Supabase provides:
- JWT-based authentication
- Built-in session management
- Row Level Security (RLS) for database access
- Multiple authentication methods (email/password, OAuth, etc.)

### Key Components

**Frontend:**
- `@supabase/supabase-js` client library
- React Context API for auth state management
- Protected route components

**Backend:**
- Supabase Python client
- FastAPI endpoints for auth operations
- Admin client for privileged operations

---

## Frontend Implementation

### 1. Supabase Client Configuration

**Location:** `frontend/src/services/supabase.ts:1-28`

```typescript
// Supabase client initialization
export const supabase = createSupabaseClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,      // Auto-refresh tokens before expiry
    persistSession: true,         // Persist session in localStorage
    detectSessionInUrl: true,     // Handle OAuth callbacks
    storage: window.localStorage, // Store session data
  },
  global: {
    headers: {
      'x-application-name': 'Finkargo Pre-Approval System',
    },
  },
});
```

**Environment Variables Required:**
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Public anonymous key

### 2. Authentication Context

**Location:** `frontend/src/contexts/AuthContext.tsx`

The `AuthContext` provides application-wide authentication state and methods:

```typescript
interface AuthContextType {
  user: User | null;              // Current authenticated user
  session: Session | null;        // Active session with JWT token
  loading: boolean;               // Loading state during auth checks
  signIn: (email, password) => Promise<void>;
  signUp: (email, password, fullName, role) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;       // Quick auth status check
}
```

#### Key Features:

**Initialization (AuthContext.tsx:37-55):**
- Retrieves existing session on app load
- Sets up auth state change listener
- Automatically updates user state on auth changes

**Sign In (AuthContext.tsx:57-76):**
```typescript
const handleSignIn = async (email: string, password: string) => {
  const { user } = await signIn(email, password);

  // Update last login timestamp
  if (user) {
    await supabase
      .from('user_profiles')
      .update({ last_login: new Date().toISOString() })
      .eq('id', user.id);
  }
};
```

**Sign Up (AuthContext.tsx:78-106):**
```typescript
const handleSignUp = async (email, password, fullName, role = 'commercial') => {
  const { user } = await signUp(email, password, { full_name: fullName });

  // Create user profile record
  if (user) {
    await supabase
      .from('user_profiles')
      .insert({
        id: user.id,
        full_name: fullName,
        role: role,
        is_active: true,
      });
  }
};
```

### 3. Auth Helper Functions

**Location:** `frontend/src/services/supabase.ts:31-69`

```typescript
// Sign in with email/password
export const signIn = async (email: string, password: string)

// Register new user
export const signUp = async (email: string, password: string, metadata?: Record<string, any>)

// Sign out current user
export const signOut = async ()

// Get current authenticated user
export const getCurrentUser = async ()

// Get active session
export const getSession = async ()
```

### 4. Protected Routes

**Location:** `frontend/src/components/ProtectedRoute.tsx`

The `ProtectedRoute` component guards routes requiring authentication:

```typescript
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  // Show loading spinner during auth check
  if (loading) {
    return <CircularProgress />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Render protected content
  return <>{children}</>;
};
```

**Usage Example:**
```typescript
<Route path="/dashboard" element={
  <ProtectedRoute>
    <Dashboard />
  </ProtectedRoute>
} />
```

---

## Backend Implementation

### 1. Supabase Configuration

**Location:** `backend/src/config/supabase_config.py`

The backend uses a **singleton pattern** for Supabase client management:

```python
class SupabaseClient:
    """Singleton Supabase client manager."""

    # Two client instances:
    _client: Client           # Public client (anon key)
    _admin_client: Client     # Admin client (service key)
```

**Environment Variables Required:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Public anonymous key
- `SUPABASE_SERVICE_KEY` - Service role key (privileged access)
- `SUPABASE_JWT_SECRET` - JWT secret for token validation

#### Client Types:

**Public Client (supabase_config.py:56-60):**
- Uses anonymous key
- Respects Row Level Security (RLS)
- Used for standard auth operations

**Admin Client (supabase_config.py:62-66):**
- Uses service role key
- Bypasses RLS policies
- Used for privileged operations (user management, system tasks)

### 2. Token Validation

**Location:** `backend/src/config/supabase_config.py:102-117`

```python
def get_user_from_token(self, token: str):
    """
    Validate and get user from JWT token.

    Returns:
        User object if valid, None otherwise
    """
    try:
        user = self.auth.get_user(token)
        return user
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        return None
```

### 3. Authentication Routes

**Location:** `backend/src/adapter/rest/auth_routes.py`

#### Login Endpoint (`/login`)

```python
@router.post("/login", response_model=TokenResponseDTO)
async def login(credentials: UserLoginDTO):
    # Authenticate with Supabase
    response = supabase_client.auth.sign_in_with_password({
        "email": credentials.email,
        "password": credentials.password
    })

    # Return JWT token
    return TokenResponseDTO(
        access_token=response.session.access_token,
        token_type="bearer",
        expires_in=response.session.expires_in
    )
```

#### Registration Endpoint (`/register`)

```python
@router.post("/register", response_model=TokenResponseDTO)
async def register(user_data: UserCreateDTO):
    # Register with Supabase Auth
    response = supabase_client.auth.sign_up({
        "email": user_data.email,
        "password": user_data.password,
        "options": {
            "data": {
                "full_name": user_data.full_name,
                "role": user_data.role
            }
        }
    })

    # Create user profile in database
    supabase_client.admin_client.table("user_profiles").insert({
        "id": response.user.id,
        "full_name": user_data.full_name,
        "role": user_data.role,
        "is_active": True
    }).execute()

    return token_response
```

#### Current User Endpoint (`/me`)

```python
@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Validate token and get user
    user = supabase_client.get_user_from_token(credentials.credentials)

    # Fetch user profile
    response = supabase_client.client.table("user_profiles")
        .select("*")
        .eq("id", user.id)
        .execute()

    return user_profile_data
```

### 4. Repository Pattern

**Location:** `backend/src/repositorio/supabase_repository.py`

The repository uses the **admin client** for all database operations to bypass RLS:

```python
class SupabaseRepository:
    def __init__(self):
        # Use admin client for all operations
        self.admin_client = supabase_client.admin_client

    async def create_client(self, client_data: ClientCreateDTO, user_id: str):
        # Admin client bypasses RLS policies
        response = self.admin_client.table('clients').insert(data).execute()
        return response.data[0]
```

**Why Admin Client?**
- Backend operations need privileged access
- Centralized authorization logic in API layer
- Simplified RLS policy management
- Better performance (no RLS overhead)

---

## Authentication Flow

### 1. User Login Flow

```
┌─────────────┐        ┌──────────────┐        ┌─────────────┐
│   Browser   │        │   Frontend   │        │   Supabase  │
└─────┬───────┘        └──────┬───────┘        └──────┬──────┘
      │                       │                       │
      │  1. Enter credentials │                       │
      ├──────────────────────►│                       │
      │                       │                       │
      │                       │  2. signIn()          │
      │                       ├──────────────────────►│
      │                       │                       │
      │                       │  3. Validate creds    │
      │                       │     Generate JWT      │
      │                       │                       │
      │                       │◄──────────────────────┤
      │                       │  4. Session + Token   │
      │                       │                       │
      │                       │  5. Store in localStorage
      │                       │  6. Update AuthContext
      │                       │                       │
      │  7. Redirect to app   │                       │
      │◄──────────────────────┤                       │
      │                       │                       │
```

### 2. Protected API Request Flow

```
┌──────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │     │  Backend  │     │ Supabase │     │ Database │
└────┬─────┘     └─────┬─────┘     └────┬─────┘     └────┬─────┘
     │                 │                 │                │
     │  1. API request │                 │                │
     │    + JWT token  │                 │                │
     ├────────────────►│                 │                │
     │                 │                 │                │
     │                 │  2. Validate JWT│                │
     │                 ├────────────────►│                │
     │                 │                 │                │
     │                 │◄────────────────┤                │
     │                 │  3. User data   │                │
     │                 │                 │                │
     │                 │  4. Execute query (admin client) │
     │                 ├─────────────────────────────────►│
     │                 │                 │                │
     │                 │◄─────────────────────────────────┤
     │                 │  5. Results     │                │
     │                 │                 │                │
     │◄────────────────┤                 │                │
     │  6. JSON response                 │                │
     │                 │                 │                │
```

### 3. Session Refresh Flow

Supabase automatically handles token refresh:

```typescript
// Configured in supabase client
auth: {
  autoRefreshToken: true,  // Refresh before expiry
  persistSession: true,    // Keep session across reloads
}
```

**Refresh Timing:**
- Default token expiry: 3600 seconds (1 hour)
- Auto-refresh triggers ~5 minutes before expiry
- New token issued seamlessly
- No user interaction required

---

## Session Management

### 1. Session Storage

**Storage Location:** Browser `localStorage`
**Key:** `supabase.auth.token`

**Session Data:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "...",
  "expires_in": 3600,
  "expires_at": 1234567890,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "user_metadata": { }
  }
}
```

### 2. Auth State Change Listener

**Location:** `frontend/src/contexts/AuthContext.tsx:46-54`

```typescript
// Listen for auth state changes
const { data: { subscription } } = supabase.auth.onAuthStateChange(
  (_event, session) => {
    setSession(session);
    setUser(session?.user ?? null);
    setLoading(false);
  }
);

// Cleanup on unmount
return () => subscription.unsubscribe();
```

**Events Handled:**
- `SIGNED_IN` - User logged in
- `SIGNED_OUT` - User logged out
- `TOKEN_REFRESHED` - Token auto-refreshed
- `USER_UPDATED` - User metadata updated

### 3. Session Persistence

Sessions persist across:
- Page reloads
- Browser restarts
- Tab closures

**Session cleared on:**
- Explicit sign out
- Token expiration without refresh
- Manual localStorage clear

---

## Protected Routes

### Frontend Route Protection

**Pattern:**
```typescript
// Wrap protected pages with ProtectedRoute
<Route path="/dashboard" element={
  <ProtectedRoute>
    <Dashboard />
  </ProtectedRoute>
} />
```

**Protection Logic:**
1. Check `loading` state → Show spinner
2. Check `isAuthenticated` → Redirect if false
3. Render protected content → If authenticated

### Backend Route Protection

**Pattern:**
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@router.get("/protected")
async def protected_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Extract token
    token = credentials.credentials

    # Validate token
    user = supabase_client.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401)

    # Process request
    return protected_data
```

---

## User Profile Management

### Database Schema

**Table:** `user_profiles`

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'admin', 'commercial', 'analyst', 'mesa_control'
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Profile Creation Flow

**During Registration:**

1. **Create Auth User** (auth_routes.py:62-72)
   ```python
   response = supabase_client.auth.sign_up({
       "email": email,
       "password": password,
       "options": {
           "data": {"full_name": full_name, "role": role}
       }
   })
   ```

2. **Create Profile Record** (auth_routes.py:80-86)
   ```python
   supabase_client.admin_client.table("user_profiles").insert({
       "id": user.id,
       "full_name": full_name,
       "role": role,
       "is_active": True
   }).execute()
   ```

### Profile Updates

**Last Login Update** (AuthContext.tsx:62-71)
```typescript
await supabase
  .from('user_profiles')
  .update({ last_login: new Date().toISOString() })
  .eq('id', user.id);
```

---

## Security Considerations

### 1. Key Management

**Frontend (.env):**
```env
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...  # Safe to expose
```

**Backend (.env):**
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...        # Safe to expose
SUPABASE_SERVICE_KEY=eyJ...     # MUST KEEP SECRET!
SUPABASE_JWT_SECRET=...         # MUST KEEP SECRET!
```

⚠️ **CRITICAL:** Never expose `SERVICE_KEY` or `JWT_SECRET` in frontend code!

### 2. Row Level Security (RLS)

While the backend uses admin client (bypasses RLS), RLS policies should still be configured for:
- Direct client connections
- Supabase Studio access
- Additional security layer

**Example Policy:**
```sql
-- Users can only see their own profile
CREATE POLICY "Users can view own profile"
ON user_profiles
FOR SELECT
USING (auth.uid() = id);
```

### 3. Token Security

**Best Practices:**
- ✅ Store tokens in `localStorage` (not cookies for SPA)
- ✅ Use HTTPS in production
- ✅ Validate tokens on every backend request
- ✅ Set appropriate token expiry (1 hour default)
- ✅ Implement token refresh
- ❌ Never log tokens
- ❌ Never send tokens in URL parameters

### 4. Password Security

Supabase handles:
- Password hashing (bcrypt)
- Salting
- Secure storage
- Rate limiting on auth endpoints

**Requirements:**
- Minimum length: 6 characters
- Can be configured in Supabase dashboard

### 5. CORS Configuration

**Backend must allow frontend origin:**
```python
# backend/src/config/settings.py
CORS_ORIGINS = [
    "http://localhost:5173",  # Development
    "https://app.finkargo.com"  # Production
]
```

---

## Common Operations

### 1. Sign In

**Frontend:**
```typescript
import { useAuth } from '@/contexts/AuthContext';

const LoginComponent = () => {
  const { signIn } = useAuth();

  const handleSubmit = async () => {
    try {
      await signIn(email, password);
      // Redirect handled by ProtectedRoute
    } catch (error) {
      console.error('Login failed:', error);
    }
  };
};
```

### 2. Sign Up

**Frontend:**
```typescript
const { signUp } = useAuth();

await signUp(email, password, fullName, 'commercial');
```

### 3. Sign Out

**Frontend:**
```typescript
const { signOut } = useAuth();

await signOut();
// User automatically redirected to login
```

### 4. Get Current User

**Frontend:**
```typescript
const { user } = useAuth();

console.log(user?.email);
console.log(user?.id);
```

### 5. Check Authentication

**Frontend:**
```typescript
const { isAuthenticated } = useAuth();

if (isAuthenticated) {
  // User is logged in
}
```

### 6. Get Session Token

**Frontend:**
```typescript
const { session } = useAuth();
const token = session?.access_token;

// Use in API requests
fetch('/api/endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 7. Validate Token (Backend)

**Backend:**
```python
user = supabase_client.get_user_from_token(token)
if user:
    user_id = user.id
    user_email = user.email
```

### 8. Create User Profile

**Backend:**
```python
from src.repositorio.supabase_repository import SupabaseRepository

repo = SupabaseRepository()
profile = await repo.create_user_profile(
    user_id=user.id,
    profile_data={
        'full_name': 'John Doe',
        'role': 'commercial',
        'is_active': True
    }
)
```

### 9. Get Users by Role

**Backend:**
```python
repo = SupabaseRepository()
analysts = await repo.get_users_by_role('analyst')
admins = await repo.get_users_by_role('admin')
```

---

## Troubleshooting

### Common Issues

#### 1. "Invalid API key"
- Check environment variables are loaded
- Verify key values in Supabase dashboard
- Ensure correct key for environment (dev/prod)

#### 2. "Session expired"
- Check `autoRefreshToken: true` is set
- Verify token hasn't been manually invalidated
- Check system clock is accurate

#### 3. "Permission denied"
- Verify user is authenticated
- Check RLS policies if using public client
- Ensure admin client is used for backend operations

#### 4. "Failed to fetch"
- Check CORS configuration
- Verify Supabase URL is correct
- Check network connectivity

#### 5. User stuck in loading state
- Check auth state change listener is set up
- Verify `getSession()` is called on app load
- Check for errors in browser console

### Debug Tips

**Frontend:**
```typescript
// Log auth state changes
supabase.auth.onAuthStateChange((event, session) => {
  console.log('Auth event:', event);
  console.log('Session:', session);
});

// Check current session
const { data } = await supabase.auth.getSession();
console.log('Current session:', data.session);
```

**Backend:**
```python
# Log token validation
user = supabase_client.get_user_from_token(token)
logger.info(f"Validated user: {user.id if user else 'None'}")
```

---

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)
- [JWT Introduction](https://jwt.io/introduction)

---

## Related Documentation

- [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) - Initial Supabase setup guide
- [CLAUDE.md](./CLAUDE.md) - Project architecture and standards
- Backend API Documentation: `/api/docs` (Swagger UI)
