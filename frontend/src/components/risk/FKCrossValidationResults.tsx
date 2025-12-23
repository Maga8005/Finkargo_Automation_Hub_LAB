/**
 * FKCrossValidationResults - Cross-validation discrepancy display component
 */
import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Collapse,
  IconButton,
  Paper,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  PlayArrow,
  Warning,
  Error as ErrorIcon,
  CheckCircle,
  ExpandMore,
  ExpandLess,
  Refresh,
  Info,
  PictureAsPdf,
} from '@mui/icons-material';
import { riskService } from '../../services/riskService';
import type {
  CrossValidationResponse,
  CrossValidationResult,
  DiscrepancySeverity,
  ClientInfo,
} from '../../types/risk';
import {
  DISCREPANCY_SEVERITY_CONFIG,
  VALIDATION_TYPE_LABELS,
  DOCUMENT_TYPE_CONFIG,
  VERIFICATION_STATUS_CONFIG,
} from '../../types/risk';
import { exportCrossValidationToPDF } from '../../utils/crossValidationPdfExport';

interface FKCrossValidationResultsProps {
  evaluationId: string;
  canValidate: boolean;
  onValidationComplete?: (response: CrossValidationResponse) => void;
  assessmentId?: string;
  clientNit?: string;
  clientInfo?: ClientInfo;
}

