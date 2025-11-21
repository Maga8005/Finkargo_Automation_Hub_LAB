/**
 * TypeScript Type Definitions for Declaration-Payment Matching Results Dashboard
 *
 * These types define the data structures used in the matching results dashboard,
 * aligned with backend DTOs from declaraciones_normalization_dtos.py
 */

/**
 * Individual match between a payment and a declaration
 *
 * @example
 * {
 *   id: "550e8400-e29b-41d4-a716-446655440000",
 *   session_id: "660e8400-e29b-41d4-a716-446655440001",
 *   payment_date: "2024-10-15",
 *   declaration_number: "24  00001",
 *   amount_payment: 201387.11,
 *   amount_declaration: 201387.11,
 *   amount_difference: 0.0,
 *   date_difference_days: 1,
 *   customer_name_payment: "BICICLETAS STRONGMAN",
 *   customer_name_declaration: "BICICLETAS STRONGMAN",
 *   customer_name_similarity: 1.0,
 *   confidence_score: 1.0,
 *   match_status: "approved",
 *   is_manual_override: false,
 *   override_reason: null,
 *   created_at: "2024-11-05T10:30:00Z"
 * }
 */
export interface MatchDetail {
  id: string;
  session_id: string;
  payment_date: string;
  declaration_number: string;
  amount_payment: number;
  amount_declaration: number;
  amount_difference: number;
  date_difference_days: number;
  customer_name_payment: string;
  customer_name_declaration: string;
  customer_name_similarity: number;
  confidence_score: number;
  match_status: 'approved' | 'pending_review' | 'rejected';
  is_manual_override: boolean;
  override_reason: string | null;
  override_type?: 'exact_match' | 'tolerance_exception' | 'customer_name_correction';
  created_at: string;
  updated_at?: string;
  created_by?: string;
}

/**
 * Aggregate statistics for matching results
 *
 * @example
 * {
 *   total_payments: 54,
 *   matched_payments: 37,
 *   unmatched_payments: 17,
 *   match_percentage: 68.5,
 *   total_declarations: 20,
 *   declarations_used: 20,
 *   declarations_unused: 0,
 *   declaration_usage_percentage: 100.0,
 *   average_confidence_score: 0.95,
 *   perfect_matches_count: 30,
 *   good_matches_count: 7,
 *   possible_matches_count: 0
 * }
 */
export interface MatchingResultsStatistics {
  total_payments: number;
  matched_payments: number;
  unmatched_payments: number;
  match_percentage: number;
  total_declarations: number;
  declarations_used: number;
  declarations_unused: number;
  declaration_usage_percentage: number;
  average_confidence_score: number;
  perfect_matches_count: number;  // 0.95-1.0
  good_matches_count: number;      // 0.70-0.94
  possible_matches_count: number;  // 0.50-0.69
}

/**
 * Payment record that didn't match any declaration
 *
 * @example
 * {
 *   payment_date: "2024-10-20",
 *   amount: 5000.00,
 *   customer_name: "ACME CORPORATION",
 *   customer_name_normalized: "ACME CORPORATION",
 *   unmatch_reason: "Amount outside tolerance - closest: $250 difference",
 *   unmatch_reason_type: "amount_mismatch",
 *   closest_declaration_number: "24  00005",
 *   closest_amount_difference: 250.00
 * }
 */
export interface UnmatchedPayment {
  payment_date: string;
  amount: number;
  customer_name: string;
  customer_name_normalized: string;
  unmatch_reason: string;
  unmatch_reason_type: 'amount_mismatch' | 'date_mismatch' | 'customer_name_mismatch' | 'no_candidates';
  closest_declaration_number?: string;
  closest_amount_difference?: number;
  closest_date_difference_days?: number;
  closest_customer_similarity?: number;
}

/**
 * Declaration record that wasn't assigned to any payment
 *
 * @example
 * {
 *   declaration_number: "24  00099",
 *   declaration_date: "2024-09-01",
 *   amount: 15000.00,
 *   customer_name: "OLD CUSTOMER INC",
 *   customer_name_normalized: "OLD CUSTOMER INC",
 *   unmatch_reason: "No payments found within date range",
 *   unmatch_reason_type: "no_candidates"
 * }
 */
export interface UnmatchedDeclaration {
  declaration_number: string;
  declaration_date: string;
  amount: number;
  customer_name: string;
  customer_name_normalized: string;
  unmatch_reason: string;
  unmatch_reason_type: 'amount_mismatch' | 'date_mismatch' | 'customer_name_mismatch' | 'no_candidates';
  closest_payment_date?: string;
  closest_amount_difference?: number;
  closest_date_difference_days?: number;
  closest_customer_similarity?: number;
}

