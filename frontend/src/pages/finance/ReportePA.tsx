/**
 * ReportePA - PA Report Classification Processing
 *
 * Finance page for processing PA reports:
 * - Upload NetSuite movements file
 * - Step 1: Clean and filter PA data
 * - Step 2: Apply classification rules
 * - Download processed files
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
  Chip,
  Stack,
  CircularProgress,
  Grid,
  Stepper,
  Step,
  StepLabel,
  StepContent,
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
  CloudDownload as DownloadIcon,
  CheckCircle as CheckIcon,
  PlayArrow as PlayIcon,
  Assessment as ReportIcon,
  History as HistoryIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  getRulesSummary,
  uploadNetSuiteFile,
  cleanData,
  downloadCleanedFile,
  classifyData,
  downloadClassifiedFile,
  getProcessingHistory,
  triggerDownload,
} from '../../services/financeServicePA';
import type {
  PARulesSummary,
  PAUploadResponse,
  PACleanedPreview,
  PAClassifiedPreview,
  PAProcessingStats,
  PAProcessingHistoryEntry,
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
      id={`pa-report-tabpanel-${index}`}
      aria-labelledby={`pa-report-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

// Processing steps
const steps = [
  { label: 'Cargar Archivo', description: 'Sube el archivo de movimientos de NetSuite' },
  { label: 'Limpiar Datos', description: 'Filtra cuentas PA y agrega columnas de homologación' },
  { label: 'Clasificar', description: 'Aplica reglas de clasificación' },
];

const ReportePA: React.FC = () => {
  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // Rules summary state
  const [rulesSummary, setRulesSummary] = useState<PARulesSummary | null>(null);
  const [loadingRules, setLoadingRules] = useState(true);

  // Processing state
  const [activeStep, setActiveStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] = useState<PAUploadResponse | null>(null);
  const [cleanedPreview, setCleanedPreview] = useState<PACleanedPreview | null>(null);
  const [classifiedPreview, setClassifiedPreview] = useState<PAClassifiedPreview | null>(null);

  // Loading states
  const [uploading, setUploading] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // History state
  const [history, setHistory] = useState<PAProcessingHistoryEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Load rules summary
  const loadRulesSummary = useCallback(async () => {
    try {
      setLoadingRules(true);
      const data = await getRulesSummary();
      setRulesSummary(data);
    } catch (error) {
      console.error('Error loading rules summary:', error);
    } finally {
      setLoadingRules(false);
    }
  }, []);

  useEffect(() => {
    loadRulesSummary();
  }, [loadRulesSummary]);

  // Load history when tab changes
  useEffect(() => {
    if (activeTab === 1) {
      loadHistory();
    }
  }, [activeTab]);

  const loadHistory = async () => {
    try {
      setLoadingHistory(true);
      const response = await getProcessingHistory({ limit: 20 });
      setHistory(response.entries);
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      setUploadResponse(null);
      setCleanedPreview(null);
      setClassifiedPreview(null);

      const response = await uploadNetSuiteFile(file);

      if (response.success) {
        setUploadResponse(response);
        setSessionId(response.session_id);
        setActiveStep(1);
      } else {
        setError(response.message || 'Error al cargar archivo');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  // Handle clean step
  const handleClean = async () => {
    if (!sessionId) return;

    try {
      setCleaning(true);
      setError(null);

      const response = await cleanData(sessionId);

      if (response.status === 'cleaned') {
        setCleanedPreview(response);
        setActiveStep(2);
      } else if (response.status === 'failed') {
        setError(response.stats.warnings.join(', ') || 'Error al limpiar datos');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
    } finally {
      setCleaning(false);
    }
  };

  // Handle classify step
  const handleClassify = async () => {
    if (!sessionId) return;

    try {
      setClassifying(true);
      setError(null);

      const response = await classifyData(sessionId);

      if (response.status === 'classified') {
        setClassifiedPreview(response);
        setActiveStep(3);
      } else if (response.status === 'failed') {
        setError(response.stats.warnings.join(', ') || 'Error al clasificar datos');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
    } finally {
      setClassifying(false);
    }
  };

  // Handle downloads
  const handleDownloadCleaned = async () => {
    if (!sessionId) return;

    try {
      setDownloading('cleaned');
      const blob = await downloadCleanedFile(sessionId);
      triggerDownload(blob, `PA_Limpio_${sessionId}.xlsx`);
    } catch (err) {
      console.error('Error downloading cleaned file:', err);
      setError('Error al descargar archivo limpio');
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadClassified = async () => {
    if (!sessionId) return;

    try {
      setDownloading('classified');
      const blob = await downloadClassifiedFile(sessionId);
      triggerDownload(blob, `PA_Clasificado_${sessionId}.xlsx`);
    } catch (err) {
      console.error('Error downloading classified file:', err);
      setError('Error al descargar archivo clasificado');
    } finally {
      setDownloading(null);
    }
  };

  // Reset processing
  const handleReset = () => {
    setActiveStep(0);
    setSessionId(null);
    setUploadResponse(null);
    setCleanedPreview(null);
    setClassifiedPreview(null);
    setError(null);
  };

  // Format number for display
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('es-CO').format(num);
  };

  // Render stats card
  const renderStats = (stats: PAProcessingStats) => (
    <Grid container spacing={2} sx={{ mt: 2 }}>
      <Grid size={{ xs: 6, md: 3 }}>
        <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light' }}>
          <Typography variant="h5" color="primary.contrastText">
            {formatNumber(stats.pa_rows)}
          </Typography>
          <Typography variant="body2" color="primary.contrastText">
            Registros PA
          </Typography>
        </Paper>
      </Grid>
      <Grid size={{ xs: 6, md: 3 }}>
        <Paper sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="h5" color="text.primary">
            {formatNumber(stats.total_rows)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Filas
          </Typography>
        </Paper>
      </Grid>
      <Grid size={{ xs: 6, md: 3 }}>
        <Paper
          sx={{
            p: 2,
            textAlign: 'center',
            bgcolor: stats.balance_valid ? 'success.light' : 'warning.light',
          }}
        >
          <Typography variant="h5">
            {stats.balance_valid ? <CheckIcon /> : <WarningIcon />}
          </Typography>
          <Typography variant="body2">
            {stats.balance_valid ? 'Balance OK' : 'Balance no cuadra'}
          </Typography>
        </Paper>
      </Grid>
      <Grid size={{ xs: 6, md: 3 }}>
        <Paper sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="h5" color="text.primary">
            {formatNumber(stats.classified_count)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Clasificados
          </Typography>
        </Paper>
      </Grid>

      {stats.warnings.length > 0 && (
        <Grid size={{ xs: 12 }}>
          <Alert severity="warning">
            {stats.warnings.map((w, i) => (
              <div key={i}>{w}</div>
            ))}
          </Alert>
        </Grid>
      )}
    </Grid>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
          <ReportIcon sx={{ mr: 1, verticalAlign: 'bottom' }} />
          Reporte PA
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Procesamiento y clasificación de reportes de Patrimonio Autónomo
        </Typography>
      </Box>

      {/* Rules Check */}
      {loadingRules ? (
        <Alert severity="info" sx={{ mb: 3 }}>
          <CircularProgress size={16} sx={{ mr: 1 }} /> Verificando reglas de clasificación...
        </Alert>
      ) : rulesSummary && rulesSummary.catalog_count === 0 ? (
        <Alert severity="warning" sx={{ mb: 3 }}>
          No hay catálogo de cuentas PA cargado. Por favor cargue el catálogo en "Reglas Clasificación PA" antes de procesar reportes.
        </Alert>
      ) : null}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Card>
        <CardContent>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
          >
            <Tab label="Procesar Reporte" icon={<ReportIcon />} iconPosition="start" />
            <Tab label="Historial" icon={<HistoryIcon />} iconPosition="start" />
          </Tabs>

          {/* Tab 0: Processing */}
          <TabPanel value={activeTab} index={0}>
            <Stepper activeStep={activeStep} orientation="vertical">
              {/* Step 0: Upload */}
              <Step>
                <StepLabel>{steps[0].label}</StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {steps[0].description}
                  </Typography>

                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    style={{ display: 'none' }}
                    id="netsuite-upload"
                    onChange={handleFileUpload}
                  />
                  <label htmlFor="netsuite-upload">
                    <Button
                      variant="contained"
                      component="span"
                      startIcon={uploading ? <CircularProgress size={20} /> : <UploadIcon />}
                      disabled={uploading}
                    >
                      {uploading ? 'Cargando...' : 'Cargar Archivo NetSuite'}
                    </Button>
                  </label>

                  {uploadResponse && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      {uploadResponse.message}
                    </Alert>
                  )}
                </StepContent>
              </Step>

              {/* Step 1: Clean */}
              <Step>
                <StepLabel>{steps[1].label}</StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {steps[1].description}
                  </Typography>

                  {uploadResponse && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2">
                        Archivo: <strong>{uploadResponse.filename}</strong>
                      </Typography>
                      <Typography variant="body2">
                        Filas totales: <strong>{formatNumber(uploadResponse.total_rows)}</strong>
                      </Typography>
                      <Typography variant="body2">
                        Registros PA: <strong>{formatNumber(uploadResponse.pa_rows)}</strong>
                      </Typography>
                    </Box>
                  )}

                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      onClick={handleClean}
                      startIcon={cleaning ? <CircularProgress size={20} /> : <PlayIcon />}
                      disabled={cleaning}
                    >
                      {cleaning ? 'Limpiando...' : 'Ejecutar Limpieza'}
                    </Button>
                  </Stack>

                  {cleanedPreview && (
                    <Box sx={{ mt: 3 }}>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        Datos limpiados correctamente
                      </Alert>

                      {renderStats(cleanedPreview.stats)}

                      <Button
                        variant="outlined"
                        onClick={handleDownloadCleaned}
                        startIcon={downloading === 'cleaned' ? <CircularProgress size={20} /> : <DownloadIcon />}
                        disabled={downloading !== null}
                        sx={{ mt: 2 }}
                      >
                        Descargar Archivo Limpio
                      </Button>
                    </Box>
                  )}
                </StepContent>
              </Step>

              {/* Step 2: Classify */}
              <Step>
                <StepLabel>{steps[2].label}</StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {steps[2].description}
                  </Typography>

                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      onClick={handleClassify}
                      startIcon={classifying ? <CircularProgress size={20} /> : <PlayIcon />}
                      disabled={classifying}
                    >
                      {classifying ? 'Clasificando...' : 'Ejecutar Clasificación'}
                    </Button>
                  </Stack>

                  {classifiedPreview && (
                    <Box sx={{ mt: 3 }}>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        Datos clasificados correctamente
                      </Alert>

                      {renderStats(classifiedPreview.stats)}

                      {/* Classification Summary */}
                      {Object.keys(classifiedPreview.classification_summary).length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Resumen por Categoría:
                          </Typography>
                          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                            {Object.entries(classifiedPreview.classification_summary).map(([cat, count]) => (
                              <Chip
                                key={cat}
                                label={`${cat}: ${formatNumber(count)}`}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                            ))}
                          </Stack>
                        </Box>
                      )}

                      <Button
                        variant="contained"
                        color="success"
                        onClick={handleDownloadClassified}
                        startIcon={downloading === 'classified' ? <CircularProgress size={20} /> : <DownloadIcon />}
                        disabled={downloading !== null}
                        sx={{ mt: 2 }}
                      >
                        Descargar Archivo Clasificado
                      </Button>
                    </Box>
                  )}
                </StepContent>
              </Step>
            </Stepper>

            {/* Reset button */}
            {activeStep > 0 && (
              <Box sx={{ mt: 3 }}>
                <Button variant="outlined" onClick={handleReset}>
                  Nuevo Reporte
                </Button>
              </Box>
            )}
          </TabPanel>

          {/* Tab 1: History */}
          <TabPanel value={activeTab} index={1}>
            {loadingHistory ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Session ID</TableCell>
                      <TableCell>Archivo</TableCell>
                      <TableCell>Estado</TableCell>
                      <TableCell>Registros PA</TableCell>
                      <TableCell>Usuario</TableCell>
                      <TableCell>Fecha</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {history.map((entry) => (
                      <TableRow key={entry.id}>
                        <TableCell>{entry.session_id}</TableCell>
                        <TableCell>{entry.original_filename || '-'}</TableCell>
                        <TableCell>
                          <Chip
                            label={entry.status}
                            color={
                              entry.status === 'classified'
                                ? 'success'
                                : entry.status === 'failed'
                                ? 'error'
                                : 'default'
                            }
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{entry.stats?.pa_rows || 0}</TableCell>
                        <TableCell>{entry.processed_by_email || '-'}</TableCell>
                        <TableCell>
                          {new Date(entry.started_at).toLocaleString('es-CO')}
                        </TableCell>
                      </TableRow>
                    ))}
                    {history.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          No hay historial de procesamiento
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </TabPanel>
        </CardContent>
      </Card>
    </Container>
  );
};

export default ReportePA;
