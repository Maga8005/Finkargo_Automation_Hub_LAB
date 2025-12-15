/**
 * FKMatchResultsTable - Match results DataGrid component.
 *
 * Displays matching results with status chips, confidence scores,
 * and action buttons for manual override.
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import {
  Edit as EditIcon,
  Clear as ClearIcon,
  Search as SearchIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import type {
  MatchResult,
  MatchStatus,
} from '../../types/treasuryMatching';

interface FKMatchResultsTableProps {
  results: MatchResult[];
  onOverride: (groupId: string) => void;
  onClearMatch: (groupId: string) => void;
  loading?: boolean;
}

const statusColors: Record<MatchStatus, 'success' | 'warning' | 'error' | 'info'> = {
  matched: 'success',
  partial: 'warning',
  unmatched: 'error',
  conflict: 'info',
};

const statusLabels: Record<MatchStatus, string> = {
  matched: 'Coincidencia',
  partial: 'Parcial',
  unmatched: 'Sin coincidencia',
  conflict: 'Conflicto',
};

const statusIcons: Record<MatchStatus, React.ReactNode> = {
  matched: <CheckCircleIcon fontSize="small" />,
  partial: <WarningIcon fontSize="small" />,
  unmatched: <ErrorIcon fontSize="small" />,
  conflict: <HelpIcon fontSize="small" />,
};

const FKMatchResultsTable: React.FC<FKMatchResultsTableProps> = ({
  results,
  onOverride,
  onClearMatch,
  loading = false,
}) => {
  const [statusFilter, setStatusFilter] = useState<MatchStatus | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Filter results
  const filteredResults = useMemo(() => {
    let filtered = results;

    if (statusFilter !== 'all') {
      filtered = filtered.filter((r) => r.match_status === statusFilter);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          r.payment_group.cliente.toLowerCase().includes(term) ||
          r.payment_group.identificacion_cliente.toLowerCase().includes(term) ||
          (r.declaration?.declaration_number || '').toLowerCase().includes(term)
      );
    }

    return filtered;
  }, [results, statusFilter, searchTerm]);

  const columns: GridColDef[] = [
    {
      field: 'match_status',
      headerName: 'Estado',
      width: 140,
      renderCell: (params: GridRenderCellParams<MatchResult>) => {
        const status = params.row.match_status as MatchStatus;
        return (
          <Chip
            icon={statusIcons[status] as React.ReactElement}
            label={statusLabels[status]}
            color={statusColors[status]}
            size="small"
            variant="outlined"
          />
        );
      },
    },
    {
      field: 'cliente',
      headerName: 'Cliente',
      flex: 1,
      minWidth: 200,
      valueGetter: (_value, row) => row.payment_group.cliente,
    },
    {
      field: 'identificacion',
      headerName: 'NIT',
      width: 130,
      valueGetter: (_value, row) => row.payment_group.identificacion_cliente,
    },
    {
      field: 'fecha_pago',
      headerName: 'Fecha Pago',
      width: 120,
      valueGetter: (_value, row) => row.payment_group.fecha_pago,
    },
    {
      field: 'total_capital',
      headerName: 'Capital',
      width: 120,
      valueGetter: (_value, row) => row.payment_group.total_capital,
      valueFormatter: (value: number) => {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(value);
      },
    },
    {
      field: 'record_info',
      headerName: 'Filas',
      width: 100,
      renderCell: (params: GridRenderCellParams<MatchResult>) => {
        const { record_count, record_row_numbers } = params.row.payment_group;
        if (record_count === 1) {
          return (
            <Typography variant="caption" color="text.secondary">
              Fila {record_row_numbers[0]}
            </Typography>
          );
        }
        return (
          <Tooltip title={`Filas: ${record_row_numbers.join(', ')}`}>
            <Typography variant="caption" color="text.secondary">
              {record_count} filas
            </Typography>
          </Tooltip>
        );
      },
    },
    {
      field: 'declaration_number',
      headerName: 'No. Declaracion',
      width: 140,
      valueGetter: (_value, row) => row.declaration?.declaration_number || '-',
    },
    {
      field: 'match_confidence',
      headerName: 'Confianza',
      width: 130,
      renderCell: (params: GridRenderCellParams<MatchResult>) => {
        const confidence = params.row.match_confidence * 100;
        const color =
          confidence >= 95 ? 'success' : confidence >= 70 ? 'info' : confidence >= 50 ? 'warning' : 'error';

        return (
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 1 }}>
            <LinearProgress
              variant="determinate"
              value={confidence}
              color={color as 'success' | 'info' | 'warning' | 'error'}
              sx={{ flex: 1, height: 8, borderRadius: 1 }}
            />
            <Typography variant="caption" sx={{ minWidth: 40 }}>
              {confidence.toFixed(0)}%
            </Typography>
          </Box>
        );
      },
    },
    {
      field: 'differences',
      headerName: 'Diferencias',
      width: 150,
      renderCell: (params: GridRenderCellParams<MatchResult>) => {
        const { date_difference_days, amount_difference } = params.row;
        if (date_difference_days === null && amount_difference === null) {
          return '-';
        }
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', fontSize: '0.75rem' }}>
            {date_difference_days !== null && (
              <Typography variant="caption">
                Fecha: {date_difference_days}d
              </Typography>
            )}
            {amount_difference !== null && (
              <Typography variant="caption">
                Monto: ${amount_difference?.toFixed(2)}
              </Typography>
            )}
          </Box>
        );
      },
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 100,
      sortable: false,
      renderCell: (params: GridRenderCellParams<MatchResult>) => (
        <Box>
          <Tooltip title="Asignar manualmente">
            <IconButton
              size="small"
              onClick={() => onOverride(params.row.group_id)}
              color="primary"
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {params.row.declaration && (
            <Tooltip title="Quitar coincidencia">
              <IconButton
                size="small"
                onClick={() => onClearMatch(params.row.group_id)}
                color="error"
              >
                <ClearIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ];

  // Status counts for filter badges
  const statusCounts = useMemo(() => {
    const counts: Record<MatchStatus | 'all', number> = {
      all: results.length,
      matched: 0,
      partial: 0,
      unmatched: 0,
      conflict: 0,
    };
    results.forEach((r) => {
      counts[r.match_status]++;
    });
    return counts;
  }, [results]);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Resultados de Coincidencias
        </Typography>

        {/* Filters */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <TextField
            size="small"
            placeholder="Buscar cliente, NIT o declaracion..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 280 }}
          />

          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Estado</InputLabel>
            <Select
              value={statusFilter}
              label="Estado"
              onChange={(e) => setStatusFilter(e.target.value as MatchStatus | 'all')}
            >
              <MenuItem value="all">
                Todos ({statusCounts.all})
              </MenuItem>
              <MenuItem value="matched">
                <Chip
                  icon={<CheckCircleIcon fontSize="small" />}
                  label={`Coincidencia (${statusCounts.matched})`}
                  color="success"
                  size="small"
                  variant="outlined"
                />
              </MenuItem>
              <MenuItem value="partial">
                <Chip
                  icon={<WarningIcon fontSize="small" />}
                  label={`Parcial (${statusCounts.partial})`}
                  color="warning"
                  size="small"
                  variant="outlined"
                />
              </MenuItem>
              <MenuItem value="unmatched">
                <Chip
                  icon={<ErrorIcon fontSize="small" />}
                  label={`Sin coincidencia (${statusCounts.unmatched})`}
                  color="error"
                  size="small"
                  variant="outlined"
                />
              </MenuItem>
              <MenuItem value="conflict">
                <Chip
                  icon={<HelpIcon fontSize="small" />}
                  label={`Conflicto (${statusCounts.conflict})`}
                  color="info"
                  size="small"
                  variant="outlined"
                />
              </MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* DataGrid */}
        <Box sx={{ height: 500 }}>
          <DataGrid
            rows={filteredResults}
            columns={columns}
            getRowId={(row) => row.group_id}
            loading={loading}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 10 },
              },
              sorting: {
                sortModel: [{ field: 'match_confidence', sort: 'desc' }],
              },
            }}
            disableRowSelectionOnClick
            sx={{
              '& .MuiDataGrid-cell': {
                borderBottom: '1px solid',
                borderColor: 'divider',
              },
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default FKMatchResultsTable;
