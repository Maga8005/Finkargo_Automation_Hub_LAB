"""
Risk Management - Data Transfer Objects (DTOs)
Pydantic models for fraud detection and risk assessment system
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ==================== Enums ====================

class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssessmentStatus(str, Enum):
    """Risk assessment status"""
    PENDING = "pending"
    PENDING_DOCUMENTS = "pending_documents"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    APPROVED = "approved"
    REJECTED = "rejected"


class AlertSeverity(str, Enum):
    """Alert severity level"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert type classification"""
    NEW_CRITICAL = "new_critical"
    ESCALATION = "escalation"
    THRESHOLD_BREACH = "threshold_breach"
    BLACKLIST_MATCH = "blacklist_match"
    REVIEW_REQUIRED = "review_required"


class EntityType(str, Enum):
    """Blacklist entity type"""
    NIT = "nit"
    EMAIL_DOMAIN = "email_domain"
    COMPANY_NAME = "company_name"
    PERSON_ID = "person_id"
    ADDRESS = "address"
    PHONE = "phone"


class RuleType(str, Enum):
    """Fraud detection rule type"""
    IDENTITY = "identity"
    EMAIL = "email"
    DOCUMENT = "document"
    NIT = "nit"
    ADDRESS = "address"
    FINANCIAL = "financial"
    HISTORY = "history"


class VerificationStatus(str, Enum):
    """Binary verification status for risk assessments"""
    PASS = "pass"
    REQUIRES_MANUAL_VERIFICATION = "requires_manual_verification"


# NOTE: AssessmentType enum removed as per bug fix - only one evaluation workflow exists
# Existing database records may have assessment_type values; handled via response model defaults


# ==================== Fraud Indicator Models ====================

class FraudIndicator(BaseModel):
    """Individual fraud indicator result"""
    indicator_name: str = Field(..., description="Name of the fraud indicator")
    indicator_value: bool = Field(..., description="True if indicator triggered (fraud signal)")
    severity: RiskLevel = Field(..., description="Severity level of this indicator")
    evidence: Optional[str] = Field(None, description="Supporting evidence or details")
    score_impact: Decimal = Field(..., ge=0, le=100, description="Impact on overall risk score (0-100)")

    @validator('score_impact', pre=True)
    def coerce_score_impact(cls, v):
        """Convert to Decimal"""
        if v is None:
            return Decimal('0')
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


# ==================== Risk Assessment DTOs ====================

class RiskAssessmentRequest(BaseModel):
    """Request to create a new risk evaluation"""
    client_nit: str = Field(..., min_length=5, max_length=50, description="Client NIT to evaluate")
    # NOTE: assessment_type removed - only comprehensive evaluation workflow exists

    @validator('client_nit')
    def validate_nit(cls, v):
        """Validate NIT is not empty"""
        if not v or not v.strip():
            raise ValueError('client_nit cannot be empty')
        return v.strip()


class RiskAssessmentResponse(BaseModel):
    """Response after creating a risk evaluation"""
    id: str
    assessment_id: str = Field(..., description="Business ID (RISK-YYYY-NNN)")
    client_nit: str
    risk_level: RiskLevel
    risk_score: Decimal = Field(..., ge=0, le=100)
    fraud_indicators: List[FraudIndicator]
    status: AssessmentStatus
    assessment_type: str
    created_at: datetime
    # Binary verification status fields
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PASS,
        description="Binary pass/fail status based on discrepancies"
    )
    has_discrepancies: bool = Field(
        default=False,
        description="Whether any cross-validation discrepancies were found"
    )
    discrepancy_count: int = Field(
        default=0,
        description="Count of discrepancies found in cross-validation"
    )

    class Config:
        from_attributes = True

    @validator('risk_score', pre=True)
    def coerce_risk_score(cls, v):
        """Convert to Decimal"""
        if v is None:
            return Decimal('0')
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class ClientInfo(BaseModel):
    """Client information snapshot for risk detail"""
    nit: str
    nombre_importador: Optional[str] = None
    representante_legal: Optional[str] = None
    ciudad_domicilio: Optional[str] = None
    cupo_plataforma: Optional[Decimal] = None


class RiskAssessmentDetail(RiskAssessmentResponse):
    """Detailed risk assessment with additional info"""
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    client_info: Optional[ClientInfo] = None
    client_data_snapshot: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskDecisionRequest(BaseModel):
    """Request to submit a decision on a risk assessment"""
    status: AssessmentStatus = Field(
        ...,
        description="New status (approved, rejected, or escalated)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Review notes explaining the decision"
    )

    @validator('status')
    def validate_status(cls, v):
        """Only allow decision statuses"""
        allowed = [AssessmentStatus.APPROVED, AssessmentStatus.REJECTED, AssessmentStatus.ESCALATED]
        if v not in allowed:
            raise ValueError(f'Status must be one of: {", ".join([s.value for s in allowed])}')
        return v


