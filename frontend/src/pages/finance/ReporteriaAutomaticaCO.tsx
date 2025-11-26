/**
 * ReporteriaAutomaticaCO - Reportería Automática Colombia
 * Funcionalidad para procesar archivos de facturación Colombia
 */
import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Divider,
  Alert,
  Chip,
  Stack,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
} from '@mui/material';
import {
  CloudDownload as DownloadIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material';
import FKExcelUploaderCO from '../../components/forms/FKExcelUploaderCO';
import {
  processCOFiles,
  downloadCOReport,
  triggerDownload,
  type COProcessingResponse,
  type COFileSet,
} from '../../services/financeServiceCO';

const ReporteriaAutomaticaCO: React.FC = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<COProcessingResponse | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  /**
   * Handle file upload and processing
   */
  const handleUpload = async (fileSet: COFileSet) => {
    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
      const response = await processCOFiles(fileSet);
      setResult(response);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error desconocido al procesar archivos';
      setError(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  /**
   * Handle report download
   */
  const handleDownload = async () => {
    if (!result?.session_id) return;

    setIsDownloading(true);
    try {
      const blob = await downloadCOReport(result.session_id);
      const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
      const filename = `Reporte_Facturacion_CO_${timestamp}.xlsx`;
      triggerDownload(blob, filename);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data
          ?.detail ||
        (err as { message?: string })?.message ||
        'Error al descargar el reporte';
      setError(errorMessage);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography fontSize="2rem">🇨🇴</Typography>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
              Reportería Automática Colombia
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Procesamiento y consolidación de facturas Netsuite + Noova
            </Typography>
          </Box>
        </Box>
      </Box>

      <Divider sx={{ mb: 4 }} />

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} lg={result ? 5 : 12}>
          <FKExcelUploaderCO
            onUploadSuccess={handleUpload}
            onUploadError={(err) => setError(err)}
          />

          {/* Processing Indicator */}
          {isProcessing && (
            <Card sx={{ mt: 3 }} elevation={2}>
              <CardContent>
                <Stack spacing={2} alignItems="center">
                  <CircularProgress size={48} />
                  <Typography variant="h6">Procesando archivos...</Typography>
                  <Typography variant="body2" color="text.secondary" textAlign="center">
                    Consolidando datos de Netsuite y Noova.
                    <br />
                    Esto puede tomar algunos minutos.
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* Error Display */}
          {error && !isProcessing && (
            <Alert severity="error" sx={{ mt: 3 }} onClose={() => setError(null)}>
              <Typography variant="body2">{error}</Typography>
            </Alert>
          )}
        </Grid>

        {/* Results Section */}
        {result && !isProcessing && (
          <Grid item xs={12} lg={7}>
            <Card elevation={3}>
              <CardContent>
                <Stack spacing={3}>
                  {/* Success Header */}
                  <Box display="flex" alignItems="center" gap={2}>
                    <CheckIcon color="success" sx={{ fontSize: 40 }} />
                    <Box flex={1}>
                      <Typography variant="h5" fontWeight={600}>
                        Procesamiento Completado
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {result.message}
                      </Typography>
                    </Box>
                  </Box>

                  <Divider />

                  {/* Statistics Overview */}
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Resumen del Procesamiento
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="primary.main" fontWeight={700}>
                            {result.stats.total_consolidated}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Total Consolidado
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="success.main" fontWeight={700}>
                            {result.stats.matched_with_netsuite}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Con Match NS
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="info.main" fontWeight={700}>
                            {result.stats.costos_fijos_count}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Costos Fijos
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="secondary.main" fontWeight={700}>
                            {result.stats.mandato_count}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Mandato
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Detailed Stats Table */}
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>
                            <strong>Métrica</strong>
                          </TableCell>
                          <TableCell align="right">
                            <strong>Cantidad</strong>
                          </TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Registros Noova (Origen)</TableCell>
                          <TableCell align="right">{result.stats.total_records_noova}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Registros Netsuite (Valores)</TableCell>
                          <TableCell align="right">{result.stats.total_records_netsuite}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Registros sin match Netsuite</TableCell>
                          <TableCell align="right">{result.stats.unmatched_noova}</TableCell>
                        </TableRow>
                        <TableRow sx={{ bgcolor: 'primary.light' }}>
                          <TableCell>
                            <strong>Total Consolidado</strong>
                          </TableCell>
                          <TableCell align="right">
                            <strong>{result.stats.total_consolidated}</strong>
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Sheet Information */}
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Hojas Generadas
                    </Typography>
                    <Stack spacing={1}>
                      {result.sheets.map((sheet, idx) => (
                        <Paper key={idx} variant="outlined" sx={{ p: 2 }}>
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Box display="flex" alignItems="center" gap={1}>
                              <ReportIcon color="primary" />
                              <Box>
                                <Typography variant="body1" fontWeight={600}>
                                  {sheet.sheet_name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {sheet.row_count} filas × {sheet.column_count} columnas
                                </Typography>
                              </Box>
                            </Box>
                            <Chip
                              label={`${sheet.row_count} registros`}
                              color="primary"
                              size="small"
                            />
                          </Box>
                        </Paper>
                      ))}
                    </Stack>
                  </Box>

                  {/* Errors Display */}
                  {result.stats.errors.length > 0 && (
                    <Alert severity="warning" icon={<InfoIcon />}>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        Se encontraron algunos errores menores:
                      </Typography>
                      <ul style={{ margin: 0, paddingLeft: 20 }}>
                        {result.stats.errors.slice(0, 5).map((err, idx) => (
                          <li key={idx}>
                            <Typography variant="caption">{err}</Typography>
                          </li>
                        ))}
                      </ul>
                      {result.stats.errors.length > 5 && (
                        <Typography variant="caption" color="text.secondary">
                          ... y {result.stats.errors.length - 5} errores más
                        </Typography>
                      )}
                    </Alert>
                  )}

                  {/* Download Button */}
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={isDownloading ? <CircularProgress size={20} /> : <DownloadIcon />}
                    onClick={handleDownload}
                    disabled={isDownloading}
                    fullWidth
                    sx={{ height: 56 }}
                  >
                    {isDownloading ? 'Descargando...' : 'Descargar Reporte Excel'}
                  </Button>

                  {/* Session Info */}
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="caption" color="text.secondary">
                      <strong>Sesión:</strong> {result.session_id}
                    </Typography>
                  </Paper>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Help Section */}
        {!result && !isProcessing && (
          <Grid item xs={12}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  ℹ️ Instrucciones
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" paragraph>
                      <strong>Archivos por parejas:</strong>
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      Puede subir los 4 archivos o solo una pareja:
                    </Typography>
                    <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                      <li>
                        <Typography variant="body2">
                          <strong>Pareja 1 - Facturas:</strong>
                          <br />• Netsuite Facturas (valores moneda extranjera)
                          <br />• Noova Facturas (información principal)
                        </Typography>
                      </li>
                      <li style={{ marginTop: '8px' }}>
                        <Typography variant="body2">
                          <strong>Pareja 2 - Notas de Crédito:</strong>
                          <br />• Netsuite NC (valores)
                          <br />• Noova NC (información principal)
                        </Typography>
                      </li>
                    </ul>
                    <Typography variant="caption" color="warning.main">
                      ⚠️ Debe subir al menos una pareja completa (ambos archivos)
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" paragraph>
                      <strong>Proceso:</strong>
                    </Typography>
                    <ol style={{ margin: 0 }}>
                      <li>
                        <Typography variant="body2">
                          El sistema lee los 4 archivos Excel
                        </Typography>
                      </li>
                      <li>
                        <Typography variant="body2">
                          Consolida datos con LEFT JOIN por número de factura
                        </Typography>
                      </li>
                      <li>
                        <Typography variant="body2">
                          Clasifica por código de producto (146 códigos)
                        </Typography>
                      </li>
                      <li>
                        <Typography variant="body2">
                          Genera 2 hojas: Costos Fijos (11 cols) y Mandato (9 cols)
                        </Typography>
                      </li>
                    </ol>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default ReporteriaAutomaticaCO;
