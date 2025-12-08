/**
 * FKPagaLocalCODocumentosOperacion - Operation documents for Paga Local Colombia
 * Contains subtabs for: Mandato (IM), Solicitud de Desembolso, Template DIAN - Mandato (IM)
 */
import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Card,
  CardContent,
  Typography,
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  MonetizationOn as MonetizationOnIcon,
  AccountBalance as AccountBalanceIcon,
} from '@mui/icons-material';
import FKPagaLocalCOContractRequest from './FKPagaLocalCOContractRequest';
import FKSolicitudDesembolsoRequest from './FKSolicitudDesembolsoRequest';
import FKInstruccionMandatoForm from './FKInstruccionMandatoForm';
import FKDIANMandatoForm from './FKDIANMandatoForm';

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
      id={`documentos-operacion-tabpanel-${index}`}
      aria-labelledby={`documentos-operacion-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

// Document type configurations
const DOCUMENT_CONFIGS = [
  {
    type: 'pl_co_mandato_im',
    label: 'Mandato (IM)',
    tabLabel: 'Mandato (IM)',
    description: 'Documento de mandato para importación. Este documento autoriza a Finkargo a actuar en nombre del cliente para operaciones de importación.',
    icon: <AssignmentIcon />,
  },
  {
    type: 'pl_co_solicitud_desembolso',
    label: 'Solicitud de Desembolso',
    tabLabel: 'Solicitud Desembolso',
    description: 'Formulario de solicitud de desembolso para operaciones de Paga Local. Requerido para iniciar el proceso de pago.',
    icon: <MonetizationOnIcon />,
  },
  {
    type: 'pl_co_dian_mandato_im',
    label: 'Template DIAN - Mandato (IM)',
    tabLabel: 'DIAN Mandato (IM)',
    description: 'Template oficial de la DIAN para mandato de importación. Formato requerido para trámites aduaneros.',
    icon: <AccountBalanceIcon />,
  },
];

const FKPagaLocalCODocumentosOperacion: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              minHeight: 64,
            },
          }}
        >
          {DOCUMENT_CONFIGS.map((config, index) => (
            <Tab
              key={config.type}
              label={config.tabLabel}
              icon={config.icon}
              iconPosition="start"
              id={`documentos-operacion-tab-${index}`}
              aria-controls={`documentos-operacion-tabpanel-${index}`}
            />
          ))}
        </Tabs>
      </Paper>

      {DOCUMENT_CONFIGS.map((config, index) => (
        <TabPanel key={config.type} value={currentTab} index={index}>
          {/* Info Card */}
          <Card
            elevation={0}
            sx={{ bgcolor: 'warning.50', border: 1, borderColor: 'warning.200', mb: 3 }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ color: 'warning.main', mt: 0.5 }}>
                  {React.cloneElement(config.icon, { fontSize: 'large' })}
                </Box>
                <Box>
                  <Typography
                    variant="subtitle1"
                    sx={{ fontWeight: 600, mb: 1, color: 'warning.dark' }}
                  >
                    {config.label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {config.description}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Contract Request Form - Use specialized forms for each document type */}
          {config.type === 'pl_co_solicitud_desembolso' ? (
            <FKSolicitudDesembolsoRequest />
          ) : config.type === 'pl_co_mandato_im' ? (
            <FKInstruccionMandatoForm />
          ) : config.type === 'pl_co_dian_mandato_im' ? (
            <FKDIANMandatoForm />
          ) : (
            <FKPagaLocalCOContractRequest
              contractType={config.type}
              contractLabel={config.label}
            />
          )}
        </TabPanel>
      ))}
    </Box>
  );
};

export default FKPagaLocalCODocumentosOperacion;
