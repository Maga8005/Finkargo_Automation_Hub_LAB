"""
Legal Contract Automation - Data Transfer Objects (DTOs)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ContractType(str, Enum):
    """Contract type enum"""
    ACTIVOS = "activos"
    OTROSI = "otrosi"
    INVENTARIO_BODEGA = "inventario_bodega"

    # Paga Local Colombia - Contratos Cuenta Cliente - Aval Persona Jurídica
    PL_CO_CREDITO_AVAL_PJ = "pl_co_credito_aval_pj"
    PL_CO_MANDATO_PJ = "pl_co_mandato_pj"

    # Paga Local Colombia - Contratos Cuenta Cliente - Aval Persona Natural
    PL_CO_CREDITO_AVAL_PN = "pl_co_credito_aval_pn"
    PL_CO_MANDATO_PN = "pl_co_mandato_pn"

    # Paga Local Colombia - Contratos Cuenta Cliente - Sin Aval
    PL_CO_CREDITO_NO_AVAL = "pl_co_credito_no_aval"
    PL_CO_MANDATO_NO_AVAL = "pl_co_mandato_no_aval"

    # Paga Local Colombia - Documentos Operación
    PL_CO_MANDATO_IM = "pl_co_mandato_im"
    PL_CO_SOLICITUD_DESEMBOLSO = "pl_co_solicitud_desembolso"
    PL_CO_DIAN_MANDATO_IM = "pl_co_dian_mandato_im"


class ContractStatus(str, Enum):
    """Contract status enum"""
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ImportStatus(str, Enum):
    """Data import status enum"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== Client DTOs ====================

class ClientBase(BaseModel):
    """Base client data"""
    nit: str = Field(..., min_length=5, max_length=20, description="Colombian tax ID")
    nombre_importador: str = Field(..., min_length=1, max_length=255)
    representante_legal: str = Field(..., min_length=1, max_length=255)
    cedula_representante: str = Field(..., min_length=1, max_length=50)
    ciudad_domicilio: str = Field(..., min_length=1, max_length=100)
    cupo_plataforma: Decimal = Field(..., description="Credit limit from platform (negative values indicate placeholder/incomplete records)")
    # New optional fields for contract template
    direccion_comercial: Optional[str] = None
    tipo_identificacion_representante: Optional[str] = Field(default='CC', max_length=10)
    nombre_contrato_marco: Optional[str] = Field(default='Compra de Cartera', max_length=100)
    kam_nombre: Optional[str] = None
    kam_email: Optional[str] = None
    destinatario_nombre: Optional[str] = None
    destinatario_email: Optional[str] = None

    @validator('cupo_plataforma', pre=True)
    def coerce_cupo_plataforma(cls, v):
        """Convert string or float to Decimal"""
        if v is None:
            raise ValueError('cupo_plataforma cannot be None')
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        raise ValueError(f'Invalid type for cupo_plataforma: {type(v)}')


class ClientCreate(ClientBase):
    """Client creation request"""
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    """Client update request"""
    nombre_importador: Optional[str] = None
    representante_legal: Optional[str] = None
    cedula_representante: Optional[str] = None
    ciudad_domicilio: Optional[str] = None
    cupo_plataforma: Optional[Decimal] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ClientResponse(ClientBase):
    """Client response"""
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ClientSearchRequest(BaseModel):
    """Client search parameters"""
    query: Optional[str] = Field(None, description="Search by NIT or name")
    nit: Optional[str] = None
    nombre: Optional[str] = None
    is_active: Optional[bool] = True


# ==================== Contract Generation DTOs ====================

class CustodianData(BaseModel):
    """Custodian operator data extracted from RUT document (for Inventario Bodega contracts)"""
    nombre_operador_custodio: str
    ciudad_domicilio_custodio: str
    nit_operador_custodio: str
    nombre_representante_legal_custodio: str
    email_operador_custodio: str
    cc_representante_legal_custodio: str
    tipo_identificacion_representante_legal_custodio: str  # e.g., "CC", "CE", "Pasaporte"

    @validator('email_operador_custodio')
    def validate_email(cls, v):
        """Basic email validation"""
        if '@' not in v or '.' not in v:
            raise ValueError(f"Invalid email format: {v}")
        return v.lower()


