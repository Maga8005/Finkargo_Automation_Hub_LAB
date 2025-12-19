/**
 * BrokerIncentivesPage - Broker contract incentive extraction page
 *
 * Main page for scanning broker contract directories and extracting
 * incentive percentages. Integrates:
 * - FKBrokerContractScanForm for configuration
 * - FKBrokerIncentiveResultsGrid for results display
 */
import React, { useState } from 'react';
import { Container, Grid, Box, Typography, Alert, Snackbar } from '@mui/material';
import FKBrokerContractScanForm from '../../components/alianzas/FKBrokerContractScanForm';
import FKBrokerIncentiveResultsGrid from '../../components/alianzas/FKBrokerIncentiveResultsGrid';
import {
  scanBrokerContracts,
  type BrokerContractScanConfig,
  type BrokerContractScanResult,
  type BrokerIncentiveData,
} from '../../services/brokerIncentiveService';
import { extractErrorMessage } from '../../utils/errorUtils';

const BrokerIncentivesPage: React.FC = () => {
  const [scanResult, setScanResult] = useState<BrokerContractScanResult | null>(null);
  const [records, setRecords] = useState<BrokerIncentiveData[]>([]);
  const [snackbarOpen, setSnackbarOpen] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info'>('success');

  console.log('[BrokerIncentivesPage] Rendering', {
    hasResult: !!scanResult,
    recordCount: records.length,
  });

  /**
   * Handle scan start
   */
  const handleScanStart = async (config: BrokerContractScanConfig) => {
    console.log('[BrokerIncentivesPage] Scan started', config);

    try {
      const result = await scanBrokerContracts(config);

      console.log('[BrokerIncentivesPage] Scan completed', {
        totalFolders: result.total_folders_found,
        successful: result.successful_extractions,
        failed: result.failed_extractions,
      });

      setScanResult(result);
      setRecords(result.records);

      // Show success message
      setSnackbarMessage(
        `Escaneo completado: ${result.total_folders_found} carpetas encontradas, ` +
          `${result.successful_extractions} extracciones exitosas`
      );
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error: unknown) {
      console.error('[BrokerIncentivesPage] Scan failed', error);

      setSnackbarMessage(extractErrorMessage(error, 'Error al escanear contratos'));
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
          Extraccion de Incentivos de Brokers
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Escanea directorios de contratos de brokers para extraer automaticamente
          los porcentajes de incentivos. El sistema identifica contratos tipo
          &quot;Bono&quot; e &quot;Incentivos&quot; y extrae los porcentajes de linea de credito
          y operaciones.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Scan Form */}
        <Grid size={{ xs: 12, md: 4 }}>
          <FKBrokerContractScanForm onScanStart={handleScanStart} />
        </Grid>

        {/* Scan Result Summary (if available) */}
        {scanResult && (
          <Grid size={{ xs: 12, md: 8 }}>
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
                    <strong>Carpetas Encontradas:</strong> {scanResult.total_folders_found}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>PDFs Procesados:</strong> {scanResult.total_pdfs_processed}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Extracciones Exitosas:</strong> {scanResult.successful_extractions}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Extracciones Fallidas:</strong> {scanResult.failed_extractions}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Duracion:</strong> {scanResult.scan_duration_seconds.toFixed(1)}s
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Contratos Bono:</strong> {scanResult.statistics.bono_contracts}
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    <strong>Contratos Incentivos:</strong> {scanResult.statistics.incentivos_contracts}
                  </Typography>
                </li>
                {scanResult.statistics.average_credit_line_pct > 0 && (
                  <li>
                    <Typography variant="body2">
                      <strong>Promedio Linea Credito:</strong>{' '}
                      {scanResult.statistics.average_credit_line_pct.toFixed(2)}%
                    </Typography>
                  </li>
                )}
                {scanResult.statistics.average_operations_pct > 0 && (
                  <li>
                    <Typography variant="body2">
                      <strong>Promedio Operaciones:</strong>{' '}
                      {scanResult.statistics.average_operations_pct.toFixed(2)}%
                    </Typography>
                  </li>
                )}
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Archivo generado: {scanResult.output_file_path}
              </Typography>
            </Alert>
          </Grid>
        )}

        {/* Results Grid */}
        {records.length > 0 && (
          <Grid size={{ xs: 12 }}>
            <FKBrokerIncentiveResultsGrid records={records} />
          </Grid>
        )}

        {/* Empty State */}
        {!scanResult && records.length === 0 && (
          <Grid size={{ xs: 12, md: 8 }}>
            <Alert severity="info" sx={{ borderRadius: 2 }}>
              <Typography variant="body2">
                Configura la ruta del directorio y haz clic en &quot;Escanear Directorio&quot;
                para iniciar la extraccion de incentivos de contratos de brokers.
              </Typography>
            </Alert>
          </Grid>
        )}
      </Grid>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default BrokerIncentivesPage;
