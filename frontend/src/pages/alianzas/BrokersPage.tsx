/**
 * BrokersPage - Main page for broker management in the Alianzas module
 * Displays list of brokers with search, filter, create/edit/delete functionality
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  People as PeopleIcon,
} from '@mui/icons-material';

import { alianzasService } from '../../services/alianzasService';
import FKBrokerForm from '../../components/alianzas/FKBrokerForm';
import type {
  Broker,
  BrokerCreateRequest,
  BrokerUpdateRequest,
  MasterBrokerOption,
  TipoBroker,
  EstadoBroker,
} from '../../types/alianzas';
import {
  TIPO_BROKER_LABELS,
  ESTADO_BROKER_LABELS,
  ESTADO_BROKER_COLORS,
} from '../../types/alianzas';

const BrokersPage: React.FC = () => {
  // Data state
  const [brokers, setBrokers] = useState<Broker[]>([]);
  const [masterBrokerOptions, setMasterBrokerOptions] = useState<MasterBrokerOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Filter state
  const [searchNombre, setSearchNombre] = useState('');
  const [filterTipo, setFilterTipo] = useState<string>('');
  const [filterEstado, setFilterEstado] = useState<string>('');

  // Dialog state
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedBroker, setSelectedBroker] = useState<Broker | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Load brokers
  const loadBrokers = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params: {
        active_only?: boolean;
        tipo_broker?: string;
        estado?: string;
      } = {
        active_only: false, // Show all by default
      };

      if (filterTipo) params.tipo_broker = filterTipo;
      if (filterEstado) params.estado = filterEstado;

      const data = await alianzasService.getBrokers(params);
      setBrokers(data);
    } catch (err) {
      console.error('Error loading brokers:', err);
      setError('Error al cargar los brokers. Por favor intente nuevamente.');
    } finally {
      setLoading(false);
    }
  }, [filterTipo, filterEstado]);

  // Load master broker options for form
  const loadMasterBrokers = useCallback(async () => {
    try {
      const data = await alianzasService.getMasterBrokers();
      setMasterBrokerOptions(data);
    } catch (err) {
      console.error('Error loading master brokers:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadBrokers();
    loadMasterBrokers();
  }, [loadBrokers, loadMasterBrokers]);

  // Filter brokers by search term (client-side)
  const filteredBrokers = brokers.filter((broker) => {
    if (!searchNombre) return true;
    return broker.nombre.toLowerCase().includes(searchNombre.toLowerCase());
  });

  // Handle search
  const handleSearch = async () => {
    if (!searchNombre.trim()) {
      loadBrokers();
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await alianzasService.searchBrokers({
        nombre: searchNombre.trim(),
        tipo_broker: filterTipo ? (filterTipo as TipoBroker) : undefined,
        estado: filterEstado ? (filterEstado as EstadoBroker) : undefined,
        active_only: false,
      });
      setBrokers(data);
    } catch (err) {
      console.error('Error searching brokers:', err);
      setError('Error al buscar brokers.');
    } finally {
      setLoading(false);
    }
  };

  // Handle create/edit form submission
  const handleFormSubmit = async (data: BrokerCreateRequest | BrokerUpdateRequest) => {
    setFormLoading(true);
    setError(null);

    try {
      if (selectedBroker) {
        // Update
        await alianzasService.updateBroker(selectedBroker.id, data as BrokerUpdateRequest);
        setSuccess(`Broker "${(data as BrokerUpdateRequest).nombre || selectedBroker.nombre}" actualizado exitosamente.`);
      } else {
        // Create
        const created = await alianzasService.createBroker(data as BrokerCreateRequest);
        setSuccess(`Broker "${created.nombre}" creado exitosamente.`);
      }

      setFormDialogOpen(false);
      setSelectedBroker(null);
      loadBrokers();
      loadMasterBrokers(); // Refresh in case a new master broker was added
    } catch (err) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const errorMessage = axiosError.response?.data?.detail || 'Error al guardar el broker.';
      setError(errorMessage);
    } finally {
      setFormLoading(false);
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!selectedBroker) return;

    setDeleteLoading(true);
    setError(null);

    try {
      await alianzasService.deleteBroker(selectedBroker.id);
      setSuccess(`Broker "${selectedBroker.nombre}" eliminado exitosamente.`);
      setDeleteDialogOpen(false);
      setSelectedBroker(null);
      loadBrokers();
    } catch (err) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const errorMessage = axiosError.response?.data?.detail || 'Error al eliminar el broker.';
      setError(errorMessage);
    } finally {
      setDeleteLoading(false);
    }
  };

  // Open create dialog
  const handleOpenCreate = () => {
    setSelectedBroker(null);
    setFormDialogOpen(true);
  };

  // Open edit dialog
  const handleOpenEdit = (broker: Broker) => {
    setSelectedBroker(broker);
    setFormDialogOpen(true);
  };

  // Open delete dialog
  const handleOpenDelete = (broker: Broker) => {
    setSelectedBroker(broker);
    setDeleteDialogOpen(true);
  };

  // Format percentage for display
  const formatPercentage = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(2)}%`;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <PeopleIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              Gestión de Brokers
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Administra los brokers y sus comisiones
            </Typography>
          </Box>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreate}
          size="large"
        >
          Nuevo Broker
        </Button>
      </Box>

      {/* Success/Error Messages */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <TextField
              label="Buscar por nombre"
              value={searchNombre}
              onChange={(e) => setSearchNombre(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              size="small"
              sx={{ minWidth: 250 }}
            />
            <TextField
              select
              label="Tipo"
              value={filterTipo}
              onChange={(e) => setFilterTipo(e.target.value)}
              size="small"
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="">Todos</MenuItem>
              {Object.entries(TIPO_BROKER_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Estado"
              value={filterEstado}
              onChange={(e) => setFilterEstado(e.target.value)}
              size="small"
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">Todos</MenuItem>
              {Object.entries(ESTADO_BROKER_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </TextField>
            <Button
              variant="outlined"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
            >
              Buscar
            </Button>
            <Tooltip title="Actualizar lista">
              <IconButton onClick={loadBrokers} color="primary">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </CardContent>
      </Card>

      {/* Brokers Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Nombre</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Tipo</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Estado</TableCell>
                <TableCell sx={{ fontWeight: 600 }} align="right">% Apertura</TableCell>
                <TableCell sx={{ fontWeight: 600 }} align="right">% Operativa</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Banco</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>RFC</TableCell>
                <TableCell sx={{ fontWeight: 600 }} align="center">Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                    <Typography variant="body2" sx={{ mt: 2 }}>
                      Cargando brokers...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : filteredBrokers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No se encontraron brokers
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {searchNombre || filterTipo || filterEstado
                        ? 'Intenta con otros filtros'
                        : 'Crea el primer broker haciendo clic en "Nuevo Broker"'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredBrokers.map((broker) => (
                  <TableRow
                    key={broker.id}
                    hover
                    sx={{
                      '&:last-child td, &:last-child th': { border: 0 },
                      opacity: broker.estado === 'inactivo' ? 0.6 : 1,
                    }}
                  >
                    <TableCell>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {broker.nombre}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {TIPO_BROKER_LABELS[broker.tipo_broker as TipoBroker] || broker.tipo_broker}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={ESTADO_BROKER_LABELS[broker.estado as EstadoBroker] || broker.estado}
                        color={ESTADO_BROKER_COLORS[broker.estado as EstadoBroker] || 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      {formatPercentage(broker.porcentaje_apertura)}
                    </TableCell>
                    <TableCell align="right">
                      {formatPercentage(broker.porcentaje_operativa)}
                    </TableCell>
                    <TableCell>{broker.banco || '-'}</TableCell>
                    <TableCell>{broker.rfc || '-'}</TableCell>
                    <TableCell align="center">
                      <Tooltip title="Editar">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleOpenEdit(broker)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Eliminar">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleOpenDelete(broker)}
                          disabled={broker.estado === 'inactivo'}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog
        open={formDialogOpen}
        onClose={() => !formLoading && setFormDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedBroker ? `Editar Broker: ${selectedBroker.nombre}` : 'Nuevo Broker'}
        </DialogTitle>
        <DialogContent>
          <FKBrokerForm
            broker={selectedBroker}
            masterBrokerOptions={masterBrokerOptions}
            onSubmit={handleFormSubmit}
            onCancel={() => setFormDialogOpen(false)}
            loading={formLoading}
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !deleteLoading && setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirmar Eliminación</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Está seguro que desea eliminar el broker &quot;{selectedBroker?.nombre}&quot;?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Esta acción marcará el broker como inactivo.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            disabled={deleteLoading}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleDelete}
            color="error"
            variant="contained"
            disabled={deleteLoading}
            startIcon={deleteLoading ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {deleteLoading ? 'Eliminando...' : 'Eliminar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BrokersPage;
