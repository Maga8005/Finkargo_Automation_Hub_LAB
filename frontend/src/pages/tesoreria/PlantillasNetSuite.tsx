/**
 * PlantillasNetSuite - Landing page for NetSuite payment templates.
 *
 * Displays country selection (Colombia/México) for payment template conversion.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Divider,
  Grid,
  Chip,
} from '@mui/material';
import {
  AccountBalance as TreasuryIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';

const PlantillasNetSuite: React.FC = () => {
  const navigate = useNavigate();

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
              Conversión de Historial de Pagos a Template de Aplicación de Pagos
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider sx={{ mb: 4 }} />

      {/* Description */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Esta herramienta convierte archivos de Historial de Pagos exportados del sistema core
          al formato específico requerido para la aplicación de pagos en NetSuite.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Cada fila del archivo fuente se transforma en múltiples filas de salida,
          una por cada tipo de concepto de pago con valores no cero.
        </Typography>
      </Box>

      {/* Country Selection Cards */}
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
        Selecciona el país
      </Typography>

      <Grid container spacing={3}>
        {/* Colombia Card */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card
            sx={{
              height: '100%',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 6,
              },
            }}
          >
            <CardActionArea
              onClick={() => navigate('/tesoreria/plantillas-netsuite/colombia')}
              sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
            >
              <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Typography variant="h2" sx={{ lineHeight: 1 }}>
                    🇨🇴
                  </Typography>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      Colombia
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Aplicación de Pagos CO
                    </Typography>
                  </Box>
                  <ArrowForwardIcon color="primary" />
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Conceptos soportados:
                </Typography>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  <Chip label="Capital" size="small" variant="outlined" />
                  <Chip label="4x1000" size="small" variant="outlined" />
                  <Chip label="Fondo Garantías" size="small" variant="outlined" />
                  <Chip label="Seguros" size="small" variant="outlined" />
                  <Chip label="Intereses" size="small" variant="outlined" />
                  <Chip label="Moratorios" size="small" variant="outlined" />
                </Box>

                <Box sx={{ mt: 2 }}>
                  <Chip
                    label="Soporta Operaciones Cedidas (NT)"
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </Box>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>

        {/* México Card */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card
            sx={{
              height: '100%',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 6,
              },
            }}
          >
            <CardActionArea
              onClick={() => navigate('/tesoreria/plantillas-netsuite/mexico')}
              sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}
            >
              <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Typography variant="h2" sx={{ lineHeight: 1 }}>
                    🇲🇽
                  </Typography>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      México
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Aplicación de Pagos MX
                    </Typography>
                  </Box>
                  <ArrowForwardIcon color="primary" />
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Conceptos soportados:
                </Typography>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  <Chip label="Capital" size="small" variant="outlined" />
                  <Chip label="Comisión Desembolso" size="small" variant="outlined" />
                  <Chip label="Comisión Disposición" size="small" variant="outlined" />
                  <Chip label="Comisión Swift" size="small" variant="outlined" />
                  <Chip label="Seguros" size="small" variant="outlined" />
                  <Chip label="Intereses" size="small" variant="outlined" />
                  <Chip label="Moratorios" size="small" variant="outlined" />
                </Box>

                <Box sx={{ mt: 2 }}>
                  <Chip
                    label="Comisiones México"
                    size="small"
                    color="secondary"
                    variant="outlined"
                  />
                </Box>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      </Grid>

      {/* Instructions */}
      <Box sx={{ mt: 6 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
          ¿Cómo funciona?
        </Typography>
        <Box component="ol" sx={{ pl: 3, color: 'text.secondary' }}>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Selecciona el país correspondiente (Colombia o México)
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Sube el archivo Historial de Pagos (.xlsx) exportado del sistema core
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            El sistema validará las columnas y mostrará una vista previa
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Haz clic en "Convertir y Descargar" para generar el template de NetSuite
          </Typography>
          <Typography component="li" variant="body2">
            Descarga el archivo convertido listo para cargar en NetSuite
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

export default PlantillasNetSuite;
