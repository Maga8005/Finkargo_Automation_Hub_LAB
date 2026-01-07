/**
 * FKContractUpload - Contract file upload component with extraction preview.
 *
 * Handles file selection, validation, and extraction for broker contracts.
 * Supports PDF and DOCX files with drag & drop functionality.
 * Offers both standard (regex) and AI (LandingAI) extraction methods.
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Alert,
  AlertTitle,
  Grid,
  TextField,
  Chip,
  IconButton,
  Card,
  CardContent,
  CardActions,
  InputAdornment,
  RadioGroup,
  Radio,
  FormControlLabel,
  FormControl,
  FormLabel,
  FormHelperText,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Description as FileIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  AutoAwesome as AIIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';

import { alianzasService } from '../../services/alianzasService';
import type { BrokerContractData, ExtractionMethod, AIExtractionStatus } from '../../types/alianzas';
import { AI_EXTRACTION_STATUS_LABELS } from '../../types/alianzas';

// Accepted file formats (constant to avoid dependency issues)
const ACCEPTED_FORMATS = ['.pdf', '.docx'];
// For AI extraction, only PDF is supported
const AI_ACCEPTED_FORMATS = ['.pdf'];

// AI extraction steps for progress stepper
const AI_EXTRACTION_STEPS = [
  { status: 'uploading' as const, label: 'Subir documento' },
  { status: 'parsing' as const, label: 'Convertir a texto' },
  { status: 'extracting' as const, label: 'Extraer datos' },
  { status: 'complete' as const, label: 'Completado' },
];

interface FKContractUploadProps {
  /** Callback when extraction succeeds and user clicks "Apply to Form" */
  onExtracted: (data: BrokerContractData) => void;
  /** Callback when extraction fails */
  onError?: (error: string) => void;
  /** Maximum file size in MB (default: 10) */
  maxSizeMB?: number;
  /** Whether the uploader is disabled */
  disabled?: boolean;
}

/**
 * Contract file uploader with extraction preview.
 */