# ==================== Statistics DTOs ====================

class RiskStatsResponse(BaseModel):
    """Risk dashboard statistics"""
    total_assessments: int = Field(default=0)
    pending_review: int = Field(default=0)
    in_progress: int = Field(default=0)
    completed: int = Field(default=0)
    escalated: int = Field(default=0)
    approved: int = Field(default=0)
    rejected: int = Field(default=0)
    low_risk_count: int = Field(default=0)
    medium_risk_count: int = Field(default=0)
    high_risk_count: int = Field(default=0)
    critical_risk_count: int = Field(default=0)
    assessed_today: int = Field(default=0)
    assessed_this_week: int = Field(default=0)
    approval_rate: Optional[Decimal] = Field(default=None, description="Percentage of approved assessments")
    rejection_rate: Optional[Decimal] = Field(default=None, description="Percentage of rejected assessments")
    # Binary verification status counts
    pass_count: int = Field(default=0, description="Count of assessments with PASS verification status")
    requires_verification_count: int = Field(default=0, description="Count of assessments requiring manual verification")


# ==================== Fraud Detection Rules DTOs ====================

class FraudDetectionRuleResponse(BaseModel):
    """Fraud detection rule configuration"""
    id: str
    rule_name: str
    rule_type: RuleType
    description: Optional[str] = None
    weight: Decimal = Field(..., ge=0, le=1)
    threshold: Decimal = Field(..., ge=0, le=100)
    is_active: bool
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @validator('weight', pre=True)
    def coerce_weight(cls, v):
        """Convert to Decimal"""
        if v is None:
            return Decimal('0')
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @validator('threshold', pre=True)
    def coerce_threshold(cls, v):
        """Convert to Decimal"""
        if v is None:
            return Decimal('50')
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class RuleUpdateRequest(BaseModel):
    """Request to update a fraud detection rule"""
    weight: Optional[Decimal] = Field(None, ge=0, le=1, description="Rule weight (0.00-1.00)")
    threshold: Optional[Decimal] = Field(None, ge=0, le=100, description="Threshold value (0-100)")
    is_active: Optional[bool] = Field(None, description="Enable/disable rule")
    config: Optional[Dict[str, Any]] = Field(None, description="Rule-specific configuration")

    @validator('weight', pre=True)
    def coerce_weight(cls, v):
        """Convert to Decimal"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @validator('threshold', pre=True)
    def coerce_threshold(cls, v):
        """Convert to Decimal"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


# ==================== Blacklist DTOs ====================

class BlacklistEntryRequest(BaseModel):
    """Request to add an entity to the blacklist"""
    entity_type: EntityType = Field(..., description="Type of entity being blacklisted")
    entity_value: str = Field(..., min_length=1, max_length=500, description="The value to blacklist")
    reason: str = Field(..., min_length=5, max_length=1000, description="Reason for blacklisting")

    @validator('entity_value')
    def validate_entity_value(cls, v):
        """Validate entity value is not empty"""
        if not v or not v.strip():
            raise ValueError('entity_value cannot be empty')
        return v.strip()


class BlacklistEntryResponse(BaseModel):
    """Blacklist entry response"""
    id: str
    entity_type: EntityType
    entity_value: str
    reason: str
    source: Optional[str] = Field(default="manual")
    added_by: Optional[str] = None
    added_by_name: Optional[str] = None
    added_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


# ==================== Alert DTOs ====================

class RiskAlertResponse(BaseModel):
    """Risk alert response"""
    id: str
    assessment_id: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    is_read: bool
    read_by: Optional[str] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCreateRequest(BaseModel):
    """Request to create an alert (internal use)"""
    assessment_id: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., max_length=200)
    message: str


# ==================== Query Filter DTOs ====================

class RiskAssessmentFilter(BaseModel):
    """Filter parameters for risk assessment queries"""
    status: Optional[AssessmentStatus] = None
    risk_level: Optional[RiskLevel] = None
    client_nit: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    assessed_by: Optional[str] = None
    limit: int = Field(default=50, le=100, ge=1)
    offset: int = Field(default=0, ge=0)


class BlacklistFilter(BaseModel):
    """Filter parameters for blacklist queries"""
    entity_type: Optional[EntityType] = None
    is_active: Optional[bool] = True
    limit: int = Field(default=50, le=100, ge=1)
    offset: int = Field(default=0, ge=0)


# ==================== Document Extraction DTOs ====================

