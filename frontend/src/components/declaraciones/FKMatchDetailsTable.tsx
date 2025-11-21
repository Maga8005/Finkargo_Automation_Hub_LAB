/**
 * FKMatchDetailsTable - Match Details Table Component
 *
 * DataGrid table displaying matched payment-declaration records with confidence scores,
 * amount/date differences, customer similarity, and action buttons. Supports sorting,
 * filtering, pagination, and row selection for bulk operations.
 */
import React, { useMemo } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import type {
  GridColDef,
  GridRenderCellParams,
  GridRowSelectionModel,
} from '@mui/x-data-grid';
import {
  Box,
  Chip,
  IconButton,
  LinearProgress,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import type { MatchDetail } from '../../types/matching_results_types';

interface FKMatchDetailsTableProps {
  matches: MatchDetail[];
  loading?: boolean;
  page: number;
  pageSize: number;
  totalCount: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newPageSize: number) => void;
  onSortChange?: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  onViewDetails: (matchId: string) => void;
  onOverride?: (matchId: string) => void;
  onReject?: (matchId: string) => void;
  selectedRows?: string[];
  onSelectionChange?: (selectedIds: string[]) => void;
}

const FKMatchDetailsTable: React.FC<FKMatchDetailsTableProps> = ({
  matches,
  loading = false,
  page,
  pageSize,
  totalCount,
  onPageChange,
  onPageSizeChange,
  onViewDetails,
  onOverride,
  onReject,
  selectedRows = [],
  onSelectionChange,
}) => {
  console.log('[FKMatchDetailsTable] Rendering table', {
    matchesCount: matches.length,
    totalCount,
    page,
    pageSize,
    loading,
  });

  // Format currency with $ symbol
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Get color for amount difference
  const getAmountDifferenceColor = (difference: number): string => {
    if (difference === 0) return 'success.main';
    if (difference <= 0.20) return 'warning.main';
    return 'error.main';
  };

  // Get color for date difference
  const getDateDifferenceColor = (days: number): string => {
    if (days === 0) return 'success.main';
    if (days <= 3) return 'info.main';
    if (days <= 7) return 'warning.main';
    return 'error.main';
  };

  // Get color for customer similarity
  const getCustomerSimilarityColor = (similarity: number): string => {
    if (similarity >= 0.95) return 'success.main';
    if (similarity >= 0.75) return 'info.main';
    return 'warning.main';
  };

  // Get color for confidence score
  const getConfidenceColor = (score: number): string => {
    if (score >= 0.95) return 'success.main';
    if (score >= 0.70) return 'info.main';
    return 'warning.main';
  };

  // Get match status color
  const getMatchStatusColor = (
    status: 'approved' | 'pending_review' | 'rejected'
  ): 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      default:
        return 'warning';
    }
  };

  // Get match status label
  const getMatchStatusLabel = (status: 'approved' | 'pending_review' | 'rejected'): string => {
    switch (status) {
      case 'approved':
        return 'Approved';
      case 'rejected':
        return 'Rejected';
      default:
        return 'Pending Review';
    }
  };

  // Define columns
  const columns: GridColDef[] = useMemo(
    () => [
      {
        field: 'payment_date',
        headerName: 'Payment Date',
        width: 130,
        renderCell: (params: GridRenderCellParams) => (
          <Typography variant="body2">{params.value}</Typography>
        ),
      },
      {
        field: 'declaration_number',
        headerName: 'Declaration Number',
        width: 150,
        renderCell: (params: GridRenderCellParams) => (
          <Tooltip title="Click to view details">
            <Typography
              variant="body2"
              sx={{
                color: 'primary.main',
                cursor: 'pointer',
                '&:hover': { textDecoration: 'underline' },
              }}
              onClick={() => onViewDetails(params.row.id)}
            >
              {params.value}
            </Typography>
          </Tooltip>
        ),
      },
      {
        field: 'amount_difference',
        headerName: 'Amount Difference',
        width: 150,
        renderCell: (params: GridRenderCellParams) => {
          const difference = Math.abs(params.value as number);
          const color = getAmountDifferenceColor(difference);
          return (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {difference === 0 && <CheckCircleIcon sx={{ fontSize: 16, color }} />}
              {difference > 0 && difference <= 0.20 && <WarningIcon sx={{ fontSize: 16, color }} />}
              {difference > 0.20 && <CloseIcon sx={{ fontSize: 16, color }} />}
              <Typography variant="body2" sx={{ color, fontWeight: 600 }}>
                {formatCurrency(difference)}
              </Typography>
            </Box>
          );
        },
      },
      {
        field: 'date_difference_days',
        headerName: 'Date Difference',
        width: 140,
        renderCell: (params: GridRenderCellParams) => {
          const days = Math.abs(params.value as number);
          const color = getDateDifferenceColor(days);
          return (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {days === 0 && <CheckCircleIcon sx={{ fontSize: 16, color }} />}
              <Typography variant="body2" sx={{ color, fontWeight: 600 }}>
                {days === 0 ? 'Same day' : `${days} day${days !== 1 ? 's' : ''}`}
              </Typography>
            </Box>
          );
        },
      },
      {
        field: 'customer_name_similarity',
        headerName: 'Customer Similarity',
        width: 170,
        renderCell: (params: GridRenderCellParams) => {
          const similarity = params.value as number;
          const percentage = (similarity * 100).toFixed(0);
          const color = getCustomerSimilarityColor(similarity);
          return (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <LinearProgress
                variant="determinate"
                value={similarity * 100}
                sx={{
                  flex: 1,
                  height: 6,
                  borderRadius: 1,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: color,
                  },
                }}
              />
              <Typography variant="caption" fontWeight={600} sx={{ color, minWidth: 35 }}>
                {percentage}%
              </Typography>
            </Box>
          );
        },
      },
      {
        field: 'confidence_score',
        headerName: 'Confidence',
        width: 150,
        renderCell: (params: GridRenderCellParams) => {
          const score = params.value as number;
          const percentage = (score * 100).toFixed(0);
          const color = getConfidenceColor(score);
          return (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <LinearProgress
                variant="determinate"
                value={score * 100}
                sx={{
                  flex: 1,
                  height: 6,
                  borderRadius: 1,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: color,
                  },
                }}
              />
              <Typography variant="caption" fontWeight={600} sx={{ color, minWidth: 35 }}>
                {percentage}%
              </Typography>
            </Box>
          );
        },
      },
      {
        field: 'match_status',
        headerName: 'Status',
        width: 130,
        renderCell: (params: GridRenderCellParams) => {
          const status = params.value as 'approved' | 'pending_review' | 'rejected';
          return (
            <Chip
              label={getMatchStatusLabel(status)}
              color={getMatchStatusColor(status)}
              size="small"
              sx={{ fontWeight: 600 }}
            />
          );
        },
      },
      {
        field: 'is_manual_override',
        headerName: 'Type',
        width: 100,
        renderCell: (params: GridRenderCellParams) => {
          if (params.value) {
            return (
              <Tooltip title={params.row.override_reason || 'Manual override'}>
                <Chip
                  label="Manual"
                  size="small"
                  color="secondary"
                  sx={{ fontWeight: 600 }}
                />
              </Tooltip>
            );
          }
          return (
            <Chip
              label="Auto"
              size="small"
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          );
        },
      },
      {
        field: 'actions',
        headerName: 'Actions',
        width: 150,
        sortable: false,
        renderCell: (params: GridRenderCellParams) => (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="View Details">
              <IconButton
                size="small"
                onClick={() => onViewDetails(params.row.id)}
                sx={{ color: 'primary.main' }}
              >
                <VisibilityIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            {onOverride && (
              <Tooltip title="Override Match">
                <IconButton
                  size="small"
                  onClick={() => onOverride(params.row.id)}
                  sx={{ color: 'info.main' }}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {onReject && params.row.match_status !== 'rejected' && (
              <Tooltip title="Reject Match">
                <IconButton
                  size="small"
                  onClick={() => onReject(params.row.id)}
                  sx={{ color: 'error.main' }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        ),
      },
    ],
    [onViewDetails, onOverride, onReject]
  );

  // Handle selection change
  const handleSelectionChange = (selectionModel: GridRowSelectionModel) => {
    if (onSelectionChange) {
      // GridRowSelectionModel has an 'ids' Set property
      const selectedIds = Array.from(selectionModel.ids) as string[];
      onSelectionChange(selectedIds);
    }
  };

  return (
    <Box sx={{ width: '100%', height: 650 }}>
      <DataGrid
        rows={matches}
        columns={columns}
        loading={loading}
        pagination
        paginationMode="server"
        rowCount={totalCount}
        paginationModel={{
          page: page - 1, // DataGrid uses 0-based indexing
          pageSize: pageSize,
        }}
        onPaginationModelChange={(model) => {
          if (model.page !== page - 1) {
            onPageChange(model.page + 1); // Convert back to 1-based
          }
          if (model.pageSize !== pageSize) {
            onPageSizeChange(model.pageSize);
          }
        }}
        pageSizeOptions={[10, 25, 50, 100]}
        checkboxSelection={!!onSelectionChange}
        rowSelectionModel={{
          type: 'include',
          ids: new Set(selectedRows),
        }}
        onRowSelectionModelChange={handleSelectionChange}
        disableRowSelectionOnClick
        sx={{
          border: 'none',
          '& .MuiDataGrid-cell:focus': {
            outline: 'none',
          },
          '& .MuiDataGrid-row:hover': {
            backgroundColor: 'action.hover',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: 'grey.100',
            borderBottom: '2px solid',
            borderColor: 'divider',
          },
        }}
      />
    </Box>
  );
};

export default FKMatchDetailsTable;
