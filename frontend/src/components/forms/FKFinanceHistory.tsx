/**
 * FKFinanceHistory - Component to display finance report generation history
 *
 * Shows a table with all generated reports for CO and/or MX operations
 * with filtering, pagination, and statistics.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Grid,
  Divider,
  Button,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  History as HistoryIcon,
  CloudDone as CloudIcon,
  CloudOff as CloudOffIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';
import {
  getFinanceHistory,
  getFinanceStats,
  exportFinanceHistoryCSV,
  triggerCSVDownload,
  formatReportType,
  formatReportStatus,
  getStatusColor,
  getCountryFlag,
  formatCountry,
  type FinanceReportSummary,
  type FinanceReportStats,
  type FinanceHistoryFilter,
  type ReportCountry,
  type ReportType,
  type ReportStatus,
} from '../../services/financeHistoryService';

interface FKFinanceHistoryProps {
  /** Filter to specific country (optional) */
  country?: ReportCountry;
  /** Show statistics panel */
  showStats?: boolean;
  /** Page size options */
  rowsPerPageOptions?: number[];
}

const FKFinanceHistory: React.FC<FKFinanceHistoryProps> = ({
  country,
  showStats = true,
  rowsPerPageOptions = [10, 25, 50],
}) => {
  // Data state
  const [reports, setReports] = useState<FinanceReportSummary[]>([]);
  const [stats, setStats] = useState<FinanceReportStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Filter state
  const [filterCountry, setFilterCountry] = useState<ReportCountry | ''>(country || '');
  const [filterType, setFilterType] = useState<ReportType | ''>('');
  const [filterStatus, setFilterStatus] = useState<ReportStatus | ''>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Export state
  const [exporting, setExporting] = useState(false);

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const filters: FinanceHistoryFilter = {
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      };

      if (filterCountry) filters.country = filterCountry;
      if (filterType) filters.report_type = filterType;
      if (filterStatus) filters.status = filterStatus;
      if (dateFrom) filters.date_from = dateFrom;
      if (dateTo) filters.date_to = dateTo;

      const [historyResponse, statsResponse] = await Promise.all([
        getFinanceHistory(filters),
        showStats ? getFinanceStats(filterCountry || undefined) : Promise.resolve(null),
      ]);

      setReports(historyResponse.reports);
      setTotal(historyResponse.total);

      if (statsResponse) {
        setStats(statsResponse);
      }
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err as Error)?.message ||
        'Error al cargar historial';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, filterCountry, filterType, filterStatus, dateFrom, dateTo, showStats]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handlers
  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleRefresh = () => {
    fetchData();
  };

  const handleClearFilters = () => {
    setFilterCountry(country || '');
    setFilterType('');
    setFilterStatus('');
    setDateFrom('');
    setDateTo('');
    setPage(0);
  };

  // Export to CSV
  const handleExportCSV = async () => {
    setExporting(true);
    setError(null);

    try {
      const filters: FinanceHistoryFilter = {};
      if (filterCountry) filters.country = filterCountry;
      if (filterType) filters.report_type = filterType;
      if (filterStatus) filters.status = filterStatus;
      if (dateFrom) filters.date_from = dateFrom;
      if (dateTo) filters.date_to = dateTo;

      const blob = await exportFinanceHistoryCSV(filters);

      // Generate filename
      const timestamp = new Date().toISOString().slice(0, 10);
      const countrySuffix = filterCountry ? `_${filterCountry}` : '';
      const filename = `Historial_Reportes${countrySuffix}_${timestamp}.csv`;

      triggerCSVDownload(blob, filename);
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err as Error)?.message ||
        'Error al exportar historial';
      setError(errorMessage);
    } finally {
      setExporting(false);
    }
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), "dd MMM yyyy, HH:mm", { locale: es });
    } catch {
      return dateString;
    }
  };

  return (
    <Card elevation={2}>
      <CardContent>
        {/* Header */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
          <Box display="flex" alignItems="center" gap={1}>
            <HistoryIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Historial de Reportes
              {country && ` - ${formatCountry(country)}`}
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={exporting ? <CircularProgress size={16} /> : <DownloadIcon />}
              onClick={handleExportCSV}
              disabled={loading || exporting || total === 0}
            >
              {exporting ? 'Exportando...' : 'Exportar CSV'}
            </Button>
            <Tooltip title="Actualizar">
              <IconButton onClick={handleRefresh} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Statistics Panel */}
        {showStats && stats && (
          <>
            <Grid container spacing={2} mb={3}>
              <Grid size={{ xs: 6, sm: 4, md: 2 }}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary.main" fontWeight={700}>
                    {stats.total_reports}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Total Reportes
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 6, sm: 4, md: 2 }}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main" fontWeight={700}>
                    {stats.reports_today}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Hoy
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 6, sm: 4, md: 2 }}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="info.main" fontWeight={700}>
                    {stats.reports_this_week}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Esta Semana
                  </Typography>
                </Paper>
              </Grid>
              {!country && (
                <>
                  <Grid size={{ xs: 6, sm: 4, md: 2 }}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700}>
                        {stats.co_reports}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Colombia
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 6, sm: 4, md: 2 }}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700}>
                        {stats.mx_reports}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        México
                      </Typography>
                    </Paper>
                  </Grid>
                </>
              )}
              <Grid size={{ xs: 6, sm: 4, md: 2 }}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="error.main" fontWeight={700}>
                    {stats.failed_count}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Fallidos
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
            <Divider sx={{ mb: 3 }} />
          </>
        )}

        {/* Filters */}
        <Box mb={3}>
          <Box display="flex" alignItems="center" gap={1} mb={2}>
            <FilterIcon fontSize="small" color="action" />
            <Typography variant="subtitle2" color="text.secondary">
              Filtros
            </Typography>
          </Box>
          <Grid container spacing={2}>
            {!country && (
              <Grid size={{ xs: 12, sm: 6, md: 2 }}>
                <FormControl size="small" fullWidth>
                  <InputLabel>País</InputLabel>
                  <Select
                    value={filterCountry}
                    label="País"
                    onChange={(e) => {
                      setFilterCountry(e.target.value as ReportCountry | '');
                      setPage(0);
                    }}
                  >
                    <MenuItem value="">Todos</MenuItem>
                    <MenuItem value="CO">Colombia</MenuItem>
                    <MenuItem value="MX">México</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl size="small" fullWidth>
                <InputLabel>Tipo</InputLabel>
                <Select
                  value={filterType}
                  label="Tipo"
                  onChange={(e) => {
                    setFilterType(e.target.value as ReportType | '');
                    setPage(0);
                  }}
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="facturacion">Procesamiento</MenuItem>
                  <MenuItem value="consulta">Consulta</MenuItem>
                  <MenuItem value="zip_download">Descarga ZIP</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl size="small" fullWidth>
                <InputLabel>Estado</InputLabel>
                <Select
                  value={filterStatus}
                  label="Estado"
                  onChange={(e) => {
                    setFilterStatus(e.target.value as ReportStatus | '');
                    setPage(0);
                  }}
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="completed">Completado</MenuItem>
                  <MenuItem value="failed">Fallido</MenuItem>
                  <MenuItem value="processing">Procesando</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <TextField
                size="small"
                fullWidth
                type="date"
                label="Desde"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  setPage(0);
                }}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <TextField
                size="small"
                fullWidth
                type="date"
                label="Hasta"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  setPage(0);
                }}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
          </Grid>
        </Box>

        {/* Error */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Loading */}
        {loading && (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        )}

        {/* Table */}
        {!loading && (
          <>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'grey.50' }}>
                    <TableCell>ID Reporte</TableCell>
                    {!country && <TableCell>País</TableCell>}
                    <TableCell>Tipo</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Resumen</TableCell>
                    <TableCell>Drive</TableCell>
                    <TableCell>Fecha</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reports.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={country ? 6 : 7} align="center">
                        <Typography color="text.secondary" py={4}>
                          No hay reportes que mostrar
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    reports.map((report) => (
                      <TableRow key={report.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {report.report_id}
                          </Typography>
                        </TableCell>
                        {!country && (
                          <TableCell>
                            <Tooltip title={formatCountry(report.country)}>
                              <Typography fontSize="1.2rem">
                                {getCountryFlag(report.country)}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                        )}
                        <TableCell>
                          <Chip
                            label={formatReportType(report.report_type)}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={formatReportStatus(report.status)}
                            size="small"
                            color={getStatusColor(report.status)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {report.stats_summary}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {report.drive_uploaded ? (
                            <Tooltip title="Subido a Drive">
                              <CloudIcon color="success" fontSize="small" />
                            </Tooltip>
                          ) : (
                            <Tooltip title="No subido a Drive">
                              <CloudOffIcon color="disabled" fontSize="small" />
                            </Tooltip>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(report.generated_at)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              component="div"
              count={total}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={rowsPerPageOptions}
              labelRowsPerPage="Filas por página:"
              labelDisplayedRows={({ from, to, count }) =>
                `${from}-${to} de ${count !== -1 ? count : `más de ${to}`}`
              }
            />
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default FKFinanceHistory;
