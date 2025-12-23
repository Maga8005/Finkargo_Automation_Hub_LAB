/**
 * FKRiskEvaluationForm - Trigger evaluation form component
 * NOTE: Evaluation type selection removed - only comprehensive workflow exists
 */
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Assessment } from '@mui/icons-material';
import type { RiskAssessmentRequest } from '../../types/risk';

interface FKRiskEvaluationFormProps {
  onEvaluate: (request: RiskAssessmentRequest) => Promise<void>;
  loading?: boolean;
  error?: string | null;
}

interface FormData {
  client_nit: string;
}

const FKRiskEvaluationForm: React.FC<FKRiskEvaluationFormProps> = ({
  onEvaluate,
  loading = false,
  error = null,
}) => {
  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormData>({
    defaultValues: {
      client_nit: '',
    },
  });

  const onSubmit = async (data: FormData) => {
    await onEvaluate({
      client_nit: data.client_nit.trim(),
    });
    reset();
  };

  // Validate NIT format
  const validateNit = (value: string): string | true => {
    const trimmed = value.trim();
    if (!trimmed) return 'NIT es requerido';
    if (trimmed.length < 5) return 'NIT debe tener al menos 5 caracteres';
    if (trimmed.length > 20) return 'NIT no puede tener más de 20 caracteres';
    return true;
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit(onSubmit)}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {error && (
        <Alert severity="error" sx={{ mb: 1 }}>
          {error}
        </Alert>
      )}

      <Controller
        name="client_nit"
        control={control}
        rules={{
          validate: validateNit,
        }}
        render={({ field }) => (
          <TextField
            {...field}
            label="NIT del Cliente"
            placeholder="Ej: 900.123.456-7"
            fullWidth
            error={!!errors.client_nit}
            helperText={errors.client_nit?.message || 'Ingrese el NIT del cliente a evaluar'}
            disabled={loading}
            InputProps={{
              sx: { borderRadius: 2 },
            }}
          />
        )}
      />

      <Button
        type="submit"
        variant="contained"
        color="primary"
        fullWidth
        disabled={loading}
        startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Assessment />}
        sx={{
          py: 1.5,
          borderRadius: 2,
          fontWeight: 600,
        }}
      >
        {loading ? 'Evaluando...' : 'Iniciar Evaluación'}
      </Button>
    </Box>
  );
};

export default FKRiskEvaluationForm;