class ContractGenerationRequest(BaseModel):
    """Request to generate a contract"""
    client_nit: str = Field(..., description="Client NIT to generate contract for")
    contract_type: ContractType = Field(default=ContractType.ACTIVOS, description="Type of contract to generate")
    custodian_data: Optional[CustodianData] = Field(None, description="Custodian data from RUT (required for Inventario Bodega)")

    @validator('client_nit')
    def validate_nit(cls, v):
        if not v or len(v) < 5:
            raise ValueError('NIT must be at least 5 characters')
        return v


class ClientDataSnapshot(BaseModel):
    """Snapshot of client data at time of generation"""
    nit: str
    nombre_importador: str
    representante_legal: str
    cedula_representante: str
    ciudad_domicilio: str
    cupo_plataforma: Decimal
    contract_id: str
    contract_type: str
    generation_date: str
    # Additional fields for contract template
    direccion_comercial: Optional[str] = None
    tipo_identificacion_representante: Optional[str] = 'CC'
    nombre_contrato_marco: Optional[str] = 'Compra de Cartera'
    kam_nombre: Optional[str] = None
    kam_email: Optional[str] = None
    destinatario_nombre: Optional[str] = None
    destinatario_email: Optional[str] = None
    # Custodian fields (for Inventario Bodega contracts)
    nombre_operador_custodio: Optional[str] = None
    ciudad_domicilio_custodio: Optional[str] = None
    nit_operador_custodio: Optional[str] = None
    nombre_representante_legal_custodio: Optional[str] = None
    email_operador_custodio: Optional[str] = None
    cc_representante_legal_custodio: Optional[str] = None
    tipo_identificacion_representante_legal_custodio: Optional[str] = None


class ContractGenerationResponse(BaseModel):
    """Response after contract generation"""
    id: str
    contract_id: str
    contract_type: str
    client_nit: str
    status: ContractStatus
    generated_at: datetime
    pdf_url: Optional[str] = None
    approved_document_url: Optional[str] = None
    data_snapshot: Dict[str, Any]

    class Config:
        from_attributes = True


class ContractGenerationDetail(BaseModel):
    """Detailed contract generation record"""
    id: str
    contract_id: str
    contract_type: str
    client_nit: str
    status: ContractStatus
    generated_by: Optional[str] = None  # Nullable until auth is implemented
    generated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    pdf_url: Optional[str] = None
    approved_document_url: Optional[str] = None
    template_version: str
    data_snapshot: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Contract Review DTOs ====================

class ContractReviewAction(str, Enum):
    """Review action enum"""
    APPROVE = "approve"
    REJECT = "reject"


class ContractReviewRequest(BaseModel):
    """Request to review a contract"""
    action: ContractReviewAction = Field(..., description="approve or reject")
    notes: Optional[str] = Field(None, max_length=1000, description="Review comments")


class ContractReviewResponse(BaseModel):
    """Response after contract review"""
    contract_id: str
    status: ContractStatus
    reviewed_by: Optional[str] = None  # Nullable until auth is implemented
    reviewed_at: Optional[datetime] = None  # Nullable until auth is implemented
    review_notes: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Template DTOs ====================

class ContractTemplateCreate(BaseModel):
    """Create new contract template"""
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$', description="Semantic version (e.g., 1.0.0)")
    contract_type: str = Field(default="activos", max_length=50)
    template_content: str = Field(..., min_length=1)
    notes: Optional[str] = None


class ContractTemplateResponse(BaseModel):
    """Contract template response"""
    id: str
    version: str
    contract_type: str
    template_content: str
    active: bool
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Data Import DTOs ====================

class DataImportResponse(BaseModel):
    """Data import result"""
    id: str
    file_name: str
    total_rows: Optional[int] = None
    successful_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    error_log: Optional[Dict[str, Any]] = None
    status: ImportStatus
    imported_at: datetime

    class Config:
        from_attributes = True


