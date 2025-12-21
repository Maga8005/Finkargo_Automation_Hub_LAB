/**
 * FKBlacklistManager - Blacklist management component
 */
import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Add,
  Delete,
  Block,
} from '@mui/icons-material';
import type { BlacklistEntry, BlacklistEntryRequest, EntityType } from '../../types/risk';
import { ENTITY_TYPE_LABELS } from '../../types/risk';

interface FKBlacklistManagerProps {
  entries: BlacklistEntry[];
  onAdd: (entry: BlacklistEntryRequest) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
  canManage: boolean;
  loading?: boolean;
  error?: string | null;
}

interface FormData {
  entity_type: EntityType;
  entity_value: string;
  reason: string;
}

const FKBlacklistManager: React.FC<FKBlacklistManagerProps> = ({
  entries,
  onAdd,
  onRemove,
  canManage,
  loading = false,
  error = null,
}) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormData>({
    defaultValues: {
      entity_type: 'nit',
      entity_value: '',
      reason: '',
    },
  });

  const handleOpenDialog = () => {
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    reset();
  };

  const onSubmit = async (data: FormData) => {
    await onAdd({
      entity_type: data.entity_type,
      entity_value: data.entity_value.trim(),
      reason: data.reason.trim(),
    });
    handleCloseDialog();
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    await onRemove(id);
    setDeletingId(null);
  };

  // Format date for display
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Add Button */}
      {canManage && (
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleOpenDialog}
            disabled={loading}
          >
            Agregar a Blacklist
          </Button>
        </Box>
      )}

      {/* Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Tipo</TableCell>
              <TableCell>Valor</TableCell>
              <TableCell>Razón</TableCell>
              <TableCell>Fecha</TableCell>
              <TableCell>Estado</TableCell>
              {canManage && <TableCell align="right">Acciones</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.length === 0 ? (
              <TableRow>
                <TableCell colSpan={canManage ? 6 : 5} align="center" sx={{ py: 4 }}>
                  <Block sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
                  <Typography color="text.secondary">
                    No hay entradas en la lista negra
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              entries.map((entry) => (
                <TableRow
                  key={entry.id}
                  sx={{
                    backgroundColor: entry.is_active ? 'inherit' : 'action.disabledBackground',
                    opacity: entry.is_active ? 1 : 0.6,
                  }}
                >
                  <TableCell>
                    <Chip
                      label={ENTITY_TYPE_LABELS[entry.entity_type]}
                      size="small"
                      color="default"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {entry.entity_value}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Tooltip title={entry.reason}>
                      <Typography
                        variant="body2"
                        sx={{
                          maxWidth: 200,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {entry.reason}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(entry.added_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={entry.is_active ? 'Activo' : 'Inactivo'}
                      size="small"
                      color={entry.is_active ? 'error' : 'default'}
                    />
                  </TableCell>
                  {canManage && (
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(entry.id)}
                        disabled={loading || deletingId === entry.id || !entry.is_active}
                      >
                        {deletingId === entry.id ? (
                          <CircularProgress size={20} />
                        ) : (
                          <Delete />
                        )}
                      </IconButton>
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Agregar a Lista Negra</DialogTitle>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <Controller
                name="entity_type"
                control={control}
                rules={{ required: 'Tipo es requerido' }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.entity_type}>
                    <InputLabel>Tipo de Entidad</InputLabel>
                    <Select {...field} label="Tipo de Entidad">
                      {(Object.keys(ENTITY_TYPE_LABELS) as EntityType[]).map((type) => (
                        <MenuItem key={type} value={type}>
                          {ENTITY_TYPE_LABELS[type]}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />

              <Controller
                name="entity_value"
                control={control}
                rules={{
                  required: 'Valor es requerido',
                  minLength: { value: 1, message: 'Valor es requerido' },
                  maxLength: { value: 500, message: 'Máximo 500 caracteres' },
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Valor"
                    placeholder="Ej: 900.123.456-7 o dominio.com"
                    fullWidth
                    error={!!errors.entity_value}
                    helperText={errors.entity_value?.message}
                  />
                )}
              />

              <Controller
                name="reason"
                control={control}
                rules={{
                  required: 'Razón es requerida',
                  minLength: { value: 5, message: 'Mínimo 5 caracteres' },
                  maxLength: { value: 1000, message: 'Máximo 1000 caracteres' },
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Razón"
                    placeholder="Describa la razón para agregar a la lista negra"
                    fullWidth
                    multiline
                    rows={3}
                    error={!!errors.reason}
                    helperText={errors.reason?.message}
                  />
                )}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog} disabled={loading}>
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="contained"
              color="error"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <Block />}
            >
              Agregar
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};

export default FKBlacklistManager;
