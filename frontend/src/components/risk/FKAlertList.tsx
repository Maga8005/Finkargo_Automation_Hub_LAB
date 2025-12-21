/**
 * FKAlertList - Active alerts display component
 */
import React from 'react';
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip,
  Typography,
  Box,
  Paper,
} from '@mui/material';
import {
  Info,
  Warning,
  Error,
  CheckCircle,
} from '@mui/icons-material';
import type { RiskAlert, AlertSeverity } from '../../types/risk';
import { ALERT_SEVERITY_CONFIG } from '../../types/risk';

interface FKAlertListProps {
  alerts: RiskAlert[];
  onMarkRead: (id: string) => void;
  loading?: boolean;
}

const FKAlertList: React.FC<FKAlertListProps> = ({
  alerts,
  onMarkRead,
  loading = false,
}) => {
  // Get icon for severity
  const getSeverityIcon = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical':
        return <Error color="error" />;
      case 'warning':
        return <Warning color="warning" />;
      default:
        return <Info color="info" />;
    }
  };

  // Format date for display
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Ahora';
    if (minutes < 60) return `Hace ${minutes} min`;
    if (hours < 24) return `Hace ${hours}h`;
    if (days < 7) return `Hace ${days}d`;

    return date.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: 'short',
    });
  };

  if (alerts.length === 0) {
    return (
      <Box
        sx={{
          textAlign: 'center',
          py: 4,
          color: 'text.secondary',
        }}
      >
        <CheckCircle sx={{ fontSize: 48, color: 'success.light', mb: 1 }} />
        <Typography variant="body1">
          No hay alertas pendientes
        </Typography>
      </Box>
    );
  }

  return (
    <List sx={{ width: '100%' }}>
      {alerts.map((alert) => {
        const config = ALERT_SEVERITY_CONFIG[alert.severity];

        return (
          <Paper
            key={alert.id}
            elevation={alert.is_read ? 0 : 1}
            sx={{
              mb: 1,
              backgroundColor: alert.is_read ? 'transparent' : 'background.paper',
              opacity: alert.is_read ? 0.7 : 1,
              border: alert.severity === 'critical' && !alert.is_read
                ? '1px solid'
                : 'none',
              borderColor: 'error.main',
            }}
          >
            <ListItem
              secondaryAction={
                !alert.is_read && (
                  <IconButton
                    edge="end"
                    aria-label="mark as read"
                    onClick={() => onMarkRead(alert.id)}
                    size="small"
                    disabled={loading}
                  >
                    <CheckCircle fontSize="small" />
                  </IconButton>
                )
              }
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                {getSeverityIcon(alert.severity)}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                    <Typography
                      variant="body2"
                      component="span"
                      sx={{
                        fontWeight: alert.is_read ? 400 : 600,
                      }}
                    >
                      {alert.title}
                    </Typography>
                    <Chip
                      label={config.label}
                      size="small"
                      color={config.color}
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Box>
                }
                secondary={
                  <Box component="span">
                    <Typography
                      variant="caption"
                      component="span"
                      sx={{
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        maxWidth: '90%',
                      }}
                    >
                      {alert.message}
                    </Typography>
                    <Typography
                      variant="caption"
                      component="span"
                      color="text.secondary"
                    >
                      {formatDate(alert.created_at)}
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          </Paper>
        );
      })}
    </List>
  );
};

export default FKAlertList;
