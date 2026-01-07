/**
 * Treasury Matching Service for Declaration-Historial matching.
 *
 * Provides API methods for the Exchange Declaration to Historial de Pagos
 * matching workflow.
 */

import apiClient from '../api/clients/apiClient';
import type {
  HistorialUploadResponse,
  DeclarationInventoryUploadResponse,
  MatchConfig,
  MatchingSessionResponse,
  ManualOverrideRequest,
  ManualOverrideResponse,
  DeclarationItem,
  PaymentGroup,
} from '../types/treasuryMatching';

const BASE_URL = '/treasury/declarations/match';

/**
 * Treasury Matching service with all API methods.
 */
export const treasuryMatchingService = {
  /**
   * Upload and parse a Historial de Pagos Excel file.
   *
   * @param file - Excel file to upload (.xlsx)
   * @returns Upload response with parsed groups and validation status
   */
  uploadHistorial: async (file: File): Promise<HistorialUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<HistorialUploadResponse>(
      `${BASE_URL}/upload-historial`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes timeout for large files
      }
    );

    return response.data;
  },

  /**
   * Upload declaration inventory Excel file.
   *
   * @param sessionId - Session ID from historial upload
   * @param file - Declaration inventory Excel file (.xlsx)
   * @returns Upload response with parsed declarations
   */
  uploadDeclarations: async (
    sessionId: string,
    file: File
  ): Promise<DeclarationInventoryUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DeclarationInventoryUploadResponse>(
      `${BASE_URL}/upload-declarations?session_id=${sessionId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000,
      }
    );

    return response.data;
  },

  /**
   * Execute the matching algorithm.
   *
   * @param sessionId - Session ID
   * @param config - Matching configuration
   * @returns Matching results with statistics
   */
  executeMatching: async (
    sessionId: string,
    config: MatchConfig
  ): Promise<MatchingSessionResponse> => {
    const response = await apiClient.post<MatchingSessionResponse>(
      `${BASE_URL}/execute?session_id=${sessionId}`,
      config,
      {
        timeout: 300000, // 5 minutes for matching
      }
    );

    return response.data;
  },

  /**
   * Get cached matching results for a session.
   *
   * @param sessionId - Session ID
   * @returns Cached matching results
   */
  getResults: async (sessionId: string): Promise<MatchingSessionResponse> => {
    const response = await apiClient.get<MatchingSessionResponse>(
      `${BASE_URL}/results/${sessionId}`
    );

    return response.data;
  },

  /**
   * Manually override a match result.
   *
   * @param request - Override request with group and declaration IDs
   * @returns Override response with updated result
   */
  overrideMatch: async (
    request: ManualOverrideRequest
  ): Promise<ManualOverrideResponse> => {
    const response = await apiClient.post<ManualOverrideResponse>(
      `${BASE_URL}/override`,
      request
    );

    return response.data;
  },

  /**
   * Download the enriched Excel file.
   *
   * @param sessionId - Session ID
   * @returns Blob with Excel file
   */
  downloadEnrichedExcel: async (sessionId: string): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_URL}/download/${sessionId}`, {
      responseType: 'blob',
      timeout: 120000,
    });

    return response.data;
  },

  /**
   * Get available declarations for a session.
   *
   * @param sessionId - Session ID
   * @returns List of declarations
   */
  getDeclarations: async (sessionId: string): Promise<DeclarationItem[]> => {
    const response = await apiClient.get<DeclarationItem[]>(
      `${BASE_URL}/declarations/${sessionId}`
    );

    return response.data;
  },

  /**
   * Get payment groups for a session.
   *
   * @param sessionId - Session ID
   * @returns List of payment groups
   */
  getPaymentGroups: async (sessionId: string): Promise<PaymentGroup[]> => {
    const response = await apiClient.get<PaymentGroup[]>(
      `${BASE_URL}/payment-groups/${sessionId}`
    );

    return response.data;
  },

  /**
   * Trigger download of a blob as a file.
   *
   * @param blob - File blob to download
   * @param filename - Name for the downloaded file
   */
  downloadBlob: (blob: Blob, filename: string): void => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

export default treasuryMatchingService;
