/**
 * Operations Service - API calls for Operations department
 */
import apiClient from '../api/clients/apiClient';
import type {
  ContractGenerationRequest,
  ContractGeneration,
} from '../types/legal';

const BASE_URL = '/operations';

export const operationsService = {
  /**
   * Request contract generation (Operations initiates)
   */
  async requestContractGeneration(
    request: ContractGenerationRequest
  ): Promise<ContractGeneration> {
    const response = await apiClient.post<ContractGeneration>(
      `${BASE_URL}/contracts/generate`,
      request
    );
    return response.data;
  },

  /**
   * Get all approved contracts
   */
  async getApprovedContracts(): Promise<ContractGeneration[]> {
    const response = await apiClient.get<ContractGeneration[]>(
      `${BASE_URL}/contracts/approved`
    );
    return response.data;
  },

  /**
   * Get contract details by ID
   */
  async getContractDetails(contractId: string): Promise<ContractGeneration> {
    const response = await apiClient.get<ContractGeneration>(
      `${BASE_URL}/contracts/${contractId}`
    );
    return response.data;
  },

  /**
   * Download approved contract PDF
   */
  async downloadApprovedContractPdf(contractId: string): Promise<Blob> {
    const response = await apiClient.get(
      `${BASE_URL}/contracts/${contractId}/download/pdf`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },
};
