/**
 * FKExcelUploaderCO - Colombia File Uploader Component
 *
 * Component for uploading 4 Excel files for Colombia invoicing processing:
 * 1. Netsuite Facturas
 * 2. Netsuite NC (Notas de Crédito)
 * 3. Noova Facturas
 * 4. Noova NC (Notas de Crédito)
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Stack,
  Alert,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Close as CloseIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';

export interface FileState {
  file: File | null;
  label: string;
  key: string;
  required: boolean;
}

export interface FKExcelUploaderCOProps {
  onUploadSuccess?: (response: Record<string, File>) => void;
  onUploadError?: (error: string) => void;
}

const FKExcelUploaderCO: React.FC<FKExcelUploaderCOProps> = ({
  onUploadSuccess,
}) => {
  const [files, setFiles] = useState<FileState[]>([
    {
      file: null,
      label: 'Netsuite Facturas',
      key: 'netsuite',
      required: false,
    },
    {
      file: null,
      label: 'Noova Facturas',
      key: 'noova_facturas',
      required: false,
    },
    {
      file: null,
      label: 'Netsuite NC',
      key: 'netsuite_nc',
      required: false,
    },
    {
      file: null,
      label: 'Noova NC',
      key: 'noova_nc',
      required: false,
    },
  ]);

  const [isUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handle file selection for a specific slot
   */
  const handleFileChange = (index: number, file: File | null) => {
    if (file) {
      // Validate file type
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
      ];
      if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls)$/i)) {
        setError(`Archivo inválido: ${file.name}. Solo se aceptan archivos .xlsx o .xls`);
        return;
      }
    }

    setFiles((prev) => {
      const updated = [...prev];
      updated[index].file = file;
      return updated;
    });
    setError(null);
  };

  /**
   * Remove file from a specific slot
   */
  const handleRemoveFile = (index: number) => {
    setFiles((prev) => {
      const updated = [...prev];
      updated[index].file = null;
      return updated;
    });
  };

  /**
   * Check if at least one valid pair is selected
   * Valid pairs:
   * - Facturas: Netsuite Facturas + Noova Facturas (indices 0, 1)
   * - Notas de Crédito: Netsuite NC + Noova NC (indices 2, 3)
   */
  const allFilesSelected = (): boolean => {
    const netsuiteFacturas = files[0].file;
    const noovaFacturas = files[1].file;
    const netsuiteNC = files[2].file;
    const noovaNC = files[3].file;

    // At least one complete pair must be selected
    const facturasComplete = netsuiteFacturas && noovaFacturas;
    const notasCreditoComplete = netsuiteNC && noovaNC;

    return !!(facturasComplete || notasCreditoComplete);
  };

  /**
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  /**
   * Handle file upload trigger
   */
  const handleUpload = () => {
    if (onUploadSuccess) {
      // Create file set object
      const fileSet: Record<string, File> = {};
      files.forEach((f) => {
        if (f.file) {
          fileSet[f.key] = f.file;
        }
      });

      // Call parent callback with file set
      onUploadSuccess(fileSet);
    }
  };

  return (
    <Card elevation={2}>
      <CardContent>
        <Stack spacing={3}>
          {/* Header */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Cargar Archivos de Colombia
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Seleccione los 4 archivos Excel requeridos para procesar la facturación de Colombia
            </Typography>
          </Box>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Loading Bar */}
          {isUploading && <LinearProgress />}

          {/* File Upload Slots - 2 Columns Layout */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
              gap: 3,
            }}
          >
            {/* Column 1: Facturas */}
            <Box>
              <Box
                sx={{
                  border: '2px solid',
                  borderColor: 'primary.main',
                  borderRadius: 2,
                  p: 2,
                  bgcolor: 'rgba(60, 71, 211, 0.05)',
                  height: '100%',
                }}
              >
                <Typography variant="h6" fontWeight={700} gutterBottom color="primary.main">
                  📄 Facturas
                </Typography>
                <Stack spacing={2}>
                  {/* Netsuite Facturas */}
                  {[0, 1].map((index) => {
                    const fileState = files[index];
                    return (
                      <Card
                        key={fileState.key}
                        variant="outlined"
                        sx={{
                          p: 2,
                          bgcolor: fileState.file ? 'success.light' : 'white',
                          borderColor: fileState.file ? 'success.main' : 'grey.300',
                          transition: 'all 0.2s',
                          '&:hover': {
                            borderColor: 'primary.main',
                            bgcolor: fileState.file ? 'success.light' : 'grey.50',
                          },
                        }}
                      >
                        <Stack spacing={1}>
                          {/* Label */}
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="subtitle2" fontWeight={600}>
                              {fileState.label}
                            </Typography>
                            {fileState.file && <CheckIcon color="success" fontSize="small" />}
                          </Box>

                          {/* File Display or Upload Button */}
                          {fileState.file ? (
                            <Box
                              display="flex"
                              alignItems="center"
                              justifyContent="space-between"
                              sx={{
                                p: 1,
                                bgcolor: 'white',
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'success.main',
                              }}
                            >
                              <Box display="flex" alignItems="center" gap={1} flex={1} minWidth={0}>
                                <FileIcon fontSize="small" color="success" />
                                <Box flex={1} minWidth={0}>
                                  <Typography variant="body2" noWrap sx={{ fontWeight: 500 }}>
                                    {fileState.file.name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {formatFileSize(fileState.file.size)}
                                  </Typography>
                                </Box>
                              </Box>
                              <Tooltip title="Eliminar archivo">
                                <IconButton
                                  size="small"
                                  onClick={() => handleRemoveFile(index)}
                                  disabled={isUploading}
                                >
                                  <CloseIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          ) : (
                            <Button
                              variant="outlined"
                              component="label"
                              startIcon={<UploadIcon />}
                              fullWidth
                              disabled={isUploading}
                              size="small"
                            >
                              Seleccionar archivo
                              <input
                                type="file"
                                hidden
                                accept=".xlsx,.xls"
                                onChange={(e) => {
                                  const file = e.target.files?.[0] || null;
                                  handleFileChange(index, file);
                                  e.target.value = '';
                                }}
                              />
                            </Button>
                          )}
                        </Stack>
                      </Card>
                    );
                  })}
                </Stack>
              </Box>
            </Box>

            {/* Column 2: Notas de Crédito */}
            <Box>
              <Box
                sx={{
                  border: '2px solid',
                  borderColor: 'secondary.main',
                  borderRadius: 2,
                  p: 2,
                  bgcolor: 'rgba(235, 135, 116, 0.05)',
                  height: '100%',
                }}
              >
                <Typography variant="h6" fontWeight={700} gutterBottom color="secondary.main">
                  📋 Notas de Crédito
                </Typography>
                <Stack spacing={2}>
                  {/* Netsuite NC + Noova NC */}
                  {[2, 3].map((index) => {
                    const fileState = files[index];
                    return (
                      <Card
                        key={fileState.key}
                        variant="outlined"
                        sx={{
                          p: 2,
                          bgcolor: fileState.file ? 'success.light' : 'white',
                          borderColor: fileState.file ? 'success.main' : 'grey.300',
                          transition: 'all 0.2s',
                          '&:hover': {
                            borderColor: 'secondary.main',
                            bgcolor: fileState.file ? 'success.light' : 'grey.50',
                          },
                        }}
                      >
                        <Stack spacing={1}>
                          {/* Label */}
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="subtitle2" fontWeight={600}>
                              {fileState.label}
                            </Typography>
                            {fileState.file && <CheckIcon color="success" fontSize="small" />}
                          </Box>

                          {/* File Display or Upload Button */}
                          {fileState.file ? (
                            <Box
                              display="flex"
                              alignItems="center"
                              justifyContent="space-between"
                              sx={{
                                p: 1,
                                bgcolor: 'white',
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'success.main',
                              }}
                            >
                              <Box display="flex" alignItems="center" gap={1} flex={1} minWidth={0}>
                                <FileIcon fontSize="small" color="success" />
                                <Box flex={1} minWidth={0}>
                                  <Typography variant="body2" noWrap sx={{ fontWeight: 500 }}>
                                    {fileState.file.name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {formatFileSize(fileState.file.size)}
                                  </Typography>
                                </Box>
                              </Box>
                              <Tooltip title="Eliminar archivo">
                                <IconButton
                                  size="small"
                                  onClick={() => handleRemoveFile(index)}
                                  disabled={isUploading}
                                >
                                  <CloseIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          ) : (
                            <Button
                              variant="outlined"
                              component="label"
                              startIcon={<UploadIcon />}
                              fullWidth
                              disabled={isUploading}
                              size="small"
                            >
                              Seleccionar archivo
                              <input
                                type="file"
                                hidden
                                accept=".xlsx,.xls"
                                onChange={(e) => {
                                  const file = e.target.files?.[0] || null;
                                  handleFileChange(index, file);
                                  e.target.value = '';
                                }}
                              />
                            </Button>
                          )}
                        </Stack>
                      </Card>
                    );
                  })}
                </Stack>
              </Box>
            </Box>
          </Box>

          {/* Upload Status Summary */}
          <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
            <Chip
              label={`${files.filter((f) => f.file !== null).length} / 4 archivos seleccionados`}
              color={allFilesSelected() ? 'success' : 'default'}
              size="small"
            />
            {allFilesSelected() ? (
              <Typography variant="caption" color="success.main">
                ✓ Al menos una pareja completa está lista
              </Typography>
            ) : (
              <Typography variant="caption" color="warning.main">
                ⚠️ Debe subir al menos una pareja completa (Netsuite + Noova)
              </Typography>
            )}
          </Box>

          {/* Action Button */}
          <Button
            variant="contained"
            size="large"
            startIcon={<UploadIcon />}
            onClick={handleUpload}
            disabled={!allFilesSelected() || isUploading}
            fullWidth
            sx={{ height: 52 }}
          >
            {isUploading ? 'Procesando...' : 'Procesar Archivos'}
          </Button>

          {/* Help Text */}
          <Alert severity="info" variant="outlined">
            <Typography variant="body2" fontWeight={600} gutterBottom>
              📝 Instrucciones de carga:
            </Typography>
            <Typography variant="body2" paragraph>
              Puede subir archivos por <strong>parejas</strong>:
            </Typography>
            <ul style={{ margin: '0 0 8px 0', paddingLeft: '20px' }}>
              <li>
                <strong>Pareja 1 - Facturas:</strong> Netsuite Facturas + Noova Facturas
              </li>
              <li>
                <strong>Pareja 2 - Notas de Crédito:</strong> Netsuite NC + Noova NC
              </li>
            </ul>
            <Typography variant="body2" color="text.secondary">
              Debe subir al menos <strong>una pareja completa</strong> (ambos archivos Netsuite y Noova de la misma categoría).
            </Typography>
          </Alert>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default FKExcelUploaderCO;
