/**
 * FKInventarioRequest - Inventario Bodega de 3ro contract request form for Operations department
 */
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  Divider,
  Checkbox,
  FormControlLabel,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Warehouse as WarehouseIcon,
  CheckCircle as CheckCircleIcon,
  UploadFile as UploadFileIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';
import { operationsService } from '../../services/operationsService';
import type { Client, ContractGeneration } from '../../types/legal';

const FKInventarioRequest: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [searchResults, setSearchResults] = useState<Client[]>([]);
  const [requestedContract, setRequestedContract] = useState<ContractGeneration | null>(null);
  const [error, setError] = useState<string | null>(null);

  // RUT file upload state
  const [rutFile, setRutFile] = useState<File | null>(null);
  const [rutFileName, setRutFileName] = useState<string>('');
  const [fileError, setFileError] = useState<string | null>(null);

  // AI extraction state
  const [useAiExtraction, setUseAiExtraction] = useState(false);

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
        // Auto-select if only one result
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

    // Validate PDF
    if (file.type !== 'application/pdf') {
      setFileError('Solo se permiten archivos PDF');
      setRutFile(null);
      setRutFileName('');
      return;
    }

    // Validate size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setFileError('El archivo no debe superar 5MB');
      setRutFile(null);
      setRutFileName('');
      return;
    }

    setRutFile(file);
    setRutFileName(file.name);
    setFileError(null);
  };

  const handleRequestContract = async () => {
    if (!selectedClient) {
      setError('Por favor seleccione un cliente');
      return;
    }

    if (!rutFile) {
      setError('Debe cargar el documento RUT del operador custodio');
      return;
    }

    setRequesting(true);
    setError(null);
    setFileError(null);

    try {
      const contract = await operationsService.requestInventarioBodegaGeneration(
        selectedClient.nit,
        rutFile,
        useAiExtraction
      );

      setRequestedContract(contract);
      setSearchQuery('');
      setSelectedClient(null);
      setSearchResults([]);
      setRutFile(null);
      setRutFileName('');
      setUseAiExtraction(false);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const errorDetail = axiosError.response?.data?.detail || 'Error al solicitar el Inventario Bodega de 3ro';
      setError(errorDetail);
      console.error('Request error:', err);
    } finally {
      setRequesting(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Box>
      {/* Success Message */}
      {requestedContract && (
        <Alert
          severity="success"
          icon={<CheckCircleIcon />}
          sx={{ mb: 3 }}
          onClose={() => setRequestedContract(null)}
        >
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            ¡Solicitud de Inventario Bodega de 3ro enviada exitosamente!
          </Typography>
          <Typography variant="body2">
            ID: {requestedContract.contract_id} - El contrato está pendiente de revisión legal.
          </Typography>
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Search Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            Buscar Cliente
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Busque por NIT o nombre del importador. Deje vacío para ver todos los clientes.
          </Typography>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              placeholder="Ej: 900123456-1 o Importadora XYZ"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              disabled={searching}
            />
            <Button
              variant="contained"
              startIcon={searching ? <CircularProgress size={20} /> : <SearchIcon />}
              onClick={handleSearch}
              disabled={searching}
              sx={{ minWidth: 120 }}
            >
              {searching ? 'Buscando...' : 'Buscar'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResults.length > 1 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Resultados de Búsqueda ({searchResults.length})
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Seleccione un cliente para solicitar el Inventario Bodega de 3ro
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {searchResults.map((client) => (
                <Card
                  key={client.id}
                  variant="outlined"
                  sx={{
                    cursor: 'pointer',
                    border: selectedClient?.id === client.id ? 2 : 1,
                    borderColor: selectedClient?.id === client.id ? 'primary.main' : 'divider',
                    '&:hover': {
                      borderColor: 'primary.light',
                      bgcolor: 'grey.50',
                    },
                  }}
                  onClick={() => setSelectedClient(client)}
                >
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, md: 6 }}>
                        <Typography variant="body2" color="text.secondary">
                          Importador
                        </Typography>
                        <Typography variant="body1" sx={{ fontWeight: 600 }}>
                          {client.nombre_importador}
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                          NIT
                        </Typography>
                        <Typography variant="body1">{client.nit}</Typography>
                      </Grid>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                          Cupo
                        </Typography>
                        <Typography variant="body1" sx={{ fontWeight: 600, color: 'primary.main' }}>
                          {formatCurrency(client.cupo_plataforma)}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Client Preview & Request */}
      {selectedClient && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Datos del Cliente Seleccionado
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Verifique los datos antes de solicitar el Inventario Bodega de 3ro
            </Typography>

            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Nombre del Importador
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {selectedClient.nombre_importador}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  NIT
                </Typography>
                <Typography variant="body1">{selectedClient.nit}</Typography>
              </Grid>

              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Cupo Plataforma
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  {formatCurrency(selectedClient.cupo_plataforma)}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Representante Legal
                </Typography>
                <Typography variant="body1">{selectedClient.representante_legal}</Typography>
              </Grid>

              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Cédula Representante
                </Typography>
                <Typography variant="body1">{selectedClient.cedula_representante}</Typography>
              </Grid>

              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Ciudad de Domicilio
                </Typography>
                <Typography variant="body1">{selectedClient.ciudad_domicilio}</Typography>
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Documento RUT del Operador Custodio
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Suba el documento RUT (Registro Único Tributario) del operador de bodega de terceros
            </Typography>

            <Box sx={{ mb: 3 }}>
              <input
                accept="application/pdf"
                style={{ display: 'none' }}
                id="rut-file-upload"
                type="file"
                onChange={handleFileChange}
              />
              <label htmlFor="rut-file-upload">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<UploadFileIcon />}
                  fullWidth
                  sx={{ height: 56 }}
                >
                  {rutFileName || 'Seleccionar archivo RUT (PDF)'}
                </Button>
              </label>

              {fileError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {fileError}
                </Alert>
              )}

              {rutFile && !fileError && (
                <Alert severity="success" sx={{ mt: 2 }} icon={<CheckCircleIcon />}>
                  Archivo cargado: {rutFileName}
                </Alert>
              )}

              {rutFile && !fileError && (
                <Box sx={{ mt: 2 }}>
                  <Tooltip
                    title="Usa inteligencia artificial para extraer datos de documentos escaneados. Más robusto pero toma más tiempo (30-60 segundos)."
                    arrow
                    placement="right"
                  >
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={useAiExtraction}
                          onChange={(e) => setUseAiExtraction(e.target.checked)}
                        />
                      }
                      label="Usar extracción AI (para PDFs escaneados)"
                    />
                  </Tooltip>
                </Box>
              )}
            </Box>

            <Divider sx={{ my: 3 }} />

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => {
                  setSelectedClient(null);
                  setSearchResults([]);
                  setSearchQuery('');
                  setRutFile(null);
                  setRutFileName('');
                  setFileError(null);
                  setUseAiExtraction(false);
                }}
                disabled={requesting}
              >
                Cancelar
              </Button>
              <Button
                variant="contained"
                size="large"
                startIcon={requesting ? <CircularProgress size={20} /> : <WarehouseIcon />}
                onClick={handleRequestContract}
                disabled={requesting || !rutFile}
                sx={{ bgcolor: 'success.main', '&:hover': { bgcolor: 'success.dark' } }}
              >
                {requesting
                  ? (useAiExtraction ? 'Extrayendo datos con AI...' : 'Solicitando...')
                  : 'Solicitar Inventario Bodega de 3ro'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default FKInventarioRequest;
