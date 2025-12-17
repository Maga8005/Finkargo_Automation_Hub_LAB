/**
 * Broker Incentive Service - API Integration
 *
 * Provides API methods for broker contract scanning and incentive extraction.
 * All methods include authentication, error handling, and comprehensive logging.
 *
 * @module brokerIncentiveService
 */

import apiClient from '../api/clients/apiClient';
import { extractErrorMessage } from '../utils/errorUtils';

const BASE_PATH = '/alianzas/broker-contracts';

// Timeout for directory scanning operations (30 minutes for large directories)
const SCAN_TIMEOUT = 1800000;

/**
 * Contract type enumeration.
 */
export type ContractType = 'bono' | 'incentivos' | 'colaboracion' | 'unknown';

/**
 * Contract status enumeration.
 */
export type ContractStatus = 'found' | 'not_found' | 'error';

/**
 * Configuration for broker contract directory scan.
 */
export interface BrokerContractScanConfig {
  directory_path: string;
  include_subfolders?: boolean;
  output_file_path?: string;
  request_timeout_seconds?: number;
}

/**
 * Extracted broker incentive data.
 */
export interface BrokerIncentiveData {
  broker_name: string;
  contract_date: string | null;
  rfc: string | null;
  signatory_name: string | null;
  credit_line_incentive_pct: number | null;
  operations_incentive_pct: number | null;
  contract_type: ContractType;
  contract_status: ContractStatus;
  pdf_path: string;
  extraction_date: string;
  warnings: string[];
  extraction_confidence: number;
}

/**
 * Statistics from a broker contract scan.
 */
export interface BrokerScanStatistics {
  bono_contracts: number;
  incentivos_contracts: number;
  unknown_contracts: number;
  average_credit_line_pct: number;
  average_operations_pct: number;
}

/**
 * Result from broker contract directory scan.
 */
export interface BrokerContractScanResult {
  total_folders_found: number;
  total_pdfs_processed: number;
  successful_extractions: number;
  failed_extractions: number;
  output_file_path: string;
  scan_duration_seconds: number;
  records: BrokerIncentiveData[];
  statistics: BrokerScanStatistics;
}

/**
 * Scan a directory for broker contracts and extract incentive data.
 *
 * This method triggers a directory scan that:
 * 1. Scans for folders matching 'YYYYMMDD Broker Name' pattern
 * 2. Extracts PDF text and identifies contract type
 * 3. Uses regex patterns to extract incentive percentages
 * 4. Extracts RFC and signatory information
 * 5. Generates a styled Excel report
 *
 * @param config - Scan configuration
 * @returns Promise resolving to scan results
 *
 * @example
 * const result = await scanBrokerContracts({
 *   directory_path: '/Users/alianzas/Brokers',
 *   include_subfolders: true
 * });
 * console.log('Folders found:', result.total_folders_found);
 * console.log('Successful extractions:', result.successful_extractions);
 */
export const scanBrokerContracts = async (
  config: BrokerContractScanConfig
): Promise<BrokerContractScanResult> => {
  const requestTimeoutSeconds = config.request_timeout_seconds ?? 1800;
  const axiosTimeout = Math.max((requestTimeoutSeconds + 5) * 1000, SCAN_TIMEOUT);

  console.log('[brokerIncentiveService.scanBrokerContracts] Starting broker contract scan', {
    directory_path: config.directory_path,
    include_subfolders: config.include_subfolders,
    timeout_seconds: requestTimeoutSeconds,
  });

  try {
    const response = await apiClient.post<BrokerContractScanResult>(
      `${BASE_PATH}/scan`,
      {
        ...config,
        request_timeout_seconds: requestTimeoutSeconds,
      },
      {
        timeout: axiosTimeout,
      }
    );

    console.log('[brokerIncentiveService.scanBrokerContracts] Scan completed successfully', {
      total_folders: response.data.total_folders_found,
      successful: response.data.successful_extractions,
      failed: response.data.failed_extractions,
      duration: response.data.scan_duration_seconds,
    });

    return response.data;
  } catch (error: unknown) {
    const axiosError = error as { message?: string; response?: { data?: unknown; status?: number } };
    console.error('[brokerIncentiveService.scanBrokerContracts] Scan failed:', {
      error: axiosError.message,
      response: axiosError.response?.data,
      status: axiosError.response?.status,
    });

    const errorMessage = extractErrorMessage(error, 'Error al escanear contratos de brokers');
    throw new Error(errorMessage);
  }
};

