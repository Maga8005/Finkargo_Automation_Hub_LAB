/**
 * Operations Paga Local Colombia Dashboard
 * Request contracts and download approved documents for Paga Local Colombia product
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
  AccountBalance as AccountBalanceIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import FKPagaLocalCOCuentaCliente from '../../components/forms/FKPagaLocalCOCuentaCliente';
import FKPagaLocalCODocumentosOperacion from '../../components/forms/FKPagaLocalCODocumentosOperacion';
import FKPagaLocalCOApprovedContracts from '../../components/forms/FKPagaLocalCOApprovedContracts';

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
      id={`paga-local-co-tabpanel-${index}`}
      aria-labelledby={`paga-local-co-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const OperationsPagaLocalColombia: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
          Paga Local Colombia - Solicitar
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Solicitud de contratos y documentos para operaciones de Paga Local en Colombia
        </Typography>
      </Box>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange} aria-label="paga local colombia tabs">
            <Tab
              label="Contratos Cuenta Cliente"
              icon={<AccountBalanceIcon />}
              iconPosition="start"
            />
            <Tab
              label="Documentos Operación"
              icon={<AssignmentIcon />}
              iconPosition="start"
            />
            <Tab
              label="Contratos Aprobados"
              icon={<CheckCircleIcon />}
              iconPosition="start"
            />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          <Box sx={{ mb: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'primary.50', border: 1, borderColor: 'primary.200' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <AccountBalanceIcon sx={{ color: 'primary.main', mt: 0.5 }} />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'primary.dark' }}>
                      Contratos Cuenta Cliente
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Solicite contratos marco para cuentas de cliente según el tipo de aval:
                    </Typography>
                    <Typography variant="body2" color="text.secondary" component="ul" sx={{ pl: 2, m: 0 }}>
                      <li><strong>Aval Persona Jurídica:</strong> K° Crédito y K° Mandato PJ</li>
                      <li><strong>Aval Persona Natural:</strong> K° Crédito y K° Mandato PN</li>
                      <li><strong>Sin Aval:</strong> K° Crédito y K° Mandato No Aval</li>
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <FKPagaLocalCOCuentaCliente />
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <Box sx={{ mb: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'warning.50', border: 1, borderColor: 'warning.200' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <AssignmentIcon sx={{ color: 'warning.main', mt: 0.5 }} />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'warning.dark' }}>
                      Documentos Operación
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Solicite documentos operativos requeridos para las operaciones de Paga Local:
                    </Typography>
                    <Typography variant="body2" color="text.secondary" component="ul" sx={{ pl: 2, m: 0 }}>
                      <li><strong>Mandato (IM):</strong> Autorización para actuar en importaciones</li>
                      <li><strong>Solicitud de Desembolso:</strong> Formulario para solicitar pagos</li>
                      <li><strong>Template DIAN - Mandato (IM):</strong> Formato oficial para trámites aduaneros</li>
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <FKPagaLocalCODocumentosOperacion />
        </TabPanel>

        <TabPanel value={currentTab} index={2}>
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
                      Descarga los PDFs aprobados por el equipo legal para enviarlos a los clientes.
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Los documentos están guardados en Supabase Storage y son inmutables para mantener la trazabilidad.
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          <FKPagaLocalCOApprovedContracts />
        </TabPanel>
      </Card>
    </Box>
  );
};

export default OperationsPagaLocalColombia;
