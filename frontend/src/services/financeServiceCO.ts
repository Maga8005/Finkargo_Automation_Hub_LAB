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
