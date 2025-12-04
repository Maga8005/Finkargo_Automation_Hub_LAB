/**
 * FKMXFilterResults - Component to display MX filter results
 *
 * Shows filtered records from the MX master Excel with:
 * - Summary statistics
 * - Sortable and paginated table
 * - Download options (Excel and ZIP)
 */
import React, { useState, useMemo } from 'react';
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
  TableSortLabel,
  Paper,
  Chip,
  Stack,
  Button,
  CircularProgress,
  TextField,
  InputAdornment,
  Alert,
  LinearProgress,
  Fade,
} from '@mui/material';
import {
  CloudDownload as DownloadIcon,
  TableChart as TableIcon,
  CheckCircle as CheckIcon,
  Search as SearchIcon,
  FolderZip as ZipIcon,
} from '@mui/icons-material';
import {
  type MXFilterResponse,
  type MXFilteredRecord,
  formatCurrency,
  formatDate,
} from '../../services/financeServiceMX';

interface FKMXFilterResultsProps {
  result: MXFilterResponse | null;
  isLoading?: boolean;
  isDownloading?: boolean;
  isDownloadingZip?: boolean;
  zipProgress?: number; // 0-100 percentage
  onDownload: () => void;
  onDownloadZip?: () => void;
}

type Order = 'asc' | 'desc';

