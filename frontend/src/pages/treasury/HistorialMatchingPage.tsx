/**
 * HistorialMatchingPage - Main page for Declaration-Historial matching workflow.
 *
 * Implements a 4-step workflow using MUI Stepper:
 * 1. Upload files (Historial de Pagos + Declaration inventory)
 * 2. Configure matching parameters
 * 3. Review and adjust match results
 * 4. Download enriched Excel
 */
import React, { useState, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Button,
  Alert,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  NavigateNext as NextIcon,
  NavigateBefore as BackIcon,
  Download as DownloadIcon,
  PlayArrow as RunIcon,
} from '@mui/icons-material';

import FKHistorialMatchingUploader from '../../components/treasury/FKHistorialMatchingUploader';
import FKMatchingConfigForm from '../../components/treasury/FKMatchingConfigForm';
import FKMatchResultsTable from '../../components/treasury/FKMatchResultsTable';
import FKManualMatchDialog from '../../components/treasury/FKManualMatchDialog';
import FKMatchStatisticsCard from '../../components/treasury/FKMatchStatisticsCard';
import treasuryMatchingService from '../../services/treasuryMatchingService';

import type {
  MatchConfig,
  HistorialUploadResponse,
  DeclarationInventoryUploadResponse,
  MatchingSessionResponse,
  PaymentGroup,
} from '../../types/treasuryMatching';
import { DEFAULT_MATCH_CONFIG } from '../../types/treasuryMatching';

const STEPS = [
  {
    label: 'Cargar Archivos',
    description: 'Suba el Historial de Pagos y el inventario de declaraciones',
  },
  {
    label: 'Configurar Parametros',
    description: 'Ajuste los parametros de tolerancia para la coincidencia',
  },
  {
    label: 'Revisar Resultados',
    description: 'Revise y ajuste las coincidencias encontradas',
  },
  {
    label: 'Descargar',
    description: 'Descargue el archivo enriquecido con las declaraciones',
  },
];

// Session error message shown when session is lost
const SESSION_EXPIRED_MESSAGE =
  'La sesion ha expirado o el servidor fue reiniciado. Por favor, vuelva a cargar el archivo de Historial de Pagos para continuar.';

// Helper to check if error is a 404 session error
const isSessionError = (err: unknown): boolean => {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { status?: number } }).response;
    return response?.status === 404;
  }
  return false;
};

