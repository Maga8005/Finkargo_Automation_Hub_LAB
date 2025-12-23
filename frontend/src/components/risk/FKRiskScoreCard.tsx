/**
 * FKRiskScoreCard - Risk assessment indicators display component
 *
 * NOTE: Numeric scores are intentionally hidden from the UI.
 * The stakeholder requirement is to show only binary pass/fail status,
 * not numeric scores. The score is preserved for internal analytics only.
 */
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Cancel,
  HourglassEmpty,
} from '@mui/icons-material';
import type { FraudIndicator, VerificationStatus } from '../../types/risk';
import { VERIFICATION_STATUS_CONFIG } from '../../types/risk';

interface FKRiskScoreCardProps {
  score: number; // Kept for backward compatibility but not displayed
  level: string; // Kept for backward compatibility but not displayed
  indicators: FraudIndicator[];
  isPreliminary?: boolean;
  verificationStatus?: VerificationStatus;
  discrepancyCount?: number;
}

const FKRiskScoreCard: React.FC<FKRiskScoreCardProps> = ({
  indicators,
  isPreliminary = false,
  verificationStatus = 'pass',
  discrepancyCount = 0,
}) => {
  const config = VERIFICATION_STATUS_CONFIG[verificationStatus];
  const isPass = verificationStatus === 'pass';

  // Get icon for indicator
  const getIndicatorIcon = (indicator: FraudIndicator) => {
    if (!indicator.indicator_value) {
      return <CheckCircle color="success" />;
    }

    switch (indicator.severity) {
      case 'critical':
        return <Cancel color="error" />;
      case 'high':
        return <Error color="error" />;
      case 'medium':
        return <Warning color="warning" />;
      default:
        return <Warning color="info" />;
    }
  };

  // Separate triggered vs passed indicators
  const triggeredIndicators = indicators.filter(ind => ind.indicator_value);
  const passedIndicators = indicators.filter(ind => !ind.indicator_value);

  // Get status icon
  const StatusIcon = isPass ? CheckCircle : Warning;

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Estado de Verificación
        </Typography>

        {/* Binary Status Display */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 3,
            backgroundColor: config.bgColor,
            borderRadius: 2,
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
            variant="h6"
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
              label={`${discrepancyCount} discrepancia${discrepancyCount > 1 ? 's' : ''}`}
              size="small"
              sx={{
                mt: 1,
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
                mt: 1,
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

        <Divider sx={{ my: 2 }} />

        {/* Indicators List - Grouped by triggered vs passed */}
        {triggeredIndicators.length > 0 && (
          <>
            <Typography variant="subtitle2" color="error" gutterBottom>
              Alertas Detectadas ({triggeredIndicators.length})
            </Typography>

            <List dense sx={{ maxHeight: 150, overflow: 'auto', mb: 2 }}>
              {triggeredIndicators.map((indicator, index) => (
                <ListItem
                  key={index}
                  sx={{
                    backgroundColor: 'rgba(255, 0, 0, 0.05)',
                    borderRadius: 1,
                    mb: 0.5,
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getIndicatorIcon(indicator)}
                  </ListItemIcon>
                  <ListItemText
                    primary={indicator.indicator_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    secondary={indicator.evidence || 'Detectado'}
                    primaryTypographyProps={{
                      variant: 'body2',
                      fontWeight: 600,
                    }}
                    secondaryTypographyProps={{
                      variant: 'caption',
                      sx: {
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      },
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </>
        )}

        {passedIndicators.length > 0 && (
          <>
            <Typography variant="subtitle2" color="success.main" gutterBottom>
              Verificaciones OK ({passedIndicators.length})
            </Typography>

            <List dense sx={{ maxHeight: 150, overflow: 'auto' }}>
              {passedIndicators.map((indicator, index) => (
                <ListItem
                  key={index}
                  sx={{
                    backgroundColor: 'transparent',
                    borderRadius: 1,
                    mb: 0.5,
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getIndicatorIcon(indicator)}
                  </ListItemIcon>
                  <ListItemText
                    primary={indicator.indicator_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    secondary="OK"
                    primaryTypographyProps={{
                      variant: 'body2',
                      fontWeight: 400,
                    }}
                    secondaryTypographyProps={{
                      variant: 'caption',
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default FKRiskScoreCard;
