/**
 * FKContractGenerator - Contract generation form component
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
import type { Client, ContractGeneration } from '../../types/legal';

const FKContractGenerator: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [searchResults, setSearchResults] = useState<Client[]>([]);
  const [generatedContract, setGeneratedContract] = useState<ContractGeneration | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Por favor ingrese un NIT o nombre para buscar');
      return;
    }

    setSearching(true);
    setError(null);
    setSearchResults([]);
    setSelectedClient(null);

    try {
      const results = await legalService.searchClients({ query: searchQuery });
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

  const handleGenerateContract = async () => {
    if (!selectedClient) {
      setError('Por favor seleccione un cliente');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const contract = await legalService.generateContract({
        client_nit: selectedClient.nit,
      });

      setGeneratedContract(contract);
      setSearchQuery('');
      setSelectedClient(null);
      setSearchResults([]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al generar el contrato');
      console.error('Generation error:', err);
    } finally {
      setGenerating(false);
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
      {generatedContract && (
        <Alert
          severity="success"
          icon={<CheckCircleIcon />}
          sx={{ mb: 3 }}
          onClose={() => setGeneratedContract(null)}
        >
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            ¡Contrato generado exitosamente!
          </Typography>
          <Typography variant="body2">
            ID: {generatedContract.contract_id} - El contrato está en cola de revisión legal.
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
            Busque por NIT o nombre del importador
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
              disabled={searching || !searchQuery.trim()}
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
              Seleccione un cliente para generar el contrato
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

      {/* Client Preview & Generate */}
      {selectedClient && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Datos del Cliente Seleccionado
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Verifique los datos antes de generar el contrato
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
                disabled={generating}
              >
                Cancelar
              </Button>
              <Button
                variant="contained"
                size="large"
                startIcon={generating ? <CircularProgress size={20} /> : <DescriptionIcon />}
                onClick={handleGenerateContract}
                disabled={generating}
              >
                {generating ? 'Generando...' : 'Generar Contrato'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default FKContractGenerator;
