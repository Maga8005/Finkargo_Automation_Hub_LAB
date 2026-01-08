/**
 * FKClientDataImport - CSV/Excel upload component for client data
 */
import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';

const FKClientDataImport: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{
    total_processed: number;
    successful: number;
    failed: number;
    errors: string[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const validTypes = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      ];

      if (!validTypes.includes(selectedFile.type) &&
          !selectedFile.name.match(/\.(csv|xlsx|xls)$/i)) {
        setError('Por favor seleccione un archivo CSV o Excel (.csv, .xlsx, .xls)');
        return;
      }

      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Por favor seleccione un archivo');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const importResult = await legalService.importClients(file);
      setResult(importResult);
      setFile(null);

      // Reset file input
      const fileInput = document.getElementById('file-upload-input') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || 'Error al importar el archivo');
      console.error('Import error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      {/* Instructions */}
      <Alert severity="info" sx={{ mb: 3 }} icon={<InfoIcon />}>
        <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
          Formato del Archivo
        </Typography>
        <Typography variant="body2">
          El archivo debe contener las siguientes columnas:{' '}
          <strong>nit, nombre_importador, representante_legal, cedula_representante, ciudad_domicilio, cupo_plataforma</strong>
        </Typography>
      </Alert>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Upload Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            Cargar Archivo
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Seleccione un archivo CSV o Excel con los datos de clientes
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
            <input
              accept=".csv,.xlsx,.xls"
              style={{ display: 'none' }}
              id="file-upload-input"
              type="file"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <label htmlFor="file-upload-input">
              <Button
                variant="outlined"
                component="span"
                startIcon={<UploadIcon />}
                disabled={uploading}
              >
                Seleccionar Archivo
              </Button>
            </label>

            {file && (
              <Chip
                label={file.name}
                onDelete={() => {
                  setFile(null);
                  const fileInput = document.getElementById('file-upload-input') as HTMLInputElement;
                  if (fileInput) fileInput.value = '';
                }}
                color="primary"
                variant="outlined"
              />
            )}
          </Box>

          {file && (
            <Box sx={{ mt: 3 }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<UploadIcon />}
                onClick={handleUpload}
                disabled={uploading}
                fullWidth
              >
                {uploading ? 'Importando...' : 'Importar Datos'}
              </Button>
            </Box>
          )}

          {uploading && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Procesando archivo...
              </Typography>
              <LinearProgress />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Resultado de la Importación
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <Chip
                label={`Total: ${result.total_processed}`}
                color="default"
                variant="outlined"
              />
              <Chip
                label={`Exitosos: ${result.successful}`}
                color="success"
                icon={<SuccessIcon />}
              />
              {result.failed > 0 && (
                <Chip
                  label={`Fallidos: ${result.failed}`}
                  color="error"
                  icon={<ErrorIcon />}
                />
              )}
            </Box>

            {result.errors && result.errors.length > 0 && (
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                  Errores:
                </Typography>
                <List dense>
                  {result.errors.slice(0, 10).map((errorMsg, index) => (
                    <ListItem key={index}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <ErrorIcon color="error" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={errorMsg}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                  {result.errors.length > 10 && (
                    <ListItem>
                      <ListItemText
                        primary={`... y ${result.errors.length - 10} errores más`}
                        primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                      />
                    </ListItem>
                  )}
                </List>
              </Box>
            )}

            {result.successful > 0 && result.failed === 0 && (
              <Alert severity="success" sx={{ mt: 2 }}>
                ¡Importación completada exitosamente! Todos los registros fueron procesados.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Download Template Link */}
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          ¿Necesita una plantilla?{' '}
          <Button
            size="small"
            onClick={() => {
              // TODO: Generate and download template CSV
              alert('La plantilla se descargará próximamente');
            }}
          >
            Descargar plantilla CSV
          </Button>
        </Typography>
      </Box>
    </Box>
  );
};

export default FKClientDataImport;
