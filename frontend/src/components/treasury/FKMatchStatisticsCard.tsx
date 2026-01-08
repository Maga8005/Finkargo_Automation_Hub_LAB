/**
 * FKMatchStatisticsCard - Statistics summary card for matching results.
 *
 * Displays matching statistics with visual indicators.
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Grid,
  Skeleton,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Assignment as AssignmentIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import type { MatchingStatistics } from '../../types/treasuryMatching';

interface FKMatchStatisticsCardProps {
  statistics: MatchingStatistics | null;
  loading?: boolean;
}

const FKMatchStatisticsCard: React.FC<FKMatchStatisticsCardProps> = ({
  statistics,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width="40%" height={32} sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            {[...Array(6)].map((_, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
                <Skeleton variant="rectangular" height={100} sx={{ borderRadius: 1 }} />
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    );
  }

  if (!statistics) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Ejecute el algoritmo de coincidencias para ver las estadisticas
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // Color helpers
  const getMatchPercentageColor = (percentage: number): string => {
    if (percentage >= 80) return 'success.main';
    if (percentage >= 60) return 'warning.main';
    return 'error.main';
  };

  const getConfidenceColor = (score: number): string => {
    if (score >= 0.95) return 'success.main';
    if (score >= 0.70) return 'info.main';
    return 'warning.main';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Resumen de Coincidencias
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Resultados del algoritmo de coincidencia entre pagos y declaraciones
        </Typography>

        <Grid container spacing={3}>
          {/* Matched Groups */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                height: '100%',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1,
                    backgroundColor: 'success.50',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'success.main',
                  }}
                >
                  <CheckCircleIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Coincidencias
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {statistics.matched_groups}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                de {statistics.total_payment_groups} grupos
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={statistics.match_percentage}
                  sx={{
                    flex: 1,
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getMatchPercentageColor(statistics.match_percentage),
                    },
                  }}
                />
                <Typography
                  variant="caption"
                  fontWeight={600}
                  color={getMatchPercentageColor(statistics.match_percentage)}
                >
                  {statistics.match_percentage.toFixed(1)}%
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Unmatched Groups */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                height: '100%',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1,
                    backgroundColor: 'error.50',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'error.main',
                  }}
                >
                  <CancelIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Sin Coincidencia
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="error.main">
                {statistics.unmatched_groups}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                grupos sin declaracion
              </Typography>
            </Box>
          </Grid>

          {/* Partial Matches */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                height: '100%',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1,
                    backgroundColor: 'warning.50',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'warning.main',
                  }}
                >
                  <WarningIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Parciales
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="warning.main">
                {statistics.partial_matches}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                requieren revision
              </Typography>
            </Box>
          </Grid>

          {/* Conflicts */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                height: '100%',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1,
                    backgroundColor: 'info.50',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'info.main',
                  }}
                >
                  <HelpIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Conflictos
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {statistics.conflict_groups}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                multiples candidatos
              </Typography>
            </Box>
          </Grid>

          {/* Declaration Usage */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                height: '100%',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1,
                    backgroundColor: 'primary.50',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'primary.main',
                  }}
                >
                  <AssignmentIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Declaraciones Usadas
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="primary.main">
                {statistics.declarations_used}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                de {statistics.total_declarations} disponibles
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {statistics.declarations_unused} sin usar
              </Typography>
            </Box>
          </Grid>

          {/* Average Confidence */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
                height: '100%',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1,
                    backgroundColor: 'grey.100',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: getConfidenceColor(statistics.average_confidence),
                  }}
                >
                  <TrendingUpIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Confianza Promedio
                </Typography>
              </Box>
              <Typography
                variant="h4"
                fontWeight={700}
                color={getConfidenceColor(statistics.average_confidence)}
              >
                {(statistics.average_confidence * 100).toFixed(0)}%
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={statistics.average_confidence * 100}
                  sx={{
                    flex: 1,
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getConfidenceColor(statistics.average_confidence),
                    },
                  }}
                />
              </Box>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default FKMatchStatisticsCard;