const FKCrossValidationResults: React.FC<FKCrossValidationResultsProps> = ({
  evaluationId,
  canValidate,
  onValidationComplete,
  assessmentId,
  clientNit,
  clientInfo,
}) => {
  // State
  const [results, setResults] = useState<CrossValidationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

  // Load existing results
  const loadResults = useCallback(async () => {
    if (!evaluationId) return;

    try {
      setLoading(true);
      const data = await riskService.getDiscrepancies(evaluationId);
      setResults(data);
    } catch {
      // No results yet is not an error
      console.debug('No validation results yet');
    } finally {
      setLoading(false);
    }
  }, [evaluationId]);

  // Trigger validation
  const handleValidate = async () => {
    try {
      setValidating(true);
      setError(null);
      setSuccess(null);

      const response = await riskService.triggerCrossValidation(evaluationId);
      setResults(response);
      onValidationComplete?.(response);

      // Show success message
      setSuccess('Validación cruzada completada. El puntaje de riesgo ha sido actualizado.');
    } catch (err) {
      console.error('Validation error:', err);
      const message = err instanceof Error ? err.message : 'Error en validación cruzada';
      setError(message);
    } finally {
      setValidating(false);
    }
  };

  // Handle PDF export
  const handleExportPDF = async () => {
    if (!results) return;

    try {
      setExporting(true);

      // Use assessment context from props or results
      const exportAssessmentId = assessmentId || results.assessment_id;
      const exportClientNit = clientNit || 'N/A';

      exportCrossValidationToPDF(results, {
        assessment_id: exportAssessmentId,
        client_nit: exportClientNit,
        client_info: clientInfo,
      });
    } catch (err) {
      console.error('PDF export error:', err);
      setError('Error al exportar PDF');
    } finally {
      setExporting(false);
    }
  };

  // Toggle result expansion
  const toggleExpanded = (resultId: string) => {
    setExpandedResults(prev => {
      const newSet = new Set(prev);
      if (newSet.has(resultId)) {
        newSet.delete(resultId);
      } else {
        newSet.add(resultId);
      }
      return newSet;
    });
  };

  // Get severity icon
  const getSeverityIcon = (severity?: DiscrepancySeverity) => {
    if (!severity) return <CheckCircle color="success" />;

    switch (severity) {
      case 'critical':
        return <ErrorIcon sx={{ color: '#CC071E' }} />;
      case 'high':
        return <ErrorIcon color="error" />;
      case 'medium':
        return <Warning color="warning" />;
      default:
        return <Info color="info" />;
    }
  };

  // Get document label from document type string
  const getDocumentLabel = (docType: string): string => {
    const config = DOCUMENT_TYPE_CONFIG[docType as keyof typeof DOCUMENT_TYPE_CONFIG];
    return config?.label || docType;
  };

  // Format value for display based on type
  const formatValueForDisplay = (value: unknown): string => {
    if (value === null || value === undefined) {
      return 'N/A';
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return 'N/A';
      }
      // Check if array of objects (like shareholders)
      if (typeof value[0] === 'object' && value[0] !== null) {
        const formatted = value.map((item, idx) => {
          // Try to get a meaningful name/identifier from the object
          const name = item.name || item.nombre || item.razon_social || `Item ${idx + 1}`;
          const percentage = item.percentage || item.porcentaje;
          if (percentage !== undefined && percentage !== null) {
            return `${name} (${percentage}%)`;
          }
          return name;
        });
        // Truncate if too many items
        if (formatted.length > 5) {
          return `${formatted.slice(0, 5).join(', ')} ... y ${formatted.length - 5} más`;
        }
        return formatted.join(', ');
      }
      // Array of primitives
      return value.join(', ');
    }

    if (typeof value === 'object') {
      // Single object - extract key info
      const obj = value as Record<string, unknown>;
      const name = obj.name || obj.nombre || obj.razon_social;
      if (name) {
        return String(name);
      }
      return JSON.stringify(value);
    }

    return String(value);
  };

  // Render values comparison
  const renderValuesComparison = (values: Record<string, unknown>) => {
    return (
      <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Documento</TableCell>
              <TableCell>Valor</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(values).map(([key, value]) => (
              <TableRow key={key}>
                <TableCell>
                  <Typography variant="body2">{getDocumentLabel(key)}</Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: 500 }}
                  >
                    {formatValueForDisplay(value)}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  // Render single result
  const renderResult = (result: CrossValidationResult, index: number) => {
    const resultId = result.id || `result-${index}`;
    const isExpanded = expandedResults.has(resultId);
    const severityConfig = result.severity
      ? DISCREPANCY_SEVERITY_CONFIG[result.severity]
      : null;

    return (
      <Box
        key={resultId}
        sx={{
          mb: 1,
          border: 1,
          borderColor: result.is_discrepancy
            ? severityConfig?.textColor || 'error.main'
            : 'success.main',
          borderRadius: 2,
          overflow: 'hidden',
        }}
      >
        {/* Result header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            p: 1.5,
            backgroundColor: result.is_discrepancy
              ? severityConfig?.bgColor || 'error.lighter'
              : 'success.lighter',
            cursor: 'pointer',
          }}
          onClick={() => toggleExpanded(resultId)}
        >
          {getSeverityIcon(result.severity)}

          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle2" sx={{ color: severityConfig?.textColor || 'success.main' }}>
              {VALIDATION_TYPE_LABELS[result.validation_type]}
              {result.field_compared && ` - ${result.field_compared}`}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Documentos: {result.documents_compared.map(getDocumentLabel).join(', ')}
            </Typography>
          </Box>

          {result.is_discrepancy && result.severity && (
            <Chip
              size="small"
              label={severityConfig?.label}
              sx={{
                backgroundColor: severityConfig?.bgColor,
                color: severityConfig?.textColor,
                fontWeight: 600,
              }}
            />
          )}

          {/* NOTE: Score impact chip removed - numeric scores hidden per stakeholder requirement */}

          <IconButton size="small">
            {isExpanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>

        {/* Expanded details */}
        <Collapse in={isExpanded}>
          <Box sx={{ p: 2, backgroundColor: 'background.paper' }}>
            {result.description && (
              <Alert
                severity={result.is_discrepancy ? 'warning' : 'success'}
                sx={{ mb: 2 }}
                icon={result.is_discrepancy ? <Warning /> : <CheckCircle />}
              >
                {result.description}
              </Alert>
            )}

            <Typography variant="subtitle2" gutterBottom>
              Valores encontrados:
            </Typography>
            {renderValuesComparison(result.values_found)}
          </Box>
        </Collapse>
      </Box>
    );
  };

  // Load on mount
  useEffect(() => {
    loadResults();
  }, [loadResults]);

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Validación Cruzada de Documentos
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {results && (
              <>
                <Button
                  size="small"
                  startIcon={<Refresh />}
                  onClick={loadResults}
                  disabled={loading}
                >
                  Actualizar
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  color="primary"
                  startIcon={exporting ? <CircularProgress size={16} color="inherit" /> : <PictureAsPdf />}
                  onClick={handleExportPDF}
                  disabled={exporting || !results}
                >
                  {exporting ? 'Exportando...' : 'Exportar PDF'}
                </Button>
              </>
            )}
            <Button
              variant="contained"
              color="primary"
              startIcon={validating ? <CircularProgress size={16} color="inherit" /> : <PlayArrow />}
              onClick={handleValidate}
              disabled={!canValidate || validating}
            >
              {validating ? 'Validando...' : 'Ejecutar Validación'}
            </Button>
          </Box>
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

        {!canValidate && !results && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Se requieren al menos 2 documentos procesados para ejecutar la validación cruzada.
          </Alert>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {results && !loading && (
          <>
            {/* Summary cards */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid size={{ xs: 6, md: 3 }}>
                <Paper
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    backgroundColor: results.total_discrepancies > 0 ? 'error.lighter' : 'success.lighter',
                  }}
                >
                  <Typography variant="h4" color={results.total_discrepancies > 0 ? 'error' : 'success'}>
                    {results.total_discrepancies}
                  </Typography>
                  <Typography variant="caption">Discrepancias</Typography>
                </Paper>
              </Grid>

              <Grid size={{ xs: 6, md: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#CC071E20' }}>
                  <Typography variant="h4" sx={{ color: '#CC071E' }}>
                    {results.critical_count}
                  </Typography>
                  <Typography variant="caption">Críticas</Typography>
                </Paper>
              </Grid>

              <Grid size={{ xs: 6, md: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#FFE4E4' }}>
                  <Typography variant="h4" color="error">
                    {results.high_count}
                  </Typography>
                  <Typography variant="caption">Altas</Typography>
                </Paper>
              </Grid>

              <Grid size={{ xs: 6, md: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#FFF4E5' }}>
                  <Typography variant="h4" color="warning.dark">
                    {results.medium_count + results.low_count}
                  </Typography>
                  <Typography variant="caption">Medias/Bajas</Typography>
                </Paper>
              </Grid>
            </Grid>

            {/* Binary verification status banner - replaces numeric score display */}
            {results.total_discrepancies > 0 ? (
              <Box
                sx={{
                  p: 3,
                  mb: 2,
                  borderRadius: 2,
                  backgroundColor: VERIFICATION_STATUS_CONFIG.requires_manual_verification.bgColor,
                  border: `2px solid ${VERIFICATION_STATUS_CONFIG.requires_manual_verification.textColor}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                }}
              >
                <Warning sx={{ fontSize: 40, color: VERIFICATION_STATUS_CONFIG.requires_manual_verification.textColor }} />
                <Box>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700, color: VERIFICATION_STATUS_CONFIG.requires_manual_verification.textColor }}
                  >
                    {VERIFICATION_STATUS_CONFIG.requires_manual_verification.label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Se encontraron {results.total_discrepancies} discrepancia{results.total_discrepancies !== 1 ? 's' : ''} que requieren verificación manual.
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Box
                sx={{
                  p: 3,
                  mb: 2,
                  borderRadius: 2,
                  backgroundColor: VERIFICATION_STATUS_CONFIG.pass.bgColor,
                  border: `2px solid ${VERIFICATION_STATUS_CONFIG.pass.textColor}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                }}
              >
                <CheckCircle sx={{ fontSize: 40, color: VERIFICATION_STATUS_CONFIG.pass.textColor }} />
                <Box>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700, color: VERIFICATION_STATUS_CONFIG.pass.textColor }}
                  >
                    {VERIFICATION_STATUS_CONFIG.pass.label} - Todos los datos son consistentes
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    No se encontraron discrepancias en la validación cruzada de documentos.
                  </Typography>
                </Box>
              </Box>
            )}

            {/* NOTE: Numeric score impact is intentionally hidden from UI per stakeholder requirement */}

            <Divider sx={{ my: 2 }} />

            {/* Results list */}
            <Typography variant="subtitle2" gutterBottom>
              Resultados de Validación ({results.results.length})
            </Typography>

            {/* Discrepancies first */}
            {results.results
              .filter(r => r.is_discrepancy)
              .sort((a, b) => {
                const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
                return (severityOrder[a.severity || 'low'] || 4) - (severityOrder[b.severity || 'low'] || 4);
              })
              .map((result, index) => renderResult(result, index))}

            {/* Passed validations */}
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              Validaciones Exitosas
            </Typography>
            {results.results
              .filter(r => !r.is_discrepancy)
              .map((result, index) => renderResult(result, index + 100))}

            {/* Validation timestamp */}
            {results.validated_at && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Última validación: {new Date(results.validated_at).toLocaleString('es-CO')}
              </Typography>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default FKCrossValidationResults;