const HistorialMatchingPage: React.FC = () => {
  // Workflow state
  const [activeStep, setActiveStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data state
  const [uploadResponse, setUploadResponse] = useState<HistorialUploadResponse | null>(null);
  const [declarationsResponse, setDeclarationsResponse] =
    useState<DeclarationInventoryUploadResponse | null>(null);
  const [matchConfig, setMatchConfig] = useState<MatchConfig>(DEFAULT_MATCH_CONFIG);
  const [matchingResponse, setMatchingResponse] = useState<MatchingSessionResponse | null>(null);

  // Manual match dialog state
  const [manualMatchDialogOpen, setManualMatchDialogOpen] = useState(false);
  const [selectedGroupForOverride, setSelectedGroupForOverride] = useState<PaymentGroup | null>(
    null
  );

  // Reset session and workflow state when session is lost
  const resetSession = useCallback(() => {
    setSessionId(null);
    setUploadResponse(null);
    setDeclarationsResponse(null);
    setMatchingResponse(null);
    setActiveStep(0);
    setManualMatchDialogOpen(false);
    setSelectedGroupForOverride(null);
  }, []);

  // Upload handlers
  const handleHistorialUpload = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);

    try {
      const response = await treasuryMatchingService.uploadHistorial(file);
      setUploadResponse(response);
      setSessionId(response.session_id);

      if (!response.success) {
        setError('Error al procesar el archivo de Historial de Pagos');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al cargar archivo';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDeclarationsUpload = useCallback(
    async (file: File) => {
      // Validate session before attempting upload
      if (!sessionId) {
        setError('No hay sesion activa. Por favor, primero suba el archivo de Historial de Pagos.');
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await treasuryMatchingService.uploadDeclarations(sessionId, file);
        setDeclarationsResponse(response);

        if (!response.success) {
          setError('Error al procesar el inventario de declaraciones');
        }
      } catch (err) {
        // Handle 404 session errors specifically
        if (isSessionError(err)) {
          setError(SESSION_EXPIRED_MESSAGE);
          resetSession();
        } else {
          const errorMessage = err instanceof Error ? err.message : 'Error al cargar archivo';
          setError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    },
    [sessionId, resetSession]
  );

  // Execute matching
  const handleExecuteMatching = useCallback(async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await treasuryMatchingService.executeMatching(sessionId, matchConfig);
      setMatchingResponse(response);
      setActiveStep(2); // Move to results step
    } catch (err) {
      // Handle 404 session errors specifically
      if (isSessionError(err)) {
        setError(SESSION_EXPIRED_MESSAGE);
        resetSession();
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Error al ejecutar coincidencias';
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [sessionId, matchConfig, resetSession]);

  // Manual override handlers
  const handleOpenOverrideDialog = useCallback(
    (groupId: string) => {
      const result = matchingResponse?.results.find((r) => r.group_id === groupId);
      if (result) {
        setSelectedGroupForOverride(result.payment_group);
        setManualMatchDialogOpen(true);
      }
    },
    [matchingResponse]
  );

  const handleConfirmOverride = useCallback(
    async (declarationId: string) => {
      if (!sessionId || !selectedGroupForOverride) return;

      setLoading(true);
      setError(null);

      try {
        await treasuryMatchingService.overrideMatch({
          session_id: sessionId,
          group_id: selectedGroupForOverride.group_id,
          declaration_id: declarationId,
        });

        // Refresh results
        const response = await treasuryMatchingService.getResults(sessionId);
        setMatchingResponse(response);
        setManualMatchDialogOpen(false);
        setSelectedGroupForOverride(null);
      } catch (err) {
        // Handle 404 session errors specifically
        if (isSessionError(err)) {
          setError(SESSION_EXPIRED_MESSAGE);
          resetSession();
        } else {
          const errorMessage = err instanceof Error ? err.message : 'Error al asignar declaracion';
          setError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    },
    [sessionId, selectedGroupForOverride, resetSession]
  );

  const handleClearMatch = useCallback(
    async (groupId: string) => {
      if (!sessionId) return;

      setLoading(true);
      setError(null);

      try {
        await treasuryMatchingService.overrideMatch({
          session_id: sessionId,
          group_id: groupId,
          declaration_id: undefined,
        });

        // Refresh results
        const response = await treasuryMatchingService.getResults(sessionId);
        setMatchingResponse(response);
      } catch (err) {
        // Handle 404 session errors specifically
        if (isSessionError(err)) {
          setError(SESSION_EXPIRED_MESSAGE);
          resetSession();
        } else {
          const errorMessage = err instanceof Error ? err.message : 'Error al quitar coincidencia';
          setError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    },
    [sessionId, resetSession]
  );

  // Download handler
  const handleDownload = useCallback(async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const blob = await treasuryMatchingService.downloadEnrichedExcel(sessionId);
      const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const filename = `Historial_Enriquecido_${timestamp}.xlsx`;
      treasuryMatchingService.downloadBlob(blob, filename);
    } catch (err) {
      // Handle 404 session errors specifically
      if (isSessionError(err)) {
        setError(SESSION_EXPIRED_MESSAGE);
        resetSession();
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Error al descargar archivo';
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  }, [sessionId, resetSession]);

  // Navigation
  const canProceedToStep2 =
    uploadResponse?.success && declarationsResponse?.success && sessionId;
  const canDownload = matchingResponse?.success;

  const handleNext = () => {
    if (activeStep === 1) {
      handleExecuteMatching();
    } else {
      setActiveStep((prev) => Math.min(prev + 1, STEPS.length - 1));
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => Math.max(prev - 1, 0));
  };

  const isNextDisabled = () => {
    if (loading) return true;
    if (activeStep === 0) return !canProceedToStep2;
    if (activeStep === 1) return !canProceedToStep2;
    if (activeStep === 2) return false;
    return true;
  };

  // Render step content
  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <FKHistorialMatchingUploader
            onHistorialUpload={handleHistorialUpload}
            onDeclarationsUpload={handleDeclarationsUpload}
            historialResponse={uploadResponse}
            declarationsResponse={declarationsResponse}
            loading={loading}
            sessionId={sessionId}
          />
        );

      case 1:
        return (
          <FKMatchingConfigForm
            config={matchConfig}
            onChange={setMatchConfig}
            groupCount={uploadResponse?.group_count || 0}
            declarationCount={declarationsResponse?.total_declarations || 0}
          />
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <FKMatchStatisticsCard
              statistics={matchingResponse?.statistics || null}
              loading={loading}
            />
            <FKMatchResultsTable
              results={matchingResponse?.results || []}
              onOverride={handleOpenOverrideDialog}
              onClearMatch={handleClearMatch}
              loading={loading}
            />
          </Box>
        );

      case 3:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h5" gutterBottom>
              Archivo Listo para Descargar
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              El archivo Historial de Pagos enriquecido con las columnas de Declaracion de Cambio
              esta listo para descargar.
            </Typography>

            {matchingResponse?.statistics && (
              <Box sx={{ mb: 4 }}>
                <Alert severity="success" sx={{ display: 'inline-flex' }}>
                  <Typography>
                    <strong>{matchingResponse.statistics.matched_groups}</strong> de{' '}
                    <strong>{matchingResponse.statistics.total_payment_groups}</strong> grupos de
                    pago tienen declaracion asignada (
                    {matchingResponse.statistics.match_percentage.toFixed(1)}%)
                  </Typography>
                </Alert>
              </Box>
            )}

            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
              onClick={handleDownload}
              disabled={loading || !canDownload}
            >
              Descargar Excel Enriquecido
            </Button>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Coincidencia Declaraciones - Historial de Pagos
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Asocie automaticamente las declaraciones de cambio con los registros del historial de pagos
      </Typography>

      {/* Stepper */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Stepper activeStep={activeStep}>
          {STEPS.map((step) => (
            <Step key={step.label}>
              <StepLabel
                optional={
                  <Typography variant="caption" color="text.secondary">
                    {step.description}
                  </Typography>
                }
              >
                {step.label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Step Content */}
      <Box sx={{ mb: 4 }}>{renderStepContent()}</Box>

      {/* Navigation Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={handleBack}
          disabled={activeStep === 0 || loading}
        >
          Anterior
        </Button>

        {activeStep < STEPS.length - 1 && (
          <Button
            variant="contained"
            endIcon={
              loading ? (
                <CircularProgress size={20} color="inherit" />
              ) : activeStep === 1 ? (
                <RunIcon />
              ) : (
                <NextIcon />
              )
            }
            onClick={handleNext}
            disabled={isNextDisabled()}
          >
            {activeStep === 1 ? 'Ejecutar Coincidencias' : 'Siguiente'}
          </Button>
        )}
      </Box>

      {/* Manual Match Dialog */}
      <FKManualMatchDialog
        open={manualMatchDialogOpen}
        onClose={() => {
          setManualMatchDialogOpen(false);
          setSelectedGroupForOverride(null);
        }}
        onConfirm={handleConfirmOverride}
        paymentGroup={selectedGroupForOverride}
        declarations={declarationsResponse?.declarations || []}
        loading={loading}
      />
    </Container>
  );
};

export default HistorialMatchingPage;
