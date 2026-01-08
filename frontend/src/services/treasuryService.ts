/**
 * Treasury Service for Tesorería payment template conversion.
 *
 * Provides API methods for Historial de Pagos validation and
 * NetSuite template generation.
 */

import apiClient from '../api/clients/apiClient';
import type {
  HistorialValidationResponse,
  CountryCode,
  ConversionHeaderStats,
} from '../types/tesoreria';

const BASE_URL = '/tesoreria';

/**
 * Result of a conversion operation including the blob and stats.
 */
export interface ConversionResult {
  /** The converted Excel file as a Blob */
  blob: Blob;
  /** Filename from Content-Disposition header */
  filename: string;
  /** Conversion statistics from headers */
  stats: ConversionHeaderStats;
}

/**
 * Treasury service with all API methods for payment template conversion.
 */
export const treasuryService = {
  /**
   * Validate an uploaded Historial de Pagos Excel file.
   *
   * @param file - Excel file to validate (.xlsx)
   * @param country - Target country ('colombia' or 'mexico')
   * @returns Validation response with column status, errors, and preview
   * @throws Error if upload or validation fails
   */
  validateHistorial: async (
    file: File,
    country: CountryCode
  ): Promise<HistorialValidationResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<HistorialValidationResponse>(
      `${BASE_URL}/validate/${country}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 1 minute timeout for validation
      }
    );

    return response.data;
  },

  /**
   * Convert Historial de Pagos to NetSuite template format.
   *
   * @param file - Excel file to convert (.xlsx)
   * @param country - Target country ('colombia' or 'mexico')
   * @returns ConversionResult with blob, filename, and stats
   * @throws Error if conversion fails
   */
  convertToNetsuiteTemplate: async (
    file: File,
    country: CountryCode
  ): Promise<ConversionResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(
      `${BASE_URL}/convert/${country}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
        timeout: 300000, // 5 minutes timeout for conversion
      }
    );

    // Parse filename from Content-Disposition header
    const contentDisposition = response.headers['content-disposition'] || '';
    const filenameMatch = contentDisposition.match(/filename=(.+?)(?:$|;)/);
    const filename = filenameMatch
      ? filenameMatch[1].replace(/["']/g, '')
      : `Aplicacion_Pagos_${country.toUpperCase().slice(0, 2)}.xlsx`;

    // Parse stats from custom header
    const statsHeader = response.headers['x-conversion-stats'] || '';
    const stats = parseStatsFromHeader(statsHeader);

    return {
      blob: response.data,
      filename,
      stats,
    };
  },

  /**
   * Get AR account catalog for a country.
   *
   * @param country - Target country ('colombia' or 'mexico')
   * @returns Catalog data with AR account mappings
   */
  getCatalogs: async (country: CountryCode): Promise<Record<string, unknown>> => {
    const response = await apiClient.get<Record<string, unknown>>(
      `${BASE_URL}/catalogs/${country}`
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

/**
 * Parse conversion stats from X-Conversion-Stats header.
 */
function parseStatsFromHeader(headerValue: string): ConversionHeaderStats {
  const stats: ConversionHeaderStats = {
    source: 0,
    output: 0,
    skipped: 0,
    errors: 0,
  };

  if (!headerValue) return stats;

  const parts = headerValue.split(';');
  for (const part of parts) {
    const [key, value] = part.split('=');
    if (key && value) {
      const numValue = parseInt(value, 10);
      if (!isNaN(numValue)) {
        switch (key.trim()) {
          case 'source':
            stats.source = numValue;
            break;
          case 'output':
            stats.output = numValue;
            break;
          case 'skipped':
            stats.skipped = numValue;
            break;
          case 'errors':
            stats.errors = numValue;
            break;
        }
      }
    }
  }

  return stats;
}

export default treasuryService;
