/**
 * MatchingResultsDashboardPage - Main Matching Results Dashboard
 *
 * Comprehensive dashboard for viewing and managing declaration-payment matching results.
 * Includes statistics, match details table, unmatched records, and quality assessment.
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Breadcrumbs,
  Link,
  Tabs,
  Tab,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import FKMatchingStatisticsCard from '../../components/declaraciones/FKMatchingStatisticsCard';
import FKMatchDetailsTable from '../../components/declaraciones/FKMatchDetailsTable';
import FKUnmatchedRecordsView from '../../components/declaraciones/FKUnmatchedRecordsView';
import FKConfidenceDistributionChart from '../../components/declaraciones/FKConfidenceDistributionChart';
import FKMatchDetailModal from '../../components/declaraciones/FKMatchDetailModal';
import FKManualMatchOverrideForm from '../../components/declaraciones/FKManualMatchOverrideForm';
import {
  getMatchingSummary,
  getMatchingResults,
  getUnmatchedPayments,
  getUnmatchedDeclarations,
  getMatchDetail,
  createManualOverride,
  bulkApproveMatches,
  bulkRejectMatches,
} from '../../services/matchingResultsService';
import type {
  MatchingResultsSummary,
  MatchDetail,
  UnmatchedPayment,
  UnmatchedDeclaration,
  ManualOverrideRequest,
} from '../../types/matching_results_types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const MatchingResultsDashboardPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  // State
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<MatchingResultsSummary | null>(null);
  const [matches, setMatches] = useState<MatchDetail[]>([]);
  const [unmatchedPayments, setUnmatchedPayments] = useState<UnmatchedPayment[]>([]);
  const [unmatchedDeclarations, setUnmatchedDeclarations] = useState<UnmatchedDeclaration[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<MatchDetail | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [overrideFormOpen, setOverrideFormOpen] = useState(false);
  const [selectedRows, setSelectedRows] = useState<string[]>([]);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalCount, setTotalCount] = useState(0);

  console.log('[MatchingResultsDashboardPage] Rendering dashboard', {
    sessionId,
    activeTab,
    loading,
  });

  // Load data
  useEffect(() => {
    if (!sessionId) {
      setError('Session ID is required');
      setLoading(false);
      return;
    }

    loadData();
  }, [sessionId]);

  const loadData = async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      // Load summary
      const summaryData = await getMatchingSummary(sessionId);
      setSummary(summaryData);

      // Load matches
      const resultsData = await getMatchingResults(sessionId, {}, { page, page_size: pageSize });
      setMatches(resultsData.matches);
      setTotalCount(resultsData.total_count);

      // Load unmatched records
      const [paymentsData, declarationsData] = await Promise.all([
        getUnmatchedPayments(sessionId),
        getUnmatchedDeclarations(sessionId),
      ]);
      setUnmatchedPayments(paymentsData);
      setUnmatchedDeclarations(declarationsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load matching results';
      setError(errorMessage);
      console.error('[MatchingResultsDashboardPage] Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Handle view details
  const handleViewDetails = async (matchId: string) => {
    try {
      const matchDetail = await getMatchDetail(matchId);
      setSelectedMatch(matchDetail);
      setDetailModalOpen(true);
    } catch (err) {
      console.error('[MatchingResultsDashboardPage] Error loading match detail:', err);
    }
  };

  // Handle manual override
  const handleManualOverrideSubmit = async (data: ManualOverrideRequest) => {
    if (!sessionId) return;

    try {
      await createManualOverride(sessionId, data);
      await loadData(); // Reload data
    } catch (err) {
      throw err; // Let form handle error
    }
  };

  // Handle bulk approve
  const handleBulkApprove = async () => {
    if (selectedRows.length === 0) return;

    try {
      await bulkApproveMatches(selectedRows, 'Bulk approval from dashboard');
      await loadData();
      setSelectedRows([]);
    } catch (err) {
      console.error('[MatchingResultsDashboardPage] Error bulk approving:', err);
    }
  };

  // Handle bulk reject
  const handleBulkReject = async () => {
    if (selectedRows.length === 0) return;

    try {
      await bulkRejectMatches(selectedRows, 'Bulk rejection from dashboard');
      await loadData();
      setSelectedRows([]);
    } catch (err) {
      console.error('[MatchingResultsDashboardPage] Error bulk rejecting:', err);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link href="/" underline="hover" color="inherit">
          Home
        </Link>
        <Link href="/declaraciones" underline="hover" color="inherit">
          Declaraciones
        </Link>
        <Typography color="text.primary">Matching Results</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Matching Results Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Session: {sessionId}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/declaraciones/excel-upload')}
          >
            Back to Upload
          </Button>
          <Button
            variant="contained"
            startIcon={<AssessmentIcon />}
            onClick={() => navigate(`/declaraciones/generate-report/${sessionId}`)}
          >
            Generate Report
          </Button>
        </Box>
      </Box>

      {/* Statistics Card */}
      <Box sx={{ mb: 3 }}>
        <FKMatchingStatisticsCard statistics={summary?.statistics || null} loading={loading} />
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Matched Records" />
          <Tab label="Unmatched Records" />
          <Tab label="Confidence Distribution" />
        </Tabs>
      </Box>

      {/* Matched Records Tab */}
      <TabPanel value={activeTab} index={0}>
        {selectedRows.length > 0 && (
          <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
            <Typography variant="body2">{selectedRows.length} matches selected</Typography>
            <Button variant="contained" color="success" onClick={handleBulkApprove}>
              Approve Selected
            </Button>
            <Button variant="outlined" color="error" onClick={handleBulkReject}>
              Reject Selected
            </Button>
          </Box>
        )}
        <FKMatchDetailsTable
          matches={matches}
          loading={loading}
          page={page}
          pageSize={pageSize}
          totalCount={totalCount}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          onViewDetails={handleViewDetails}
          selectedRows={selectedRows}
          onSelectionChange={setSelectedRows}
        />
      </TabPanel>

      {/* Unmatched Records Tab */}
      <TabPanel value={activeTab} index={1}>
        <FKUnmatchedRecordsView
          unmatchedPayments={unmatchedPayments}
          unmatchedDeclarations={unmatchedDeclarations}
          onAttemptManualMatch={() => setOverrideFormOpen(true)}
        />
      </TabPanel>

      {/* Confidence Distribution Tab */}
      <TabPanel value={activeTab} index={2}>
        <FKConfidenceDistributionChart
          distribution={summary?.confidence_distribution || null}
          loading={loading}
        />
      </TabPanel>

      {/* Match Detail Modal */}
      <FKMatchDetailModal
        open={detailModalOpen}
        match={selectedMatch}
        onClose={() => setDetailModalOpen(false)}
        onApprove={async (matchId) => {
          await bulkApproveMatches([matchId]);
          await loadData();
          setDetailModalOpen(false);
        }}
        onReject={async (matchId) => {
          await bulkRejectMatches([matchId]);
          await loadData();
          setDetailModalOpen(false);
        }}
      />

      {/* Manual Override Form */}
      <FKManualMatchOverrideForm
        open={overrideFormOpen}
        onClose={() => setOverrideFormOpen(false)}
        onSubmit={handleManualOverrideSubmit}
      />
    </Container>
  );
};

export default MatchingResultsDashboardPage;
