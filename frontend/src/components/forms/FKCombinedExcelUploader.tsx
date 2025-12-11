/**
 * FKCombinedExcelUploader - Combined Excel file upload component.
 *
 * Handles dual file upload for Facturas and Complementos de Pago
 * for the Facturacion MX automation feature.
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
  Grid,
  Divider,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Error as ErrorIcon,
  Close as CloseIcon,
  Warning as WarningIcon,
  Receipt as ReceiptIcon,
  Payment as PaymentIcon,
} from '@mui/icons-material';
import type { CombinedUploadResponse, ExcelValidationError } from '../../types/finance';
import financeService from '../../services/financeService';

interface FKCombinedExcelUploaderProps {
  /** Callback when upload and validation succeeds */
  onUploadSuccess: (response: CombinedUploadResponse) => void;
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
 * Combined Excel file uploader for Facturas + Complementos de Pago.
 */
const FKCombinedExcelUploader: React.FC<FKCombinedExcelUploaderProps> = ({
  onUploadSuccess,
  onUploadError,
  maxSizeMB = 10,
  acceptedFormats = ['.xlsx', '.xls'],
  disabled = false,
}) => {
  // File state for both upload zones
  const [facturasFile, setFacturasFile] = useState<File | null>(null);
  const [complementosFile, setComplementosFile] = useState<File | null>(null);
  const [isDraggingFacturas, setIsDraggingFacturas] = useState(false);
  const [isDraggingComplementos, setIsDraggingComplementos] = useState(false);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Errors
  const [facturasErrors, setFacturasErrors] = useState<ExcelValidationError[]>([]);
  const [complementosErrors, setComplementosErrors] = useState<ExcelValidationError[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);

  const facturasInputRef = useRef<HTMLInputElement>(null);
  const complementosInputRef = useRef<HTMLInputElement>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  /**
   * Validate selected file.
   */
  const validateFile = useCallback(
    (file: File): string | null => {
      const fileName = file.name.toLowerCase();
      const hasValidExtension = acceptedFormats.some((format) =>
        fileName.endsWith(format.toLowerCase())
      );
      if (!hasValidExtension) {
        return `Formato no valido. Use: ${acceptedFormats.join(', ')}`;
      }
      if (file.size > maxSizeBytes) {
        return `El archivo excede el tamano maximo de ${maxSizeMB}MB`;
      }
      return null;
    },
    [acceptedFormats, maxSizeBytes, maxSizeMB]
  );

  /**
   * Handle file selection for facturas.
   */
  const handleFacturasSelect = useCallback(
    (file: File) => {
      setFileError(null);
      setFacturasErrors([]);
      const error = validateFile(file);
      if (error) {
        setFileError(`Facturas: ${error}`);
        return;
      }
      setFacturasFile(file);
    },
    [validateFile]
  );

  /**
   * Handle file selection for complementos.
   */
  const handleComplementosSelect = useCallback(
    (file: File) => {
      setFileError(null);
      setComplementosErrors([]);
      const error = validateFile(file);
      if (error) {
        setFileError(`Complementos: ${error}`);
        return;
      }
      setComplementosFile(file);
    },
    [validateFile]
  );

  /**
   * Handle drag events for facturas zone.
   */
  const handleDragEnterFacturas = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingFacturas(true);
  }, []);

  const handleDragLeaveFacturas = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingFacturas(false);
  }, []);

  const handleDropFacturas = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDraggingFacturas(false);
      if (disabled) return;
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFacturasSelect(files[0]);
      }
    },
    [disabled, handleFacturasSelect]
  );

  /**
   * Handle drag events for complementos zone.
   */
  const handleDragEnterComplementos = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingComplementos(true);
  }, []);

  const handleDragLeaveComplementos = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingComplementos(false);
  }, []);

  const handleDropComplementos = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDraggingComplementos(false);
      if (disabled) return;
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleComplementosSelect(files[0]);
      }
    },
    [disabled, handleComplementosSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  /**
   * Clear file selections.
   */
  const handleClearFacturas = useCallback(() => {
    setFacturasFile(null);
    setFacturasErrors([]);
    if (facturasInputRef.current) {
      facturasInputRef.current.value = '';
    }
  }, []);

  const handleClearComplementos = useCallback(() => {
    setComplementosFile(null);
    setComplementosErrors([]);
    if (complementosInputRef.current) {
      complementosInputRef.current.value = '';
    }
  }, []);

  /**
   * Upload files to backend.
   */
  const handleUpload = useCallback(async () => {
    if (!facturasFile && !complementosFile) {
      setFileError('Debe seleccionar al menos un archivo');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setFacturasErrors([]);
    setComplementosErrors([]);
    setFileError(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 300);

      const response = await financeService.uploadCombinedExcel(
        facturasFile || undefined,
        complementosFile || undefined
      );

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Store errors for display
      if (response.facturas_errors.length > 0) {
        setFacturasErrors(response.facturas_errors);
      }
      if (response.complementos_errors.length > 0) {
        setComplementosErrors(response.complementos_errors);
      }

      // Call success if we have valid data
      if (response.total_records > 0) {
        onUploadSuccess(response);
      } else if (response.facturas_errors.length > 0 || response.complementos_errors.length > 0) {
        onUploadError('No se encontraron registros validos en los archivos');
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            'Error al cargar los archivos';
      setFileError(errorMessage);
      onUploadError(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [facturasFile, complementosFile, onUploadSuccess, onUploadError]);

  /**
   * Format file size for display.
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  /**
   * Render a single drop zone.
   */
  const renderDropZone = (
    title: string,
    icon: React.ReactNode,
    file: File | null,
    isDragging: boolean,
    inputRef: React.RefObject<HTMLInputElement | null>,
    onDragEnter: (e: React.DragEvent) => void,
    onDragLeave: (e: React.DragEvent) => void,
    onDrop: (e: React.DragEvent) => void,
    onClear: () => void,
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  ) => (
    <Paper
      elevation={isDragging ? 4 : 1}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDragOver={handleDragOver}
      onDrop={onDrop}
      sx={{
        p: 3,
        textAlign: 'center',
        border: '2px dashed',
        borderColor: isDragging ? 'primary.main' : 'grey.300',
        borderRadius: 2,
        backgroundColor: isDragging ? 'action.hover' : disabled ? 'grey.100' : 'background.paper',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.2s ease',
        minHeight: 160,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        '&:hover': {
          borderColor: disabled ? 'grey.300' : 'primary.main',
          backgroundColor: disabled ? 'grey.100' : 'action.hover',
        },
      }}
      onClick={!disabled && !file ? () => inputRef.current?.click() : undefined}
    >
      <input
        ref={inputRef}
        type="file"
        accept={acceptedFormats.join(',')}
        onChange={onInputChange}
        style={{ display: 'none' }}
        disabled={disabled}
      />

      {!file ? (
        <>
          <Box sx={{ mb: 1 }}>{icon}</Box>
          <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Arrastra o haz clic para seleccionar
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
              mb: 1,
            }}
          >
            <FileIcon color="primary" fontSize="small" />
            <Typography variant="body2" fontWeight="medium" noWrap sx={{ maxWidth: 150 }}>
              {file.name}
            </Typography>
            <Chip label={formatFileSize(file.size)} size="small" variant="outlined" />
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onClear();
              }}
              disabled={uploading}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
          <Typography variant="caption" color="success.main">
            Listo para cargar
          </Typography>
        </Box>
      )}
    </Paper>
  );

  /**
   * Render validation errors list.
   */
  const renderErrors = (errors: ExcelValidationError[], title: string) => {
    if (errors.length === 0) return null;

    return (
      <Alert severity={errors.length > 10 ? 'error' : 'warning'} sx={{ mt: 2 }}>
        <AlertTitle>{title}</AlertTitle>
        <Typography variant="body2" gutterBottom>
          Se encontraron {errors.length} errores:
        </Typography>
        <List dense sx={{ maxHeight: 150, overflow: 'auto' }}>
          {errors.slice(0, 10).map((error, index) => (
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
          {errors.length > 10 && (
            <ListItem disableGutters>
              <ListItemText
                primary={
                  <Typography variant="body2" color="text.secondary">
                    ... y {errors.length - 10} errores mas
                  </Typography>
                }
              />
            </ListItem>
          )}
        </List>
      </Alert>
    );
  };

  return (
    <Box>
      {/* Instructions */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>Carga Combinada de Archivos</AlertTitle>
        <Typography variant="body2">
          Sube los archivos Excel de <strong>Facturas</strong> y{' '}
          <strong>Complementos de Pago</strong>. Ambos deben tener las mismas columnas: UUID,
          CODIGO DE OPERACION, Conceptos, Fecha emision, RFC receptor, SubTotal, IVA, Total, etc.
        </Typography>
      </Alert>

      {/* Drop zones */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          {renderDropZone(
            'Facturas',
            <ReceiptIcon sx={{ fontSize: 40, color: isDraggingFacturas ? 'primary.main' : 'grey.400' }} />,
            facturasFile,
            isDraggingFacturas,
            facturasInputRef,
            handleDragEnterFacturas,
            handleDragLeaveFacturas,
            handleDropFacturas,
            handleClearFacturas,
            (e) => {
              const files = e.target.files;
              if (files && files.length > 0) {
                handleFacturasSelect(files[0]);
              }
            }
          )}
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          {renderDropZone(
            'Complementos de Pago',
            <PaymentIcon sx={{ fontSize: 40, color: isDraggingComplementos ? 'primary.main' : 'grey.400' }} />,
            complementosFile,
            isDraggingComplementos,
            complementosInputRef,
            handleDragEnterComplementos,
            handleDragLeaveComplementos,
            handleDropComplementos,
            handleClearComplementos,
            (e) => {
              const files = e.target.files;
              if (files && files.length > 0) {
                handleComplementosSelect(files[0]);
              }
            }
          )}
        </Grid>
      </Grid>

      {/* Upload progress */}
      {uploading && (
        <Box sx={{ mt: 3 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            {uploadProgress < 100 ? 'Procesando archivos...' : 'Completado'}
          </Typography>
        </Box>
      )}

      {/* Upload button */}
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleUpload}
          disabled={uploading || disabled || (!facturasFile && !complementosFile)}
          startIcon={<CloudUploadIcon />}
          sx={{ minWidth: 200 }}
        >
          {uploading ? 'Procesando...' : 'Cargar y Validar Archivos'}
        </Button>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
          Formatos: {acceptedFormats.join(', ')} | Maximo: {maxSizeMB}MB por archivo
        </Typography>
      </Box>

      <Divider sx={{ my: 3 }} />

      {/* File error */}
      {fileError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {fileError}
        </Alert>
      )}

      {/* Validation errors */}
      {renderErrors(facturasErrors, 'Errores en archivo de Facturas')}
      {renderErrors(complementosErrors, 'Errores en archivo de Complementos')}
    </Box>
  );
};

export default FKCombinedExcelUploader;
