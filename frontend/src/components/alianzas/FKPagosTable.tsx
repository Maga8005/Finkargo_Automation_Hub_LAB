/**
 * FKPagosTable - Data grid component for displaying broker payment history
 */
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  DataGrid,
  type GridColDef,
  type GridRenderCellParams,
} from '@mui/x-data-grid';
import {
  Visibility as VisibilityIcon,
  Payment as PaymentIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material';
import type {
  Pago,
  EstadoPago,
} from '../../types/alianzas';
import {
  ESTADO_PAGO_LABELS,
  ESTADO_PAGO_COLORS,
} from '../../types/alianzas';

// Spanish month names
const MESES_CORTOS = [
  'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
];

interface FKPagosTableProps {
  pagos: Pago[];
  loading: boolean;
  error?: string | null;
  onViewDetails?: (pago: Pago) => void;
  onMarkAsPaid?: (pago: Pago) => void;
  onViewReceipt?: (pago: Pago) => void;
  totalRecords?: number;
  pageSize?: number;
  page?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

/**
 * Format currency value for display
 */
const formatCurrency = (value: number, currency: 'USD' | 'MXN'): string => {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

/**
 * Format period for display (e.g., "Dic 2025")
 */
const formatPeriodo = (mes: number, anio: number): string => {
  return `${MESES_CORTOS[mes - 1]} ${anio}`;
};

/**
 * Format date for display
 */
const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
};

const FKPagosTable: React.FC<FKPagosTableProps> = ({
  pagos,
  loading,
  error,
  onViewDetails,
  onMarkAsPaid,
  onViewReceipt,
  totalRecords,
  pageSize = 25,
  page = 0,
  onPageChange,
  onPageSizeChange,
}) => {
  const [paginationModel, setPaginationModel] = useState({
    page,
    pageSize,
  });

  const columns: GridColDef[] = [
    {
      field: 'periodo',
      headerName: 'Período',
      width: 100,
      valueGetter: (_value, row) => formatPeriodo(row.periodo_mes, row.periodo_anio),
    },
    {
      field: 'broker_nombre',
      headerName: 'Broker',
      flex: 1,
      minWidth: 180,
      valueGetter: (_value, row) => row.broker_nombre || 'Sin nombre',
    },
    {
      field: 'total_usd',
      headerName: 'Total USD',
      width: 130,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value: number) => formatCurrency(value, 'USD'),
    },
    {
      field: 'total_mxn',
      headerName: 'Total MXN',
      width: 140,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value: number) => formatCurrency(value, 'MXN'),
    },
    {
      field: 'tipo_cambio',
      headerName: 'T/C',
      width: 90,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value: number) => value?.toFixed(4) || '-',
    },
    {
      field: 'estado',
      headerName: 'Estado',
      width: 120,
      renderCell: (params: GridRenderCellParams<Pago>) => {
        const estado = params.value as EstadoPago;
        return (
          <Chip
            label={ESTADO_PAGO_LABELS[estado] || estado}
            color={ESTADO_PAGO_COLORS[estado] || 'default'}
            size="small"
            sx={{ fontWeight: 500 }}
          />
        );
      },
    },
    {
      field: 'fecha_pago',
      headerName: 'Fecha Pago',
      width: 120,
      valueFormatter: (value: string | null) => formatDate(value),
    },
    {
      field: 'created_at',
      headerName: 'Creado',
      width: 110,
      valueFormatter: (value: string) => formatDate(value),
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 130,
      sortable: false,
      filterable: false,
      renderCell: (params: GridRenderCellParams<Pago>) => {
        const pago = params.row;
        return (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {onViewDetails && (
              <Tooltip title="Ver detalles">
                <IconButton
                  size="small"
                  onClick={() => onViewDetails(pago)}
                  sx={{ color: 'primary.main' }}
                >
                  <VisibilityIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {onMarkAsPaid && pago.estado !== 'pagado' && (
              <Tooltip title="Marcar como pagado">
                <IconButton
                  size="small"
                  onClick={() => onMarkAsPaid(pago)}
                  sx={{ color: 'success.main' }}
                >
                  <PaymentIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {onViewReceipt && pago.comprobante_url && (
              <Tooltip title="Ver comprobante">
                <IconButton
                  size="small"
                  onClick={() => onViewReceipt(pago)}
                  sx={{ color: 'info.main' }}
                >
                  <ReceiptIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        );
      },
    },
  ];

  const handlePaginationModelChange = (model: { page: number; pageSize: number }) => {
    setPaginationModel(model);
    if (onPageChange && model.page !== page) {
      onPageChange(model.page);
    }
    if (onPageSizeChange && model.pageSize !== pageSize) {
      onPageSizeChange(model.pageSize);
    }
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <DataGrid
        rows={pagos}
        columns={columns}
        loading={loading}
        paginationModel={paginationModel}
        onPaginationModelChange={handlePaginationModelChange}
        pageSizeOptions={[10, 25, 50, 100]}
        rowCount={totalRecords ?? pagos.length}
        paginationMode={totalRecords !== undefined ? 'server' : 'client'}
        disableRowSelectionOnClick
        autoHeight
        sx={{
          border: 'none',
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: 'grey.100',
            fontWeight: 600,
          },
          '& .MuiDataGrid-cell': {
            borderColor: 'grey.200',
          },
          '& .MuiDataGrid-row:hover': {
            backgroundColor: 'grey.50',
          },
        }}
        localeText={{
          noRowsLabel: 'No hay pagos registrados',
          MuiTablePagination: {
            labelRowsPerPage: 'Filas por página:',
            labelDisplayedRows: ({ from, to, count }) =>
              `${from}-${to} de ${count !== -1 ? count : `más de ${to}`}`,
          },
        }}
        slots={{
          loadingOverlay: () => (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
              }}
            >
              <CircularProgress />
            </Box>
          ),
        }}
      />
    </Paper>
  );
};

export default FKPagosTable;
