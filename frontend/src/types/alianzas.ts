/**
 * Alianzas (Partnerships) Module Types
 * Broker management, commission tracking, and payment types.
 */

// ==================== Broker Types ====================

/**
 * Broker type enum values
 */
export type TipoBroker = 'master_broker' | 'independiente' | 'aliado_logistico' | 'consultoria';

export const TipoBroker = {
  MASTER_BROKER: 'master_broker' as const,
  INDEPENDIENTE: 'independiente' as const,
  ALIADO_LOGISTICO: 'aliado_logistico' as const,
  CONSULTORIA: 'consultoria' as const,
};

/**
 * Broker type labels for display
 */
export const TIPO_BROKER_LABELS: Record<TipoBroker, string> = {
  master_broker: 'Master Broker',
  independiente: 'Independiente',
  aliado_logistico: 'Aliado Logístico',
  consultoria: 'Consultoría',
};

/**
 * Broker status enum values
 */
export type EstadoBroker = 'activo' | 'inactivo' | 'pendiente';

export const EstadoBroker = {
  ACTIVO: 'activo' as const,
  INACTIVO: 'inactivo' as const,
  PENDIENTE: 'pendiente' as const,
};

/**
 * Broker status labels for display
 */
export const ESTADO_BROKER_LABELS: Record<EstadoBroker, string> = {
  activo: 'Activo',
  inactivo: 'Inactivo',
  pendiente: 'Pendiente',
};

/**
 * Broker status colors for Chip components
 */
export const ESTADO_BROKER_COLORS: Record<EstadoBroker, 'success' | 'error' | 'warning'> = {
  activo: 'success',
  inactivo: 'error',
  pendiente: 'warning',
};

/**
 * Complete broker interface (matches BrokerResponse from backend)
 */
export interface Broker {
  id: string;
  nombre: string;
  tipo_broker: TipoBroker;
  master_broker_id?: string | null;
  porcentaje_apertura?: number | null;
  porcentaje_operativa?: number | null;
  cuenta_bancaria?: string | null;
  banco?: string | null;
  rfc?: string | null;
  fecha_contrato?: string | null;
  vigencia_contrato?: string | null;
  estado: EstadoBroker;
  link_expediente?: string | null;
  notas?: string | null;
  created_at: string;
  updated_at: string;
  created_by?: string | null;
}

/**
 * DTO for creating a new broker (matches BrokerCreate from backend)
 */
export interface BrokerCreateRequest {
  nombre: string;
  tipo_broker: TipoBroker;
  master_broker_id?: string | null;
  porcentaje_apertura?: number | null;
  porcentaje_operativa?: number | null;
  cuenta_bancaria?: string | null;
  banco?: string | null;
  rfc?: string | null;
  fecha_contrato?: string | null;
  vigencia_contrato?: string | null;
  estado?: EstadoBroker;
  link_expediente?: string | null;
  notas?: string | null;
}

/**
 * DTO for updating a broker (all fields optional)
 */
export interface BrokerUpdateRequest {
  nombre?: string;
  tipo_broker?: TipoBroker;
  master_broker_id?: string | null;
  porcentaje_apertura?: number | null;
  porcentaje_operativa?: number | null;
  cuenta_bancaria?: string | null;
  banco?: string | null;
  rfc?: string | null;
  fecha_contrato?: string | null;
  vigencia_contrato?: string | null;
  estado?: EstadoBroker;
  link_expediente?: string | null;
  notas?: string | null;
}

/**
 * Search parameters for broker search endpoint
 */
export interface BrokerSearchParams {
  nombre?: string;
  tipo_broker?: TipoBroker;
  estado?: EstadoBroker;
  rfc?: string;
  active_only?: boolean;
}

/**
 * Broker with sub-brokers list
 */
export interface BrokerWithSubBrokers extends Broker {
  sub_brokers: Broker[];
}

/**
 * Master broker option for dropdown selection
 */
export interface MasterBrokerOption {
  id: string;
  nombre: string;
  estado: EstadoBroker;
}

/**
 * Form data for broker create/edit form
 */
export interface BrokerFormData {
  nombre: string;
  tipo_broker: TipoBroker;
  master_broker_id: string;
  porcentaje_apertura: string;
  porcentaje_operativa: string;
  cuenta_bancaria: string;
  banco: string;
  rfc: string;
  fecha_contrato: string;
  vigencia_contrato: string;
  estado: EstadoBroker;
  link_expediente: string;
  notas: string;
}

/**
 * Default form values for new broker
 */
