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
import type { VerificationStatus, FraudIndicator } from '../../types/risk';
import { VERIFICATION_STATUS_CONFIG } from '../../types/risk';

interface FKVerificationStatusCardProps {
  verificationStatus: VerificationStatus;
  discrepancyCount: number;
  onAcknowledge?: (acknowledged: boolean) => void;
  isAcknowledged?: boolean;
  isPreliminary?: boolean;
  indicators?: FraudIndicator[];
}

const FKVerificationStatusCard: React.FC<FKVerificationStatusCardProps> = ({
  verificationStatus,
  discrepancyCount,
  onAcknowledge,
  isAcknowledged = false,
  isPreliminary = false,
  indicators = [],
}) => {
  const config = VERIFICATION_STATUS_CONFIG[verificationStatus];
  const isPass = verificationStatus === 'pass';

  // Get icon component based on status
  const StatusIcon = isPass ? CheckCircle : Warning;

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

          {!isPass && discrepancyCount > 0 && (
            <Chip
              label={`${discrepancyCount} discrepancia${discrepancyCount > 1 ? 's' : ''} encontrada${discrepancyCount > 1 ? 's' : ''}`}
              sx={{
                mt: 2,
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                color: config.textColor,
                fontWeight: 600,
              }}
            />
          )}

          {isPreliminary && (
            <Chip
              icon={<HourglassEmpty sx={{ fontSize: 16 }} />}
              label="Verificación Pendiente"
              size="small"
              sx={{
                mt: 2,
                backgroundColor: '#E3F2FD',
                color: '#1976D2',
                fontWeight: 500,
                fontSize: '0.75rem',
                '& .MuiChip-icon': {
                  color: '#1976D2',
                },
              }}
            />
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
