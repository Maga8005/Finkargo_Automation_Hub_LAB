/**
 * FKFinalizeButton - Finalization button with requirements checklist
 *
 * This component displays the finalization status and allows users to
 * finalize an evaluation after meeting all requirements.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  PlayArrow,
  ErrorOutline,
  AssignmentTurnedIn,
} from '@mui/icons-material';
import { riskService } from '../../services/riskService';
import type { FinalizationStatus, RiskAssessmentDetail } from '../../types/risk';

interface FKFinalizeButtonProps {
  evaluationId: string;
  evaluationStatus?: string;
  onFinalizationComplete?: (assessment: RiskAssessmentDetail) => void;
  crossValidationDone?: boolean;
}

const FKFinalizeButton: React.FC<FKFinalizeButtonProps> = ({
  evaluationId,
  evaluationStatus,
  onFinalizationComplete,
  crossValidationDone = false,
}) => {
  // State
  const [status, setStatus] = useState<FinalizationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Load finalization status
  const loadStatus = useCallback(async () => {
    if (!evaluationId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await riskService.getFinalizationStatus(evaluationId);
      setStatus(data);
    } catch (err) {
      console.error('Error loading finalization status:', err);
      // Don't show error for loading - just disable button
    } finally {
      setLoading(false);
    }
  }, [evaluationId]);

  // Handle finalization
  const handleFinalize = async () => {
    setShowConfirmDialog(false);

    try {
      setFinalizing(true);
      setError(null);
      setSuccess(null);

      const result = await riskService.finalizeEvaluation(evaluationId, {
        force_complete: false,
      });

      setSuccess('Evaluación finalizada exitosamente');
      onFinalizationComplete?.(result);

      // Reload status
      await loadStatus();
    } catch (err: unknown) {
      console.error('Error finalizing evaluation:', err);
      const message = err instanceof Error ? err.message : 'Error al finalizar la evaluación';
      setError(message);
    } finally {
      setFinalizing(false);
    }
  };

  // Check if finalization is allowed based on status
  const canShowButton = [
    'pending_documents',
    'pending_finalization',
  ].includes(evaluationStatus || '');

  // Load status on mount and when cross-validation status changes
  useEffect(() => {
    if (canShowButton) {
      loadStatus();
    }
  }, [loadStatus, canShowButton, crossValidationDone]);

  // Don't render if evaluation is not in correct state
  if (!canShowButton) {
    return null;
  }

  // Get requirements status
  const requirements = status?.requirements;
  const canFinalize = status?.can_finalize || false;
  const pendingItems = status?.pending_items || [];

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <AssignmentTurnedIn color="primary" />
          <Typography variant="h6">
            Finalizar Evaluación
          </Typography>
          {status?.current_status && (
            <Chip
              size="small"
              label={
                status.current_status === 'pending_documents'
                  ? 'Pendiente Documentos'
                  : 'Listo para Finalizar'
              }
              color={status.current_status === 'pending_finalization' ? 'success' : 'warning'}
            />
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          <>
            {/* Requirements checklist */}
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
              Requisitos para Finalización:
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  {requirements?.min_documents_met ? (
                    <CheckCircle color="success" fontSize="small" />
                  ) : (
                    <ErrorOutline color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary="Documentos subidos (mínimo 2)"
                  secondary={requirements?.min_documents_met ? 'Completado' : 'Pendiente'}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  {requirements?.cross_validation_done ? (
                    <CheckCircle color="success" fontSize="small" />
                  ) : (
                    <ErrorOutline color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary="Validación cruzada ejecutada"
                  secondary={requirements?.cross_validation_done ? 'Completado' : 'Pendiente'}
                />
              </ListItem>
              {/* Optional requirements - distinguish "no items" vs "all validated" */}
              <ListItem>
                <ListItemIcon>
                  {/* Email chains: Show different status based on count */}
                  {(requirements?.email_chain_count ?? 0) === 0 ? (
                    // No email chains uploaded - show as optional/not started
                    <Warning color="warning" fontSize="small" />
                  ) : requirements?.email_chains_validated ? (
                    // Has items and all validated
                    <CheckCircle color="success" fontSize="small" />
                  ) : (
                    // Has items but not all validated
                    <ErrorOutline color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary="Cadenas de correo validadas"
                  secondary={
                    (requirements?.email_chain_count ?? 0) === 0
                      ? 'Opcional - No hay cadenas'
                      : requirements?.email_chains_validated
                        ? 'Completado'
                        : `Pendiente (${requirements?.email_chain_validated_count ?? 0}/${requirements?.email_chain_count ?? 0})`
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  {/* External contacts: Show different status based on count */}
                  {(requirements?.external_contact_count ?? 0) === 0 ? (
                    // No external contacts uploaded - show as optional/not started
                    <Warning color="warning" fontSize="small" />
                  ) : requirements?.external_contacts_validated ? (
                    // Has items and all validated
                    <CheckCircle color="success" fontSize="small" />
                  ) : (
                    // Has items but not all validated
                    <ErrorOutline color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary="Contactos externos validados"
                  secondary={
                    (requirements?.external_contact_count ?? 0) === 0
                      ? 'Opcional - No hay contactos'
                      : requirements?.external_contacts_validated
                        ? 'Completado'
                        : `Pendiente (${requirements?.external_contact_validated_count ?? 0}/${requirements?.external_contact_count ?? 0})`
                  }
                />
              </ListItem>
            </List>

            {/* Pending items warning */}
            {pendingItems.length > 0 && !canFinalize && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  Items pendientes:
                </Typography>
                <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                  {pendingItems.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Finalize button */}
            <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                startIcon={
                  finalizing ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : (
                    <PlayArrow />
                  )
                }
                onClick={() => setShowConfirmDialog(true)}
                disabled={finalizing || !canFinalize}
                sx={{
                  flex: 1,
                  py: 1.5,
                  fontWeight: 600,
                }}
              >
                {finalizing ? 'Finalizando...' : 'Finalizar Evaluación'}
              </Button>
            </Box>

          </>
        )}

        {/* Confirmation Dialog */}
        <Dialog open={showConfirmDialog} onClose={() => setShowConfirmDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            Confirmar Finalización
          </DialogTitle>
          <DialogContent>
            <Typography variant="body1" gutterBottom>
              ¿Está seguro de que desea finalizar esta evaluación?
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Esta acción ejecutará:
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle color="primary" fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Verificación de lista negra" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle color="primary" fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Análisis de indicadores de fraude" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle color="primary" fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Agregación de resultados de validación" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle color="primary" fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="Cálculo del puntaje final de riesgo" />
              </ListItem>
            </List>

          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowConfirmDialog(false)}>
              Cancelar
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={handleFinalize}
              disabled={!canFinalize}
            >
              Confirmar Finalización
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default FKFinalizeButton;
