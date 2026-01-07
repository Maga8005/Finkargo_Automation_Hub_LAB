/**
 * FKDIANMandatoForm - DIAN Mandato (IM) contract request form for Operations department
 * Simplified form with Cotización PDF upload only (no Bank Certificate needed for DIAN payments)
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
  Stack,
} from '@mui/material';
import {
  Search as SearchIcon,
  UploadFile as UploadFileIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';
import { operationsService } from '../../services/operationsService';
import type {
  Client,
  ContractGeneration,
  CotizacionData,
  DIANMandatoRequest,
} from '../../types/legal';

const FKDIANMandatoForm: React.FC = () => {
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

  // Submission state
  const [requesting, setRequesting] = useState(false);
  const [requestedContract, setRequestedContract] = useState<ContractGeneration | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Update monto when cotizacion data changes
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
  };

  const handleExtractCotizacion = async () => {
    if (!cotizacionFile) {
      setError('Debe seleccionar un archivo PDF primero');
      return;
    }

    setExtracting(true);
    setError(null);

    try {
      const data = await operationsService.parseCotizacionForDIANMandato(cotizacionFile);
      setCotizacionData(data);

      // Pre-populate form fields
      setNumeroCotizacion(data.numero_cotizacion || '');
      setFechaMandato(data.fecha_contrato_credito || '');

      setError(null);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(`Error al extraer datos del PDF: ${error.response?.data?.detail || error.message || 'Error desconocido'}`);
      console.error('Extract error:', err);
    } finally {
      setExtracting(false);
    }
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

    if (montoTotal <= 0) {
      setError('El monto debe ser mayor a cero');
      return;
    }

    setRequesting(true);
    setError(null);

    try {
      const request: DIANMandatoRequest = {
        client_nit: selectedClient.nit,
        numero_cotizacion_desembolso: numeroCotizacion,
        fecha_contrato_mandato: fechaMandato,
        monto: montoTotal,
      };

      const contract = await operationsService.generateDIANMandato(request);
      setRequestedContract(contract);
      setError(null);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(`Error al generar documento: ${error.response?.data?.detail || error.message || 'Error desconocido'}`);
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
                DIAN Mandato (IM) Generado Exitosamente
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
              <Typography variant="subtitle2" color="text.secondary">Tipo de Documento</Typography>
              <Typography variant="body1">DIAN Mandato (IM)</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">Estado</Typography>
              <Typography variant="body1" color="warning.main">En Revisión</Typography>
            </Box>
          </Stack>

          <Box mt={3}>
            <Button variant="contained" onClick={handleReset} fullWidth>
              Generar Nuevo DIAN Mandato (IM)
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Template DIAN - Mandato (IM)
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Documento simplificado para pagos a la DIAN. No requiere certificados bancarios.
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
            id="cotizacion-dian-mandato-upload"
          />
          <label htmlFor="cotizacion-dian-mandato-upload">
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
              Datos extraídos exitosamente del documento de cotización
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Extracted Data (Editable) */}
      {cotizacionData && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom fontWeight="medium">
              3. Datos del DIAN Mandato (IM)
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
                required
                size="small"
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                label="Monto Total (COP)"
                type="number"
                value={montoTotal}
                onChange={(e) => setMontoTotal(Number(e.target.value))}
                required
                size="small"
                InputProps={{
                  startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
                }}
              />
            </Stack>

            <Alert severity="info" sx={{ mt: 2 }}>
              Este documento es para pagos a la DIAN. No se requiere información bancaria adicional.
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Section 4: Generate Document */}
      {cotizacionData && selectedClient && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom fontWeight="medium">
              4. Generar Documento
            </Typography>

            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmit}
              disabled={requesting || !numeroCotizacion || !fechaMandato || montoTotal <= 0}
              startIcon={requesting ? <CircularProgress size={20} /> : null}
              fullWidth
              size="large"
            >
              {requesting ? 'Generando...' : 'Generar DIAN Mandato (IM)'}
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default FKDIANMandatoForm;
