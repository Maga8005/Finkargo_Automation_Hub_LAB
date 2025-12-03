/**
 * FKOtrosiRequest - Otrosí No. 1 contract request form for Operations department
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
} from '@mui/material';
import {
  Search as SearchIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';
import { operationsService } from '../../services/operationsService';
import { formatApiError } from '../../utils/errorUtils';
import type { Client, ContractGeneration } from '../../types/legal';

const FKOtrosiRequest: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [searchResults, setSearchResults] = useState<Client[]>([]);
  const [requestedContract, setRequestedContract] = useState<ContractGeneration | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const handleRequestContract = async () => {
    if (!selectedClient) {
      setError('Por favor seleccione un cliente');
      return;
    }

    setRequesting(true);
    setError(null);

    try {
      const contract = await operationsService.requestOtrosiGeneration(selectedClient.nit);

      setRequestedContract(contract);
      setSearchQuery('');
      setSelectedClient(null);
      setSearchResults([]);
    } catch (err: unknown) {
      // Use formatApiError to handle Pydantic validation errors and other error formats
      const errorMessage = formatApiError(err);
      setError(errorMessage);
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
            ¡Solicitud de Otrosí No. 1 enviada exitosamente!
          </Typography>
          <Typography variant="body2">
            ID: {requestedContract.contract_id} - El Otrosí está pendiente de revisión legal.
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
              Seleccione un cliente para solicitar el Otrosí No. 1
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
              Verifique los datos antes de solicitar el Otrosí No. 1
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

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => {
                  setSelectedClient(null);
                  setSearchResults([]);
                  setSearchQuery('');
                }}
                disabled={requesting}
              >
                Cancelar
              </Button>
              <Button
                variant="contained"
                size="large"
                startIcon={requesting ? <CircularProgress size={20} /> : <DescriptionIcon />}
                onClick={handleRequestContract}
                disabled={requesting}
              >
                {requesting ? 'Solicitando...' : 'Solicitar Otrosí No. 1'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default FKOtrosiRequest;
