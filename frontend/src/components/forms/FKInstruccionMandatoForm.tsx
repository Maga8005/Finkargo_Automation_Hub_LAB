/**
 * FKInstruccionMandatoForm - Instrucción de Mandato contract request form for Operations department
 * Specialized form with Cotización PDF upload, Bank Certificate upload, and creditor management
 *
 * Enhanced with DIAN checkbox support for mixed creditor types (DIAN and non-DIAN) in a single document.
 * When a creditor is marked as DIAN:
 * - Auto-fills predefined DIAN wording
 * - Disables bank certificate upload
 * - Sets account type to PSE
 * - Auto-detects DIAN creditors based on name patterns
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Divider,
  IconButton,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Chip,
} from '@mui/material';
import {
  Search as SearchIcon,
  UploadFile as UploadFileIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  AccountBalance as AccountBalanceIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';
import { operationsService } from '../../services/operationsService';
import type {
  Client,
  ContractGeneration,
  CotizacionData,
  AcreedorGastosNacionales,
  InstruccionMandatoRequest,
  BankCertificateData,
} from '../../types/legal';

// Maximum number of creditors allowed
const MAX_CREDITORS = 3;

// Account types available
const ACCOUNT_TYPES = ['Ahorros', 'Corriente', 'PSE'];

// DIAN Payment Constants
const DIAN_RAZON_SOCIAL = 'DIAN';
const DIAN_NIT = '800.197.268-4';
const DIAN_NA_MESSAGE = 'N/A – En la medida en que el pago del instrumento de pago se deberá realizar por el Mandato usando el link de pago enviado por el Mandante.';
const DIAN_KEYWORDS = ['DIAN', 'Direccion de Impuestos', 'Aduanas Nacionales', 'Entidad de pago de Impuestos'];
// Legacy constant for backwards compatibility
const DIAN_WORDING = DIAN_RAZON_SOCIAL;

/**
 * Check if a creditor name matches DIAN keywords for auto-detection
 * Uses case-insensitive matching to identify DIAN-related creditors
 * Prevents false positives (e.g., "GUARDIAN" should NOT match)
 */
const isDianCreditor = (acreedorName: string): boolean => {
  const nameLower = acreedorName.toLowerCase();
  return DIAN_KEYWORDS.some(keyword => {
    const keywordLower = keyword.toLowerCase();
    // For "DIAN", require it to be a word boundary to avoid false positives like "GUARDIAN"
    if (keywordLower === 'dian') {
      // Match DIAN as a standalone word (not part of another word)
      return /\bdian\b/i.test(acreedorName);
    }
    return nameLower.includes(keywordLower);
  });
};

/**
 * Normalize account type from bank certificate format to dropdown format
 * Maps: "CUENTA DE AHORROS" → "Ahorros", "CUENTA CORRIENTE" → "Corriente"
 */
const normalizeTipoCuenta = (tipoCuenta: string): string => {
  const lower = tipoCuenta.toLowerCase();
  if (lower.includes('ahorr')) return 'Ahorros';
  if (lower.includes('corriente')) return 'Corriente';
  if (lower.includes('pse')) return 'PSE';
  // Return original if no match (let validation catch it)
  return tipoCuenta;
};

