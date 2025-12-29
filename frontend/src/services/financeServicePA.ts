/**
 * Finance Service for PA (Patrimonio Autónomo) Classification
 *
 * Service for handling PA report classification and rule management.
 */

import apiClient from '../api/clients/apiClient';
import type {
  PARulesSummary,
  PAAccountCatalogResponse,
  PAAccountCatalogUploadResponse,
  PAClassificationRulesResponse,
  PAClassificationRulesUploadResponse,
  PAClasificacionCuentaRulesResponse,
  PAClasificacionCuentaRulesUploadResponse,
  PANexoRulesResponse,
  PANexoRulesUploadResponse,
  PAUploadResponse,
  PACleanedPreview,
  PAClassifiedPreview,
  PAProcessingHistoryResponse,
  PAProcessingHistoryFilter,
  PAProcessingStats,
} from '../types/financePA';

const PA_API_BASE = '/finance/pa';

// =============================================================================
// Rules Summary
// =============================================================================

/**
 * Get summary of all loaded PA classification rules
 */
export const getRulesSummary = async (): Promise<PARulesSummary> => {
  const response = await apiClient.get<PARulesSummary>(`${PA_API_BASE}/rules/summary`);
  return response.data;
};

// =============================================================================
// Account Catalog
// =============================================================================

/**
 * Upload PA account catalog Excel file
 */
export const uploadAccountCatalog = async (
  file: File,
  replaceExisting: boolean = true
): Promise<PAAccountCatalogUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<PAAccountCatalogUploadResponse>(
    `${PA_API_BASE}/rules/catalog/upload`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { replace_existing: replaceExisting },
    }
  );
  return response.data;
};

/**
 * Get PA account catalog entries
 */
export const getAccountCatalog = async (
  limit: number = 100,
  offset: number = 0
): Promise<PAAccountCatalogResponse> => {
  const response = await apiClient.get<PAAccountCatalogResponse>(
    `${PA_API_BASE}/rules/catalog`,
    { params: { limit, offset } }
  );
  return response.data;
};

// =============================================================================
// Classification Rules
// =============================================================================

/**
 * Upload PA classification rules Excel file
 */
export const uploadClassificationRules = async (
  file: File,
  replaceExisting: boolean = true
): Promise<PAClassificationRulesUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<PAClassificationRulesUploadResponse>(
    `${PA_API_BASE}/rules/classification/upload`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { replace_existing: replaceExisting },
    }
  );
  return response.data;
};

/**
 * Get PA classification rules
 */
export const getClassificationRules = async (
  activeOnly: boolean = true
): Promise<PAClassificationRulesResponse> => {
  const response = await apiClient.get<PAClassificationRulesResponse>(
    `${PA_API_BASE}/rules/classification`,
    { params: { active_only: activeOnly } }
  );
  return response.data;
};

// =============================================================================
// Clasificación Cuenta Rules
// =============================================================================

/**
 * Upload clasificación cuenta rules Excel file
 */
export const uploadClasificacionCuentaRules = async (
  file: File,
  replaceExisting: boolean = true
): Promise<PAClasificacionCuentaRulesUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<PAClasificacionCuentaRulesUploadResponse>(
    `${PA_API_BASE}/rules/clasificacion-cuenta/upload`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { replace_existing: replaceExisting },
    }
  );
  return response.data;
};

/**
 * Get clasificación cuenta rules
 */
export const getClasificacionCuentaRules = async (
  activeOnly: boolean = true
): Promise<PAClasificacionCuentaRulesResponse> => {
  const response = await apiClient.get<PAClasificacionCuentaRulesResponse>(
    `${PA_API_BASE}/rules/clasificacion-cuenta`,
    { params: { active_only: activeOnly } }
  );
  return response.data;
};

// =============================================================================
// Nexo Rules
// =============================================================================

/**
 * Upload nexo rules Excel file
 */
export const uploadNexoRules = async (
  file: File,
  replaceExisting: boolean = true
): Promise<PANexoRulesUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<PANexoRulesUploadResponse>(
    `${PA_API_BASE}/rules/nexo/upload`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { replace_existing: replaceExisting },
    }
  );
  return response.data;
};

/**
 * Get nexo rules
 */
export const getNexoRules = async (
  activeOnly: boolean = true
): Promise<PANexoRulesResponse> => {
  const response = await apiClient.get<PANexoRulesResponse>(
    `${PA_API_BASE}/rules/nexo`,
    { params: { active_only: activeOnly } }
  );
  return response.data;
};

// =============================================================================
// Report Processing
// =============================================================================

/**
 * Upload NetSuite movements file
 */
export const uploadNetSuiteFile = async (file: File): Promise<PAUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<PAUploadResponse>(
    `${PA_API_BASE}/process/upload`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 minute timeout for large files
    }
  );
  return response.data;
};

/**
 * Step 1: Clean and prepare PA data
 */
export const cleanData = async (sessionId: string): Promise<PACleanedPreview> => {
  const response = await apiClient.post<PACleanedPreview>(
    `${PA_API_BASE}/process/${sessionId}/clean`
  );
  return response.data;
};

/**
 * Download cleaned Excel file
 */
export const downloadCleanedFile = async (sessionId: string): Promise<Blob> => {
  const response = await apiClient.get(
    `${PA_API_BASE}/process/${sessionId}/clean/download`,
    { responseType: 'blob' }
  );
  return response.data;
};

/**
 * Step 2: Apply classification rules
 */
export const classifyData = async (sessionId: string): Promise<PAClassifiedPreview> => {
  const response = await apiClient.post<PAClassifiedPreview>(
    `${PA_API_BASE}/process/${sessionId}/classify`
  );
  return response.data;
};

/**
 * Download classified Excel file
 */
export const downloadClassifiedFile = async (sessionId: string): Promise<Blob> => {
  const response = await apiClient.get(
    `${PA_API_BASE}/process/${sessionId}/classify/download`,
    { responseType: 'blob' }
  );
  return response.data;
};

/**
 * Get processing session statistics
 */
export const getSessionStats = async (sessionId: string): Promise<PAProcessingStats> => {
  const response = await apiClient.get<PAProcessingStats>(
    `${PA_API_BASE}/process/${sessionId}/stats`
  );
  return response.data;
};

// =============================================================================
// Processing History
// =============================================================================

/**
 * Get processing history with filters
 */
export const getProcessingHistory = async (
  filters: PAProcessingHistoryFilter = {}
): Promise<PAProcessingHistoryResponse> => {
  const response = await apiClient.get<PAProcessingHistoryResponse>(
    `${PA_API_BASE}/history`,
    { params: filters }
  );
  return response.data;
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Download file helper - triggers browser download
 */
export const triggerDownload = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