/**
 * Match quality assessment metrics
 *
 * @example
 * {
 *   overall_quality_score: 92.5,
 *   perfect_matches_ratio: 0.81,
 *   amount_tolerance_usage: {
 *     within_perfect: 30,
 *     within_tolerance: 7,
 *     outside_tolerance: 0
 *   },
 *   date_tolerance_usage: {
 *     same_day: 10,
 *     within_3_days: 20,
 *     within_7_days: 7
 *   },
 *   customer_normalization_effectiveness: 0.85,
 *   data_quality_issues: ["5 matches have low confidence - review manually"],
 *   recommendations: ["Review 7 matches with date differences > 3 days"]
 * }
 */
export interface MatchQualityMetrics {
  overall_quality_score: number;
  perfect_matches_ratio: number;
  amount_tolerance_usage: {
    within_perfect: number;
    within_tolerance: number;
    outside_tolerance: number;
  };
  date_tolerance_usage: {
    same_day: number;
    within_3_days: number;
    within_7_days: number;
  };
  customer_normalization_effectiveness: number;
  data_quality_issues: string[];
  recommendations: string[];
}

/**
 * Request to manually override/create a match
 *
 * @example
 * {
 *   payment_date: "2024-10-15",
 *   declaration_number: "24  00001",
 *   override_reason: "Manual match: Customer confirmed this payment matches declaration",
 *   override_type: "tolerance_exception",
 *   confidence_override: 0.75
 * }
 */
export interface ManualOverrideRequest {
  payment_date: string;
  declaration_number: string;
  override_reason: string;
  override_type: 'exact_match' | 'tolerance_exception' | 'customer_name_correction';
  confidence_override: number;
}

/**
 * Request for bulk operations on multiple matches
 *
 * @example
 * {
 *   match_ids: ["550e8400-e29b-41d4-a716-446655440000", "660e8400-e29b-41d4-a716-446655440001"],
 *   action: "approve",
 *   reason: "Bulk approval after manual review"
 * }
 */
export interface BulkActionRequest {
  match_ids: string[];
  action: 'approve' | 'reject' | 'flag_for_review';
  reason?: string;
}

/**
 * Confidence score distribution buckets
 *
 * @example
 * {
 *   perfect: { count: 30, percentage: 81.1, range: "0.95-1.0" },
 *   good: { count: 7, percentage: 18.9, range: "0.70-0.94" },
 *   possible: { count: 0, percentage: 0.0, range: "0.50-0.69" }
 * }
 */
export interface ConfidenceDistribution {
  perfect: {
    count: number;
    percentage: number;
    range: string;
  };
  good: {
    count: number;
    percentage: number;
    range: string;
  };
  possible: {
    count: number;
    percentage: number;
    range: string;
  };
}

/**
 * Filters for matching results queries
 *
 * @example
 * {
 *   confidence_min: 0.70,
 *   confidence_max: 1.0,
 *   date_from: "2024-10-01",
 *   date_to: "2024-10-31",
 *   match_status: "approved",
 *   amount_difference_max: 0.20
 * }
 */
export interface MatchingResultsFilters {
  confidence_min?: number;
  confidence_max?: number;
  date_from?: string;
  date_to?: string;
  match_status?: 'approved' | 'pending_review' | 'rejected' | 'all';
  amount_difference_max?: number;
  is_manual_override?: boolean;
}

/**
 * Pagination parameters for matching results queries
 *
 * @example
 * {
 *   page: 1,
 *   page_size: 25,
 *   sort_by: "confidence_score",
 *   sort_order: "desc"
 * }
 */
export interface MatchingResultsPagination {
  page: number;
  page_size: number;
  sort_by?: 'confidence_score' | 'amount_difference' | 'date_difference_days' | 'payment_date';
  sort_order?: 'asc' | 'desc';
}

/**
 * Paginated response for matching results
 *
 * @example
 * {
 *   matches: [...],
 *   total_count: 37,
 *   page: 1,
 *   page_size: 25,
 *   total_pages: 2
 * }
 */
export interface MatchingResultsResponse {
  matches: MatchDetail[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Response from bulk operations
 *
 * @example
 * {
 *   success_count: 5,
 *   failure_count: 0,
 *   updated_matches: [...],
 *   errors: []
 * }
 */
export interface BulkActionResponse {
  success_count: number;
  failure_count: number;
  updated_matches: MatchDetail[];
  errors: Array<{
    match_id: string;
    error_message: string;
  }>;
}

/**
 * Complete matching results summary for dashboard
 *
 * @example
 * {
 *   statistics: {...},
 *   confidence_distribution: {...},
 *   quality_metrics: {...}
 * }
 */
export interface MatchingResultsSummary {
  statistics: MatchingResultsStatistics;
  confidence_distribution: ConfidenceDistribution;
  quality_metrics: MatchQualityMetrics;
}
