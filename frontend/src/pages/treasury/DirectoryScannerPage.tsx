/**
 * DirectoryScannerPage - Local directory scanning page
 *
 * Main page for scanning local directories and managing inventory files.
 * Integrates FKDirectoryScanForm and FKInventoryFilesTable components.
 */
import React, { useState } from 'react';
import { Container, Grid, Box, Typography, Alert, Snackbar } from '@mui/material';
import FKDirectoryScanForm from '../../components/treasury/FKDirectoryScanForm';
import FKInventoryFilesTable from '../../components/treasury/FKInventoryFilesTable';
import {
  scanLocalDirectory,
  type LocalDirectoryScanConfig,
  type LocalDirectoryScanResult,
} from '../../services/directoryScannerService';

const DirectoryScannerPage: React.FC = () => {
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [scanResult, setScanResult] = useState<LocalDirectoryScanResult | null>(
    null
  );
  const [snackbarOpen, setSnackbarOpen] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<
    'success' | 'error' | 'info'
  >('success');

  console.log('[DirectoryScannerPage] Rendering');

  /**
   * Handle scan start
   */
  const handleScanStart = async (config: LocalDirectoryScanConfig) => {
    console.log('[DirectoryScannerPage] Scan started', config);

    try {
      const result = await scanLocalDirectory(config);

      console.log('[DirectoryScannerPage] Scan completed', result);

      setScanResult(result);

      // Show success message
      setSnackbarMessage(
        `Escaneo completado: ${result.total_pdfs_found} PDFs encontrados, ` +
          `${result.successful_extractions} extracciones exitosas`
      );
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      // Trigger inventory files table refresh
      setRefreshTrigger((prev) => prev + 1);
    } catch (error: any) {
      console.error('[DirectoryScannerPage] Scan failed', error);

      // Show error message
      setSnackbarMessage(error.message || 'Error al escanear directorio');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);

      throw error; // Re-throw to let form handle it
    }
  };

  /**
   * Handle snackbar close
   */
  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom color="primary">
          Escaneo de Directorio Local
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Escanea directorios locales para generar inventarios de archivos PDF
          de declaraciones y gestionar archivos de inventario existentes.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Scan Form */}
        <Grid size={{ xs: 12, md: 6 }}>
          <FKDirectoryScanForm onScanStart={handleScanStart} />
        </Grid>

        {/* Scan Result (if available) */}
        {scanResult && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Alert
              severity="success"
              onClose={() => setScanResult(null)}
              sx={{
                backgroundColor: '#E0F7E6',
                borderRadius: 2,
                '& .MuiAlert-icon': {
                  color: '#2CA14D',
                },
              }}
            >
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Escaneo Completado Exitosamente
              </Typography>
              <Box component="ul" sx={{ pl: 2, mt: 1, mb: 0 }}>
                <li>
                  <Typography variant="body2">
                    <strong>PDFs Encontrados:</strong>{' '}
                    {scanResult.total_pdfs_found}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Extracciones Exitosas:</strong>{' '}
                    {scanResult.successful_extractions}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Extracciones Fallidas:</strong>{' '}
                    {scanResult.failed_extractions}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Duración:</strong>{' '}
                    {scanResult.scan_duration_seconds.toFixed(1)}s
                  </Typography>
                </li>
                {scanResult.statistics.unique_customers !== undefined && (
                  <li>
                    <Typography variant="body2">
                      <strong>Clientes Únicos:</strong>{' '}
                      {scanResult.statistics.unique_customers}
                    </Typography>
                  </li>
                )}
                {scanResult.statistics.total_amount !== undefined && (
                  <li>
                    <Typography variant="body2">
                      <strong>Monto Total:</strong> $
                      {scanResult.statistics.total_amount.toLocaleString(
                        'en-US',
                        {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        }
                      )}
                    </Typography>
                  </li>
                )}
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
                Archivo generado: {scanResult.output_file_path}
              </Typography>
            </Alert>
          </Grid>
        )}

        {/* Inventory Files Table */}
        <Grid size={{ xs: 12 }}>
          <FKInventoryFilesTable refreshTrigger={refreshTrigger} />
        </Grid>
      </Grid>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default DirectoryScannerPage;
