/**
 * Risk Management Types
 * TypeScript types for fraud detection and risk assessment
 */

// ==================== Enums as Union Types ====================

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type AssessmentStatus =
  | 'pending'
  | 'pending_documents'
  | 'pending_finalization'
  | 'in_progress'
  | 'completed'
  | 'escalated'
  | 'approved'
  | 'rejected';

export type AlertSeverity = 'info' | 'warning' | 'critical';

export type AlertType =
  | 'new_critical'
  | 'escalation'
  | 'threshold_breach'
  | 'blacklist_match'
  | 'review_required';

export type EntityType =
  | 'nit'
  | 'email_domain'
  | 'company_name'
  | 'person_id'
  | 'address'
  | 'phone';

export type RuleType =
  | 'identity'
  | 'email'
  | 'document'
  | 'nit'
  | 'address'
  | 'financial'
  | 'history';

// Binary verification status for risk assessments
export type VerificationStatus = 'pending' | 'pass' | 'requires_manual_verification';

// NOTE: AssessmentType removed - only one evaluation workflow exists (comprehensive)
// Kept as comment for backward compatibility awareness with existing database records

// ==================== Fraud Indicator ====================

export interface FraudIndicator {
  indicator_name: string;
  indicator_value: boolean;
  severity: RiskLevel;
  evidence?: string;
  score_impact: number;
}

// ==================== Risk Assessment ====================

export interface RiskAssessment {
  id: string;
  assessment_id: string;
  client_nit: string;
  risk_level: RiskLevel;
  risk_score: number;
  fraud_indicators: FraudIndicator[];
  status: AssessmentStatus;
  assessment_type: string;
  created_at: string;
  // Binary verification status fields
  verification_status: VerificationStatus;
  has_discrepancies: boolean;
  discrepancy_count: number;
}

export interface ClientInfo {
  nit: string;
  nombre_importador?: string;
  representante_legal?: string;
  ciudad_domicilio?: string;
  cupo_plataforma?: number;
}

export interface RiskAssessmentDetail extends RiskAssessment {
  assessed_by?: string;
  assessed_at?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
  client_info?: ClientInfo;
  client_data_snapshot?: Record<string, unknown>;
  updated_at?: string;
  finalized_by?: string;
  finalized_at?: string;
}

// ==================== Request/Response Types ====================

export interface RiskAssessmentRequest {
  client_nit: string;
  // NOTE: assessment_type removed - only comprehensive evaluation workflow exists
}

export interface RiskDecisionRequest {
  status: 'approved' | 'rejected' | 'escalated';
  notes?: string;
}

// ==================== Statistics ====================

export interface RiskStats {
  total_assessments: number;
  pending_review: number;
  in_progress: number;
  completed: number;
  escalated: number;
  approved: number;
  rejected: number;
  low_risk_count: number;
  medium_risk_count: number;
  high_risk_count: number;
  critical_risk_count: number;
  assessed_today: number;
  assessed_this_week: number;
  approval_rate?: number;
  rejection_rate?: number;
  // Binary verification status counts
  pass_count: number;
  requires_verification_count: number;
}

// ==================== Fraud Detection Rules ====================

