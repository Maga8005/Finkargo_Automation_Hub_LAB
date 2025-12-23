/**
 * RiskDashboard - Main risk management dashboard page
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { Add, Refresh } from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';
import { riskService } from '../../services/riskService';
import FKRiskMetrics from '../../components/risk/FKRiskMetrics';
import FKAlertList from '../../components/risk/FKAlertList';
import FKBlacklistManager from '../../components/risk/FKBlacklistManager';
import FKRiskEvaluationForm from '../../components/risk/FKRiskEvaluationForm';
import type {
  RiskStats,
  RiskAssessmentDetail,
  RiskAlert,
  BlacklistEntry,
  RiskAssessmentRequest,
  BlacklistEntryRequest,
} from '../../types/risk';
import { VERIFICATION_STATUS_CONFIG, ASSESSMENT_STATUS_CONFIG } from '../../types/risk';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`risk-tabpanel-${index}`}
      aria-labelledby={`risk-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const RiskDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { userProfile } = useAuth();

  // State
  const [currentTab, setCurrentTab] = useState(0);
  const [stats, setStats] = useState<RiskStats | null>(null);
  const [evaluations, setEvaluations] = useState<RiskAssessmentDetail[]>([]);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [blacklist, setBlacklist] = useState<BlacklistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [evalDialogOpen, setEvalDialogOpen] = useState(false);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  // Check if user is risk manager
  const isRiskManager = userProfile?.role === 'risk_manager' || userProfile?.role === 'admin';

  // Load data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsData, evaluationsData, alertsData, blacklistData] = await Promise.all([
        riskService.getDashboard(),
        riskService.getEvaluations({ limit: 50 }),
        riskService.getAlerts(false, 20),
        riskService.getBlacklist({ is_active: true }),
      ]);

      setStats(statsData);
      setEvaluations(evaluationsData);
      setAlerts(alertsData);
      setBlacklist(blacklistData);
    } catch (err) {
      console.error('Error loading risk data:', err);
      setError('Error al cargar los datos de riesgo');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handlers
  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleEvaluate = async (request: RiskAssessmentRequest) => {
    try {
      setEvalLoading(true);
      setEvalError(null);

      const result = await riskService.createEvaluation(request);

      // Close dialog and refresh
      setEvalDialogOpen(false);
      await loadData();

      // Navigate to detail page
      navigate(`/risk/evaluations/${result.id}`);
    } catch (err: unknown) {
      console.error('Error creating evaluation:', err);
      const message = err instanceof Error ? err.message : 'Error al crear la evaluación';
      setEvalError(message);
    } finally {
      setEvalLoading(false);
    }
  };

  const handleMarkAlertRead = async (id: string) => {
    try {
      await riskService.markAlertRead(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true } : a)));
    } catch (err) {
      console.error('Error marking alert as read:', err);
    }
  };

  const handleAddToBlacklist = async (entry: BlacklistEntryRequest) => {
    await riskService.addToBlacklist(entry);
    await loadData();
  };

  const handleRemoveFromBlacklist = async (id: string) => {
    await riskService.removeFromBlacklist(id);
    setBlacklist((prev) => prev.filter((e) => e.id !== id));
  };

  // Table columns - Updated to show verification status instead of risk level/score
  const columns: GridColDef[] = [
    {
      field: 'assessment_id',
      headerName: 'ID',
      width: 140,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'client_nit',
      headerName: 'NIT Cliente',
      width: 140,
    },
    {
      field: 'client_info',
      headerName: 'Cliente',
      width: 200,
      valueGetter: (value: Record<string, string> | null | undefined) => value?.nombre_importador || 'N/A',
    },
    // Binary verification status replaces risk_level and risk_score columns
    {
      field: 'verification_status',
      headerName: 'Verificación',
      width: 200,
      renderCell: (params) => {
        const status = params.value || 'pass';
        const config = VERIFICATION_STATUS_CONFIG[status as keyof typeof VERIFICATION_STATUS_CONFIG];
        return (
          <Chip
            label={config.label}
            size="small"
            sx={{
              backgroundColor: config.bgColor,
              color: config.textColor,
              fontWeight: 600,
              fontSize: '0.7rem',
            }}
          />
        );
      },
    },
    {
      field: 'discrepancy_count',
      headerName: 'Discrepancias',
      width: 100,
      renderCell: (params) => {
        const count = params.value || 0;
        return (
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: count > 0 ? '#CC071E' : '#2CA14D',
            }}
          >
            {count}
          </Typography>
        );
      },
    },
    {
      field: 'status',
      headerName: 'Decisión',
      width: 120,
      renderCell: (params) => {
        const config = ASSESSMENT_STATUS_CONFIG[params.value as keyof typeof ASSESSMENT_STATUS_CONFIG];
        return (
          <Chip
            label={config.label}
            size="small"
            color={config.color}
          />
        );
      },
    },
    {
      field: 'created_at',
      headerName: 'Fecha',
      width: 150,
      valueGetter: (value) => {
        if (!value) return 'N/A';
        return new Date(value).toLocaleDateString('es-CO', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        });
      },
    },
  ];

  if (loading && !stats) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
            Gestión de Riesgos y Fraude
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Evaluación y detección de fraude para clientes
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadData}
            disabled={loading}
          >
            Actualizar
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setEvalDialogOpen(true)}
          >
            Nueva Evaluación
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Metrics */}
      {stats && <FKRiskMetrics stats={stats} />}

      {/* Tabs */}
      <Paper sx={{ mt: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label={`Evaluaciones (${evaluations.length})`} />
          <Tab label={`Alertas (${alerts.filter(a => !a.is_read).length})`} />
          <Tab label={`Blacklist (${blacklist.length})`} />
        </Tabs>

        {/* Evaluations Tab */}
        <TabPanel value={currentTab} index={0}>
          <DataGrid
            rows={evaluations}
            columns={columns}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: { paginationModel: { pageSize: 10 } },
              sorting: { sortModel: [{ field: 'created_at', sort: 'desc' }] },
            }}
            disableRowSelectionOnClick
            onRowClick={(params) => navigate(`/risk/evaluations/${params.row.id}`)}
            sx={{
              '& .MuiDataGrid-row': {
                cursor: 'pointer',
              },
              '& .MuiDataGrid-row:hover': {
                backgroundColor: 'action.hover',
              },
            }}
            autoHeight
          />
        </TabPanel>

        {/* Alerts Tab */}
        <TabPanel value={currentTab} index={1}>
          <FKAlertList
            alerts={alerts}
            onMarkRead={handleMarkAlertRead}
            loading={loading}
          />
        </TabPanel>

        {/* Blacklist Tab */}
        <TabPanel value={currentTab} index={2}>
          <FKBlacklistManager
            entries={blacklist}
            onAdd={handleAddToBlacklist}
            onRemove={handleRemoveFromBlacklist}
            canManage={isRiskManager}
            loading={loading}
          />
        </TabPanel>
      </Paper>

      {/* Evaluation Dialog */}
      <Dialog
        open={evalDialogOpen}
        onClose={() => setEvalDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Nueva Evaluación de Riesgo</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <FKRiskEvaluationForm
              onEvaluate={handleEvaluate}
              loading={evalLoading}
              error={evalError}
            />
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default RiskDashboard;
