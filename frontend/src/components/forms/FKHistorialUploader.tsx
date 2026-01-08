/**
 * FKHistorialUploader - Historial de Pagos file upload component with drag & drop.
 *
 * Handles file selection, validation, and preview for the
 * Treasury payment template conversion feature.
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
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Collapse,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Error as ErrorIcon,
  Close as CloseIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import type { HistorialValidationResponse, CountryCode } from '../../types/tesoreria';
import treasuryService from '../../services/treasuryService';

interface FKHistorialUploaderProps {
  /** Target country for validation */
  country: CountryCode;
  /** Callback when upload and validation succeeds */
  onValidationSuccess: (response: HistorialValidationResponse, file: File) => void;
  /** Callback when upload fails */
  onValidationError: (error: string) => void;
  /** Maximum file size in MB (default: 10) */
  maxSizeMB?: number;
  /** Whether the uploader is disabled */
  disabled?: boolean;
}

/**
 * Historial de Pagos file uploader with drag & drop support.
 */
const FKHistorialUploader: React.FC<FKHistorialUploaderProps> = ({
  country,
  onValidationSuccess,
  onValidationError,
  maxSizeMB = 10,
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationResult, setValidationResult] = useState<HistorialValidationResponse | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [showColumnDetails, setShowColumnDetails] = useState(false);
  const [showConceptStats, setShowConceptStats] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  /**
   * Validate selected file.
   */
  const validateFile = useCallback(
    (file: File): string | null => {
      // Check file extension
      const fileName = file.name.toLowerCase();
      if (!fileName.endsWith('.xlsx')) {
        return 'Formato no válido. Solo se aceptan archivos .xlsx';
      }

      // Check file size
      if (file.size > maxSizeBytes) {
        return `El archivo excede el tamaño máximo de ${maxSizeMB}MB`;
      }

      return null;
    },
    [maxSizeBytes, maxSizeMB]
  );

  /**
   * Handle file selection from input or drop.
   */
  const handleFileSelect = useCallback(
    (file: File) => {
      setFileError(null);
      setValidationResult(null);

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

      if (disabled) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [disabled, handleFileSelect]
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
    setValidationResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  /**
   * Upload file to backend for validation.
   */
  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setValidationResult(null);
    setFileError(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const response = await treasuryService.validateHistorial(selectedFile, country);

      clearInterval(progressInterval);
      setUploadProgress(100);

      setValidationResult(response);

      if (response.success) {
        onValidationSuccess(response, selectedFile);
      } else if (response.errors.length > 0) {
        const criticalErrors = response.errors.filter(e => e.row === 0);
        if (criticalErrors.length > 0) {
          onValidationError(`Errores de validación: ${criticalErrors.length} columnas requeridas no encontradas`);
        }
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            'Error al cargar el archivo';
      setFileError(errorMessage);
      onValidationError(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [selectedFile, country, onValidationSuccess, onValidationError]);

  /**
   * Format file size for display.
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  /**
   * Format currency amount.
   */
  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('es-CO', {
      style: 'decimal',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <Box>
      {/* Drop zone */}
      <Paper
        elevation={isDragging ? 4 : 1}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        sx={{
          p: 4,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragging
            ? 'primary.main'
            : fileError
              ? 'error.main'
              : validationResult?.success
                ? 'success.main'
                : 'grey.300',
          borderRadius: 2,
          backgroundColor: isDragging
            ? 'action.hover'
            : disabled
              ? 'grey.100'
              : 'background.paper',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: disabled ? 'grey.300' : 'primary.main',
            backgroundColor: disabled ? 'grey.100' : 'action.hover',
          },
        }}
        onClick={!disabled && !selectedFile ? handleBrowseClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx"
          onChange={handleInputChange}
          style={{ display: 'none' }}
          disabled={disabled}
        />

        {!selectedFile ? (
          <>
            <CloudUploadIcon
              sx={{
                fontSize: 48,
                color: isDragging ? 'primary.main' : 'grey.400',
                mb: 2,
              }}
            />
            <Typography variant="h6" gutterBottom>
              Arrastra tu archivo Historial de Pagos aquí
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              o haz clic para seleccionar
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Formato: .xlsx | Máximo: {maxSizeMB}MB
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
              <FileIcon color={validationResult?.success ? 'success' : 'primary'} />
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

            {uploading && (
              <Box sx={{ width: '100%', mb: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="caption" color="text.secondary">
                  {uploadProgress < 100 ? 'Validando...' : 'Completado'}
                </Typography>
              </Box>
            )}

            {!validationResult && !uploading && (
              <Button
                variant="contained"
                onClick={(e) => {
                  e.stopPropagation();
                  handleUpload();
                }}
                disabled={uploading || disabled}
                startIcon={<CloudUploadIcon />}
              >
                Validar Archivo
              </Button>
            )}
          </Box>
        )}
      </Paper>

      {/* File error */}
      {fileError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {fileError}
        </Alert>
      )}

      {/* Validation Result */}
      {validationResult && (
        <Box sx={{ mt: 2 }}>
          {validationResult.success ? (
            <Alert severity="success" sx={{ mb: 2 }}>
              <AlertTitle>Archivo validado correctamente</AlertTitle>
              <Typography variant="body2">
                {validationResult.total_rows} filas encontradas •{' '}
                {validationResult.valid_rows} filas válidas •{' '}
                {validationResult.estimated_output_rows} filas de salida estimadas
              </Typography>
            </Alert>
          ) : (
            <Alert severity="error" sx={{ mb: 2 }}>
              <AlertTitle>Errores de validación</AlertTitle>
              <Typography variant="body2">
                Se encontraron {validationResult.errors.length} errores que deben corregirse
              </Typography>
            </Alert>
          )}

          {/* Column Validation Status */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box
              sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
              onClick={() => setShowColumnDetails(!showColumnDetails)}
            >
              <Typography variant="subtitle2" sx={{ flex: 1 }}>
                Estado de Columnas Requeridas
              </Typography>
              <Chip
                label={`${validationResult.column_status.filter(c => c.found).length}/${validationResult.column_status.length}`}
                size="small"
                color={validationResult.column_status.every(c => c.found) ? 'success' : 'warning'}
              />
              {showColumnDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </Box>

            <Collapse in={showColumnDetails}>
              <List dense sx={{ mt: 1 }}>
                {validationResult.column_status.map((col, idx) => (
                  <ListItem key={idx} disableGutters>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      {col.found ? (
                        <CheckCircleIcon color="success" fontSize="small" />
                      ) : (
                        <ErrorIcon color="error" fontSize="small" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={col.column_name}
                      secondary={col.found ? `Encontrada como: ${col.source_column}` : 'No encontrada'}
                    />
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </Paper>

          {/* Concept Statistics */}
          {validationResult.concept_stats.length > 0 && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box
                sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                onClick={() => setShowConceptStats(!showConceptStats)}
              >
                <Typography variant="subtitle2" sx={{ flex: 1 }}>
                  Estadísticas por Concepto
                </Typography>
                <Chip
                  label={`${validationResult.concept_stats.length} conceptos`}
                  size="small"
                  color="primary"
                />
                {showConceptStats ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </Box>

              <Collapse in={showConceptStats}>
                <TableContainer sx={{ mt: 1 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Concepto</TableCell>
                        <TableCell align="right">Filas</TableCell>
                        <TableCell align="right">Total</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {validationResult.concept_stats.map((stat, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{stat.concept_type}</TableCell>
                          <TableCell align="right">{stat.count}</TableCell>
                          <TableCell align="right">{formatAmount(stat.total_amount)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Collapse>
            </Paper>
          )}

          {/* Validation Errors */}
          {validationResult.errors.length > 0 && (
            <Alert
              severity={validationResult.errors.some(e => e.row === 0) ? 'error' : 'warning'}
              sx={{ mt: 2 }}
            >
              <AlertTitle>
                {validationResult.errors.some(e => e.row === 0)
                  ? 'Errores críticos'
                  : 'Advertencias'}
              </AlertTitle>
              <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
                {validationResult.errors.slice(0, 20).map((error, index) => (
                  <ListItem key={index} disableGutters>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      {error.row === 0 ? (
                        <ErrorIcon color="error" fontSize="small" />
                      ) : (
                        <WarningIcon color="warning" fontSize="small" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography variant="body2">
                          {error.row > 0 && <strong>Fila {error.row}, </strong>}
                          <strong>{error.column}:</strong> {error.message}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
                {validationResult.errors.length > 20 && (
                  <ListItem disableGutters>
                    <ListItemText
                      primary={
                        <Typography variant="body2" color="text.secondary">
                          ... y {validationResult.errors.length - 20} errores más
                        </Typography>
                      }
                    />
                  </ListItem>
                )}
              </List>
            </Alert>
          )}
        </Box>
      )}
    </Box>
  );
};

export default FKHistorialUploader;