export interface FraudDetectionRule {
  id: string;
  rule_name: string;
  rule_type: RuleType;
  description?: string;
  weight: number;
  threshold: number;
  is_active: boolean;
  config?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface RuleUpdateRequest {
  weight?: number;
  threshold?: number;
  is_active?: boolean;
  config?: Record<string, unknown>;
}

// ==================== Blacklist ====================

export interface BlacklistEntry {
  id: string;
  entity_type: EntityType;
  entity_value: string;
  reason: string;
  source?: string;
  added_by?: string;
  added_by_name?: string;
  added_at: string;
  expires_at?: string;
  is_active: boolean;
}

export interface BlacklistEntryRequest {
  entity_type: EntityType;
  entity_value: string;
  reason: string;
}

// ==================== Alerts ====================

export interface RiskAlert {
  id: string;
  assessment_id?: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  is_read: boolean;
  read_by?: string;
  read_at?: string;
  created_at: string;
}

// ==================== Filter Types ====================

export interface RiskAssessmentFilter {
  status?: AssessmentStatus;
  risk_level?: RiskLevel;
  client_nit?: string;
  date_from?: string;
  date_to?: string;
  assessed_by?: string;
  limit?: number;
  offset?: number;
}

export interface BlacklistFilter {
  entity_type?: EntityType;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

// ==================== UI Helper Types ====================

export interface RiskLevelConfig {
  label: string;
  color: 'success' | 'warning' | 'error' | 'default';
  bgColor: string;
  textColor: string;
}

export const RISK_LEVEL_CONFIG: Record<RiskLevel, RiskLevelConfig> = {
  low: {
    label: 'Bajo',
    color: 'success',
    bgColor: '#E0F7E6',
    textColor: '#2CA14D',
  },
  medium: {
    label: 'Medio',
    color: 'warning',
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
  },
  high: {
    label: 'Alto',
    color: 'error',
    bgColor: '#FFE4E4',
    textColor: '#CC071E',
  },
  critical: {
    label: 'Crítico',
    color: 'error',
    bgColor: '#CC071E',
    textColor: '#FFFFFF',
  },
};

export const ASSESSMENT_STATUS_CONFIG: Record<AssessmentStatus, { label: string; color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' }> = {
  pending: { label: 'Pendiente', color: 'warning' },
  pending_documents: { label: 'Pendiente Documentos', color: 'info' },
  pending_finalization: { label: 'Pendiente Finalización', color: 'warning' },
  in_progress: { label: 'En Progreso', color: 'info' },
  completed: { label: 'Completado', color: 'success' },
  escalated: { label: 'Escalado', color: 'error' },
  approved: { label: 'Aprobado', color: 'success' },
  rejected: { label: 'Rechazado', color: 'error' },
};

export const ALERT_SEVERITY_CONFIG: Record<AlertSeverity, { label: string; color: 'info' | 'warning' | 'error' }> = {
  info: { label: 'Información', color: 'info' },
  warning: { label: 'Advertencia', color: 'warning' },
  critical: { label: 'Crítico', color: 'error' },
};

// ==================== Verification Status UI Config ====================

export interface VerificationStatusConfig {
  label: string;
  color: 'success' | 'error' | 'warning';
  bgColor: string;
  textColor: string;
  icon: 'CheckCircle' | 'Warning' | 'HourglassEmpty';
}

export const VERIFICATION_STATUS_CONFIG: Record<VerificationStatus, VerificationStatusConfig> = {
  pending: {
    label: 'PENDIENTE',
    color: 'warning',
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
    icon: 'HourglassEmpty',
  },
  pass: {
    label: 'APROBADO',
    color: 'success',
    bgColor: '#E0F7E6',
    textColor: '#2CA14D',
    icon: 'CheckCircle',
  },
  requires_manual_verification: {
    label: 'FALLIDO-REQUIERE REVISIÓN',
    color: 'error',
    bgColor: '#FFE4E4',
    textColor: '#CC071E',
    icon: 'Warning',
  },
};

export const ENTITY_TYPE_LABELS: Record<EntityType, string> = {
  nit: 'NIT',
  email_domain: 'Dominio de Email',
  company_name: 'Nombre de Empresa',
  person_id: 'Cédula',
  address: 'Dirección',
  phone: 'Teléfono',
};

// ==================== Document Extraction Types ====================

export type DocumentType =
  | 'financial_statement_current'
  | 'financial_statement_prior'
  | 'cedula'
  | 'composicion_accionaria'
  | 'rut'
  | 'certificado_existencia';

export type ExtractionStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type ValidationType =
  | 'company_name'
  | 'nit'
  | 'nit_check_digit'
  | 'legal_representative'
  | 'shareholders'
  | 'financial_continuity'
  | 'email_domain'
  | 'typosquatting'
  | 'provider_domain'
  | 'address'
  | 'domain_existence'
  | 'domain_age';

export type DiscrepancySeverity = 'low' | 'medium' | 'high' | 'critical';

export interface DocumentExtraction {
  id: string;
  assessment_id: string;
  document_type: DocumentType;
  document_filename: string;
  extraction_status: ExtractionStatus;
  extraction_method: string;
  extraction_confidence?: number;
  extracted_data?: Record<string, unknown>;
  extraction_errors?: string[];
  created_at: string;
  updated_at?: string;
}

export interface DocumentExtractionList {
  assessment_id: string;
  total_documents: number;
  pending_count: number;
  processing_count: number;
  completed_count: number;
  failed_count: number;
  extractions: DocumentExtraction[];
}

export interface CrossValidationResult {
  id?: string;
  validation_type: ValidationType;
  documents_compared: string[];
  field_compared?: string;
  values_found: Record<string, unknown>;
  is_discrepancy: boolean;
  severity?: DiscrepancySeverity;
  description?: string;
  score_impact: number;
}

export interface CrossValidationResponse {
  assessment_id: string;
  total_discrepancies: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_score_impact: number;
  results: CrossValidationResult[];
  validated_at?: string;
}

export interface DocumentUploadResponse {
  id: string;
  assessment_id: string;
  document_type: DocumentType;
  document_filename: string;
  extraction_status: ExtractionStatus;
  created_at: string;
}

export interface TriggerExtractionResponse {
  assessment_id: string;
  documents_queued: number;
  message: string;
}

export interface TriggerValidationResponse {
  assessment_id: string;
  validation_status: string;
  discrepancies_found: number;
  message: string;
}

// ==================== Document Type Configuration ====================

export interface DocumentTypeConfig {
  label: string;
  accepted_formats: string[];
  max_size_mb: number;
  required: boolean;
}

export const DOCUMENT_TYPE_CONFIG: Record<DocumentType, DocumentTypeConfig> = {
  financial_statement_current: {
    label: 'Estados Financieros (Año Actual)',
    accepted_formats: ['pdf'],
    max_size_mb: 50,
    required: true,
  },
  financial_statement_prior: {
    label: 'Estados Financieros (Año Anterior)',
    accepted_formats: ['pdf'],
    max_size_mb: 50,
    required: true,
  },
  cedula: {
    label: 'Cédula del Representante Legal',
    accepted_formats: ['pdf', 'png', 'jpg', 'jpeg'],
    max_size_mb: 5,
    required: true,
  },
  composicion_accionaria: {
    label: 'Composición Accionaria',
    accepted_formats: ['pdf'],
    max_size_mb: 10,
    required: true,
  },
  rut: {
    label: 'RUT',
    accepted_formats: ['pdf', 'png'],
    max_size_mb: 5,
    required: true,
  },
  certificado_existencia: {
    label: 'Certificado de Existencia',
    accepted_formats: ['pdf'],
    max_size_mb: 50,
    required: false,
  },
};

export const EXTRACTION_STATUS_CONFIG: Record<ExtractionStatus, { label: string; color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' }> = {
  pending: { label: 'Pendiente', color: 'warning' },
  processing: { label: 'Procesando', color: 'info' },
  completed: { label: 'Completado', color: 'success' },
  failed: { label: 'Fallido', color: 'error' },
};

export const DISCREPANCY_SEVERITY_CONFIG: Record<DiscrepancySeverity, { label: string; color: 'success' | 'warning' | 'error' | 'default'; bgColor: string; textColor: string }> = {
  low: {
    label: 'Bajo',
    color: 'success',
    bgColor: '#E0F7E6',
    textColor: '#2CA14D',
  },
  medium: {
    label: 'Medio',
    color: 'warning',
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
  },
  high: {
    label: 'Alto',
    color: 'error',
    bgColor: '#FFE4E4',
    textColor: '#CC071E',
  },
  critical: {
    label: 'Crítico',
    color: 'error',
    bgColor: '#CC071E',
    textColor: '#FFFFFF',
  },
};

export const VALIDATION_TYPE_LABELS: Record<ValidationType, string> = {
  company_name: 'Nombre de Empresa',
  nit: 'NIT',
  nit_check_digit: 'Dígito de Verificación NIT',
  legal_representative: 'Representante Legal',
  shareholders: 'Accionistas',
  financial_continuity: 'Continuidad Financiera',
  email_domain: 'Dominio de Email',
  typosquatting: 'Typosquatting de Dominio',
  provider_domain: 'Proveedor de Email',
  address: 'Dirección',
  domain_existence: 'Existencia de Dominio',
  domain_age: 'Antigüedad de Dominio',
};

// ==================== External Contact Types ====================

export type ExternalContactValidationStatus = 'pending' | 'validated' | 'suspicious' | 'critical';

export type ExternalContactSource = 'comercial_team' | 'whatsapp' | 'email' | 'phone' | 'other';

export interface EmailValidationResult {
  is_suspicious: boolean;
  similar_domain: string | null;
  similarity_score: number;
  levenshtein_distance: number;
  detection_type: string; // 'typosquatting', 'tld_variation', 'provider_domain', 'exact_match', 'no_match', 'domain_not_found', 'young_domain'
  description: string;
  is_free_provider: boolean;
  // Domain existence and age validation fields
  domain_exists?: boolean | null; // null = unknown/pending
  domain_age_days?: number | null; // null = unavailable
  domain_creation_date?: string | null; // ISO date string, null = unavailable
  age_lookup_status?: string; // 'success', 'failed', 'unavailable', 'pending'
  domain_registrar?: string | null; // null = unavailable
}

export interface ExternalContact {
  id: string;
  assessment_id: string;
  email: string;
  sender_name?: string;
  source: string;
  validation_status: ExternalContactValidationStatus;
  validation_result?: EmailValidationResult;
  validated_at?: string;
  created_at: string;
  created_by?: string;
  notes?: string;
  is_active: boolean;
}

export interface ExternalContactRequest {
  email: string;
  sender_name?: string;
  source: string;
  notes?: string;
}

export interface ExternalContactListResponse {
  assessment_id: string;
  total_contacts: number;
  pending_count: number;
  validated_count: number;
  suspicious_count: number;
  critical_count: number;
  contacts: ExternalContact[];
}

// ==================== External Contact UI Config ====================

export interface ExternalContactValidationStatusConfig {
  label: string;
  color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  bgColor: string;
  textColor: string;
}

export const EXTERNAL_CONTACT_VALIDATION_STATUS_CONFIG: Record<ExternalContactValidationStatus, ExternalContactValidationStatusConfig> = {
  pending: {
    label: 'Pendiente',
    color: 'warning',
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
  },
  validated: {
    label: 'Validado',
    color: 'success',
    bgColor: '#E0F7E6',
    textColor: '#2CA14D',
  },
  suspicious: {
    label: 'Sospechoso',
    color: 'warning',
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
  },
  critical: {
    label: 'Crítico',
    color: 'error',
    bgColor: '#FFE4E4',
    textColor: '#CC071E',
  },
};

export const EXTERNAL_CONTACT_SOURCE_LABELS: Record<ExternalContactSource, string> = {
  comercial_team: 'Equipo Comercial',
  whatsapp: 'WhatsApp',
  email: 'Correo Electrónico',
  phone: 'Teléfono',
  other: 'Otro',
};

// ==================== Email Chain Types ====================

export type EmailChainValidationStatus = 'pending' | 'validated' | 'suspicious' | 'critical';

export interface EmailMessage {
  sender_email: string;
  sender_name?: string;
  sender_domain: string;
  date?: string;
  subject?: string;
  body_excerpt?: string;
}

export interface ExtractedMentions {
  company_names: string[];
  nits: string[];
  representative_names: string[];
  domains: string[];
}

export interface EmailChainParsedData {
  messages: EmailMessage[];
  mentions: ExtractedMentions;
  parse_errors: string[];
}

export interface EmailChainDiscrepancy {
  field: string;
  email_value: string;
  document_value?: string;
  severity: DiscrepancySeverity;
  description: string;
  is_typosquatting: boolean;
  similarity_score?: number;
  // Domain age validation fields (for domain_existence and domain_age fields)
  domain_exists?: boolean;
  domain_age_days?: number | null;
  domain_creation_date?: string | null;
  domain_registrar?: string | null;
}

export interface EmailChainValidationResult {
  total_discrepancies: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  discrepancies: EmailChainDiscrepancy[];
  summary: string;
  validated_at?: string;
}

export interface EmailChain {
  id: string;
  assessment_id: string;
  original_filename?: string;
  parsed_data?: EmailChainParsedData;
  validation_status: EmailChainValidationStatus;
  validation_result?: EmailChainValidationResult;
  validated_at?: string;
  created_at: string;
  created_by?: string;
  is_active: boolean;
}

export interface EmailChainListResponse {
  assessment_id: string;
  total_chains: number;
  pending_count: number;
  validated_count: number;
  suspicious_count: number;
  critical_count: number;
  chains: EmailChain[];
}

// ==================== Email Chain UI Config ====================

export interface EmailChainValidationStatusConfig {
  label: string;
  color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  bgColor: string;
  textColor: string;
}

export const EMAIL_CHAIN_VALIDATION_STATUS_CONFIG: Record<EmailChainValidationStatus, EmailChainValidationStatusConfig> = {
  pending: {
    label: 'Pendiente',
    color: 'warning',
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
  },
  validated: {
    label: 'Validado',
    color: 'success',
    bgColor: '#E0F7E6',
    textColor: '#2CA14D',
  },
  suspicious: {
    label: 'Sospechoso',
    color: 'warning',
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
  },
  critical: {
    label: 'Crítico',
    color: 'error',
    bgColor: '#FFE4E4',
    textColor: '#CC071E',
  },
};

export const EMAIL_CHAIN_FIELD_LABELS: Record<string, string> = {
  sender_domain: 'Dominio del Remitente',
  company_name: 'Nombre de Empresa',
  nit: 'NIT',
  representative_name: 'Representante Legal',
  official_document_domain: 'Dominio Email Documento Oficial',
  domain_existence: 'Existencia de Dominio',
  domain_age: 'Antigüedad de Dominio',
};

// ==================== Finalization Types ====================

export interface FinalizeEvaluationRequest {
  force_complete?: boolean;
}

export interface FinalizationRequirements {
  cross_validation_done: boolean;
  email_chains_validated: boolean;
  external_contacts_validated: boolean;
  min_documents_met: boolean;
}

export interface FinalizationStatus {
  assessment_id: string;
  can_finalize: boolean;
  requirements: FinalizationRequirements;
  pending_items: string[];
  current_status: AssessmentStatus;
}

export interface EvaluationRequirementsConfig {
  id?: string;
  require_cross_validation: boolean;
  require_email_chain_validation: boolean;
  require_external_contact_validation: boolean;
  min_documents_required: number;
  allow_force_complete: boolean;
  updated_at?: string;
  updated_by?: string;
}
