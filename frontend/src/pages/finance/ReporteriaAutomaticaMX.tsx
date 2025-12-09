/**
 * ReporteriaAutomaticaMX - Mexico Invoicing Automation Page
 *
 * Main page for the Facturación MX automation feature.
 * Allows users to:
 * - Query the master Excel file without uploading (Consultar tab)
 * - Upload Excel files, search invoices, and generate ZIP files (Cargar Archivos tab)
 * - View history of reports generated (Historial tab)
 */

import React, { useState, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
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
  TablePagination,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Tabs,
  Tab,
  Stack,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Upload as UploadIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  History as HistoryIcon,
  CloudSync as CloudSyncIcon,
} from '@mui/icons-material';
import FKExcelUploader from '../../components/forms/FKExcelUploader';
import FKFinanceHistory from '../../components/forms/FKFinanceHistory';
import FKMXFilterPanel from '../../components/forms/FKMXFilterPanel';
import FKMXFilterResults from '../../components/forms/FKMXFilterResults';
import type {
  ExcelValidationResponse,
  InvoiceRecord,
  InvoiceSearchRequest,
  InvoiceSearchResponse,
  SearchType,
  SessionStats,
} from '../../types/finance';
import financeService from '../../services/financeService';
import {
  filterMXRecords,
  downloadFilteredMXData,
  downloadFilteredMXZip,
  triggerDownload,
  populateDriveCache,
  getDriveCacheStats,
  type MXFilterRequest,
  type MXFilterResponse,
  type PopulateCacheResponse,
  type CacheStatsResponse,
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

  // Cache population state
  const [isPopulatingCache, setIsPopulatingCache] = useState(false);
  const [cacheResult, setCacheResult] = useState<PopulateCacheResponse | null>(null);
  const [cacheStats, setCacheStats] = useState<CacheStatsResponse | null>(null);
  const [isLoadingCacheStats, setIsLoadingCacheStats] = useState(false);

  // =========================================================================
  // Upload tab state (Tab 1 - Cargar Archivos)
  // =========================================================================
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadedData, setUploadedData] = useState<InvoiceRecord[]>([]);
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Search state
  const [searchType, setSearchType] = useState<SearchType>('codigo_operacion');
  const [searchValue, setSearchValue] = useState('');
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [searchResults, setSearchResults] = useState<InvoiceSearchResponse | null>(null);
  const [searching, setSearching] = useState(false);

  // ZIP generation state
  const [generating, setGenerating] = useState(false);

  // Table state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // =========================================================================
  // Cache stats loader (Tab 0 - Consultar)
  // =========================================================================

  const loadCacheStats = async () => {
    setIsLoadingCacheStats(true);
    try {
      const stats = await getDriveCacheStats();
      setCacheStats(stats);
    } catch (err) {
      console.error('Error loading cache stats:', err);
      setCacheStats(null);
    } finally {
      setIsLoadingCacheStats(false);
    }
  };

  // Load cache stats when switching to Consultar or Cargar Archivos tab
  React.useEffect(() => {
    if (activeTab === 0 || activeTab === 1) {
      loadCacheStats();
    }
  }, [activeTab]);

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

  const handlePopulateCache = async () => {
    setIsPopulatingCache(true);
    setError(null);
    setCacheResult(null);

    try {
      const result = await populateDriveCache();
      setCacheResult(result);
      // Refresh cache stats after populating
      await loadCacheStats();
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al poblar cache de Drive';
      setError(errorMessage);
    } finally {
      setIsPopulatingCache(false);
    }
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
  // Upload handlers (Tab 1)
  // =========================================================================

  /**
   * Handle successful Excel upload.
   */
  const handleUploadSuccess = useCallback(async (response: ExcelValidationResponse) => {
    setSessionId(response.session_id);
    setUploadedData(response.data);
    setUploadSuccess(true);
    setError(null);
    setSearchResults(null);

    // Fetch session stats and merge with drive sync stats from response
    try {
      const stats = await financeService.getSessionStats(response.session_id);
      // Add drive sync stats from upload response
      if (response.drive_sync_stats) {
        stats.drive_sync_stats = response.drive_sync_stats;
      }
      setSessionStats(stats);
    } catch (err) {
      console.error('Error fetching session stats:', err);
      // If stats fetch fails, at least show drive sync stats
      if (response.drive_sync_stats) {
        setSessionStats({
          session_id: response.session_id,
          total_records: response.data.length,
          total_amount: 0,
          total_subtotal: 0,
          total_iva: 0,
          unique_rfcs: 0,
          unique_operaciones: 0,
          drive_sync_stats: response.drive_sync_stats,
        });
      }
    }
  }, []);

  /**
   * Handle upload error.
   */
  const handleUploadError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setUploadSuccess(false);
  }, []);

  /**
   * Handle search with combined filters support.
   */
  const handleSearch = useCallback(async () => {
    if (!sessionId) return;

    setSearching(true);
    setError(null);

    try {
      const request: InvoiceSearchRequest = {
        session_id: sessionId,
        search_type: searchType,
      };

      // Add primary search field based on type
      if (searchType === 'codigo_operacion') {
        request.codigo_operacion = searchValue;
      } else if (searchType === 'rfc') {
        request.rfc = searchValue;
      }

      // Always add date range if provided (for combined filters or fecha-only search)
      if (fechaInicio) {
        request.fecha_inicio = fechaInicio;
      }
      if (fechaFin) {
        request.fecha_fin = fechaFin;
      }

      const results = await financeService.searchInvoices(request);
      setSearchResults(results);
      setPage(0);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Error al buscar facturas';
      setError(errorMessage);
    } finally {
      setSearching(false);
    }
  }, [sessionId, searchType, searchValue, fechaInicio, fechaFin]);

  /**
   * Reset to initial state.
   */
  const handleReset = useCallback(() => {
    setSessionId(null);
    setUploadedData([]);
    setSessionStats(null);
    setUploadSuccess(false);
    setSearchResults(null);
    setSearchValue('');
    setFechaInicio('');
    setFechaFin('');
    setError(null);
  }, []);

  /**
   * Generate ZIP package with invoices.
   */
  const handleGenerateZip = useCallback(async () => {
    if (!sessionId || !searchResults) return;

    setGenerating(true);
    setError(null);

    try {
      // Extract UUIDs from search results
      const uuids = searchResults.results.map(r => r.uuid);

      // Prepare metadata for ZIP naming
      const metadata: Record<string, unknown> = {};

      if (searchType === 'codigo_operacion' && searchValue) {
        metadata.codigo_operacion = searchValue;
      } else if (searchType === 'rfc' && searchValue) {
        metadata.rfc = searchValue;
      } else if (searchType === 'fecha' && fechaInicio && fechaFin) {
        metadata.fecha_inicio = fechaInicio;
        metadata.fecha_fin = fechaFin;
      }

      // Call backend to generate ZIP
      const zipBlob = await financeService.generateZip({
        session_id: sessionId,
        uuids,
        metadata,
      });

      // Create download link and trigger download
      const url = window.URL.createObjectURL(zipBlob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      const filename = metadata.codigo_operacion
        ? `Facturacion_MX_${metadata.codigo_operacion}_${timestamp}.zip`
        : `Facturacion_MX_${timestamp}.zip`;

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      // Cleanup
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Error al generar el paquete ZIP';
      setError(errorMessage);
    } finally {
      setGenerating(false);
    }
  }, [sessionId, searchResults, searchType, searchValue, fechaInicio, fechaFin]);

  /**
   * Format currency for display.
   */
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  /**
   * Format date for display.
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Data to display in table
  const tableData = searchResults?.results || uploadedData;
  const displayData = tableData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

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
        >
          <Tab
            icon={<SearchIcon />}
            iconPosition="start"
            label="Consultar"
            id="mx-tab-0"
            aria-controls="mx-tabpanel-0"
          />
          <Tab
            icon={<UploadIcon />}
            iconPosition="start"
            label="Cargar Archivos"
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

        {/* Cache status warning - Show if cache is empty */}
        {!isLoadingCacheStats && cacheStats && !cacheStats.cache_ready && (
          <Alert
            severity="warning"
            sx={{ mb: 3 }}
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => setActiveTab(1)}
              >
                Ir a Cargar Archivos
              </Button>
            }
          >
            <AlertTitle>Cache de Drive no configurado</AlertTitle>
            <Typography variant="body2">
              Para generar ZIPs con PDFs y XMLs, primero debe cargar el archivo Excel maestro
              y ejecutar "Optimizar Cache" en la pestaña "Cargar Archivos".
            </Typography>
          </Alert>
        )}

        {/* Cache status info - Show if cache is ready */}
        {!isLoadingCacheStats && cacheStats && cacheStats.cache_ready && (
          <Alert severity="success" sx={{ mb: 3 }} icon={<CloudSyncIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
              <Typography variant="body2">
                <strong>Cache listo:</strong>
              </Typography>
              <Chip
                label={`${cacheStats.total_cached.toLocaleString()} archivos`}
                size="small"
                color="success"
              />
              <Chip
                label={`${cacheStats.pdf_count.toLocaleString()} PDFs`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`${cacheStats.xml_count.toLocaleString()} XMLs`}
                size="small"
                variant="outlined"
              />
            </Box>
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
            cacheReady={cacheStats?.cache_ready ?? false}
          />
        </Stack>
      </TabPanel>

      {/* Tab 1: Upload and Optimize Cache */}
      <TabPanel value={activeTab} index={1}>
        {/* Error alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        )}

        <Stack spacing={3}>
          {/* Step 1: Upload Excel */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Chip label="Paso 1" color="primary" size="small" />
                <Typography variant="h6">
                  <UploadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Cargar Excel Maestro
                </Typography>
              </Box>

              {!uploadSuccess ? (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Sube el archivo Excel con los datos de facturación. El archivo debe contener
                    las columnas: UUID, CODIGO DE OPERACIÓN, Conceptos, Fecha emision, RFC receptor,
                    Razon receptor, SubTotal, IVA Trasladado, IVA Exento, Total.
                  </Typography>
                  <FKExcelUploader
                    onUploadSuccess={handleUploadSuccess}
                    onUploadError={handleUploadError}
                    maxSizeMB={10}
                  />
                </>
              ) : (
                <Alert
                  severity="success"
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      startIcon={<RefreshIcon />}
                      onClick={handleReset}
                    >
                      Cargar nuevo archivo
                    </Button>
                  }
                >
                  <AlertTitle>Archivo cargado y sincronizado con Drive</AlertTitle>
                  <Box>
                    <Typography variant="body2">
                      Total de registros: <strong>{uploadedData.length.toLocaleString()}</strong>
                    </Typography>
                    {sessionStats?.drive_sync_stats && (
                      <Box sx={{ mt: 1, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        {sessionStats.drive_sync_stats.new > 0 && (
                          <Chip
                            label={`${sessionStats.drive_sync_stats.new} nuevos`}
                            color="success"
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {sessionStats.drive_sync_stats.updated > 0 && (
                          <Chip
                            label={`${sessionStats.drive_sync_stats.updated} actualizados`}
                            color="info"
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {sessionStats.drive_sync_stats.unchanged > 0 && (
                          <Chip
                            label={`${sessionStats.drive_sync_stats.unchanged.toLocaleString()} sin cambios`}
                            color="default"
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    )}
                  </Box>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Step 2: Optimize Cache */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Chip label="Paso 2" color={uploadSuccess ? 'primary' : 'default'} size="small" />
                <Typography variant="h6" color={uploadSuccess ? 'text.primary' : 'text.disabled'}>
                  <CloudSyncIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Optimizar Cache de Drive
                </Typography>
              </Box>

              <Typography variant="body2" color={uploadSuccess ? 'text.secondary' : 'text.disabled'} sx={{ mb: 3 }}>
                Pre-cachea los IDs de archivos de Google Drive para acelerar la generación de ZIPs.
                Este paso es <strong>obligatorio</strong> después de cargar un nuevo archivo Excel.
              </Typography>

              {/* Cache result display */}
              {cacheResult && (
                <Alert
                  severity="success"
                  sx={{ mb: 3 }}
                  onClose={() => setCacheResult(null)}
                >
                  <AlertTitle>Cache optimizado exitosamente</AlertTitle>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
                    <Chip
                      label={`${cacheResult.stats.total.toLocaleString()} total`}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={`${cacheResult.stats.cached.toLocaleString()} cacheados`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`${cacheResult.stats.already_cached.toLocaleString()} ya en cache`}
                      color="info"
                      size="small"
                    />
                    {cacheResult.stats.not_found > 0 && (
                      <Chip
                        label={`${cacheResult.stats.not_found.toLocaleString()} no encontrados`}
                        color="warning"
                        size="small"
                      />
                    )}
                  </Box>
                </Alert>
              )}

              <Button
                variant="contained"
                color="secondary"
                onClick={handlePopulateCache}
                disabled={!uploadSuccess || isPopulatingCache}
                startIcon={isPopulatingCache ? <CircularProgress size={20} /> : <CloudSyncIcon />}
                fullWidth
                sx={{ height: 56 }}
              >
                {isPopulatingCache ? 'Optimizando cache... (puede tomar varios minutos)' : 'Optimizar Cache'}
              </Button>

              {isPopulatingCache && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Este proceso puede tomar varios minutos para archivos grandes (6000+ registros).
                  Por favor espera...
                </Alert>
              )}

              {!uploadSuccess && (
                <Alert severity="info" sx={{ mt: 2 }} variant="outlined">
                  Primero cargue el archivo Excel maestro (Paso 1) para habilitar esta opción.
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Cache Status Summary */}
          {cacheStats && (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Estado actual del cache
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Chip
                    icon={<CloudSyncIcon />}
                    label={cacheStats.cache_ready ? 'Cache listo' : 'Cache vacío'}
                    color={cacheStats.cache_ready ? 'success' : 'warning'}
                  />
                  {cacheStats.cache_ready && (
                    <>
                      <Chip
                        label={`${cacheStats.total_cached.toLocaleString()} archivos`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`${cacheStats.pdf_count.toLocaleString()} PDFs`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`${cacheStats.xml_count.toLocaleString()} XMLs`}
                        size="small"
                        variant="outlined"
                      />
                    </>
                  )}
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Next step hint */}
          {cacheStats?.cache_ready && (
            <Alert
              severity="success"
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => setActiveTab(0)}
                >
                  Ir a Consultar
                </Button>
              }
            >
              <AlertTitle>Listo para consultar</AlertTitle>
              El cache está configurado. Puede ir a la pestaña "Consultar" para buscar facturas
              y generar paquetes ZIP con PDFs y XMLs.
            </Alert>
          )}
        </Stack>
      </TabPanel>

      {/* Tab 2: History */}
      <TabPanel value={activeTab} index={2}>
        <FKFinanceHistory country="MX" showStats={true} />
      </TabPanel>
    </Container>
  );
};

export default ReporteriaAutomaticaMX;
