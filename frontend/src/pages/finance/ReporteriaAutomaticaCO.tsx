/**
 * ReporteriaAutomaticaCO - Reportería Automática Colombia
 * Funcionalidad para procesar archivos de facturación Colombia
 * y consultar el Excel maestro con filtros.
 */
import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Divider,
  Alert,
  Chip,
  Stack,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
} from '@mui/material';
import {
  CloudDownload as DownloadIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  Assessment as ReportIcon,
  Upload as UploadIcon,
  Search as SearchIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import FKExcelUploaderCO from '../../components/forms/FKExcelUploaderCO';
import FKCOFilterPanel from '../../components/forms/FKCOFilterPanel';
import FKCOFilterResults from '../../components/forms/FKCOFilterResults';
import FKFinanceHistory from '../../components/forms/FKFinanceHistory';
import {
  processCOFiles,
  downloadCOReport,
  triggerDownload,
  filterCORecords,
  downloadFilteredCOData,
  downloadFilteredCOZip,
  type COProcessingResponse,
  type COFileSet,
  type COFilterRequest,
  type COFilterResponse,
} from '../../services/financeServiceCO';

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
      id={`co-tabpanel-${index}`}
      aria-labelledby={`co-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const ReporteriaAutomaticaCO: React.FC = () => {
  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // Upload/Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<COProcessingResponse | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  // Filter state
  const [filterResult, setFilterResult] = useState<COFilterResponse | null>(null);
  const [isFiltering, setIsFiltering] = useState(false);
  const [isDownloadingFiltered, setIsDownloadingFiltered] = useState(false);
  const [isDownloadingZip, setIsDownloadingZip] = useState(false);
  const [currentFilters, setCurrentFilters] = useState<COFilterRequest | null>(null);

  /**
   * Handle file upload and processing
   */
  const handleUpload = async (fileSet: COFileSet) => {
    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
      const response = await processCOFiles(fileSet);
      setResult(response);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error desconocido al procesar archivos';
      setError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Handle report download
   */
  const handleDownload = async () => {
    if (!result?.session_id) return;

    setIsDownloading(true);
    try {
      const blob = await downloadCOReport(result.session_id);
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      const filename = `Reporte_Facturacion_CO_${timestamp}.xlsx`;
      triggerDownload(blob, filename);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al descargar el reporte';
      setError(errorMessage);
    } finally {
      setIsDownloading(false);
    }
  };

  /**
   * Handle filter request
   */
  const handleFilter = async (filters: COFilterRequest) => {
    setIsFiltering(true);
    setError(null);
    setFilterResult(null);
    setCurrentFilters(filters);

    try {
      const response = await filterCORecords(filters);
      setFilterResult(response);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al consultar datos';
      setError(errorMessage);
    } finally {
      setIsFiltering(false);
    }
  };

  /**
   * Handle clear filters
   */
  const handleClearFilters = () => {
    setFilterResult(null);
    setCurrentFilters(null);
    setError(null);
  };

  /**
   * Handle download filtered data
   */
  const handleDownloadFiltered = async () => {
    if (!currentFilters) return;

    setIsDownloadingFiltered(true);
    try {
      const blob = await downloadFilteredCOData(currentFilters);
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      const filename = `Reporte_Filtrado_CO_${timestamp}.xlsx`;
      triggerDownload(blob, filename);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al descargar datos filtrados';
      setError(errorMessage);
    } finally {
      setIsDownloadingFiltered(false);
    }
  };

  /**
   * Handle download filtered data with PDFs as ZIP
   */
  const handleDownloadZip = async () => {
    if (!currentFilters) return;

    setIsDownloadingZip(true);
    setError(null);
    try {
      const blob = await downloadFilteredCOZip(currentFilters);
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      const nit = currentFilters.nit?.replace(/\./g, '').replace(/-/g, '') || '';
      const filename = nit
        ? `Facturacion_CO_${nit}_${timestamp}.zip`
        : `Facturacion_CO_${timestamp}.zip`;
      triggerDownload(blob, filename);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al generar paquete ZIP con PDFs';
      setError(errorMessage);
    } finally {
      setIsDownloadingZip(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography fontSize="2rem">🇨🇴</Typography>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
              Reportería Automática Colombia
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Procesamiento y consulta de facturas Netsuite + Noova
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab
            icon={<SearchIcon />}
            iconPosition="start"
            label="Consultar Reporte"
            id="co-tab-0"
            aria-controls="co-tabpanel-0"
          />
          <Tab
            icon={<UploadIcon />}
            iconPosition="start"
            label="Cargar Archivos"
            id="co-tab-1"
            aria-controls="co-tabpanel-1"
          />
          <Tab
            icon={<HistoryIcon />}
            iconPosition="start"
            label="Historial"
            id="co-tab-2"
            aria-controls="co-tabpanel-2"
          />
        </Tabs>
      </Paper>

      {/* Error Display (global) */}
      {error && !isProcessing && !isFiltering && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      )}

      {/* Tab 0: Filter/Query Section */}
      <TabPanel value={activeTab} index={0}>
        <Stack spacing={3}>
          {/* Filter Panel - Full width */}
          <FKCOFilterPanel
            onFilter={handleFilter}
            onClear={handleClearFilters}
            isLoading={isFiltering}
          />

          {/* Filter Results */}
          <FKCOFilterResults
            result={filterResult}
            isLoading={isFiltering}
            isDownloading={isDownloadingFiltered}
            isDownloadingZip={isDownloadingZip}
            onDownload={handleDownloadFiltered}
            onDownloadZip={handleDownloadZip}
          />
        </Stack>
      </TabPanel>

      {/* Tab 1: Upload Section */}
      <TabPanel value={activeTab} index={1}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', lg: 'row' },
            gap: 3,
          }}
        >
          {/* Upload Section */}
          <Box sx={{ width: { xs: '100%', lg: result ? '42%' : '100%' }, flexShrink: 0 }}>
            <FKExcelUploaderCO
              onUploadSuccess={handleUpload}
              onUploadError={(err) => setError(err)}
            />

            {/* Processing Indicator */}
            {isProcessing && (
              <Card sx={{ mt: 3 }} elevation={2}>
                <CardContent>
                  <Stack spacing={2} alignItems="center">
                    <CircularProgress size={48} />
                    <Typography variant="h6">Procesando archivos...</Typography>
                    <Typography variant="body2" color="text.secondary" textAlign="center">
                      Consolidando datos de Netsuite y Noova.
                      <br />
                      Esto puede tomar algunos minutos.
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            )}
          </Box>

          {/* Results Section */}
          {result && !isProcessing && (
            <Box sx={{ flex: 1 }}>
              <Card elevation={3}>
                <CardContent>
                  <Stack spacing={3}>
                    {/* Success Header */}
                    <Box display="flex" alignItems="center" gap={2}>
                      <CheckIcon color="success" sx={{ fontSize: 40 }} />
                      <Box flex={1}>
                        <Typography variant="h5" fontWeight={600}>
                          Procesamiento Completado
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {result.message}
                        </Typography>
                      </Box>
                    </Box>

                    <Divider />

                    {/* Statistics Overview */}
                    <Box>
                      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                        Resumen del Procesamiento
                      </Typography>
                      <Box
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' },
                          gap: 2,
                        }}
                      >
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="primary.main" fontWeight={700}>
                            {result.stats.total_consolidated}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Total Consolidado
                          </Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="success.main" fontWeight={700}>
                            {result.stats.matched_with_netsuite}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Con Match NS
                          </Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="info.main" fontWeight={700}>
                            {result.stats.costos_fijos_count}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Costos Fijos
                          </Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="secondary.main" fontWeight={700}>
                            {result.stats.mandato_count}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Mandato
                          </Typography>
                        </Paper>
                      </Box>
                    </Box>

                    {/* Detailed Stats Table */}
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>
                              <strong>Métrica</strong>
                            </TableCell>
                            <TableCell align="right">
                              <strong>Cantidad</strong>
                            </TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell>Registros Noova (Origen)</TableCell>
                            <TableCell align="right">{result.stats.total_records_noova}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Registros Netsuite (Valores)</TableCell>
                            <TableCell align="right">
                              {result.stats.total_records_netsuite}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Registros sin match Netsuite</TableCell>
                            <TableCell align="right">{result.stats.unmatched_noova}</TableCell>
                          </TableRow>
                          <TableRow sx={{ bgcolor: 'primary.light' }}>
                            <TableCell>
                              <strong>Total Consolidado</strong>
                            </TableCell>
                            <TableCell align="right">
                              <strong>{result.stats.total_consolidated}</strong>
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>

                    {/* Sheet Information */}
                    <Box>
                      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                        Hojas Generadas
                      </Typography>
                      <Stack spacing={1}>
                        {result.sheets.map((sheet, idx) => (
                          <Paper key={idx} variant="outlined" sx={{ p: 2 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                              <Box display="flex" alignItems="center" gap={1}>
                                <ReportIcon color="primary" />
                                <Box>
                                  <Typography variant="body1" fontWeight={600}>
                                    {sheet.sheet_name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {sheet.row_count} filas × {sheet.column_count} columnas
                                  </Typography>
                                </Box>
                              </Box>
                              <Chip
                                label={`${sheet.row_count} registros`}
                                color="primary"
                                size="small"
                              />
                            </Box>
                          </Paper>
                        ))}
                      </Stack>
                    </Box>

                    {/* Errors Display */}
                    {result.stats.errors.length > 0 && (
                      <Alert severity="warning" icon={<InfoIcon />}>
                        <Typography variant="body2" fontWeight={600} gutterBottom>
                          Se encontraron algunos errores menores:
                        </Typography>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {result.stats.errors.slice(0, 5).map((err, idx) => (
                            <li key={idx}>
                              <Typography variant="caption">{err}</Typography>
                            </li>
                          ))}
                        </ul>
                        {result.stats.errors.length > 5 && (
                          <Typography variant="caption" color="text.secondary">
                            ... y {result.stats.errors.length - 5} errores más
                          </Typography>
                        )}
                      </Alert>
                    )}

                    {/* Download Button */}
                    <Button
                      variant="contained"
                      size="large"
                      startIcon={isDownloading ? <CircularProgress size={20} /> : <DownloadIcon />}
                      onClick={handleDownload}
                      disabled={isDownloading}
                      fullWidth
                      sx={{ height: 56 }}
                    >
                      {isDownloading ? 'Descargando...' : 'Descargar Reporte Excel'}
                    </Button>

                    {/* Session Info */}
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                      <Typography variant="caption" color="text.secondary">
                        <strong>Sesión:</strong> {result.session_id}
                      </Typography>
                    </Paper>
                  </Stack>
                </CardContent>
              </Card>
            </Box>
          )}
        </Box>
      </TabPanel>

      {/* Tab 2: History */}
      <TabPanel value={activeTab} index={2}>
        <FKFinanceHistory country="CO" showStats={true} />
      </TabPanel>
    </Container>
  );
};

export default ReporteriaAutomaticaCO;