const FKInstruccionMandatoForm: React.FC = () => {
  // Client search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [searchResults, setSearchResults] = useState<Client[]>([]);

  // Cotización PDF state
  const [cotizacionFile, setCotizacionFile] = useState<File | null>(null);
  const [cotizacionData, setCotizacionData] = useState<CotizacionData | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  // Form state (editable extracted data)
  const [numeroCotizacion, setNumeroCotizacion] = useState('');
  const [fechaMandato, setFechaMandato] = useState('');
  const [montoTotal, setMontoTotal] = useState(0);

  // Creditors state
  const [acreedores, setAcreedores] = useState<AcreedorGastosNacionales[]>([]);
  const [bankCertFiles, setBankCertFiles] = useState<Map<number, File>>(new Map());
  const [extractingBankCert, setExtractingBankCert] = useState<number | null>(null);

  // Submission state
  const [requesting, setRequesting] = useState(false);
  const [requestedContract, setRequestedContract] = useState<ContractGeneration | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Calculate total when acreedores change
  useEffect(() => {
    if (cotizacionData?.monto_total) {
      setMontoTotal(cotizacionData.monto_total);
    }
  }, [cotizacionData]);

  const handleSearch = async () => {
    setSearching(true);
    setError(null);
    setSearchResults([]);
    setSelectedClient(null);

    try {
      const results = await legalService.searchClients({ query: searchQuery.trim() || undefined });
      setSearchResults(results);

      if (results.length === 0) {
        setError('No se encontraron clientes con ese criterio de búsqueda');
      } else if (results.length === 1) {
        setSelectedClient(results[0]);
      }
    } catch (err) {
      setError('Error al buscar clientes. Por favor intente nuevamente.');
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setFileError('Solo se permiten archivos PDF');
      setCotizacionFile(null);
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setFileError('El archivo no debe superar 5MB');
      setCotizacionFile(null);
      return;
    }

    setCotizacionFile(file);
    setFileError(null);
    // Reset extracted data when new file is uploaded
    setCotizacionData(null);
    setAcreedores([]);
    setBankCertFiles(new Map());
  };

  const handleExtractCotizacion = async () => {
    if (!cotizacionFile) {
      setError('Debe seleccionar un archivo PDF primero');
      return;
    }

    setExtracting(true);
    setError(null);

    try {
      const data = await operationsService.parseCotizacionForMandato(cotizacionFile);
      setCotizacionData(data);

      // Pre-populate form fields
      setNumeroCotizacion(data.numero_cotizacion || '');
      setFechaMandato(data.fecha_contrato_credito || '');

      // Initialize acreedores from anexo_items with DIAN auto-detection
      const initialAcreedores: AcreedorGastosNacionales[] = (data.anexo_items || []).map(item => {
        const detectedAsDian = isDianCreditor(item.acreedor);

        if (detectedAsDian) {
          // Auto-fill DIAN creditor with predefined values per spec
          return {
            razon_social: DIAN_RAZON_SOCIAL,
            nit: DIAN_NIT,
            banco: DIAN_NA_MESSAGE,
            tipo_cuenta: DIAN_NA_MESSAGE,
            numero_cuenta: DIAN_NA_MESSAGE,
            es_dian: true,
          };
        } else {
          // Regular creditor - user needs to provide bank details
          return {
            razon_social: item.acreedor,
            nit: '',
            banco: '',
            tipo_cuenta: '',
            numero_cuenta: '',
            es_dian: false,
          };
        }
      });
      setAcreedores(initialAcreedores);

      setError(null);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(`Error al extraer datos del PDF: ${error.response?.data?.detail || error.message || 'Error desconocido'}`);
      console.error('Extract error:', err);
    } finally {
      setExtracting(false);
    }
  };

  const handleBankCertFileChange = (index: number) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setError('Solo se permiten archivos PDF para certificados bancarios');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError('El archivo no debe superar 5MB');
      return;
    }

    const newBankCertFiles = new Map(bankCertFiles);
    newBankCertFiles.set(index, file);
    setBankCertFiles(newBankCertFiles);
    setError(null);
  };

  const handleExtractBankCert = async (index: number) => {
    const file = bankCertFiles.get(index);
    if (!file) {
      setError('Debe seleccionar un archivo PDF de certificado bancario primero');
      return;
    }

    setExtractingBankCert(index);
    setError(null);

    try {
      const data: BankCertificateData = await operationsService.parseBankCertificate(file);

      // Update the specific creditor with extracted data
      const updatedAcreedores = [...acreedores];
      updatedAcreedores[index] = {
        ...updatedAcreedores[index],
        razon_social: data.razon_social || updatedAcreedores[index].razon_social,
        nit: data.nit || updatedAcreedores[index].nit,
        banco: data.banco || '',
        tipo_cuenta: data.tipo_cuenta ? normalizeTipoCuenta(data.tipo_cuenta) : '',
        numero_cuenta: data.numero_cuenta || '',
      };
      setAcreedores(updatedAcreedores);
      setError(null);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(`Error al extraer datos del certificado bancario: ${error.response?.data?.detail || error.message || 'Error desconocido'}`);
      console.error('Extract bank cert error:', err);
    } finally {
      setExtractingBankCert(null);
    }
  };

  const handleAcreedorChange = (index: number, field: keyof AcreedorGastosNacionales, value: string) => {
    const updated = [...acreedores];
    updated[index] = { ...updated[index], [field]: value };
    setAcreedores(updated);
  };

  /**
   * Handle DIAN checkbox toggle for a creditor
   * When checked: auto-fill DIAN predefined values and disable bank cert upload
   * When unchecked: clear auto-filled values and enable manual entry
   */
  const handleDianToggle = (index: number, checked: boolean) => {
    const updated = [...acreedores];
    if (checked) {
      // Mark as DIAN and auto-fill predefined values per spec
      updated[index] = {
        razon_social: DIAN_RAZON_SOCIAL,
        nit: DIAN_NIT,
        banco: DIAN_NA_MESSAGE,
        tipo_cuenta: DIAN_NA_MESSAGE,
        numero_cuenta: DIAN_NA_MESSAGE,
        es_dian: true,
      };
      // Remove bank certificate file for this creditor
      const newBankCertFiles = new Map(bankCertFiles);
      newBankCertFiles.delete(index);
      setBankCertFiles(newBankCertFiles);
    } else {
      // Unmark as DIAN and clear auto-filled values for manual entry
      updated[index] = {
        razon_social: '',
        nit: '',
        banco: '',
        tipo_cuenta: '',
        numero_cuenta: '',
        es_dian: false,
      };
    }
    setAcreedores(updated);
  };

  const handleAddAcreedor = () => {
    if (acreedores.length >= MAX_CREDITORS) {
      setError(`Máximo ${MAX_CREDITORS} acreedores permitidos`);
      return;
    }
    setAcreedores([
      ...acreedores,
      { razon_social: '', nit: '', banco: '', tipo_cuenta: '', numero_cuenta: '', es_dian: false },
    ]);
  };

  const handleRemoveAcreedor = (index: number) => {
    setAcreedores(acreedores.filter((_, i) => i !== index));
    const newBankCertFiles = new Map(bankCertFiles);
    newBankCertFiles.delete(index);
    // Re-index remaining files
    const reindexed = new Map<number, File>();
    let newIndex = 0;
    for (let i = 0; i < acreedores.length; i++) {
      if (i !== index && bankCertFiles.has(i)) {
        reindexed.set(newIndex, bankCertFiles.get(i)!);
      }
      if (i !== index) newIndex++;
    }
    setBankCertFiles(reindexed);
  };

  /**
   * Validate all creditors before submission
   * DIAN creditors: skip bank cert validation (auto-filled)
   * Non-DIAN creditors: require all bank account fields
   */
  const validateAcreedores = (): boolean => {
    for (let i = 0; i < acreedores.length; i++) {
      const acr = acreedores[i];

      // DIAN creditors have pre-filled values, just verify es_dian flag is set correctly
      if (acr.es_dian) {
        // DIAN creditor validation - values should be pre-filled
        if (acr.razon_social !== DIAN_WORDING) {
          setError(`Acreedor ${i + 1}: Datos de DIAN inconsistentes. Por favor desmarque y vuelva a marcar la casilla DIAN.`);
          return false;
        }
        // Skip remaining validation for DIAN creditors
        continue;
      }

      // Non-DIAN creditor validation - require all fields
      if (!acr.razon_social.trim()) {
        setError(`Acreedor ${i + 1}: Razón Social es requerida`);
        return false;
      }
      if (!acr.banco.trim()) {
        setError(`Acreedor ${i + 1}: Banco es requerido`);
        return false;
      }
      if (!acr.tipo_cuenta.trim()) {
        setError(`Acreedor ${i + 1}: Tipo de Cuenta es requerido`);
        return false;
      }
      if (!acr.numero_cuenta.trim()) {
        setError(`Acreedor ${i + 1}: Número de Cuenta es requerido`);
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!selectedClient) {
      setError('Por favor seleccione un cliente');
      return;
    }

    if (!numeroCotizacion) {
      setError('Número de cotización es requerido');
      return;
    }

    if (!fechaMandato) {
      setError('Fecha del contrato de mandato es requerida');
      return;
    }

    if (acreedores.length === 0) {
      setError('Debe agregar al menos un acreedor');
      return;
    }

    if (!validateAcreedores()) {
      return;
    }

    setRequesting(true);
    setError(null);

    try {
      const request: InstruccionMandatoRequest = {
        client_nit: selectedClient.nit,
        numero_cotizacion_desembolso: numeroCotizacion,
        fecha_contrato_mandato: fechaMandato,
        monto: montoTotal,
        acreedores: acreedores,
      };

      const contract = await operationsService.generateInstruccionMandato(request);
      setRequestedContract(contract);
      setError(null);
    } catch (err) {
      // Handle Pydantic validation errors which return as array of objects
      interface PydanticError {
        loc?: (string | number)[];
        msg?: string;
        type?: string;
      }
      const error = err as { response?: { data?: { detail?: string | PydanticError[] } }; message?: string };
      let errorMessage = 'Error desconocido';

      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors come as array of objects
          errorMessage = detail
            .map((e: PydanticError) => {
              const field = e.loc ? e.loc.slice(-1)[0] : 'campo';
              return `${field}: ${e.msg || 'error de validación'}`;
            })
            .join('; ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else {
          errorMessage = JSON.stringify(detail);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      setError(`Error al generar documento: ${errorMessage}`);
      console.error('Generation error:', err);
    } finally {
      setRequesting(false);
    }
  };

  const handleReset = () => {
    setSearchQuery('');
    setSelectedClient(null);
    setSearchResults([]);
    setCotizacionFile(null);
    setCotizacionData(null);
    setNumeroCotizacion('');
    setFechaMandato('');
    setMontoTotal(0);
    setAcreedores([]);
    setBankCertFiles(new Map());
    setRequestedContract(null);
    setError(null);
    setFileError(null);
  };

  if (requestedContract) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <CheckCircleIcon color="success" sx={{ fontSize: 48, mr: 2 }} />
            <Box>
              <Typography variant="h6" gutterBottom>
                Instrucción de Mandato Generada Exitosamente
              </Typography>
              <Typography variant="body2" color="text.secondary">
                El documento ha sido enviado al departamento Legal para revisión
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Stack spacing={2}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">ID de Contrato</Typography>
              <Typography variant="body1" fontWeight="medium">{requestedContract.contract_id}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Cliente</Typography>
              <Typography variant="body1">{selectedClient?.nombre_importador}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Número de Cotización</Typography>
              <Typography variant="body1">{numeroCotizacion}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Monto Total</Typography>
              <Typography variant="body1">${montoTotal.toLocaleString()} COP</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Acreedores</Typography>
              <Typography variant="body1">{acreedores.length} acreedor(es)</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Estado</Typography>
              <Typography variant="body1" color="warning.main">En Revisión</Typography>
            </Box>
          </Stack>

          <Box mt={3}>
            <Button variant="contained" onClick={handleReset} fullWidth>
              Generar Nueva Instrucción de Mandato
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Instrucción de Mandato
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Section 1: Client Search */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom fontWeight="medium">
            1. Seleccionar Cliente
          </Typography>

          <Stack direction="row" spacing={2} alignItems="center">
            <TextField
              fullWidth
              label="Buscar por NIT o Nombre"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              disabled={searching}
              size="small"
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
              startIcon={searching ? <CircularProgress size={20} /> : <SearchIcon />}
              sx={{ minWidth: 120 }}
            >
              Buscar
            </Button>
          </Stack>

          {searchResults.length > 1 && (
            <Box mt={2}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Resultados de búsqueda:
              </Typography>
              {searchResults.map((client) => (
                <Card
                  key={client.id}
                  variant="outlined"
                  sx={{
                    mb: 1,
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' },
                    bgcolor: selectedClient?.id === client.id ? 'action.selected' : 'inherit',
                  }}
                  onClick={() => setSelectedClient(client)}
                >
                  <CardContent sx={{ py: 1 }}>
                    <Typography variant="body1" fontWeight="medium">
                      {client.nombre_importador}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      NIT: {client.nit} | {client.ciudad_domicilio}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}

          {selectedClient && (
            <Box mt={2} p={2} bgcolor="success.lighter" borderRadius={1}>
              <Typography variant="body2" color="success.dark" fontWeight="medium">
                Cliente seleccionado: {selectedClient.nombre_importador} (NIT: {selectedClient.nit})
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Section 2: Cotización Upload */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom fontWeight="medium">
            2. Cargar Cotización PDF
          </Typography>

          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            id="cotizacion-mandato-upload"
          />
          <label htmlFor="cotizacion-mandato-upload">
            <Button variant="outlined" component="span" startIcon={<UploadFileIcon />} fullWidth>
              {cotizacionFile ? cotizacionFile.name : 'Seleccionar Archivo PDF'}
            </Button>
          </label>

          {fileError && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {fileError}
            </Alert>
          )}

          {cotizacionFile && !cotizacionData && (
            <Box mt={2}>
              <Button
                variant="contained"
                onClick={handleExtractCotizacion}
                disabled={extracting}
                startIcon={extracting ? <CircularProgress size={20} /> : <UploadFileIcon />}
                fullWidth
              >
                {extracting ? 'Extrayendo Datos...' : 'Extraer Datos del PDF'}
              </Button>
            </Box>
          )}

          {cotizacionData && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Datos extraídos exitosamente: {cotizacionData.anexo_items.length} acreedor(es) encontrado(s)
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Extracted Data (Editable) */}
      {cotizacionData && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom fontWeight="medium">
              3. Datos de la Instrucción de Mandato
            </Typography>

            <Stack spacing={2}>
              <TextField
                fullWidth
                label="Número de Cotización de Desembolso"
                value={numeroCotizacion}
                onChange={(e) => setNumeroCotizacion(e.target.value)}
                required
                size="small"
              />
              <TextField
                fullWidth
                label="Fecha del Contrato de Mandato"
                type="date"
                value={fechaMandato}
                onChange={(e) => setFechaMandato(e.target.value)}
                InputLabelProps={{ shrink: true }}
                required
                size="small"
              />
              <TextField
                fullWidth
                label="Monto Total"
                value={`$${montoTotal.toLocaleString()} COP`}
                InputProps={{ readOnly: true }}
                size="small"
              />
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Section 4: Creditor Bank Account Information */}
      {cotizacionData && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1" fontWeight="medium">
                4. Información Bancaria de Acreedores
              </Typography>
              {acreedores.length < MAX_CREDITORS && (
                <Button startIcon={<AddIcon />} onClick={handleAddAcreedor} size="small">
                  Agregar Acreedor
                </Button>
              )}
            </Box>

            {acreedores.length === 0 && (
              <Alert severity="info">
                No hay acreedores. Agregue al menos un acreedor para continuar.
              </Alert>
            )}

            {acreedores.map((acreedor, index) => (
              <Card
                key={index}
                variant="outlined"
                sx={{
                  mb: 2,
                  p: 2,
                  bgcolor: acreedor.es_dian ? 'primary.lighter' : 'inherit',
                  borderColor: acreedor.es_dian ? 'primary.main' : 'divider',
                }}
              >
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="subtitle2" fontWeight="medium">
                      Acreedor {index + 1}
                    </Typography>
                    {acreedor.es_dian && (
                      <Chip
                        label="DIAN"
                        size="small"
                        color="primary"
                        icon={<AccountBalanceIcon />}
                      />
                    )}
                  </Box>
                  <IconButton size="small" onClick={() => handleRemoveAcreedor(index)} color="error">
                    <DeleteIcon />
                  </IconButton>
                </Box>

                {/* DIAN Checkbox - Always visible at top of creditor card */}
                <Box mb={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={acreedor.es_dian || false}
                        onChange={(e) => handleDianToggle(index, e.target.checked)}
                        color="primary"
                      />
                    }
                    label={
                      <Typography variant="body2">
                        Es DIAN (Transferencia electrónica PSE a la DIAN)
                      </Typography>
                    }
                  />
                  {acreedor.es_dian && (
                    <Alert severity="info" sx={{ mt: 1 }}>
                      Este acreedor es un pago DIAN. Los datos bancarios se llenan automáticamente.
                    </Alert>
                  )}
                </Box>

                {/* Conditional rendering based on DIAN status */}
                {acreedor.es_dian ? (
                  /* DIAN Creditor: Show read-only info card */
                  <Box
                    sx={{
                      p: 2,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'grey.300',
                    }}
                  >
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Información de pago DIAN (auto-llenada):
                    </Typography>
                    <Stack spacing={1}>
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                        <Typography variant="body2" fontWeight="medium" sx={{ minWidth: 120 }}>Razón Social:</Typography>
                        <Typography variant="body2">{acreedor.razon_social}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                        <Typography variant="body2" fontWeight="medium" sx={{ minWidth: 120 }}>NIT:</Typography>
                        <Typography variant="body2">{acreedor.nit}</Typography>
                      </Box>
                      <Box display="flex" flexDirection="column" gap={0.5}>
                        <Typography variant="body2" fontWeight="medium">Banco / Tipo de Cuenta / Número de Cuenta:</Typography>
                        <Typography variant="body2" sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>
                          {DIAN_NA_MESSAGE}
                        </Typography>
                      </Box>
                    </Stack>
                  </Box>
                ) : (
                  /* Non-DIAN Creditor: Show editable fields and bank cert upload */
                  <>
                    {/* Bank Certificate Upload */}
                    <Box mb={2}>
                      <input
                        type="file"
                        accept="application/pdf"
                        onChange={handleBankCertFileChange(index)}
                        style={{ display: 'none' }}
                        id={`bank-cert-upload-${index}`}
                      />
                      <Stack direction="row" spacing={1} alignItems="center">
                        <label htmlFor={`bank-cert-upload-${index}`} style={{ flex: 1 }}>
                          <Button variant="outlined" component="span" startIcon={<UploadFileIcon />} fullWidth size="small">
                            {bankCertFiles.get(index)?.name || 'Cargar Certificado Bancario'}
                          </Button>
                        </label>
                        {bankCertFiles.has(index) && (
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => handleExtractBankCert(index)}
                            disabled={extractingBankCert === index}
                            startIcon={extractingBankCert === index ? <CircularProgress size={16} /> : undefined}
                          >
                            {extractingBankCert === index ? 'Extrayendo...' : 'Extraer Datos'}
                          </Button>
                        )}
                      </Stack>
                    </Box>

                    <Stack spacing={2}>
                      <TextField
                        fullWidth
                        label="Razón Social"
                        value={acreedor.razon_social}
                        onChange={(e) => handleAcreedorChange(index, 'razon_social', e.target.value)}
                        required
                        size="small"
                      />
                      <TextField
                        fullWidth
                        label="NIT (opcional)"
                        value={acreedor.nit || ''}
                        onChange={(e) => handleAcreedorChange(index, 'nit', e.target.value)}
                        size="small"
                      />
                      <TextField
                        fullWidth
                        label="Banco"
                        value={acreedor.banco}
                        onChange={(e) => handleAcreedorChange(index, 'banco', e.target.value)}
                        required
                        size="small"
                      />
                      <FormControl fullWidth size="small" required>
                        <InputLabel>Tipo de Cuenta</InputLabel>
                        <Select
                          value={acreedor.tipo_cuenta}
                          label="Tipo de Cuenta"
                          onChange={(e) => handleAcreedorChange(index, 'tipo_cuenta', e.target.value)}
                        >
                          {ACCOUNT_TYPES.map((type) => (
                            <MenuItem key={type} value={type}>
                              {type}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <TextField
                        fullWidth
                        label="Número de Cuenta"
                        value={acreedor.numero_cuenta}
                        onChange={(e) => handleAcreedorChange(index, 'numero_cuenta', e.target.value)}
                        required
                        size="small"
                      />
                    </Stack>
                  </>
                )}
              </Card>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Section 5: Submit */}
      {cotizacionData && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom fontWeight="medium">
              5. Generar Documento
            </Typography>

            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmit}
              disabled={requesting || !selectedClient || !numeroCotizacion || !fechaMandato || acreedores.length === 0}
              startIcon={requesting ? <CircularProgress size={20} /> : <CheckCircleIcon />}
              fullWidth
              size="large"
            >
              {requesting ? 'Generando...' : 'Generar Instrucción de Mandato'}
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default FKInstruccionMandatoForm;
