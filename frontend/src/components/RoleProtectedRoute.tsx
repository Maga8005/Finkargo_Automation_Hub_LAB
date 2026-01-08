/**
 * RoleProtectedRoute - Route guard that checks user role before allowing access
 * Admins bypass all role checks
 */
import React from 'react';
import { Navigate } from 'react-router-dom';
import { Box, Typography, Container, Button } from '@mui/material';
import { Lock } from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import type { UserRole } from '../types';

interface RoleProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles: UserRole[];
}

const RoleProtectedRoute: React.FC<RoleProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { userProfile, loading } = useAuth();

  // Show loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <Typography>Cargando...</Typography>
      </Box>
    );
  }

  // If no user profile, redirect to home
  if (!userProfile) {
    return <Navigate to="/" replace />;
  }

  const userRole = userProfile.role;

  // Admin bypass - admins have access to everything
  if (userRole === 'admin') {
    return <>{children}</>;
  }

  // Check if user's role is in the allowed roles list
  if (!allowedRoles.includes(userRole)) {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            py: 6,
          }}
        >
          <Lock sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'grey.800' }}>
            Acceso Denegado
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, color: 'grey.600' }}>
            No tienes permisos para acceder a este módulo.
          </Typography>
          <Typography variant="body2" sx={{ mb: 3, color: 'grey.500' }}>
            Tu rol: <strong>{userRole}</strong>
            <br />
            Roles requeridos: <strong>{allowedRoles.join(', ')}</strong>
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => window.history.back()}
            sx={{ borderRadius: 2 }}
          >
            Volver
          </Button>
        </Box>
      </Container>
    );
  }

  // User has required role
  return <>{children}</>;
};

export default RoleProtectedRoute;
