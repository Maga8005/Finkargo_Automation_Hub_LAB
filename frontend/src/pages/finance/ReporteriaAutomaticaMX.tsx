/**
 * ReporteriaAutomaticaMX - Mexico Invoicing Automation Page
 *
 * Main page for the Facturación MX automation feature.
 * Allows users to:
 * - Query the master Excel file without uploading (Consultar tab)
 * - Upload Facturas + Complementos Excel files (Facturas + Complementos tab)
 * - View history of reports generated (Historial tab)
 */

import React, { useState, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  Chip,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Tabs,
  Tab,
  Stack,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  History as HistoryIcon,
  Payment as PaymentIcon,
  CheckCircle as CheckIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material';
import FKCombinedExcelUploader from '../../components/forms/FKCombinedExcelUploader';
import FKFinanceHistory from '../../components/forms/FKFinanceHistory';
import FKMXFilterPanel from '../../components/forms/FKMXFilterPanel';
import FKMXFilterResults from '../../components/forms/FKMXFilterResults';
import type {
  CombinedUploadResponse,
  CombinedSessionStats,
} from '../../types/finance';
import financeService from '../../services/financeService';
import {
  filterMXRecords,
  downloadFilteredMXData,
  downloadFilteredMXZip,
  triggerDownload,
  clearMXFilterCache,
  type MXFilterRequest,
  type MXFilterResponse,
} from '../../services/financeServiceMX';

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
      id={`mx-tabpanel-${index}`}
      aria-labelledby={`mx-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Mexico Invoicing Automation Page Component.
 */
const ReporteriaAutomaticaMX: React.FC = () => {
  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // =========================================================================
  // Filter tab state (Tab 0 - Consultar)
  // =========================================================================
  const [filterResult, setFilterResult] = useState<MXFilterResponse | null>(null);
  const [isFiltering, setIsFiltering] = useState(false);
  const [isDownloadingFiltered, setIsDownloadingFiltered] = useState(false);
  const [isDownloadingZip, setIsDownloadingZip] = useState(false);
  const [currentFilters, setCurrentFilters] = useState<MXFilterRequest | null>(null);
  const [filterError, setFilterError] = useState<string | null>(null);

  // =========================================================================
  // Combined Upload tab state (Tab 1 - Facturas + Complementos)
  // =========================================================================
  const [combinedSessionId, setCombinedSessionId] = useState<string | null>(null);
  const [combinedStats, setCombinedStats] = useState<CombinedSessionStats | null>(null);
  const [combinedUploadSuccess, setCombinedUploadSuccess] = useState(false);
  const [combinedError, setCombinedError] = useState<string | null>(null);
  const [driveSyncStats, setDriveSyncStats] = useState<{
    new: number;
    updated: number;
    unchanged: number;
  } | null>(null);
  const [isRefreshingCache, setIsRefreshingCache] = useState(false);
  const [cacheRefreshSuccess, setCacheRefreshSuccess] = useState(false);

  // =========================================================================
  // Filter handlers (Tab 0)
  // =========================================================================

  const handleFilter = async (filters: MXFilterRequest) => {
    setIsFiltering(true);
    setFilterError(null);
    setCurrentFilters(filters);

    try {
      const response = await filterMXRecords(filters);
      setFilterResult(response);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al consultar archivo maestro';
      setFilterError(errorMessage);
    } finally {
      setIsFiltering(false);
    }
  };

  const handleClearFilter = () => {
    setFilterResult(null);
    setCurrentFilters(null);
    setFilterError(null);
  };

  const handleDownloadFiltered = async () => {
    if (!currentFilters) return;

    setIsDownloadingFiltered(true);
    setFilterError(null);
    try {
      const blob = await downloadFilteredMXData(currentFilters);
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      const rfc = currentFilters.rfc?.replace(/\./g, '').replace(/-/g, '') || '';
      const filename = rfc
        ? `Facturacion_MX_${rfc}_${timestamp}.xlsx`
        : `Facturacion_MX_${timestamp}.xlsx`;
      triggerDownload(blob, filename);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al descargar datos filtrados';
      setFilterError(errorMessage);
    } finally {
      setIsDownloadingFiltered(false);
    }
  };

  const handleDownloadZipFiltered = async () => {
    if (!currentFilters) return;

    setIsDownloadingZip(true);
    setFilterError(null);
    try {
      const blob = await downloadFilteredMXZip(currentFilters);
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      const rfc = currentFilters.rfc?.replace(/\./g, '').replace(/-/g, '') || '';
      const filename = rfc
        ? `Facturacion_MX_${rfc}_${timestamp}.zip`
        : `Facturacion_MX_${timestamp}.zip`;
      triggerDownload(blob, filename);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al generar paquete ZIP con PDFs/XMLs';
      setFilterError(errorMessage);
    } finally {
      setIsDownloadingZip(false);
    }
  };

  // =========================================================================
  // Combined Upload handlers (Tab 1)
  // =========================================================================

  /**
   * Handle successful combined Excel upload.
   */
  const handleCombinedUploadSuccess = useCallback(async (response: CombinedUploadResponse) => {
    setCombinedSessionId(response.session_id);
    setCombinedUploadSuccess(true);
    setCombinedError(null);

    // Store Drive sync stats if available
    if (response.drive_sync_stats) {
      setDriveSyncStats(response.drive_sync_stats);
    } else {
      setDriveSyncStats(null);
    }

    // Fetch session stats
    const allData = [...response.facturas_data, ...response.complementos_data];
    try {
      const stats = await financeService.getCombinedSessionStats(response.session_id);
      setCombinedStats(stats);
    } catch (err) {
      console.error('Error fetching combined session stats:', err);
      // Set basic stats from response
      setCombinedStats({
        session_id: response.session_id,
        facturas_count: response.facturas_valid_rows,
        complementos_count: response.complementos_valid_rows,
        total_records: response.total_records,
        facturas_total: response.facturas_data.reduce((sum, r) => sum + r.total, 0),
        complementos_total: response.complementos_data.reduce((sum, r) => sum + r.total, 0),
        combined_total: allData.reduce((sum, r) => sum + r.total, 0),
        unique_rfcs: new Set(allData.map(r => r.rfc_receptor)).size,
        unique_operaciones: new Set(allData.map(r => r.codigo_operacion)).size,
      });
    }
  }, []);

  /**
   * Handle combined upload error.
   */
  const handleCombinedUploadError = useCallback((errorMessage: string) => {
    setCombinedError(errorMessage);
    setCombinedUploadSuccess(false);
  }, []);

  /**
   * Reset combined state.
   */
  const handleCombinedReset = useCallback(() => {
    setCombinedSessionId(null);
    setCombinedStats(null);
    setCombinedUploadSuccess(false);
    setCombinedError(null);
    setDriveSyncStats(null);
  }, []);

  /**
   * Refresh cache - clears the backend filter cache so next query fetches fresh data.
   */
  const handleRefreshCache = useCallback(async () => {
    setIsRefreshingCache(true);
    setCombinedError(null);
    setCacheRefreshSuccess(false);
    try {
      await clearMXFilterCache();
      // Show success feedback - user can now query with fresh data
      setCacheRefreshSuccess(true);
      // Auto-hide success message after 3 seconds
      setTimeout(() => setCacheRefreshSuccess(false), 3000);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al recargar cache';
      setCombinedError(errorMessage);
    } finally {
      setIsRefreshingCache(false);
    }
  }, []);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography fontSize="2rem">🇲🇽</Typography>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" fontWeight="bold" color="primary.main">
              Reportería Automática MX
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Automatización de búsqueda y generación de paquetes de facturación
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
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab
            icon={<SearchIcon />}
            iconPosition="start"
            label="Consultar"
            id="mx-tab-0"
            aria-controls="mx-tabpanel-0"
          />
          <Tab
            icon={<PaymentIcon />}
            iconPosition="start"
            label="Facturas + Complementos"
            id="mx-tab-1"
            aria-controls="mx-tabpanel-1"
          />
          <Tab
            icon={<HistoryIcon />}
            iconPosition="start"
            label="Historial"
            id="mx-tab-2"
            aria-controls="mx-tabpanel-2"
          />
        </Tabs>
      </Paper>

      {/* Tab 0: Query/Filter */}
      <TabPanel value={activeTab} index={0}>
        {/* Filter error display */}
        {filterError && !isFiltering && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setFilterError(null)}>
            <Typography variant="body2">{filterError}</Typography>
          </Alert>
        )}

        <Stack spacing={3}>
          {/* Filter Panel - Full width */}
          <FKMXFilterPanel
            onFilter={handleFilter}
            onClear={handleClearFilter}
            isLoading={isFiltering}
          />

          {/* Filter Results */}
          <FKMXFilterResults
            result={filterResult}
            isLoading={isFiltering}
            isDownloading={isDownloadingFiltered}
            isDownloadingZip={isDownloadingZip}
            onDownload={handleDownloadFiltered}
            onDownloadZip={handleDownloadZipFiltered}
          />
        </Stack>
      </TabPanel>

      {/* Tab 1: Combined Upload (Facturas + Complementos) */}
      <TabPanel value={activeTab} index={1}>
        {/* Combined error alert */}
        {combinedError && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setCombinedError(null)}>
            <AlertTitle>Error</AlertTitle>
            {combinedError}
          </Alert>
        )}

        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', lg: 'row' },
            gap: 3,
          }}
        >
          {/* Left side: Upload Section */}
          <Box sx={{ width: { xs: '100%', lg: combinedUploadSuccess ? '42%' : '100%' }, flexShrink: 0 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <UploadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Paso 1: Cargar Facturas y Complementos de Pago
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Sube dos archivos Excel: uno con facturas y otro con complementos de pago.
                  Ambos archivos deben tener la misma estructura de columnas.
                </Typography>
                <FKCombinedExcelUploader
                  onUploadSuccess={handleCombinedUploadSuccess}
                  onUploadError={handleCombinedUploadError}
                  maxSizeMB={10}
                />
              </CardContent>
            </Card>

            {/* Paso 2: Recargar Cache - Only show after upload success */}
            {combinedUploadSuccess && (
              <Card sx={{ mt: 3 }} elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="warning.main">
                    <RefreshIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Paso 2: Recargar Cache (Obligatorio)
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Después de cargar nuevos archivos, es obligatorio recargar el cache
                    para que la pestaña "Consultar" muestre los datos actualizados.
                  </Typography>
                  <Button
                    fullWidth
                    variant="contained"
                    color="warning"
                    onClick={handleRefreshCache}
                    disabled={isRefreshingCache}
                    startIcon={isRefreshingCache ? <CircularProgress size={20} /> : <RefreshIcon />}
                    sx={{ height: 48 }}
                  >
                    {isRefreshingCache ? 'Recargando Cache...' : 'Recargar Cache'}
                  </Button>
                  {cacheRefreshSuccess && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      Cache recargado exitosamente. Ya puede consultar los datos actualizados.
                    </Alert>
                  )}
                </CardContent>
              </Card>
            )}
          </Box>

          {/* Right side: Results Section (only shows after upload) */}
          {combinedUploadSuccess && (
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
                          Procesamiento completado y reporte subido a Google Drive
                        </Typography>
                      </Box>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<RefreshIcon />}
                        onClick={handleCombinedReset}
                      >
                        Cargar nuevos
                      </Button>
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
                            {combinedStats?.total_records || 0}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Total Consolidado
                          </Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="info.main" fontWeight={700}>
                            {combinedStats?.facturas_count || 0}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Facturas
                          </Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="secondary.main" fontWeight={700}>
                            {combinedStats?.complementos_count || 0}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Complementos
                          </Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="success.main" fontWeight={700}>
                            {combinedStats?.unique_rfcs || 0}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            RFCs Únicos
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
                            <TableCell>Facturas procesadas</TableCell>
                            <TableCell align="right">{combinedStats?.facturas_count || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Complementos de pago procesados</TableCell>
                            <TableCell align="right">{combinedStats?.complementos_count || 0}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Operaciones únicas</TableCell>
                            <TableCell align="right">{combinedStats?.unique_operaciones || 0}</TableCell>
                          </TableRow>
                          <TableRow sx={{ bgcolor: 'primary.light' }}>
                            <TableCell>
                              <strong>Total Consolidado</strong>
                            </TableCell>
                            <TableCell align="right">
                              <strong>{combinedStats?.total_records || 0}</strong>
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>

                    {/* Drive Sync Stats */}
                    {driveSyncStats && (
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                          Sincronización con Google Drive
                        </Typography>
                        <Stack spacing={1}>
                          <Paper variant="outlined" sx={{ p: 2 }}>
                            <Box display="flex" alignItems="center" justifyContent="space-between">
                              <Box display="flex" alignItems="center" gap={1}>
                                <ReportIcon color="primary" />
                                <Box>
                                  <Typography variant="body1" fontWeight={600}>
                                    Archivo Maestro MX
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    2 hojas: Facturas + Complementos de Pago
                                  </Typography>
                                </Box>
                              </Box>
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                <Chip
                                  label={`${driveSyncStats.new} nuevos`}
                                  color="success"
                                  size="small"
                                />
                                <Chip
                                  label={`${driveSyncStats.updated} actualizados`}
                                  color="info"
                                  size="small"
                                />
                                <Chip
                                  label={`${driveSyncStats.unchanged} sin cambios`}
                                  color="default"
                                  size="small"
                                />
                              </Box>
                            </Box>
                          </Paper>
                        </Stack>
                      </Box>
                    )}

                    {/* Session Info */}
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                      <Typography variant="caption" color="text.secondary">
                        <strong>Sesión:</strong> {combinedSessionId}
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
        <FKFinanceHistory country="MX" showStats={true} />
      </TabPanel>
    </Container>
  );
};

export default ReporteriaAutomaticaMX;
