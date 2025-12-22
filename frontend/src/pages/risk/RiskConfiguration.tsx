/**
 * RiskConfiguration - Rules and threshold configuration page
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Slider,
  Switch,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Save,
  Refresh,
  Info,
} from '@mui/icons-material';
import { riskService } from '../../services/riskService';
import type {
  FraudDetectionRule,
  RuleUpdateRequest,
  RuleType,
} from '../../types/risk';

// Rule type labels
const RULE_TYPE_LABELS: Record<RuleType, string> = {
  identity: 'Identidad',
  email: 'Email',
  document: 'Documento',
  nit: 'NIT',
  address: 'Dirección',
  financial: 'Financiero',
  history: 'Historial',
};

interface EditedRule {
  weight: number;
  threshold: number;
  is_active: boolean;
}

const RiskConfiguration: React.FC = () => {
  // State
  const [rules, setRules] = useState<FraudDetectionRule[]>([]);
  const [editedRules, setEditedRules] = useState<Record<string, EditedRule>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load rules
  const loadRules = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await riskService.getRules();
      setRules(data);

      // Initialize edited rules
      const edited: Record<string, EditedRule> = {};
      data.forEach((rule) => {
        edited[rule.id] = {
          weight: Number(rule.weight) * 100,
          threshold: Number(rule.threshold),
          is_active: rule.is_active,
        };
      });
      setEditedRules(edited);
    } catch (err) {
      console.error('Error loading rules:', err);
      setError('Error al cargar las reglas');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  // Handle value changes
  const handleWeightChange = (ruleId: string, value: number) => {
    setEditedRules((prev) => ({
      ...prev,
      [ruleId]: {
        ...prev[ruleId],
        weight: value,
      },
    }));
  };

  const handleThresholdChange = (ruleId: string, value: string) => {
    const numValue = parseFloat(value) || 0;
    setEditedRules((prev) => ({
      ...prev,
      [ruleId]: {
        ...prev[ruleId],
        threshold: Math.min(100, Math.max(0, numValue)),
      },
    }));
  };

  const handleActiveChange = (ruleId: string, value: boolean) => {
    setEditedRules((prev) => ({
      ...prev,
      [ruleId]: {
        ...prev[ruleId],
        is_active: value,
      },
    }));
  };

  // Check if rule has been modified
  const isModified = (rule: FraudDetectionRule): boolean => {
    const edited = editedRules[rule.id];
    if (!edited) return false;

    return (
      Math.abs(edited.weight - Number(rule.weight) * 100) > 0.01 ||
      Math.abs(edited.threshold - Number(rule.threshold)) > 0.01 ||
      edited.is_active !== rule.is_active
    );
  };

  // Save rule changes
  const handleSaveRule = async (rule: FraudDetectionRule) => {
    const edited = editedRules[rule.id];
    if (!edited) return;

    try {
      setSaving(rule.id);
      setError(null);
      setSuccess(null);

      const updates: RuleUpdateRequest = {
        weight: edited.weight / 100,
        threshold: edited.threshold,
        is_active: edited.is_active,
      };

      const updated = await riskService.updateRule(rule.id, updates);

      // Update rules list
      setRules((prev) =>
        prev.map((r) => (r.id === rule.id ? updated : r))
      );

      setSuccess(`Regla "${rule.rule_name}" actualizada`);
    } catch (err) {
      console.error('Error saving rule:', err);
      setError(`Error al guardar la regla: ${rule.rule_name}`);
    } finally {
      setSaving(null);
    }
  };

  // Calculate total weight
  const totalWeight = Object.values(editedRules)
    .filter((_, index) => rules[index]?.is_active !== false)
    .reduce((sum, rule) => sum + (rule.is_active ? rule.weight : 0), 0);

  if (loading) {
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
            Configuración de Reglas de Detección
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Ajuste los pesos y umbrales de las reglas de detección de fraude
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={loadRules}
          disabled={loading}
        >
          Recargar
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Weight Summary */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="subtitle1">
            Peso Total de Reglas Activas:
          </Typography>
          <Chip
            label={`${totalWeight.toFixed(0)}%`}
            color={Math.abs(totalWeight - 100) < 1 ? 'success' : 'warning'}
            sx={{ fontWeight: 600 }}
          />
          {Math.abs(totalWeight - 100) >= 1 && (
            <Typography variant="body2" color="warning.main">
              Se recomienda que el peso total sea 100%
            </Typography>
          )}
        </Box>
      </Paper>

      {/* Rules Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Regla</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Descripción</TableCell>
              <TableCell sx={{ width: 200 }}>Peso (%)</TableCell>
              <TableCell sx={{ width: 100 }}>Umbral</TableCell>
              <TableCell align="center">Activa</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rules.map((rule) => {
              const edited = editedRules[rule.id];
              const modified = isModified(rule);

              return (
                <TableRow
                  key={rule.id}
                  sx={{
                    backgroundColor: modified ? 'action.hover' : 'inherit',
                    opacity: edited?.is_active !== false ? 1 : 0.6,
                  }}
                >
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {rule.rule_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={RULE_TYPE_LABELS[rule.rule_type] || rule.rule_type}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title={rule.description || ''}>
                      <Typography
                        variant="body2"
                        sx={{
                          maxWidth: 250,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {rule.description || 'Sin descripción'}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ px: 1 }}>
                      <Slider
                        value={edited?.weight ?? Number(rule.weight) * 100}
                        onChange={(_, value) => handleWeightChange(rule.id, value as number)}
                        min={0}
                        max={50}
                        step={1}
                        disabled={!edited?.is_active || saving === rule.id}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(value) => `${value}%`}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
                        {edited?.weight?.toFixed(0) ?? (Number(rule.weight) * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <TextField
                      type="number"
                      value={edited?.threshold ?? rule.threshold}
                      onChange={(e) => handleThresholdChange(rule.id, e.target.value)}
                      disabled={!edited?.is_active || saving === rule.id}
                      size="small"
                      inputProps={{
                        min: 0,
                        max: 100,
                        step: 1,
                      }}
                      sx={{ width: 80 }}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Switch
                      checked={edited?.is_active ?? rule.is_active}
                      onChange={(e) => handleActiveChange(rule.id, e.target.checked)}
                      disabled={saving === rule.id}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      color="primary"
                      onClick={() => handleSaveRule(rule)}
                      disabled={!modified || saving === rule.id}
                    >
                      {saving === rule.id ? (
                        <CircularProgress size={20} />
                      ) : (
                        <Save />
                      )}
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Threshold Info */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Info color="info" />
          <Typography variant="subtitle1">
            Umbrales de Nivel de Riesgo
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Box>
            <Chip label="Bajo" color="success" size="small" sx={{ mr: 1 }} />
            <Typography variant="body2" component="span">0 - 30 puntos</Typography>
          </Box>
          <Box>
            <Chip label="Medio" color="warning" size="small" sx={{ mr: 1 }} />
            <Typography variant="body2" component="span">31 - 60 puntos</Typography>
          </Box>
          <Box>
            <Chip label="Alto" color="error" size="small" sx={{ mr: 1, backgroundColor: '#E65100' }} />
            <Typography variant="body2" component="span">61 - 80 puntos</Typography>
          </Box>
          <Box>
            <Chip label="Crítico" color="error" size="small" sx={{ mr: 1 }} />
            <Typography variant="body2" component="span">81 - 100 puntos</Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default RiskConfiguration;
