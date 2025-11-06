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

class ContractGenerationRequest(BaseModel):
    """Request to generate a contract"""
    client_nit: str = Field(..., description="Client NIT to generate contract for")
    contract_type: ContractType = Field(default=ContractType.ACTIVOS, description="Type of contract to generate")

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
