/**
 * TypeScript types for Treasury Declaration-Historial Matching feature.
 *
 * All types use snake_case to match backend Pydantic models.
 */

/**
 * Match status for a payment group.
 */
export type MatchStatus = 'matched' | 'partial' | 'unmatched' | 'conflict';

/**
 * Single row from Historial de Pagos Excel file.
 */
export interface HistorialRecord {
  row_number: number;
  cliente: string;
  cliente_normalized?: string;
  identificacion_cliente: string;
  codigo_desembolso?: string;
  codigo_recaudo?: string;
  numero_factura?: string;
  fecha_desembolso?: string;
  fecha_vencimiento?: string;
  valor_desembolso?: number;
  estado_desembolso?: string;
  fecha_pago: string;
  total_pagado?: number;
  moneda?: string;
  medio_pago?: string;
  tasa_cambio?: number;
  total_pagado_usd?: number;
  capital: number;
  declaracion_cambio_numero?: string;
  dc_nombre?: string;
  dim?: string;
  factura_final?: string;
}

/**
 * Aggregated group of payment records.
 */
export interface PaymentGroup {
  group_id: string;
  cliente: string;
  cliente_normalized: string;
  identificacion_cliente: string;
  fecha_pago: string;
  total_capital: number;
  record_count: number;
  record_row_numbers: number[];
  moneda?: string;
}

/**
 * Declaration information from inventory.
 */
export interface DeclarationItem {
  declaration_id: string;
  declaration_number: string;
  customer_name: string;
  customer_name_normalized: string;
  fecha: string;
  amount: number;
  pdf_file_name: string;
  folder_path?: string;
}

/**
 * Configuration for the matching algorithm.
 */
export interface MatchConfig {
  date_tolerance_days: number;
  amount_tolerance: number;
  customer_match_threshold: number;
  customer_match_strict: boolean;
}

/**
 * Default matching configuration.
 */
export const DEFAULT_MATCH_CONFIG: MatchConfig = {
  date_tolerance_days: 7,
  amount_tolerance: 2.0,
  customer_match_threshold: 85,
  customer_match_strict: false,
};

/**
 * Result of matching a payment group to a declaration.
 */
export interface MatchResult {
  group_id: string;
  payment_group: PaymentGroup;
  declaration?: DeclarationItem;
  match_status: MatchStatus;
  match_confidence: number;
  customer_similarity?: number;
  date_difference_days?: number;
  amount_difference?: number;
  conflict_declarations?: DeclarationItem[];
}

/**
 * Column validation status.
 */
export interface ColumnValidationStatus {
  column_name: string;
  found: boolean;
  source_column?: string;
}

/**
 * Response from uploading and parsing Historial de Pagos Excel.
 */
export interface HistorialUploadResponse {
  success: boolean;
  session_id: string;
  total_rows: number;
  valid_rows: number;
  payment_groups: PaymentGroup[];
  group_count: number;
  column_status: ColumnValidationStatus[];
  errors: string[];
  preview_data?: Record<string, string | null>[];
}

/**
 * Statistics summary of matching results.
 */
export interface MatchingStatistics {
  total_payment_groups: number;
  matched_groups: number;
  partial_matches: number;
  unmatched_groups: number;
  conflict_groups: number;
  match_percentage: number;
  average_confidence: number;
  total_declarations: number;
  declarations_used: number;
  declarations_unused: number;
}

/**
 * Full matching session response.
 */
export interface MatchingSessionResponse {
  session_id: string;
  success: boolean;
  config: MatchConfig;
  results: MatchResult[];
  statistics: MatchingStatistics;
  errors: string[];
}

/**
 * Request to manually override a match.
 */
export interface ManualOverrideRequest {
  session_id: string;
  group_id: string;
  declaration_id?: string;
}

/**
 * Response from manual override operation.
 */
export interface ManualOverrideResponse {
  success: boolean;
  message: string;
  updated_result?: MatchResult;
}

/**
 * Response from uploading declaration inventory Excel.
 */
export interface DeclarationInventoryUploadResponse {
  success: boolean;
  session_id: string;
  total_declarations: number;
  declarations: DeclarationItem[];
  errors: string[];
}

/**
 * Status chip color mapping for match statuses.
 */
export const MATCH_STATUS_COLORS: Record<MatchStatus, 'success' | 'warning' | 'error' | 'info'> = {
  matched: 'success',
  partial: 'warning',
  unmatched: 'error',
  conflict: 'info',
};

/**
 * Spanish labels for match statuses.
 */
export const MATCH_STATUS_LABELS: Record<MatchStatus, string> = {
  matched: 'Coincidencia',
  partial: 'Parcial',
  unmatched: 'Sin coincidencia',
  conflict: 'Conflicto',
};

/**
 * State for the matching workflow.
 */
export interface MatchingWorkflowState {
  activeStep: number;
  sessionId: string | null;
  historialFile: File | null;
  declarationsFile: File | null;
  uploadResponse: HistorialUploadResponse | null;
  declarationsResponse: DeclarationInventoryUploadResponse | null;
  matchConfig: MatchConfig;
  matchingResponse: MatchingSessionResponse | null;
  loading: boolean;
  error: string | null;
}

/**
 * Initial state for matching workflow.
 */
export const INITIAL_WORKFLOW_STATE: MatchingWorkflowState = {
  activeStep: 0,
  sessionId: null,
  historialFile: null,
  declarationsFile: null,
  uploadResponse: null,
  declarationsResponse: null,
  matchConfig: DEFAULT_MATCH_CONFIG,
  matchingResponse: null,
  loading: false,
  error: null,
};

/**
 * Workflow steps for the matching page.
 */
export const WORKFLOW_STEPS = [
  {
    label: 'Cargar Archivos',
    description: 'Suba el Historial de Pagos y el inventario de declaraciones',
  },
  {
    label: 'Configurar Parámetros',
    description: 'Ajuste los parámetros de tolerancia para la coincidencia',
  },
  {
    label: 'Revisar Resultados',
    description: 'Revise y ajuste las coincidencias encontradas',
  },
  {
    label: 'Descargar',
    description: 'Descargue el archivo enriquecido con las declaraciones',
  },
];
