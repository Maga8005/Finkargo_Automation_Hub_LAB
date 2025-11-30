/**
 * PlantillasNetSuite - Plantillas para Cargar NetSuite
 * Gestión de plantillas para carga masiva en NetSuite
 */
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Divider,
  Grid,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Description as DocumentIcon,
  AddCircle as AddIcon,
  History as HistoryIcon,
  AccountBalance as TreasuryIcon,
} from '@mui/icons-material';

const PlantillasNetSuite: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <TreasuryIcon sx={{ fontSize: '2rem', color: 'primary.main' }} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
              Plantillas para Cargar NetSuite
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Gestión de plantillas para carga masiva en NetSuite
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider sx={{ mb: 4 }} />

      <Grid container spacing={3}>
        {/* Upload Templates Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <AddIcon color="primary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Cargar Nueva Plantilla
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Sube plantillas de Excel para procesar y cargar en NetSuite
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<DocumentIcon />}
                  fullWidth
                  sx={{ justifyContent: 'flex-start', py: 1.5 }}
                  disabled
                >
                  Plantilla de Pagos
                </Button>

                <Button
                  variant="contained"
                  startIcon={<DocumentIcon />}
                  fullWidth
                  sx={{ justifyContent: 'flex-start', py: 1.5 }}
                  disabled
                >
                  Plantilla de Cobros
                </Button>

                <Button
                  variant="contained"
                  startIcon={<DocumentIcon />}
                  fullWidth
                  sx={{ justifyContent: 'flex-start', py: 1.5 }}
                  disabled
                >
                  Plantilla de Conciliación
                </Button>
              </Box>

              <Divider sx={{ my: 3 }} />

              <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                fullWidth
                disabled
              >
                Cargar Archivo Excel
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Template History Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <HistoryIcon color="primary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Historial de Cargas
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Revisa el historial de plantillas procesadas y cargadas en NetSuite
              </Typography>

              <Box
                sx={{
                  minHeight: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'grey.50',
                  borderRadius: 2,
                  border: '2px dashed',
                  borderColor: 'grey.300',
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  El historial de cargas aparecerá aquí
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Pending Uploads */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Cargas Pendientes
              </Typography>
              <Box
                sx={{
                  minHeight: 150,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'grey.50',
                  borderRadius: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  No hay cargas pendientes para procesar
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default PlantillasNetSuite;
