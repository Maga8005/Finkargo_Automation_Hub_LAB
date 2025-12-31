/**
 * FKVerificationStatusCard - Binary pass/fail verification status display
 *
 * Displays binary verification status (PASS or REQUIRES MANUAL VERIFICATION)
 * instead of numeric risk scores. Includes acknowledgment functionality for
 * cases requiring manual verification.
 */
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  Checkbox,
  FormControlLabel,
  Alert,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  HourglassEmpty,
} from '@mui/icons-material';
import type {
  VerificationStatus,
  FraudIndicator,
  DiscrepancyValidationProgress,
} from '../../types/risk';
import { VERIFICATION_STATUS_CONFIG } from '../../types/risk';

interface FKVerificationStatusCardProps {
  verificationStatus: VerificationStatus;
  discrepancyCount: number;
  validationProgress?: DiscrepancyValidationProgress;
  onAcknowledge?: (acknowledged: boolean) => void;
  isAcknowledged?: boolean;
  isPreliminary?: boolean;
  indicators?: FraudIndicator[];
}

const FKVerificationStatusCard: React.FC<FKVerificationStatusCardProps> = ({
  verificationStatus,
  discrepancyCount,
  validationProgress,
  onAcknowledge,
  isAcknowledged = false,
  isPreliminary = false,
  indicators = [],
}) => {
  // Check if all discrepancies are validated
  const allValidated = validationProgress?.all_validated ?? false;

  // Override display status based on validation progress
  const displayStatus = isPreliminary ? 'pending' : verificationStatus;

  // Use validated styling when all discrepancies are validated by mesa de control
  const showValidatedStatus = allValidated && discrepancyCount > 0;

  const config = showValidatedStatus
    ? {
        label: 'VALIDADO POR MESA DE CONTROL',
        bgColor: '#E0F7E6',
        textColor: '#2CA14D',
        color: 'success' as const,
        icon: 'CheckCircle' as const,
      }
    : VERIFICATION_STATUS_CONFIG[displayStatus];

  const isPass = (verificationStatus === 'pass' && !isPreliminary) || showValidatedStatus;

  // Get icon component based on display status
  const StatusIcon = displayStatus === 'pending' ? HourglassEmpty : (isPass ? CheckCircle : Warning);

  // Count triggered indicators
  const triggeredIndicators = indicators.filter(ind => ind.indicator_value);
  const passedIndicators = indicators.filter(ind => !ind.indicator_value);

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Estado de Verificación
        </Typography>

        {/* Main Status Display */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 4,
            backgroundColor: config.bgColor,
            borderRadius: 2,
            mb: 2,
          }}
        >
          <StatusIcon
            sx={{
              fontSize: 80,
              color: config.textColor,
              mb: 2,
            }}
          />

          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: config.textColor,
              textAlign: 'center',
              px: 2,
            }}
          >
            {config.label}
          </Typography>

          {/* Show discrepancy count with validation progress */}
          {!isPreliminary && discrepancyCount > 0 && (
            <>
              {showValidatedStatus ? (
                <Chip
                  label={`${validationProgress?.validated_count}/${validationProgress?.total_discrepancies} discrepancias validadas`}
                  sx={{
                    mt: 2,
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    color: config.textColor,
                    fontWeight: 600,
                  }}
                />
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={`${discrepancyCount} discrepancia${discrepancyCount > 1 ? 's' : ''} encontrada${discrepancyCount > 1 ? 's' : ''}`}
                    sx={{
                      mt: 2,
                      backgroundColor: 'rgba(255, 255, 255, 0.8)',
                      color: config.textColor,
                      fontWeight: 600,
                    }}
                  />
                  {validationProgress && validationProgress.validated_count > 0 && (
                    <Chip
                      label={`Validados: ${validationProgress.validated_count}/${validationProgress.total_discrepancies}`}
                      size="small"
                      sx={{
                        backgroundColor: '#FFF4E5',
                        color: '#B86E00',
                        fontWeight: 500,
                      }}
                    />
                  )}
                </Box>
              )}
            </>
          )}
        </Box>

        {/* Preliminary Info */}
        {isPreliminary && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Suba y valide documentos para obtener el estado de verificación final.
            </Typography>
          </Alert>
        )}

        {/* Acknowledgment Section - Only for REQUIRES_MANUAL_VERIFICATION */}
        {!isPass && !isPreliminary && onAcknowledge && (
          <Box
            sx={{
              p: 2,
              backgroundColor: '#FFF4E5',
              borderRadius: 2,
              border: '1px solid #FFB74D',
              mb: 2,
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
              Acción Requerida
            </Typography>
            <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
              Se encontraron discrepancias en la validación cruzada de documentos.
              Debe revisar las discrepancias antes de tomar una decisión.
            </Typography>
            <FormControlLabel
              control={
                <Checkbox
                  checked={isAcknowledged}
                  onChange={(e) => onAcknowledge(e.target.checked)}
                  color="warning"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  Confirmo que he revisado las discrepancias encontradas
                </Typography>
              }
            />
          </Box>
        )}

        {/* Indicators Summary */}
        {indicators.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Resumen de Indicadores
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
              {triggeredIndicators.length > 0 && (
                <Box
                  sx={{
                    flex: 1,
                    p: 1.5,
                    backgroundColor: '#FFE4E4',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="caption" color="error" sx={{ fontWeight: 600 }}>
                    Alertas Detectadas
                  </Typography>
                  <Typography variant="h6" color="error">
                    {triggeredIndicators.length}
                  </Typography>
                </Box>
              )}
              {passedIndicators.length > 0 && (
                <Box
                  sx={{
                    flex: 1,
                    p: 1.5,
                    backgroundColor: '#E0F7E6',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="caption" color="success.main" sx={{ fontWeight: 600 }}>
                    Verificaciones OK
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {passedIndicators.length}
                  </Typography>
                </Box>
              )}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default FKVerificationStatusCard;
