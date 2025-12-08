/**
 * Legal Contract Automation Types
 * Updated: Contract workflow types
 */

export interface Client {
  id: string;
  nit: string;
  nombre_importador: string;
  representante_legal: string;
  cedula_representante: string;
  ciudad_domicilio: string;
  cupo_plataforma: number;
  created_at?: string;
  updated_at?: string;
  is_active?: boolean;
  notes?: string;
  // New fields for contract template
  direccion_comercial?: string;
  tipo_identificacion_representante?: string;
  nombre_contrato_marco?: string;
  kam_nombre?: string;
  kam_email?: string;
  destinatario_nombre?: string;
  destinatario_email?: string;
}

export interface ContractTemplate {
  id: string;
  version: string;
  contract_type: string;
  template_content: string;
  active: boolean;
  created_by?: string;
  created_at?: string;
  notes?: string;
}

export type ContractStatus =
  | 'generated'
  | 'under_review'
  | 'approved'
  | 'rejected';

export const ContractStatus = {
  GENERATED: 'generated' as const,
  UNDER_REVIEW: 'under_review' as const,
  APPROVED: 'approved' as const,
  REJECTED: 'rejected' as const,
};

export interface ContractGeneration {
  id: string;
  contract_id: string;
  contract_type: string;
  client_nit: string;
  client_id: string;
  status: ContractStatus;
  generated_by: string;
  generated_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
  pdf_url?: string;
  pdf_storage_path?: string;
  approved_document_url?: string;
  template_id: string;
  template_version: string;
  data_snapshot: ClientDataSnapshot;
  created_at: string;
  updated_at: string;
}

export interface ClientDataSnapshot {
  nit: string;
  nombre_importador: string;
  representante_legal: string;
  cedula_representante: string;
  ciudad_domicilio: string;
  cupo_plataforma: number;
  contract_id: string;
  contract_type: string;
  generation_date: string;
  // Additional fields for contract template
  direccion_comercial?: string;
  tipo_identificacion_representante?: string;
  nombre_contrato_marco?: string;
  kam_nombre?: string;
  kam_email?: string;
  destinatario_nombre?: string;
  destinatario_email?: string;
}

export interface DataImport {
  id: string;
  file_name: string;
  file_size?: number;
  total_rows?: number;
  successful_rows?: number;
  failed_rows?: number;
  error_log?: Record<string, unknown>;
  imported_by: string;
  imported_at: string;
  status: 'processing' | 'completed' | 'failed';
}

export interface ContractGenerationRequest {
  client_nit: string;
  contract_type?:
    | 'activos'
    | 'otrosi'
    | 'inventario_bodega'
    // Paga Local Colombia - Cuenta Cliente - Aval PJ
    | 'pl_co_credito_aval_pj'
    | 'pl_co_mandato_pj'
    // Paga Local Colombia - Cuenta Cliente - Aval PN
    | 'pl_co_credito_aval_pn'
    | 'pl_co_mandato_pn'
    // Paga Local Colombia - Cuenta Cliente - Sin Aval
    | 'pl_co_credito_no_aval'
    | 'pl_co_mandato_no_aval'
    // Paga Local Colombia - Documentos Operación
    | 'pl_co_mandato_im'
    | 'pl_co_solicitud_desembolso'
    | 'pl_co_dian_mandato_im';
}

export interface ContractReviewRequest {
  action: 'approve' | 'reject';
  notes?: string;
}

export interface ClientSearchParams {
  query?: string;
  nit?: string;
  nombre?: string;
  is_active?: boolean;
}

// Operations Sorting Types
export type OperationsSortField =
  | 'contract_id'
  | 'contract_type'
  | 'client_nit'
  | 'reviewed_at'
  | 'nombre_importador'
  | 'cupo_plataforma';

export type OperationsSortOrder = 'asc' | 'desc';

export interface OperationsSortParams {
  sort_by?: OperationsSortField;
  sort_order?: OperationsSortOrder;
}

// Operations Filter Types
export interface OperationsFilterParams {
  contract_types?: string[];
  client_name?: string;
  client_nit?: string;
  date_from?: string;
  date_to?: string;
  cupo_min?: number;
  cupo_max?: number;
}

// Solicitud de Desembolso Types
export interface AnexoItem {
  acreedor: string;
  numero_instrumento: string;
  monto: number;
}

export interface CotizacionData {
  numero_cotizacion: string;
  fecha_cotizacion?: string;
  fecha_contrato_credito?: string;
  representante_legal?: string;
  tipo_id_representante?: string;
  numero_id_representante?: string;
  anexo_items: AnexoItem[];
  monto_total: number;
}

export interface SolicitudDesembolsoRequest {
  client_nit: string;
  numero_cotizacion_desembolso: string;
  fecha_contrato_credito: string; // ISO date string
  monto: number;
  dias_plazo: number;
  anexo_items: AnexoItem[];
}

// Instrucción de Mandato Types
export interface BankCertificateData {
  numero_certificado?: string;
  banco: string;
  fecha_emision?: string;
  razon_social: string;
  nit: string;
  tipo_cuenta: string;
  numero_cuenta: string;
}

export interface AcreedorGastosNacionales {
  razon_social: string;
  nit?: string;
  banco: string;
  tipo_cuenta: string;
  numero_cuenta: string;
}

export interface InstruccionMandatoRequest {
  client_nit: string;
  numero_cotizacion_desembolso: string;
  fecha_contrato_mandato: string; // ISO date string
  monto: number;
  acreedores: AcreedorGastosNacionales[];
}

export interface InstruccionMandatoFormData {
  cotizacion_file?: File;
  cotizacion_data?: CotizacionData;
  bank_certificate_files: File[];
  acreedores: AcreedorGastosNacionales[];
  is_dian_only: boolean;
  manual_acreedores: AcreedorGastosNacionales[];
}

// DIAN Mandato (IM) Types - Simplified, no creditors
export interface DIANMandatoRequest {
  client_nit: string;
  numero_cotizacion_desembolso: string;
  fecha_contrato_mandato: string; // ISO date string
  monto: number;
}
