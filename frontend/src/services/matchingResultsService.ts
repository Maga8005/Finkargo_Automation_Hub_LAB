/**
 * Matching Results Service - API Integration
 *
 * Provides API methods for interacting with declaration-payment matching results.
 * Includes endpoints for viewing match details, statistics, unmatched records,
 * manual overrides, and bulk operations.
 *
 * @module matchingResultsService
 */

import apiClient from '../api/clients/apiClient';
import type {
  MatchDetail,
  MatchingResultsStatistics,
  MatchingResultsSummary,
  MatchingResultsResponse,
  MatchingResultsFilters,
  MatchingResultsPagination,
  UnmatchedPayment,
  UnmatchedDeclaration,
  ManualOverrideRequest,
  BulkActionRequest,
  BulkActionResponse,
} from '../types/matching_results_types';

const BASE_PATH = '/v1/declaraciones/matching';

/**
 * Fetch paginated matching results with optional filtering
 *
 * @param sessionId - Upload session ID
 * @param filters - Optional filters for confidence, dates, status, etc.
 * @param pagination - Pagination and sorting parameters
 * @returns Promise resolving to paginated matching results
 *
 * @example
 * const results = await getMatchingResults(
 *   '550e8400-e29b-41d4-a716-446655440000',
 *   { confidence_min: 0.70, match_status: 'approved' },
 *   { page: 1, page_size: 25, sort_by: 'confidence_score', sort_order: 'desc' }
 * );
 * console.log('Fetched', results.matches.length, 'matches');
 */