class DocumentType(str, Enum):
    """Document types for fraud detection cross-validation"""
    FINANCIAL_STATEMENT_CURRENT = "financial_statement_current"
    FINANCIAL_STATEMENT_PRIOR = "financial_statement_prior"
    CEDULA = "cedula"
    COMPOSICION_ACCIONARIA = "composicion_accionaria"
    RUT = "rut"
    CERTIFICADO_EXISTENCIA = "certificado_existencia"


class ExtractionStatus(str, Enum):
    """Status of document extraction"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DiscrepancySeverity(str, Enum):
    """Severity level of cross-validation discrepancy"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationType(str, Enum):
    """Type of cross-validation check"""
    COMPANY_NAME = "company_name"
    NIT = "nit"
    NIT_CHECK_DIGIT = "nit_check_digit"  # Separate validation for check digit mismatches
    LEGAL_REPRESENTATIVE = "legal_representative"
    SHAREHOLDERS = "shareholders"
    FINANCIAL_CONTINUITY = "financial_continuity"
    EMAIL_DOMAIN = "email_domain"
    TYPOSQUATTING = "typosquatting"  # Domain typosquatting detection
    PROVIDER_DOMAIN = "provider_domain"  # Free email provider detection
    ADDRESS = "address"
    DOMAIN_EXISTENCE = "domain_existence"  # DNS lookup validation
    DOMAIN_AGE = "domain_age"  # WHOIS domain age validation


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    id: str
    assessment_id: str
    document_type: DocumentType
    document_filename: str
    extraction_status: ExtractionStatus
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentExtractionResponse(BaseModel):
    """Response containing extracted document data"""
    id: str
    assessment_id: str
    document_type: DocumentType
    document_filename: str
    extraction_status: ExtractionStatus
    extraction_method: str = "landingai"
    extraction_confidence: Optional[Decimal] = None
    extracted_data: Optional[Dict[str, Any]] = None
    extraction_errors: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @validator('extraction_confidence', pre=True)
    def coerce_confidence(cls, v):
        """Convert to Decimal"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class CrossValidationResult(BaseModel):
    """Individual cross-validation result"""
    id: Optional[str] = None
    validation_type: ValidationType
    documents_compared: List[str]
    field_compared: Optional[str] = None
    values_found: Dict[str, Any]
    is_discrepancy: bool = False
    severity: Optional[DiscrepancySeverity] = None
    description: Optional[str] = None
    score_impact: Decimal = Field(default=Decimal('0'), ge=0, le=100)

    class Config:
        from_attributes = True

    @validator('score_impact', pre=True)
    def coerce_score_impact(cls, v):
        """Convert to Decimal"""
        if v is None:
            return Decimal('0')
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class CrossValidationResponse(BaseModel):
    """Response containing all cross-validation results for an assessment"""
    assessment_id: str
    total_discrepancies: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_score_impact: Decimal = Field(default=Decimal('0'))
    results: List[CrossValidationResult] = []
    validated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @validator('total_score_impact', pre=True)
    def coerce_total_score_impact(cls, v):
        """Convert to Decimal"""
        if v is None:
            return Decimal('0')
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


class DocumentExtractionListResponse(BaseModel):
    """Response containing all document extractions for an assessment"""
    assessment_id: str
    total_documents: int = 0
    pending_count: int = 0
    processing_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    extractions: List[DocumentExtractionResponse] = []


class TriggerExtractionResponse(BaseModel):
    """Response after triggering extraction for all documents"""
    assessment_id: str
    documents_queued: int
    message: str


class TriggerValidationResponse(BaseModel):
    """Response after triggering cross-validation"""
    assessment_id: str
    validation_status: str
    discrepancies_found: int
    message: str


# ==================== External Contact DTOs ====================

class ExternalContactValidationStatus(str, Enum):
    """Status of external contact email validation"""
    PENDING = "pending"
    VALIDATED = "validated"
    SUSPICIOUS = "suspicious"
    CRITICAL = "critical"


class ExternalContactRequest(BaseModel):
    """Request to create a new external contact"""
    email: str = Field(..., min_length=5, max_length=255, description="Email address to validate")
    sender_name: Optional[str] = Field(None, max_length=255, description="Name of the sender")
    source: str = Field(default="comercial_team", max_length=100, description="Source of the email")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")

    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        v = v.strip().lower()
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v


class EmailValidationResult(BaseModel):
    """Result of email domain typosquatting validation"""
    is_suspicious: bool = Field(..., description="Whether the domain appears suspicious")
    similar_domain: Optional[str] = Field(None, description="The legitimate domain it's similar to")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1)")
    levenshtein_distance: int = Field(..., ge=0, description="Edit distance from similar domain")
    detection_type: str = Field(..., description="Type of detection: typosquatting, tld_variation, provider_domain, exact_match, no_match")
    description: str = Field(..., description="Human-readable description")
    is_free_provider: bool = Field(default=False, description="Whether using a free email provider")
    # Domain existence and age validation fields
    domain_exists: Optional[bool] = Field(None, description="Whether the domain resolves via DNS (null = unknown/pending)")
    domain_age_days: Optional[int] = Field(None, description="Age of domain in days (null = unavailable)")
    domain_creation_date: Optional[datetime] = Field(None, description="Domain creation date from WHOIS (null = unavailable)")
    age_lookup_status: str = Field(default="pending", description="Status of age lookup: success, failed, unavailable, pending")
    domain_registrar: Optional[str] = Field(None, description="Domain registrar from WHOIS (null = unavailable)")


class ExternalContactResponse(BaseModel):
    """Response for an external contact record"""
    id: str
    assessment_id: str
    email: str
    sender_name: Optional[str] = None
    source: str
    validation_status: ExternalContactValidationStatus
    validation_result: Optional[EmailValidationResult] = None
    validated_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class ExternalContactListResponse(BaseModel):
    """Response containing all external contacts for an assessment"""
    assessment_id: str
    total_contacts: int = 0
    pending_count: int = 0
    validated_count: int = 0
    suspicious_count: int = 0
    critical_count: int = 0
    contacts: List[ExternalContactResponse] = []


# ==================== Email Chain DTOs ====================

class EmailChainValidationStatus(str, Enum):
    """Status of email chain validation"""
    PENDING = "pending"
    VALIDATED = "validated"
    SUSPICIOUS = "suspicious"
    CRITICAL = "critical"


class EmailMessage(BaseModel):
    """Individual email message in a chain"""
    sender_email: str = Field(..., description="Sender email address")
    sender_name: Optional[str] = Field(None, description="Sender display name")
    sender_domain: str = Field(..., description="Sender email domain")
    date: Optional[str] = Field(None, description="Email date in ISO format")
    subject: Optional[str] = Field(None, description="Email subject line")
    body_excerpt: Optional[str] = Field(None, max_length=2000, description="First 2000 chars of body")


class ExtractedMentions(BaseModel):
    """Data extracted from email body content"""
    company_names: List[str] = Field(default_factory=list, description="Company names mentioned in email body")
    nits: List[str] = Field(default_factory=list, description="NITs mentioned in email body")
    representative_names: List[str] = Field(default_factory=list, description="Representative names mentioned")
    domains: List[str] = Field(default_factory=list, description="All email domains found")


class EmailChainParsedData(BaseModel):
    """Parsed data from email chain"""
    messages: List[EmailMessage] = Field(default_factory=list, description="Parsed email messages")
    mentions: ExtractedMentions = Field(default_factory=ExtractedMentions, description="Extracted mentions from body")
    parse_errors: List[str] = Field(default_factory=list, description="Any parsing errors encountered")


class EmailChainDiscrepancy(BaseModel):
    """Individual discrepancy found during email chain validation"""
    field: str = Field(..., description="Field being compared (sender_domain, company_name, nit, rep_name)")
    email_value: str = Field(..., description="Value found in email")
    document_value: Optional[str] = Field(None, description="Value from documents for comparison")
    severity: DiscrepancySeverity = Field(..., description="Severity level of the discrepancy")
    description: str = Field(..., description="Human-readable description")
    is_typosquatting: bool = Field(default=False, description="Whether typosquatting was detected")
    similarity_score: Optional[float] = Field(None, ge=0, le=1, description="Similarity score if applicable")


class EmailChainValidationResult(BaseModel):
    """Full validation result for an email chain"""
    total_discrepancies: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    discrepancies: List[EmailChainDiscrepancy] = Field(default_factory=list)
    summary: str = Field(default="", description="Summary of validation results")
    validated_at: Optional[datetime] = None


class EmailChainUploadRequest(BaseModel):
    """Request to upload an email chain (text content only, file handled separately)"""
    text_content: Optional[str] = Field(None, max_length=512000, description="Raw email text (up to 500KB)")

    @validator('text_content')
    def validate_content(cls, v):
        """Validate text content is not empty if provided"""
        if v is not None and not v.strip():
            raise ValueError('text_content cannot be empty if provided')
        return v


class EmailChainResponse(BaseModel):
    """Response for an email chain record"""
    id: str
    assessment_id: str
    original_filename: Optional[str] = None
    parsed_data: Optional[EmailChainParsedData] = None
    validation_status: EmailChainValidationStatus = EmailChainValidationStatus.PENDING
    validation_result: Optional[EmailChainValidationResult] = None
    validated_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class EmailChainListResponse(BaseModel):
    """Response containing all email chains for an assessment"""
    assessment_id: str
    total_chains: int = 0
    pending_count: int = 0
    validated_count: int = 0
    suspicious_count: int = 0
    critical_count: int = 0
    chains: List[EmailChainResponse] = []
