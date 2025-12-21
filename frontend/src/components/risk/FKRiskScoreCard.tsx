/**
 * FKRiskScoreCard - Risk score visualization component
 */
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Cancel,
} from '@mui/icons-material';
import type { RiskLevel, FraudIndicator } from '../../types/risk';
import { RISK_LEVEL_CONFIG } from '../../types/risk';

interface FKRiskScoreCardProps {
  score: number;
  level: RiskLevel;
  indicators: FraudIndicator[];
}

const FKRiskScoreCard: React.FC<FKRiskScoreCardProps> = ({
  score,
  level,
  indicators,
}) => {
  const config = RISK_LEVEL_CONFIG[level];

  // Get color for circular progress
  const getProgressColor = (): string => {
    if (level === 'low') return '#2CA14D';
    if (level === 'medium') return '#B86E00';
    if (level === 'high') return '#E65100';
    return '#CC071E';
  };

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

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Puntuación de Riesgo
        </Typography>

        {/* Score Circle */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 3,
          }}
        >
          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <CircularProgress
              variant="determinate"
              value={score}
              size={120}
              thickness={6}
              sx={{
                color: getProgressColor(),
                '& .MuiCircularProgress-circle': {
                  strokeLinecap: 'round',
                },
              }}
            />
            <Box
              sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography
                variant="h4"
                component="div"
                sx={{ fontWeight: 700 }}
              >
                {score.toFixed(0)}
              </Typography>
            </Box>
          </Box>

          <Chip
            label={config.label}
            sx={{
              mt: 2,
              backgroundColor: config.bgColor,
              color: config.textColor,
              fontWeight: 600,
              fontSize: '0.9rem',
              px: 2,
            }}
          />
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Indicators List */}
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Indicadores de Fraude ({indicators.length})
        </Typography>

        <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
          {indicators.map((indicator, index) => (
            <ListItem
              key={index}
              sx={{
                backgroundColor: indicator.indicator_value
                  ? 'rgba(255, 0, 0, 0.05)'
                  : 'transparent',
                borderRadius: 1,
                mb: 0.5,
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {getIndicatorIcon(indicator)}
              </ListItemIcon>
              <ListItemText
                primary={indicator.indicator_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                secondary={indicator.evidence || (indicator.indicator_value ? 'Detectado' : 'OK')}
                primaryTypographyProps={{
                  variant: 'body2',
                  fontWeight: indicator.indicator_value ? 600 : 400,
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
              {indicator.indicator_value && (
                <Typography
                  variant="caption"
                  color="error"
                  sx={{ fontWeight: 600 }}
                >
                  +{indicator.score_impact.toFixed(0)}
                </Typography>
              )}
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default FKRiskScoreCard;
