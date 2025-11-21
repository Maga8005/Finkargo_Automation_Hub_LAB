/**
 * FKUnmatchedRecordsView - Unmatched Records Display Component
 *
 * Displays unmatched payments and declarations in separate tabs with clear unmatch reasons.
 * Color-codes reasons by type (amount, date, customer name mismatch, no candidates).
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Tabs,
  Tab,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Tooltip,
  Alert,
  Paper,
} from '@mui/material';
import {
  ErrorOutline as ErrorOutlineIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  HelpOutline as HelpOutlineIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import type { UnmatchedPayment, UnmatchedDeclaration } from '../../types/matching_results_types';

interface FKUnmatchedRecordsViewProps {
  unmatchedPayments: UnmatchedPayment[];
  unmatchedDeclarations: UnmatchedDeclaration[];
  onAttemptManualMatch?: (
    type: 'payment' | 'declaration',
    record: UnmatchedPayment | UnmatchedDeclaration
  ) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

const FKUnmatchedRecordsView: React.FC<FKUnmatchedRecordsViewProps> = ({
  unmatchedPayments,
  unmatchedDeclarations,
  onAttemptManualMatch,
}) => {
  const [activeTab, setActiveTab] = useState(0);

  console.log('[FKUnmatchedRecordsView] Rendering unmatched records view', {
    unmatchedPayments: unmatchedPayments.length,
    unmatchedDeclarations: unmatchedDeclarations.length,
    activeTab,
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

  // Get unmatch reason color
  const getUnmatchReasonColor = (
    reasonType: 'amount_mismatch' | 'date_mismatch' | 'customer_name_mismatch' | 'no_candidates'
  ): 'error' | 'warning' | 'info' | 'default' => {
    switch (reasonType) {
      case 'amount_mismatch':
        return 'error';
      case 'date_mismatch':
        return 'warning';
      case 'customer_name_mismatch':
        return 'info';
      case 'no_candidates':
        return 'default';
    }
  };

  // Get unmatch reason icon
  const getUnmatchReasonIcon = (
    reasonType: 'amount_mismatch' | 'date_mismatch' | 'customer_name_mismatch' | 'no_candidates'
  ) => {
    switch (reasonType) {
      case 'amount_mismatch':
        return <ErrorOutlineIcon fontSize="small" />;
      case 'date_mismatch':
        return <WarningIcon fontSize="small" />;
      case 'customer_name_mismatch':
        return <InfoIcon fontSize="small" />;
      case 'no_candidates':
        return <HelpOutlineIcon fontSize="small" />;
    }
  };

  // Get tooltip explanation for unmatch reason type
  const getUnmatchReasonTooltip = (
    reasonType: 'amount_mismatch' | 'date_mismatch' | 'customer_name_mismatch' | 'no_candidates'
  ): string => {
    switch (reasonType) {
      case 'amount_mismatch':
        return 'Amount difference exceeds tolerance threshold (±$0.20 or ±5%)';
      case 'date_mismatch':
        return 'Date difference exceeds tolerance range (±7 days)';
      case 'customer_name_mismatch':
        return 'Customer name similarity below threshold (75%)';
      case 'no_candidates':
        return 'No potential matches found in the dataset';
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Unmatched Records Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Payments and declarations that could not be automatically matched with clear reasons
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Unmatched Payments
                  <Chip label={unmatchedPayments.length} size="small" color="error" />
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Unmatched Declarations
                  <Chip label={unmatchedDeclarations.length} size="small" color="warning" />
                </Box>
              }
            />
          </Tabs>
        </Box>

        {/* Unmatched Payments Tab */}
        <TabPanel value={activeTab} index={0}>
          {unmatchedPayments.length === 0 ? (
            <Alert severity="success">
              All payments have been matched to declarations. No unmatched payments.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'grey.100' }}>
                    <TableCell>Payment Date</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Customer Name</TableCell>
                    <TableCell>Unmatch Reason</TableCell>
                    <TableCell>Closest Match Info</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {unmatchedPayments.map((payment, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2">{payment.payment_date}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {formatCurrency(payment.amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={`Normalized: ${payment.customer_name_normalized}`}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {payment.customer_name}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={getUnmatchReasonTooltip(payment.unmatch_reason_type)}>
                          <Chip
                            icon={getUnmatchReasonIcon(payment.unmatch_reason_type)}
                            label={payment.unmatch_reason}
                            color={getUnmatchReasonColor(payment.unmatch_reason_type)}
                            size="small"
                            sx={{ maxWidth: 300 }}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        {payment.closest_declaration_number && (
                          <Box>
                            <Typography variant="caption" display="block">
                              Declaration: {payment.closest_declaration_number}
                            </Typography>
                            {payment.closest_amount_difference !== undefined && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                Δ Amount: {formatCurrency(payment.closest_amount_difference)}
                              </Typography>
                            )}
                            {payment.closest_date_difference_days !== undefined && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                Δ Date: {payment.closest_date_difference_days} days
                              </Typography>
                            )}
                            {payment.closest_customer_similarity !== undefined && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                Similarity: {(payment.closest_customer_similarity * 100).toFixed(0)}
                                %
                              </Typography>
                            )}
                          </Box>
                        )}
                        {!payment.closest_declaration_number && (
                          <Typography variant="caption" color="text.secondary">
                            No close matches found
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {onAttemptManualMatch && (
                          <Tooltip title="Attempt manual match">
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<EditIcon />}
                              onClick={() => onAttemptManualMatch('payment', payment)}
                            >
                              Match
                            </Button>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Unmatched Declarations Tab */}
        <TabPanel value={activeTab} index={1}>
          {unmatchedDeclarations.length === 0 ? (
            <Alert severity="success">
              All declarations have been assigned to payments. No unmatched declarations.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'grey.100' }}>
                    <TableCell>Declaration Number</TableCell>
                    <TableCell>Declaration Date</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Customer Name</TableCell>
                    <TableCell>Unmatch Reason</TableCell>
                    <TableCell>Closest Match Info</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {unmatchedDeclarations.map((declaration, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {declaration.declaration_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{declaration.declaration_date}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {formatCurrency(declaration.amount)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={`Normalized: ${declaration.customer_name_normalized}`}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {declaration.customer_name}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={getUnmatchReasonTooltip(declaration.unmatch_reason_type)}>
                          <Chip
                            icon={getUnmatchReasonIcon(declaration.unmatch_reason_type)}
                            label={declaration.unmatch_reason}
                            color={getUnmatchReasonColor(declaration.unmatch_reason_type)}
                            size="small"
                            sx={{ maxWidth: 300 }}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        {declaration.closest_payment_date && (
                          <Box>
                            <Typography variant="caption" display="block">
                              Payment Date: {declaration.closest_payment_date}
                            </Typography>
                            {declaration.closest_amount_difference !== undefined && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                Δ Amount: {formatCurrency(declaration.closest_amount_difference)}
                              </Typography>
                            )}
                            {declaration.closest_date_difference_days !== undefined && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                Δ Date: {declaration.closest_date_difference_days} days
                              </Typography>
                            )}
                            {declaration.closest_customer_similarity !== undefined && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                Similarity: {(declaration.closest_customer_similarity * 100).toFixed(0)}
                                %
                              </Typography>
                            )}
                          </Box>
                        )}
                        {!declaration.closest_payment_date && (
                          <Typography variant="caption" color="text.secondary">
                            No close matches found
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {onAttemptManualMatch && (
                          <Tooltip title="Attempt manual match">
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<EditIcon />}
                              onClick={() => onAttemptManualMatch('declaration', declaration)}
                            >
                              Match
                            </Button>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>
      </CardContent>
    </Card>
  );
};

export default FKUnmatchedRecordsView;
