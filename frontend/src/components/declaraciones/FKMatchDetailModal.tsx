/**
 * FKMatchDetailModal - Match Detail Modal Component
 *
 * Modal dialog displaying comprehensive information about a specific match including
 * payment data, declaration data, matching criteria analysis, and confidence breakdown.
 */
import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Divider,
  LinearProgress,
  IconButton,
} from '@mui/material';
import {
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import type { MatchDetail } from '../../types/matching_results_types';

interface FKMatchDetailModalProps {
  open: boolean;
  match: MatchDetail | null;
  onClose: () => void;
  onApprove?: (matchId: string) => void;
  onReject?: (matchId: string) => void;
  onOverride?: (matchId: string) => void;
}

const FKMatchDetailModal: React.FC<FKMatchDetailModalProps> = ({
  open,
  match,
  onClose,
  onApprove,
  onReject,
  onOverride,
}) => {
  console.log('[FKMatchDetailModal] Rendering match detail modal', {
    open,
    hasMatch: !!match,
    matchId: match?.id,
  });

  if (!match) {
    return null;
  }

  // Format currency
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Get match status color
  const getMatchStatusColor = (
    status: 'approved' | 'pending_review' | 'rejected'
  ): 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      default:
        return 'warning';
    }
  };

  // Render criteria indicator
  const renderCriteriaIndicator = (passed: boolean, label: string) => {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        {passed ? (
          <CheckCircleIcon sx={{ fontSize: 20, color: 'success.main' }} />
        ) : (
          <CancelIcon sx={{ fontSize: 20, color: 'error.main' }} />
        )}
        <Typography variant="body2" color={passed ? 'success.main' : 'error.main'}>
          {label}
        </Typography>
      </Box>
    );
  };

  // Generate match reasoning
  const generateMatchReasoning = (): string => {
    const parts: string[] = [];

    // Amount match
    if (match.amount_difference === 0) {
      parts.push(`Perfect amount match (${formatCurrency(match.amount_payment)})`);
    } else {
      parts.push(
        `Amount difference: ${formatCurrency(Math.abs(match.amount_difference))} (${
          Math.abs(match.amount_difference) <= 0.20 ? 'within tolerance' : 'outside tolerance'
        })`
      );
    }

    // Date match
    if (match.date_difference_days === 0) {
      parts.push('same day');
    } else {
      parts.push(
        `${Math.abs(match.date_difference_days)}-day date difference (${
          Math.abs(match.date_difference_days) <= 7 ? 'within 7-day tolerance' : 'outside tolerance'
        })`
      );
    }

    // Customer name match
    const similarityPct = (match.customer_name_similarity * 100).toFixed(0);
    if (match.customer_name_similarity >= 0.95) {
      parts.push(`excellent customer name match (${similarityPct}% similarity)`);
    } else if (match.customer_name_similarity >= 0.75) {
      parts.push(`good customer name match (${similarityPct}% similarity)`);
    } else {
      parts.push(`low customer name similarity (${similarityPct}%)`);
    }

    return parts.join(' with ');
  };

  // Calculate if criteria passed
  const amountPassed = Math.abs(match.amount_difference) <= 0.20;
  const datePassed = Math.abs(match.date_difference_days) <= 7;
  const customerPassed = match.customer_name_similarity >= 0.75;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Match Details
            </Typography>
            <Chip
              label={`Confidence: ${(match.confidence_score * 100).toFixed(0)}%`}
              color={
                match.confidence_score >= 0.95
                  ? 'success'
                  : match.confidence_score >= 0.70
                  ? 'info'
                  : 'warning'
              }
              size="small"
            />
            <Chip
              label={match.match_status.replace('_', ' ').toUpperCase()}
              color={getMatchStatusColor(match.match_status)}
              size="small"
            />
            {match.is_manual_override && (
              <Chip label="MANUAL OVERRIDE" color="secondary" size="small" />
            )}
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Payment Information */}
          <Box sx={{ flex: 1 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom color="primary">
                  Payment Information
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Payment Date
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {match.payment_date}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Amount
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {formatCurrency(match.amount_payment)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Customer Name (Payment)
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {match.customer_name_payment}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Declaration Information */}
          <Box sx={{ flex: 1 }}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom color="primary">
                  Declaration Information
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Declaration Number
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {match.declaration_number}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Amount
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {formatCurrency(match.amount_declaration)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Customer Name (Declaration)
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {match.customer_name_declaration}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Matching Criteria Analysis */}
          <Box>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  Matching Criteria Analysis
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* Amount Match */}
                  <Box>
                    <Box>
                      {renderCriteriaIndicator(amountPassed, 'Amount Match')}
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                        Difference: {formatCurrency(Math.abs(match.amount_difference))}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Tolerance: ±$0.20 or ±5%
                      </Typography>
                    </Box>
                  </Box>

                  {/* Date Match */}
                  <Box>
                    <Box>
                      {renderCriteriaIndicator(datePassed, 'Date Match')}
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                        Difference: {Math.abs(match.date_difference_days)} day
                        {Math.abs(match.date_difference_days) !== 1 ? 's' : ''}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Tolerance: ±7 days
                      </Typography>
                    </Box>
                  </Box>

                  {/* Customer Name Match */}
                  <Box>
                    <Box>
                      {renderCriteriaIndicator(customerPassed, 'Customer Name Match')}
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                        Similarity: {(match.customer_name_similarity * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Threshold: ≥75%
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Confidence Score Breakdown */}
          <Box>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                  Confidence Score: {(match.confidence_score * 100).toFixed(1)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={match.confidence_score * 100}
                  sx={{
                    height: 10,
                    borderRadius: 1,
                    mb: 2,
                    backgroundColor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor:
                        match.confidence_score >= 0.95
                          ? 'success.main'
                          : match.confidence_score >= 0.70
                          ? 'info.main'
                          : 'warning.main',
                    },
                  }}
                />
                <Typography variant="body2" color="text.secondary">
                  {generateMatchReasoning()}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          {/* Manual Override Info */}
          {match.is_manual_override && match.override_reason && (
            <Box>
              <Card variant="outlined" sx={{ backgroundColor: 'warning.50' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <WarningIcon sx={{ color: 'warning.main' }} />
                    <Typography variant="subtitle1" fontWeight={600}>
                      Manual Override
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Reason:</strong> {match.override_reason}
                  </Typography>
                  {match.override_type && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      <strong>Type:</strong> {match.override_type.replace(/_/g, ' ')}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} color="inherit">
          Close
        </Button>
        {onReject && match.match_status !== 'rejected' && (
          <Button onClick={() => onReject(match.id)} color="error" variant="outlined">
            Reject Match
          </Button>
        )}
        {onOverride && (
          <Button onClick={() => onOverride(match.id)} color="info" variant="outlined">
            Manual Override
          </Button>
        )}
        {onApprove && match.match_status !== 'approved' && (
          <Button onClick={() => onApprove(match.id)} color="success" variant="contained">
            Approve Match
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default FKMatchDetailModal;
