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
  contract_type?: 'activos' | 'otrosi';
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
