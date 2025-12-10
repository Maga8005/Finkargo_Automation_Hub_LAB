/**
 * FKComisionForm - Dialog/Modal form for adding/editing commissions
 * Uses react-hook-form with Material-UI components
 */
import React, { useEffect, useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Grid,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormLabel,
  Box,
  Typography,
  InputAdornment,
  CircularProgress,
  Divider,
  Paper,
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  Calculate as CalculateIcon,
} from '@mui/icons-material';

import type {
  Broker,
  ComisionFormData,
  ComisionCalculada,
} from '../../types/alianzas';
import {
  TIPO_COMISION_LABELS,
  DEFAULT_COMISION_FORM_VALUES,
} from '../../types/alianzas';

interface FKComisionFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: ComisionFormData) => void;
  brokers: Broker[];
  editingComision?: ComisionCalculada | null;
  loading?: boolean;
  tipoCambio: number;
  previewResult?: ComisionCalculada | null;
  onCalculatePreview?: (data: ComisionFormData) => void;
}

const FKComisionForm: React.FC<FKComisionFormProps> = ({
  open,
  onClose,
  onSubmit,
  brokers,
  editingComision,
  loading = false,
  tipoCambio,
  previewResult,
  onCalculatePreview,
}) => {
  const isEditing = !!editingComision;

  const {
    control,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ComisionFormData>({
    defaultValues: DEFAULT_COMISION_FORM_VALUES,
  });

  // Watch tipo_comision to show conditional fields
  const tipoComision = watch('tipo_comision');
  const brokerId = watch('broker_id');

  // Get selected broker info
  const selectedBroker = useMemo(() => {
    return brokers.find((b) => b.id === brokerId);
  }, [brokers, brokerId]);

  // Get broker's commission percentage based on type
  const brokerPorcentaje = useMemo(() => {
    if (!selectedBroker) return null;
    return tipoComision === 'apertura'
      ? selectedBroker.porcentaje_apertura
      : selectedBroker.porcentaje_operativa;
  }, [selectedBroker, tipoComision]);

  // Populate form when editing
  useEffect(() => {
    if (editingComision) {
      reset({
        broker_id: editingComision.broker_id,
        tipo_comision: editingComision.tipo_comision,
        cliente_nombre: editingComision.cliente_nombre || '',
        cliente_nit: editingComision.cliente_nit || '',
        linea_credito: editingComision.linea_credito?.toString() || '',
        porcentaje_comision_cliente:
          editingComision.porcentaje_comision_cliente?.toString() || '',
        cliente_pago_pct: editingComision.cliente_pago_pct?.toString() || '100',
        operaciones_mes: editingComision.operaciones_mes?.toString() || '',
        notas: editingComision.notas || '',
      });
    } else {
      reset(DEFAULT_COMISION_FORM_VALUES);
    }
  }, [editingComision, reset, open]);

  // Format currency for display
  const formatCurrency = (value: number, currency: 'USD' | 'MXN'): string => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const onFormSubmit = (data: ComisionFormData) => {
    onSubmit(data);
  };

  const handleCalculatePreview = () => {
    if (onCalculatePreview) {
      const formData = watch();
      onCalculatePreview(formData);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { borderRadius: 2 } }}
    >
      <DialogTitle>
        {isEditing ? 'Editar Comisión' : 'Agregar Comisión'}
      </DialogTitle>
      <form onSubmit={handleSubmit(onFormSubmit)}>
        <DialogContent dividers>
          <Grid container spacing={3}>
            {/* Broker Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Controller
                name="broker_id"
                control={control}
                rules={{ required: 'El broker es requerido' }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.broker_id}>
                    <InputLabel>Broker</InputLabel>
                    <Select
                      {...field}
                      label="Broker"
                      disabled={loading || isSubmitting}
                    >
                      {brokers
                        .filter((b) => b.estado === 'activo')
                        .map((broker) => (
                          <MenuItem key={broker.id} value={broker.id}>
                            {broker.nombre}
                          </MenuItem>
                        ))}
                    </Select>
                    {errors.broker_id && (
                      <FormHelperText>{errors.broker_id.message}</FormHelperText>
                    )}
                    {selectedBroker && (
                      <FormHelperText>
                        % Apertura: {selectedBroker.porcentaje_apertura ?? 'N/A'} |
                        % Operativa: {selectedBroker.porcentaje_operativa ?? 'N/A'}
                      </FormHelperText>
                    )}
                  </FormControl>
                )}
              />
            </Grid>

            {/* Tipo Comision */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Controller
                name="tipo_comision"
                control={control}
                rules={{ required: 'El tipo es requerido' }}
                render={({ field }) => (
                  <FormControl component="fieldset" error={!!errors.tipo_comision}>
                    <FormLabel component="legend">Tipo de Comisión</FormLabel>
                    <RadioGroup {...field} row>
                      {Object.entries(TIPO_COMISION_LABELS).map(([value, label]) => (
                        <FormControlLabel
                          key={value}
                          value={value}
                          control={<Radio />}
                          label={label}
                          disabled={loading || isSubmitting}
                        />
                      ))}
                    </RadioGroup>
                    {errors.tipo_comision && (
                      <FormHelperText>{errors.tipo_comision.message}</FormHelperText>
                    )}
                  </FormControl>
                )}
              />
            </Grid>

            {/* Cliente Info */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Controller
                name="cliente_nombre"
                control={control}
                rules={{ required: 'El nombre del cliente es requerido' }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Nombre del Cliente"
                    error={!!errors.cliente_nombre}
                    helperText={errors.cliente_nombre?.message}
                    disabled={loading || isSubmitting}
                  />
                )}
              />
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Controller
                name="cliente_nit"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="NIT del Cliente"
                    placeholder="Ej: RFC123456ABC"
                    helperText="Identificación fiscal (opcional)"
                    disabled={loading || isSubmitting}
                  />
                )}
              />
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Divider sx={{ my: 1 }} />
            </Grid>

            {/* Apertura-specific fields */}
            {tipoComision === 'apertura' && (
              <>
                <Grid size={{ xs: 12, md: 4 }}>
                  <Controller
                    name="linea_credito"
                    control={control}
                    rules={{
                      required: 'La línea de crédito es requerida',
                      validate: (value) => {
                        const num = parseFloat(value);
                        if (isNaN(num) || num <= 0)
                          return 'Debe ser un número mayor a 0';
                        return true;
                      },
                    }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        fullWidth
                        label="Línea de Crédito"
                        type="number"
                        inputProps={{ step: '0.01', min: 0 }}
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">USD</InputAdornment>
                          ),
                        }}
                        error={!!errors.linea_credito}
                        helperText={
                          errors.linea_credito?.message || 'Monto en dólares'
                        }
                        disabled={loading || isSubmitting}
                      />
                    )}
                  />
                </Grid>

                <Grid size={{ xs: 12, md: 4 }}>
                  <Controller
                    name="porcentaje_comision_cliente"
                    control={control}
                    rules={{
                      required: '% comisión cliente es requerido',
                      validate: (value) => {
                        const num = parseFloat(value);
                        if (isNaN(num)) return 'Debe ser un número válido';
                        if (num < 0 || num > 100) return 'Debe estar entre 0 y 100';
                        return true;
                      },
                    }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        fullWidth
                        label="% Comisión Cliente"
                        type="number"
                        inputProps={{ step: '0.01', min: 0, max: 100 }}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">%</InputAdornment>
                          ),
                        }}
                        error={!!errors.porcentaje_comision_cliente}
                        helperText={
                          errors.porcentaje_comision_cliente?.message ||
                          'Ej: 3.00 para 3%'
                        }
                        disabled={loading || isSubmitting}
                      />
                    )}
                  />
                </Grid>

                <Grid size={{ xs: 12, md: 4 }}>
                  <Controller
                    name="cliente_pago_pct"
                    control={control}
                    rules={{
                      required: '% pagado es requerido',
                      validate: (value) => {
                        const num = parseFloat(value);
                        if (isNaN(num)) return 'Debe ser un número válido';
                        if (num < 0 || num > 100) return 'Debe estar entre 0 y 100';
                        return true;
                      },
                    }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        fullWidth
                        label="% Pagado por Cliente"
                        type="number"
                        inputProps={{ step: '1', min: 0, max: 100 }}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">%</InputAdornment>
                          ),
                        }}
                        error={!!errors.cliente_pago_pct}
                        helperText={
                          errors.cliente_pago_pct?.message ||
                          'Por defecto 100%'
                        }
                        disabled={loading || isSubmitting}
                      />
                    )}
                  />
                </Grid>
              </>
            )}

            {/* Operativa-specific fields */}
            {tipoComision === 'operativa' && (
              <Grid size={{ xs: 12, md: 6 }}>
                <Controller
                  name="operaciones_mes"
                  control={control}
                  rules={{
                    required: 'El monto de operaciones es requerido',
                    validate: (value) => {
                      const num = parseFloat(value);
                      if (isNaN(num) || num <= 0)
                        return 'Debe ser un número mayor a 0';
                      return true;
                    },
                  }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Operaciones del Mes"
                      type="number"
                      inputProps={{ step: '0.01', min: 0 }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">USD</InputAdornment>
                        ),
                      }}
                      error={!!errors.operaciones_mes}
                      helperText={
                        errors.operaciones_mes?.message ||
                        'Desembolsos del mes en dólares'
                      }
                      disabled={loading || isSubmitting}
                    />
                  )}
                />
              </Grid>
            )}

            {/* Notas */}
            <Grid size={{ xs: 12 }}>
              <Controller
                name="notas"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Notas"
                    multiline
                    rows={2}
                    placeholder="Notas adicionales (opcional)"
                    disabled={loading || isSubmitting}
                  />
                )}
              />
            </Grid>

            {/* Preview Section */}
            {onCalculatePreview && (
              <Grid size={{ xs: 12 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<CalculateIcon />}
                    onClick={handleCalculatePreview}
                    disabled={loading || isSubmitting}
                  >
                    Calcular Preview
                  </Button>
                  <Typography variant="body2" color="text.secondary">
                    TC: {formatCurrency(tipoCambio, 'MXN')} por USD
                  </Typography>
                </Box>

                {previewResult && (
                  <Paper
                    variant="outlined"
                    sx={{ p: 2, bgcolor: 'success.50', borderColor: 'success.main' }}
                  >
                    <Typography variant="subtitle2" color="success.dark" gutterBottom>
                      Vista Previa del Cálculo
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Typography variant="caption" color="text.secondary">
                          % Broker
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {previewResult.porcentaje_broker}%
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Typography variant="caption" color="text.secondary">
                          Comisión USD
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {formatCurrency(previewResult.monto_broker_usd, 'USD')}
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Typography variant="caption" color="text.secondary">
                          Comisión MXN
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {formatCurrency(previewResult.monto_broker_mxn, 'MXN')}
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Typography variant="caption" color="text.secondary">
                          Tipo de Cambio
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {previewResult.tipo_cambio}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Paper>
                )}
              </Grid>
            )}

            {/* Broker percentage info */}
            {selectedBroker && brokerPorcentaje !== null && (
              <Grid size={{ xs: 12 }}>
                <Typography variant="body2" color="text.secondary">
                  El broker <strong>{selectedBroker.nombre}</strong> tiene un{' '}
                  {brokerPorcentaje}% de comisión {tipoComision} configurado.
                </Typography>
              </Grid>
            )}
          </Grid>
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button
            onClick={onClose}
            startIcon={<CancelIcon />}
            disabled={loading || isSubmitting}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="contained"
            startIcon={
              loading || isSubmitting ? <CircularProgress size={20} /> : <SaveIcon />
            }
            disabled={loading || isSubmitting}
          >
            {isEditing ? 'Actualizar' : 'Agregar'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default FKComisionForm;
