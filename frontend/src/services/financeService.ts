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
};

export default financeService;
