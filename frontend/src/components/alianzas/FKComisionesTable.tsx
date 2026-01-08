/**
 * FKComisionesTable - DataGrid for displaying commission rows
 * Features: edit, delete, sort, and group by broker
 */
import React, { useMemo } from 'react';
import {
  DataGrid,
  GridActionsCellItem,
} from '@mui/x-data-grid';
import type { GridColDef, GridRowParams } from '@mui/x-data-grid';
import {
  Box,
  Chip,
  Typography,
  Tooltip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';

import type { ComisionCalculada, TipoComision, EstadoComision } from '../../types/alianzas';
import {
  TIPO_COMISION_LABELS,
  ESTADO_COMISION_LABELS,
  ESTADO_COMISION_COLORS,
} from '../../types/alianzas';

interface FKComisionesTableProps {
  comisiones: ComisionCalculada[];
  onEdit?: (comision: ComisionCalculada) => void;
  onDelete?: (comision: ComisionCalculada) => void;
  loading?: boolean;
  showActions?: boolean;
}

const FKComisionesTable: React.FC<FKComisionesTableProps> = ({
  comisiones,
  onEdit,
  onDelete,
  loading = false,
  showActions = true,
}) => {
  // Format currency for display
  const formatCurrency = (value: number | null | undefined, currency: 'USD' | 'MXN'): string => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Format percentage for display
  const formatPercentage = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '-';
    return `${value}%`;
  };

  // Get base amount depending on commission type
  const getBaseAmount = (row: ComisionCalculada): string => {
    if (row.tipo_comision === 'apertura') {
      return formatCurrency(row.linea_credito, 'USD');
    }
    return formatCurrency(row.operaciones_mes, 'USD');
  };

  // Get percentage depending on commission type
  const getPercentage = (row: ComisionCalculada): string => {
    if (row.tipo_comision === 'apertura') {
      return formatPercentage(row.porcentaje_comision_cliente);
    }
    return formatPercentage(row.porcentaje_broker);
  };

  const columns: GridColDef[] = useMemo(() => {
    const baseColumns: GridColDef[] = [
      {
        field: 'cliente_nombre',
        headerName: 'Cliente',
        flex: 1,
        minWidth: 150,
        renderCell: (params) => (
          <Box>
            <Typography variant="body2" fontWeight={500}>
              {params.value || 'Sin nombre'}
            </Typography>
            {params.row.cliente_nit && (
              <Typography variant="caption" color="text.secondary">
                {params.row.cliente_nit}
              </Typography>
            )}
          </Box>
        ),
      },
      {
        field: 'broker_nombre',
        headerName: 'Broker',
        width: 150,
        renderCell: (params) => params.value || params.row.broker_id?.substring(0, 8),
      },
      {
        field: 'tipo_comision',
        headerName: 'Tipo',
        width: 100,
        renderCell: (params) => (
          <Chip
            label={TIPO_COMISION_LABELS[params.value as TipoComision]}
            size="small"
            color={params.value === 'apertura' ? 'primary' : 'secondary'}
            variant="outlined"
          />
        ),
      },
      {
        field: 'base_amount',
        headerName: 'Base',
        width: 130,
        valueGetter: (_value, row) => {
          if (row.tipo_comision === 'apertura') {
            return row.linea_credito;
          }
          return row.operaciones_mes;
        },
        renderCell: (params) => (
          <Typography variant="body2">
            {getBaseAmount(params.row)}
          </Typography>
        ),
      },
      {
        field: 'percentage',
        headerName: '%',
        width: 80,
        valueGetter: (_value, row) => {
          if (row.tipo_comision === 'apertura') {
            return row.porcentaje_comision_cliente;
          }
          return row.porcentaje_broker;
        },
        renderCell: (params) => (
          <Typography variant="body2">
            {getPercentage(params.row)}
          </Typography>
        ),
      },
      {
        field: 'monto_broker_usd',
        headerName: 'USD',
        width: 120,
        renderCell: (params) => (
          <Typography variant="body2" fontWeight={500}>
            {formatCurrency(params.value, 'USD')}
          </Typography>
        ),
      },
      {
        field: 'monto_broker_mxn',
        headerName: 'MXN',
        width: 130,
        renderCell: (params) => (
          <Typography variant="body2" fontWeight={500}>
            {formatCurrency(params.value, 'MXN')}
          </Typography>
        ),
      },
      {
        field: 'estado',
        headerName: 'Estado',
        width: 100,
        renderCell: (params) => (
          <Chip
            label={ESTADO_COMISION_LABELS[params.value as EstadoComision]}
            size="small"
            color={ESTADO_COMISION_COLORS[params.value as EstadoComision]}
          />
        ),
      },
    ];

    // Add actions column if needed
    if (showActions) {
      baseColumns.push({
        field: 'actions',
        type: 'actions',
        headerName: '',
        width: 80,
        getActions: (params: GridRowParams<ComisionCalculada>) => {
          const actions = [];

          if (onEdit) {
            actions.push(
              <GridActionsCellItem
                key="edit"
                icon={
                  <Tooltip title="Editar">
                    <EditIcon />
                  </Tooltip>
                }
                label="Editar"
                onClick={() => onEdit(params.row)}
              />
            );
          }

          if (onDelete) {
            actions.push(
              <GridActionsCellItem
                key="delete"
                icon={
                  <Tooltip title="Eliminar">
                    <DeleteIcon color="error" />
                  </Tooltip>
                }
                label="Eliminar"
                onClick={() => onDelete(params.row)}
              />
            );
          }

          return actions;
        },
      });
    }

    return baseColumns;
  }, [showActions, onEdit, onDelete]);

  // Generate row IDs - use saved ID or create a temporary one
  const rows = useMemo(() => {
    return comisiones.map((comision, index) => ({
      ...comision,
      id: comision.id || `temp-${index}-${comision.broker_id}-${comision.cliente_nombre}`,
    }));
  }, [comisiones]);

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      loading={loading}
      autoHeight
      disableRowSelectionOnClick
      pageSizeOptions={[10, 25, 50]}
      initialState={{
        pagination: { paginationModel: { pageSize: 10 } },
        sorting: {
          sortModel: [{ field: 'broker_nombre', sort: 'asc' }],
        },
      }}
      sx={{
        border: 'none',
        '& .MuiDataGrid-cell': {
          borderBottom: '1px solid',
          borderBottomColor: 'divider',
        },
        '& .MuiDataGrid-columnHeaders': {
          backgroundColor: 'grey.50',
          borderBottom: '2px solid',
          borderBottomColor: 'divider',
        },
        '& .MuiDataGrid-row:hover': {
          backgroundColor: 'action.hover',
        },
      }}
      localeText={{
        noRowsLabel: 'No hay comisiones',
        footerRowSelected: (count) =>
          count !== 1
            ? `${count.toLocaleString()} filas seleccionadas`
            : `${count.toLocaleString()} fila seleccionada`,
        MuiTablePagination: {
          labelRowsPerPage: 'Filas por página:',
          labelDisplayedRows: ({ from, to, count }) =>
            `${from}-${to} de ${count !== -1 ? count : `más de ${to}`}`,
        },
      }}
    />
  );
};

export default FKComisionesTable;
