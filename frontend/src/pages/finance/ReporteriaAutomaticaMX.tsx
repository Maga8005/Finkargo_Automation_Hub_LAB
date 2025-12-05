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

      {/* Tab 1: Upload and Search */}
      <TabPanel value={activeTab} index={1}>
        {/* Error alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        )}

        {/* Upload Section - Outside Grid when showing Alert */}
        {!uploadSuccess ? (
          <Grid container spacing={3}>
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <UploadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Cargar Excel Maestro
                  </Typography>
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
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <Box>
            <Alert
              severity="success"
              sx={{ mb: 3 }}
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
                  Total de registros: <strong>{uploadedData.length}</strong>
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
                        label={`${sessionStats.drive_sync_stats.unchanged} sin cambios`}
                        color="default"
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                )}
              </Box>
            </Alert>

            {/* Search Section */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <SearchIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Buscar Facturas
                </Typography>

                <Grid container spacing={2} alignItems="flex-end" sx={{ width: '100%', m: 0 }}>
                  {/* Search type selector */}
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Tipo de búsqueda</InputLabel>
                      <Select
                        value={searchType}
                        label="Tipo de búsqueda"
                        onChange={(e) => {
                          setSearchType(e.target.value as SearchType);
                          setSearchValue('');
                          setFechaInicio('');
                          setFechaFin('');
                        }}
                      >
                        <MenuItem value="codigo_operacion">Código de Operación</MenuItem>
                        <MenuItem value="rfc">RFC Receptor</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  {/* Primary search input (codigo or rfc) */}
                  <Grid size={{ xs: 12, sm: 3 }} key="search-value">
                    <TextField
                      fullWidth
                      size="small"
                      label={
                        searchType === 'codigo_operacion'
                          ? 'Código(s) de Operación'
                          : 'RFC Receptor'
                      }
                      value={searchValue}
                      onChange={(e) => setSearchValue(e.target.value)}
                      placeholder={
                        searchType === 'codigo_operacion'
                          ? 'Ej: OP-001, OP-002'
                          : 'Ej: XAXX010101000'
                      }
                    />
                  </Grid>

                  {/* Date range inputs - always visible for combined filters */}
                  <Grid size={{ xs: 12, sm: 2 }} key="fecha-inicio">
                    <TextField
                      fullWidth
                      size="small"
                      type="date"
                      label="Fecha Inicio (opcional)"
                      value={fechaInicio}
                      onChange={(e) => setFechaInicio(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 2 }} key="fecha-fin">
                    <TextField
                      fullWidth
                      size="small"
                      type="date"
                      label="Fecha Fin (opcional)"
                      value={fechaFin}
                      onChange={(e) => setFechaFin(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>

                  {/* Search button */}
                  <Grid size={{ xs: 12, sm: 2 }}>
                    <Button
                      fullWidth
                      variant="contained"
                      onClick={handleSearch}
                      disabled={searching}
                      startIcon={searching ? <CircularProgress size={20} /> : <SearchIcon />}
                    >
                      Buscar
                    </Button>
                  </Grid>
                </Grid>

                {/* Helper text for search section */}
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                  {searchType === 'codigo_operacion' && (
                    <>
                      <strong>Búsqueda:</strong> Separa múltiples códigos con coma.
                      Las fechas son opcionales para filtrar por rango.
                    </>
                  )}
                  {searchType === 'rfc' && (
                    <>
                      <strong>Búsqueda:</strong> Ingresa el RFC del receptor.
                      Las fechas son opcionales para filtrar por rango.
                    </>
                  )}
                </Typography>

                {/* Search results summary */}
                {searchResults && (
                  <Box sx={{ mt: 2 }}>
                    <Divider sx={{ mb: 2 }} />
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
                      <Chip
                        label={`${searchResults.total_found} resultados`}
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        label={`Total: ${formatCurrency(searchResults.total_amount)}`}
                        color="success"
                        variant="outlined"
                      />
                      <Button
                        size="small"
                        onClick={() => setSearchResults(null)}
                      >
                        Ver todos
                      </Button>
                    </Box>

                    {/* Generate ZIP Button */}
                    <Button
                      fullWidth
                      variant="contained"
                      size="large"
                      onClick={handleGenerateZip}
                      disabled={generating}
                      startIcon={generating ? <CircularProgress size={20} /> : <DescriptionIcon />}
                      sx={{
                        height: 56,
                        backgroundColor: 'primary.main',
                        '&:hover': {
                          backgroundColor: 'primary.dark',
                        },
                      }}
                    >
                      {generating
                        ? 'Generando paquete ZIP...'
                        : `Generar Paquete ZIP (${searchResults.total_found} facturas)`}
                    </Button>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                      Incluye PDFs, XMLs y reporte Excel detallado
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Results Table */}
            {tableData.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {searchResults ? 'Resultados de Búsqueda' : 'Todos los Registros'}
                  </Typography>

                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>UUID</TableCell>
                          <TableCell>Código Op.</TableCell>
                          <TableCell>Fecha</TableCell>
                          <TableCell>RFC Receptor</TableCell>
                          <TableCell>Razón Social</TableCell>
                          <TableCell align="right">SubTotal</TableCell>
                          <TableCell align="right">IVA</TableCell>
                          <TableCell align="right">Total</TableCell>
                          <TableCell>Tipo</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {displayData.map((row, index) => (
                          <TableRow key={row.uuid + index} hover>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                {row.uuid.substring(0, 8)}...
                              </Typography>
                            </TableCell>
                            <TableCell>{row.codigo_operacion}</TableCell>
                            <TableCell>{formatDate(row.fecha_emision)}</TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                {row.rfc_receptor}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                                {row.razon_receptor}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">{formatCurrency(row.subtotal)}</TableCell>
                            <TableCell align="right">{formatCurrency(row.iva_trasladado)}</TableCell>
                            <TableCell align="right">
                              <strong>{formatCurrency(row.total)}</strong>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={row.tipo_comprobante || '-'}
                                size="small"
                                variant="outlined"
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  <TablePagination
                    component="div"
                    count={tableData.length}
                    page={page}
                    onPageChange={(_, newPage) => setPage(newPage)}
                    rowsPerPage={rowsPerPage}
                    onRowsPerPageChange={(e) => {
                      setRowsPerPage(parseInt(e.target.value, 10));
                      setPage(0);
                    }}
                    labelRowsPerPage="Filas por página:"
                    labelDisplayedRows={({ from, to, count }) =>
                      `${from}-${to} de ${count}`
                    }
                  />
                </CardContent>
              </Card>
            )}
          </Box>
        )}
      </TabPanel>

      {/* Tab 2: History */}
      <TabPanel value={activeTab} index={2}>
        <FKFinanceHistory country="MX" showStats={true} />
      </TabPanel>
    </Container>
  );
};

export default ReporteriaAutomaticaMX;
