/**
 * FiscalModulePage - Template page for fiscal reporting modules
 * Displays module details and functionality
 */
import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  Divider,
  Grid,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Download as DownloadIcon,
  PlayArrow as PlayIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// Module metadata
const moduleData: Record<string, {
  title: string;
  country: string;
  flag: string;
  description: string;
  features: string[];
  status: 'active' | 'development' | 'new';
}> = {
  'dian-1007': {
    title: 'DIAN - Reporte 1007',
    country: 'Colombia',
    flag: '🇨🇴',
    description: 'Automatización del reporte 1007 de la DIAN para declaración de información exógena.',
    features: [
      'Carga de archivos Excel/CSV',
      'Validación de formato DIAN',
      'Generación automática de archivo XML',
      'Reporte de errores detallado',
    ],
    status: 'active',
  },
  'dian-1001': {
    title: 'DIAN - Reporte 1001',
    country: 'Colombia',
    flag: '🇨🇴',
    description: 'Generación del reporte 1001 de pagos y abonos en cuenta.',
    features: [
      'Procesamiento masivo de datos',
      'Validación de NIT y valores',
      'Exportación en formato DIAN',
      'Histórico de reportes',
    ],
    status: 'active',
  },
  'medios-magneticos': {
    title: 'Medios Magnéticos',
    country: 'Colombia',
    flag: '🇨🇴',
    description: 'Consolidación y generación de medios magnéticos para presentación ante la DIAN.',
    features: [
      'Múltiples formatos soportados',
      'Validación cruzada de información',
      'Firma digital de reportes',
      'Envío directo a DIAN',
    ],
    status: 'active',
  },
  'inventario-bodega': {
    title: 'Inventario Bodega',
    country: 'Colombia',
    flag: '🇨🇴',
    description: 'Sistema automatizado de gestión de inventarios en bodega con generación de reportes fiscales.',
    features: [
      'Control de stock en tiempo real',
      'Reportes de movimientos',
      'Integración con RUT',
      'Exportación a formatos fiscales',
    ],
    status: 'new',
  },
  'sat-facturacion': {
    title: 'SAT - Facturación',
    country: 'México',
    flag: '🇲🇽',
    description: 'Automatización de facturación electrónica conforme a los requisitos del SAT.',
    features: [
      'Generación de facturas CFDI 4.0',
      'Timbrado automático',
      'Validación SAT en línea',
      'Cancelación de facturas',
    ],
    status: 'development',
  },
  'cfdi-validacion': {
    title: 'CFDI - Validación',
    country: 'México',
    flag: '🇲🇽',
    description: 'Validación de Comprobantes Fiscales Digitales por Internet (CFDI).',
    features: [
      'Verificación de UUID',
      'Validación de estructura XML',
      'Consulta de estatus SAT',
      'Reporte de inconsistencias',
    ],
    status: 'development',
  },
  'complementos-pago': {
    title: 'Complementos de Pago',
    country: 'México',
    flag: '🇲🇽',
    description: 'Generación automática de complementos de pago para CFDI.',
    features: [
      'Vinculación con facturas',
      'Cálculo de parcialidades',
      'Tipos de cambio automatizados',
      'Conciliación bancaria',
    ],
    status: 'development',
  },
};

const FiscalModulePage: React.FC = () => {
  const { moduleId } = useParams<{ country: string; moduleId: string }>();
  const module = moduleData[moduleId || ''];

  if (!module) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" color="error">
          Módulo no encontrado
        </Typography>
      </Container>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'development':
        return 'warning';
      case 'new':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return 'Activo';
      case 'development':
        return 'En Desarrollo';
      case 'new':
        return 'Nuevo';
      default:
        return status;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography fontSize="2rem">{module.flag}</Typography>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
              {module.title}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {module.country}
            </Typography>
          </Box>
          <Chip
            label={getStatusLabel(module.status)}
            color={getStatusColor(module.status)}
            sx={{ fontWeight: 600 }}
          />
        </Box>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: '800px' }}>
          {module.description}
        </Typography>
      </Box>

      <Divider sx={{ mb: 4 }} />

      <Grid container spacing={3}>
        {/* Module Info Card */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <InfoIcon color="primary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Características del Módulo
                </Typography>
              </Box>

              <Box component="ul" sx={{ pl: 2 }}>
                {module.features.map((feature, index) => (
                  <Typography
                    key={index}
                    component="li"
                    variant="body1"
                    sx={{ mb: 1, color: 'grey.700' }}
                  >
                    {feature}
                  </Typography>
                ))}
              </Box>

              {module.status === 'development' && (
                <Box
                  sx={{
                    mt: 3,
                    p: 2,
                    backgroundColor: 'warning.light',
                    borderRadius: 2,
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    ⚠️ Este módulo está en desarrollo
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    Algunas funcionalidades pueden estar limitadas o en fase de prueba.
                  </Typography>
                </Box>
              )}

              {module.status === 'new' && (
                <Box
                  sx={{
                    mt: 3,
                    p: 2,
                    backgroundColor: 'info.light',
                    borderRadius: 2,
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    🎉 Módulo recientemente agregado
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    Explora las nuevas funcionalidades disponibles.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Actions Card */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Acciones Rápidas
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<UploadIcon />}
                  fullWidth
                  disabled={module.status === 'development'}
                >
                  Cargar Datos
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<PlayIcon />}
                  fullWidth
                  disabled={module.status === 'development'}
                >
                  Procesar Reporte
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  fullWidth
                  disabled={module.status === 'development'}
                >
                  Descargar Resultados
                </Button>
              </Box>

              <Divider sx={{ my: 3 }} />

              <Typography variant="caption" color="text.secondary">
                <strong>Última actualización:</strong> {new Date().toLocaleDateString('es-ES')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Content Area - Placeholder for module-specific functionality */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Área de Trabajo
              </Typography>
              <Box
                sx={{
                  minHeight: 300,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'grey.50',
                  borderRadius: 2,
                  border: '2px dashed',
                  borderColor: 'grey.300',
                }}
              >
                <Typography variant="body1" color="text.secondary">
                  {module.status === 'development'
                    ? 'Contenido en desarrollo...'
                    : 'Selecciona una acción para comenzar'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default FiscalModulePage;
