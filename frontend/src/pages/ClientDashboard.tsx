/**
 * ClientDashboard - Dashboard for external clients
 * Shows client-specific features and information
 */
import React from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Avatar,
  Divider,
  AppBar,
  Toolbar,
  Grid,
} from '@mui/material';
import {
  Description as DocumentIcon,
  LocalShipping as ShippingIcon,
  Assessment as ReportIcon,
  ContactSupport as SupportIcon,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import FKUserMenu from '../components/ui/FKUserMenu';

interface ClientFeature {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  route: string;
  enabled: boolean;
}

const clientFeatures: ClientFeature[] = [
  {
    id: 'documents',
    title: 'Mis Documentos',
    description: 'Consulta y gestiona tus documentos',
    icon: <DocumentIcon sx={{ fontSize: 40 }} />,
    route: '/client/documents',
    enabled: true,
  },
  {
    id: 'shipments',
    title: 'Seguimiento de Envíos',
    description: 'Rastrea el estado de tus envíos',
    icon: <ShippingIcon sx={{ fontSize: 40 }} />,
    route: '/client/shipments',
    enabled: true,
  },
  {
    id: 'reports',
    title: 'Reportes',
    description: 'Visualiza reportes y estadísticas',
    icon: <ReportIcon sx={{ fontSize: 40 }} />,
    route: '/client/reports',
    enabled: true,
  },
  {
    id: 'support',
    title: 'Soporte',
    description: 'Contacta a nuestro equipo de soporte',
    icon: <SupportIcon sx={{ fontSize: 40 }} />,
    route: '/client/support',
    enabled: true,
  },
];

const ClientDashboard: React.FC = () => {
  const { userProfile } = useAuth();

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'grey.50' }}>
      {/* Client Navbar */}
      <AppBar
        position="fixed"
        sx={{
          backgroundColor: 'primary.dark',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
            <Typography
              variant="h5"
              component="h1"
              sx={{
                fontWeight: 700,
                color: 'white',
                letterSpacing: '0.5px',
              }}
            >
              Finkargo - Portal de Cliente
            </Typography>
          </Box>
          <FKUserMenu />
        </Toolbar>
      </AppBar>

      {/* Content with top padding for fixed navbar */}
      <Container maxWidth="lg" sx={{ pt: 12, pb: 4 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
          Bienvenido, {userProfile?.full_name || 'Cliente'}
        </Typography>
        {userProfile?.company_name && (
          <Typography variant="h6" color="text.secondary">
            {userProfile.company_name}
          </Typography>
        )}
        <Divider sx={{ mt: 2 }} />
      </Box>

      {/* Info Box */}
      <Box
        sx={{
          mb: 4,
          p: 3,
          backgroundColor: 'primary.light',
          borderRadius: 2,
          color: 'white',
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
          Portal de Cliente - Finkargo
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.9 }}>
          Accede a tus servicios y consulta información de tus operaciones en tiempo real.
        </Typography>
      </Box>

      {/* Features Grid */}
      <Grid container spacing={3}>
        {clientFeatures.map((feature) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={feature.id}>
            <Card
              sx={{
                height: '100%',
                opacity: feature.enabled ? 1 : 0.6,
                transition: 'all 0.3s ease',
                '&:hover': feature.enabled
                  ? {
                      transform: 'translateY(-8px)',
                      boxShadow: 6,
                    }
                  : {},
              }}
            >
              <CardActionArea
                disabled={!feature.enabled}
                sx={{ height: '100%', p: 2 }}
                onClick={() => {
                  if (feature.enabled) {
                    console.log(`Navigate to ${feature.route}`);
                    // TODO: Implement navigation when routes are created
                  }
                }}
              >
                <CardContent
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                    gap: 2,
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: 'primary.main',
                      width: 80,
                      height: 80,
                    }}
                  >
                    {feature.icon}
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </Box>
                  {!feature.enabled && (
                    <Typography
                      variant="caption"
                      sx={{
                        mt: 1,
                        px: 2,
                        py: 0.5,
                        backgroundColor: 'grey.200',
                        borderRadius: 1,
                        color: 'grey.600',
                      }}
                    >
                      Próximamente
                    </Typography>
                  )}
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Additional Info */}
      <Box sx={{ mt: 6, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          ¿Necesitas ayuda? Contáctanos en{' '}
          <Typography component="span" sx={{ fontWeight: 600, color: 'primary.main' }}>
            soporte@finkargo.com
          </Typography>
        </Typography>
      </Box>
    </Container>
    </Box>
  );
};

export default ClientDashboard;
