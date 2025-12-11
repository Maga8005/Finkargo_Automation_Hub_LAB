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
  Sync as SyncIcon,
  Storage as StorageIcon,
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
  populateDriveCacheCO,
  getDriveCacheStatsCO,
  type COProcessingResponse,
  type COFileSet,
  type COFilterRequest,
  type COFilterResponse,
  type CacheStatsResponse,
  type PopulateCacheResponse,
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

  // Cache state
  const [cacheStats, setCacheStats] = useState<CacheStatsResponse | null>(null);
  const [isLoadingCacheStats, setIsLoadingCacheStats] = useState(false);
  const [isOptimizingCache, setIsOptimizingCache] = useState(false);
  const [cacheResult, setCacheResult] = useState<PopulateCacheResponse | null>(null);

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

  /**
   * Load cache statistics
   */
  const loadCacheStats = async () => {
    setIsLoadingCacheStats(true);
    try {
      const stats = await getDriveCacheStatsCO();
      setCacheStats(stats);
    } catch (err) {
      console.error('Error loading cache stats:', err);
      setCacheStats(null);
    } finally {
      setIsLoadingCacheStats(false);
    }
  };

  /**
   * Handle cache optimization
   */
  const handleOptimizeCache = async () => {
    setIsOptimizingCache(true);
    setError(null);
    setCacheResult(null);
    try {
      const result = await populateDriveCacheCO();
      setCacheResult(result);
      // Reload cache stats after optimization
      await loadCacheStats();
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al optimizar el cache de Drive';
      setError(errorMessage);
    } finally {
      setIsOptimizingCache(false);
    }
  };

  // Load cache stats when tab changes
  React.useEffect(() => {
    if (activeTab === 0 || activeTab === 1) {
      loadCacheStats();
    }
  }, [activeTab]);

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
            cacheReady={cacheStats?.cache_ready ?? false}
          />
        </Stack>
      </TabPanel>

      {/* Tab 1: Upload Section - 2 Steps */}
      <TabPanel value={activeTab} index={1}>
        <Stack spacing={3}>
          {/* Step 1: Upload Files */}
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Chip label="Paso 1" color="primary" size="small" />
                <Typography variant="h6" fontWeight={600}>
                  Cargar Archivos Excel
                </Typography>
              </Box>

              <FKExcelUploaderCO
                onUploadSuccess={handleUpload}
                onUploadError={(err) => setError(err)}
              />

              {/* Processing Indicator */}
              {isProcessing && (
                <Card sx={{ mt: 3 }} elevation={1}>
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

              {/* Results Section */}
              {result && !isProcessing && (
                <Card elevation={1} sx={{ mt: 3 }}>
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
              )}
            </CardContent>
          </Card>

          {/* Step 2: Optimize Cache */}
          <Card
            elevation={2}
            sx={{
              opacity: result ? 1 : 0.6,
              transition: 'opacity 0.3s',
            }}
          >
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Chip label="Paso 2" color={result ? 'primary' : 'default'} size="small" />
                <Typography variant="h6" fontWeight={600}>
                  Optimizar Cache de Drive
                </Typography>
              </Box>

              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  Este paso indexa los archivos PDF en Google Drive para acelerar la generación de ZIPs.
                  <strong> Es necesario ejecutar esto después de cargar nuevos archivos para habilitar la descarga de ZIPs con PDFs.</strong>
                </Typography>
              </Alert>

              {/* Cache Status */}
              {isLoadingCacheStats ? (
                <Box display="flex" alignItems="center" gap={2} py={2}>
                  <CircularProgress size={24} />
                  <Typography>Cargando estado del cache...</Typography>
                </Box>
              ) : cacheStats ? (
                <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
                  <Stack spacing={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <StorageIcon color={cacheStats.cache_ready ? 'success' : 'warning'} />
                      <Typography variant="subtitle1" fontWeight={600}>
                        Estado del Cache
                      </Typography>
                      <Chip
                        label={cacheStats.cache_ready ? 'Listo' : 'No configurado'}
                        color={cacheStats.cache_ready ? 'success' : 'warning'}
                        size="small"
                      />
                    </Box>
                    <Box display="flex" gap={3} flexWrap="wrap">
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Total Archivos Cacheados
                        </Typography>
                        <Typography variant="h5" fontWeight={600}>
                          {cacheStats.total_cached}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          PDFs
                        </Typography>
                        <Typography variant="h5" fontWeight={600} color="primary.main">
                          {cacheStats.pdf_count}
                        </Typography>
                      </Box>
                    </Box>
                  </Stack>
                </Paper>
              ) : (
                <Alert severity="warning" sx={{ mb: 3 }}>
                  No se pudo cargar el estado del cache.
                </Alert>
              )}

              {/* Cache Result */}
              {cacheResult && (
                <Alert
                  severity="success"
                  sx={{ mb: 3 }}
                  onClose={() => setCacheResult(null)}
                >
                  <Typography variant="body2" fontWeight={600}>
                    {cacheResult.message}
                  </Typography>
                  <Typography variant="body2">
                    Total procesados: {cacheResult.stats.total} |
                    Nuevos cacheados: {cacheResult.stats.cached} |
                    Ya existentes: {cacheResult.stats.already_cached} |
                    No encontrados: {cacheResult.stats.not_found}
                  </Typography>
                </Alert>
              )}

              {/* Optimize Button */}
              <Button
                variant="contained"
                color="secondary"
                size="large"
                startIcon={isOptimizingCache ? <CircularProgress size={20} color="inherit" /> : <SyncIcon />}
                onClick={handleOptimizeCache}
                disabled={!result || isOptimizingCache}
                fullWidth
                sx={{ height: 56 }}
              >
                {isOptimizingCache ? 'Optimizando Cache...' : 'Optimizar Cache de Drive'}
              </Button>

              {!result && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Primero complete el Paso 1 para habilitar esta opción.
                </Typography>
              )}

              {isOptimizingCache && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    Indexando archivos PDF en Google Drive. Este proceso puede tomar varios minutos dependiendo de la cantidad de facturas.
                    Por favor no cierre esta ventana.
                  </Typography>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Stack>
      </TabPanel>

      {/* Tab 2: History */}
      <TabPanel value={activeTab} index={2}>
        <FKFinanceHistory country="CO" showStats={true} />
      </TabPanel>
    </Container>
  );
};

export default ReporteriaAutomaticaCO;
