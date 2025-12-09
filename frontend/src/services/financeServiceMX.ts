/**
 * Finance Service MX - Handles filter operations for Mexico invoicing.
 *
 * Provides API methods for querying the MX master Excel file stored in Google Drive
 * without needing an active session.
 */

import apiClient from '../api/clients/apiClient';

// ============================================================================
// Types
// ============================================================================

export interface MXFilterRequest {
  operaciones?: string[];
  rfc?: string;
  fecha_inicio?: string; // YYYY-MM-DD
  fecha_fin?: string; // YYYY-MM-DD
}

export interface MXFilteredRecord {
  uuid?: string;
  codigo_operacion?: string;
  conceptos?: string;
  fecha_emision?: string;
  rfc_receptor?: string;
  razon_receptor?: string;
  subtotal?: number;
  iva_trasladado?: number;
  iva_exento?: number;
  total?: number;
  uuid_relacionados?: string;
  tipo_comprobante?: string;
}

export interface MXFilterResponse {
  success: boolean;
  total_records: number;
  records: MXFilteredRecord[];
  filters_applied: Record<string, string>;
  total_amount: number;
  total_subtotal: number;
  total_iva: number;
  message: string;
}

export interface MXDistinctValuesResponse {
  success: boolean;
  field: string;
  values: string[];
  count: number;
}

// ============================================================================
// API Functions
// ============================================================================

const BASE_URL = '/finance';

/**
 * Filter MX master Excel records.
 *
 * @param request - Filter criteria
 * @returns Filtered records with totals
 */
export const filterMXRecords = async (
  request: MXFilterRequest
): Promise<MXFilterResponse> => {
  const response = await apiClient.post<MXFilterResponse>(
    `${BASE_URL}/mx/filter`,
    request,
    { timeout: 60000 } // 60 seconds for large files
  );
  return response.data;
};

/**
 * Get distinct values for a field (for autocomplete).
 *
 * @param field - Field name ('rfc', 'operacion')
 * @param limit - Maximum values to return
 * @returns Unique values for the field
 */
export const getMXDistinctValues = async (
  field: string,
  limit: number = 100
): Promise<MXDistinctValuesResponse> => {
  const response = await apiClient.get<MXDistinctValuesResponse>(
    `${BASE_URL}/mx/distinct/${field}`,
    { params: { limit } }
  );
  return response.data;
};

/**
 * Get operation codes for a specific RFC.
 *
 * @param rfc - RFC to filter by
 * @param limit - Maximum values to return
 * @returns Operation codes for the RFC
 */
export const getMXOperationsByRfc = async (
  rfc: string,
  limit: number = 100
): Promise<MXDistinctValuesResponse> => {
  const response = await apiClient.get<MXDistinctValuesResponse>(
    `${BASE_URL}/mx/operations-by-rfc/${encodeURIComponent(rfc)}`,
    { params: { limit } }
  );
  return response.data;
};

/**
 * Download filtered MX data as Excel.
 *
 * @param request - Filter criteria
 * @returns Excel file as Blob
 */
export const downloadFilteredMXData = async (
  request: MXFilterRequest
): Promise<Blob> => {
  const response = await apiClient.post(
    `${BASE_URL}/mx/filter/download`,
    request,
    {
      responseType: 'blob',
      timeout: 120000, // 2 minutes
    }
  );
  return response.data;
};

/**
 * Download filtered MX data with PDFs/XMLs as ZIP.
 *
 * @param request - Filter criteria
 * @returns ZIP file as Blob
 */
export const downloadFilteredMXZip = async (
  request: MXFilterRequest
): Promise<Blob> => {
  const response = await apiClient.post(
    `${BASE_URL}/mx/filter/download-zip`,
    request,
    {
      responseType: 'blob',
      timeout: 600000, // 10 minutes - Drive downloads can be slow
    }
  );
  return response.data;
};

/**
 * Clear MX filter cache.
 */
export const clearMXFilterCache = async (): Promise<{ message: string }> => {
  const response = await apiClient.delete<{ message: string }>(
    `${BASE_URL}/mx/filter/cache`
  );
  return response.data;
};

/**
 * Populate Drive file cache from master Excel.
 * This pre-caches file IDs to speed up ZIP generation.
 *
 * @returns Cache population statistics
 */
export interface PopulateCacheResponse {
  message: string;
  stats: {
    total: number;
    cached: number;
    not_found: number;
    already_cached: number;
  };
}

export const populateDriveCache = async (): Promise<PopulateCacheResponse> => {
  const response = await apiClient.post<PopulateCacheResponse>(
    `${BASE_URL}/populate-drive-cache`,
    {},
    { timeout: 600000 } // 10 minutes for large files
  );
  return response.data;
};

/**
 * Get Drive file cache statistics for MX.
 * Use this to check if the cache needs to be populated before generating ZIPs.
 *
 * @returns Cache statistics
 */
export interface CacheStatsResponse {
  success: boolean;
  country: string;
  total_cached: number;
  pdf_count: number;
  xml_count: number;
  cache_ready: boolean;
  message: string;
}

export const getDriveCacheStats = async (): Promise<CacheStatsResponse> => {
  const response = await apiClient.get<CacheStatsResponse>(
    `${BASE_URL}/mx/cache-stats`
  );
  return response.data;
};

/**
 * Trigger file download in browser.
 *
 * @param blob - File blob to download
 * @param filename - Name for the downloaded file
 */
export const triggerDownload = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
  window.URL.revokeObjectURL(url);
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Format currency for display.
 */
export const formatCurrency = (amount: number | undefined): string => {
  if (amount === undefined || amount === null) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
};

/**
 * Format date for display.
 */
export const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};