const FKContractUpload: React.FC<FKContractUploadProps> = ({
  onExtracted,
  onError,
  maxSizeMB = 10,
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [extractedData, setExtractedData] = useState<BrokerContractData | null>(null);
  const [editedData, setEditedData] = useState<BrokerContractData | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [extractionMethod, setExtractionMethod] = useState<ExtractionMethod>('standard');
  const [aiStatus, setAiStatus] = useState<AIExtractionStatus>('idle');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  /**
   * Get the current AI extraction step index for the stepper.
   */
  const getAIStepIndex = (): number => {
    const stepIndex = AI_EXTRACTION_STEPS.findIndex((step) => step.status === aiStatus);
    return stepIndex >= 0 ? stepIndex : 0;
  };

  /**
   * Validate selected file.
   */
  const validateFile = useCallback(
    (file: File): string | null => {
      const fileName = file.name.toLowerCase();
      const acceptedFormats =
        extractionMethod === 'ai' ? AI_ACCEPTED_FORMATS : ACCEPTED_FORMATS;
      const hasValidExtension = acceptedFormats.some((format) =>
        fileName.endsWith(format.toLowerCase())
      );

      if (!hasValidExtension) {
        if (extractionMethod === 'ai') {
          return 'La extracción IA solo soporta archivos PDF.';
        }
        return `Formato no válido. Use: ${acceptedFormats.join(', ')}`;
      }

      if (file.size > maxSizeBytes) {
        return `El archivo excede el tamaño máximo de ${maxSizeMB}MB`;
      }

      return null;
    },
    [maxSizeBytes, maxSizeMB, extractionMethod]
  );

  /**
   * Handle file selection from input or drop.
   */
  const handleFileSelect = useCallback(
    (file: File) => {
      setFileError(null);
      setExtractedData(null);
      setEditedData(null);
      setAiStatus('idle');

      const error = validateFile(file);
      if (error) {
        setFileError(error);
        return;
      }

      setSelectedFile(file);
    },
    [validateFile]
  );

  /**
   * Handle drag events.
   */
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (disabled || uploading) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [disabled, uploading, handleFileSelect]
  );

  /**
   * Handle file input change.
   */
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  /**
   * Trigger file input click.
   */
  const handleBrowseClick = useCallback(() => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, []);

  /**
   * Clear selected file.
   */
  const handleClearFile = useCallback(() => {
    setSelectedFile(null);
    setFileError(null);
    setExtractedData(null);
    setEditedData(null);
    setAiStatus('idle');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  /**
   * Handle extraction method change.
   */
  const handleExtractionMethodChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newMethod = e.target.value as ExtractionMethod;
      setExtractionMethod(newMethod);
      setFileError(null);
      setExtractedData(null);
      setEditedData(null);
      setAiStatus('idle');

      // Re-validate selected file with new method
      if (selectedFile) {
        const fileName = selectedFile.name.toLowerCase();
        if (newMethod === 'ai' && !fileName.endsWith('.pdf')) {
          setFileError('La extracción IA solo soporta archivos PDF. Por favor seleccione un PDF.');
          setSelectedFile(null);
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        }
      }
    },
    [selectedFile]
  );

  /**
   * Upload and extract contract data using standard method.
   */
  const handleStandardExtract = useCallback(async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setFileError(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 15, 85));
      }, 200);

      const response = await alianzasService.extractContract(selectedFile);

      clearInterval(progressInterval);
      setUploadProgress(100);

      setExtractedData(response);
      setEditedData(response);

      if ((response.extraction_confidence ?? 0) === 0) {
        setFileError(
          'No se pudieron extraer datos del contrato. Considere usar extracción IA para documentos escaneados.'
        );
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            'Error al procesar el contrato';
      setFileError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [selectedFile, onError]);

  /**
   * Upload and extract contract data using AI method.
   */
  const handleAIExtract = useCallback(async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setFileError(null);
    setAiStatus('uploading');

    try {
      // Simulate uploading phase
      setUploadProgress(10);
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Simulate parsing phase
      setAiStatus('parsing');
      setUploadProgress(30);

      // Start AI extraction (this takes 30-60 seconds)
      const extractPromise = alianzasService.extractContractAI(selectedFile);

      // Simulate progress during extraction
      setAiStatus('extracting');
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 2, 85));
      }, 1000);

      const response = await extractPromise;

      clearInterval(progressInterval);
      setUploadProgress(100);
      setAiStatus('complete');

      setExtractedData(response);
      setEditedData(response);

      // Check for low confidence warning
      if ((response.extraction_confidence ?? 0) < 0.3) {
        setFileError(
          'La extracción IA obtuvo baja confianza. Verifique los datos extraídos.'
        );
      }
    } catch (error: unknown) {
      setAiStatus('error');

      // Parse error message
      let errorMessage = 'Error en extracción IA';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else {
        const axiosError = error as {
          response?: { data?: { detail?: string }; status?: number };
          code?: string;
        };
        if (axiosError.code === 'ECONNABORTED' || axiosError.code === 'ERR_NETWORK') {
          errorMessage = 'La extracción IA está tomando demasiado tiempo. Intente de nuevo.';
        } else if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail;
        }
      }

      setFileError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [selectedFile, onError]);

  /**
   * Upload and extract contract data based on selected method.
   */
  const handleExtract = useCallback(async () => {
    if (extractionMethod === 'ai') {
      await handleAIExtract();
    } else {
      await handleStandardExtract();
    }
  }, [extractionMethod, handleAIExtract, handleStandardExtract]);

  /**
   * Apply extracted data to form.
   */
  const handleApplyToForm = useCallback(() => {
    if (editedData) {
      onExtracted(editedData);
    }
  }, [editedData, onExtracted]);

  /**
   * Update editable field.
   */
  const handleFieldChange = (field: keyof BrokerContractData, value: string | number | null) => {
    if (!editedData) return;
    setEditedData({
      ...editedData,
      [field]: value,
    });
  };

  /**
   * Format file size for display.
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  /**
   * Get confidence color based on value.
   */
  const getConfidenceColor = (confidence: number): 'success' | 'warning' | 'error' => {
    if (confidence >= 0.6) return 'success';
    if (confidence >= 0.3) return 'warning';
    return 'error';
  };

  // Check if form controls should be disabled
  const isDisabled = disabled || uploading;

  return (
    <Box>
      {/* Extraction Method Selection */}
      <FormControl component="fieldset" sx={{ mb: 2 }} disabled={isDisabled}>
        <FormLabel component="legend">Método de Extracción</FormLabel>
        <RadioGroup
          row
          value={extractionMethod}
          onChange={handleExtractionMethodChange}
        >
          <FormControlLabel
            value="standard"
            control={<Radio size="small" />}
            label="Estándar"
          />
          <FormControlLabel
            value="ai"
            control={<Radio size="small" />}
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <AIIcon fontSize="small" color="primary" />
                <span>IA (para escaneados)</span>
              </Box>
            }
          />
        </RadioGroup>
        {extractionMethod === 'ai' && (
          <FormHelperText sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TimerIcon fontSize="small" />
            La extracción IA toma 30-60 segundos. Solo soporta PDF.
          </FormHelperText>
        )}
      </FormControl>

      {/* Drop zone */}
      <Paper
        elevation={isDragging ? 4 : 1}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        sx={{
          p: 3,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragging
            ? 'primary.main'
            : fileError
              ? 'error.main'
              : 'grey.300',
          borderRadius: 2,
          backgroundColor: isDragging
            ? 'action.hover'
            : isDisabled
              ? 'grey.100'
              : 'background.paper',
          cursor: isDisabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: isDisabled ? 'grey.300' : 'primary.main',
            backgroundColor: isDisabled ? 'grey.100' : 'action.hover',
          },
        }}
        onClick={!isDisabled && !selectedFile ? handleBrowseClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={extractionMethod === 'ai' ? AI_ACCEPTED_FORMATS.join(',') : ACCEPTED_FORMATS.join(',')}
          onChange={handleInputChange}
          style={{ display: 'none' }}
          disabled={isDisabled}
        />

        {!selectedFile ? (
          <>
            <CloudUploadIcon
              sx={{
                fontSize: 40,
                color: isDragging ? 'primary.main' : 'grey.400',
                mb: 1,
              }}
            />
            <Typography variant="subtitle1" gutterBottom>
              Arrastra tu contrato aquí
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              o haz clic para seleccionar
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Formatos: {extractionMethod === 'ai' ? 'PDF' : ACCEPTED_FORMATS.join(', ')} | Máximo: {maxSizeMB}MB
            </Typography>
          </>
        ) : (
          <Box>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 1,
                mb: 2,
              }}
            >
              <FileIcon color="primary" />
              <Typography variant="body1" fontWeight="medium">
                {selectedFile.name}
              </Typography>
              <Chip
                label={formatFileSize(selectedFile.size)}
                size="small"
                variant="outlined"
              />
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClearFile();
                }}
                disabled={uploading}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>

            {uploading && extractionMethod === 'standard' && (
              <Box sx={{ width: '100%', mb: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="caption" color="text.secondary">
                  {uploadProgress < 100 ? 'Extrayendo datos...' : 'Completado'}
                </Typography>
              </Box>
            )}

            {uploading && extractionMethod === 'ai' && (
              <Box sx={{ width: '100%', mb: 2 }}>
                <Stepper activeStep={getAIStepIndex()} alternativeLabel sx={{ mb: 2 }}>
                  {AI_EXTRACTION_STEPS.map((step) => (
                    <Step key={step.status}>
                      <StepLabel>{step.label}</StepLabel>
                    </Step>
                  ))}
                </Stepper>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {AI_EXTRACTION_STATUS_LABELS[aiStatus]}
                </Typography>
              </Box>
            )}

            {!extractedData && !uploading && (
              <Button
                variant="contained"
                onClick={(e) => {
                  e.stopPropagation();
                  handleExtract();
                }}
                disabled={uploading || disabled}
                startIcon={extractionMethod === 'ai' ? <AIIcon /> : <CloudUploadIcon />}
              >
                {extractionMethod === 'ai' ? 'Extraer con IA' : 'Extraer Datos'}
              </Button>
            )}
          </Box>
        )}
      </Paper>

      {/* File error */}
      {fileError && (
        <Alert
          severity={
            (extractedData?.extraction_confidence ?? 0) === 0 ||
            (extractedData?.extraction_confidence ?? 0) < 0.3
              ? 'warning'
              : 'error'
          }
          sx={{ mt: 2 }}
          action={
            (extractedData?.extraction_confidence ?? 0) === 0 &&
            extractionMethod === 'standard' && (
              <Button
                color="inherit"
                size="small"
                startIcon={<AIIcon />}
                onClick={() => setExtractionMethod('ai')}
              >
                Usar IA
              </Button>
            )
          }
        >
          <AlertTitle>
            {(extractedData?.extraction_confidence ?? 0) === 0
              ? 'Extracción parcial'
              : (extractedData?.extraction_confidence ?? 0) < 0.3
                ? 'Baja confianza'
                : 'Error'}
          </AlertTitle>
          {fileError}
        </Alert>
      )}

      {/* Extraction results */}
      {extractedData && editedData && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
              <Typography variant="subtitle1" fontWeight="medium">
                Datos Extraídos
              </Typography>
              <Chip
                icon={
                  (extractedData.extraction_confidence ?? 0) >= 0.5 ? (
                    <CheckCircleIcon />
                  ) : (
                    <WarningIcon />
                  )
                }
                label={`${Math.round((extractedData.extraction_confidence ?? 0) * 100)}% confianza`}
                color={getConfidenceColor(extractedData.extraction_confidence ?? 0)}
                size="small"
              />
              <Chip
                icon={extractedData.extraction_method === 'ai' ? <AIIcon /> : undefined}
                label={`Método: ${extractedData.extraction_method === 'ai' ? 'IA' : 'Estándar'}`}
                variant="outlined"
                size="small"
                color={extractedData.extraction_method === 'ai' ? 'primary' : 'default'}
              />
            </Box>

            <Grid container spacing={2}>
              {/* Broker Name */}
              <Grid size={{ xs: 12 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Nombre del Broker"
                  value={editedData.nombre_broker ?? ''}
                  onChange={(e) => handleFieldChange('nombre_broker', e.target.value || null)}
                />
              </Grid>

              {/* Opening Commission */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="% Comisión Apertura"
                  type="number"
                  value={editedData.porcentaje_comision_apertura ?? ''}
                  onChange={(e) =>
                    handleFieldChange(
                      'porcentaje_comision_apertura',
                      e.target.value ? parseFloat(e.target.value) : null
                    )
                  }
                  InputProps={{
                    endAdornment: <InputAdornment position="end">%</InputAdornment>,
                  }}
                  inputProps={{ step: '0.01', min: 0, max: 100 }}
                />
              </Grid>

              {/* Operational Commission */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="% Comisión Operativa"
                  type="number"
                  value={editedData.porcentaje_comision_operativa ?? ''}
                  onChange={(e) =>
                    handleFieldChange(
                      'porcentaje_comision_operativa',
                      e.target.value ? parseFloat(e.target.value) : null
                    )
                  }
                  InputProps={{
                    endAdornment: <InputAdornment position="end">%</InputAdornment>,
                  }}
                  inputProps={{ step: '0.001', min: 0, max: 100 }}
                />
              </Grid>

              {/* Bank */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Banco"
                  value={editedData.banco ?? ''}
                  onChange={(e) => handleFieldChange('banco', e.target.value || null)}
                />
              </Grid>

              {/* Bank Account */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Cuenta Bancaria (CLABE)"
                  value={editedData.cuenta_bancaria ?? ''}
                  onChange={(e) => handleFieldChange('cuenta_bancaria', e.target.value || null)}
                />
              </Grid>

              {/* RFC */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="RFC"
                  value={editedData.rfc_broker ?? ''}
                  onChange={(e) => handleFieldChange('rfc_broker', e.target.value || null)}
                />
              </Grid>

              {/* Contract Date */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Fecha Contrato"
                  type="date"
                  value={editedData.fecha_contrato ?? ''}
                  onChange={(e) => handleFieldChange('fecha_contrato', e.target.value || null)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              {/* Contract Duration */}
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Vigencia (meses)"
                  type="number"
                  value={editedData.vigencia_meses ?? ''}
                  onChange={(e) =>
                    handleFieldChange(
                      'vigencia_meses',
                      e.target.value ? parseInt(e.target.value, 10) : null
                    )
                  }
                  inputProps={{ min: 0, max: 120 }}
                />
              </Grid>
            </Grid>
          </CardContent>

          <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
            <Button variant="outlined" onClick={handleClearFile}>
              Cancelar
            </Button>
            <Button variant="contained" onClick={handleApplyToForm}>
              Aplicar al Formulario
            </Button>
          </CardActions>
        </Card>
      )}
    </Box>
  );
};

export default FKContractUpload;
