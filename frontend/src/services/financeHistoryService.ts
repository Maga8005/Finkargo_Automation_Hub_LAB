/**
 * Finance History Service
 *
 * Service for tracking and querying finance report generation history
 * for both Colombia (CO) and Mexico (MX) operations.
 */

import apiClient from '../api/clients/apiClient';

// ============================================================================
// Types
// ============================================================================

export type ReportCountry = 'CO' | 'MX';
export type ReportType = 'facturacion' | 'consulta' | 'zip_download';
export type ReportStatus = 'processing' | 'completed' | 'failed' | 'downloaded';

export interface FinanceReportSummary {
  id: string;
  report_id: string;
  country: ReportCountry;
  report_type: ReportType;
  status: ReportStatus;
  generated_by_email?: string;
  generated_at: string;
  stats_summary: string;
  drive_uploaded: boolean;
}

export interface FinanceReportDetail {
  id: string;
  report_id: string;
  country: ReportCountry;
  report_type: ReportType;
  status: ReportStatus;
  generated_by?: string;
  generated_by_email?: string;
  generated_at: string;
  stats: Record<string, unknown>;
  filters_applied?: Record<string, unknown>;
  file_name?: string;
  file_size_bytes?: number;
  drive_uploaded: boolean;
  drive_url?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface FinanceHistoryFilter {
  country?: ReportCountry;
  report_type?: ReportType;
  status?: ReportStatus;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

export interface FinanceHistoryResponse {
  success: boolean;
  total: number;
  reports: FinanceReportSummary[];
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface FinanceReportStats {
  total_reports: number;
  reports_today: number;
  reports_this_week: number;
  reports_this_month: number;
  co_reports: number;
  mx_reports: number;
  facturacion_count: number;
  consulta_count: number;
  zip_download_count: number;
  completed_count: number;
  failed_count: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Get finance report history with optional filters
 *
 * @param filters - Optional filter parameters
 * @returns Paginated list of report summaries
 */
export const getFinanceHistory = async (
  filters?: FinanceHistoryFilter
): Promise<FinanceHistoryResponse> => {
  const params = new URLSearchParams();

  if (filters?.country) {
    params.append('country', filters.country);
  }
  if (filters?.report_type) {
    params.append('report_type', filters.report_type);
  }
  if (filters?.status) {
    params.append('status', filters.status);
  }
  if (filters?.date_from) {
    params.append('date_from', filters.date_from);
  }
  if (filters?.date_to) {
    params.append('date_to', filters.date_to);
  }
  if (filters?.limit !== undefined) {
    params.append('limit', filters.limit.toString());
  }
  if (filters?.offset !== undefined) {
    params.append('offset', filters.offset.toString());
  }

  const queryString = params.toString();
  const url = `/finance/history${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get<FinanceHistoryResponse>(url);
  return response.data;
};

/**
 * Get finance report statistics
 *
 * @param country - Optional country filter (CO or MX)
 * @returns Statistics object
 */
export const getFinanceStats = async (
  country?: ReportCountry
): Promise<FinanceReportStats> => {
  const url = country
    ? `/finance/history/stats?country=${country}`
    : '/finance/history/stats';

  const response = await apiClient.get<FinanceReportStats>(url);
  return response.data;
};

/**
 * Get detailed information about a specific report
 *
 * @param reportId - Report UUID or business ID (FIN-CO-2025-0001)
 * @returns Detailed report information
 */
export const getFinanceReportDetail = async (
  reportId: string
): Promise<FinanceReportDetail> => {
  const response = await apiClient.get<FinanceReportDetail>(
    `/finance/history/${reportId}`
  );
  return response.data;
};

/**
 * Export finance history to CSV file
 *
 * @param filters - Optional filter parameters
 * @returns CSV file as Blob
 */
export const exportFinanceHistoryCSV = async (
  filters?: FinanceHistoryFilter
): Promise<Blob> => {
  const params = new URLSearchParams();

  if (filters?.country) {
    params.append('country', filters.country);
  }
  if (filters?.report_type) {
    params.append('report_type', filters.report_type);
  }
  if (filters?.status) {
    params.append('status', filters.status);
  }
  if (filters?.date_from) {
    params.append('date_from', filters.date_from);
  }
  if (filters?.date_to) {
    params.append('date_to', filters.date_to);
  }

  const queryString = params.toString();
  const url = `/finance/history/export/csv${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get(url, {
    responseType: 'blob',
    timeout: 60000, // 60 seconds
  });

  return response.data;
};

/**
 * Trigger CSV download in browser
 *
 * @param blob - CSV file blob
 * @param filename - Name for the downloaded file
 */
export const triggerCSVDownload = (blob: Blob, filename: string): void => {
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
 * Format report type for display
 */
export const formatReportType = (type: ReportType): string => {
  const labels: Record<ReportType, string> = {
    facturacion: 'Procesamiento',
    consulta: 'Consulta',
    zip_download: 'Descarga ZIP',
  };
  return labels[type] || type;
};

/**
 * Format report status for display
 */
export const formatReportStatus = (status: ReportStatus): string => {
  const labels: Record<ReportStatus, string> = {
    processing: 'Procesando',
    completed: 'Completado',
    failed: 'Fallido',
    downloaded: 'Descargado',
  };
  return labels[status] || status;
};

/**
 * Get status color for MUI components
 */
export const getStatusColor = (
  status: ReportStatus
): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  const colors: Record<ReportStatus, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
    processing: 'info',
    completed: 'success',
    failed: 'error',
    downloaded: 'primary',
  };
  return colors[status] || 'default';
};

/**
 * Get country flag emoji
 */
export const getCountryFlag = (country: ReportCountry): string => {
  const flags: Record<ReportCountry, string> = {
    CO: '🇨🇴',
    MX: '🇲🇽',
  };
  return flags[country] || '🌎';
};

/**
 * Format country for display
 */
export const formatCountry = (country: ReportCountry): string => {
  const labels: Record<ReportCountry, string> = {
    CO: 'Colombia',
    MX: 'México',
  };
  return labels[country] || country;
};
