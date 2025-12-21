/**
 * Risk Management Types
 * TypeScript types for fraud detection and risk assessment
 */

// ==================== Enums as Union Types ====================

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type AssessmentStatus =
  | 'pending'
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

export type AssessmentType = 'comprehensive' | 'quick';

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
}

// ==================== Request/Response Types ====================

export interface RiskAssessmentRequest {
  client_nit: string;
  assessment_type?: AssessmentType;
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

export const ENTITY_TYPE_LABELS: Record<EntityType, string> = {
  nit: 'NIT',
  email_domain: 'Dominio de Email',
  company_name: 'Nombre de Empresa',
  person_id: 'Cédula',
  address: 'Dirección',
  phone: 'Teléfono',
};
