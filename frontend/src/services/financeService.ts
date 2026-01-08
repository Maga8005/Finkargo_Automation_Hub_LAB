/**
 * Finance Service for Facturación MX automation.
 *
 * Provides API methods for Excel upload, invoice search,
 * and ZIP generation operations.
 */

import apiClient from '../api/clients/apiClient';
import type {
  ExcelValidationResponse,
  InvoiceSearchRequest,
  InvoiceSearchResponse,
  ZipGenerationRequest,
  SessionStats,
  CombinedUploadResponse,
  CombinedSearchRequest,
  CombinedSearchResponse,
  CombinedSessionStats,
} from '../types/finance';

const BASE_URL = '/finance';

/**
 * Finance service with all API methods for Facturación MX.
 */
export const financeService = {
  /**
   * Upload and validate an Excel file with invoice data.
   *
   * @param file - Excel file to upload (.xlsx or .xls)
   * @returns Validation response with parsed data and session ID
   * @throws Error if upload or validation fails
   */
  uploadExcel: async (file: File): Promise<ExcelValidationResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<ExcelValidationResponse>(
      `${BASE_URL}/upload-excel`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes timeout for large Excel files
      }
    );

    return response.data;
  },

  /**
   * Search for invoices in a session based on provided criteria.
   *
   * @param request - Search criteria including session ID and filters
   * @returns Search results with matching invoices
   * @throws Error if session not found or search fails
   */
  searchInvoices: async (request: InvoiceSearchRequest): Promise<InvoiceSearchResponse> => {
    const response = await apiClient.post<InvoiceSearchResponse>(
      `${BASE_URL}/search`,
      request
    );

    return response.data;
  },

  /**
   * Get statistics for a session.
   *
   * @param sessionId - Session ID from Excel upload
   * @returns Session statistics including totals and counts
   * @throws Error if session not found
   */
  getSessionStats: async (sessionId: string): Promise<SessionStats> => {
    const response = await apiClient.get<SessionStats>(
      `${BASE_URL}/session/${sessionId}/stats`
    );

    return response.data;
  },

  /**
   * Clear session data from server cache.
   *
   * @param sessionId - Session ID to clear
   * @returns Success message
   */
  clearSession: async (sessionId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(
      `${BASE_URL}/session/${sessionId}`
    );

    return response.data;
  },

  /**
   * Generate and download ZIP file with invoice documents.
   *
   * Note: This endpoint will be implemented in Sprint 3.
   *
   * @param request - ZIP generation request with UUIDs to include
   * @returns Blob containing the ZIP file
   * @throws Error if generation fails
   */
  generateZip: async (request: ZipGenerationRequest): Promise<Blob> => {
    const response = await apiClient.post(
      `${BASE_URL}/generate-zip`,
      request,
      {
        responseType: 'blob',
        timeout: 300000, // 5 minutes timeout for ZIP generation (downloads from Drive)
      }
    );

    return response.data;
  },

  // ==========================================================================
  // Combined Upload Methods (Facturas + Complementos de Pago)
  // ==========================================================================

  /**
   * Upload and validate both facturas and complementos de pago Excel files.
   *
   * @param facturasFile - Excel file with invoice data (optional)
   * @param complementosFile - Excel file with payment supplements (optional)
   * @returns Combined validation response with parsed data from both files
   * @throws Error if upload or validation fails
   */
  uploadCombinedExcel: async (
    facturasFile?: File,
    complementosFile?: File
  ): Promise<CombinedUploadResponse> => {
    const formData = new FormData();

    if (facturasFile) {
      formData.append('facturas_file', facturasFile);
    }
    if (complementosFile) {
      formData.append('complementos_file', complementosFile);
    }

    const response = await apiClient.post<CombinedUploadResponse>(
      `${BASE_URL}/mx/upload-combined`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 3 minutes timeout for processing 2 files
      }
    );

    return response.data;
  },

  /**
   * Search for records in combined session (facturas + complementos).
   *
   * @param request - Search criteria with session ID and filters
   * @returns Combined search results with matching records
   * @throws Error if session not found or search fails
   */
  searchCombined: async (request: CombinedSearchRequest): Promise<CombinedSearchResponse> => {
    const response = await apiClient.post<CombinedSearchResponse>(
      `${BASE_URL}/mx/search-combined`,
      request
    );

    return response.data;
  },

  /**
   * Get statistics for a combined session.
   *
   * @param sessionId - Session ID from combined upload
   * @returns Combined session statistics
   * @throws Error if session not found
   */
  getCombinedSessionStats: async (sessionId: string): Promise<CombinedSessionStats> => {
    const response = await apiClient.get<CombinedSessionStats>(
      `${BASE_URL}/mx/combined-session/${sessionId}/stats`
    );

    return response.data;
  },

  /**
   * Clear combined session data.
   *
   * @param sessionId - Combined session ID to clear
   * @returns Success message
   */
  clearCombinedSession: async (sessionId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(
      `${BASE_URL}/mx/combined-session/${sessionId}`
    );

    return response.data;
  },

  /**
   * Generate and download ZIP file with combined invoice and payment supplement documents.
   *
   * @param sessionId - Session ID from combined upload
   * @param searchCriteria - Optional search criteria to filter records
   * @param uuids - Optional comma-separated UUIDs to include
   * @returns Blob containing the ZIP file
   * @throws Error if generation fails
   */
  generateCombinedZip: async (
    sessionId: string,
    searchCriteria?: CombinedSearchRequest,
    uuids?: string
  ): Promise<Blob> => {
    const params = new URLSearchParams();
    params.append('session_id', sessionId);
    if (uuids) {
      params.append('uuids', uuids);
    }

    const response = await apiClient.post(
      `${BASE_URL}/mx/generate-combined-zip?${params.toString()}`,
      searchCriteria || null,
      {
        responseType: 'blob',
        timeout: 300000, // 5 minutes timeout for ZIP generation
      }
    );

    return response.data;
  },
};

export default financeService;
