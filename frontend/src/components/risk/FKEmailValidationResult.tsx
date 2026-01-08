/**
 * FKEmailValidationResult - Displays email domain validation results
 *
 * Shows typosquatting detection results including:
 * - Validation status (validated, suspicious, critical)
 * - Similarity score for typosquatting detection
 * - Detection type (typosquatting, TLD variation, free provider)
 * - Similar domain comparison
 */
import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  HelpOutline,
} from '@mui/icons-material';
import type { EmailValidationResult, ExternalContactValidationStatus } from '../../types/risk';
import { EXTERNAL_CONTACT_VALIDATION_STATUS_CONFIG } from '../../types/risk';

interface FKEmailValidationResultProps {
  validationStatus: ExternalContactValidationStatus;
  validationResult?: EmailValidationResult;
}

const FKEmailValidationResult: React.FC<FKEmailValidationResultProps> = ({
  validationStatus,
  validationResult,
}) => {
  const statusConfig = EXTERNAL_CONTACT_VALIDATION_STATUS_CONFIG[validationStatus];

  // Get icon based on status
  const getStatusIcon = () => {
    switch (validationStatus) {
      case 'validated':
        return <CheckCircle sx={{ color: statusConfig.textColor, fontSize: 20 }} />;
      case 'suspicious':
        return <Warning sx={{ color: statusConfig.textColor, fontSize: 20 }} />;
      case 'critical':
        return <Error sx={{ color: statusConfig.textColor, fontSize: 20 }} />;
      default:
        return <HelpOutline sx={{ color: statusConfig.textColor, fontSize: 20 }} />;
    }
  };

  // Get severity for Alert
  const getAlertSeverity = (): 'success' | 'warning' | 'error' | 'info' => {
    switch (validationStatus) {
      case 'validated':
        return 'success';
      case 'suspicious':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'info';
    }
  };

  // Get detection type label in Spanish
  const getDetectionTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      typosquatting: 'Typosquatting Detectado',
      tld_variation: 'Variación de TLD',
      provider_domain: 'Proveedor de Email Gratuito',
      exact_match: 'Coincidencia Exacta',
      no_match: 'Sin Coincidencia',
      suspicious_tld: 'TLD Sospechoso',
      invalid_format: 'Formato Inválido',
      domain_not_found: 'Dominio No Existe',
      young_domain: 'Dominio Reciente',
    };
    return labels[type] || type;
  };

  // Format domain age for display
  const formatDomainAge = (days: number | null | undefined): string => {
    if (days === null || days === undefined) return 'Desconocida';
    if (days < 30) return `${days} días`;
    if (days < 365) return `${Math.floor(days / 30)} meses`;
    const years = Math.floor(days / 365);
    const months = Math.floor((days % 365) / 30);
    if (months > 0) return `${years} años, ${months} meses`;
    return `${years} años`;
  };

  // If pending status, show minimal info
  if (validationStatus === 'pending') {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          p: 1,
          backgroundColor: statusConfig.bgColor,
          borderRadius: 1,
        }}
      >
        <HelpOutline sx={{ color: statusConfig.textColor, fontSize: 18 }} />
        <Typography variant="body2" sx={{ color: statusConfig.textColor }}>
          Pendiente de validación
        </Typography>
      </Box>
    );
  }

  // If no validation result, show status chip only
  if (!validationResult) {
    return (
      <Chip
        icon={getStatusIcon()}
        label={statusConfig.label}
        sx={{
          backgroundColor: statusConfig.bgColor,
          color: statusConfig.textColor,
          fontWeight: 500,
        }}
      />
    );
  }

  const { is_suspicious, similar_domain, similarity_score, detection_type, description, is_free_provider } = validationResult;

  return (
    <Alert
      severity={getAlertSeverity()}
      icon={getStatusIcon()}
      sx={{
        '& .MuiAlert-icon': {
          alignItems: 'center',
        },
      }}
    >
      <AlertTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
        {getDetectionTypeLabel(detection_type)}
        {is_free_provider && (
          <Chip
            label="Email Gratuito"
            size="small"
            sx={{
              fontSize: '0.7rem',
              height: 20,
              backgroundColor: '#FFF4E5',
              color: '#B86E00',
            }}
          />
        )}
      </AlertTitle>

      <Typography variant="body2" sx={{ mb: 1 }}>
        {description}
      </Typography>

      {/* Show similarity info for typosquatting/TLD variation */}
      {is_suspicious && similar_domain && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
          <Chip
            label={`Similar a: ${similar_domain}`}
            size="small"
            variant="outlined"
            sx={{ fontSize: '0.75rem' }}
          />
          {similarity_score > 0 && (
            <Chip
              label={`Similitud: ${Math.round(similarity_score * 100)}%`}
              size="small"
              sx={{
                fontSize: '0.75rem',
                backgroundColor: similarity_score > 0.8 ? '#FFE4E4' : '#FFF4E5',
                color: similarity_score > 0.8 ? '#CC071E' : '#B86E00',
              }}
            />
          )}
        </Box>
      )}

      {/* Show exact match info */}
      {detection_type === 'exact_match' && similar_domain && (
        <Box sx={{ mt: 1 }}>
          <Chip
            icon={<CheckCircle sx={{ fontSize: 16 }} />}
            label={`Verificado: ${similar_domain}`}
            size="small"
            color="success"
            sx={{ fontSize: '0.75rem' }}
          />
        </Box>
      )}

      {/* Show domain age info when available */}
      {validationResult.domain_exists !== undefined && validationResult.domain_exists !== null && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
          {validationResult.domain_exists === false && (
            <Chip
              icon={<Error sx={{ fontSize: 16 }} />}
              label="Dominio No Resuelve (DNS)"
              size="small"
              sx={{
                fontSize: '0.75rem',
                backgroundColor: '#FFE4E4',
                color: '#CC071E',
              }}
            />
          )}
          {validationResult.domain_exists && validationResult.domain_age_days !== undefined && validationResult.domain_age_days !== null && (
            <Chip
              label={`Antigüedad: ${formatDomainAge(validationResult.domain_age_days)}`}
              size="small"
              sx={{
                fontSize: '0.75rem',
                backgroundColor: validationResult.domain_age_days < 90 ? '#FFE4E4' :
                  validationResult.domain_age_days < 365 ? '#FFF4E5' : '#E0F7E6',
                color: validationResult.domain_age_days < 90 ? '#CC071E' :
                  validationResult.domain_age_days < 365 ? '#B86E00' : '#2CA14D',
              }}
            />
          )}
          {validationResult.domain_registrar && (
            <Chip
              label={`Registrador: ${validationResult.domain_registrar}`}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem' }}
            />
          )}
        </Box>
      )}
    </Alert>
  );
};

export default FKEmailValidationResult;
