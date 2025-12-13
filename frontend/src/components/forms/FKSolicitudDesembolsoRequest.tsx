/**
 * FKSolicitudDesembolsoRequest - Solicitud de Desembolso contract request form for Operations department
 * Specialized form with PDF upload, data extraction, and dynamic Anexo I table
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Paper,
  Stack,
} from '@mui/material';
import {
  Search as SearchIcon,
  UploadFile as UploadFileIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';
import { operationsService } from '../../services/operationsService';
import type { Client, ContractGeneration, AnexoItem, CotizacionData, SolicitudDesembolsoRequest } from '../../types/legal';

const FKSolicitudDesembolsoRequest: React.FC = () => {
  // Client search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [searchResults, setSearchResults] = useState<Client[]>([]);

  // Cotización PDF state
  const [cotizacionFile, setCotizacionFile] = useState<File | null>(null);
  const [extractedData, setExtractedData] = useState<CotizacionData | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  // Form state
  const [numeroCotizacion, setNumeroCotizacion] = useState('');
  const [fechaContrato, setFechaContrato] = useState('');
  const [diasPlazo, setDiasPlazo] = useState(120);
  const [iteracionContrato, setIteracionContrato] = useState(1);
  const [anexoItems, setAnexoItems] = useState<AnexoItem[]>([]);
  const [montoTotal, setMontoTotal] = useState(0);

  // Submission state
  const [requesting, setRequesting] = useState(false);
  const [requestedContract, setRequestedContract] = useState<ContractGeneration | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Calculate total when anexo items change
  useEffect(() => {
    const total = anexoItems.reduce((sum, item) => {
      // Ensure monto is treated as a number (defensive check for string values)
      const monto = typeof item.monto === 'string' ? parseFloat(item.monto) : Number(item.monto);
      return sum + (monto || 0);
    }, 0);
    setMontoTotal(total);
  }, [anexoItems]);

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
    setExtractedData(null);
  };

  const handleExtractData = async () => {
    if (!cotizacionFile) {
      setError('Debe seleccionar un archivo PDF primero');
      return;
    }

    setExtracting(true);
    setError(null);

    try {
      const data = await operationsService.parseCotizacionPdf(cotizacionFile);
      setExtractedData(data);

      // Pre-populate form fields
      setNumeroCotizacion(data.numero_cotizacion || '');
      setFechaContrato(data.fecha_contrato_credito || '');

      // Convert monto from string to number for each anexo item
      // Backend serializes Decimal as string, frontend needs numbers for calculations
      const convertedItems = (data.anexo_items || []).map(item => ({
        ...item,
        monto: typeof item.monto === 'string' ? parseFloat(item.monto) : Number(item.monto)
      }));
      setAnexoItems(convertedItems);

      setError(null);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(`Error al extraer datos del PDF: ${error.response?.data?.detail || error.message || 'Error desconocido'}`);
      console.error('Extract error:', err);
    } finally {
      setExtracting(false);
    }
  };

  const handleAddAnexoRow = () => {
    setAnexoItems([...anexoItems, { acreedor: '', numero_instrumento: '', monto: 0 }]);
  };

  const handleRemoveAnexoRow = (index: number) => {
    setAnexoItems(anexoItems.filter((_, i) => i !== index));
  };

  const handleAnexoItemChange = (index: number, field: keyof AnexoItem, value: string | number) => {
    const updated = [...anexoItems];
    updated[index] = { ...updated[index], [field]: value };
    setAnexoItems(updated);
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

    if (!fechaContrato) {
      setError('Fecha de contrato de crédito es requerida');
      return;
    }

    if (anexoItems.length === 0) {
      setError('Debe agregar al menos un ítem en el Anexo I');
      return;
    }

    if (montoTotal <= 0) {
      setError('El monto total debe ser mayor a 0');
      return;
    }

    setRequesting(true);
    setError(null);

    try {
      const request: SolicitudDesembolsoRequest = {
        client_nit: selectedClient.nit,
        numero_cotizacion_desembolso: numeroCotizacion,
        fecha_contrato_credito: fechaContrato,
        monto: montoTotal,
        dias_plazo: diasPlazo,
        iteracion_contrato: iteracionContrato,
        anexo_items: anexoItems,
      };

      const contract = await operationsService.generateSolicitudDesembolso(request);
      setRequestedContract(contract);
      setError(null);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(`Error al generar solicitud: ${error.response?.data?.detail || error.message || 'Error desconocido'}`);
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
    setExtractedData(null);
    setNumeroCotizacion('');
    setFechaContrato('');
    setDiasPlazo(120);
    setIteracionContrato(1);
    setAnexoItems([]);
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
                Solicitud de Desembolso Generada Exitosamente
              </Typography>
              <Typography variant="body2" color="text.secondary">
                La solicitud ha sido enviada al departamento Legal para revisión
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
              <Typography variant="subtitle2" color="text.secondary">Estado</Typography>
              <Typography variant="body1" color="warning.main">En Revisión</Typography>
            </Box>
          </Stack>

          <Box mt={3}>
            <Button variant="contained" onClick={handleReset} fullWidth>
              Generar Nueva Solicitud
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Solicitud de Desembolso
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
            id="cotizacion-upload"
          />
          <label htmlFor="cotizacion-upload">
            <Button variant="outlined" component="span" startIcon={<UploadFileIcon />} fullWidth>
              {cotizacionFile ? cotizacionFile.name : 'Seleccionar Archivo PDF'}
            </Button>
          </label>

          {fileError && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {fileError}
            </Alert>
          )}

          {cotizacionFile && !extractedData && (
            <Box mt={2}>
              <Button
                variant="contained"
                onClick={handleExtractData}
                disabled={extracting}
                startIcon={extracting ? <CircularProgress size={20} /> : <UploadFileIcon />}
                fullWidth
              >
                {extracting ? 'Extrayendo Datos...' : 'Extraer Datos del PDF'}
              </Button>
            </Box>
          )}

          {extractedData && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Datos extraídos exitosamente: {extractedData.anexo_items.length} ítems encontrados
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Extracted Data (Editable) */}
      {extractedData && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom fontWeight="medium">
              3. Datos de la Solicitud
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
                label="Iteración del Contrato"
                type="number"
                value={iteracionContrato}
                onChange={(e) => setIteracionContrato(Number(e.target.value))}
                inputProps={{ min: 1, max: 99 }}
                required
                size="small"
                helperText="Número de iteración proporcionado por Mesa de Control (1-99)"
              />
              <TextField
                fullWidth
                label="Fecha del Contrato de Crédito"
                type="date"
                value={fechaContrato}
                onChange={(e) => setFechaContrato(e.target.value)}
                InputLabelProps={{ shrink: true }}
                required
                size="small"
              />
              <TextField
                fullWidth
                label="Días de Plazo"
                type="number"
                value={diasPlazo}
                onChange={(e) => setDiasPlazo(Number(e.target.value))}
                inputProps={{ min: 30, max: 180 }}
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

      {/* Section 4: Anexo I Table */}
      {extractedData && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1" fontWeight="medium">
                4. Anexo I - Detalle de Pagos
              </Typography>
              <Button startIcon={<AddIcon />} onClick={handleAddAnexoRow} size="small">
                Agregar Fila
              </Button>
            </Box>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Acreedor</TableCell>
                    <TableCell>No. Instrumento</TableCell>
                    <TableCell>Monto (COP)</TableCell>
                    <TableCell width={60}>Acción</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {anexoItems.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <TextField
                          fullWidth
                          value={item.acreedor}
                          onChange={(e) => handleAnexoItemChange(index, 'acreedor', e.target.value)}
                          size="small"
                          variant="standard"
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          value={item.numero_instrumento}
                          onChange={(e) => handleAnexoItemChange(index, 'numero_instrumento', e.target.value)}
                          size="small"
                          variant="standard"
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          type="number"
                          value={item.monto}
                          onChange={(e) => handleAnexoItemChange(index, 'monto', Number(e.target.value))}
                          size="small"
                          variant="standard"
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => handleRemoveAnexoRow(index)} color="error">
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell colSpan={2} align="right">
                      <strong>TOTAL:</strong>
                    </TableCell>
                    <TableCell colSpan={2}>
                      <strong>${montoTotal.toLocaleString()} COP</strong>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Section 5: Submit */}
      {extractedData && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom fontWeight="medium">
              5. Generar Solicitud
            </Typography>

            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmit}
              disabled={requesting || !selectedClient || !numeroCotizacion || !fechaContrato || anexoItems.length === 0}
              startIcon={requesting ? <CircularProgress size={20} /> : <CheckCircleIcon />}
              fullWidth
              size="large"
            >
              {requesting ? 'Generando...' : 'Solicitar Documento'}
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default FKSolicitudDesembolsoRequest;
