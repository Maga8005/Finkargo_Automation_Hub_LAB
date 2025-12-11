/**
 * FKCOFilterPanel - Panel de filtros para consultar el Excel de Drive CO
 *
 * Permite filtrar por:
 * - NIT del cliente (primero)
 * - Operación(es) asociadas al NIT seleccionado
 * - Rango de fecha
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  Autocomplete,
  CircularProgress,
  Alert,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import {
  getCODistinctValues,
  getCOOperationsByNit,
  precacheDriveFilesCO,
  type COFilterRequest,
  type PrecacheResponse,
} from '../../services/financeServiceCO';

interface FKCOFilterPanelProps {
  onFilter: (filters: COFilterRequest) => void;
  onClear: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const FKCOFilterPanel: React.FC<FKCOFilterPanelProps> = ({
  onFilter,
  onClear,
  isLoading = false,
  disabled = false,
}) => {
  // Filter state
  const [nit, setNit] = useState('');
  const [operaciones, setOperaciones] = useState<string[]>([]);
  const [operacionInput, setOperacionInput] = useState('');
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [hoja, setHoja] = useState<'' | 'costos_fijos' | 'mandato'>('');

  // Autocomplete options
  const [nitOptions, setNitOptions] = useState<string[]>([]);
  const [operacionOptions, setOperacionOptions] = useState<string[]>([]);
  const [loadingNits, setLoadingNits] = useState(false);
  const [loadingOps, setLoadingOps] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Track if a NIT has been selected
  const [nitSelected, setNitSelected] = useState(false);

  // Precache state
  const [isPrecaching, setIsPrecaching] = useState(false);
  const [precacheMessage, setPrecacheMessage] = useState<string | null>(null);

  // Load NITs on mount
  useEffect(() => {
    loadNitOptions();
  }, []);

  // Load operations when NIT changes
  useEffect(() => {
    if (nit.trim()) {
      loadOperationsForNit(nit.trim());
      setNitSelected(true);
    } else {
      // Clear operations when NIT is cleared
      setOperacionOptions([]);
      setOperaciones([]);
      setNitSelected(false);
    }
  }, [nit]);

  const loadNitOptions = async () => {
    setLoadingNits(true);
    try {
      const nitResponse = await getCODistinctValues('nit', 200);
      if (nitResponse.success) {
        setNitOptions(nitResponse.values);
      }
    } catch (err) {
      console.error('Error loading NITs:', err);
    } finally {
      setLoadingNits(false);
    }
  };

  const loadOperationsForNit = async (nitValue: string) => {
    setLoadingOps(true);
    try {
      const opsResponse = await getCOOperationsByNit(nitValue, 200);
      if (opsResponse.success) {
        setOperacionOptions(opsResponse.values);
      } else {
        setOperacionOptions([]);
      }
    } catch (err) {
      console.error('Error loading operations for NIT:', err);
      setOperacionOptions([]);
    } finally {
      setLoadingOps(false);
    }
  };

  // Handle add operacion chip
  const handleAddOperacion = () => {
    const trimmed = operacionInput.trim().toUpperCase();
    if (trimmed && !operaciones.includes(trimmed)) {
      setOperaciones([...operaciones, trimmed]);
      setOperacionInput('');
    }
  };

  // Handle remove operacion chip
  const handleRemoveOperacion = (op: string) => {
    setOperaciones(operaciones.filter((o) => o !== op));
  };

  // Handle filter submit
  const handleFilter = () => {
    // Build filter request
    const filters: COFilterRequest = {};

    if (nit.trim()) {
      filters.nit = nit.trim();
    }

    if (operaciones.length > 0) {
      filters.operaciones = operaciones;
    }

    if (fechaInicio) {
      filters.fecha_inicio = fechaInicio;
    }

    if (fechaFin) {
      filters.fecha_fin = fechaFin;
    }

    if (hoja) {
      filters.hoja = hoja;
    }

    // Validate at least one filter is set
    if (Object.keys(filters).length === 0) {
      setError('Debe especificar al menos un filtro');
      return;
    }

    setError(null);
    onFilter(filters);
  };

  // Handle clear filters
  const handleClear = () => {
    setNit('');
    setOperaciones([]);
    setOperacionInput('');
    setFechaInicio('');
    setFechaFin('');
    setHoja('');
    setError(null);
    setNitSelected(false);
    setOperacionOptions([]);
    onClear();
  };

  // Check if any filter is active
  const hasActiveFilters =
    nit.trim() || operaciones.length > 0 || fechaInicio || fechaFin || hoja;

  // Handle precache
  const handlePrecache = async () => {
    setIsPrecaching(true);
    setPrecacheMessage(null);
    setError(null);

    try {
      const result: PrecacheResponse = await precacheDriveFilesCO();
      if (result.success) {
        setPrecacheMessage(
          `Cache optimizado: ${result.stats.cached} archivos nuevos, ${result.stats.already_cached} ya en cache, ${result.stats.not_found} no encontrados`
        );
      } else {
        setError(result.message || 'Error al optimizar cache');
      }
    } catch (err) {
      console.error('Error during precache:', err);
      setError('Error al optimizar cache de archivos');
    } finally {
      setIsPrecaching(false);
    }
  };

  return (
    <Card elevation={2}>
      <CardContent>
        {/* Header */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <FilterIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Consultar Reporte de Facturación
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Tooltip title="⚡ Optimizar cache: Ejecutar 1 vez antes de descargar ZIPs grandes. Tarda ~5 min pero acelera todas las descargas futuras.">
              <IconButton
                size="small"
                onClick={handlePrecache}
                disabled={isPrecaching}
                color="secondary"
              >
                {isPrecaching ? <CircularProgress size={20} /> : <SpeedIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Recargar opciones de NITs">
              <IconButton
                size="small"
                onClick={loadNitOptions}
                disabled={loadingNits}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={3}>
          Consulta el archivo Reporte_Facturacion_CO.xlsx desde Google Drive
        </Typography>

        <Stack spacing={3}>
          {/* NIT Filter - FIRST */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              NIT del Cliente
            </Typography>
            <Autocomplete
              freeSolo
              options={nitOptions}
              loading={loadingNits}
              value={nit}
              onInputChange={(_, value) => setNit(value)}
              disabled={disabled}
              renderInput={(params) => (
                <TextField
                  {...params}
                  size="small"
                  placeholder="Seleccione o ingrese el NIT del cliente"
                  helperText="Ingrese primero el NIT para ver las operaciones asociadas"
                  slotProps={{
                    input: {
                      ...params.InputProps,
                      endAdornment: (
                        <>
                          {loadingNits ? <CircularProgress size={16} /> : null}
                          {params.InputProps.endAdornment}
                        </>
                      ),
                    },
                  }}
                />
              )}
            />
          </Box>

          {/* Operaciones Filter - Shows operations for selected NIT */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Código(s) de Operación
              {nitSelected && operacionOptions.length > 0 && (
                <Chip
                  label={`${operacionOptions.length} operaciones disponibles`}
                  size="small"
                  color="info"
                  variant="outlined"
                  sx={{ ml: 1 }}
                />
              )}
            </Typography>
            <Box display="flex" gap={1} alignItems="flex-start">
              <Autocomplete
                freeSolo
                options={operacionOptions}
                loading={loadingOps}
                inputValue={operacionInput}
                onInputChange={(_, value) => setOperacionInput(value)}
                onChange={(_, value) => {
                  if (value && typeof value === 'string') {
                    const trimmed = value.trim().toUpperCase();
                    if (trimmed && !operaciones.includes(trimmed)) {
                      setOperaciones([...operaciones, trimmed]);
                      setOperacionInput('');
                    }
                  }
                }}
                disabled={disabled}
                sx={{ flex: 1 }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    size="small"
                    placeholder={
                      nitSelected
                        ? 'Seleccione una operación del NIT'
                        : 'Ingrese primero un NIT'
                    }
                    helperText={
                      !nitSelected
                        ? 'Seleccione un NIT para ver las operaciones asociadas'
                        : operacionOptions.length === 0 && !loadingOps
                          ? 'No se encontraron operaciones para este NIT'
                          : ''
                    }
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddOperacion();
                      }
                    }}
                    slotProps={{
                      input: {
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {loadingOps ? <CircularProgress size={16} /> : null}
                            {params.InputProps.endAdornment}
                          </>
                        ),
                      },
                    }}
                  />
                )}
              />
              <Button
                variant="outlined"
                size="small"
                onClick={handleAddOperacion}
                disabled={!operacionInput.trim() || disabled}
                sx={{ minWidth: 80 }}
              >
                Agregar
              </Button>
            </Box>
            {operaciones.length > 0 && (
              <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                {operaciones.map((op) => (
                  <Chip
                    key={op}
                    label={op}
                    size="small"
                    onDelete={() => handleRemoveOperacion(op)}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            )}
          </Box>

          {/* Date Range Filter */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Rango de Fechas
            </Typography>
            <Box display="flex" gap={2}>
              <TextField
                type="date"
                label="Fecha Inicio"
                size="small"
                fullWidth
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
                disabled={disabled}
                slotProps={{
                  inputLabel: { shrink: true },
                }}
              />
              <TextField
                type="date"
                label="Fecha Fin"
                size="small"
                fullWidth
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
                disabled={disabled}
                slotProps={{
                  inputLabel: { shrink: true },
                  htmlInput: { min: fechaInicio || undefined },
                }}
              />
            </Box>
          </Box>

          {/* Sheet Filter */}
          <FormControl size="small" fullWidth>
            <InputLabel>Hoja (opcional)</InputLabel>
            <Select
              value={hoja}
              label="Hoja (opcional)"
              onChange={(e) => setHoja(e.target.value as typeof hoja)}
              disabled={disabled}
              displayEmpty
            >
              <MenuItem value="costos_fijos">Costos Fijos</MenuItem>
              <MenuItem value="mandato">Mandato</MenuItem>
            </Select>
          </FormControl>

          {/* Precache Success Message */}
          {precacheMessage && (
            <Alert severity="success" onClose={() => setPrecacheMessage(null)}>
              {precacheMessage}
            </Alert>
          )}

          {/* Error Display */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Divider />

          {/* Action Buttons */}
          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              startIcon={isLoading ? <CircularProgress size={20} /> : <SearchIcon />}
              onClick={handleFilter}
              disabled={isLoading || disabled}
              fullWidth
            >
              {isLoading ? 'Consultando...' : 'Consultar'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={handleClear}
              disabled={isLoading || disabled || !hasActiveFilters}
            >
              Limpiar
            </Button>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default FKCOFilterPanel;
