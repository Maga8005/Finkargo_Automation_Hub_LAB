/**
 * FKPagaLocalCOApprovedContracts - Approved contracts view for Paga Local Colombia
 * Displays all approved Paga Local CO contracts with filtering and download capabilities
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
import { exportPagaLocalContractsToExcel } from '../../utils/excelExport';
import type { ContractGeneration, OperationsSortOrder, OperationsFilterParams } from '../../types/legal';
import { exportPagaLocalContractsToPDF } from '../../utils/pdfExport';

// Paga Local Colombia contract types
const PAGA_LOCAL_CO_TYPES = [
  'pl_co_credito_aval_pj',
  'pl_co_mandato_pj',
  'pl_co_credito_aval_pn',
  'pl_co_mandato_pn',
  'pl_co_credito_no_aval',
  'pl_co_mandato_no_aval',
  'pl_co_mandato_im',
  'pl_co_solicitud_desembolso',
  'pl_co_dian_mandato_im',
];

// Contract type labels for display
const CONTRACT_TYPE_LABELS: Record<string, { label: string; color: 'primary' | 'secondary' | 'success' | 'warning' | 'info' | 'error' }> = {
  pl_co_credito_aval_pj: { label: 'Crédito Aval PJ', color: 'primary' },
  pl_co_mandato_pj: { label: 'Mandato PJ', color: 'primary' },
  pl_co_credito_aval_pn: { label: 'Crédito Aval PN', color: 'secondary' },
  pl_co_mandato_pn: { label: 'Mandato PN', color: 'secondary' },
  pl_co_credito_no_aval: { label: 'Crédito No Aval', color: 'warning' },
  pl_co_mandato_no_aval: { label: 'Mandato No Aval', color: 'warning' },
  pl_co_mandato_im: { label: 'Mandato (IM)', color: 'info' },
  pl_co_solicitud_desembolso: { label: 'Solicitud Desembolso', color: 'success' },
  pl_co_dian_mandato_im: { label: 'DIAN Mandato (IM)', color: 'error' },
};

// Mapping of frontend sort field names to backend database fields
const SORT_FIELD_MAP: Record<string, string> = {
  'contract_id': 'contract_id',
  'contract_type': 'contract_type',
  'nombre_importador': 'data_snapshot->nombre_importador',
  'client_nit': 'client_nit',
  'cupo_plataforma': 'data_snapshot->cupo_plataforma',
  'reviewed_at': 'reviewed_at',
};

const FKPagaLocalCOApprovedContracts: React.FC = () => {
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

      // Get all approved contracts and filter by Paga Local CO types
      const allContracts = await operationsService.getApprovedContracts(
        {
          ...filters,
          contract_types: filters.contract_types?.length
            ? filters.contract_types.filter((t) => PAGA_LOCAL_CO_TYPES.includes(t))
            : PAGA_LOCAL_CO_TYPES,
        },
        backendSortField,
        sortOrder
      );

      // Filter to only Paga Local CO contracts
      const pagaLocalContracts = allContracts.filter((c) =>
        PAGA_LOCAL_CO_TYPES.includes(c.contract_type)
      );

      setContracts(pagaLocalContracts);
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
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
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

  const handleExportExcel = () => {
    if (contracts.length === 0) return;
    exportPagaLocalContractsToExcel(contracts);
  };

  const handleDownloadPDF = async (contract: ContractGeneration) => {
    if (!contract.approved_document_url) {
      alert('No hay PDF disponible para este contrato');
      return;
    }

    try {
      setDownloadingId(contract.id);

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
      exportPagaLocalContractsToPDF(contracts);
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


  const getContractTypeBadge = (contractType: string) => {
    const config = CONTRACT_TYPE_LABELS[contractType];
    if (config) {
      return config;
    }
    return { label: contractType, color: 'info' as const };
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
        No hay contratos Paga Local Colombia aprobados disponibles para descarga.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Contratos Paga Local CO Aprobados ({contracts.length})
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
          <Tooltip title={contracts.length === 0 ? 'No hay contratos para exportar' : 'Exportar contratos visibles a Excel'}>
            <span>
              <Button
                variant="outlined"
                size="small"
                onClick={handleExportExcel}
                disabled={contracts.length === 0}
                startIcon={<FileDownloadIcon />}
                sx={{ textTransform: 'none' }}
                color="success"
              >
                Exportar Excel
              </Button>
            </span>
          </Tooltip>
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
                Tipo de Documento
              </FormLabel>
              <FormGroup row sx={{ flexWrap: 'wrap', gap: 1 }}>
                {PAGA_LOCAL_CO_TYPES.map((type) => {
                  const badge = getContractTypeBadge(type);
                  return (
                    <FormControlLabel
                      key={type}
                      control={
                        <Checkbox
                          checked={filters.contract_types?.includes(type) || false}
                          onChange={(e) => handleContractTypeChange(type, e.target.checked)}
                          size="small"
                        />
                      }
                      label={<Chip label={badge.label} color={badge.color} size="small" />}
                    />
                  );
                })}
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

            {/* Date Filters Row */}
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
                    const badge = getContractTypeBadge(contract.contract_type);
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
            <strong>Instrucciones:</strong> Haga clic en el ícono <PdfIcon fontSize="small" sx={{ verticalAlign: 'middle' }} /> para descargar el PDF aprobado del documento. Estos documentos están listos para ser enviados al cliente.
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default FKPagaLocalCOApprovedContracts;
