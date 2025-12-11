/**
 * FKCOFilterResults - Muestra los resultados de filtrado del Excel CO
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Stack,
  Paper,
  Alert,
  CircularProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  TextField,
  InputAdornment,
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
  type COFilterResponse,
  type COFilteredRecord,
} from '../../services/financeServiceCO';

interface FKCOFilterResultsProps {
  result: COFilterResponse | null;
  isLoading?: boolean;
  isDownloading?: boolean;
  isDownloadingZip?: boolean;
  zipProgress?: number; // 0-100 percentage
  onDownload: () => void;
  onDownloadZip?: () => void;
  cacheReady?: boolean; // Whether the Drive cache is populated
}

type Order = 'asc' | 'desc';

const FKCOFilterResults: React.FC<FKCOFilterResultsProps> = ({
  result,
  isLoading = false,
  isDownloading = false,
  isDownloadingZip = false,
  zipProgress,
  onDownload,
  onDownloadZip,
  cacheReady = false,
}) => {
  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Sorting state
  const [orderBy, setOrderBy] = useState<keyof COFilteredRecord>('fecha');
  const [order, setOrder] = useState<Order>('desc');

  // Search state
  const [searchTerm, setSearchTerm] = useState('');

  // Format currency
  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Handle sort
  const handleRequestSort = (property: keyof COFilteredRecord) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  // Filter and sort data
  const filteredAndSortedRecords = useMemo(() => {
    if (!result?.records) return [];

    let filtered = result.records;

    // Apply search filter
    if (searchTerm) {
      const lowerSearch = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (record) =>
          record.codigo_operacion?.toLowerCase().includes(lowerSearch) ||
          record.nit?.toLowerCase().includes(lowerSearch) ||
          record.numero_factura?.toLowerCase().includes(lowerSearch)
      );
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return order === 'asc' ? aValue - bValue : bValue - aValue;
      }

      const aStr = String(aValue);
      const bStr = String(bValue);
      return order === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
    });

    return filtered;
  }, [result?.records, searchTerm, orderBy, order]);

  // Handle pagination
  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Get paginated data
  const paginatedRecords = filteredAndSortedRecords.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Shorten sheet name
  const shortenSheetName = (name: string | undefined) => {
    if (!name) return '-';
    if (name.includes('Costos Fijos')) return 'Costos Fijos';
    if (name.includes('mandato')) return 'Mandato';
    return name;
  };

  // Loading state
  if (isLoading) {
    return (
      <Card elevation={2}>
        <CardContent>
          <Stack spacing={2} alignItems="center" py={4}>
            <CircularProgress size={48} />
            <Typography variant="h6">Consultando datos...</Typography>
            <Typography variant="body2" color="text.secondary">
              Descargando y filtrando el archivo de Google Drive
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

  // Error state
  if (!result.success) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {result.message}
      </Alert>
    );
  }

  // Empty results
  if (result.total_records === 0) {
    return (
      <Card elevation={2}>
        <CardContent>
          <Alert severity="info">
            <Typography variant="body1" fontWeight={500}>
              No se encontraron registros
            </Typography>
            <Typography variant="body2">
              No hay registros que coincidan con los filtros especificados. Intente con otros
              criterios de búsqueda.
            </Typography>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card elevation={3}>
      <CardContent>
        <Stack spacing={3}>
          {/* Success Header */}
          <Box display="flex" alignItems="center" gap={2}>
            <CheckIcon color="success" sx={{ fontSize: 40 }} />
            <Box flex={1}>
              <Typography variant="h5" fontWeight={600}>
                Resultados de Consulta
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {result.message}
              </Typography>
            </Box>
          </Box>

          <Divider />

          {/* Summary Stats */}
          <Box display="flex" gap={2} flexWrap="wrap">
            <Paper variant="outlined" sx={{ p: 2, minWidth: 120, textAlign: 'center' }}>
              <Typography variant="h4" color="primary.main" fontWeight={700}>
                {result.total_records}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Registros Encontrados
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, minWidth: 120, textAlign: 'center' }}>
              <Typography variant="h4" color="info.main" fontWeight={700}>
                {result.sheets_searched.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Hojas Consultadas
              </Typography>
            </Paper>
          </Box>

          {/* Filters Applied */}
          {Object.keys(result.filters_applied).length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Filtros Aplicados:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {Object.entries(result.filters_applied).map(([key, value]) => (
                  <Chip
                    key={key}
                    label={`${key}: ${value}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Data Table */}
          <Box>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
              <Box display="flex" alignItems="center" gap={1}>
                <TableIcon color="primary" />
                <Typography variant="subtitle1" fontWeight={600}>
                  Datos Encontrados
                </Typography>
              </Box>
              <TextField
                size="small"
                placeholder="Buscar en resultados..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(0);
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                sx={{ width: 250 }}
              />
            </Box>

            <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 450 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>
                      <TableSortLabel
                        active={orderBy === 'codigo_operacion'}
                        direction={orderBy === 'codigo_operacion' ? order : 'asc'}
                        onClick={() => handleRequestSort('codigo_operacion')}
                      >
                        Operación
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={orderBy === 'fecha'}
                        direction={orderBy === 'fecha' ? order : 'asc'}
                        onClick={() => handleRequestSort('fecha')}
                      >
                        Fecha
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={orderBy === 'numero_factura'}
                        direction={orderBy === 'numero_factura' ? order : 'asc'}
                        onClick={() => handleRequestSort('numero_factura')}
                      >
                        # Factura
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={orderBy === 'nit'}
                        direction={orderBy === 'nit' ? order : 'asc'}
                        onClick={() => handleRequestSort('nit')}
                      >
                        NIT
                      </TableSortLabel>
                    </TableCell>
                    <TableCell align="right">Costos Fijos</TableCell>
                    <TableCell align="right">Int. Corriente</TableCell>
                    <TableCell align="right">Valor Neto</TableCell>
                    <TableCell align="right">Otros</TableCell>
                    <TableCell>Hoja</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedRecords.map((record, index) => (
                    <TableRow key={index} hover>
                      <TableCell sx={{ fontSize: '0.85rem' }}>
                        {record.codigo_operacion || '-'}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.85rem' }}>{record.fecha || '-'}</TableCell>
                      <TableCell sx={{ fontSize: '0.85rem' }}>
                        {record.numero_factura || '-'}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.85rem' }}>{record.nit || '-'}</TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.85rem' }}>
                        {formatCurrency(record.valor_costos_fijos)}
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.85rem' }}>
                        {formatCurrency(record.int_corriente)}
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.85rem' }}>
                        {formatCurrency(record.valor_neto)}
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.85rem' }}>
                        {formatCurrency(record.otros_valor)}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.85rem' }}>
                        <Chip
                          label={shortenSheetName(record.hoja_origen)}
                          size="small"
                          variant="outlined"
                          color={record.hoja_origen?.includes('Costos') ? 'primary' : 'secondary'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={filteredAndSortedRecords.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
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
                    Descargando {result?.total_records || 0} archivos PDF desde Google Drive.
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
                disabled={isDownloading || isDownloadingZip || !cacheReady}
                fullWidth
                sx={{ height: 56 }}
              >
                {isDownloadingZip ? 'Generando ZIP...' : 'Descargar con PDFs (ZIP)'}
              </Button>
            )}
          </Stack>

          {/* Cache warning message - show when cache is not ready */}
          {onDownloadZip && !cacheReady && !isDownloadingZip && (
            <Alert severity="warning" variant="outlined">
              <Typography variant="body2">
                <strong>Cache no configurado:</strong> Para descargar ZIPs con PDFs, primero debe cargar los
                archivos y ejecutar "Optimizar Cache" en la pestaña "Cargar Archivos".
              </Typography>
            </Alert>
          )}

          {/* ZIP info message - only show when cache is ready and not downloading */}
          {onDownloadZip && cacheReady && !isDownloadingZip && (
            <Alert severity="info" variant="outlined">
              <Typography variant="body2">
                <strong>Descargar con PDFs:</strong> Genera un archivo ZIP con el reporte Excel y los archivos PDF de
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

export default FKCOFilterResults;
