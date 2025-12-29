/**
 * ReglasClasificacionPA - PA Classification Rules Management
 *
 * Admin page for uploading and managing PA classification rules:
 * - Account Catalog
 * - Classification Rules
 * - Clasificación Cuenta Rules
 * - Nexo Rules
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  Description as FileIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import {
  getRulesSummary,
  uploadAccountCatalog,
  getAccountCatalog,
  uploadClassificationRules,
  getClassificationRules,
  uploadClasificacionCuentaRules,
  getClasificacionCuentaRules,
  uploadNexoRules,
  getNexoRules,
} from '../../services/financeServicePA';
import type {
  PARulesSummary,
  PAAccountCatalogEntry,
  PAClassificationRuleEntry,
  PAClasificacionCuentaRuleEntry,
  PANexoRuleEntry,
} from '../../types/financePA';

// Tab panel component
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
      id={`pa-rules-tabpanel-${index}`}
      aria-labelledby={`pa-rules-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const ReglasClasificacionPA: React.FC = () => {
  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // Summary state
  const [summary, setSummary] = useState<PARulesSummary | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  // Upload states
  const [uploading, setUploading] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Data states
  const [catalogEntries, setCatalogEntries] = useState<PAAccountCatalogEntry[]>([]);
  const [classificationRules, setClassificationRules] = useState<PAClassificationRuleEntry[]>([]);
  const [clasificacionCuentaRules, setClasificacionCuentaRules] = useState<PAClasificacionCuentaRuleEntry[]>([]);
  const [nexoRules, setNexoRules] = useState<PANexoRuleEntry[]>([]);

  // Load summary on mount
  const loadSummary = useCallback(async () => {
    try {
      setLoadingSummary(true);
      const data = await getRulesSummary();
      setSummary(data);
    } catch (error) {
      console.error('Error loading summary:', error);
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  // Load data based on active tab
  useEffect(() => {
    const loadTabData = async () => {
      try {
        switch (activeTab) {
          case 0: {
            const catalogResponse = await getAccountCatalog(100, 0);
            setCatalogEntries(catalogResponse.entries);
            break;
          }
          case 1: {
            const classResponse = await getClassificationRules();
            setClassificationRules(classResponse.rules);
            break;
          }
          case 2: {
            const cuentaResponse = await getClasificacionCuentaRules();
            setClasificacionCuentaRules(cuentaResponse.rules);
            break;
          }
          case 3: {
            const nexoResponse = await getNexoRules();
            setNexoRules(nexoResponse.rules);
            break;
          }
        }
      } catch (error) {
        console.error('Error loading tab data:', error);
      }
    };

    loadTabData();
  }, [activeTab]);

  // Handle file upload
  const handleFileUpload = async (
    file: File,
    type: 'catalog' | 'classification' | 'clasificacion_cuenta' | 'nexo'
  ) => {
    try {
      setUploading(type);
      setUploadError(null);
      setUploadSuccess(null);

      let response;
      switch (type) {
        case 'catalog':
          response = await uploadAccountCatalog(file);
          break;
        case 'classification':
          response = await uploadClassificationRules(file);
          break;
        case 'clasificacion_cuenta':
          response = await uploadClasificacionCuentaRules(file);
          break;
        case 'nexo':
          response = await uploadNexoRules(file);
          break;
      }

      if (response.success) {
        setUploadSuccess(response.message);
        loadSummary();
        // Reload current tab data
        setActiveTab((prev) => prev);
      } else {
        setUploadError(response.message || 'Error al cargar archivo');
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      setUploadError(errorMessage);
    } finally {
      setUploading(null);
    }
  };

  // File input handler
  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>,
    type: 'catalog' | 'classification' | 'clasificacion_cuenta' | 'nexo'
  ) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileUpload(file, type);
    }
    // Reset input
    event.target.value = '';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
          <SettingsIcon sx={{ mr: 1, verticalAlign: 'bottom' }} />
          Reglas Clasificación PA
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Administración de reglas para clasificación de reportes PA (Patrimonio Autónomo)
        </Typography>
      </Box>

      {/* Alerts */}
      {uploadError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setUploadError(null)}>
          {uploadError}
        </Alert>
      )}
      {uploadSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setUploadSuccess(null)}>
          {uploadSuccess}
        </Alert>
      )}

      {/* Summary Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Resumen de Reglas</Typography>
            <Button
              size="small"
              startIcon={loadingSummary ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={loadSummary}
              disabled={loadingSummary}
            >
              Actualizar
            </Button>
          </Box>

          {loadingSummary ? (
            <CircularProgress />
          ) : summary ? (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {summary.catalog_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Cuentas PA
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {summary.classification_rules_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reglas Clasificación
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {summary.clasificacion_cuenta_rules_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reglas Cuenta
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {summary.nexo_rules_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reglas Nexo
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          ) : (
            <Typography color="text.secondary">No hay datos disponibles</Typography>
          )}
        </CardContent>
      </Card>

      {/* Tabs */}
      <Card>
        <CardContent>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="Catálogo de Cuentas" icon={<FileIcon />} iconPosition="start" />
            <Tab label="Reglas Clasificación" icon={<FileIcon />} iconPosition="start" />
            <Tab label="Reglas por Cuenta" icon={<FileIcon />} iconPosition="start" />
            <Tab label="Reglas Nexo" icon={<FileIcon />} iconPosition="start" />
          </Tabs>

          {/* Tab 0: Account Catalog */}
          <TabPanel value={activeTab} index={0}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Catálogo de Cuentas PA
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Carga el catálogo de cuentas PA que se usará para filtrar los movimientos de NetSuite.
                Columnas requeridas: Cuenta Finkargo, Cuenta Homologación, Nombre Homologación
              </Typography>

              <input
                type="file"
                accept=".xlsx,.xls"
                style={{ display: 'none' }}
                id="catalog-upload"
                onChange={(e) => handleFileChange(e, 'catalog')}
              />
              <label htmlFor="catalog-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={uploading === 'catalog' ? <CircularProgress size={20} /> : <UploadIcon />}
                  disabled={uploading !== null}
                >
                  {uploading === 'catalog' ? 'Cargando...' : 'Cargar Catálogo'}
                </Button>
              </label>
            </Box>

            <Divider sx={{ my: 2 }} />

            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Cuenta Finkargo</TableCell>
                    <TableCell>Cuenta Homologación</TableCell>
                    <TableCell>Nombre Homologación</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {catalogEntries.map((entry, index) => (
                    <TableRow key={entry.id || index}>
                      <TableCell>{entry.cuenta_finkargo}</TableCell>
                      <TableCell>{entry.cuenta_homologacion}</TableCell>
                      <TableCell>{entry.nombre_homologacion}</TableCell>
                    </TableRow>
                  ))}
                  {catalogEntries.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} align="center">
                        No hay datos cargados
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Tab 1: Classification Rules */}
          <TabPanel value={activeTab} index={1}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Reglas de Clasificación Principal
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Reglas para determinar Categoría y Subcategoría basadas en Tipo de Transacción y Tipo de Comprobante.
                Columnas requeridas: Tipo Transacción, Tipo Comprobante, Categoría
              </Typography>

              <input
                type="file"
                accept=".xlsx,.xls"
                style={{ display: 'none' }}
                id="classification-upload"
                onChange={(e) => handleFileChange(e, 'classification')}
              />
              <label htmlFor="classification-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={uploading === 'classification' ? <CircularProgress size={20} /> : <UploadIcon />}
                  disabled={uploading !== null}
                >
                  {uploading === 'classification' ? 'Cargando...' : 'Cargar Reglas'}
                </Button>
              </label>
            </Box>

            <Divider sx={{ my: 2 }} />

            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Tipo Transacción</TableCell>
                    <TableCell>Tipo Comprobante</TableCell>
                    <TableCell>Categoría</TableCell>
                    <TableCell>Subcategoría Base</TableCell>
                    <TableCell>Prioridad</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {classificationRules.map((rule, index) => (
                    <TableRow key={rule.id || index}>
                      <TableCell>{rule.tipo_transaccion}</TableCell>
                      <TableCell>{rule.tipo_comprobante}</TableCell>
                      <TableCell>{rule.categoria}</TableCell>
                      <TableCell>{rule.subcategoria_base || '-'}</TableCell>
                      <TableCell>{rule.prioridad}</TableCell>
                    </TableRow>
                  ))}
                  {classificationRules.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        No hay reglas cargadas
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Tab 2: Clasificación Cuenta Rules */}
          <TabPanel value={activeTab} index={2}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Reglas por Nombre de Cuenta
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Reglas para determinar Clasificación (Realizada/No Realizada, etc.) basadas en el nombre de la cuenta.
                Columnas requeridas: Cuenta Nombre Patrón, Clasificación
              </Typography>

              <input
                type="file"
                accept=".xlsx,.xls"
                style={{ display: 'none' }}
                id="clasificacion-cuenta-upload"
                onChange={(e) => handleFileChange(e, 'clasificacion_cuenta')}
              />
              <label htmlFor="clasificacion-cuenta-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={uploading === 'clasificacion_cuenta' ? <CircularProgress size={20} /> : <UploadIcon />}
                  disabled={uploading !== null}
                >
                  {uploading === 'clasificacion_cuenta' ? 'Cargando...' : 'Cargar Reglas'}
                </Button>
              </label>
            </Box>

            <Divider sx={{ my: 2 }} />

            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Patrón Nombre Cuenta</TableCell>
                    <TableCell>Clasificación</TableCell>
                    <TableCell>Categoría Aplicable</TableCell>
                    <TableCell>Prioridad</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {clasificacionCuentaRules.map((rule, index) => (
                    <TableRow key={rule.id || index}>
                      <TableCell>{rule.cuenta_nombre_patron}</TableCell>
                      <TableCell>{rule.clasificacion}</TableCell>
                      <TableCell>{rule.categoria_aplicable || 'Todas'}</TableCell>
                      <TableCell>{rule.prioridad}</TableCell>
                    </TableRow>
                  ))}
                  {clasificacionCuentaRules.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} align="center">
                        No hay reglas cargadas
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Tab 3: Nexo Rules */}
          <TabPanel value={activeTab} index={3}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Reglas de Nexo
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Reglas para determinar el valor de Nexo basado en el nombre de la cuenta.
                Columnas requeridas: Cuenta Nombre Patrón, Nexo
              </Typography>

              <input
                type="file"
                accept=".xlsx,.xls"
                style={{ display: 'none' }}
                id="nexo-upload"
                onChange={(e) => handleFileChange(e, 'nexo')}
              />
              <label htmlFor="nexo-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={uploading === 'nexo' ? <CircularProgress size={20} /> : <UploadIcon />}
                  disabled={uploading !== null}
                >
                  {uploading === 'nexo' ? 'Cargando...' : 'Cargar Reglas'}
                </Button>
              </label>
            </Box>

            <Divider sx={{ my: 2 }} />

            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Patrón Nombre Cuenta</TableCell>
                    <TableCell>Nexo</TableCell>
                    <TableCell>Prioridad</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {nexoRules.map((rule, index) => (
                    <TableRow key={rule.id || index}>
                      <TableCell>{rule.cuenta_nombre_patron}</TableCell>
                      <TableCell>{rule.nexo}</TableCell>
                      <TableCell>{rule.prioridad}</TableCell>
                    </TableRow>
                  ))}
                  {nexoRules.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} align="center">
                        No hay reglas cargadas
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>
        </CardContent>
      </Card>
    </Container>
  );
};

export default ReglasClasificacionPA;