export const getMatchingResults = async (
  sessionId: string,
  filters?: MatchingResultsFilters,
  pagination?: MatchingResultsPagination
): Promise<MatchingResultsResponse> => {
  console.log('[matchingResultsService.getMatchingResults] Fetching matching results', {
    sessionId,
    filters,
    pagination,
  });

  try {
    const params: Record<string, string | number> = {
      session_id: sessionId,
      page: pagination?.page || 1,
      page_size: pagination?.page_size || 25,
    };

    if (pagination?.sort_by) {
      params.sort_by = pagination.sort_by;
    }
    if (pagination?.sort_order) {
      params.sort_order = pagination.sort_order;
    }

    if (filters) {
      if (filters.confidence_min !== undefined) {
        params.confidence_min = filters.confidence_min;
      }
      if (filters.confidence_max !== undefined) {
        params.confidence_max = filters.confidence_max;
      }
      if (filters.date_from) {
        params.date_from = filters.date_from;
      }
      if (filters.date_to) {
        params.date_to = filters.date_to;
      }
      if (filters.match_status && filters.match_status !== 'all') {
        params.match_status = filters.match_status;
      }
      if (filters.amount_difference_max !== undefined) {
        params.amount_difference_max = filters.amount_difference_max;
      }
      if (filters.is_manual_override !== undefined) {
        params.is_manual_override = filters.is_manual_override ? 'true' : 'false';
      }
    }

    const response = await apiClient.get<MatchingResultsResponse>(
      `${BASE_PATH}/results`,
      { params }
    );

    console.log('[matchingResultsService.getMatchingResults] Fetched results successfully', {
      total_count: response.data.total_count,
      page: response.data.page,
      matches_count: response.data.matches.length,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.getMatchingResults] Error fetching matching results:', error);
    throw error;
  }
};

/**
 * Fetch aggregate statistics and summary for matching session
 *
 * @param sessionId - Upload session ID
 * @returns Promise resolving to matching summary with statistics, distribution, and quality metrics
 *
 * @example
 * const summary = await getMatchingSummary('550e8400-e29b-41d4-a716-446655440000');
 * console.log('Matched:', summary.statistics.matched_payments, '/', summary.statistics.total_payments);
 * console.log('Average confidence:', summary.statistics.average_confidence_score);
 */
export const getMatchingSummary = async (
  sessionId: string
): Promise<MatchingResultsSummary> => {
  console.log('[matchingResultsService.getMatchingSummary] Fetching matching summary', {
    sessionId,
  });

  try {
    const response = await apiClient.get<MatchingResultsSummary>(
      `${BASE_PATH}/summary`,
      { params: { session_id: sessionId } }
    );

    console.log('[matchingResultsService.getMatchingSummary] Fetched summary successfully', {
      matched_payments: response.data.statistics.matched_payments,
      total_payments: response.data.statistics.total_payments,
      average_confidence: response.data.statistics.average_confidence_score,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.getMatchingSummary] Error fetching summary:', error);
    throw error;
  }
};

/**
 * Fetch aggregate statistics only (lightweight endpoint)
 *
 * @param sessionId - Upload session ID
 * @returns Promise resolving to matching statistics
 *
 * @example
 * const stats = await getMatchingStatistics('550e8400-e29b-41d4-a716-446655440000');
 * console.log('Match percentage:', stats.match_percentage.toFixed(1) + '%');
 */
export const getMatchingStatistics = async (
  sessionId: string
): Promise<MatchingResultsStatistics> => {
  console.log('[matchingResultsService.getMatchingStatistics] Fetching statistics', {
    sessionId,
  });

  try {
    const response = await apiClient.get<MatchingResultsStatistics>(
      `${BASE_PATH}/statistics`,
      { params: { session_id: sessionId } }
    );

    console.log('[matchingResultsService.getMatchingStatistics] Fetched statistics successfully', {
      total_payments: response.data.total_payments,
      matched_payments: response.data.matched_payments,
      match_percentage: response.data.match_percentage,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.getMatchingStatistics] Error fetching statistics:', error);
    throw error;
  }
};

/**
 * Fetch unmatched payments with reasons why they didn't match
 *
 * @param sessionId - Upload session ID
 * @returns Promise resolving to array of unmatched payments
 *
 * @example
 * const unmatched = await getUnmatchedPayments('550e8400-e29b-41d4-a716-446655440000');
 * console.log('Found', unmatched.length, 'unmatched payments');
 * unmatched.forEach(p => console.log(p.unmatch_reason));
 */
export const getUnmatchedPayments = async (
  sessionId: string
): Promise<UnmatchedPayment[]> => {
  console.log('[matchingResultsService.getUnmatchedPayments] Fetching unmatched payments', {
    sessionId,
  });

  try {
    const response = await apiClient.get<{ unmatched_payments: UnmatchedPayment[] }>(
      `${BASE_PATH}/unmatched-payments`,
      { params: { session_id: sessionId } }
    );

    console.log('[matchingResultsService.getUnmatchedPayments] Fetched unmatched payments successfully', {
      count: response.data.unmatched_payments.length,
    });

    return response.data.unmatched_payments;
  } catch (error) {
    console.error('[matchingResultsService.getUnmatchedPayments] Error fetching unmatched payments:', error);
    throw error;
  }
};

/**
 * Fetch unmatched declarations with reasons why they weren't used
 *
 * @param sessionId - Upload session ID
 * @returns Promise resolving to array of unmatched declarations
 *
 * @example
 * const unmatched = await getUnmatchedDeclarations('550e8400-e29b-41d4-a716-446655440000');
 * console.log('Found', unmatched.length, 'unmatched declarations');
 */
export const getUnmatchedDeclarations = async (
  sessionId: string
): Promise<UnmatchedDeclaration[]> => {
  console.log('[matchingResultsService.getUnmatchedDeclarations] Fetching unmatched declarations', {
    sessionId,
  });

  try {
    const response = await apiClient.get<{ unmatched_declarations: UnmatchedDeclaration[] }>(
      `${BASE_PATH}/unmatched-declarations`,
      { params: { session_id: sessionId } }
    );

    console.log('[matchingResultsService.getUnmatchedDeclarations] Fetched unmatched declarations successfully', {
      count: response.data.unmatched_declarations.length,
    });

    return response.data.unmatched_declarations;
  } catch (error) {
    console.error('[matchingResultsService.getUnmatchedDeclarations] Error fetching unmatched declarations:', error);
    throw error;
  }
};

/**
 * Fetch detailed information for a single match
 *
 * @param matchId - Match record ID
 * @returns Promise resolving to match detail
 *
 * @example
 * const match = await getMatchDetail('550e8400-e29b-41d4-a716-446655440000');
 * console.log('Match confidence:', match.confidence_score);
 * console.log('Amount difference:', match.amount_difference);
 */
export const getMatchDetail = async (matchId: string): Promise<MatchDetail> => {
  console.log('[matchingResultsService.getMatchDetail] Fetching match detail', {
    matchId,
  });

  try {
    const response = await apiClient.get<MatchDetail>(
      `${BASE_PATH}/results/${matchId}`
    );

    console.log('[matchingResultsService.getMatchDetail] Fetched match detail successfully', {
      matchId: response.data.id,
      confidence_score: response.data.confidence_score,
      match_status: response.data.match_status,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.getMatchDetail] Error fetching match detail:', error);
    throw error;
  }
};

/**
 * Create a manual override to match a payment to a declaration
 *
 * @param sessionId - Upload session ID
 * @param overrideData - Manual override request data
 * @returns Promise resolving to created match detail
 *
 * @example
 * const match = await createManualOverride(
 *   '550e8400-e29b-41d4-a716-446655440000',
 *   {
 *     payment_date: '2024-10-15',
 *     declaration_number: '24  00001',
 *     override_reason: 'Manual match: Customer confirmed this payment matches declaration',
 *     override_type: 'tolerance_exception',
 *     confidence_override: 0.75
 *   }
 * );
 * console.log('Created manual match:', match.id);
 */
export const createManualOverride = async (
  sessionId: string,
  overrideData: ManualOverrideRequest
): Promise<MatchDetail> => {
  console.log('[matchingResultsService.createManualOverride] Creating manual override', {
    sessionId,
    payment_date: overrideData.payment_date,
    declaration_number: overrideData.declaration_number,
    override_type: overrideData.override_type,
  });

  try {
    const response = await apiClient.post<MatchDetail>(
      `${BASE_PATH}/manual-override`,
      {
        session_id: sessionId,
        ...overrideData,
      }
    );

    console.log('[matchingResultsService.createManualOverride] Created manual override successfully', {
      matchId: response.data.id,
      confidence_score: response.data.confidence_score,
      is_manual_override: response.data.is_manual_override,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.createManualOverride] Error creating manual override:', error);
    throw error;
  }
};

/**
 * Approve multiple matches in bulk
 *
 * @param matchIds - Array of match IDs to approve
 * @param reason - Optional reason for bulk approval
 * @returns Promise resolving to bulk action response
 *
 * @example
 * const result = await bulkApproveMatches(
 *   ['550e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440001'],
 *   'Bulk approval after manual review'
 * );
 * console.log('Approved', result.success_count, 'matches');
 */
export const bulkApproveMatches = async (
  matchIds: string[],
  reason?: string
): Promise<BulkActionResponse> => {
  console.log('[matchingResultsService.bulkApproveMatches] Approving matches in bulk', {
    count: matchIds.length,
    reason,
  });

  try {
    const request: BulkActionRequest = {
      match_ids: matchIds,
      action: 'approve',
      reason,
    };

    const response = await apiClient.post<BulkActionResponse>(
      `${BASE_PATH}/bulk-action`,
      request
    );

    console.log('[matchingResultsService.bulkApproveMatches] Bulk approval completed', {
      success_count: response.data.success_count,
      failure_count: response.data.failure_count,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.bulkApproveMatches] Error approving matches:', error);
    throw error;
  }
};

/**
 * Reject multiple matches in bulk
 *
 * @param matchIds - Array of match IDs to reject
 * @param reason - Optional reason for bulk rejection
 * @returns Promise resolving to bulk action response
 *
 * @example
 * const result = await bulkRejectMatches(
 *   ['550e8400-e29b-41d4-a716-446655440000'],
 *   'Incorrect matches - manual review required'
 * );
 * console.log('Rejected', result.success_count, 'matches');
 */
export const bulkRejectMatches = async (
  matchIds: string[],
  reason?: string
): Promise<BulkActionResponse> => {
  console.log('[matchingResultsService.bulkRejectMatches] Rejecting matches in bulk', {
    count: matchIds.length,
    reason,
  });

  try {
    const request: BulkActionRequest = {
      match_ids: matchIds,
      action: 'reject',
      reason,
    };

    const response = await apiClient.post<BulkActionResponse>(
      `${BASE_PATH}/bulk-action`,
      request
    );

    console.log('[matchingResultsService.bulkRejectMatches] Bulk rejection completed', {
      success_count: response.data.success_count,
      failure_count: response.data.failure_count,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.bulkRejectMatches] Error rejecting matches:', error);
    throw error;
  }
};

/**
 * Flag multiple matches for review in bulk
 *
 * @param matchIds - Array of match IDs to flag
 * @param reason - Optional reason for flagging
 * @returns Promise resolving to bulk action response
 *
 * @example
 * const result = await bulkFlagForReview(
 *   ['550e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440001'],
 *   'Low confidence scores - needs manual verification'
 * );
 * console.log('Flagged', result.success_count, 'matches for review');
 */
export const bulkFlagForReview = async (
  matchIds: string[],
  reason?: string
): Promise<BulkActionResponse> => {
  console.log('[matchingResultsService.bulkFlagForReview] Flagging matches for review in bulk', {
    count: matchIds.length,
    reason,
  });

  try {
    const request: BulkActionRequest = {
      match_ids: matchIds,
      action: 'flag_for_review',
      reason,
    };

    const response = await apiClient.post<BulkActionResponse>(
      `${BASE_PATH}/bulk-action`,
      request
    );

    console.log('[matchingResultsService.bulkFlagForReview] Bulk flagging completed', {
      success_count: response.data.success_count,
      failure_count: response.data.failure_count,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.bulkFlagForReview] Error flagging matches:', error);
    throw error;
  }
};

/**
 * Export match quality report to Excel
 *
 * @param sessionId - Upload session ID
 * @returns Promise resolving to Blob containing Excel file
 *
 * @example
 * const blob = await exportMatchQualityReport('550e8400-e29b-41d4-a716-446655440000');
 * const url = URL.createObjectURL(blob);
 * const link = document.createElement('a');
 * link.href = url;
 * link.download = 'match-quality-report.xlsx';
 * link.click();
 */
export const exportMatchQualityReport = async (sessionId: string): Promise<Blob> => {
  console.log('[matchingResultsService.exportMatchQualityReport] Exporting match quality report', {
    sessionId,
  });

  try {
    const response = await apiClient.get(
      `${BASE_PATH}/export-quality-report`,
      {
        params: { session_id: sessionId },
        responseType: 'blob',
      }
    );

    console.log('[matchingResultsService.exportMatchQualityReport] Export completed successfully', {
      size: response.data.size,
    });

    return response.data;
  } catch (error) {
    console.error('[matchingResultsService.exportMatchQualityReport] Error exporting report:', error);
    throw error;
  }
};
