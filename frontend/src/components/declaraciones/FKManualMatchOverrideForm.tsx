/**
 * FKManualMatchOverrideForm - Manual Match Override Form Component
 *
 * Form for manually creating/overriding matches between payments and declarations.
 * Includes validation, calculated field previews, and confidence override slider.
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Slider,
  Alert,
  IconButton,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import type { ManualOverrideRequest } from '../../types/matching_results_types';

interface FKManualMatchOverrideFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: ManualOverrideRequest) => Promise<void>;
  prefilledPaymentDate?: string;
  prefilledDeclarationNumber?: string;
}

interface FormData {
  payment_date: string;
  declaration_number: string;
  override_reason: string;
  override_type: 'exact_match' | 'tolerance_exception' | 'customer_name_correction';
  confidence_override: number;
}

const FKManualMatchOverrideForm: React.FC<FKManualMatchOverrideFormProps> = ({
  open,
  onClose,
  onSubmit,
  prefilledPaymentDate,
  prefilledDeclarationNumber,
}) => {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      payment_date: prefilledPaymentDate || '',
      declaration_number: prefilledDeclarationNumber || '',
      override_reason: '',
      override_type: 'tolerance_exception',
      confidence_override: 0.75,
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        payment_date: prefilledPaymentDate || '',
        declaration_number: prefilledDeclarationNumber || '',
        override_reason: '',
        override_type: 'tolerance_exception',
        confidence_override: 0.75,
      });
      setError(null);
    }
  }, [open, prefilledPaymentDate, prefilledDeclarationNumber, reset]);

  const handleFormSubmit = async (data: FormData) => {
    setSubmitting(true);
    setError(null);

    try {
      await onSubmit(data);
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create manual override';
      setError(errorMessage);
      console.error('[FKManualMatchOverrideForm] Error submitting form:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" fontWeight={600}>
            Manual Match Override
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent dividers>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Payment Date */}
            <Controller
              name="payment_date"
              control={control}
              rules={{ required: 'Payment date is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Payment Date"
                  type="date"
                  InputLabelProps={{ shrink: true }}
                  error={!!errors.payment_date}
                  helperText={errors.payment_date?.message}
                  fullWidth
                />
              )}
            />

            {/* Declaration Number */}
            <Controller
              name="declaration_number"
              control={control}
              rules={{ required: 'Declaration number is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Declaration Number"
                  error={!!errors.declaration_number}
                  helperText={errors.declaration_number?.message}
                  fullWidth
                />
              )}
            />

            {/* Override Reason */}
            <Controller
              name="override_reason"
              control={control}
              rules={{
                required: 'Override reason is required',
                minLength: {
                  value: 10,
                  message: 'Reason must be at least 10 characters',
                },
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Override Reason"
                  multiline
                  rows={3}
                  error={!!errors.override_reason}
                  helperText={errors.override_reason?.message || 'Explain why this manual match is needed'}
                  fullWidth
                />
              )}
            />

            {/* Override Type */}
            <FormControl component="fieldset">
              <FormLabel component="legend">Override Type</FormLabel>
              <Controller
                name="override_type"
                control={control}
                render={({ field }) => (
                  <RadioGroup {...field}>
                    <FormControlLabel
                      value="exact_match"
                      control={<Radio />}
                      label="Exact Match Override"
                    />
                    <FormControlLabel
                      value="tolerance_exception"
                      control={<Radio />}
                      label="Tolerance Exception"
                    />
                    <FormControlLabel
                      value="customer_name_correction"
                      control={<Radio />}
                      label="Customer Name Correction"
                    />
                  </RadioGroup>
                )}
              />
            </FormControl>

            {/* Confidence Override Slider */}
            <Box>
              <FormLabel component="legend">Confidence Score Override</FormLabel>
              <Controller
                name="confidence_override"
                control={control}
                render={({ field }) => (
                  <Box sx={{ px: 1 }}>
                    <Slider
                      {...field}
                      min={0.5}
                      max={1.0}
                      step={0.05}
                      marks={[
                        { value: 0.5, label: '50%' },
                        { value: 0.7, label: '70%' },
                        { value: 0.95, label: '95%' },
                        { value: 1.0, label: '100%' },
                      ]}
                      valueLabelDisplay="on"
                      valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                    />
                  </Box>
                )}
              />
              <Typography variant="caption" color="text.secondary">
                Set the confidence score for this manual match (0.50 = Possible, 0.70 = Good, 0.95 = Perfect)
              </Typography>
            </Box>
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={onClose} color="inherit" disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" color="primary" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create Manual Match'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default FKManualMatchOverrideForm;
