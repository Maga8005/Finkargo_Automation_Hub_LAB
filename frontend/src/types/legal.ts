/**
 * Legal Contract Automation Types
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

export enum ContractStatus {
  GENERATED = 'generated',
  UNDER_REVIEW = 'under_review',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export interface ContractGeneration {
  id: string;
  contract_id: string;
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
  generation_date: string;
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
}

export interface ContractReviewRequest {
  contract_id: string;
  action: 'approve' | 'reject';
  notes?: string;
}

export interface ClientSearchParams {
  query?: string;
  nit?: string;
  nombre?: string;
  is_active?: boolean;
}
