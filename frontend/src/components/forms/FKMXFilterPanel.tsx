/**
 * FKMXFilterPanel - Panel de filtros para consultar el Excel de Drive MX
 *
 * Permite filtrar por:
 * - RFC del receptor (primero)
 * - Código(s) de operación asociados al RFC seleccionado
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
  getMXDistinctValues,
  getMXOperationsByRfc,
  precacheDriveFilesMX,
  type MXFilterRequest,
} from '../../services/financeServiceMX';

interface FKMXFilterPanelProps {
  onFilter: (filters: MXFilterRequest) => void;
  onClear: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const FKMXFilterPanel: React.FC<FKMXFilterPanelProps> = ({
  onFilter,
  onClear,
  isLoading = false,
  disabled = false,
}) => {
  // Filter state
  const [rfc, setRfc] = useState('');
  const [operaciones, setOperaciones] = useState<string[]>([]);
  const [operacionInput, setOperacionInput] = useState('');
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');

  // Autocomplete options
  const [rfcOptions, setRfcOptions] = useState<string[]>([]);
  const [operacionOptions, setOperacionOptions] = useState<string[]>([]);
  const [loadingRfcs, setLoadingRfcs] = useState(false);
  const [loadingOps, setLoadingOps] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Precache state
  const [isPrecaching, setIsPrecaching] = useState(false);
  const [precacheMessage, setPrecacheMessage] = useState<string | null>(null);

  // Track if an RFC has been selected
  const [rfcSelected, setRfcSelected] = useState(false);

  // Load RFCs on mount
  useEffect(() => {
    loadRfcOptions();
  }, []);

  // Load operations when RFC changes
  useEffect(() => {
    if (rfc.trim()) {
      loadOperationsForRfc(rfc.trim());
      setRfcSelected(true);
    } else {
      // Clear operations when RFC is cleared
      setOperacionOptions([]);
      setOperaciones([]);
      setRfcSelected(false);
    }
  }, [rfc]);

  const loadRfcOptions = async () => {
    setLoadingRfcs(true);
    try {
      const rfcResponse = await getMXDistinctValues('rfc', 200);
      if (rfcResponse.success) {
        setRfcOptions(rfcResponse.values);
      }
    } catch (err) {
      console.error('Error loading RFCs:', err);
    } finally {
      setLoadingRfcs(false);
    }
  };

  const loadOperationsForRfc = async (rfcValue: string) => {
    setLoadingOps(true);
    try {
      const opsResponse = await getMXOperationsByRfc(rfcValue, 200);
      if (opsResponse.success) {
        setOperacionOptions(opsResponse.values);
      } else {
        setOperacionOptions([]);
      }
    } catch (err) {
      console.error('Error loading operations for RFC:', err);
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
    const filters: MXFilterRequest = {};

    if (rfc.trim()) {
      filters.rfc = rfc.trim();
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

    // Validate at least one filter is set
    if (Object.keys(filters).length === 0) {
      setError('Debe especificar al menos un filtro');
      return;
    }

    // Debug: log filters being sent
    console.log('[FKMXFilterPanel] Enviando filtros:', JSON.stringify(filters, null, 2));

    setError(null);
    onFilter(filters);
  };

  // Handle clear filters
  const handleClear = () => {
    setRfc('');
    setOperaciones([]);
    setOperacionInput('');
    setFechaInicio('');
    setFechaFin('');
    setError(null);
    setRfcSelected(false);
    setOperacionOptions([]);
    onClear();
  };

  // Check if any filter is active
  const hasActiveFilters =
    rfc.trim() || operaciones.length > 0 || fechaInicio || fechaFin;

  // Handle precache
  const handlePrecache = async () => {
    setIsPrecaching(true);
    setPrecacheMessage(null);
    setError(null);

    try {
      const result = await precacheDriveFilesMX();
      if (result.success) {
        setPrecacheMessage(
          `Cache optimizado: ${result.stats.cached} archivos nuevos, ${result.stats.already_cached} ya en cache, ${result.stats.not_found} no encontrados`
        );
      } else {
        setError(result.message || 'Error al optimizar cache');
      }
    } catch (err) {
      console.error('Error precaching:', err);
      setError('Error al optimizar cache. Intente nuevamente.');
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
              Consultar Archivo Maestro
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            <Tooltip title="⚡ Optimizar cache: Ejecutar 1 vez antes de descargar ZIPs. Tarda ~5 min pero acelera todas las descargas futuras.">
              <IconButton
                size="small"
                onClick={handlePrecache}
                disabled={isPrecaching}
                color={isPrecaching ? 'primary' : 'default'}
              >
                {isPrecaching ? <CircularProgress size={20} /> : <SpeedIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="🔄 Recargar RFCs: Actualiza la lista de RFCs disponibles desde el archivo maestro.">
              <IconButton
                size="small"
                onClick={loadRfcOptions}
                disabled={loadingRfcs}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={1}>
          Consulta el archivo Facturación MX 2025.xlsx desde Google Drive
        </Typography>

        {/* Ayuda contextual para los iconos */}
        <Typography variant="caption" color="text.secondary" mb={2} component="div">
          💡 <strong>Tip:</strong> Usa el ícono de velocidad (⚡) una vez antes de descargar ZIPs grandes para acelerar la descarga.
        </Typography>

        <Stack spacing={3}>
          {/* RFC Filter - FIRST */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              RFC Receptor
            </Typography>
            <Autocomplete
              freeSolo
              options={rfcOptions}
              loading={loadingRfcs}
              value={rfc}
              onInputChange={(_, value) => setRfc(value)}
              disabled={disabled}
              renderInput={(params) => (
                <TextField
                  {...params}
                  size="small"
                  placeholder="Seleccione o ingrese el RFC del receptor"
                  helperText="Ingrese primero el RFC para ver las operaciones asociadas"
                  slotProps={{
                    input: {
                      ...params.InputProps,
                      endAdornment: (
                        <>
                          {loadingRfcs ? <CircularProgress size={16} /> : null}
                          {params.InputProps.endAdornment}
                        </>
                      ),
                    },
                  }}
                />
              )}
            />
          </Box>

          {/* Operaciones Filter - Shows operations for selected RFC */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Código(s) de Operación
              {rfcSelected && operacionOptions.length > 0 && (
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
                      rfcSelected
                        ? 'Seleccione una operación del RFC'
                        : 'Ingrese primero un RFC'
                    }
                    helperText={
                      !rfcSelected
                        ? 'Seleccione un RFC para ver las operaciones asociadas'
                        : operacionOptions.length === 0 && !loadingOps
                          ? 'No se encontraron operaciones para este RFC'
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

          {/* Messages Display */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          {precacheMessage && (
            <Alert severity="success" onClose={() => setPrecacheMessage(null)}>
              {precacheMessage}
            </Alert>
          )}
          {isPrecaching && (
            <Alert severity="info" icon={<CircularProgress size={20} />}>
              Optimizando cache... esto puede tardar 5-10 minutos. No cierre esta ventana.
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

export default FKMXFilterPanel;