export const DEFAULT_BROKER_FORM_VALUES: BrokerFormData = {
  nombre: '',
  tipo_broker: TipoBroker.INDEPENDIENTE,
  master_broker_id: '',
  porcentaje_apertura: '',
  porcentaje_operativa: '',
  cuenta_bancaria: '',
  banco: '',
  rfc: '',
  fecha_contrato: '',
  vigencia_contrato: '',
  estado: EstadoBroker.ACTIVO,
  link_expediente: '',
  notas: '',
};


// ==================== Contract Extraction Types ====================

/**
 * Extraction method used for contract data
 */
export type ExtractionMethod = 'standard' | 'ai';

export const ExtractionMethod = {
  STANDARD: 'standard' as const,
  AI: 'ai' as const,
};

/**
 * AI extraction status for progress tracking
 */
export type AIExtractionStatus = 'idle' | 'uploading' | 'parsing' | 'extracting' | 'complete' | 'error';

export const AIExtractionStatus = {
  IDLE: 'idle' as const,
  UPLOADING: 'uploading' as const,
  PARSING: 'parsing' as const,
  EXTRACTING: 'extracting' as const,
  COMPLETE: 'complete' as const,
  ERROR: 'error' as const,
};

/**
 * AI extraction status labels for display
 */
export const AI_EXTRACTION_STATUS_LABELS: Record<AIExtractionStatus, string> = {
  idle: 'Listo',
  uploading: 'Subiendo documento...',
  parsing: 'Convirtiendo a texto (IA)...',
  extracting: 'Extrayendo datos (IA)...',
  complete: 'Completado',
  error: 'Error',
};

/**
 * Extracted broker contract data from document processing
 */
export interface BrokerContractData {
  nombre_broker?: string | null;
  porcentaje_comision_apertura?: number | null;
  porcentaje_comision_operativa?: number | null;
  fecha_contrato?: string | null;
  vigencia_meses?: number | null;
  rfc_broker?: string | null;
  cuenta_bancaria?: string | null;
  banco?: string | null;
  extraction_method: ExtractionMethod;
  extraction_confidence?: number | null;
  raw_text_preview?: string | null;
}


// ==================== Exchange Rate Types ====================

/**
 * Response from Banxico USD/MXN exchange rate endpoint
 * Matches TipoCambioResponse from backend
 */
export interface TipoCambioResponse {
  /** Exchange rate (MXN per USD) */
  tipo_cambio: number;
  /** Date of the exchange rate in ISO format (YYYY-MM-DD) */
  fecha: string;
  /** Data source description */
  fuente: string;
}


// ==================== Commission Types ====================

/**
 * Commission type enum values
 */
export type TipoComision = 'apertura' | 'operativa';

export const TipoComision = {
  APERTURA: 'apertura' as const,
  OPERATIVA: 'operativa' as const,
};

/**
 * Commission type labels for display
 */
export const TIPO_COMISION_LABELS: Record<TipoComision, string> = {
  apertura: 'Apertura',
  operativa: 'Operativa',
};

/**
 * Commission status enum values
 */
export type EstadoComision = 'calculado' | 'aprobado' | 'pagado';

export const EstadoComision = {
  CALCULADO: 'calculado' as const,
  APROBADO: 'aprobado' as const,
  PAGADO: 'pagado' as const,
};

/**
 * Commission status labels for display
 */
export const ESTADO_COMISION_LABELS: Record<EstadoComision, string> = {
  calculado: 'Calculado',
  aprobado: 'Aprobado',
  pagado: 'Pagado',
};

/**
 * Commission status colors for Chip components
 */
export const ESTADO_COMISION_COLORS: Record<EstadoComision, 'warning' | 'success' | 'info'> = {
  calculado: 'warning',
  aprobado: 'success',
  pagado: 'info',
};

/**
 * Input for commission calculation (matches ComisionInput from backend)
 */
export interface ComisionInput {
  broker_id: string;
  tipo_comision: TipoComision;
  cliente_nombre?: string | null;
  cliente_nit?: string | null;
  // Apertura-specific fields
  linea_credito?: number | null;
  porcentaje_comision_cliente?: number | null;
  cliente_pago_pct?: number | null;
  // Operativa-specific fields
  operaciones_mes?: number | null;
  // Optional period override
  periodo_mes?: number | null;
  periodo_anio?: number | null;
  // Optional exchange rate date override
  fecha_tipo_cambio?: string | null;
  // Optional notes
  notas?: string | null;
}

/**
 * Calculated commission result (matches ComisionCalculada from backend)
 */
