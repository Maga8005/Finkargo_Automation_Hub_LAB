/**
 * FKDocumentUploader - Document upload and AI extraction component
 */
import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Grid,
  LinearProgress,
  Collapse,
  Snackbar,
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  Error,
  HourglassEmpty,
  Refresh,
  ExpandMore,
  ExpandLess,
  Info,
  Download,
} from '@mui/icons-material';
import { riskService } from '../../services/riskService';
import type {
  DocumentType,
  DocumentExtraction,
  DocumentExtractionList,
} from '../../types/risk';
import {
  DOCUMENT_TYPE_CONFIG,
  EXTRACTION_STATUS_CONFIG,
} from '../../types/risk';
import {
  exportDocumentExtractionsToExcel,
  hasExportableExtractions,
} from '../../utils/riskExcelExport';

interface FKDocumentUploaderProps {
  evaluationId: string;
  evaluationStatus?: string;
  clientNit?: string;
  onExtractionComplete?: (extractions: DocumentExtraction[]) => void;
  onValidationReady?: (ready: boolean) => void;
}

interface UploadState {
  [key: string]: {
    file?: File;
    uploading: boolean;
    extracting: boolean;
    error?: string;
  };
}

const FKDocumentUploader: React.FC<FKDocumentUploaderProps> = ({
  evaluationId,
  evaluationStatus,
  clientNit,
  onExtractionComplete,
  onValidationReady,
}) => {
  // Check if score is preliminary (pending_documents status)
  const isPendingDocuments = evaluationStatus === 'pending_documents';
  // State
  const [extractions, setExtractions] = useState<DocumentExtractionList | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  // File input refs for each document type
  const fileInputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({});

  // Document types in order
  const documentTypes: DocumentType[] = [
    'financial_statement_current',
    'financial_statement_prior',
    'cedula',
    'composicion_accionaria',
    'rut',
    'certificado_existencia',
  ];

  // Load current extractions
  const loadExtractions = useCallback(async () => {
    if (!evaluationId) return;

    try {
      setLoading(true);
      const data = await riskService.getExtractions(evaluationId);
      setExtractions(data);

      // Check if ready for validation
      const completedCount = data.extractions.filter(
        e => e.extraction_status === 'completed'
      ).length;
      onValidationReady?.(completedCount >= 2);

      // Notify parent of completed extractions
      if (data.completed_count > 0) {
        onExtractionComplete?.(data.extractions.filter(e => e.extraction_status === 'completed'));
      }
    } catch (err) {
      console.error('Error loading extractions:', err);
      setError('Error al cargar documentos');
    } finally {
      setLoading(false);
    }
  }, [evaluationId, onExtractionComplete, onValidationReady]);

  // Handle file selection
  const handleFileSelect = async (docType: DocumentType, file: File) => {
    const config = DOCUMENT_TYPE_CONFIG[docType];

    // Validate file type
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !config.accepted_formats.includes(extension)) {
      setError(`Formato no válido para ${config.label}. Formatos aceptados: ${config.accepted_formats.join(', ')}`);
      return;
    }

    // Validate file size
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > config.max_size_mb) {
      setError(`Archivo muy grande. Máximo: ${config.max_size_mb}MB`);
      return;
    }

    setError(null);

    // Update upload state
    setUploadState(prev => ({
      ...prev,
      [docType]: { file, uploading: true, extracting: false },
    }));

    try {
      // Upload document
      const response = await riskService.uploadDocument(evaluationId, docType, file);

      setUploadState(prev => ({
        ...prev,
        [docType]: { file, uploading: false, extracting: false },
      }));

      // Refresh extractions list
      await loadExtractions();

      // If we got an extraction ID, start processing
      if (response.id) {
        await processExtraction(docType, response.id, file);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setUploadState(prev => ({
        ...prev,
        [docType]: {
          file,
          uploading: false,
          extracting: false,
          error: 'Error al subir documento',
        },
      }));
    }
  };

  // Process extraction for a document
  const processExtraction = async (docType: DocumentType, extractionId: string, file: File) => {
    setUploadState(prev => ({
      ...prev,
      [docType]: { ...prev[docType], extracting: true, error: undefined },
    }));

    try {
      await riskService.processExtraction(evaluationId, extractionId, file);
      await loadExtractions();

      setUploadState(prev => ({
        ...prev,
        [docType]: { ...prev[docType], extracting: false },
      }));
    } catch (err) {
      console.error('Extraction error:', err);
      setUploadState(prev => ({
        ...prev,
        [docType]: {
          ...prev[docType],
          extracting: false,
          error: 'Error en extracción AI',
        },
      }));
    }
  };

  // Get extraction for a document type
  const getExtraction = (docType: DocumentType): DocumentExtraction | undefined => {
    return extractions?.extractions.find(e => e.document_type === docType);
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'processing':
        return <CircularProgress size={20} />;
      default:
        return <HourglassEmpty color="action" />;
    }
  };

  // Handle click on upload button
  const handleUploadClick = (docType: DocumentType) => {
    fileInputRefs.current[docType]?.click();
  };

  // Handle retry extraction
  const handleRetry = async (docType: DocumentType) => {
    const extraction = getExtraction(docType);
    const state = uploadState[docType];

    if (extraction && state?.file) {
      await processExtraction(docType, extraction.id, state.file);
    }
  };

  // Toggle expanded view
  const toggleExpanded = (docType: string) => {
    setExpandedDoc(prev => (prev === docType ? null : docType));
  };

  // Handle export to Excel
  const handleExportToExcel = () => {
    if (!extractions) return;

    setExporting(true);
    setExportSuccess(false);

    try {
      const success = exportDocumentExtractionsToExcel(
        extractions,
        evaluationId,
        clientNit
      );

      if (success) {
        setExportSuccess(true);
        // Clear success message after 3 seconds
        setTimeout(() => setExportSuccess(false), 3000);
      } else {
        setError('No hay datos extraídos para exportar');
      }
    } catch (err) {
      console.error('Export error:', err);
      setError('Error al exportar datos a Excel');
    } finally {
      setExporting(false);
    }
  };

  // Check if export is available
  const canExport = hasExportableExtractions(extractions);

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

  // Render extracted data preview
  const renderExtractedData = (data: Record<string, unknown>) => {
    const displayFields = Object.entries(data).slice(0, 6);

    return (
      <Box sx={{ mt: 1, pl: 2 }}>
        {displayFields.map(([key, value]) => (
          <Typography key={key} variant="caption" display="block" color="text.secondary">
            <strong>{key.replace(/_/g, ' ')}:</strong> {formatValueForDisplay(value)}
          </Typography>
        ))}
        {Object.keys(data).length > 6 && (
          <Typography variant="caption" color="text.secondary">
            ... y {Object.keys(data).length - 6} campos más
          </Typography>
        )}
      </Box>
    );
  };

  // Initialize on mount
  React.useEffect(() => {
    loadExtractions();
  }, [loadExtractions]);

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Documentos para Validación Cruzada
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip
              title={canExport ? 'Exportar datos extraídos a Excel' : 'No hay datos extraídos para exportar'}
            >
              <span>
                <Button
                  size="small"
                  startIcon={exporting ? <CircularProgress size={16} /> : <Download />}
                  onClick={handleExportToExcel}
                  disabled={!canExport || exporting}
                  color={exportSuccess ? 'success' : 'primary'}
                >
                  {exportSuccess ? 'Exportado' : 'Exportar a Excel'}
                </Button>
              </span>
            </Tooltip>
            <Button
              size="small"
              startIcon={<Refresh />}
              onClick={loadExtractions}
              disabled={loading}
            >
              Actualizar
            </Button>
          </Box>
        </Box>

        {isPendingDocuments && (
          <Alert severity="info" icon={<Info />} sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              Suba documentos y ejecute la validación cruzada para calcular el puntaje final de riesgo
            </Typography>
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {extractions && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress
              variant="determinate"
              value={(extractions.completed_count / documentTypes.length) * 100}
              sx={{ mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              {extractions.completed_count} de {documentTypes.length} documentos procesados
            </Typography>
          </Box>
        )}

        <Grid container spacing={2}>
          {documentTypes.map(docType => {
            const config = DOCUMENT_TYPE_CONFIG[docType];
            const extraction = getExtraction(docType);
            const state = uploadState[docType];
            const isUploading = state?.uploading;
            const isExtracting = state?.extracting;
            const hasError = state?.error || extraction?.extraction_status === 'failed';
            const isCompleted = extraction?.extraction_status === 'completed';
            const isExpanded = expandedDoc === docType;

            return (
              <Grid size={{ xs: 12, md: 6 }} key={docType}>
                <Box
                  sx={{
                    border: 1,
                    borderColor: hasError
                      ? 'error.main'
                      : isCompleted
                        ? 'success.main'
                        : 'divider',
                    borderRadius: 2,
                    p: 2,
                    backgroundColor: hasError
                      ? 'error.lighter'
                      : isCompleted
                        ? 'success.lighter'
                        : 'background.paper',
                  }}
                >
                  {/* Document Header */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Description color="action" />
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle2">
                        {config.label}
                        {config.required && (
                          <Typography component="span" color="error" sx={{ ml: 0.5 }}>
                            *
                          </Typography>
                        )}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {config.accepted_formats.join(', ').toUpperCase()} - Máx {config.max_size_mb}MB
                      </Typography>
                    </Box>

                    {/* Status indicator */}
                    {extraction && (
                      <Chip
                        size="small"
                        label={EXTRACTION_STATUS_CONFIG[extraction.extraction_status].label}
                        color={EXTRACTION_STATUS_CONFIG[extraction.extraction_status].color}
                        icon={getStatusIcon(extraction.extraction_status)}
                      />
                    )}
                  </Box>

                  {/* File info or upload */}
                  <Box sx={{ mt: 2 }}>
                    {extraction?.document_filename ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {extraction.document_filename}
                        </Typography>

                        {isCompleted && extraction.extracted_data && (
                          <Tooltip title="Ver datos extraídos">
                            <IconButton size="small" onClick={() => toggleExpanded(docType)}>
                              {isExpanded ? <ExpandLess /> : <ExpandMore />}
                            </IconButton>
                          </Tooltip>
                        )}

                        {hasError && (
                          <Tooltip title="Reintentar extracción">
                            <IconButton size="small" onClick={() => handleRetry(docType)}>
                              <Refresh />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    ) : (
                      <Box>
                        <input
                          type="file"
                          ref={el => { fileInputRefs.current[docType] = el; }}
                          style={{ display: 'none' }}
                          accept={config.accepted_formats.map(f => `.${f}`).join(',')}
                          onChange={e => {
                            const file = e.target.files?.[0];
                            if (file) handleFileSelect(docType, file);
                          }}
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={isUploading || isExtracting ? <CircularProgress size={16} /> : <CloudUpload />}
                          onClick={() => handleUploadClick(docType)}
                          disabled={isUploading || isExtracting}
                          fullWidth
                        >
                          {isUploading
                            ? 'Subiendo...'
                            : isExtracting
                              ? 'Extrayendo...'
                              : 'Subir Documento'}
                        </Button>
                      </Box>
                    )}

                    {/* Extraction progress */}
                    {isExtracting && (
                      <Box sx={{ mt: 1 }}>
                        <LinearProgress />
                        <Typography variant="caption" color="text.secondary">
                          Extrayendo datos con AI (30-60 segundos)...
                        </Typography>
                      </Box>
                    )}

                    {/* Error message */}
                    {hasError && (
                      <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                        {state?.error || extraction?.extraction_errors?.join(', ') || 'Error en extracción'}
                      </Typography>
                    )}

                    {/* Confidence score */}
                    {isCompleted && extraction?.extraction_confidence && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Confianza: {(extraction.extraction_confidence * 100).toFixed(0)}%
                      </Typography>
                    )}
                  </Box>

                  {/* Expanded extracted data */}
                  <Collapse in={isExpanded}>
                    {extraction?.extracted_data && renderExtractedData(extraction.extracted_data)}
                  </Collapse>
                </Box>
              </Grid>
            );
          })}
        </Grid>

        {/* Action buttons */}
        {extractions && extractions.completed_count >= 2 && (
          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Typography variant="body2" color="success.main">
              {extractions.completed_count} documentos listos para validación cruzada
            </Typography>
          </Box>
        )}

        {/* Export success snackbar */}
        <Snackbar
          open={exportSuccess}
          autoHideDuration={3000}
          onClose={() => setExportSuccess(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert severity="success" variant="filled" onClose={() => setExportSuccess(false)}>
            Archivo Excel descargado exitosamente
          </Alert>
        </Snackbar>
      </CardContent>
    </Card>
  );
};

export default FKDocumentUploader;
