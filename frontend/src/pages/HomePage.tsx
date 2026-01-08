/**
 * HomePage - Dashboard/Welcome page
 * Redirects clients to their dedicated dashboard
 */
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Card, CardContent, CircularProgress } from '@mui/material';
import { useAuth } from '../hooks/useAuth';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { userProfile, loading } = useAuth();

  // Redirect clients to their dedicated dashboard
  useEffect(() => {
    if (!loading && userProfile) {
      if (userProfile.user_type === 'cliente') {
        console.log('[HomePage] Client user detected, redirecting to client dashboard');
        navigate('/client', { replace: true });
      }
    }
  }, [userProfile, loading, navigate]);

  // Show loading while checking user type
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Show employee dashboard
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
        Bienvenido al Hub de Automatización
      </Typography>
      <Typography variant="body1" sx={{ mb: 4, color: 'grey.700' }}>
        Selecciona un departamento del menú lateral para ver las automatizaciones disponibles.
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Inicio Rápido
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Este es el hub centralizado de automatización de Finkargo. Aquí podrás acceder a
            todas las herramientas de automatización organizadas por departamento.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default HomePage;