export interface ComisionCalculada {
  // Broker reference
  broker_id: string;
  broker_nombre?: string | null;
  // Period
  periodo_mes: number;
  periodo_anio: number;
  // Client information
  cliente_nombre?: string | null;
  cliente_nit?: string | null;
  // Commission type
  tipo_comision: TipoComision;
  // Apertura calculation details
  linea_credito?: number | null;
  porcentaje_comision_cliente?: number | null;
  monto_comision_cliente?: number | null;
  cliente_pago_pct?: number | null;
  // Operativa calculation details
  operaciones_mes?: number | null;
  // Broker commission
  porcentaje_broker: number;
  monto_broker_usd: number;
  // Currency conversion
  tipo_cambio: number;
  monto_broker_mxn: number;
  // Status
  estado: EstadoComision;
  // Notes
  notas?: string | null;
  // Metadata (only present when saved)
  id?: string | null;
  created_at?: string | null;
  created_by?: string | null;
}

/**
 * Input for batch commission calculation
 */
export interface ComisionBatchInput {
  comisiones: ComisionInput[];
  guardar: boolean;
}

/**
 * Response from batch commission calculation
 */
export interface ComisionBatchResponse {
  comisiones: ComisionCalculada[];
  total_usd: number;
  total_mxn: number;
  guardadas: boolean;
}

/**
 * Response for commission list by period
 */
export interface ComisionListResponse {
  comisiones: ComisionCalculada[];
  total: number;
  periodo_mes: number;
  periodo_anio: number;
}

/**
 * Broker commission summary for a period (matches ComisionResumenBroker from backend)
 */
export interface ComisionResumenBroker {
  broker_id: string;
  broker_nombre: string;
  periodo_mes: number;
  periodo_anio: number;
  total_apertura_usd: number;
  total_apertura_mxn: number;
  total_operativa_usd: number;
  total_operativa_mxn: number;
  total_usd: number;
  total_mxn: number;
  num_comisiones: number;
}

/**
 * DTO for updating commission status
 */
export interface ComisionEstadoUpdate {
  estado: EstadoComision;
}

/**
 * Form data for commission input form
 * Uses strings for numeric fields to work with react-hook-form
 */
export interface ComisionFormData {
  broker_id: string;
  tipo_comision: TipoComision;
  cliente_nombre: string;
  cliente_nit: string;
  // Apertura fields
  linea_credito: string;
  porcentaje_comision_cliente: string;
  cliente_pago_pct: string;
  // Operativa fields
  operaciones_mes: string;
  // Notes
  notas: string;
}

/**
 * Default form values for new commission
 */
export const DEFAULT_COMISION_FORM_VALUES: ComisionFormData = {
  broker_id: '',
  tipo_comision: TipoComision.APERTURA,
  cliente_nombre: '',
  cliente_nit: '',
  linea_credito: '',
  porcentaje_comision_cliente: '',
  cliente_pago_pct: '100',
  operaciones_mes: '',
  notas: '',
};


// ==================== Payment Types ====================

/**
 * Payment status enum values
 */
export type EstadoPago = 'pendiente' | 'programado' | 'pagado';

export const EstadoPago = {
  PENDIENTE: 'pendiente' as const,
  PROGRAMADO: 'programado' as const,
  PAGADO: 'pagado' as const,
};

/**
 * Payment status labels for display
 */
export const ESTADO_PAGO_LABELS: Record<EstadoPago, string> = {
  pendiente: 'Pendiente',
  programado: 'Programado',
  pagado: 'Pagado',
};

/**
 * Payment status colors for Chip components
 */
export const ESTADO_PAGO_COLORS: Record<EstadoPago, 'warning' | 'info' | 'success'> = {
  pendiente: 'warning',
  programado: 'info',
  pagado: 'success',
};

/**
 * Payment response from API (matches PagoResponse from backend)
 */
export interface Pago {
  id: string;
  broker_id: string;
  broker_nombre?: string | null;
  periodo_mes: number;
  periodo_anio: number;
  total_usd: number;
  total_mxn: number;
  tipo_cambio: number;
  fecha_programada?: string | null;
  fecha_pago?: string | null;
  estado: EstadoPago;
  comprobante_url?: string | null;
  factura_broker_url?: string | null;
  notas?: string | null;
  created_at: string;
  approved_by?: string | null;
}

/**
 * Paginated payment list response
 */
export interface PagoListResponse {
  pagos: Pago[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * DTO for updating payment status
 */
export interface PagoEstadoUpdate {
  estado: EstadoPago;
  fecha_pago?: string | null;
  comprobante_url?: string | null;
}

/**
 * Request for approving commissions
 */
export interface ComisionAprobacionRequest {
  periodo_mes: number;
  periodo_anio: number;
}

/**
 * Response from commission approval
 */
export interface ComisionAprobacionResponse {
  periodo_mes: number;
  periodo_anio: number;
  comisiones_aprobadas: number;
  pagos_creados: number;
  total_usd: number;
  total_mxn: number;
  brokers_ids: string[];
  message: string;
}
