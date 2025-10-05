/**
 * Legal Department Dashboard
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  RateReview as ReviewIcon,
  CloudUpload as UploadIcon,
  Assessment as StatsIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';
import FKClientDataImport from '../../components/forms/FKClientDataImport';
import FKReviewQueue from '../../components/forms/FKReviewQueue';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`legal-tabpanel-${index}`}
      aria-labelledby={`legal-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const LegalDashboard: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [stats, setStats] = useState({
    total_generated: 0,
    pending_review: 0,
    approved: 0,
    rejected: 0,
    generated_today: 0,
  });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await legalService.getContractStats();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
          Departamento Legal
        </Typography>
        <Typography variant="body1" sx={{ color: 'grey.700' }}>
          Revisión y aprobación de contratos
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <AssignmentIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {stats.total_generated}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Generados
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <ReviewIcon sx={{ fontSize: 40, color: 'warning.main' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {stats.pending_review}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pendientes Revisión
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <StatsIcon sx={{ fontSize: 40, color: 'success.main' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {stats.approved}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Aprobados
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <AddIcon sx={{ fontSize: 40, color: 'info.main' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {stats.generated_today}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Hoy
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange} aria-label="legal tabs">
            <Tab label="Cola de Revisión" icon={<ReviewIcon />} iconPosition="start" />
            <Tab label="Historial" icon={<AssignmentIcon />} iconPosition="start" />
            <Tab label="Importar Datos" icon={<UploadIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          <FKReviewQueue />
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <Typography variant="h6" gutterBottom>
            Historial de Contratos
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Componente de historial próximamente
          </Typography>
        </TabPanel>

        <TabPanel value={currentTab} index={2}>
          <FKClientDataImport />
        </TabPanel>
      </Card>
    </Box>
  );
};

export default LegalDashboard;
