/**
 * FKDirectoryScanForm - Directory scan configuration form
 *
 * Provides form inputs for configuring local directory scanning:
 * - Directory path
 * - Output file name (optional)
 * - Extract declaration numbers toggle
 * - Recursive scan toggle
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
import type { LocalDirectoryScanConfig } from '../../services/directoryScannerService';
import { extractErrorMessage } from '../../utils/errorUtils';

interface FKDirectoryScanFormProps {
  onScanStart: (config: LocalDirectoryScanConfig) => Promise<void>;
  disabled?: boolean;
}

const DEFAULT_DIRECTORY_PATH =
  'C:/Users/Usuario/Finkargo_Automation_Hub/Exchange Declarations and Legalization Process/FINKARGO DCS';

const FKDirectoryScanForm: React.FC<FKDirectoryScanFormProps> = ({
  onScanStart,
  disabled = false,
}) => {
  const [directoryPath, setDirectoryPath] = useState<string>(
    DEFAULT_DIRECTORY_PATH
  );
  const [outputFileName, setOutputFileName] = useState<string>('');
  const [extractDeclarationNumbers, setExtractDeclarationNumbers] =
    useState<boolean>(true);
  const [recursive, setRecursive] = useState<boolean>(true);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [directoryPathError, setDirectoryPathError] = useState<string>('');

  console.log('[FKDirectoryScanForm] Rendering', {
    directoryPath,
    extractDeclarationNumbers,
    recursive,
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

    // Basic path validation (Windows or Unix-like paths)
    const pathRegex = /^([a-zA-Z]:[\\/]|\/|\\\\).+/;
    if (!pathRegex.test(value)) {
      return 'Ruta de directorio inválida';
    }

    return null;
  };

  /**
   * Handle directory path change
   */
  const handleDirectoryPathChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    const error = validateDirectoryPath(value);
    setDirectoryPathError(error || '');
    setDirectoryPath(value);
  };

  /**
   * Handle scan button click
   */
  const handleScan = async () => {
    console.log('[FKDirectoryScanForm] Scan button clicked');

    // Validate directory path
    const pathError = validateDirectoryPath(directoryPath);
    if (pathError) {
      setDirectoryPathError(pathError);
      setError(pathError);
      return;
    }

    // Build scan configuration
    const config: LocalDirectoryScanConfig = {
      directory_path: directoryPath,
      output_file_path: outputFileName || undefined,
      extract_declaration_numbers: extractDeclarationNumbers,
      recursive,
      pdf_extensions: ['.pdf', '.PDF'],
    };

    console.log('[FKDirectoryScanForm] Starting scan with config:', config);

    try {
      setIsScanning(true);
      setError('');

      await onScanStart(config);

      console.log('[FKDirectoryScanForm] Scan completed successfully');
    } catch (err: unknown) {
      console.error('[FKDirectoryScanForm] Scan failed:', err);
      setError(extractErrorMessage(err, 'Error al escanear directorio'));
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
          <FolderOpenIcon color="primary" />
          <Typography variant="h6" component="h2" color="primary">
            Escaneo de Directorio Local
          </Typography>
        </Box>

        <Typography variant="body2" color="text.secondary">
          Escanea un directorio local para generar un inventario de archivos
          PDF de declaraciones. El sistema extraerá metadata de la estructura
          de carpetas y opcionalmente los números de declaración de los PDFs.
        </Typography>

        {/* Directory Path */}
        <TextField
          label="Ruta del Directorio"
          value={directoryPath}
          onChange={handleDirectoryPathChange}
          error={Boolean(directoryPathError)}
          helperText={
            directoryPathError ||
            'Ruta completa al directorio raíz (ej: C:/FINKARGO DCS)'
          }
          disabled={disabled || isScanning}
          required
          fullWidth
          variant="outlined"
        />

        {/* Output File Name (Optional) */}
        <TextField
          label="Nombre de Archivo de Salida (Opcional)"
          value={outputFileName}
          onChange={(e) => setOutputFileName(e.target.value)}
          helperText="Si no se especifica, se generará automáticamente con timestamp"
          disabled={disabled || isScanning}
          fullWidth
          variant="outlined"
          placeholder="inventory_20251103.xlsx"
        />

        {/* Options */}
        <Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={extractDeclarationNumbers}
                onChange={(e) =>
                  setExtractDeclarationNumbers(e.target.checked)
                }
                disabled={disabled || isScanning}
                color="primary"
              />
            }
            label={
              <Box>
                <Typography variant="body2">
                  Extraer Números de Declaración
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Extrae los números de declaración de los PDFs (proceso más
                  lento pero más completo)
                </Typography>
              </Box>
            }
          />
        </Box>

        <Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={recursive}
                onChange={(e) => setRecursive(e.target.checked)}
                disabled={disabled || isScanning}
                color="primary"
              />
            }
            label={
              <Box>
                <Typography variant="body2">Escaneo Recursivo</Typography>
                <Typography variant="caption" color="text.secondary">
                  Escanea subdirectorios de forma recursiva
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
          {isScanning ? 'Escaneando...' : 'Escanear Directorio'}
        </Button>

        {/* Info Box */}
        <Alert severity="info" icon={false}>
          <Typography variant="caption" color="text.secondary">
            <strong>Nota:</strong> El escaneo puede tomar varios minutos
            dependiendo del número de archivos PDF. Si se activa la extracción
            de números de declaración, el proceso será más lento.
          </Typography>
        </Alert>
      </Stack>
    </Paper>
  );
};

export default FKDirectoryScanForm;
