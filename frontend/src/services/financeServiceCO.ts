/**
 * Finance Service for Colombia (CO) Operations
 *
 * Service for handling Colombia invoicing file uploads and processing.
 */

import apiClient from '../api/clients/apiClient';

export interface COFileSet {
  netsuite?: File;
  netsuite_nc?: File;
  noova_facturas?: File;
  noova_nc?: File;
}

export interface COProcessingStats {
  total_records_noova: number;
  total_records_netsuite: number;
  total_consolidated: number;
  matched_with_netsuite: number;
  unmatched_noova: number;
  costos_fijos_count: number;
  mandato_count: number;
  errors: string[];
}

export interface COReportSheet {
  sheet_name: string;
  column_count: number;
  row_count: number;
  columns: string[];
}

export interface COProcessingResponse {
  success: boolean;
  session_id: string;
  stats: COProcessingStats;
  sheets: COReportSheet[];
  download_url: string;
  drive_uploaded: boolean;
  drive_url: string | null;
  message: string;
}

/**
 * Upload and process Colombia Excel files (by pairs)
 *
 * @param files - Object containing uploaded files (at least one pair required)
 * @returns Processing result with statistics and download URL
 */
export const processCOFiles = async (
  files: COFileSet
): Promise<COProcessingResponse> => {
  // Create FormData with only uploaded files
  const formData = new FormData();

  if (files.netsuite) {
    formData.append('netsuite', files.netsuite);
  }
  if (files.netsuite_nc) {
    formData.append('netsuite_nc', files.netsuite_nc);
  }
  if (files.noova_facturas) {
    formData.append('noova_facturas', files.noova_facturas);
  }
  if (files.noova_nc) {
    formData.append('noova_nc', files.noova_nc);
  }

  const response = await apiClient.post<COProcessingResponse>(
    '/finance/co/process-files',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Allow longer timeout for file processing (5 minutes)
      timeout: 300000,
    }
  );

  return response.data;
};

/**
 * Download generated CO Excel report
 *
 * @param sessionId - Session ID from processing response
 * @returns Blob containing Excel file
 */
export const downloadCOReport = async (sessionId: string): Promise<Blob> => {
  const response = await apiClient.get(`/finance/co/download/${sessionId}`, {
    responseType: 'blob',
  });

  return response.data;
};

/**
 * Clear CO session data from server
 *
 * @param sessionId - Session ID to clear
 */
export const clearCOSession = async (sessionId: string): Promise<void> => {
  await apiClient.delete(`/finance/co/session/${sessionId}`);
};

/**
 * Helper function to trigger download in browser
 *
 * @param blob - File blob to download
 * @param filename - Suggested filename
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


// ============================================================================
// Filter Types and Services
// ============================================================================

export interface COFilterRequest {
  operaciones?: string[];
  nit?: string;
  fecha_inicio?: string; // YYYY-MM-DD
  fecha_fin?: string; // YYYY-MM-DD
  hoja?: 'costos_fijos' | 'mandato';
}

export interface COFilteredRecord {
  codigo_operacion?: string;
  fecha?: string;
  numero_factura?: string;
  nit?: string;
  moneda?: string;
  valor_costos_fijos?: number;
  seguro_iva?: number;
  int_corriente?: number;
  int_mora?: number;
  retencion_fuente?: number;
  valor_neto?: number;
  otros_valor?: number;
  hoja_origen?: string;
}

export interface COFilterResponse {
  success: boolean;
  total_records: number;
  records: COFilteredRecord[];
  filters_applied: Record<string, string>;
  sheets_searched: string[];
  message: string;
}

export interface CODistinctValuesResponse {
  success: boolean;
  field: string;
  values: string[];
  count: number;
}

/**
 * Filter CO master Excel data from Google Drive
 *
 * @param filters - Filter criteria (operaciones, nit, fecha_inicio, fecha_fin)
 * @returns Filtered records from master Excel
 */
export const filterCORecords = async (
  filters: COFilterRequest
): Promise<COFilterResponse> => {
  const response = await apiClient.post<COFilterResponse>(
    '/finance/co/filter',
    filters
  );
  return response.data;
};

/**
 * Get distinct values for a field (for autocomplete)
 *
 * @param field - Field name ('nit', 'operacion')
 * @param limit - Maximum values to return
 * @returns Unique values found
 */
export const getCODistinctValues = async (
  field: 'nit' | 'operacion',
  limit: number = 100
): Promise<CODistinctValuesResponse> => {
  const response = await apiClient.get<CODistinctValuesResponse>(
    `/finance/co/distinct/${field}`,
    { params: { limit } }
  );
  return response.data;
};

