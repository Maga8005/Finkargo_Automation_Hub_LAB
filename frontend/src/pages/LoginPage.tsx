/**
 * LoginPage Component
 * Dual access authentication form (Funcionarios vs Clientes)
 * Spanish UI text following Finkargo design system
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  ToggleButton,
  ToggleButtonGroup,
  Divider,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Business as BusinessIcon,
  Person as PersonIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import type { UserType } from '../types';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { signIn, loading, isAuthenticated } = useAuth();

  const [userType, setUserType] = useState<UserType>('funcionario');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'email' | 'password' | 'general' | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated && !loading) {
      console.log('[LoginPage] Already authenticated, redirecting to /');
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);

  const handleUserTypeChange = (_event: React.MouseEvent<HTMLElement>, newUserType: UserType | null) => {
    if (newUserType !== null) {
      setUserType(newUserType);
      setError(null);
      setErrorType(null);
    }
  };

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleMouseDownPassword = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
  };

  const parseAuthError = (errorMessage: string): { message: string; type: 'email' | 'password' | 'general' } => {
    const lowerError = errorMessage.toLowerCase();

    console.log('[LoginPage] Error received:', errorMessage);

    // Network errors
    if (lowerError.includes('network') ||
        lowerError.includes('failed to fetch') ||
        lowerError.includes('timeout')) {
      return {
        message: 'Error de conexión. Por favor, verifica tu conexión a internet.',
        type: 'general'
      };
    }

    // Account locked/disabled
    if (lowerError.includes('account locked') ||
        lowerError.includes('account disabled') ||
        lowerError.includes('user is disabled')) {
      return {
        message: 'Esta cuenta ha sido desactivada. Contacta al administrador.',
        type: 'general'
      };
    }

    // Email not confirmed
    if (lowerError.includes('email not confirmed')) {
      return {
        message: 'Tu correo electrónico aún no ha sido confirmado. Revisa tu bandeja de entrada.',
        type: 'general'
      };
    }

    // Invalid credentials (could be email or password)
    // Supabase returns the same error for both, so we show a general message
    if (lowerError.includes('invalid login credentials') ||
        lowerError.includes('invalid email or password') ||
        lowerError.includes('user not found') ||
        lowerError.includes('invalid password') ||
        lowerError.includes('wrong password')) {
      return {
        message: 'Correo electrónico o contraseña incorrectos. Por favor, verifica tus credenciales.',
        type: 'general'
      };
    }

    // Default error - always show something
    return {
      message: errorMessage || 'Error al iniciar sesión. Por favor, intenta nuevamente.',
      type: 'general'
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setErrorType(null);
    setIsSubmitting(true);

    try {
      await signIn(email, password);
      console.log('[LoginPage] Sign in successful, waiting for redirect...');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al iniciar sesión';
      const parsedError = parseAuthError(errorMessage);
      setError(parsedError.message);
      setErrorType(parsedError.type);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #050A53 0%, #0C147B 50%, #3C47D3 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={24}
          sx={{
            padding: 4,
            borderRadius: 2,
          }}
        >
          {/* Logo/Title */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography
              variant="h4"
              component="h1"
              gutterBottom
              sx={{
                fontWeight: 700,
                color: 'primary.main',
              }}
            >
              Finkargo
            </Typography>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ fontWeight: 500 }}
            >
              Automation Hub
            </Typography>
          </Box>

          {/* User Type Selector */}
          <Box sx={{ mb: 3 }}>
            <Typography
              variant="subtitle2"
              color="text.secondary"
              sx={{ mb: 1.5, fontWeight: 600 }}
            >
              Tipo de acceso
            </Typography>
            <ToggleButtonGroup
              value={userType}
              exclusive
              onChange={handleUserTypeChange}
              fullWidth
              sx={{
                '& .MuiToggleButton-root': {
                  py: 1.5,
                  borderRadius: 2,
                  border: '2px solid',
                  borderColor: 'divider',
                  '&.Mui-selected': {
                    borderColor: 'primary.main',
                    backgroundColor: 'primary.main',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                  },
                },
              }}
            >
              <ToggleButton value="funcionario" aria-label="funcionario">
                <PersonIcon sx={{ mr: 1 }} />
                <Box sx={{ textAlign: 'left' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Funcionario
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.8 }}>
                    Personal de Finkargo
                  </Typography>
                </Box>
              </ToggleButton>
              <ToggleButton value="cliente" aria-label="cliente">
                <BusinessIcon sx={{ mr: 1 }} />
                <Box sx={{ textAlign: 'left' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Cliente
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.8 }}>
                    Acceso externo
                  </Typography>
                </Box>
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Error Alert - Only show for general errors */}
          {error && errorType === 'general' && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Correo electrónico"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errorType === 'email') {
                  setError(null);
                  setErrorType(null);
                }
              }}
              required
              autoComplete="email"
              margin="normal"
              disabled={isSubmitting || loading}
              error={errorType === 'email'}
              helperText={errorType === 'email' ? error : ''}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Contraseña"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errorType === 'password') {
                  setError(null);
                  setErrorType(null);
                }
              }}
              required
              autoComplete="current-password"
              margin="normal"
              disabled={isSubmitting || loading}
              error={errorType === 'password'}
              helperText={errorType === 'password' ? error : ''}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleClickShowPassword}
                      onMouseDown={handleMouseDownPassword}
                      edge="end"
                      disabled={isSubmitting || loading}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 3 }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isSubmitting || loading}
              sx={{
                height: 52,
                borderRadius: 2,
                fontWeight: 600,
                fontSize: '1rem',
                textTransform: 'none',
              }}
            >
              {isSubmitting || loading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Iniciar sesión'
              )}
            </Button>
          </form>

          {/* Footer Text */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              © {new Date().getFullYear()} Finkargo. Todos los derechos reservados.
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default LoginPage;