const FKMXFilterResults: React.FC<FKMXFilterResultsProps> = ({
  result,
  isLoading = false,
  isDownloading = false,
  isDownloadingZip = false,
  zipProgress,
  onDownload,
  onDownloadZip,
}) => {
  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Sorting state
  const [orderBy, setOrderBy] = useState<keyof MXFilteredRecord>('fecha_emision');
  const [order, setOrder] = useState<Order>('desc');

  // Search state for table filtering
  const [searchTerm, setSearchTerm] = useState('');

  // Reset pagination when results change
  React.useEffect(() => {
    setPage(0);
  }, [result]);

  // Handle sorting
  const handleSort = (property: keyof MXFilteredRecord) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
    setPage(0);
  };

  // Handle page change
  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  // Handle rows per page change
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Filtered and sorted data
  const processedRecords = useMemo(() => {
    if (!result?.records) return [];

    let filtered = result.records;

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter((record) => {
        return (
          record.uuid?.toLowerCase().includes(term) ||
          record.codigo_operacion?.toLowerCase().includes(term) ||
          record.rfc_receptor?.toLowerCase().includes(term) ||
          record.razon_receptor?.toLowerCase().includes(term) ||
          record.conceptos?.toLowerCase().includes(term)
        );
      });
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      const aValue = a[orderBy] ?? '';
      const bValue = b[orderBy] ?? '';

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return order === 'asc' ? aValue - bValue : bValue - aValue;
      }

      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();

      if (order === 'asc') {
        return aStr.localeCompare(bStr);
      }
      return bStr.localeCompare(aStr);
    });

    return filtered;
  }, [result?.records, searchTerm, orderBy, order]);

  // Paginated data
  const paginatedRecords = useMemo(() => {
    return processedRecords.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [processedRecords, page, rowsPerPage]);

  // Loading state
  if (isLoading) {
    return (
      <Card elevation={2}>
        <CardContent>
          <Stack alignItems="center" spacing={2} py={4}>
            <CircularProgress />
            <Typography color="text.secondary">
              Consultando archivo maestro MX...
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    );
  }

  // No results yet
  if (!result) {
    return null;
  }

  // No records found
  if (result.total_records === 0) {
    return (
      <Card elevation={2}>
        <CardContent>
          <Alert severity="info">
            No se encontraron registros con los filtros especificados.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={2}>
      <CardContent>
        <Stack spacing={3}>
          {/* Header with stats */}
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <CheckIcon color="success" />
              <Typography variant="h6" fontWeight={600}>
                Resultados
              </Typography>
            </Box>
            <Chip
              icon={<TableIcon />}
              label={`${result.total_records} registros encontrados`}
              color="primary"
              variant="outlined"
            />
          </Box>

          {/* Summary Stats */}
          <Box display="flex" gap={2} flexWrap="wrap">
            <Paper variant="outlined" sx={{ px: 2, py: 1 }}>
              <Typography variant="caption" color="text.secondary">Total</Typography>
              <Typography variant="h6" fontWeight={600} color="primary.main">
                {formatCurrency(result.total_amount)}
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ px: 2, py: 1 }}>
              <Typography variant="caption" color="text.secondary">SubTotal</Typography>
              <Typography variant="h6" fontWeight={600}>
                {formatCurrency(result.total_subtotal)}
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ px: 2, py: 1 }}>
              <Typography variant="caption" color="text.secondary">IVA</Typography>
              <Typography variant="h6" fontWeight={600}>
                {formatCurrency(result.total_iva)}
              </Typography>
            </Paper>
          </Box>

          {/* Filters Applied */}
          {Object.keys(result.filters_applied).length > 0 && (
            <Box display="flex" gap={1} flexWrap="wrap" alignItems="center">
              <Typography variant="body2" color="text.secondary">Filtros:</Typography>
              {Object.entries(result.filters_applied).map(([key, value]) => (
                <Chip
                  key={key}
                  label={`${key}: ${value}`}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          )}

          {/* Search within results */}
          <TextField
            size="small"
            placeholder="Buscar en resultados..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(0);
            }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }
            }}
          />

          {/* Results Table */}
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow sx={{ backgroundColor: 'grey.50' }}>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'uuid'}
                      direction={orderBy === 'uuid' ? order : 'asc'}
                      onClick={() => handleSort('uuid')}
                    >
                      UUID
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'codigo_operacion'}
                      direction={orderBy === 'codigo_operacion' ? order : 'asc'}
                      onClick={() => handleSort('codigo_operacion')}
                    >
                      Código Op.
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'fecha_emision'}
                      direction={orderBy === 'fecha_emision' ? order : 'asc'}
                      onClick={() => handleSort('fecha_emision')}
                    >
                      Fecha
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={orderBy === 'rfc_receptor'}
                      direction={orderBy === 'rfc_receptor' ? order : 'asc'}
                      onClick={() => handleSort('rfc_receptor')}
                    >
                      RFC
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Razón Social</TableCell>
                  <TableCell align="right">
                    <TableSortLabel
                      active={orderBy === 'subtotal'}
                      direction={orderBy === 'subtotal' ? order : 'asc'}
                      onClick={() => handleSort('subtotal')}
                    >
                      SubTotal
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="right">IVA</TableCell>
                  <TableCell align="right">
                    <TableSortLabel
                      active={orderBy === 'total'}
                      direction={orderBy === 'total' ? order : 'asc'}
                      onClick={() => handleSort('total')}
                    >
                      Total
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Tipo</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedRecords.map((record, index) => (
                  <TableRow key={`${record.uuid}-${index}`} hover>
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          maxWidth: 100,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                        title={record.uuid}
                      >
                        {record.uuid ? `${record.uuid.substring(0, 8)}...` : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>{record.codigo_operacion || '-'}</TableCell>
                    <TableCell>{formatDate(record.fecha_emision)}</TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {record.rfc_receptor || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{
                          maxWidth: 150,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                        title={record.razon_receptor}
                      >
                        {record.razon_receptor || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{formatCurrency(record.subtotal)}</TableCell>
                    <TableCell align="right">{formatCurrency(record.iva_trasladado)}</TableCell>
                    <TableCell align="right">
                      <Typography fontWeight={600}>{formatCurrency(record.total)}</Typography>
                    </TableCell>
                    <TableCell>
                      {record.tipo_comprobante && (
                        <Chip
                          label={record.tipo_comprobante}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" color="text.secondary">
              Mostrando {page * rowsPerPage + 1} -{' '}
              {Math.min((page + 1) * rowsPerPage, processedRecords.length)} de{' '}
              {processedRecords.length}
              {searchTerm && ` (filtrado de ${result.total_records})`}
            </Typography>
            <TablePagination
              component="div"
              count={processedRecords.length}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[10, 25, 50, 100]}
              labelRowsPerPage="Filas por página:"
              labelDisplayedRows={({ from, to, count }) =>
                `${from}-${to} de ${count !== -1 ? count : `más de ${to}`}`
              }
            />
          </Box>

          {/* ZIP Generation Progress */}
          <Fade in={isDownloadingZip}>
            <Box sx={{ display: isDownloadingZip ? 'block' : 'none' }}>
              <Alert
                severity="info"
                icon={<CircularProgress size={24} />}
                sx={{ mb: 2 }}
              >
                <Box sx={{ width: '100%' }}>
                  <Typography variant="body1" fontWeight={600} gutterBottom>
                    Generando paquete ZIP...
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Descargando {result?.total_records || 0} archivos PDF y XML desde Google Drive.
                    Este proceso puede tomar varios minutos.
                  </Typography>
                  <LinearProgress
                    variant={zipProgress !== undefined ? "determinate" : "indeterminate"}
                    value={zipProgress}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'rgba(0,0,0,0.1)',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 4,
                      }
                    }}
                  />
                  {zipProgress !== undefined && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      {zipProgress}% completado
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Por favor no cierre esta ventana. La descarga comenzará automáticamente al finalizar.
                  </Typography>
                </Box>
              </Alert>
            </Box>
          </Fade>

          {/* Download Buttons */}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Button
              variant="contained"
              size="large"
              startIcon={isDownloading ? <CircularProgress size={20} color="inherit" /> : <DownloadIcon />}
              onClick={onDownload}
              disabled={isDownloading || isDownloadingZip}
              fullWidth
              sx={{ height: 56 }}
            >
              {isDownloading ? 'Descargando...' : 'Descargar Excel'}
            </Button>

            {onDownloadZip && (
              <Button
                variant="outlined"
                size="large"
                color="secondary"
                startIcon={isDownloadingZip ? <CircularProgress size={20} color="inherit" /> : <ZipIcon />}
                onClick={onDownloadZip}
                disabled={isDownloading || isDownloadingZip}
                fullWidth
                sx={{ height: 56 }}
              >
                {isDownloadingZip ? 'Generando ZIP...' : 'Descargar con PDFs/XMLs (ZIP)'}
              </Button>
            )}
          </Stack>

          {/* ZIP info message - only show when not downloading */}
          {onDownloadZip && !isDownloadingZip && (
            <Alert severity="info" variant="outlined">
              <Typography variant="body2">
                <strong>Descargar con PDFs/XMLs:</strong> Genera un archivo ZIP con el reporte Excel y los archivos PDF/XML de
                las facturas encontrados en Google Drive. Este proceso puede tomar varios minutos dependiendo de la
                cantidad de facturas.
              </Typography>
            </Alert>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default FKMXFilterResults;
