/**
 * HomePage - Dashboard/Welcome page
 */
import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const HomePage: React.FC = () => {
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
