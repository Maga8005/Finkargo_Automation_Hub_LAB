/**
 * Operations Department Dashboard
 * Request contracts and download approved contracts for customer signature
 */
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Description as DescriptionIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import FKApprovedContracts from '../../components/forms/FKApprovedContracts';
import FKContractRequest from '../../components/forms/FKContractRequest';

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
      id={`operations-tabpanel-${index}`}
      aria-labelledby={`operations-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const OperationsDashboard: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
          Departamento de Operaciones
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Solicitud de contratos y gestión de aprobados
        </Typography>
      </Box>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange} aria-label="operations tabs">
            <Tab label="Solicitar Contrato" icon={<AddIcon />} iconPosition="start" />
            <Tab label="Contratos Aprobados" icon={<CheckCircleIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          <Box sx={{ mb: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'info.50', border: 1, borderColor: 'info.200' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <DescriptionIcon sx={{ color: 'info.main', mt: 0.5 }} />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'info.dark' }}>
                      Solicitud de Contrato
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Busca el cliente y solicita la generación de un contrato. El equipo legal lo revisará y aprobará antes de que puedas descargarlo.
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <FKContractRequest />
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <Box sx={{ mb: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'success.50', border: 1, borderColor: 'success.200' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <CheckCircleIcon sx={{ color: 'success.main', mt: 0.5 }} />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'success.dark' }}>
                      Contratos Aprobados
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Descarga los PDFs aprobados por el equipo legal para enviarlos a los clientes para su firma.
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Los PDFs están guardados en Supabase Storage y son inmutables para mantener la trazabilidad.
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <FKApprovedContracts />
        </TabPanel>
      </Card>
    </Box>
  );
};

export default OperationsDashboard;
