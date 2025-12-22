/**
 * FKRiskMetrics - Dashboard metrics cards component
 */
import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
} from '@mui/material';
import {
  Assessment,
  PendingActions,
  Warning,
  Error,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';
import type { RiskStats } from '../../types/risk';

interface FKRiskMetricsProps {
  stats: RiskStats;
}

interface MetricCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  color,
  subtitle,
}) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 700, color }}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box
          sx={{
            backgroundColor: `${color}15`,
            borderRadius: 2,
            p: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color,
            '& svg': { fontSize: 28 },
          }}
        >
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const FKRiskMetrics: React.FC<FKRiskMetricsProps> = ({ stats }) => {
  const formatPercentage = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return `${value.toFixed(1)}%`;
  };

  return (
    <Grid container spacing={3}>
      {/* Total Evaluations */}
      <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
        <MetricCard
          title="Total Evaluaciones"
          value={stats.total_assessments}
          icon={<Assessment />}
          color="#3C47D3"
          subtitle={`Hoy: ${stats.assessed_today}`}
        />
      </Grid>

      {/* Pending Review */}
      <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
        <MetricCard
          title="Pendientes"
          value={stats.pending_review}
          icon={<PendingActions />}
          color="#B86E00"
          subtitle="Requieren revisión"
        />
      </Grid>

      {/* High Risk */}
      <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
        <MetricCard
          title="Alto Riesgo"
          value={stats.high_risk_count}
          icon={<Warning />}
          color="#E65100"
        />
      </Grid>

      {/* Critical Risk */}
      <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
        <MetricCard
          title="Críticos"
          value={stats.critical_risk_count}
          icon={<Error />}
          color="#CC071E"
        />
      </Grid>

      {/* Approved */}
      <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
        <MetricCard
          title="Aprobados"
          value={stats.approved}
          icon={<CheckCircle />}
          color="#2CA14D"
          subtitle={formatPercentage(stats.approval_rate)}
        />
      </Grid>

      {/* Rejected */}
      <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
        <MetricCard
          title="Rechazados"
          value={stats.rejected}
          icon={<Cancel />}
          color="#CC071E"
          subtitle={formatPercentage(stats.rejection_rate)}
        />
      </Grid>
    </Grid>
  );
};

export default FKRiskMetrics;
