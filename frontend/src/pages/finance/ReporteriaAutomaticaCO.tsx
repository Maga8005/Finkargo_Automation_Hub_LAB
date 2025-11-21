/**
 * ReporteriaAutomaticaCO - Reportería Automática Colombia
 * Funcionalidad para crear reportes y buscar PDFs - Colombia
 */
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Divider,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Search as SearchIcon,
  CloudDownload as DownloadIcon,
  Description as DocumentIcon,
  AddCircle as AddIcon,
} from '@mui/icons-material';

const ReporteriaAutomaticaCO: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography fontSize="2rem">🇨🇴</Typography>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
              Reportería Automática Colombia
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Gestión de reportes fiscales - DIAN
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider sx={{ mb: 4 }} />

      <Grid container spacing={3}>
        {/* Create Reports Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <AddIcon color="primary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Crear Nuevo Reporte
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Genera reportes fiscales automáticos para la DIAN
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<DocumentIcon />}
                  fullWidth
                  sx={{ justifyContent: 'flex-start', py: 1.5 }}
                >
                  Reporte DIAN 1007
                </Button>

                <Button
                  variant="contained"
                  startIcon={<DocumentIcon />}
                  fullWidth
                  sx={{ justifyContent: 'flex-start', py: 1.5 }}
                >
                  Reporte DIAN 1001
                </Button>

                <Button
                  variant="contained"
                  startIcon={<DocumentIcon />}
                  fullWidth
                  sx={{ justifyContent: 'flex-start', py: 1.5 }}
                >
                  Medios Magnéticos
                </Button>

                <Button
                  variant="contained"
                  startIcon={<DocumentIcon />}
                  fullWidth
                  sx={{ justifyContent: 'flex-start', py: 1.5 }}
                >
                  Inventario Bodega
                </Button>
              </Box>

              <Divider sx={{ my: 3 }} />

              <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                fullWidth
              >
                Cargar Datos desde Excel
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Search PDFs Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <SearchIcon color="primary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Buscar Reportes Generados
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Encuentra y descarga reportes anteriormente generados
              </Typography>

              <TextField
                fullWidth
                placeholder="Buscar por fecha, tipo de reporte o NIT..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 3 }}
              />

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
                  mb: 3,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  Los resultados de búsqueda aparecerán aquí
                </Typography>
              </Box>

              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                fullWidth
                disabled
              >
                Descargar Seleccionados
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Actividad Reciente
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
                  No hay actividad reciente para mostrar
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ReporteriaAutomaticaCO;
