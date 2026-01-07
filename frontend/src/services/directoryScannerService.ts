/**
 * Directory Scanner Service - API Integration
 *
 * Provides API methods for local directory scanning and inventory file management.
 * All methods include authentication, error handling, and comprehensive logging.
 *
 * @module directoryScannerService
 */

import apiClient from '../api/clients/apiClient';
import { extractErrorMessage } from '../utils/errorUtils';

const BASE_PATH = '/v1/treasury/directory-scanner';

// Timeout for directory scanning operations (60 minutes for large directories)
const SCAN_TIMEOUT = 3600000;

/**
 * Configuration for local directory scan.
 */
export interface LocalDirectoryScanConfig {
  directory_path: string;
  output_file_path?: string;
  extract_declaration_numbers?: boolean;
  recursive?: boolean;
  pdf_extensions?: string[];
  /** Request timeout in seconds (default: 3600 = 60 minutes, max: 7200 = 2 hours) */
  request_timeout_seconds?: number;
}

/**
 * Result from local directory scan.
 */
export interface LocalDirectoryScanResult {
  total_pdfs_found: number;
  successful_extractions: number;
  failed_extractions: number;
  output_file_path: string;
  scan_duration_seconds: number;
  statistics: {
    unique_customers?: number;
    unique_dates?: number;
    total_amount?: number;
    average_amount?: number;
  };
}

/**
 * Metadata about an inventory Excel file.
 */
export interface InventoryFileMetadata {
  file_name: string;
  file_path: string;
  created_at: string;
  file_size_bytes: number;
  record_count?: number;
}

/**
 * Scan local directory and generate inventory Excel file.
 *
 * This method triggers a directory scan that:
 * 1. Recursively scans the specified directory for PDFs
 * 2. Extracts metadata from folder structure
 * 3. Optionally extracts declaration numbers from PDFs
 * 4. Generates a formatted Excel inventory file
 *
 * @param config - Scan configuration
 * @returns Promise resolving to scan results
 *
 * @example
 * const result = await scanLocalDirectory({
 *   directory_path: 'C:/FINKARGO DCS',
 *   extract_declaration_numbers: true,
 *   recursive: true
 * });
 * console.log('Found PDFs:', result.total_pdfs_found);
 * console.log('Output file:', result.output_file_path);
 */
export const scanLocalDirectory = async (
  config: LocalDirectoryScanConfig
): Promise<LocalDirectoryScanResult> => {
  // Default timeout to 60 minutes (3600 seconds) for large directory scans
  const requestTimeoutSeconds = config.request_timeout_seconds ?? 3600;

  // Calculate axios timeout (add 5 second buffer for network overhead)
  // Use SCAN_TIMEOUT as minimum to ensure we have enough time
  const axiosTimeout = Math.max((requestTimeoutSeconds + 5) * 1000, SCAN_TIMEOUT);

  console.log('[directoryScannerService.scanLocalDirectory] Starting directory scan', {
    directory_path: config.directory_path,
    extract_declaration_numbers: config.extract_declaration_numbers,
    recursive: config.recursive,
    timeout_seconds: requestTimeoutSeconds,
    axios_timeout_ms: axiosTimeout,
  });

  try {
    const response = await apiClient.post<LocalDirectoryScanResult>(
      `${BASE_PATH}/scan`,
      {
        ...config,
        request_timeout_seconds: requestTimeoutSeconds,
      },
      {
        timeout: axiosTimeout, // Override default timeout for long-running scan
      }
    );

    console.log('[directoryScannerService.scanLocalDirectory] Scan completed successfully', {
      total_pdfs: response.data.total_pdfs_found,
      successful_extractions: response.data.successful_extractions,
      failed_extractions: response.data.failed_extractions,
      output_file: response.data.output_file_path,
      duration: response.data.scan_duration_seconds,
    });

    return response.data;
  } catch (error: unknown) {
    const axiosError = error as { message?: string; response?: { data?: unknown; status?: number } };
    console.error('[directoryScannerService.scanLocalDirectory] Scan failed:', {
      error: axiosError.message,
      response: axiosError.response?.data,
      status: axiosError.response?.status,
    });

    // Convert error to user-friendly format using extractErrorMessage
    const errorMessage = extractErrorMessage(error, 'Error al escanear directorio');
    throw new Error(errorMessage);
  }
};

/**
 * List all available inventory Excel files.
 *
 * Returns metadata for all inventory files in the configured output directory,
 * sorted by creation date (newest first).
 *
 * @returns Promise resolving to list of inventory file metadata
 *
 * @example
 * const files = await listInventoryFiles();
 * console.log('Available inventory files:', files.length);
 * files.forEach(file => {
 *   console.log(`- ${file.file_name} (${file.file_size_bytes} bytes)`);
 * });
 */
export const listInventoryFiles = async (): Promise<InventoryFileMetadata[]> => {
  console.log('[directoryScannerService.listInventoryFiles] Fetching inventory files list');

  try {
    const response = await apiClient.get<InventoryFileMetadata[]>(
      `${BASE_PATH}/inventory-files`
    );

    console.log('[directoryScannerService.listInventoryFiles] Files retrieved successfully', {
      count: response.data.length,
    });

    return response.data;
  } catch (error: unknown) {
    const axiosError = error as { message?: string; response?: { data?: unknown; status?: number } };
    console.error('[directoryScannerService.listInventoryFiles] Failed to list files:', {
      error: axiosError.message,
      response: axiosError.response?.data,
      status: axiosError.response?.status,
    });

    const errorMessage = extractErrorMessage(error, 'Error al listar archivos de inventario');
    throw new Error(errorMessage);
  }
};

/**
 * Download an inventory Excel file.
 *
 * Triggers browser download of the specified inventory file.
 *
 * @param filename - Name of the inventory file to download
 *
 * @example
 * await downloadInventoryFile('inventory_20251103_143052.xlsx');
 */
export const downloadInventoryFile = async (filename: string): Promise<void> => {
  console.log('[directoryScannerService.downloadInventoryFile] Downloading file', {
    filename,
  });

  try {
    const response = await apiClient.get(
      `${BASE_PATH}/inventory-files/${filename}`,
      {
        responseType: 'blob',
      }
    );

    // Create blob URL and trigger download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    console.log('[directoryScannerService.downloadInventoryFile] File downloaded successfully');
  } catch (error: unknown) {
    const axiosError = error as { message?: string; response?: { data?: unknown; status?: number } };
    console.error('[directoryScannerService.downloadInventoryFile] Download failed:', {
      error: axiosError.message,
      response: axiosError.response?.data,
      status: axiosError.response?.status,
    });

    const errorMessage = extractErrorMessage(error, 'Error al descargar archivo de inventario');
    throw new Error(errorMessage);
  }
};

/**
 * Format file size in bytes to human-readable format.
 *
 * @param bytes - File size in bytes
 * @returns Formatted file size string
 *
 * @example
 * formatFileSize(1024) // "1.0 KB"
 * formatFileSize(1048576) // "1.0 MB"
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

/**
 * Format date to localized string.
 *
 * @param dateString - ISO date string
 * @returns Formatted date string
 *
 * @example
 * formatDate('2025-11-03T14:30:52Z') // "Nov 3, 2025 2:30 PM"
 */
export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    console.error('[directoryScannerService.formatDate] Failed to format date:', error);
    return dateString;
  }
};
