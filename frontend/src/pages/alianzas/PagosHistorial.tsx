/**
 * PagosHistorial - Payment history page for broker commissions
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Snackbar,
  CircularProgress,
  Chip,
  Grid,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import FKPagosTable from '../../components/alianzas/FKPagosTable';
import { alianzasService } from '../../services/alianzasService';
import type {
  Pago,
  Broker,
  EstadoPago,
  PagoEstadoUpdate,
} from '../../types/alianzas';
import {
  EstadoPago as EstadoPagoEnum,
  ESTADO_PAGO_LABELS,
} from '../../types/alianzas';

const PagosHistorial: React.FC = () => {
  // State
  const [pagos, setPagos] = useState<Pago[]>([]);
  const [brokers, setBrokers] = useState<Broker[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalRecords, setTotalRecords] = useState(0);

  // Filters
  const [selectedBrokerId, setSelectedBrokerId] = useState<string>('');
  const [selectedEstado, setSelectedEstado] = useState<EstadoPago | ''>('');

  // Pagination
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  // Dialog for marking as paid
  const [markPaidDialog, setMarkPaidDialog] = useState(false);
  const [selectedPago, setSelectedPago] = useState<Pago | null>(null);
  const [fechaPago, setFechaPago] = useState<string>('');
  const [comprobante, setComprobante] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Snackbar
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({ open: false, message: '', severity: 'success' });

  // Load brokers on mount
  useEffect(() => {
    const loadBrokers = async () => {
      try {
        const data = await alianzasService.getBrokers({ active_only: false });
        setBrokers(data);
      } catch (err) {
        console.error('Error loading brokers:', err);
      }
    };
    loadBrokers();
  }, []);

  // Load payments
  const loadPagos = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await alianzasService.listarPagos({
        broker_id: selectedBrokerId || undefined,
        estado: selectedEstado || undefined,
        limit: pageSize,
        offset: page * pageSize,
      });

      setPagos(response.pagos);
      setTotalRecords(response.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar pagos';
      setError(message);
      console.error('Error loading payments:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedBrokerId, selectedEstado, page, pageSize]);

  useEffect(() => {
    loadPagos();
  }, [loadPagos]);

  // Handle filter changes
  const handleBrokerChange = (brokerId: string) => {
    setSelectedBrokerId(brokerId);
    setPage(0);
  };

  const handleEstadoChange = (estado: EstadoPago | '') => {
    setSelectedEstado(estado);
    setPage(0);
  };

  const handleClearFilters = () => {
    setSelectedBrokerId('');
    setSelectedEstado('');
    setPage(0);
  };

  // Handle mark as paid dialog
  const handleOpenMarkPaidDialog = (pago: Pago) => {
    setSelectedPago(pago);
    setFechaPago(new Date().toISOString().split('T')[0]);
    setComprobante('');
    setMarkPaidDialog(true);
  };

  const handleCloseMarkPaidDialog = () => {
    setMarkPaidDialog(false);
    setSelectedPago(null);
    setFechaPago('');
    setComprobante('');
  };

  const handleConfirmMarkPaid = async () => {
    if (!selectedPago || !fechaPago) return;

    setSubmitting(true);
    try {
      const updateData: PagoEstadoUpdate = {
        estado: EstadoPagoEnum.PAGADO,
        fecha_pago: fechaPago,
        comprobante_url: comprobante || null,
      };

      await alianzasService.actualizarEstadoPago(selectedPago.id, updateData);

      setSnackbar({
        open: true,
        message: 'Pago marcado como pagado exitosamente',
        severity: 'success',
      });

      handleCloseMarkPaidDialog();
      loadPagos();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al actualizar pago';
      setSnackbar({
        open: true,
        message,
        severity: 'error',
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Handle view receipt
  const handleViewReceipt = (pago: Pago) => {
    if (pago.comprobante_url) {
      window.open(pago.comprobante_url, '_blank');
    }
  };

  // Calculate summary stats
  const totalPendiente = pagos
    .filter((p) => p.estado === 'pendiente')
    .reduce((sum, p) => sum + p.total_usd, 0);
  const totalPagado = pagos
    .filter((p) => p.estado === 'pagado')
    .reduce((sum, p) => sum + p.total_usd, 0);

  return (
    <Box sx={{ p: 3 }}>
      {/* Page Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          Historial de Pagos - Brokers
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gestiona el historial de pagos a brokers por comisiones aprobadas.
        </Typography>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Total Registros
            </Typography>
            <Typography variant="h5" fontWeight={600}>
              {totalRecords}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Pendiente (USD)
            </Typography>
            <Typography variant="h5" fontWeight={600} color="warning.main">
              ${totalPendiente.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Pagado (USD)
            </Typography>
            <Typography variant="h5" fontWeight={600} color="success.main">
              ${totalPagado.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <FilterIcon color="action" />
          <Typography variant="subtitle2" color="text.secondary">
            Filtros:
          </Typography>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Broker</InputLabel>
            <Select
              value={selectedBrokerId}
              label="Broker"
              onChange={(e) => handleBrokerChange(e.target.value)}
            >
              <MenuItem value="">
                <em>Todos los brokers</em>
              </MenuItem>
              {brokers.map((broker) => (
                <MenuItem key={broker.id} value={broker.id}>
                  {broker.nombre}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Estado</InputLabel>
            <Select
              value={selectedEstado}
              label="Estado"
              onChange={(e) => handleEstadoChange(e.target.value as EstadoPago | '')}
            >
              <MenuItem value="">
                <em>Todos</em>
              </MenuItem>
              {Object.entries(ESTADO_PAGO_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            size="small"
            onClick={handleClearFilters}
            disabled={!selectedBrokerId && !selectedEstado}
          >
            Limpiar
          </Button>

          <Box sx={{ flexGrow: 1 }} />

          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadPagos}
            disabled={loading}
          >
            Actualizar
          </Button>
        </Box>
      </Paper>

      {/* Active filters display */}
      {(selectedBrokerId || selectedEstado) && (
        <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {selectedBrokerId && (
            <Chip
              label={`Broker: ${brokers.find((b) => b.id === selectedBrokerId)?.nombre || selectedBrokerId}`}
              onDelete={() => handleBrokerChange('')}
              size="small"
            />
          )}
          {selectedEstado && (
            <Chip
              label={`Estado: ${ESTADO_PAGO_LABELS[selectedEstado]}`}
              onDelete={() => handleEstadoChange('')}
              size="small"
            />
          )}
        </Box>
      )}

      {/* Payments Table */}
      <FKPagosTable
        pagos={pagos}
        loading={loading}
        error={error}
        onMarkAsPaid={handleOpenMarkPaidDialog}
        onViewReceipt={handleViewReceipt}
        totalRecords={totalRecords}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />

      {/* Mark as Paid Dialog */}
      <Dialog open={markPaidDialog} onClose={handleCloseMarkPaidDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Marcar Pago como Pagado</DialogTitle>
        <DialogContent>
          {selectedPago && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Broker: <strong>{selectedPago.broker_nombre}</strong>
                <br />
                Monto: <strong>${selectedPago.total_usd.toFixed(2)} USD</strong> (
                ${selectedPago.total_mxn.toFixed(2)} MXN)
              </Alert>

              <TextField
                label="Fecha de Pago"
                type="date"
                fullWidth
                required
                value={fechaPago}
                onChange={(e) => setFechaPago(e.target.value)}
                slotProps={{
                  inputLabel: { shrink: true },
                }}
                sx={{ mb: 2 }}
              />

              <TextField
                label="URL del Comprobante (opcional)"
                fullWidth
                value={comprobante}
                onChange={(e) => setComprobante(e.target.value)}
                placeholder="https://..."
                helperText="Ingresa la URL del comprobante de pago si lo tienes disponible"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseMarkPaidDialog} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleConfirmMarkPaid}
            disabled={submitting || !fechaPago}
          >
            {submitting ? <CircularProgress size={20} /> : 'Confirmar Pago'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default PagosHistorial;