/**
 * Download filtered CO data as Excel file
 *
 * @param filters - Filter criteria
 * @returns Blob containing Excel file
 */
export const downloadFilteredCOData = async (
  filters: COFilterRequest
): Promise<Blob> => {
  const response = await apiClient.post(
    '/finance/co/filter/download',
    filters,
    { responseType: 'blob' }
  );
  return response.data;
};

/**
 * Get operations for a specific NIT
 *
 * @param nit - Client NIT to filter by
 * @param limit - Maximum values to return
 * @returns Unique operation codes associated with the NIT
 */
export const getCOOperationsByNit = async (
  nit: string,
  limit: number = 100
): Promise<CODistinctValuesResponse> => {
  const response = await apiClient.get<CODistinctValuesResponse>(
    `/finance/co/operations-by-nit/${encodeURIComponent(nit)}`,
    { params: { limit } }
  );
  return response.data;
};

/**
 * Clear the filter cache to force fresh data from Drive
 */
export const clearCOFilterCache = async (): Promise<void> => {
  await apiClient.delete('/finance/co/filter/cache');
};

/**
 * Download filtered CO data with PDFs as ZIP package
 *
 * This will:
 * - Apply the same filters as filterCORecords
 * - Search for PDFs in Google Drive for each invoice
 * - Generate a ZIP with Excel report + PDFs folder
 *
 * @param filters - Filter criteria
 * @returns Blob containing ZIP file
 */
export const downloadFilteredCOZip = async (
  filters: COFilterRequest
): Promise<Blob> => {
  const response = await apiClient.post(
    '/finance/co/filter/download-zip',
    filters,
    {
      responseType: 'blob',
      // Allow longer timeout for PDF search and download (30 minutes for large ZIPs)
      timeout: 1800000,
    }
  );
  return response.data;
};

// ============================================================================
// Cache Optimization Functions
// ============================================================================

export interface PrecacheStats {
  total: number;
  cached: number;
  not_found: number;
  already_cached: number;
}

export interface PrecacheResponse {
  success: boolean;
  message: string;
  stats: PrecacheStats;
}

/**
 * Pre-populate the Drive file cache for CO invoices.
 *
 * This dramatically speeds up ZIP downloads by:
 * 1. Listing all PDF files from Drive in one API call
 * 2. Matching invoice numbers in memory
 * 3. Storing file IDs in Supabase cache
 *
 * Recommended to run once before downloading large ZIPs.
 *
 * @returns Precache response with statistics
 */
export const precacheDriveFilesCO = async (): Promise<PrecacheResponse> => {
  const response = await apiClient.post<PrecacheResponse>(
    '/finance/co/precache-drive-files',
    {},
    {
      // Allow longer timeout for precache operation (10 minutes)
      timeout: 600000,
    }
  );
  return response.data;
};

export interface InitializeFromHistoricalStats {
  historical_invoices: number;
  total: number;
  cached: number;
  not_found: number;
  already_cached: number;
}

export interface InitializeFromHistoricalResponse {
  success: boolean;
  message: string;
  stats: InitializeFromHistoricalStats;
}

/**
 * ONE-TIME initialization from historical invoice control file.
 *
 * Reads "Archivo control facturacion mensual Finkargo Def.xlsx" to:
 * 1. Extract ALL invoice numbers from historical record (3 sheets)
 * 2. Pre-populate Supabase cache with Drive file IDs
 *
 * This allows using the system immediately without uploading Noova/Netsuite files.
 *
 * @returns Initialization response with statistics
 */
export const initializeFromHistoricalCO = async (): Promise<InitializeFromHistoricalResponse> => {
  const response = await apiClient.post<InitializeFromHistoricalResponse>(
    '/finance/co/initialize-from-historical',
    {},
    {
      // Allow longer timeout for initialization (15 minutes)
      timeout: 900000,
    }
  );
  return response.data;
};

// ============================================================================
// Cache Stats Functions (for UI display)
// ============================================================================

export interface CacheStatsResponse {
  total_cached: number;
  pdf_count: number;
  xml_count: number;
  cache_ready: boolean;
  country?: string;
  error?: string;
}

/**
 * Get Drive cache statistics for CO.
 * Returns info about how many files are cached.
 */
export const getDriveCacheStatsCO = async (): Promise<CacheStatsResponse> => {
  const response = await apiClient.get<CacheStatsResponse>(
    '/finance/co/cache-stats'
  );
  return response.data;
};

// Alias for backwards compatibility with page component
export type PopulateCacheResponse = PrecacheResponse;
export const populateDriveCacheCO = precacheDriveFilesCO;