class BulkImportResult(BaseModel):
    """Result of bulk client import"""
    total_processed: int
    successful: int
    failed: int
    errors: list[str] = []
    import_id: str


# ==================== History and Stats DTOs ====================

class ContractHistoryFilter(BaseModel):
    """Filter parameters for contract history"""
    status: Optional[ContractStatus] = None
    client_nit: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)


class ContractStats(BaseModel):
    """Contract generation statistics"""
    total_generated: int
    pending_review: int
    approved: int
    rejected: int
    generated_today: int
    generated_this_week: int
    generated_this_month: int


# ==================== Solicitud de Desembolso DTOs ====================

class AnexoItem(BaseModel):
    """Single row item in Anexo I table for Solicitud de Desembolso"""
    acreedor: str = Field(..., min_length=1, max_length=255, description="Creditor name")
    numero_instrumento: str = Field(..., min_length=1, max_length=100, description="Instrument number")
    monto: Decimal = Field(..., description="Amount in COP")

    @validator('monto')
    def validate_monto(cls, v):
        """Validate that monto is positive"""
        if v <= 0:
            raise ValueError('monto must be greater than 0')
        return v


class CotizacionData(BaseModel):
    """Data extracted from Cotización PDF document"""
    numero_cotizacion: str = Field(..., description="Quote number (format: CO:NIT:seq:type:DOM)")
    fecha_cotizacion: Optional[str] = Field(None, description="Quote date from PDF")
    fecha_contrato_credito: Optional[str] = Field(None, description="Credit contract date from PDF")
    representante_legal: Optional[str] = Field(None, description="Legal representative name")
    tipo_id_representante: Optional[str] = Field(None, description="ID type (e.g., CC, CE)")
    numero_id_representante: Optional[str] = Field(None, description="ID number")
    anexo_items: list[AnexoItem] = Field(default_factory=list, description="List of Anexo I table items")
    monto_total: Decimal = Field(..., description="Total amount calculated from anexo items")

    @validator('monto_total')
    def validate_monto_total(cls, v):
        """Validate that total is positive"""
        if v <= 0:
            raise ValueError('monto_total must be greater than 0')
        return v


class SolicitudDesembolsoRequest(BaseModel):
    """Request to generate Solicitud de Desembolso contract"""
    client_nit: str = Field(..., min_length=5, max_length=20, description="Client NIT")
    numero_cotizacion_desembolso: str = Field(..., min_length=1, max_length=100, description="Disbursement quote number")
    fecha_contrato_credito: str = Field(..., description="Credit contract date (ISO format)")
    monto: Decimal = Field(..., description="Total disbursement amount in COP")
    dias_plazo: int = Field(default=120, ge=30, le=180, description="Term in days (30-180)")
    anexo_items: list[AnexoItem] = Field(..., min_items=1, description="At least one Anexo I item required")

    @validator('client_nit')
    def validate_client_nit(cls, v):
        """Validate NIT is not empty"""
        if not v or not v.strip():
            raise ValueError('client_nit cannot be empty')
        return v.strip()

    @validator('monto')
    def validate_monto(cls, v):
        """Validate that monto is positive"""
        if v <= 0:
            raise ValueError('monto must be greater than 0')
        return v


# ==================== Instrucción de Mandato DTOs ====================

class BankCertificateData(BaseModel):
    """Data extracted from Bank Certificate PDF"""
    numero_certificado: Optional[str] = Field(None, description="Certificate number if available")
    banco: str = Field(..., min_length=1, max_length=100, description="Bank name (e.g., BANCOLOMBIA, BBVA)")
    fecha_emision: Optional[str] = Field(None, description="Certificate issue date")
    razon_social: str = Field(..., min_length=1, max_length=255, description="Company name")
    nit: str = Field(..., min_length=5, max_length=20, description="Colombian tax ID")
    tipo_cuenta: str = Field(..., description="Account type (e.g., CUENTA DE AHORROS, CUENTA CORRIENTE)")
    numero_cuenta: str = Field(..., min_length=1, max_length=50, description="Account number")

    @validator('nit')
    def validate_nit(cls, v):
        """Validate NIT is not empty"""
        if not v or not v.strip():
            raise ValueError('nit cannot be empty')
        return v.strip()

    @validator('razon_social')
    def validate_razon_social(cls, v):
        """Validate razon_social is not empty"""
        if not v or not v.strip():
            raise ValueError('razon_social cannot be empty')
        return v.strip()


