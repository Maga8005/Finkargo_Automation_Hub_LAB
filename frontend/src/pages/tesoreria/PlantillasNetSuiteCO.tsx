/**
 * PlantillasNetSuiteCO - Colombia Payment Template Converter.
 *
 * Converts Historial de Pagos files to NetSuite payment application format
 * for Colombia operations.
 */
import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Divider,
  Alert,
  AlertTitle,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  CloudDownload as DownloadIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import FKHistorialUploader from '../../components/forms/FKHistorialUploader';
import type { HistorialValidationResponse, ConversionHeaderStats } from '../../types/tesoreria';
import treasuryService from '../../services/treasuryService';

const PlantillasNetSuiteCO: React.FC = () => {
  const navigate = useNavigate();

  // State
  const [validatedFile, setValidatedFile] = useState<File | null>(null);
  const [validationResult, setValidationResult] = useState<HistorialValidationResponse | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionStats, setConversionStats] = useState<ConversionHeaderStats | null>(null);
  const [conversionError, setConversionError] = useState<string | null>(null);
  const [downloadComplete, setDownloadComplete] = useState(false);

  /**
   * Handle successful file validation.
   */
  const handleValidationSuccess = useCallback(
    (response: HistorialValidationResponse, file: File) => {
      setValidationResult(response);
      setValidatedFile(file);
      setConversionStats(null);
      setConversionError(null);
      setDownloadComplete(false);
    },
    []
  );

  /**
   * Handle validation error.
   */
  const handleValidationError = useCallback((error: string) => {
    setValidationResult(null);
    setValidatedFile(null);
    setConversionError(error);
  }, []);

  /**
   * Convert and download the file.
   */
  const handleConvert = useCallback(async () => {
    if (!validatedFile) return;

    setIsConverting(true);
    setConversionError(null);
    setDownloadComplete(false);

    try {
      const result = await treasuryService.convertToNetsuiteTemplate(
        validatedFile,
        'colombia'
      );

      // Trigger download
      treasuryService.downloadBlob(result.blob, result.filename);

      // Update state with stats
      setConversionStats(result.stats);
      setDownloadComplete(true);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            'Error al convertir el archivo';
      setConversionError(errorMessage);
    } finally {
      setIsConverting(false);
    }
  }, [validatedFile]);

  /**
   * Reset the form for a new conversion.
   */
  const handleReset = useCallback(() => {
    setValidatedFile(null);
    setValidationResult(null);
    setConversionStats(null);
    setConversionError(null);
    setDownloadComplete(false);
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header with back button */}
      <Box sx={{ mb: 4 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/tesoreria/plantillas-netsuite')}
          sx={{ mb: 2 }}
        >
          Volver a selección de país
        </Button>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h2" sx={{ lineHeight: 1 }}>
            🇨🇴
          </Typography>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
              Aplicación de Pagos - Colombia
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Conversión de Historial de Pagos a Template de NetSuite
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider sx={{ mb: 4 }} />

      {/* Instructions */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: 'grey.50' }}>
        <Typography variant="subtitle2" gutterBottom>
          Columnas requeridas del archivo fuente:
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Cliente, Identificación del cliente, Código de desembolso, Código de recaudo,
          Fecha de pago, Moneda, Capital, Banco remitente
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          <strong>Conceptos:</strong> Capital, 4x1000, Fondo de garantías, IVA Fondo de garantías,
          Seguro + IVA, Servicio de originación, Servicio de giro + IVA, Costos adicionales,
          Intereses Corrientes, Intereses de Mora (PAR 30/60/90/120+)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          <strong>Nota:</strong> La columna NT indica Operaciones Cedidas con cuentas AR diferentes.
        </Typography>
      </Paper>

      {/* File Upload Section */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
          1. Cargar archivo Historial de Pagos
        </Typography>

        <FKHistorialUploader
          country="colombia"
          onValidationSuccess={handleValidationSuccess}
          onValidationError={handleValidationError}
          disabled={isConverting}
        />
      </Paper>

      {/* Conversion Section */}
      {validationResult?.success && validatedFile && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
            2. Convertir y Descargar
          </Typography>

          {!downloadComplete ? (
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body1" sx={{ mb: 3 }}>
                El archivo ha sido validado correctamente.
                Haz clic en el botón para generar el template de NetSuite.
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Filas a procesar: <strong>{validationResult.valid_rows}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Filas de salida estimadas: <strong>{validationResult.estimated_output_rows}</strong>
                </Typography>
              </Box>

              <Button
                variant="contained"
                size="large"
                onClick={handleConvert}
                disabled={isConverting}
                startIcon={isConverting ? <CircularProgress size={20} color="inherit" /> : <DownloadIcon />}
              >
                {isConverting ? 'Convirtiendo...' : 'Convertir y Descargar'}
              </Button>
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center' }}>
              <Alert
                severity="success"
                icon={<CheckCircleIcon />}
                sx={{ mb: 3, justifyContent: 'center' }}
              >
                <AlertTitle>Conversión completada</AlertTitle>
                El archivo ha sido descargado exitosamente.
              </Alert>

              {conversionStats && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Filas procesadas: <strong>{conversionStats.source}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Filas generadas: <strong>{conversionStats.output}</strong>
                  </Typography>
                  {conversionStats.skipped > 0 && (
                    <Typography variant="body2" color="warning.main">
                      Filas omitidas: <strong>{conversionStats.skipped}</strong>
                    </Typography>
                  )}
                  {conversionStats.errors > 0 && (
                    <Typography variant="body2" color="error.main">
                      Errores: <strong>{conversionStats.errors}</strong>
                    </Typography>
                  )}
                </Box>
              )}

              <Button
                variant="outlined"
                onClick={handleReset}
              >
                Convertir otro archivo
              </Button>
            </Box>
          )}
        </Paper>
      )}

      {/* Error Display */}
      {conversionError && (
        <Alert severity="error" sx={{ mb: 4 }}>
          <AlertTitle>Error de conversión</AlertTitle>
          {conversionError}
        </Alert>
      )}
    </Container>
  );
};

export default PlantillasNetSuiteCO;
