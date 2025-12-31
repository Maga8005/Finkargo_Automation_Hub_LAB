/**
 * FKDiscrepancyValidationItem - Individual discrepancy item with validation controls
 * Allows mesa de control users to validate discrepancies with reasons and comments
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Collapse,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import type {
  CrossValidationResultWithValidation,
  DiscrepancyValidationReason,
  DiscrepancyValidationRequest,
} from '../../types/risk';
import {
  DISCREPANCY_SEVERITY_CONFIG,
  VALIDATION_TYPE_LABELS,
  DISCREPANCY_VALIDATION_REASON_CONFIG,
} from '../../types/risk';

interface FKDiscrepancyValidationItemProps {
  result: CrossValidationResultWithValidation;
  canValidate: boolean;
  onValidate: (resultId: string, request: DiscrepancyValidationRequest) => Promise<void>;
  onRemoveValidation: (resultId: string) => Promise<void>;
}

const VALIDATION_REASONS: DiscrepancyValidationReason[] = [
  'manual_validation',
  'email_verification',
  'loading_error',
  'client_justification',
];

export const FKDiscrepancyValidationItem: React.FC<FKDiscrepancyValidationItemProps> = ({
  result,
  canValidate,
  onValidate,
  onRemoveValidation,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [reason, setReason] = useState<DiscrepancyValidationReason | ''>('');
  const [comments, setComments] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValidated = result.validation?.is_validated ?? false;
  const severityConfig = result.severity ? DISCREPANCY_SEVERITY_CONFIG[result.severity] : null;
  const validationTypeLabel = VALIDATION_TYPE_LABELS[result.validation_type] || result.validation_type;

  const handleValidate = async () => {
    if (!reason) {
      setError('Debe seleccionar una razón de validación');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onValidate(result.id!, {
        is_validated: true,
        validation_reason: reason,
        comments: comments || undefined,
      });
      setExpanded(false);
      setReason('');
      setComments('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al validar');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveValidation = async () => {
    setLoading(true);
    setError(null);

    try {
      await onRemoveValidation(result.id!);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al quitar validación');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString('es-CO', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  };

  return (
    <Paper
      elevation={1}
      sx={{
        mb: 1,
        border: isValidated ? '1px solid #2CA14D' : '1px solid #E5E7EB',
        bgcolor: isValidated ? '#F0FDF4' : 'background.paper',
      }}
    >
      {/* Header Row */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          p: 1.5,
          cursor: canValidate && !isValidated ? 'pointer' : 'default',
        }}
        onClick={() => canValidate && !isValidated && setExpanded(!expanded)}
      >
        {/* Validation Status Icon */}
        <Box sx={{ mr: 1.5 }}>
          {isValidated ? (
            <Tooltip title="Validado por Mesa de Control">
              <CheckCircleIcon sx={{ color: '#2CA14D', fontSize: 24 }} />
            </Tooltip>
          ) : (
            <Tooltip title="Pendiente de validación">
              <WarningIcon sx={{ color: severityConfig?.textColor || '#B86E00', fontSize: 24 }} />
            </Tooltip>
          )}
        </Box>

        {/* Validation Type */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {validationTypeLabel}
          </Typography>
          {result.field_compared && (
            <Typography variant="caption" color="text.secondary">
              Campo: {result.field_compared}
            </Typography>
          )}
        </Box>

        {/* Severity Chip */}
        {severityConfig && (
          <Chip
            label={severityConfig.label}
            size="small"
            sx={{
              bgcolor: severityConfig.bgColor,
              color: severityConfig.textColor,
              fontWeight: 500,
              mr: 1,
            }}
          />
        )}

        {/* Validation Badge (if validated) */}
        {isValidated && result.validation?.validation_reason && (
          <Chip
            label={DISCREPANCY_VALIDATION_REASON_CONFIG[result.validation.validation_reason].label}
            size="small"
            sx={{
              bgcolor: '#E0F7E6',
              color: '#2CA14D',
              fontWeight: 500,
              mr: 1,
            }}
          />
        )}

        {/* Expand Button */}
        {canValidate && (
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        )}
      </Box>

      {/* Description */}
      {result.description && (
        <Box sx={{ px: 1.5, pb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {result.description}
          </Typography>
        </Box>
      )}

      {/* Validation Info (if validated) */}
      {isValidated && result.validation && (
        <Box sx={{ px: 1.5, pb: 1.5 }}>
          <Typography variant="caption" color="text.secondary">
            Validado: {formatDate(result.validation.validated_at)}
            {result.validation.validated_by_name && ` por ${result.validation.validated_by_name}`}
          </Typography>
          {result.validation.comments && (
            <Typography variant="body2" sx={{ mt: 0.5, fontStyle: 'italic' }}>
              "{result.validation.comments}"
            </Typography>
          )}
        </Box>
      )}

      {/* Expandable Validation Form */}
      <Collapse in={expanded}>
        <Box sx={{ p: 2, borderTop: '1px solid #E5E7EB' }}>
          {isValidated ? (
            /* Remove Validation UI */
            <Stack spacing={2}>
              <Typography variant="body2">
                Esta discrepancia ya está validada. ¿Desea quitar la validación?
              </Typography>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleRemoveValidation}
                  disabled={loading}
                  startIcon={loading && <CircularProgress size={16} />}
                >
                  Quitar Validación
                </Button>
                <Button variant="text" onClick={() => setExpanded(false)} disabled={loading}>
                  Cancelar
                </Button>
              </Stack>
            </Stack>
          ) : (
            /* Validation Form */
            <Stack spacing={2}>
              {/* Values Found */}
              {Object.keys(result.values_found).length > 0 && (
                <Box sx={{ p: 1.5, bgcolor: '#F9FAFB', borderRadius: 1 }}>
                  <Typography variant="caption" fontWeight={600} sx={{ mb: 1, display: 'block' }}>
                    Valores encontrados:
                  </Typography>
                  {Object.entries(result.values_found).map(([key, value]) => (
                    <Typography key={key} variant="body2" sx={{ mb: 0.5 }}>
                      <strong>{key}:</strong>{' '}
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </Typography>
                  ))}
                </Box>
              )}

              {/* Validation Reason Select */}
              <FormControl fullWidth size="small" error={!!error && !reason}>
                <InputLabel id={`validation-reason-${result.id}`}>Razón de validación *</InputLabel>
                <Select
                  labelId={`validation-reason-${result.id}`}
                  value={reason}
                  label="Razón de validación *"
                  onChange={(e) => {
                    setReason(e.target.value as DiscrepancyValidationReason);
                    setError(null);
                  }}
                  disabled={loading}
                >
                  {VALIDATION_REASONS.map((r) => (
                    <MenuItem key={r} value={r}>
                      <Box>
                        <Typography variant="body2">
                          {DISCREPANCY_VALIDATION_REASON_CONFIG[r].label}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {DISCREPANCY_VALIDATION_REASON_CONFIG[r].description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Comments */}
              <TextField
                label="Comentarios (opcional)"
                multiline
                rows={2}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                disabled={loading}
                inputProps={{ maxLength: 2000 }}
                helperText={`${comments.length}/2000 caracteres`}
                fullWidth
                size="small"
              />

              {/* Error Message */}
              {error && (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              )}

              {/* Action Buttons */}
              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleValidate}
                  disabled={loading || !reason}
                  startIcon={loading ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                >
                  Guardar Validación
                </Button>
                <Button variant="text" onClick={() => setExpanded(false)} disabled={loading}>
                  Cancelar
                </Button>
              </Stack>
            </Stack>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default FKDiscrepancyValidationItem;