class AcreedorGastosNacionales(BaseModel):
    """Creditor information for Instruccion de Mandato (National Expense Creditor)"""
    razon_social: str = Field(..., min_length=1, max_length=255, description="Company name")
    nit: Optional[str] = Field(None, max_length=20, description="Colombian tax ID (optional for DIAN)")
    banco: str = Field(..., min_length=1, max_length=100, description="Bank name")
    tipo_cuenta: str = Field(..., description="Account type (Ahorros, Corriente, PCE)")
    numero_cuenta: str = Field(..., min_length=1, max_length=50, description="Account number or N/A")

    @validator('razon_social')
    def validate_razon_social(cls, v):
        """Validate razon_social is not empty"""
        if not v or not v.strip():
            raise ValueError('razon_social cannot be empty')
        return v.strip()

    @validator('banco')
    def validate_banco(cls, v):
        """Validate banco is not empty"""
        if not v or not v.strip():
            raise ValueError('banco cannot be empty')
        return v.strip()

    @validator('tipo_cuenta')
    def validate_tipo_cuenta(cls, v):
        """Validate tipo_cuenta is valid"""
        valid_types = ['Ahorros', 'Corriente', 'PCE', 'CUENTA DE AHORROS', 'CUENTA CORRIENTE']
        if v not in valid_types:
            # Normalize common variations
            v_lower = v.lower()
            if 'ahorr' in v_lower:
                return 'Ahorros'
            elif 'corriente' in v_lower:
                return 'Corriente'
            elif 'pce' in v_lower:
                return 'PCE'
            else:
                raise ValueError(f'tipo_cuenta must be one of: {", ".join(valid_types)}')
        return v


class InstruccionMandatoRequest(BaseModel):
    """Request to generate Instruccion de Mandato contract"""
    client_nit: str = Field(..., min_length=5, max_length=20, description="Client NIT")
    numero_cotizacion_desembolso: str = Field(..., min_length=1, max_length=100, description="Disbursement quote number")
    fecha_contrato_mandato: str = Field(..., description="Mandate contract date (ISO format)")
    monto: Decimal = Field(..., gt=0, description="Total amount to transfer in COP")
    acreedores: list[AcreedorGastosNacionales] = Field(..., min_items=1, max_items=3, description="List of creditors (1-3)")

    @validator('client_nit')
    def validate_client_nit(cls, v):
        """Validate NIT is not empty"""
        if not v or not v.strip():
            raise ValueError('client_nit cannot be empty')
        return v.strip()

    @validator('monto')
    def validate_monto(cls, v):
        """Validate that monto is positive"""
        if v <= 0:
            raise ValueError('monto must be greater than 0')
        return v


class DIANMandatoRequest(BaseModel):
    """Request to generate DIAN Mandato (IM) contract - simplified, no creditors"""
    client_nit: str = Field(..., min_length=5, max_length=20, description="Client NIT")
    numero_cotizacion_desembolso: str = Field(..., min_length=1, max_length=100, description="Disbursement quote number")
    fecha_contrato_mandato: str = Field(..., description="Mandate contract date (ISO format)")
    monto: Decimal = Field(..., gt=0, description="Total amount to transfer in COP")

    @validator('client_nit')
    def validate_client_nit(cls, v):
        """Validate NIT is not empty"""
        if not v or not v.strip():
            raise ValueError('client_nit cannot be empty')
        return v.strip()

    @validator('monto')
    def validate_monto(cls, v):
        """Validate that monto is positive"""
        if v <= 0:
            raise ValueError('monto must be greater than 0')
        return v
