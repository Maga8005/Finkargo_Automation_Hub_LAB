/**
 * FKBrokerIncentiveResultsGrid - Results data grid for broker incentive extraction
 *
 * Displays extracted broker incentive data in a sortable, filterable DataGrid.
 * Features:
 * - Sortable and filterable columns
 * - Conditional styling for missing data
 * - Contract type color coding
 * - Export button integration
 */
import React from 'react';
import { Paper, Box, Typography, Button, Chip, Stack } from '@mui/material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import DownloadIcon from '@mui/icons-material/Download';
import AssessmentIcon from '@mui/icons-material/Assessment';
import type {
  BrokerIncentiveData,
  ContractType,
  ContractStatus,
} from '../../services/brokerIncentiveService';
import {
  formatPercentage,
  formatContractType,
  getContractTypeColor,
  formatContractStatus,
  getContractStatusColor,
  exportBrokerIncentives,
} from '../../services/brokerIncentiveService';

interface FKBrokerIncentiveResultsGridProps {
  records: BrokerIncentiveData[];
  loading?: boolean;
  onExport?: () => Promise<void>;
}

/**
 * Get row ID from record
 */
const getRowId = (row: BrokerIncentiveData) => row.pdf_path;

/**
 * Render contract type chip with color
 */
const renderContractTypeCell = (params: GridRenderCellParams<BrokerIncentiveData, ContractType>) => {
  const type = params.value;
  if (!type) return null;

  return (
    <Chip
      label={formatContractType(type)}
      color={getContractTypeColor(type)}
      size="small"
      variant="filled"
      sx={{ fontWeight: 600 }}
    />
  );
};

/**
 * Render contract status chip with color
 */
const renderContractStatusCell = (params: GridRenderCellParams<BrokerIncentiveData, ContractStatus>) => {
  const status = params.value;
  if (!status) return null;

  return (
    <Chip
      label={formatContractStatus(status)}
      color={getContractStatusColor(status)}
      size="small"
      variant="filled"
      sx={{ fontWeight: 600 }}
    />
  );
};

/**
 * Render percentage cell with N/A styling
 */
const renderPercentageCell = (params: GridRenderCellParams<BrokerIncentiveData, number | null>) => {
  const value = params.value;

  if (value === null || value === undefined) {
    return (
      <Typography variant="body2" color="text.disabled" fontStyle="italic">
        N/A
      </Typography>
    );
  }

  return (
    <Typography variant="body2" fontWeight={500}>
      {formatPercentage(value)}
    </Typography>
  );
};

/**
 * Render text cell with N/A styling for null values
 */
const renderTextCell = (params: GridRenderCellParams<BrokerIncentiveData, string | null>) => {
  const value = params.value;

  if (!value) {
    return (
      <Typography variant="body2" color="text.disabled" fontStyle="italic">
        N/A
      </Typography>
    );
  }

  return (
    <Typography variant="body2" noWrap title={value}>
      {value}
    </Typography>
  );
};

/**
 * Render warnings cell
 */
