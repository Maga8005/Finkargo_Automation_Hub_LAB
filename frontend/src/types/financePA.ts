/**
 * TypeScript types for PA (Patrimonio Autónomo) Classification feature.
 *
 * NOTE: This project uses snake_case in both backend and frontend.
 */

// =============================================================================
// Enums
// =============================================================================

export type PAProcessingStatus =
  | 'uploading'
  | 'cleaning'
  | 'cleaned'
  | 'classifying'
  | 'classified'
  | 'failed';

export type RuleUploadType = 'catalog' | 'classification' | 'clasificacion_cuenta' | 'nexo';

// =============================================================================
// Account Catalog Types
// =============================================================================

export interface PAAccountCatalogEntry {
  id?: string;
  cuenta_finkargo: string;
  cuenta_homologacion: string;
  nombre_homologacion: string;
  created_at?: string;
  updated_at?: string;
}

export interface PAAccountCatalogResponse {
  entries: PAAccountCatalogEntry[];
  total_count: number;
}

export interface PAAccountCatalogUploadResponse {
  success: boolean;
  entries_uploaded: number;
  entries_updated: number;
  entries_skipped: number;
  errors: string[];
  message: string;
}

// =============================================================================
// Classification Rules Types
// =============================================================================

export interface PAClassificationRuleEntry {
  id?: string;
  tipo_transaccion: string;
  tipo_comprobante: string;
  numero_documento_patron?: string;
  categoria: string;
  subcategoria_base?: string;
  clasificacion_default?: string;
  prioridad: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PAClassificationRulesResponse {
  rules: PAClassificationRuleEntry[];
  total_count: number;
}

export interface PAClassificationRulesUploadResponse {
  success: boolean;
  rules_uploaded: number;
  rules_updated: number;
  rules_skipped: number;
  errors: string[];
  message: string;
}

// =============================================================================
// Clasificación Cuenta Rules Types
// =============================================================================

export interface PAClasificacionCuentaRuleEntry {
  id?: string;
  cuenta_nombre_patron: string;
  clasificacion: string;
  categoria_aplicable?: string;
  prioridad: number;
  is_active: boolean;
  created_at?: string;
}

export interface PAClasificacionCuentaRulesResponse {
  rules: PAClasificacionCuentaRuleEntry[];
  total_count: number;
}

export interface PAClasificacionCuentaRulesUploadResponse {
  success: boolean;
  rules_uploaded: number;
  rules_updated: number;
  rules_skipped: number;
  errors: string[];
  message: string;
}

// =============================================================================
// Nexo Rules Types
// =============================================================================

export interface PANexoRuleEntry {
  id?: string;
  cuenta_nombre_patron: string;
  nexo: string;
  prioridad: number;
  is_active: boolean;
  created_at?: string;
}

export interface PANexoRulesResponse {
  rules: PANexoRuleEntry[];
  total_count: number;
}

export interface PANexoRulesUploadResponse {
  success: boolean;
  rules_uploaded: number;
  rules_updated: number;
  rules_skipped: number;
  errors: string[];
  message: string;
}

// =============================================================================
// Rules Summary Types
// =============================================================================

export interface PARulesSummary {
  catalog_count: number;
  classification_rules_count: number;
  clasificacion_cuenta_rules_count: number;
  nexo_rules_count: number;
  last_catalog_update?: string;
  last_classification_update?: string;
  last_clasificacion_cuenta_update?: string;
  last_nexo_update?: string;
}

// =============================================================================
// Processing Types
// =============================================================================

export interface PAProcessingStats {
  total_rows: number;
  pa_rows: number;
  non_pa_rows: number;
  debito_sum: number;
  credito_sum: number;
  valor_cop_sum: number;
  valor_usd_sum: number;
  balance_valid: boolean;
  classified_count: number;
  unclassified_count: number;
  missing_homologacion_count: number;
  warnings: string[];
}

export interface PAUploadResponse {
  success: boolean;
  session_id: string;
  filename: string;
  total_rows: number;
  pa_rows: number;
  message: string;
  errors: string[];
}

export interface PACleanedPreview {
  session_id: string;
  status: PAProcessingStatus;
  stats: PAProcessingStats;
  sample_rows: Record<string, unknown>[];
  column_headers: string[];
}

export interface PAClassifiedPreview {
  session_id: string;
  status: PAProcessingStatus;
  stats: PAProcessingStats;
  sample_rows: Record<string, unknown>[];
  column_headers: string[];
  classification_summary: Record<string, number>;
}

// =============================================================================
// History Types
// =============================================================================

export interface PAProcessingHistoryEntry {
  id: string;
  session_id: string;
  status: PAProcessingStatus;
  original_filename?: string;
  original_file_size?: number;
  stats: PAProcessingStats;
  cleaned_file_url?: string;
  classified_file_url?: string;
  error_message?: string;
  processed_by?: string;
  processed_by_email?: string;
  started_at: string;
  cleaned_at?: string;
  classified_at?: string;
  completed_at?: string;
}

export interface PAProcessingHistoryFilter {
  status?: PAProcessingStatus;
  processed_by?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

export interface PAProcessingHistoryResponse {
  entries: PAProcessingHistoryEntry[];
  total_count: number;
  limit: number;
  offset: number;
}
