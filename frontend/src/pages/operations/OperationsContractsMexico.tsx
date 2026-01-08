import React from 'react';
import { Box, Typography, Card, CardContent, Alert } from '@mui/material';
import { Schedule } from '@mui/icons-material';

/**
 * Operations Contracts Mexico Dashboard (Placeholder)
 * Placeholder page for future Mexico operations contract functionality
 */
const OperationsContractsMexico: React.FC = () => {
  return (
    <Box sx={{ p: 4 }}>
      {/* Header Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
          Contratos México - Solicitar
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Solicitud de contratos para operaciones en México
        </Typography>
      </Box>

      {/* Coming Soon Alert */}
      <Alert
        severity="info"
        icon={<Schedule />}
        sx={{
          mb: 3,
          backgroundColor: 'info.50',
          '& .MuiAlert-icon': {
            color: 'info.main',
          },
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
          Próximamente
        </Typography>
        <Typography variant="body2">
          La funcionalidad de contratos para México estará disponible pronto.
          Estamos trabajando para expandir nuestros servicios de automatización a operaciones en México.
        </Typography>
      </Alert>

      {/* Information Card */}
      <Card sx={{ borderRadius: 2, boxShadow: 2 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
            Funcionalidad Planeada
          </Typography>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            Cuando esté disponible, esta sección permitirá:
          </Typography>
          <Box component="ul" sx={{ pl: 2, color: 'text.secondary' }}>
            <li>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Solicitar contratos de activos para clientes en México
              </Typography>
            </li>
            <li>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Generar otrosíes y anexos específicos para regulación mexicana
              </Typography>
            </li>
            <li>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Gestionar contratos de inventario de bodega
              </Typography>
            </li>
            <li>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Descargar contratos aprobados listos para firma del cliente
              </Typography>
            </li>
          </Box>
          <Typography variant="body2" sx={{ mt: 3, color: 'text.secondary', fontStyle: 'italic' }}>
            Mientras tanto, continúa utilizando las herramientas de contratos para Colombia.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default OperationsContractsMexico;
