/**
 * FKConfidenceDistributionChart - Confidence Score Distribution Component
 *
 * Displays horizontal bar chart showing distribution of matches across confidence ranges:
 * - Perfect Matches (0.95-1.0)
 * - Good Matches (0.70-0.94)
 * - Possible Matches (0.50-0.69)
 */
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  ThumbUp as ThumbUpIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import type { ConfidenceDistribution } from '../../types/matching_results_types';

interface FKConfidenceDistributionChartProps {
  distribution: ConfidenceDistribution | null;
  loading?: boolean;
  error?: string | null;
}

const FKConfidenceDistributionChart: React.FC<FKConfidenceDistributionChartProps> = ({
  distribution,
  loading = false,
  error = null,
}) => {
  console.log('[FKConfidenceDistributionChart] Rendering distribution chart', {
    hasDistribution: !!distribution,
    loading,
    error,
  });

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Loading...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" color="error" gutterBottom>
            Error Loading Distribution
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {error}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (!distribution) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            No distribution data available
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const { perfect, good, possible } = distribution;
  const total = perfect.count + good.count + possible.count;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Confidence Score Distribution
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Breakdown of match quality across confidence ranges
        </Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Perfect Matches */}
          <Box>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CheckCircleIcon sx={{ fontSize: 20, color: 'success.main' }} />
                <Typography variant="subtitle2" fontWeight={600}>
                  Perfect Matches
                </Typography>
                <Tooltip title="Confidence score between 0.95 and 1.0. These matches have excellent quality with minimal differences in amount, date, and customer name.">
                  <HelpIcon sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }} />
                </Tooltip>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 0.5 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  {perfect.range}
                </Typography>
                <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={total > 0 ? perfect.percentage : 0}
                    sx={{
                      flex: 1,
                      height: 24,
                      borderRadius: 1,
                      backgroundColor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: 'success.main',
                        borderRadius: 1,
                      },
                    }}
                  />
                  <Typography
                    variant="body2"
                    fontWeight={600}
                    sx={{ minWidth: 80, color: 'success.main' }}
                  >
                    {perfect.count} ({perfect.percentage.toFixed(1)}%)
                  </Typography>
                </Box>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Excellent quality matches - Ready for approval
              </Typography>
            </Box>
          </Box>

          {/* Good Matches */}
          <Box>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <ThumbUpIcon sx={{ fontSize: 20, color: 'info.main' }} />
                <Typography variant="subtitle2" fontWeight={600}>
                  Good Matches
                </Typography>
                <Tooltip title="Confidence score between 0.70 and 0.94. These matches have good quality but may have slight differences in one or more criteria.">
                  <HelpIcon sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }} />
                </Tooltip>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 0.5 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  {good.range}
                </Typography>
                <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={total > 0 ? good.percentage : 0}
                    sx={{
                      flex: 1,
                      height: 24,
                      borderRadius: 1,
                      backgroundColor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: 'info.main',
                        borderRadius: 1,
                      },
                    }}
                  />
                  <Typography
                    variant="body2"
                    fontWeight={600}
                    sx={{ minWidth: 80, color: 'info.main' }}
                  >
                    {good.count} ({good.percentage.toFixed(1)}%)
                  </Typography>
                </Box>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Good quality matches - Quick review recommended
              </Typography>
            </Box>
          </Box>

          {/* Possible Matches */}
          <Box>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <HelpIcon sx={{ fontSize: 20, color: 'warning.main' }} />
                <Typography variant="subtitle2" fontWeight={600}>
                  Possible Matches
                </Typography>
                <Tooltip title="Confidence score between 0.50 and 0.69. These matches have significant differences and require careful manual review.">
                  <HelpIcon sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }} />
                </Tooltip>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 0.5 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                  {possible.range}
                </Typography>
                <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={total > 0 ? possible.percentage : 0}
                    sx={{
                      flex: 1,
                      height: 24,
                      borderRadius: 1,
                      backgroundColor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: 'warning.main',
                        borderRadius: 1,
                      },
                    }}
                  />
                  <Typography
                    variant="body2"
                    fontWeight={600}
                    sx={{ minWidth: 80, color: 'warning.main' }}
                  >
                    {possible.count} ({possible.percentage.toFixed(1)}%)
                  </Typography>
                </Box>
              </Box>
              <Typography variant="caption" color="text.secondary">
                Lower quality matches - Thorough manual review required
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Summary */}
        <Box
          sx={{
            mt: 3,
            p: 2,
            borderRadius: 1,
            backgroundColor: (theme) =>
              theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100',
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography variant="body2" fontWeight={600} gutterBottom>
            Distribution Summary
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Total Matches: {total} •{' '}
            Perfect: {perfect.percentage.toFixed(1)}% •{' '}
            Good: {good.percentage.toFixed(1)}% •{' '}
            Possible: {possible.percentage.toFixed(1)}%
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FKConfidenceDistributionChart;
