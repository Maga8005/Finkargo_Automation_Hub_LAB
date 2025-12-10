/**
 * FKBrokerForm - Form component for creating and editing brokers
 * Uses react-hook-form with Material-UI components
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Box,
  TextField,
  Button,
  MenuItem,
  Grid,
  CircularProgress,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  FormHelperText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';

import type {
  Broker,
  BrokerFormData,
  BrokerCreateRequest,
  BrokerUpdateRequest,
  MasterBrokerOption,
  TipoBroker,
  EstadoBroker,
  BrokerContractData,
} from '../../types/alianzas';
import {
  TIPO_BROKER_LABELS,
  ESTADO_BROKER_LABELS,
  DEFAULT_BROKER_FORM_VALUES,
} from '../../types/alianzas';
import FKContractUpload from './FKContractUpload';

interface FKBrokerFormProps {
  broker?: Broker | null;
  masterBrokerOptions: MasterBrokerOption[];
  onSubmit: (data: BrokerCreateRequest | BrokerUpdateRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const FKBrokerForm: React.FC<FKBrokerFormProps> = ({
  broker,
  masterBrokerOptions,
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const isEditing = !!broker;
  const [contractUploadExpanded, setContractUploadExpanded] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  const {
    control,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<BrokerFormData>({
    defaultValues: DEFAULT_BROKER_FORM_VALUES,
  });

  /**
   * Handle extracted contract data
   */
  const handleContractExtracted = useCallback((data: BrokerContractData) => {
    // Map extracted data to form fields
    if (data.porcentaje_comision_apertura !== null && data.porcentaje_comision_apertura !== undefined) {
      setValue('porcentaje_apertura', data.porcentaje_comision_apertura.toString());
    }
    if (data.porcentaje_comision_operativa !== null && data.porcentaje_comision_operativa !== undefined) {
      setValue('porcentaje_operativa', data.porcentaje_comision_operativa.toString());
    }
    if (data.cuenta_bancaria) {
      setValue('cuenta_bancaria', data.cuenta_bancaria);
    }
    if (data.banco) {
      setValue('banco', data.banco);
    }
    if (data.rfc_broker) {
      setValue('rfc', data.rfc_broker);
    }
    if (data.fecha_contrato) {
      setValue('fecha_contrato', data.fecha_contrato);
    }

    // Collapse the accordion and show success message
    setContractUploadExpanded(false);
    setSnackbarMessage('Datos del contrato aplicados al formulario');
    setSnackbarOpen(true);
  }, [setValue]);

  /**
   * Handle contract extraction error
   */
  const handleContractError = useCallback((error: string) => {
    setSnackbarMessage(`Error: ${error}`);
    setSnackbarOpen(true);
  }, []);

  // Watch tipo_broker to conditionally show master_broker_id field
  const tipoBroker = watch('tipo_broker');

  // Determine if master_broker_id field should be shown
  const showMasterBrokerField = tipoBroker !== 'master_broker';

  // Populate form when editing
  useEffect(() => {
    if (broker) {
      reset({
        nombre: broker.nombre,
        tipo_broker: broker.tipo_broker,
        master_broker_id: broker.master_broker_id || '',
        porcentaje_apertura: broker.porcentaje_apertura?.toString() || '',
        porcentaje_operativa: broker.porcentaje_operativa?.toString() || '',
        cuenta_bancaria: broker.cuenta_bancaria || '',
        banco: broker.banco || '',
        rfc: broker.rfc || '',
        fecha_contrato: broker.fecha_contrato || '',
        vigencia_contrato: broker.vigencia_contrato || '',
        estado: broker.estado,
        link_expediente: broker.link_expediente || '',
        notas: broker.notas || '',
      });
    } else {
      reset(DEFAULT_BROKER_FORM_VALUES);
    }
  }, [broker, reset]);

  const processFormData = (data: BrokerFormData): BrokerCreateRequest | BrokerUpdateRequest => {
    const result: BrokerCreateRequest = {
      nombre: data.nombre.trim(),
      tipo_broker: data.tipo_broker as TipoBroker,
      master_broker_id: data.master_broker_id || null,
      porcentaje_apertura: data.porcentaje_apertura ? parseFloat(data.porcentaje_apertura) : null,
      porcentaje_operativa: data.porcentaje_operativa ? parseFloat(data.porcentaje_operativa) : null,
      cuenta_bancaria: data.cuenta_bancaria || null,
      banco: data.banco || null,
      rfc: data.rfc || null,
      fecha_contrato: data.fecha_contrato || null,
      vigencia_contrato: data.vigencia_contrato || null,
      estado: data.estado as EstadoBroker,
      link_expediente: data.link_expediente || null,
      notas: data.notas || null,
    };

    // If master_broker type, ensure master_broker_id is null
    if (result.tipo_broker === 'master_broker') {
      result.master_broker_id = null;
    }

    return result;
  };

  const onFormSubmit = async (data: BrokerFormData) => {
    const processedData = processFormData(data);
    await onSubmit(processedData);
  };

  return (
    <Box component="form" onSubmit={handleSubmit(onFormSubmit)} sx={{ mt: 2 }}>
      {/* Contract Import Section */}
      {!isEditing && (
        <Accordion
          expanded={contractUploadExpanded}
          onChange={(_, expanded) => setContractUploadExpanded(expanded)}
          sx={{ mb: 3 }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <UploadIcon color="primary" />
              <Typography>Importar desde Contrato</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Sube el contrato del broker (PDF o DOCX) para extraer automáticamente
              los datos comerciales como comisiones, información bancaria y fechas.
            </Typography>
            <FKContractUpload
              onExtracted={handleContractExtracted}
              onError={handleContractError}
              disabled={loading || isSubmitting}
            />
          </AccordionDetails>
        </Accordion>
      )}

      <Grid container spacing={3}>
        {/* Nombre */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="nombre"
            control={control}
            rules={{
              required: 'El nombre es requerido',
              minLength: { value: 1, message: 'El nombre no puede estar vacío' },
              maxLength: { value: 255, message: 'El nombre no puede exceder 255 caracteres' },
            }}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Nombre del Broker"
                error={!!errors.nombre}
                helperText={errors.nombre?.message}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Tipo Broker */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="tipo_broker"
            control={control}
            rules={{ required: 'El tipo de broker es requerido' }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.tipo_broker}>
                <InputLabel>Tipo de Broker</InputLabel>
                <Select
                  {...field}
                  label="Tipo de Broker"
                  disabled={loading || isSubmitting}
                >
                  {Object.entries(TIPO_BROKER_LABELS).map(([value, label]) => (
                    <MenuItem key={value} value={value}>
                      {label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.tipo_broker && (
                  <FormHelperText>{errors.tipo_broker.message}</FormHelperText>
                )}
              </FormControl>
            )}
          />
        </Grid>

        {/* Master Broker (conditional) */}
        {showMasterBrokerField && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Controller
              name="master_broker_id"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Master Broker (opcional)</InputLabel>
                  <Select
                    {...field}
                    label="Master Broker (opcional)"
                    disabled={loading || isSubmitting}
                  >
                    <MenuItem value="">
                      <em>Ninguno</em>
                    </MenuItem>
                    {masterBrokerOptions.map((mb) => (
                      <MenuItem key={mb.id} value={mb.id}>
                        {mb.nombre}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
          </Grid>
        )}

        {/* Estado */}
        <Grid size={{ xs: 12, md: showMasterBrokerField ? 6 : 12 }}>
          <Controller
            name="estado"
            control={control}
            rules={{ required: 'El estado es requerido' }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.estado}>
                <InputLabel>Estado</InputLabel>
                <Select
                  {...field}
                  label="Estado"
                  disabled={loading || isSubmitting}
                >
                  {Object.entries(ESTADO_BROKER_LABELS).map(([value, label]) => (
                    <MenuItem key={value} value={value}>
                      {label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.estado && (
                  <FormHelperText>{errors.estado.message}</FormHelperText>
                )}
              </FormControl>
            )}
          />
        </Grid>

        {/* Porcentaje Apertura */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="porcentaje_apertura"
            control={control}
            rules={{
              validate: (value) => {
                if (value === '') return true;
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
                label="% Comisión Apertura"
                type="number"
                inputProps={{ step: '0.01', min: 0, max: 100 }}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                error={!!errors.porcentaje_apertura}
                helperText={errors.porcentaje_apertura?.message || 'Ej: 60.00 para 60%'}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Porcentaje Operativa */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="porcentaje_operativa"
            control={control}
            rules={{
              validate: (value) => {
                if (value === '') return true;
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
                label="% Comisión Operativa"
                type="number"
                inputProps={{ step: '0.001', min: 0, max: 100 }}
                InputProps={{
                  endAdornment: <InputAdornment position="end">%</InputAdornment>,
                }}
                error={!!errors.porcentaje_operativa}
                helperText={errors.porcentaje_operativa?.message || 'Ej: 0.100 para 0.10%'}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Banco */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="banco"
            control={control}
            rules={{ maxLength: { value: 100, message: 'Máximo 100 caracteres' } }}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Banco"
                error={!!errors.banco}
                helperText={errors.banco?.message}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Cuenta Bancaria */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="cuenta_bancaria"
            control={control}
            rules={{ maxLength: { value: 50, message: 'Máximo 50 caracteres' } }}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Cuenta Bancaria"
                error={!!errors.cuenta_bancaria}
                helperText={errors.cuenta_bancaria?.message}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* RFC */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Controller
            name="rfc"
            control={control}
            rules={{ maxLength: { value: 20, message: 'Máximo 20 caracteres' } }}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="RFC"
                placeholder="XAXX010101000"
                error={!!errors.rfc}
                helperText={errors.rfc?.message || 'Identificación fiscal mexicana'}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Fecha Contrato */}
        <Grid size={{ xs: 12, md: 3 }}>
          <Controller
            name="fecha_contrato"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Fecha Contrato"
                type="date"
                InputLabelProps={{ shrink: true }}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Vigencia Contrato */}
        <Grid size={{ xs: 12, md: 3 }}>
          <Controller
            name="vigencia_contrato"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Vigencia Contrato"
                type="date"
                InputLabelProps={{ shrink: true }}
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Link Expediente */}
        <Grid size={{ xs: 12 }}>
          <Controller
            name="link_expediente"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Link Expediente"
                placeholder="https://drive.google.com/..."
                helperText="URL a la carpeta de documentación del broker"
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

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
                rows={3}
                placeholder="Notas adicionales sobre el broker..."
                disabled={loading || isSubmitting}
              />
            )}
          />
        </Grid>

        {/* Action Buttons */}
        <Grid size={{ xs: 12 }}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
            <Button
              variant="outlined"
              startIcon={<CancelIcon />}
              onClick={onCancel}
              disabled={loading || isSubmitting}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={loading || isSubmitting ? <CircularProgress size={20} /> : <SaveIcon />}
              disabled={loading || isSubmitting}
            >
              {loading || isSubmitting
                ? 'Guardando...'
                : isEditing
                ? 'Actualizar Broker'
                : 'Crear Broker'}
            </Button>
          </Box>
        </Grid>
      </Grid>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarMessage.startsWith('Error') ? 'error' : 'success'}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default FKBrokerForm;
