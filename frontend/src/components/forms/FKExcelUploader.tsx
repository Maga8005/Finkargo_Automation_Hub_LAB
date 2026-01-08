/**
 * FKExcelUploader - Excel file upload component with drag & drop.
 *
 * Handles file selection, validation, and upload for the
 * Facturación MX automation feature.
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
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Error as ErrorIcon,
  Close as CloseIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import type { ExcelValidationResponse, ExcelValidationError } from '../../types/finance';
import financeService from '../../services/financeService';

interface FKExcelUploaderProps {
  /** Callback when upload and validation succeeds */
  onUploadSuccess: (response: ExcelValidationResponse) => void;
  /** Callback when upload fails */
  onUploadError: (error: string) => void;
  /** Maximum file size in MB (default: 10) */
  maxSizeMB?: number;
  /** Accepted file formats (default: .xlsx, .xls) */
  acceptedFormats?: string[];
  /** Whether the uploader is disabled */
  disabled?: boolean;
}

/**
 * Excel file uploader with drag & drop support.
 */
const FKExcelUploader: React.FC<FKExcelUploaderProps> = ({
  onUploadSuccess,
  onUploadError,
  maxSizeMB = 10,
  acceptedFormats = ['.xlsx', '.xls'],
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationErrors, setValidationErrors] = useState<ExcelValidationError[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  /**
   * Validate selected file.
   */
  const validateFile = useCallback(
    (file: File): string | null => {
      // Check file extension
      const fileName = file.name.toLowerCase();
      const hasValidExtension = acceptedFormats.some((format) =>
        fileName.endsWith(format.toLowerCase())
      );
      if (!hasValidExtension) {
        return `Formato no válido. Use: ${acceptedFormats.join(', ')}`;
      }

      // Check file size
      if (file.size > maxSizeBytes) {
        return `El archivo excede el tamaño máximo de ${maxSizeMB}MB`;
      }

      return null;
    },
    [acceptedFormats, maxSizeBytes, maxSizeMB]
  );

  /**
   * Handle file selection from input or drop.
   */
  const handleFileSelect = useCallback(
    (file: File) => {
      setFileError(null);
      setValidationErrors([]);

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
    setValidationErrors([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  /**
   * Upload file to backend.
   */
  const handleUpload = useCallback(async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setValidationErrors([]);
    setFileError(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const response = await financeService.uploadExcel(selectedFile);

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.errors.length > 0) {
        setValidationErrors(response.errors);
      }

      // Still call success if we have valid data
      if (response.valid_rows > 0) {
        onUploadSuccess(response);
      } else if (response.errors.length > 0) {
        onUploadError('No se encontraron registros válidos en el archivo');
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            'Error al cargar el archivo';
      setFileError(errorMessage);
      onUploadError(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [selectedFile, onUploadSuccess, onUploadError]);

  /**
   * Format file size for display.
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
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
          accept={acceptedFormats.join(',')}
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
              Arrastra tu archivo Excel aquí
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              o haz clic para seleccionar
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Formatos: {acceptedFormats.join(', ')} | Máximo: {maxSizeMB}MB
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

            {uploading && (
              <Box sx={{ width: '100%', mb: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="caption" color="text.secondary">
                  {uploadProgress < 100 ? 'Procesando...' : 'Completado'}
                </Typography>
              </Box>
            )}

            <Button
              variant="contained"
              onClick={(e) => {
                e.stopPropagation();
                handleUpload();
              }}
              disabled={uploading || disabled}
              startIcon={<CloudUploadIcon />}
            >
              {uploading ? 'Procesando...' : 'Cargar y Validar'}
            </Button>
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

      {/* Validation errors */}
      {validationErrors.length > 0 && (
        <Alert
          severity={validationErrors.length > 10 ? 'error' : 'warning'}
          sx={{ mt: 2 }}
        >
          <AlertTitle>
            {validationErrors.length > 10
              ? 'Errores de validación'
              : 'Advertencias de validación'}
          </AlertTitle>
          <Typography variant="body2" gutterBottom>
            Se encontraron {validationErrors.length} errores en el archivo:
          </Typography>
          <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
            {validationErrors.slice(0, 20).map((error, index) => (
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
                      {error.row > 0 && (
                        <strong>Fila {error.row}, </strong>
                      )}
                      <strong>{error.column}:</strong> {error.message}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
            {validationErrors.length > 20 && (
              <ListItem disableGutters>
                <ListItemText
                  primary={
                    <Typography variant="body2" color="text.secondary">
                      ... y {validationErrors.length - 20} errores más
                    </Typography>
                  }
                />
              </ListItem>
            )}
          </List>
        </Alert>
      )}
    </Box>
  );
};

export default FKExcelUploader;