/**
 * Get results from the most recent broker contract scan.
 *
 * @returns Promise resolving to list of broker incentive records
 *
 * @example
 * const records = await getBrokerScanResults();
 * records.forEach(r => console.log(r.broker_name, r.credit_line_incentive_pct));
 */
export const getBrokerScanResults = async (): Promise<BrokerIncentiveData[]> => {
  console.log('[brokerIncentiveService.getBrokerScanResults] Fetching scan results');

  try {
    const response = await apiClient.get<BrokerIncentiveData[]>(`${BASE_PATH}/results`);

    console.log('[brokerIncentiveService.getBrokerScanResults] Results retrieved', {
      count: response.data.length,
    });

    return response.data;
  } catch (error: unknown) {
    const axiosError = error as { message?: string; response?: { data?: unknown; status?: number } };
    console.error('[brokerIncentiveService.getBrokerScanResults] Failed:', {
      error: axiosError.message,
      response: axiosError.response?.data,
      status: axiosError.response?.status,
    });

    const errorMessage = extractErrorMessage(error, 'Error al obtener resultados del escaneo');
    throw new Error(errorMessage);
  }
};

/**
 * Download the Excel file from the most recent broker contract scan.
 *
 * Triggers a browser download of the generated Excel file.
 *
 * @example
 * await exportBrokerIncentives();
 */
export const exportBrokerIncentives = async (): Promise<void> => {
  console.log('[brokerIncentiveService.exportBrokerIncentives] Downloading Excel file');

  try {
    const response = await apiClient.get(`${BASE_PATH}/export`, {
      responseType: 'blob',
    });

    // Extract filename from Content-Disposition header if available
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'broker_incentives.xlsx';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
      if (filenameMatch) {
        filename = filenameMatch[1].trim().replace(/['"]/g, '');
      }
    }

    // Create blob URL and trigger download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    console.log('[brokerIncentiveService.exportBrokerIncentives] File downloaded successfully', {
      filename,
    });
  } catch (error: unknown) {
    const axiosError = error as { message?: string; response?: { data?: unknown; status?: number } };
    console.error('[brokerIncentiveService.exportBrokerIncentives] Download failed:', {
      error: axiosError.message,
      response: axiosError.response?.data,
      status: axiosError.response?.status,
    });

    const errorMessage = extractErrorMessage(error, 'Error al descargar archivo de incentivos');
    throw new Error(errorMessage);
  }
};

/**
 * Format a percentage value for display.
 *
 * @param value - Percentage value or null
 * @returns Formatted string
 */
export const formatPercentage = (value: number | null): string => {
  if (value === null) return 'N/A';
  return `${value.toFixed(2)}%`;
};

/**
 * Format contract type for display.
 *
 * @param type - Contract type
 * @returns Spanish display string
 */
export const formatContractType = (type: ContractType): string => {
  switch (type) {
    case 'bono':
      return 'Bono';
    case 'incentivos':
      return 'Incentivos';
    case 'colaboracion':
      return 'Colaboracion';
    default:
      return 'Desconocido';
  }
};

/**
 * Get color for contract type display.
 *
 * @param type - Contract type
 * @returns MUI color string
 */
export const getContractTypeColor = (type: ContractType): 'success' | 'warning' | 'error' | 'info' => {
  switch (type) {
    case 'bono':
      return 'success';
    case 'incentivos':
      return 'warning';
    case 'colaboracion':
      return 'info';
    default:
      return 'error';
  }
};

/**
 * Format contract status for display.
 *
 * @param status - Contract status
 * @returns Spanish display string
 */
export const formatContractStatus = (status: ContractStatus): string => {
  switch (status) {
    case 'found':
      return 'Encontrado';
    case 'not_found':
      return 'Sin Contrato';
    case 'error':
      return 'Error';
    default:
      return 'Desconocido';
  }
};

/**
 * Get color for contract status display.
 *
 * @param status - Contract status
 * @returns MUI color string
 */
export const getContractStatusColor = (status: ContractStatus): 'success' | 'warning' | 'error' => {
  switch (status) {
    case 'found':
      return 'success';
    case 'not_found':
      return 'warning';
    case 'error':
      return 'error';
    default:
      return 'error';
  }
};
