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

interface FKDocumentUploaderProps {
  evaluationId: string;
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
  onExtractionComplete,
  onValidationReady,
}) => {
  // State
  const [extractions, setExtractions] = useState<DocumentExtractionList | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

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

  // Render extracted data preview
  const renderExtractedData = (data: Record<string, unknown>) => {
    const displayFields = Object.entries(data).slice(0, 6);

    return (
      <Box sx={{ mt: 1, pl: 2 }}>
        {displayFields.map(([key, value]) => (
          <Typography key={key} variant="caption" display="block" color="text.secondary">
            <strong>{key.replace(/_/g, ' ')}:</strong> {String(value) || 'N/A'}
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
          <Button
            size="small"
            startIcon={<Refresh />}
            onClick={loadExtractions}
            disabled={loading}
          >
            Actualizar
          </Button>
        </Box>

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
                          ref={el => (fileInputRefs.current[docType] = el)}
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
      </CardContent>
    </Card>
  );
};

export default FKDocumentUploader;
