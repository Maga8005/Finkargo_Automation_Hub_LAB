/**
 * RiskEvaluationDetail - Detailed evaluation view page
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import {
  ArrowBack,
  Business,
  Person,
  LocationCity,
  AccountBalance,
  Description,
  CompareArrows,
  Assessment,
  Info,
} from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';
import { riskService } from '../../services/riskService';
import FKRiskScoreCard from '../../components/risk/FKRiskScoreCard';
import FKDocumentUploader from '../../components/risk/FKDocumentUploader';
import FKCrossValidationResults from '../../components/risk/FKCrossValidationResults';
import type {
  RiskAssessmentDetail,
  RiskDecisionRequest,
  CrossValidationResponse,
} from '../../types/risk';
import { ASSESSMENT_STATUS_CONFIG } from '../../types/risk';

const RiskEvaluationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { userProfile } = useAuth();

  // State
  const [assessment, setAssessment] = useState<RiskAssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [decisionStatus, setDecisionStatus] = useState<'approved' | 'rejected' | 'escalated'>('approved');
  const [decisionNotes, setDecisionNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [validationReady, setValidationReady] = useState(false);
  const [validationResults, setValidationResults] = useState<CrossValidationResponse | null>(null);
  const [scoreUpdatedMessage, setScoreUpdatedMessage] = useState<string | null>(null);

  // Check if user is risk manager
  const isRiskManager = userProfile?.role === 'risk_manager' || userProfile?.role === 'admin';

  // Check if decision can be made
  const canMakeDecision = isRiskManager &&
    assessment &&
    ['pending', 'in_progress', 'escalated'].includes(assessment.status);

  // Check if score is preliminary (pending_documents status)
  const isPreliminaryScore = assessment?.status === 'pending_documents';

  // Load assessment
  const loadAssessment = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      const data = await riskService.getEvaluation(id);
      setAssessment(data);
    } catch (err) {
      console.error('Error loading assessment:', err);
      setError('Error al cargar la evaluación');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadAssessment();
  }, [loadAssessment]);

  // Handle validation complete - refresh assessment and show success message
  const handleValidationComplete = useCallback(async (results: CrossValidationResponse) => {
    setValidationResults(results);
    // Refresh assessment to get updated score
    await loadAssessment();
    // Show success message
    setScoreUpdatedMessage('Puntaje de riesgo actualizado con resultados de validación cruzada');
    // Auto-hide message after 5 seconds
    setTimeout(() => setScoreUpdatedMessage(null), 5000);
  }, [loadAssessment]);

  // Handle decision submission
  const handleSubmitDecision = async () => {
    if (!id || !assessment) return;

    try {
      setSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      const request: RiskDecisionRequest = {
        status: decisionStatus,
        notes: decisionNotes || undefined,
      };

      const updated = await riskService.submitDecision(id, request);
      setAssessment(updated);
      setSubmitSuccess(true);
      setDecisionNotes('');
    } catch (err: unknown) {
      console.error('Error submitting decision:', err);
      const message = err instanceof Error ? err.message : 'Error al enviar la decisión';
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  // Format date for display
  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Format currency
  const formatCurrency = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !assessment) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error || 'Evaluación no encontrada'}</Alert>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/risk/dashboard')}
          sx={{ mt: 2 }}
        >
          Volver al Dashboard
        </Button>
      </Box>
    );
  }

  const statusConfig = ASSESSMENT_STATUS_CONFIG[assessment.status];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/risk/dashboard')}>
          <ArrowBack />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              {assessment.assessment_id}
            </Typography>
            <Chip
              label={statusConfig.label}
              color={statusConfig.color}
            />
          </Box>
          <Typography variant="body2" color="text.secondary">
            Evaluación creada el {formatDate(assessment.created_at)}
          </Typography>
        </Box>
      </Box>

      {submitSuccess && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSubmitSuccess(false)}>
          Decisión registrada exitosamente
        </Alert>
      )}

      {submitError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setSubmitError(null)}>
          {submitError}
        </Alert>
      )}

      {scoreUpdatedMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setScoreUpdatedMessage(null)}>
          {scoreUpdatedMessage}
        </Alert>
      )}

      {isPreliminaryScore && (
        <Alert
          severity="info"
          icon={<Info />}
          sx={{ mb: 3 }}
        >
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            Suba y valide documentos para calcular el puntaje final de riesgo
          </Typography>
          <Typography variant="caption" color="text.secondary">
            El puntaje actual es preliminar y se actualizará después de la validación cruzada de documentos.
          </Typography>
        </Alert>
      )}

      {/* Tabs Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab
            icon={<Assessment />}
            iconPosition="start"
            label="Evaluación"
          />
          <Tab
            icon={<Description />}
            iconPosition="start"
            label="Documentos"
          />
          <Tab
            icon={<CompareArrows />}
            iconPosition="start"
            label={`Validación Cruzada${validationResults ? ` (${validationResults.total_discrepancies})` : ''}`}
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          {/* Left Column - Client Info */}
          <Grid size={{ xs: 12, md: 4 }}>
            {/* Client Info Card */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Información del Cliente
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Business color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">NIT</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {assessment.client_nit}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Business color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Empresa</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {assessment.client_info?.nombre_importador || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Person color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Representante Legal</Typography>
                      <Typography variant="body2">
                        {assessment.client_info?.representante_legal || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocationCity color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Ciudad</Typography>
                      <Typography variant="body2">
                        {assessment.client_info?.ciudad_domicilio || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AccountBalance color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Cupo</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {formatCurrency(assessment.client_info?.cupo_plataforma)}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>

            {/* Audit Info */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Historial
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Evaluado por</Typography>
                    <Typography variant="body2">
                      {assessment.assessed_by || 'Sistema'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(assessment.assessed_at)}
                    </Typography>
                  </Box>

                  {assessment.reviewed_by && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">Revisado por</Typography>
                      <Typography variant="body2">
                        {assessment.reviewed_by}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(assessment.reviewed_at)}
                      </Typography>
                    </Box>
                  )}

                  {assessment.review_notes && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">Notas de revisión</Typography>
                      <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                        "{assessment.review_notes}"
                      </Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Center Column - Risk Score */}
          <Grid size={{ xs: 12, md: 4 }}>
            <FKRiskScoreCard
              score={Number(assessment.risk_score)}
              level={assessment.risk_level}
              indicators={assessment.fraud_indicators}
              isPreliminary={isPreliminaryScore}
            />
          </Grid>

          {/* Right Column - Decision */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Decisión
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {canMakeDecision ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth>
                      <InputLabel>Acción</InputLabel>
                      <Select
                        value={decisionStatus}
                        label="Acción"
                        onChange={(e) => setDecisionStatus(e.target.value as typeof decisionStatus)}
                        disabled={submitting}
                      >
                        <MenuItem value="approved">
                          Aprobar - Cliente aprobado
                        </MenuItem>
                        <MenuItem value="rejected">
                          Rechazar - Cliente rechazado
                        </MenuItem>
                        <MenuItem value="escalated">
                          Escalar - Requiere revisión adicional
                        </MenuItem>
                      </Select>
                    </FormControl>

                    <TextField
                      label="Notas (opcional)"
                      multiline
                      rows={4}
                      value={decisionNotes}
                      onChange={(e) => setDecisionNotes(e.target.value)}
                      disabled={submitting}
                      placeholder="Agregue notas o comentarios sobre su decisión..."
                    />

                    <Button
                      variant="contained"
                      color={
                        decisionStatus === 'approved' ? 'success' :
                        decisionStatus === 'rejected' ? 'error' : 'warning'
                      }
                      onClick={handleSubmitDecision}
                      disabled={submitting}
                      fullWidth
                    >
                      {submitting ? (
                        <CircularProgress size={24} color="inherit" />
                      ) : (
                        `Confirmar ${
                          decisionStatus === 'approved' ? 'Aprobación' :
                          decisionStatus === 'rejected' ? 'Rechazo' : 'Escalamiento'
                        }`
                      )}
                    </Button>
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    {['approved', 'rejected'].includes(assessment.status) ? (
                      <>
                        <Chip
                          label={statusConfig.label}
                          color={statusConfig.color}
                          sx={{ fontSize: '1rem', py: 2, px: 3 }}
                        />
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                          Esta evaluación ya fue procesada
                        </Typography>
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Solo los Risk Managers pueden tomar decisiones
                      </Typography>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Documents Tab */}
      {activeTab === 1 && id && (
        <FKDocumentUploader
          evaluationId={id}
          evaluationStatus={assessment?.status}
          onValidationReady={setValidationReady}
        />
      )}

      {/* Cross-Validation Tab */}
      {activeTab === 2 && id && (
        <FKCrossValidationResults
          evaluationId={id}
          canValidate={validationReady}
          onValidationComplete={handleValidationComplete}
          assessmentId={assessment?.assessment_id}
          clientNit={assessment?.client_nit}
          clientInfo={assessment?.client_info}
        />
      )}
    </Box>
  );
};

export default RiskEvaluationDetail;