const renderWarningsCell = (params: GridRenderCellParams<BrokerIncentiveData, string[]>) => {
  const warnings = params.value;

  if (!warnings || warnings.length === 0) {
    return null;
  }

  const warningsText = warnings.join('; ');

  return (
    <Typography
      variant="caption"
      color="warning.main"
      title={warningsText}
      sx={{
        display: 'block',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}
    >
      {warningsText}
    </Typography>
  );
};

/**
 * Column definitions for the DataGrid
 */
const columns: GridColDef<BrokerIncentiveData>[] = [
  {
    field: 'broker_name',
    headerName: 'Nombre Broker',
    flex: 1,
    minWidth: 180,
    renderCell: (params) => (
      <Typography variant="body2" fontWeight={500}>
        {params.value}
      </Typography>
    ),
  },
  {
    field: 'rfc',
    headerName: 'RFC',
    width: 140,
    renderCell: renderTextCell,
  },
  {
    field: 'signatory_name',
    headerName: 'Firmante',
    width: 160,
    renderCell: renderTextCell,
  },
  {
    field: 'credit_line_incentive_pct',
    headerName: 'Linea Credito (%)',
    width: 140,
    align: 'right',
    headerAlign: 'right',
    renderCell: renderPercentageCell,
  },
  {
    field: 'operations_incentive_pct',
    headerName: 'Operaciones (%)',
    width: 140,
    align: 'right',
    headerAlign: 'right',
    renderCell: renderPercentageCell,
  },
  {
    field: 'contract_type',
    headerName: 'Tipo Contrato',
    width: 130,
    align: 'center',
    headerAlign: 'center',
    renderCell: renderContractTypeCell,
  },
  {
    field: 'contract_status',
    headerName: 'Estado Contrato',
    width: 140,
    align: 'center',
    headerAlign: 'center',
    renderCell: renderContractStatusCell,
  },
  {
    field: 'contract_date',
    headerName: 'Fecha Contrato',
    width: 120,
    renderCell: renderTextCell,
  },
  {
    field: 'warnings',
    headerName: 'Notas',
    flex: 1,
    minWidth: 200,
    renderCell: renderWarningsCell,
  },
];

const FKBrokerIncentiveResultsGrid: React.FC<FKBrokerIncentiveResultsGridProps> = ({
  records,
  loading = false,
  onExport,
}) => {
  console.log('[FKBrokerIncentiveResultsGrid] Rendering', {
    recordCount: records.length,
    loading,
  });

  /**
   * Handle export button click
   */
  const handleExport = async () => {
    try {
      if (onExport) {
        await onExport();
      } else {
        await exportBrokerIncentives();
      }
    } catch (error) {
      console.error('[FKBrokerIncentiveResultsGrid] Export failed:', error);
    }
  };

  /**
   * Calculate summary statistics
   */
  const bonoCount = records.filter((r) => r.contract_type === 'bono').length;
  const incentivosCount = records.filter((r) => r.contract_type === 'incentivos').length;
  const unknownCount = records.filter((r) => r.contract_type === 'unknown').length;

  // Contract status counts
  const foundCount = records.filter((r) => r.contract_status === 'found').length;
  const notFoundCount = records.filter((r) => r.contract_status === 'not_found').length;
  const errorCount = records.filter((r) => r.contract_status === 'error').length;

  const creditLineValues = records
    .filter((r) => r.credit_line_incentive_pct !== null)
    .map((r) => r.credit_line_incentive_pct as number);
  const avgCreditLine =
    creditLineValues.length > 0
      ? creditLineValues.reduce((a, b) => a + b, 0) / creditLineValues.length
      : 0;

  const operationsValues = records
    .filter((r) => r.operations_incentive_pct !== null)
    .map((r) => r.operations_incentive_pct as number);
  const avgOperations =
    operationsValues.length > 0
      ? operationsValues.reduce((a, b) => a + b, 0) / operationsValues.length
      : 0;

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        backgroundColor: 'background.paper',
        borderRadius: 2,
      }}
    >
      <Stack spacing={2}>
        {/* Header with export button */}
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={2}
        >
          <Box display="flex" alignItems="center" gap={1}>
            <AssessmentIcon color="primary" />
            <Typography variant="h6" component="h2" color="primary">
              Resultados de Extraccion
            </Typography>
            <Chip
              label={`${records.length} registros`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>

          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            disabled={records.length === 0}
          >
            Exportar Excel
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 2,
            p: 2,
            backgroundColor: 'grey.50',
            borderRadius: 1,
          }}
        >
          <Box>
            <Typography variant="caption" color="text.secondary">
              Contratos Bono
            </Typography>
            <Typography variant="body1" fontWeight={600} color="success.main">
              {bonoCount}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Contratos Incentivos
            </Typography>
            <Typography variant="body1" fontWeight={600} color="warning.main">
              {incentivosCount}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Desconocidos
            </Typography>
            <Typography variant="body1" fontWeight={600} color="error.main">
              {unknownCount}
            </Typography>
          </Box>
          <Box sx={{ borderLeft: '1px solid', borderColor: 'divider', pl: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Encontrados
            </Typography>
            <Typography variant="body1" fontWeight={600} color="success.main">
              {foundCount}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Sin Contrato
            </Typography>
            <Typography variant="body1" fontWeight={600} color="warning.main">
              {notFoundCount}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Errores
            </Typography>
            <Typography variant="body1" fontWeight={600} color="error.main">
              {errorCount}
            </Typography>
          </Box>
          <Box sx={{ borderLeft: '1px solid', borderColor: 'divider', pl: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Promedio Linea Credito
            </Typography>
            <Typography variant="body1" fontWeight={600}>
              {avgCreditLine.toFixed(2)}%
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Promedio Operaciones
            </Typography>
            <Typography variant="body1" fontWeight={600}>
              {avgOperations.toFixed(2)}%
            </Typography>
          </Box>
        </Box>

        {/* Data Grid */}
        <Box sx={{ height: 500, width: '100%' }}>
          <DataGrid
            rows={records}
            columns={columns}
            getRowId={getRowId}
            loading={loading}
            pageSizeOptions={[10, 25, 50, 100]}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25 },
              },
              sorting: {
                sortModel: [{ field: 'broker_name', sort: 'asc' }],
              },
            }}
            disableRowSelectionOnClick
            sx={{
              '& .MuiDataGrid-cell': {
                py: 1,
              },
              '& .MuiDataGrid-columnHeaders': {
                backgroundColor: 'grey.100',
                fontWeight: 600,
              },
            }}
          />
        </Box>
      </Stack>
    </Paper>
  );
};

export default FKBrokerIncentiveResultsGrid;
