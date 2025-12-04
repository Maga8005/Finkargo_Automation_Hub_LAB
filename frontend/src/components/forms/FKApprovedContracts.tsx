/**
 * FK Approved Contracts - Operations view for downloading approved contracts
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  TableSortLabel,
  Collapse,
  TextField,
  Stack,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Badge,
} from '@mui/material';
import {
  PictureAsPdf as PdfIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  FilterList as FilterListIcon,
  Clear as ClearIcon,
  FileDownload as FileDownloadIcon,
} from '@mui/icons-material';
import { operationsService } from '../../services/operationsService';
import type { ContractGeneration, OperationsSortOrder, OperationsFilterParams } from '../../types/legal';
import { exportContractsToPDF } from '../../utils/pdfExport';

// Mapping of frontend sort field names to backend database fields
const SORT_FIELD_MAP: Record<string, string> = {
  'contract_id': 'contract_id',
  'contract_type': 'contract_type',
  'nombre_importador': 'data_snapshot->nombre_importador',
  'client_nit': 'client_nit',
  'cupo_plataforma': 'data_snapshot->cupo_plataforma',
  'reviewed_at': 'reviewed_at',
};

const FKApprovedContracts: React.FC = () => {
  const [contracts, setContracts] = useState<ContractGeneration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<string>('reviewed_at');
  const [sortOrder, setSortOrder] = useState<OperationsSortOrder>('desc');
  const [exportingPDF, setExportingPDF] = useState(false);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<OperationsFilterParams>({});
  const [activeFilterCount, setActiveFilterCount] = useState(0);

  // Count active filters
  const countActiveFilters = useCallback((filterParams: OperationsFilterParams): number => {
    let count = 0;
    if (filterParams.contract_types && filterParams.contract_types.length > 0) count++;
    if (filterParams.client_name && filterParams.client_name.trim()) count++;
    if (filterParams.client_nit && filterParams.client_nit.trim()) count++;
    if (filterParams.date_from) count++;
    if (filterParams.date_to) count++;
    if (filterParams.cupo_min !== undefined) count++;
    if (filterParams.cupo_max !== undefined) count++;
    return count;
  }, []);

  const loadApprovedContracts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Map frontend field name to backend field name
      const backendSortField = SORT_FIELD_MAP[sortBy] || 'reviewed_at';
      const data = await operationsService.getApprovedContracts(
        filters,
        backendSortField,
        sortOrder
      );
      setContracts(data);
    } catch (err) {
      console.error('Error loading approved contracts:', err);
      setError('Error al cargar los contratos aprobados');
    } finally {
      setLoading(false);
    }
  }, [filters, sortBy, sortOrder]);

  useEffect(() => {
    loadApprovedContracts();
  }, [loadApprovedContracts]);

  // Update active filter count when filters change
  useEffect(() => {
    setActiveFilterCount(countActiveFilters(filters));
  }, [filters, countActiveFilters]);

  const handleSortRequest = (column: string) => {
    // If clicking the current sort column, toggle the order
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // If clicking a new column, set it as the sort column with descending order
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  // Filter handlers
  const handleContractTypeChange = (type: string, checked: boolean) => {
    setFilters((prev) => {
      const currentTypes = prev.contract_types || [];
      const newTypes = checked
        ? [...currentTypes, type]
        : currentTypes.filter((t) => t !== type);
      return { ...prev, contract_types: newTypes.length > 0 ? newTypes : undefined };
    });
  };

  const handleClearFilters = () => {
    setFilters({});
    setShowFilters(false);
  };

  const handleDownloadPDF = async (contract: ContractGeneration) => {
    if (!contract.approved_document_url) {
      alert('No hay PDF disponible para este contrato');
      return;
    }

    try {
      setDownloadingId(contract.id);

      // Download via backend API endpoint
      const blob = await operationsService.downloadApprovedContractPdf(contract.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `contrato_${contract.contract_id}_aprobado.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading PDF:', err);
      alert('Error al descargar el PDF');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleExportPDF = async () => {
    try {
      setExportingPDF(true);
      exportContractsToPDF(contracts);
    } catch (err) {
      console.error('Error exporting PDF:', err);
      alert('Error al exportar PDF');
    } finally {
      setExportingPDF(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getContractTypeBadge = (contractType: string) => {
    if (contractType === 'otrosi') {
      return {
        label: 'Otrosí No. 1',
        color: 'warning' as const,
      };
    }
    if (contractType === 'inventario_bodega') {
      return {
        label: 'Inventario Bodega 3ro',
        color: 'success' as const,
      };
    }
    return {
      label: 'Activos',
      color: 'info' as const,
    };
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (contracts.length === 0 && activeFilterCount === 0) {
    return (
      <Alert severity="info" icon={<InfoIcon />}>
        No hay contratos aprobados disponibles para descarga.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Contratos Aprobados ({contracts.length})
          </Typography>
          {activeFilterCount > 0 && (
            <Chip
              label={`${activeFilterCount} filtro${activeFilterCount > 1 ? 's' : ''} activo${activeFilterCount > 1 ? 's' : ''}`}
              size="small"
              color="primary"
              onDelete={handleClearFilters}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Badge badgeContent={activeFilterCount} color="primary">
            <Button
              variant={showFilters ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setShowFilters(!showFilters)}
              startIcon={<FilterListIcon />}
              sx={{ textTransform: 'none' }}
            >
              Filtros
            </Button>
          </Badge>
          <Button
            variant="outlined"
            size="small"
            onClick={loadApprovedContracts}
            sx={{ textTransform: 'none' }}
          >
            Actualizar
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={handleExportPDF}
            disabled={contracts.length === 0 || exportingPDF}
            startIcon={exportingPDF ? <CircularProgress size={16} /> : <FileDownloadIcon />}
            sx={{ textTransform: 'none' }}
          >
            {exportingPDF ? 'Exportando...' : 'Exportar PDF'}
          </Button>
        </Box>
      </Box>

      {/* Filter Panel */}
      <Collapse in={showFilters}>
        <Paper sx={{ p: 3, mb: 3, bgcolor: 'grey.50', border: 1, borderColor: 'divider' }}>
          <Stack spacing={3}>
            {/* Contract Type Filter */}
            <FormControl component="fieldset">
              <FormLabel component="legend" sx={{ fontWeight: 600, mb: 1 }}>
                Tipo de Contrato
              </FormLabel>
              <FormGroup row>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={filters.contract_types?.includes('activos') || false}
                      onChange={(e) => handleContractTypeChange('activos', e.target.checked)}
                    />
                  }
                  label={<Chip label="Activos" color="info" size="small" />}
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={filters.contract_types?.includes('otrosi') || false}
                      onChange={(e) => handleContractTypeChange('otrosi', e.target.checked)}
                    />
                  }
                  label={<Chip label="Otrosí No. 1" color="warning" size="small" />}
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={filters.contract_types?.includes('inventario_bodega') || false}
                      onChange={(e) => handleContractTypeChange('inventario_bodega', e.target.checked)}
                    />
                  }
                  label={<Chip label="Inventario Bodega 3ro" color="success" size="small" />}
                />
              </FormGroup>
            </FormControl>

            {/* Text Filters Row */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <TextField
                label="Nombre del Cliente"
                placeholder="Buscar por nombre..."
                value={filters.client_name || ''}
                onChange={(e) => setFilters({ ...filters, client_name: e.target.value || undefined })}
                size="small"
                sx={{ flex: '1 1 300px' }}
              />
              <TextField
                label="NIT"
                placeholder="Buscar por NIT..."
                value={filters.client_nit || ''}
                onChange={(e) => setFilters({ ...filters, client_nit: e.target.value || undefined })}
                size="small"
                sx={{ flex: '1 1 200px' }}
              />
            </Box>

            {/* Date and Cupo Filters Row */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <TextField
                label="Fecha Desde"
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value || undefined })}
                InputLabelProps={{ shrink: true }}
                size="small"
                sx={{ flex: '1 1 200px' }}
              />
              <TextField
                label="Fecha Hasta"
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => setFilters({ ...filters, date_to: e.target.value || undefined })}
                InputLabelProps={{ shrink: true }}
                size="small"
                sx={{ flex: '1 1 200px' }}
              />
              <TextField
                label="Cupo Mínimo"
                type="number"
                placeholder="0"
                value={filters.cupo_min !== undefined ? filters.cupo_min : ''}
                onChange={(e) => {
                  const val = e.target.value ? parseFloat(e.target.value) : undefined;
                  setFilters({ ...filters, cupo_min: val });
                }}
                size="small"
                sx={{ flex: '1 1 150px' }}
              />
              <TextField
                label="Cupo Máximo"
                type="number"
                placeholder="999999999"
                value={filters.cupo_max !== undefined ? filters.cupo_max : ''}
                onChange={(e) => {
                  const val = e.target.value ? parseFloat(e.target.value) : undefined;
                  setFilters({ ...filters, cupo_max: val });
                }}
                size="small"
                sx={{ flex: '1 1 150px' }}
              />
            </Box>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                size="small"
                onClick={handleClearFilters}
                startIcon={<ClearIcon />}
                sx={{ textTransform: 'none' }}
              >
                Limpiar Filtros
              </Button>
            </Box>
          </Stack>
        </Paper>
      </Collapse>

      {/* Empty state with filters active */}
      {contracts.length === 0 && activeFilterCount > 0 && (
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2">
            No se encontraron contratos con los filtros aplicados. Intenta ajustar los filtros.
          </Typography>
          <Button
            size="small"
            onClick={handleClearFilters}
            sx={{ mt: 1, textTransform: 'none' }}
          >
            Limpiar Filtros
          </Button>
        </Alert>
      )}

      <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
        <Table>
          {/* Theme-aware table header background: light gray in light mode, dark gray in dark mode */}
          <TableHead
            sx={{
              bgcolor: (theme) =>
                theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
            }}
          >
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>
                <TableSortLabel
                  active={sortBy === 'contract_id'}
                  direction={sortBy === 'contract_id' ? sortOrder : 'desc'}
                  onClick={() => handleSortRequest('contract_id')}
                >
                  ID Contrato
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }}>
                <TableSortLabel
                  active={sortBy === 'contract_type'}
                  direction={sortBy === 'contract_type' ? sortOrder : 'desc'}
                  onClick={() => handleSortRequest('contract_type')}
                >
                  Tipo
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }}>
                <TableSortLabel
                  active={sortBy === 'nombre_importador'}
                  direction={sortBy === 'nombre_importador' ? sortOrder : 'desc'}
                  onClick={() => handleSortRequest('nombre_importador')}
                >
                  Cliente
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }}>
                <TableSortLabel
                  active={sortBy === 'client_nit'}
                  direction={sortBy === 'client_nit' ? sortOrder : 'desc'}
                  onClick={() => handleSortRequest('client_nit')}
                >
                  NIT
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }}>
                <TableSortLabel
                  active={sortBy === 'cupo_plataforma'}
                  direction={sortBy === 'cupo_plataforma' ? sortOrder : 'desc'}
                  onClick={() => handleSortRequest('cupo_plataforma')}
                >
                  Cupo Aprobado
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }}>
                <TableSortLabel
                  active={sortBy === 'reviewed_at'}
                  direction={sortBy === 'reviewed_at' ? sortOrder : 'desc'}
                  onClick={() => handleSortRequest('reviewed_at')}
                >
                  Fecha Aprobación
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Estado</TableCell>
              <TableCell align="center" sx={{ fontWeight: 600 }}>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {contracts.map((contract) => (
              <TableRow
                key={contract.id}
                hover
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                    {contract.contract_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  {(() => {
                    const badge = getContractTypeBadge(contract.contract_type || 'activos');
                    return (
                      <Chip
                        label={badge.label}
                        color={badge.color}
                        size="small"
                        sx={{ fontWeight: 500 }}
                      />
                    );
                  })()}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {contract.data_snapshot?.nombre_importador || 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{contract.client_nit}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                    {formatCurrency(contract.data_snapshot?.cupo_plataforma || 0)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {contract.reviewed_at ? formatDate(contract.reviewed_at) : 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    icon={<CheckCircleIcon />}
                    label="Aprobado"
                    color="success"
                    size="small"
                    sx={{ fontWeight: 500 }}
                  />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Descargar PDF aprobado">
                    <span>
                      <IconButton
                        color="primary"
                        onClick={() => handleDownloadPDF(contract)}
                        disabled={!contract.approved_document_url || downloadingId === contract.id}
                        size="small"
                      >
                        {downloadingId === contract.id ? (
                          <CircularProgress size={20} />
                        ) : (
                          <PdfIcon />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>
                  {!contract.approved_document_url && (
                    <Tooltip title="PDF no disponible">
                      <InfoIcon color="disabled" fontSize="small" sx={{ ml: 1 }} />
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2 }}>
        <Alert severity="info" icon={<InfoIcon />}>
          <Typography variant="body2">
            <strong>Instrucciones:</strong> Haga clic en el ícono <PdfIcon fontSize="small" sx={{ verticalAlign: 'middle' }} /> para descargar el PDF aprobado del contrato. Estos documentos están listos para ser enviados al cliente para su firma.
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default FKApprovedContracts;
