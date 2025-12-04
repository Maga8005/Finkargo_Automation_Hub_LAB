export type SearchType = 'codigo_operacion' | 'rfc' | 'fecha';

export type ArchivoEstado = 'Disponible' | 'No disponible' | 'Pendiente';

export interface InvoiceRecord {
  uuid: string;
  codigo_operacion: string;
  conceptos: string;
  fecha_emision: string;
  rfc_receptor: string;
  razon_receptor: string;
  subtotal: number;
  iva_trasladado: number;
  iva_exento: number;
  total: number;
  uuid_relacionados?: string;
  tipo_comprobante?: string;
}

export interface ExcelValidationError {
  row: number;
  column: string;
  message: string;
}

export interface ExcelValidationResponse {
  success: boolean;
  total_rows: number;
  valid_rows: number;
  errors: ExcelValidationError[];
  data: InvoiceRecord[];
  session_id: string;
  drive_sync_stats?: {
    new: number;
    updated: number;
    unchanged: number;
  };
}

export interface InvoiceSearchRequest {
  session_id: string;
  search_type: SearchType;
  codigo_operacion?: string;
  rfc?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
}

export interface InvoiceSearchResult extends InvoiceRecord {
  archivo_estado: ArchivoEstado;
}

export interface InvoiceSearchResponse {
  results: InvoiceSearchResult[];
  total_found: number;
  total_amount: number;
}

export interface ZipGenerationRequest {
  session_id: string;
  uuids?: string[];
  search_criteria?: InvoiceSearchRequest;
  metadata?: Record<string, unknown>;
}

export interface DriveStatusResponse {
  connected: boolean;
  folder_id: string;
  folder_name: string;
  total_files: number;
  last_sync?: string;
}

export interface SessionStats {
  session_id: string;
  total_records: number;
  total_amount: number;
  total_subtotal: number;
  total_iva: number;
  unique_rfcs: number;
  unique_operaciones: number;
  drive_sync_stats?: {
    new: number;
    updated: number;
    unchanged: number;
  };
}
