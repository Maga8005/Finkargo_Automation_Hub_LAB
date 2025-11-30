/**
 * Types for Tesorería (Treasury) module - Payment Template Conversion.
 */

/**
 * Supported countries for payment template conversion.
 */
export type CountryCode = 'colombia' | 'mexico';

/**
 * Payment concept types for NetSuite template.
 */
export type ConceptType =
  | 'CAPITAL'
  | 'SEGUROS'
  | 'INTERESES'
  | 'MORATORIOS'
  | 'COSTOS_ADICIONALES'
  | '4X1000'
  | 'FONDO_GARANTIAS'
  | 'IVA_FONDO_GARANTIAS'
  | 'SERVICIO_ORIGINACION'
  | 'SERVICIO_GIRO'
  | 'COMISION_DESEMBOLSO'
  | 'COMISION_DISPOSICION'
  | 'COMISION_SWIFT'
  | 'COMISION_ADMINISTRACION'
  | 'COMISION_APERTURA';

/**
 * Represents a validation error found in the Historial de Pagos file.
 */
export interface HistorialValidationError {
  /** Row number where the error occurred (1-indexed, 0 for header errors) */
  row: number;
  /** Column name where the error occurred */
  column: string;
  /** Human-readable error message in Spanish */
  message: string;
}

/**
 * Status of column validation for a required column.
 */
export interface ColumnValidationStatus {
  /** Name of the required column */
  column_name: string;
  /** Whether the column was found in the file */
  found: boolean;
  /** Name of the column in the source file (if found) */
  source_column?: string;
}

/**
 * Statistics for a concept type in the file.
 */
export interface ConceptStats {
  /** Type of payment concept */
  concept_type: string;
  /** Number of rows with non-zero values */
  count: number;
  /** Sum of values for this concept */
  total_amount: number;
}

/**
 * Response from Historial de Pagos upload and validation endpoint.
 */
export interface HistorialValidationResponse {
  /** Whether validation passed without critical errors */
  success: boolean;
  /** Country for which validation was performed */
  country: string;
  /** Total number of data rows in the Excel */
  total_rows: number;
  /** Number of rows that passed validation */
  valid_rows: number;
  /** Estimated number of output rows after conversion */
  estimated_output_rows: number;
  /** Validation status for each required column */
  column_status: ColumnValidationStatus[];
  /** Statistics per concept type */
  concept_stats: ConceptStats[];
  /** List of validation errors found */
  errors: HistorialValidationError[];
  /** First few rows of parsed data for preview */
  preview_data?: Record<string, string | null>[];
}

/**
 * Statistics from the payment template conversion.
 */
export interface ConversionStats {
  /** Number of source rows processed */
  source_rows: number;
  /** Number of output rows generated */
  output_rows: number;
  /** Count of rows per concept type */
  concepts_breakdown: Record<string, number>;
  /** Number of rows skipped (no non-zero concepts) */
  skipped_rows: number;
  /** Number of rows with errors */
  errors_count: number;
}

/**
 * Response from payment template conversion endpoint.
 */
export interface ConversionResponse {
  /** Whether conversion was successful */
  success: boolean;
  /** Name of the generated file */
  filename: string;
  /** Conversion statistics */
  stats: ConversionStats;
  /** Optional message about the conversion */
  message?: string;
}

/**
 * Parsed conversion statistics from response headers.
 */
export interface ConversionHeaderStats {
  source: number;
  output: number;
  skipped: number;
  errors: number;
}

/**
 * Parse conversion stats from X-Conversion-Stats header.
 */
export function parseConversionStats(headerValue: string): ConversionHeaderStats {
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
