/**
 * FKBrokerContractScanForm - Broker contract scan configuration form
 *
 * Provides form inputs for configuring broker contract directory scanning:
 * - Directory path
 * - Include subfolders toggle
 * - Output file name (optional)
 */
import React, { useState } from 'react';
import {
  Paper,
  Box,
  TextField,
  Typography,
  Button,
  Stack,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
} from '@mui/material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import SearchIcon from '@mui/icons-material/Search';
import type { BrokerContractScanConfig } from '../../services/brokerIncentiveService';
import { extractErrorMessage } from '../../utils/errorUtils';

interface FKBrokerContractScanFormProps {
  onScanStart: (config: BrokerContractScanConfig) => Promise<void>;
  disabled?: boolean;
}

const DEFAULT_DIRECTORY_PATH = '/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/2024';

const FKBrokerContractScanForm: React.FC<FKBrokerContractScanFormProps> = ({
  onScanStart,
  disabled = false,
}) => {
  const [directoryPath, setDirectoryPath] = useState<string>(DEFAULT_DIRECTORY_PATH);
  const [outputFileName, setOutputFileName] = useState<string>('');
  const [includeSubfolders, setIncludeSubfolders] = useState<boolean>(true);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [directoryPathError, setDirectoryPathError] = useState<string>('');

  console.log('[FKBrokerContractScanForm] Rendering', {
    directoryPath,
    includeSubfolders,
    disabled,
    isScanning,
  });

  /**
   * Validate directory path
   */
  const validateDirectoryPath = (value: string): string | null => {
    if (!value.trim()) {
      return 'La ruta del directorio es obligatoria';
    }

    // Check for path traversal attempts
    if (value.includes('..')) {
      return 'La ruta no puede contener ".."';
    }

    // Basic path validation (Windows or Unix-like paths)
    const pathRegex = /^([a-zA-Z]:[\\/]|\/|\\\\|~\/).+/;
    if (!pathRegex.test(value)) {
      return 'Ruta de directorio invalida (use ruta absoluta)';
    }

    return null;
  };

  /**
   * Handle directory path change
   */
  const handleDirectoryPathChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    const pathError = validateDirectoryPath(value);
    setDirectoryPathError(pathError || '');
    setDirectoryPath(value);
  };

  /**
   * Handle scan button click
   */
  const handleScan = async () => {
    console.log('[FKBrokerContractScanForm] Scan button clicked');

    // Validate directory path
    const pathError = validateDirectoryPath(directoryPath);
    if (pathError) {
      setDirectoryPathError(pathError);
      setError(pathError);
      return;
    }

    // Build scan configuration
    const config: BrokerContractScanConfig = {
      directory_path: directoryPath,
      include_subfolders: includeSubfolders,
      output_file_path: outputFileName || undefined,
    };

    console.log('[FKBrokerContractScanForm] Starting scan with config:', config);

    try {
      setIsScanning(true);
      setError('');

      await onScanStart(config);

      console.log('[FKBrokerContractScanForm] Scan completed successfully');
    } catch (err: unknown) {
      console.error('[FKBrokerContractScanForm] Scan failed:', err);
      setError(extractErrorMessage(err, 'Error al escanear contratos de brokers'));
    } finally {
      setIsScanning(false);
    }
  };

  const isFormValid = !directoryPathError && directoryPath.trim() !== '';

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        backgroundColor: 'background.paper',
        borderRadius: 2,
      }}
    >
      <Stack spacing={3}>
        {/* Header */}
        <Box display="flex" alignItems="center" gap={1}>
          <SearchIcon color="primary" />
          <Typography variant="h6" component="h2" color="primary">
            Configuracion de Escaneo
          </Typography>
        </Box>

        <Typography variant="body2" color="text.secondary">
          Escanea un directorio de contratos de brokers para extraer porcentajes
          de incentivos. Las carpetas deben seguir el formato{' '}
          <strong>YYYYMMDD Nombre Broker</strong> (ej: 20240515 Broker XYZ).
        </Typography>

        {/* Directory Path */}
        <TextField
          label="Ruta del Directorio"
          value={directoryPath}
          onChange={handleDirectoryPathChange}
          error={Boolean(directoryPathError)}
          helperText={
            directoryPathError ||
            'Ruta completa al directorio raiz con carpetas de brokers'
          }
          disabled={disabled || isScanning}
          required
          fullWidth
          variant="outlined"
          placeholder="/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/2024"
        />

        {/* Output File Name (Optional) */}
        <TextField
          label="Nombre de Archivo de Salida (Opcional)"
          value={outputFileName}
          onChange={(e) => setOutputFileName(e.target.value)}
          helperText="Si no se especifica, se generara automaticamente con timestamp"
          disabled={disabled || isScanning}
          fullWidth
          variant="outlined"
          placeholder="broker_incentives_20251216.xlsx"
        />

        {/* Options */}
        <Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={includeSubfolders}
                onChange={(e) => setIncludeSubfolders(e.target.checked)}
                disabled={disabled || isScanning}
                color="primary"
              />
            }
            label={
              <Box>
                <Typography variant="body2">Incluir Subcarpetas</Typography>
                <Typography variant="caption" color="text.secondary">
                  Escanea subcarpetas dentro del directorio raiz
                </Typography>
              </Box>
            }
          />
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Scan Button */}
        <Button
          variant="contained"
          size="large"
          onClick={handleScan}
          disabled={!isFormValid || disabled || isScanning}
          startIcon={
            isScanning ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <FolderOpenIcon />
            )
          }
          sx={{
            py: 1.5,
            fontWeight: 600,
          }}
        >
          {isScanning ? 'Escaneando Contratos...' : 'Escanear Directorio'}
        </Button>

        {/* Info Box */}
        <Alert severity="info" icon={false}>
          <Typography variant="caption" color="text.secondary">
            <strong>Nota:</strong> El escaneo extrae automaticamente:
            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
              <li>Tipo de contrato (Bono vs Incentivos)</li>
              <li>Porcentaje de incentivo por linea de credito (apertura)</li>
              <li>Porcentaje de incentivo por operaciones</li>
              <li>RFC y nombre del firmante</li>
            </ul>
          </Typography>
        </Alert>
      </Stack>
    </Paper>
  );
};

export default FKBrokerContractScanForm;
