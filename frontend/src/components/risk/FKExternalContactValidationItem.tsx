/**
 * FKExternalContactValidationItem - Individual external contact alert with validation controls
 * Allows mesa de control users to validate external contact alerts with reasons and comments
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
  Email as EmailIcon,
} from '@mui/icons-material';
import type {
  ExternalContactWithValidation,
  DiscrepancyValidationReason,
  ExternalContactValidationRequest,
} from '../../types/risk';
import {
  EXTERNAL_CONTACT_VALIDATION_STATUS_CONFIG,
  DISCREPANCY_VALIDATION_REASON_CONFIG,
} from '../../types/risk';

interface FKExternalContactValidationItemProps {
  contact: ExternalContactWithValidation;
  canValidate: boolean;
  onValidate: (contactId: string, request: ExternalContactValidationRequest) => Promise<void>;
  onRemoveValidation: (contactId: string) => Promise<void>;
}

const VALIDATION_REASONS: DiscrepancyValidationReason[] = [
  'manual_validation',
  'email_verification',
  'loading_error',
  'client_justification',
];

export const FKExternalContactValidationItem: React.FC<FKExternalContactValidationItemProps> = ({
  contact,
  canValidate,
  onValidate,
  onRemoveValidation,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [reason, setReason] = useState<DiscrepancyValidationReason | ''>('');
  const [comments, setComments] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValidated = contact.validation?.is_validated ?? false;
  const isAlertStatus = contact.validation_status === 'suspicious' || contact.validation_status === 'critical';
  const statusConfig = EXTERNAL_CONTACT_VALIDATION_STATUS_CONFIG[contact.validation_status];

  const handleValidate = async () => {
    if (!reason) {
      setError('Debe seleccionar una razón de validación');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onValidate(contact.id, {
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
      await onRemoveValidation(contact.id);
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

  // Only show validation controls for suspicious/critical contacts
  if (!isAlertStatus) {
    return (
      <Paper
        elevation={0}
        sx={{
          mb: 1,
          border: '1px solid #E5E7EB',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', p: 1.5 }}>
          <EmailIcon sx={{ mr: 1.5, color: '#6B7280', fontSize: 20 }} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2">{contact.email}</Typography>
            {contact.sender_name && (
              <Typography variant="caption" color="text.secondary">
                {contact.sender_name}
              </Typography>
            )}
          </Box>
          <Chip
            label={statusConfig.label}
            size="small"
            sx={{
              bgcolor: statusConfig.bgColor,
              color: statusConfig.textColor,
              fontWeight: 500,
            }}
          />
        </Box>
      </Paper>
    );
  }

  return (
    <Paper
      elevation={0}
      sx={{
        mb: 1,
        border: isValidated ? '1px solid #2CA14D' : `1px solid ${statusConfig.textColor}`,
        bgcolor: isValidated ? '#F0FDF4' : statusConfig.bgColor,
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
              <CheckCircleIcon sx={{ color: '#2CA14D', fontSize: 20 }} />
            </Tooltip>
          ) : (
            <Tooltip title="Alerta pendiente de validación">
              <WarningIcon sx={{ color: statusConfig.textColor, fontSize: 20 }} />
            </Tooltip>
          )}
        </Box>

        {/* Email and Sender Name */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {contact.email}
          </Typography>
          {contact.sender_name && (
            <Typography variant="caption" color="text.secondary">
              {contact.sender_name}
            </Typography>
          )}
        </Box>

        {/* Status Chip */}
        <Chip
          label={statusConfig.label}
          size="small"
          sx={{
            bgcolor: statusConfig.bgColor,
            color: statusConfig.textColor,
            fontWeight: 500,
            fontSize: '0.65rem',
            mr: 1,
          }}
        />

        {/* Validation Badge (if validated) */}
        {isValidated && contact.validation?.validation_reason && (
          <Chip
            label={DISCREPANCY_VALIDATION_REASON_CONFIG[contact.validation.validation_reason].label}
            size="small"
            sx={{
              bgcolor: '#E0F7E6',
              color: '#2CA14D',
              fontWeight: 500,
              fontSize: '0.65rem',
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

      {/* Validation Result Details */}
      {contact.validation_result && (
        <Box sx={{ px: 1.5, pb: 1 }}>
          {contact.validation_result.detection_type && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              Tipo: {contact.validation_result.detection_type.replace(/_/g, ' ')}
            </Typography>
          )}
          {contact.validation_result.description && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {contact.validation_result.description}
            </Typography>
          )}
          {contact.validation_result.domain_age_days !== undefined && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              Antigüedad del dominio: {contact.validation_result.domain_age_days} días
            </Typography>
          )}
        </Box>
      )}

      {/* Validation Info (if validated) */}
      {isValidated && contact.validation && (
        <Box sx={{ px: 1.5, pb: 1.5 }}>
          <Typography variant="caption" color="text.secondary">
            Validado: {formatDate(contact.validation.validated_at)}
            {contact.validation.validated_by_name && ` por ${contact.validation.validated_by_name}`}
          </Typography>
          {contact.validation.comments && (
            <Typography variant="caption" sx={{ mt: 0.5, display: 'block', fontStyle: 'italic' }}>
              "{contact.validation.comments}"
            </Typography>
          )}
        </Box>
      )}

      {/* Expandable Validation Form */}
      <Collapse in={expanded}>
        <Box sx={{ p: 2, borderTop: '1px solid #E5E7EB', bgcolor: 'background.paper' }}>
          {isValidated ? (
            /* Remove Validation UI */
            <Stack spacing={2}>
              <Typography variant="body2">
                Esta alerta ya está validada. ¿Desea quitar la validación?
              </Typography>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  onClick={handleRemoveValidation}
                  disabled={loading}
                  startIcon={loading && <CircularProgress size={14} />}
                >
                  Quitar Validación
                </Button>
                <Button variant="text" size="small" onClick={() => setExpanded(false)} disabled={loading}>
                  Cancelar
                </Button>
              </Stack>
            </Stack>
          ) : (
            /* Validation Form */
            <Stack spacing={2}>
              {/* Validation Reason Select */}
              <FormControl fullWidth size="small" error={!!error && !reason}>
                <InputLabel id={`validation-reason-${contact.id}`}>Razón de validación *</InputLabel>
                <Select
                  labelId={`validation-reason-${contact.id}`}
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
                  size="small"
                  onClick={handleValidate}
                  disabled={loading || !reason}
                  startIcon={loading ? <CircularProgress size={14} /> : <CheckCircleIcon />}
                >
                  Guardar Validación
                </Button>
                <Button variant="text" size="small" onClick={() => setExpanded(false)} disabled={loading}>
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

export default FKExternalContactValidationItem;
