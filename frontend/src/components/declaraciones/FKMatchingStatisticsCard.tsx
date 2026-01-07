/**
 * FKMatchingStatisticsCard - Matching Statistics Display Component
 *
 * Displays comprehensive matching statistics in a grid layout with color-coded metrics.
 * Shows matched/unmatched counts, declaration usage, confidence scores, and match quality distribution.
 */
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  LinearProgress,
  Divider,
  Skeleton,
  Grid,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Assignment as AssignmentIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import type { MatchingResultsStatistics } from '../../types/matching_results_types';

interface FKMatchingStatisticsCardProps {
  statistics: MatchingResultsStatistics | null;
  loading?: boolean;
  error?: string | null;
}

const FKMatchingStatisticsCard: React.FC<FKMatchingStatisticsCardProps> = ({
  statistics,
  loading = false,
  error = null,
}) => {
  console.log('[FKMatchingStatisticsCard] Rendering statistics card', {
    hasStatistics: !!statistics,
    loading,
    error,
  });

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width="40%" height={32} sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            {[...Array(6)].map((_, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
                <Skeleton variant="rectangular" height={120} sx={{ borderRadius: 1 }} />
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" color="error" gutterBottom>
            Error Loading Statistics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {error}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (!statistics) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            No statistics available
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const {
    total_payments,
    matched_payments,
    unmatched_payments,
    match_percentage,
    total_declarations,
    declarations_used,
    declarations_unused,
    declaration_usage_percentage,
    average_confidence_score,
    perfect_matches_count,
    good_matches_count,
    possible_matches_count,
  } = statistics;

  // Determine color based on match percentage
  const getMatchPercentageColor = (percentage: number): string => {
    if (percentage >= 80) return 'success.main';
    if (percentage >= 60) return 'warning.main';
    return 'error.main';
  };

  // Determine color based on confidence score
  const getConfidenceColor = (score: number): string => {
    if (score >= 0.95) return 'success.main';
    if (score >= 0.70) return 'info.main';
    return 'warning.main';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Matching Results Summary
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Overview of declaration-payment matching performance and quality metrics
        </Typography>

        <Grid container spacing={3}>
          {/* Matched Payments */}
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
                  Matched Payments
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {matched_payments}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                of {total_payments} total payments
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={match_percentage}
                  sx={{
                    flex: 1,
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getMatchPercentageColor(match_percentage),
                    },
                  }}
                />
                <Typography
                  variant="caption"
                  fontWeight={600}
                  color={getMatchPercentageColor(match_percentage)}
                >
                  {match_percentage.toFixed(1)}%
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Unmatched Payments */}
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
                  Unmatched Payments
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="error.main">
                {unmatched_payments}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                of {total_payments} total payments
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={(unmatched_payments / total_payments) * 100}
                  sx={{
                    flex: 1,
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: 'error.main',
                    },
                  }}
                />
                <Typography variant="caption" fontWeight={600} color="error.main">
                  {((unmatched_payments / total_payments) * 100).toFixed(1)}%
                </Typography>
              </Box>
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
                    backgroundColor: 'info.50',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'info.main',
                  }}
                >
                  <AssignmentIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Declarations Used
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {declarations_used}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                of {total_declarations} total declarations
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={declaration_usage_percentage}
                  sx={{
                    flex: 1,
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: 'info.main',
                    },
                  }}
                />
                <Typography variant="caption" fontWeight={600} color="info.main">
                  {declaration_usage_percentage.toFixed(1)}%
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Average Confidence Score */}
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
                    backgroundColor: `${getConfidenceColor(average_confidence_score).replace('.main', '.50')}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: getConfidenceColor(average_confidence_score),
                  }}
                >
                  <TrendingUpIcon />
                </Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Average Confidence
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color={getConfidenceColor(average_confidence_score)}>
                {(average_confidence_score * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                across all matches
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={average_confidence_score * 100}
                  sx={{
                    flex: 1,
                    height: 8,
                    borderRadius: 1,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getConfidenceColor(average_confidence_score),
                    },
                  }}
                />
                <Typography
                  variant="caption"
                  fontWeight={600}
                  color={getConfidenceColor(average_confidence_score)}
                >
                  {(average_confidence_score).toFixed(2)}
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Perfect Matches */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'success.main',
                backgroundColor: 'success.50',
                height: '100%',
              }}
            >
              <Typography variant="subtitle2" color="success.dark" gutterBottom>
                Perfect Matches
              </Typography>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {perfect_matches_count}
              </Typography>
              <Typography variant="caption" color="success.dark">
                Confidence: 0.95-1.0 (Excellent quality)
              </Typography>
            </Box>
          </Grid>

          {/* Good Matches */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'info.main',
                backgroundColor: 'info.50',
                height: '100%',
              }}
            >
              <Typography variant="subtitle2" color="info.dark" gutterBottom>
                Good Matches
              </Typography>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {good_matches_count}
              </Typography>
              <Typography variant="caption" color="info.dark">
                Confidence: 0.70-0.94 (Good quality)
              </Typography>
            </Box>
          </Grid>

          {/* Possible Matches */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'warning.main',
                backgroundColor: 'warning.50',
                height: '100%',
              }}
            >
              <Typography variant="subtitle2" color="warning.dark" gutterBottom>
                Possible Matches
              </Typography>
              <Typography variant="h4" fontWeight={700} color="warning.main">
                {possible_matches_count}
              </Typography>
              <Typography variant="caption" color="warning.dark">
                Confidence: 0.50-0.69 (Review recommended)
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Summary Footer */}
        <Divider sx={{ my: 2 }} />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {declarations_unused > 0 && (
              <>
                {declarations_unused} declaration{declarations_unused !== 1 ? 's' : ''} unused
              </>
            )}
            {declarations_unused === 0 && 'All declarations have been assigned to payments'}
          </Typography>
          <Typography variant="body2" fontWeight={600} color="text.primary">
            Total Processed: {total_payments} payments
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FKMatchingStatisticsCard;
