/**
 * FKMatchDetailsTable - Match Details Table Component
 *
 * MUI Table displaying matched payment-declaration records with confidence scores,
 * amount/date differences, customer similarity, and action buttons. Supports sorting,
 * pagination, and row selection for bulk operations.
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Chip,
  IconButton,
  LinearProgress,
  Tooltip,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Paper,
  Checkbox,
  CircularProgress,
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

type Order = 'asc' | 'desc';

const FKMatchDetailsTable: React.FC<FKMatchDetailsTableProps> = ({
  matches,
  loading = false,
  page,
  pageSize,
  totalCount,
  onPageChange,
  onPageSizeChange,
  onSortChange,
  onViewDetails,
  onOverride,
  onReject,
  selectedRows = [],
  onSelectionChange,
}) => {
  const [orderBy, setOrderBy] = useState<string>('payment_date');
  const [order, setOrder] = useState<Order>('desc');

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

  // Handle sort request
  const handleRequestSort = (property: string) => {
    const isAsc = orderBy === property && order === 'asc';
    const newOrder = isAsc ? 'desc' : 'asc';
    setOrder(newOrder);
    setOrderBy(property);
    if (onSortChange) {
      onSortChange(property, newOrder);
    }
  };

  // Handle select all click
  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (onSelectionChange) {
      if (event.target.checked) {
        const newSelected = matches.map((m) => m.id);
        onSelectionChange(newSelected);
        return;
      }
      onSelectionChange([]);
    }
  };

  // Handle click on row checkbox
  const handleClick = (id: string) => {
    if (!onSelectionChange) return;

    const selectedIndex = selectedRows.indexOf(id);
    let newSelected: string[] = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selectedRows, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selectedRows.slice(1));
    } else if (selectedIndex === selectedRows.length - 1) {
      newSelected = newSelected.concat(selectedRows.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selectedRows.slice(0, selectedIndex),
        selectedRows.slice(selectedIndex + 1)
      );
    }

    onSelectionChange(newSelected);
  };

  const isSelected = (id: string) => selectedRows.indexOf(id) !== -1;

  // Sort data client-side for display
  const sortedMatches = useMemo(() => {
    return [...matches].sort((a, b) => {
      const aValue = a[orderBy as keyof MatchDetail];
      const bValue = b[orderBy as keyof MatchDetail];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return order === 'asc' ? aValue - bValue : bValue - aValue;
      }

      const aStr = String(aValue);
      const bStr = String(bValue);
      return order === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
    });
  }, [matches, orderBy, order]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {onSelectionChange && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selectedRows.length > 0 && selectedRows.length < matches.length}
                    checked={matches.length > 0 && selectedRows.length === matches.length}
                    onChange={handleSelectAllClick}
                  />
                </TableCell>
              )}
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'payment_date'}
                  direction={orderBy === 'payment_date' ? order : 'asc'}
                  onClick={() => handleRequestSort('payment_date')}
                >
                  Payment Date
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'declaration_number'}
                  direction={orderBy === 'declaration_number' ? order : 'asc'}
                  onClick={() => handleRequestSort('declaration_number')}
                >
                  Declaration Number
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'amount_difference'}
                  direction={orderBy === 'amount_difference' ? order : 'asc'}
                  onClick={() => handleRequestSort('amount_difference')}
                >
                  Amount Difference
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'date_difference_days'}
                  direction={orderBy === 'date_difference_days' ? order : 'asc'}
                  onClick={() => handleRequestSort('date_difference_days')}
                >
                  Date Difference
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ minWidth: 150 }}>Customer Similarity</TableCell>
              <TableCell sx={{ minWidth: 130 }}>Confidence</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedMatches.map((row) => {
              const isItemSelected = isSelected(row.id);
              return (
                <TableRow
                  hover
                  key={row.id}
                  selected={isItemSelected}
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  {onSelectionChange && (
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={isItemSelected}
                        onChange={() => handleClick(row.id)}
                      />
                    </TableCell>
                  )}
                  <TableCell>
                    <Typography variant="body2">{row.payment_date}</Typography>
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Click to view details">
                      <Typography
                        variant="body2"
                        sx={{
                          color: 'primary.main',
                          cursor: 'pointer',
                          '&:hover': { textDecoration: 'underline' },
                        }}
                        onClick={() => onViewDetails(row.id)}
                      >
                        {row.declaration_number}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    {(() => {
                      const difference = Math.abs(row.amount_difference);
                      const color = getAmountDifferenceColor(difference);
                      return (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {difference === 0 && <CheckCircleIcon sx={{ fontSize: 16, color }} />}
                          {difference > 0 && difference <= 0.20 && (
                            <WarningIcon sx={{ fontSize: 16, color }} />
                          )}
                          {difference > 0.20 && <CloseIcon sx={{ fontSize: 16, color }} />}
                          <Typography variant="body2" sx={{ color, fontWeight: 600 }}>
                            {formatCurrency(difference)}
                          </Typography>
                        </Box>
                      );
                    })()}
                  </TableCell>
                  <TableCell>
                    {(() => {
                      const days = Math.abs(row.date_difference_days);
                      const color = getDateDifferenceColor(days);
                      return (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {days === 0 && <CheckCircleIcon sx={{ fontSize: 16, color }} />}
                          <Typography variant="body2" sx={{ color, fontWeight: 600 }}>
                            {days === 0 ? 'Same day' : `${days} day${days !== 1 ? 's' : ''}`}
                          </Typography>
                        </Box>
                      );
                    })()}
                  </TableCell>
                  <TableCell>
                    {(() => {
                      const similarity = row.customer_name_similarity;
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
                          <Typography
                            variant="caption"
                            fontWeight={600}
                            sx={{ color, minWidth: 35 }}
                          >
                            {percentage}%
                          </Typography>
                        </Box>
                      );
                    })()}
                  </TableCell>
                  <TableCell>
                    {(() => {
                      const score = row.confidence_score;
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
                          <Typography
                            variant="caption"
                            fontWeight={600}
                            sx={{ color, minWidth: 35 }}
                          >
                            {percentage}%
                          </Typography>
                        </Box>
                      );
                    })()}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getMatchStatusLabel(row.match_status)}
                      color={getMatchStatusColor(row.match_status)}
                      size="small"
                      sx={{ fontWeight: 600 }}
                    />
                  </TableCell>
                  <TableCell>
                    {row.is_manual_override ? (
                      <Tooltip title={row.override_reason || 'Manual override'}>
                        <Chip
                          label="Manual"
                          size="small"
                          color="secondary"
                          sx={{ fontWeight: 600 }}
                        />
                      </Tooltip>
                    ) : (
                      <Chip
                        label="Auto"
                        size="small"
                        variant="outlined"
                        sx={{ fontWeight: 600 }}
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => onViewDetails(row.id)}
                          sx={{ color: 'primary.main' }}
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {onOverride && (
                        <Tooltip title="Override Match">
                          <IconButton
                            size="small"
                            onClick={() => onOverride(row.id)}
                            sx={{ color: 'info.main' }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {onReject && row.match_status !== 'rejected' && (
                        <Tooltip title="Reject Match">
                          <IconButton
                            size="small"
                            onClick={() => onReject(row.id)}
                            sx={{ color: 'error.main' }}
                          >
                            <CloseIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={totalCount}
        rowsPerPage={pageSize}
        page={page - 1}
        onPageChange={(_, newPage) => onPageChange(newPage + 1)}
        onRowsPerPageChange={(event) => onPageSizeChange(parseInt(event.target.value, 10))}
        labelRowsPerPage="Rows per page:"
        labelDisplayedRows={({ from, to, count }) =>
          `${from}-${to} of ${count !== -1 ? count : `more than ${to}`}`
        }
      />
    </Box>
  );
};

export default FKMatchDetailsTable;
