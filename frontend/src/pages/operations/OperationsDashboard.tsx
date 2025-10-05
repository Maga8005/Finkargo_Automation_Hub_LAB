/**
 * Operations Department Dashboard
 * View and download approved contracts for customer signature
 */
import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import FKApprovedContracts from '../../components/forms/FKApprovedContracts';

const OperationsDashboard: React.FC = () => {
  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
          Departamento de Operaciones
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gestión y descarga de contratos aprobados
        </Typography>
      </Box>

      {/* Info Cards */}
      <Box sx={{ mb: 4 }}>
        <Card elevation={0} sx={{ bgcolor: 'success.50', border: 1, borderColor: 'success.200' }}>
          <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CheckCircleIcon sx={{ fontSize: 40, color: 'success.main' }} />
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.dark' }}>
                Contratos Aprobados
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Descarga los PDFs aprobados por el equipo legal para enviarlos a los clientes para su firma.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Instructions Card */}
      <Box sx={{ mb: 3 }}>
        <Card elevation={0} sx={{ bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <DescriptionIcon sx={{ color: 'primary.main', mt: 0.5 }} />
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'primary.dark' }}>
                  Instrucciones de Uso
                </Typography>
                <Box component="ol" sx={{ m: 0, pl: 2 }}>
                  <li>
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      Revisa la lista de contratos aprobados en la tabla inferior
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      Haz clic en el ícono de PDF para descargar el contrato aprobado
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      Envía el PDF al cliente para su revisión y firma
                    </Typography>
                  </li>
                  <li>
                    <Typography variant="body2">
                      Los PDFs aprobados están guardados en Supabase Storage y son inmutables para mantener la trazabilidad
                    </Typography>
                  </li>
                </Box>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Approved Contracts Table */}
      <Box>
        <FKApprovedContracts />
      </Box>
    </Box>
  );
};

export default OperationsDashboard;
