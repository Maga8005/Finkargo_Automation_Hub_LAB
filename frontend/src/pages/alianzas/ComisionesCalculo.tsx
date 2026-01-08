/**
 * ComisionesCalculo - Page for monthly commission calculation
 * Allows adding, previewing, and saving broker commissions
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
  CircularProgress,
  TextField,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  FileDownload as ExportIcon,
  Refresh as RefreshIcon,
  CheckCircle as ApproveIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

import FKComisionForm from '../../components/alianzas/FKComisionForm';
import FKComisionesTable from '../../components/alianzas/FKComisionesTable';
import FKResumenBrokers from '../../components/alianzas/FKResumenBrokers';

import { alianzasService } from '../../services/alianzasService';
import type {
  Broker,
  ComisionCalculada,
  ComisionFormData,
  ComisionInput,
  TipoCambioResponse,
  ComisionAprobacionResponse,
} from '../../types/alianzas';

// Month names in Spanish
const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

// Generate year options (current year and 2 previous)
const getYearOptions = (): number[] => {
  const currentYear = new Date().getFullYear();
  return [currentYear - 2, currentYear - 1, currentYear, currentYear + 1];
};

const ComisionesCalculo: React.FC = () => {
  // State - Period selection
  const currentDate = new Date();
  const [periodoMes, setPeriodoMes] = useState(currentDate.getMonth() + 1);
  const [periodoAnio, setPeriodoAnio] = useState(currentDate.getFullYear());
  const [fechaCorte, setFechaCorte] = useState(format(currentDate, 'yyyy-MM-dd'));

  // State - Data
  const [brokers, setBrokers] = useState<Broker[]>([]);
  const [tipoCambio, setTipoCambio] = useState<TipoCambioResponse | null>(null);
  const [comisiones, setComisiones] = useState<ComisionCalculada[]>([]);

  // State - UI
  const [loading, setLoading] = useState(false);
  const [loadingTipoCambio, setLoadingTipoCambio] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [approving, setApproving] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingComision, setEditingComision] = useState<ComisionCalculada | null>(null);
  const [previewResult, setPreviewResult] = useState<ComisionCalculada | null>(null);
  const [confirmSaveOpen, setConfirmSaveOpen] = useState(false);
  const [confirmApproveOpen, setConfirmApproveOpen] = useState(false);

  // State - Notifications
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({ open: false, message: '', severity: 'info' });

  // Load initial data
  useEffect(() => {
    loadBrokers();
    loadTipoCambio();
  }, []);

  // Load brokers
  const loadBrokers = async () => {
    try {
      const data = await alianzasService.getBrokers({ active_only: true });
      setBrokers(data);
    } catch (error) {
      console.error('Error loading brokers:', error);
      showSnackbar('Error al cargar brokers', 'error');
    }
  };

  // Load exchange rate
  const loadTipoCambio = async (fecha?: string) => {
    try {
      setLoadingTipoCambio(true);
      let data: TipoCambioResponse;
      if (fecha) {
        data = await alianzasService.getTipoCambioFecha(fecha);
      } else {
        data = await alianzasService.getTipoCambioActual();
      }
      setTipoCambio(data);
    } catch (error) {
      console.error('Error loading exchange rate:', error);
      showSnackbar('Error al obtener tipo de cambio', 'error');
    } finally {
      setLoadingTipoCambio(false);
    }
  };

  // Show snackbar notification
  const showSnackbar = (
    message: string,
    severity: 'success' | 'error' | 'info' | 'warning' = 'info'
  ) => {
    setSnackbar({ open: true, message, severity });
  };

  // Convert form data to API input
  const formDataToInput = (data: ComisionFormData): ComisionInput => {
    return {
      broker_id: data.broker_id,
      tipo_comision: data.tipo_comision,
      cliente_nombre: data.cliente_nombre || null,
      cliente_nit: data.cliente_nit || null,
      linea_credito: data.linea_credito ? parseFloat(data.linea_credito) : null,
      porcentaje_comision_cliente: data.porcentaje_comision_cliente
        ? parseFloat(data.porcentaje_comision_cliente)
        : null,
      cliente_pago_pct: data.cliente_pago_pct ? parseFloat(data.cliente_pago_pct) : null,
      operaciones_mes: data.operaciones_mes ? parseFloat(data.operaciones_mes) : null,
      periodo_mes: periodoMes,
      periodo_anio: periodoAnio,
      fecha_tipo_cambio: fechaCorte,
      notas: data.notas || null,
    };
  };

  // Handle calculate preview
  const handleCalculatePreview = useCallback(async (data: ComisionFormData) => {
    try {
      setLoading(true);
      const input = formDataToInput(data);
      const result = await alianzasService.calcularComision(input);

      // Add broker name for display
      const broker = brokers.find((b) => b.id === input.broker_id);
      if (broker) {
        result.broker_nombre = broker.nombre;
      }

      setPreviewResult(result);
    } catch (error) {
      console.error('Error calculating preview:', error);
      showSnackbar('Error al calcular preview', 'error');
    } finally {
      setLoading(false);
    }
  }, [brokers, periodoMes, periodoAnio, fechaCorte]);

  // Handle add commission from form
  const handleAddComision = useCallback(async (data: ComisionFormData) => {
    try {
      setLoading(true);
      const input = formDataToInput(data);
      const result = await alianzasService.calcularComision(input);

      // Add broker name for display
      const broker = brokers.find((b) => b.id === input.broker_id);
      if (broker) {
        result.broker_nombre = broker.nombre;
      }

      if (editingComision) {
        // Update existing - replace in list
        setComisiones((prev) =>
          prev.map((c) =>
            (c.id === editingComision.id) ||
            (c.broker_id === editingComision.broker_id &&
              c.cliente_nombre === editingComision.cliente_nombre &&
              c.tipo_comision === editingComision.tipo_comision)
              ? result
              : c
          )
        );
        showSnackbar('Comisión actualizada', 'success');
      } else {
        // Add new
        setComisiones((prev) => [...prev, result]);
        showSnackbar('Comisión agregada', 'success');
      }

      setFormOpen(false);
      setEditingComision(null);
      setPreviewResult(null);
    } catch (error) {
      console.error('Error adding commission:', error);
      showSnackbar('Error al agregar comisión', 'error');
    } finally {
      setLoading(false);
    }
  }, [brokers, editingComision, periodoMes, periodoAnio, fechaCorte]);

  // Handle edit commission
  const handleEditComision = (comision: ComisionCalculada) => {
    setEditingComision(comision);
    setPreviewResult(null);
    setFormOpen(true);
  };

  // Handle delete commission
  const handleDeleteComision = (comision: ComisionCalculada) => {
    setComisiones((prev) =>
      prev.filter(
        (c) =>
          !(
            (c.id && c.id === comision.id) ||
            (c.broker_id === comision.broker_id &&
              c.cliente_nombre === comision.cliente_nombre &&
              c.tipo_comision === comision.tipo_comision)
          )
      )
    );
    showSnackbar('Comisión eliminada', 'info');
  };

  // Handle save all commissions
  const handleSaveComisiones = async () => {
    if (comisiones.length === 0) {
      showSnackbar('No hay comisiones para guardar', 'warning');
      return;
    }

    try {
      setSaving(true);

      // Convert to input format
      const inputs: ComisionInput[] = comisiones.map((c) => ({
        broker_id: c.broker_id,
        tipo_comision: c.tipo_comision,
        cliente_nombre: c.cliente_nombre,
        cliente_nit: c.cliente_nit,
        linea_credito: c.linea_credito,
        porcentaje_comision_cliente: c.porcentaje_comision_cliente,
        cliente_pago_pct: c.cliente_pago_pct,
        operaciones_mes: c.operaciones_mes,
        periodo_mes: periodoMes,
        periodo_anio: periodoAnio,
        fecha_tipo_cambio: fechaCorte,
        notas: c.notas,
      }));

      const response = await alianzasService.calcularComisionesLote({
        comisiones: inputs,
        guardar: true,
      });

      // Update local state with saved data (includes IDs)
      setComisiones(response.comisiones);
      setConfirmSaveOpen(false);
      showSnackbar(
        `${response.comisiones.length} comisiones guardadas exitosamente`,
        'success'
      );
    } catch (error) {
      console.error('Error saving commissions:', error);
      showSnackbar('Error al guardar comisiones', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Handle export to Excel
  const handleExportExcel = async () => {
    // First save commissions if needed
    if (comisiones.length === 0) {
      showSnackbar('No hay comisiones para exportar', 'warning');
      return;
    }

    try {
      setExporting(true);

      // If there are unsaved commissions, save them first
      const hasUnsaved = comisiones.some((c) => !c.id);
      if (hasUnsaved) {
        showSnackbar('Guardando comisiones antes de exportar...', 'info');
        await handleSaveComisiones();
      }

      // Export to Excel
      const blob = await alianzasService.exportarComisionesExcel(periodoMes, periodoAnio);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `comisiones_brokers_${periodoAnio}_${String(periodoMes).padStart(2, '0')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      showSnackbar('Excel exportado exitosamente', 'success');
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      showSnackbar('Error al exportar a Excel', 'error');
    } finally {
      setExporting(false);
    }
  };

  // Handle approve commissions
  const handleApproveComisiones = async () => {
    try {
      setApproving(true);

      // First save if there are unsaved commissions
      const hasUnsaved = comisiones.some((c) => !c.id);
      if (hasUnsaved) {
        showSnackbar('Guardando comisiones antes de aprobar...', 'info');
        await handleSaveComisiones();
      }

      // Approve commissions
      const response: ComisionAprobacionResponse = await alianzasService.aprobarComisiones({
        periodo_mes: periodoMes,
        periodo_anio: periodoAnio,
      });

      setConfirmApproveOpen(false);

      if (response.comisiones_aprobadas > 0) {
        showSnackbar(
          `${response.comisiones_aprobadas} comisiones aprobadas, ${response.pagos_creados} pagos creados`,
          'success'
        );

        // Reload commissions to show updated status
        const listResponse = await alianzasService.listarComisionesPorPeriodo(
          periodoMes,
          periodoAnio
        );
        setComisiones(listResponse.comisiones);
      } else {
        showSnackbar(response.message || 'No hay comisiones pendientes de aprobar', 'warning');
      }
    } catch (error) {
      console.error('Error approving commissions:', error);
      showSnackbar('Error al aprobar comisiones', 'error');
    } finally {
      setApproving(false);
    }
  };

  // Handle update exchange rate
  const handleUpdateTipoCambio = () => {
    loadTipoCambio(fechaCorte);
  };

  // Calculate totals
  const totals = comisiones.reduce(
    (acc, c) => ({
      usd: acc.usd + c.monto_broker_usd,
      mxn: acc.mxn + c.monto_broker_mxn,
    }),
    { usd: 0, mxn: 0 }
  );

  // Format currency
  const formatCurrency = (value: number, currency: 'USD' | 'MXN'): string => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
    }).format(value);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Cálculo de Comisiones - Brokers
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Calcula y registra las comisiones mensuales de los brokers
        </Typography>
      </Box>

      {/* Period Selection & Exchange Rate */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          {/* Period Selection */}
          <Grid size={{ xs: 12, md: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Mes</InputLabel>
              <Select
                value={periodoMes}
                label="Mes"
                onChange={(e) => setPeriodoMes(Number(e.target.value))}
              >
                {MESES.map((mes, idx) => (
                  <MenuItem key={idx} value={idx + 1}>
                    {mes}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid size={{ xs: 12, md: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Año</InputLabel>
              <Select
                value={periodoAnio}
                label="Año"
                onChange={(e) => setPeriodoAnio(Number(e.target.value))}
              >
                {getYearOptions().map((year) => (
                  <MenuItem key={year} value={year}>
                    {year}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid size={{ xs: 12, md: 3 }}>
            <TextField
              fullWidth
              size="small"
              label="Fecha Corte (TC)"
              type="date"
              value={fechaCorte}
              onChange={(e) => setFechaCorte(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Exchange Rate */}
          <Grid size={{ xs: 12, md: 5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Tipo de Cambio USD/MXN
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {loadingTipoCambio ? (
                    <CircularProgress size={20} />
                  ) : tipoCambio ? (
                    <>
                      <Typography variant="h6" fontWeight={600} color="primary.main">
                        ${tipoCambio.tipo_cambio.toFixed(4)}
                      </Typography>
                      <Chip
                        label={tipoCambio.fecha}
                        size="small"
                        variant="outlined"
                      />
                    </>
                  ) : (
                    <Typography color="error">No disponible</Typography>
                  )}
                </Box>
              </Box>
              <Tooltip title="Actualizar tipo de cambio">
                <IconButton
                  onClick={handleUpdateTipoCambio}
                  disabled={loadingTipoCambio}
                  size="small"
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Add Commission Button */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingComision(null);
            setPreviewResult(null);
            setFormOpen(true);
          }}
          disabled={!tipoCambio || brokers.length === 0}
        >
          Agregar Comisión
        </Button>

        <Typography variant="body2" color="text.secondary">
          {comisiones.length} comisiones en lista
        </Typography>
      </Box>

      {/* Commission Table */}
      <Paper sx={{ mb: 3 }}>
        <FKComisionesTable
          comisiones={comisiones}
          onEdit={handleEditComision}
          onDelete={handleDeleteComision}
          loading={loading}
          showActions={true}
        />
      </Paper>

      {/* Summary by Broker */}
      {comisiones.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <FKResumenBrokers
            comisiones={comisiones}
            loading={loading}
          />
        </Paper>
      )}

      {/* Action Buttons */}
      {comisiones.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              startIcon={exporting ? <CircularProgress size={20} /> : <ExportIcon />}
              onClick={handleExportExcel}
              disabled={exporting || saving || approving}
            >
              Exportar Excel
            </Button>
            <Button
              variant="contained"
              color="primary"
              startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
              onClick={() => setConfirmSaveOpen(true)}
              disabled={saving || exporting || approving}
            >
              Guardar Borrador
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={approving ? <CircularProgress size={20} /> : <ApproveIcon />}
              onClick={() => setConfirmApproveOpen(true)}
              disabled={saving || exporting || approving}
            >
              Aprobar Comisiones
            </Button>
          </Box>
        </Paper>
      )}

      {/* Commission Form Dialog */}
      <FKComisionForm
        open={formOpen}
        onClose={() => {
          setFormOpen(false);
          setEditingComision(null);
          setPreviewResult(null);
        }}
        onSubmit={handleAddComision}
        brokers={brokers}
        editingComision={editingComision}
        loading={loading}
        tipoCambio={tipoCambio?.tipo_cambio || 0}
        previewResult={previewResult}
        onCalculatePreview={handleCalculatePreview}
      />

      {/* Confirm Save Dialog */}
      <Dialog open={confirmSaveOpen} onClose={() => setConfirmSaveOpen(false)}>
        <DialogTitle>Confirmar Guardado</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Se guardarán <strong>{comisiones.length}</strong> comisiones para el período{' '}
            <strong>{MESES[periodoMes - 1]} {periodoAnio}</strong>.
          </DialogContentText>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
            <Typography variant="body2">
              Total USD: <strong>{formatCurrency(totals.usd, 'USD')}</strong>
            </Typography>
            <Typography variant="body2">
              Total MXN: <strong>{formatCurrency(totals.mxn, 'MXN')}</strong>
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmSaveOpen(false)} disabled={saving}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleSaveComisiones}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            Confirmar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Confirm Approval Dialog */}
      <Dialog open={confirmApproveOpen} onClose={() => setConfirmApproveOpen(false)}>
        <DialogTitle>Aprobar Comisiones</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Se aprobarán las comisiones calculadas para el período{' '}
            <strong>{MESES[periodoMes - 1]} {periodoAnio}</strong>.
          </DialogContentText>
          <Alert severity="warning" sx={{ mt: 2, mb: 2 }}>
            Esta acción creará registros de pago para cada broker. Las comisiones
            cambiarán de estado "Calculado" a "Aprobado".
          </Alert>
          <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
            <Typography variant="body2">
              <strong>{comisiones.length}</strong> comisiones serán aprobadas
            </Typography>
            <Typography variant="body2">
              Total USD: <strong>{formatCurrency(totals.usd, 'USD')}</strong>
            </Typography>
            <Typography variant="body2">
              Total MXN: <strong>{formatCurrency(totals.mxn, 'MXN')}</strong>
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmApproveOpen(false)} disabled={approving}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleApproveComisiones}
            disabled={approving}
            startIcon={approving ? <CircularProgress size={20} /> : <ApproveIcon />}
          >
            Confirmar Aprobación
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar Notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ComisionesCalculo;
