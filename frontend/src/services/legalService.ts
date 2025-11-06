/**
 * Legal Contract Service - API calls for legal contract automation
 */
import apiClient from '../api/clients/apiClient';
import type {
  Client,
  ContractGeneration,
  ContractGenerationRequest,
  ContractReviewRequest,
  ClientSearchParams,
} from '../types/legal';

export const legalService = {
  // ==================== Client Operations ====================

  /**
   * Search clients
   */
  searchClients: async (params: ClientSearchParams): Promise<Client[]> => {
    const response = await apiClient.get<Client[]>('/legal/clients/search', { params });
    return response.data;
  },

  /**
   * Get client by NIT
   */
  getClientByNit: async (nit: string): Promise<Client> => {
    const response = await apiClient.get<Client>(`/legal/clients/${nit}`);
    return response.data;
  },

  /**
   * Create new client
   */
  createClient: async (clientData: Partial<Client>): Promise<Client> => {
    const response = await apiClient.post<Client>('/legal/clients', clientData);
    return response.data;
  },

  /**
   * Update client
   */
  updateClient: async (clientId: string, clientData: Partial<Client>): Promise<Client> => {
    const response = await apiClient.put<Client>(`/legal/clients/${clientId}`, clientData);
    return response.data;
  },

  /**
   * Import clients from CSV/Excel
   */
  importClients: async (file: File): Promise<{ total_processed: number; successful: number; failed: number; errors: string[] }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/legal/clients/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // ==================== Contract Operations ====================

  /**
   * Generate new contract
   */
  generateContract: async (request: ContractGenerationRequest): Promise<ContractGeneration> => {
    const response = await apiClient.post<ContractGeneration>('/legal/contracts/generate', request);
    return response.data;
  },

  /**
   * Get contract details
   */
  getContract: async (contractId: string): Promise<ContractGeneration> => {
    const response = await apiClient.get<ContractGeneration>(`/legal/contracts/${contractId}`);
    return response.data;
  },

  /**
   * Review contract (approve/reject)
   */
  reviewContract: async (contractId: string, review: ContractReviewRequest): Promise<ContractGeneration> => {
    const response = await apiClient.post<ContractGeneration>(
      `/legal/contracts/${contractId}/review`,
      review
    );
    return response.data;
  },

  /**
   * Get contracts pending review
   */
  getPendingReviews: async (contractType?: string): Promise<ContractGeneration[]> => {
    const params = contractType ? { contract_type: contractType } : {};
    const response = await apiClient.get<ContractGeneration[]>('/legal/contracts/pending-review', { params });
    return response.data;
  },

  /**
   * Get Otrosí contracts pending review
   */
  getPendingOtrosiReviews: async (): Promise<ContractGeneration[]> => {
    return legalService.getPendingReviews('otrosi');
  },

  /**
   * Get approved contracts for Operations
   */
  getApprovedContracts: async (): Promise<ContractGeneration[]> => {
    const response = await apiClient.get<ContractGeneration[]>('/legal/contracts/approved');
    return response.data;
  },

  /**
   * Get contract history with filters
   */
  getContractHistory: async (filters?: {
    status?: string;
    client_nit?: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
    offset?: number;
  }): Promise<ContractGeneration[]> => {
    const response = await apiClient.get<ContractGeneration[]>('/legal/contracts', { params: filters });
    return response.data;
  },

  /**
   * Get contract statistics
   */
  getContractStats: async (): Promise<{
    total_generated: number;
    pending_review: number;
    approved: number;
    rejected: number;
    generated_today: number;
    generated_this_week: number;
    generated_this_month: number;
  }> => {
    const response = await apiClient.get('/legal/contracts/stats');
    return response.data;
  },

  /**
   * Preview contract content
   */
  previewContract: async (contractId: string): Promise<{ content: string }> => {
    const response = await apiClient.get<{ content: string }>(`/legal/contracts/${contractId}/preview`);
    return response.data;
  },

  /**
   * Download contract as DOCX
   */
  downloadContractDOCX: async (contractId: string): Promise<Blob> => {
    const response = await apiClient.get(`/legal/contracts/${contractId}/download/docx`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Download contract as PDF
   */
  downloadContractPDF: async (contractId: string): Promise<Blob> => {
    const response = await apiClient.get(`/legal/contracts/${contractId}/download/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // ==================== Template Operations ====================

  /**
   * Get active contract template
   */
  getActiveTemplate: async (): Promise<{ id: string; version: string; template_content: string }> => {
    const response = await apiClient.get('/legal/templates/active');
    return response.data;
  },
};
