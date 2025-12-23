/**
 * Risk Management Service - API calls for fraud detection and risk assessment
 */
import apiClient from '../api/clients/apiClient';
import type {
  RiskStats,
  RiskAssessment,
  RiskAssessmentDetail,
  RiskAssessmentRequest,
  RiskAssessmentFilter,
  RiskDecisionRequest,
  FraudDetectionRule,
  RuleUpdateRequest,
  BlacklistEntry,
  BlacklistEntryRequest,
  BlacklistFilter,
  RiskAlert,
  DocumentType,
  DocumentExtraction,
  DocumentExtractionList,
  DocumentUploadResponse,
  TriggerExtractionResponse,
  CrossValidationResponse,
} from '../types/risk';

export const riskService = {
  // ==================== Dashboard ====================

  /**
   * Get risk dashboard statistics
   */
  getDashboard: async (): Promise<RiskStats> => {
    const response = await apiClient.get<RiskStats>('/risk/dashboard');
    return response.data;
  },

  // ==================== Evaluations ====================

  /**
   * List risk evaluations with optional filters
   */
  getEvaluations: async (filters?: RiskAssessmentFilter): Promise<RiskAssessmentDetail[]> => {
    const params: Record<string, string | number | undefined> = {};

    if (filters) {
      if (filters.status) params.status = filters.status;
      if (filters.risk_level) params.risk_level = filters.risk_level;
      if (filters.client_nit) params.client_nit = filters.client_nit;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      if (filters.limit) params.limit = filters.limit;
      if (filters.offset) params.offset = filters.offset;
    }

    const response = await apiClient.get<RiskAssessmentDetail[]>('/risk/evaluations', { params });
    return response.data;
  },

  /**
   * Get a single evaluation by ID
   */
  getEvaluation: async (id: string): Promise<RiskAssessmentDetail> => {
    const response = await apiClient.get<RiskAssessmentDetail>(`/risk/evaluations/${id}`);
    return response.data;
  },

  /**
   * Create a new risk evaluation
   */
  createEvaluation: async (request: RiskAssessmentRequest): Promise<RiskAssessment> => {
    const response = await apiClient.post<RiskAssessment>('/risk/evaluate', request);
    return response.data;
  },

  /**
   * Submit a decision on an evaluation
   */
  submitDecision: async (id: string, decision: RiskDecisionRequest): Promise<RiskAssessmentDetail> => {
    const response = await apiClient.put<RiskAssessmentDetail>(
      `/risk/evaluations/${id}/decision`,
      decision
    );
    return response.data;
  },

  // ==================== Rules ====================

  /**
   * Get all fraud detection rules
   */
  getRules: async (): Promise<FraudDetectionRule[]> => {
    const response = await apiClient.get<FraudDetectionRule[]>('/risk/rules');
    return response.data;
  },

  /**
   * Update a fraud detection rule
   */
  updateRule: async (id: string, updates: RuleUpdateRequest): Promise<FraudDetectionRule> => {
    const response = await apiClient.put<FraudDetectionRule>(`/risk/rules/${id}`, updates);
    return response.data;
  },

  // ==================== Blacklist ====================

  /**
   * Get blacklist entries with optional filters
   */
  getBlacklist: async (filters?: BlacklistFilter): Promise<BlacklistEntry[]> => {
    const params: Record<string, string | number | boolean | undefined> = {};

    if (filters) {
      if (filters.entity_type) params.entity_type = filters.entity_type;
      if (filters.is_active !== undefined) params.is_active = filters.is_active;
      if (filters.limit) params.limit = filters.limit;
      if (filters.offset) params.offset = filters.offset;
    }

    const response = await apiClient.get<BlacklistEntry[]>('/risk/blacklist', { params });
    return response.data;
  },

  /**
   * Add entry to blacklist
   */
  addToBlacklist: async (entry: BlacklistEntryRequest): Promise<BlacklistEntry> => {
    const response = await apiClient.post<BlacklistEntry>('/risk/blacklist', entry);
    return response.data;
  },

  /**
   * Remove entry from blacklist
   */
  removeFromBlacklist: async (id: string): Promise<void> => {
    await apiClient.delete(`/risk/blacklist/${id}`);
  },

  // ==================== Alerts ====================

  /**
   * Get risk alerts
   */
  getAlerts: async (includeRead: boolean = false, limit: number = 20): Promise<RiskAlert[]> => {
    const response = await apiClient.get<RiskAlert[]>('/risk/alerts', {
      params: { include_read: includeRead, limit },
    });
    return response.data;
  },

  /**
   * Mark an alert as read
   */
  markAlertRead: async (id: string): Promise<void> => {
    await apiClient.put(`/risk/alerts/${id}/read`);
  },

  // ==================== Document Extraction ====================

  /**
   * Upload a document for extraction
   */
  uploadDocument: async (
    evaluationId: string,
    documentType: DocumentType,
    file: File
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('document_type', documentType);
    formData.append('file', file);

    const response = await apiClient.post<DocumentUploadResponse>(
      `/risk/evaluations/${evaluationId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Get all extractions for an evaluation
   */
  getExtractions: async (evaluationId: string): Promise<DocumentExtractionList> => {
    const response = await apiClient.get<DocumentExtractionList>(
      `/risk/evaluations/${evaluationId}/extractions`
    );
    return response.data;
  },

  /**
   * Trigger extraction for all pending documents
   */
  triggerExtraction: async (evaluationId: string): Promise<TriggerExtractionResponse> => {
    const response = await apiClient.post<TriggerExtractionResponse>(
      `/risk/evaluations/${evaluationId}/extract`
    );
    return response.data;
  },

  /**
   * Process single document extraction with file upload
   */
  processExtraction: async (
    evaluationId: string,
    extractionId: string,
    file: File
  ): Promise<DocumentExtraction> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DocumentExtraction>(
      `/risk/evaluations/${evaluationId}/extract-document/${extractionId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 3 minutes for AI extraction
      }
    );
    return response.data;
  },

  // ==================== Cross-Validation ====================

  /**
   * Run cross-validation on extracted documents
   */
  triggerCrossValidation: async (evaluationId: string): Promise<CrossValidationResponse> => {
    const response = await apiClient.post<CrossValidationResponse>(
      `/risk/evaluations/${evaluationId}/cross-validate`
    );
    return response.data;
  },

  /**
   * Get cross-validation results/discrepancies
   */
  getDiscrepancies: async (evaluationId: string): Promise<CrossValidationResponse> => {
    const response = await apiClient.get<CrossValidationResponse>(
      `/risk/evaluations/${evaluationId}/discrepancies`
    );
    return response.data;
  },
};
