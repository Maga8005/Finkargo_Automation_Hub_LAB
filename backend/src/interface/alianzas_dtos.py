"""
Alianzas (Partnerships) Module - Data Transfer Objects (DTOs)
Broker management, commission tracking, and payment DTOs.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TipoBroker(str, Enum):
    """Broker type enum"""
    MASTER_BROKER = "master_broker"
    INDEPENDIENTE = "independiente"
    ALIADO_LOGISTICO = "aliado_logistico"
    CONSULTORIA = "consultoria"


class EstadoBroker(str, Enum):
    """Broker status enum"""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    PENDIENTE = "pendiente"


# ==================== Broker DTOs ====================

class BrokerBase(BaseModel):
    """Base broker data model with all fields"""
    nombre: str = Field(..., min_length=1, max_length=255, description="Broker name")
    tipo_broker: TipoBroker = Field(..., description="Type of broker")
    master_broker_id: Optional[str] = Field(None, description="UUID of master broker (for sub-brokers)")
    porcentaje_apertura: Optional[Decimal] = Field(None, ge=0, le=100, description="Opening commission percentage (0-100)")
    porcentaje_operativa: Optional[Decimal] = Field(None, ge=0, le=100, description="Operational commission percentage (0-100)")
    cuenta_bancaria: Optional[str] = Field(None, max_length=50, description="Bank account number")
    banco: Optional[str] = Field(None, max_length=100, description="Bank name")
    rfc: Optional[str] = Field(None, max_length=20, description="Mexican tax ID (RFC)")
    fecha_contrato: Optional[date] = Field(None, description="Contract start date")
    vigencia_contrato: Optional[date] = Field(None, description="Contract end date")
    estado: EstadoBroker = Field(default=EstadoBroker.ACTIVO, description="Broker status")
    link_expediente: Optional[str] = Field(None, description="URL to broker documentation folder")
    notas: Optional[str] = Field(None, description="Additional notes")

    @validator('porcentaje_apertura', 'porcentaje_operativa', pre=True)
    def coerce_percentage(cls, v):
        """Convert string or float to Decimal for percentage fields"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        raise ValueError(f'Invalid type for percentage: {type(v)}')

    @validator('fecha_contrato', 'vigencia_contrato', pre=True)
    def parse_date(cls, v):
        """Parse date string to date object"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise ValueError(f'Invalid type for date: {type(v)}')


class BrokerCreate(BrokerBase):
    """DTO for creating a new broker"""
    pass


class BrokerUpdate(BaseModel):
    """DTO for updating a broker - all fields optional"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    tipo_broker: Optional[TipoBroker] = None
    master_broker_id: Optional[str] = None
    porcentaje_apertura: Optional[Decimal] = Field(None, ge=0, le=100)
    porcentaje_operativa: Optional[Decimal] = Field(None, ge=0, le=100)
    cuenta_bancaria: Optional[str] = Field(None, max_length=50)
    banco: Optional[str] = Field(None, max_length=100)
    rfc: Optional[str] = Field(None, max_length=20)
    fecha_contrato: Optional[date] = None
    vigencia_contrato: Optional[date] = None
    estado: Optional[EstadoBroker] = None
    link_expediente: Optional[str] = None
    notas: Optional[str] = None

    @validator('porcentaje_apertura', 'porcentaje_operativa', pre=True)
    def coerce_percentage(cls, v):
        """Convert string or float to Decimal for percentage fields"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        raise ValueError(f'Invalid type for percentage: {type(v)}')

    @validator('fecha_contrato', 'vigencia_contrato', pre=True)
    def parse_date(cls, v):
        """Parse date string to date object"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise ValueError(f'Invalid type for date: {type(v)}')


class BrokerResponse(BaseModel):
    """DTO for broker API response"""
    id: str
    nombre: str
    tipo_broker: TipoBroker
    master_broker_id: Optional[str] = None
    porcentaje_apertura: Optional[float] = None
    porcentaje_operativa: Optional[float] = None
    cuenta_bancaria: Optional[str] = None
    banco: Optional[str] = None
    rfc: Optional[str] = None
    fecha_contrato: Optional[str] = None
    vigencia_contrato: Optional[str] = None
    estado: EstadoBroker
    link_expediente: Optional[str] = None
    notas: Optional[str] = None
    created_at: str
    updated_at: str
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class BrokerSearchRequest(BaseModel):
    """DTO for broker search parameters"""
    nombre: Optional[str] = Field(None, description="Search by name (partial match)")
    tipo_broker: Optional[TipoBroker] = Field(None, description="Filter by broker type")
    estado: Optional[EstadoBroker] = Field(None, description="Filter by status")
    rfc: Optional[str] = Field(None, description="Search by RFC (partial match)")
    active_only: bool = Field(default=True, description="Only return active brokers")


class BrokerWithSubBrokers(BrokerResponse):
    """DTO for broker with sub-brokers list"""
    sub_brokers: List[BrokerResponse] = Field(default_factory=list, description="List of sub-brokers")


# ==================== Broker List Response ====================

class BrokerListResponse(BaseModel):
    """DTO for paginated broker list response"""
    brokers: List[BrokerResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ==================== Contract Extraction DTOs ====================

class ExtractionMethod(str, Enum):
    """Extraction method used for contract data"""
    STANDARD = "standard"
    AI = "ai"


class BrokerContractData(BaseModel):
    """
    DTO for extracted broker contract data.
    All fields are optional since extraction may not find all values.
    """
    nombre_broker: Optional[str] = Field(None, description="Extracted broker name")
    porcentaje_comision_apertura: Optional[float] = Field(
        None, ge=0, le=100, description="Opening commission percentage (0-100)"
    )
    porcentaje_comision_operativa: Optional[float] = Field(
        None, ge=0, le=100, description="Operational commission percentage (0-100)"
    )
    fecha_contrato: Optional[str] = Field(None, description="Contract date in ISO format")
    vigencia_meses: Optional[int] = Field(None, ge=0, description="Contract duration in months")
    rfc_broker: Optional[str] = Field(None, max_length=20, description="Mexican tax ID (RFC)")
    cuenta_bancaria: Optional[str] = Field(None, max_length=50, description="CLABE bank account number")
    banco: Optional[str] = Field(None, max_length=100, description="Bank name")
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.STANDARD, description="Method used for extraction"
    )
    extraction_confidence: Optional[float] = Field(
        None, ge=0, le=1, description="Confidence score (0-1) based on fields found"
    )
    raw_text_preview: Optional[str] = Field(
        None, max_length=500, description="First 500 chars of extracted text for debugging"
    )

    class Config:
        from_attributes = True


# ==================== Exchange Rate DTOs ====================

class TipoCambioResponse(BaseModel):
    """
    DTO for exchange rate response from Banxico API.
    Returns USD/MXN FIX exchange rate.
    """
    tipo_cambio: float = Field(..., description="Exchange rate (MXN per USD)")
    fecha: str = Field(..., description="Date of the exchange rate in ISO format (YYYY-MM-DD)")
    fuente: str = Field(
        default="Banco de México (Banxico)",
        description="Data source description"
    )

    class Config:
        from_attributes = True


# ==================== Commission DTOs ====================

class TipoComision(str, Enum):
    """Commission type enum"""
    APERTURA = "apertura"
    OPERATIVA = "operativa"


class EstadoComision(str, Enum):
    """Commission status enum"""
    CALCULADO = "calculado"
    APROBADO = "aprobado"
    PAGADO = "pagado"


class ComisionInput(BaseModel):
    """
    DTO for commission calculation input.
    Used for both preview (calculate without saving) and batch calculation requests.
    """
    broker_id: str = Field(..., description="UUID of the broker")
    tipo_comision: TipoComision = Field(..., description="Commission type: apertura or operativa")
    cliente_nombre: Optional[str] = Field(None, description="Client company name")
    cliente_nit: Optional[str] = Field(None, max_length=50, description="Client tax ID (NIT)")

    # Apertura-specific fields
    linea_credito: Optional[Decimal] = Field(
        None, ge=0, description="Credit line amount in USD (for apertura only)"
    )
    porcentaje_comision_cliente: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Client commission percentage (0-100, for apertura only)"
    )
    cliente_pago_pct: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Percentage client has paid (0-100, for apertura only)"
    )

    # Operativa-specific fields
    operaciones_mes: Optional[Decimal] = Field(
        None, ge=0, description="Monthly operation disbursements in USD (for operativa only)"
    )

    # Optional period override
    periodo_mes: Optional[int] = Field(
        None, ge=1, le=12, description="Period month (1-12). Defaults to current month."
    )
    periodo_anio: Optional[int] = Field(
        None, ge=2020, description="Period year. Defaults to current year."
    )

    # Optional exchange rate date override
    fecha_tipo_cambio: Optional[date] = Field(
        None, description="Date to use for exchange rate lookup. Defaults to today."
    )

    # Optional notes
    notas: Optional[str] = Field(None, description="Additional notes")

    @validator('linea_credito', 'porcentaje_comision_cliente', 'cliente_pago_pct', 'operaciones_mes', pre=True)
    def coerce_decimal(cls, v):
        """Convert string or float to Decimal for numeric fields"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        raise ValueError(f'Invalid type for decimal: {type(v)}')

    @validator('fecha_tipo_cambio', pre=True)
    def parse_date(cls, v):
        """Parse date string to date object"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise ValueError(f'Invalid type for date: {type(v)}')


class ComisionCalculada(BaseModel):
    """
    DTO for calculated commission result.
    Contains all calculation details and can be persisted to database.
    """
    # Broker reference
    broker_id: str = Field(..., description="UUID of the broker")
    broker_nombre: Optional[str] = Field(None, description="Broker name (for display)")

    # Period
    periodo_mes: int = Field(..., ge=1, le=12, description="Period month (1-12)")
    periodo_anio: int = Field(..., ge=2020, description="Period year")

    # Client information
    cliente_nombre: Optional[str] = Field(None, description="Client company name")
    cliente_nit: Optional[str] = Field(None, description="Client tax ID (NIT)")

    # Commission type
    tipo_comision: TipoComision = Field(..., description="Commission type")

    # Apertura calculation details
    linea_credito: Optional[Decimal] = Field(None, description="Credit line amount in USD")
    porcentaje_comision_cliente: Optional[Decimal] = Field(None, description="Client commission percentage")
    monto_comision_cliente: Optional[Decimal] = Field(None, description="Client commission amount in USD")
    cliente_pago_pct: Optional[Decimal] = Field(None, description="Percentage client has paid (0-100)")

    # Operativa calculation details
    operaciones_mes: Optional[Decimal] = Field(None, description="Monthly operation disbursements in USD")

    # Broker commission
    porcentaje_broker: Decimal = Field(..., description="Broker commission percentage")
    monto_broker_usd: Decimal = Field(..., description="Broker commission amount in USD")

    # Currency conversion
    tipo_cambio: Decimal = Field(..., description="USD/MXN exchange rate used")
    monto_broker_mxn: Decimal = Field(..., description="Broker commission amount in MXN")

    # Status
    estado: EstadoComision = Field(default=EstadoComision.CALCULADO, description="Commission status")

    # Notes
    notas: Optional[str] = Field(None, description="Additional notes")

    # Metadata (only present when saved)
    id: Optional[str] = Field(None, description="UUID of the saved commission record")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="UUID of user who created the record")

    class Config:
        from_attributes = True


class ComisionBatchInput(BaseModel):
    """DTO for batch commission calculation request"""
    comisiones: List[ComisionInput] = Field(
        ..., min_items=1, max_items=100, description="List of commission inputs to calculate"
    )
    guardar: bool = Field(
        default=False, description="If True, save calculated commissions to database"
    )


class ComisionBatchResponse(BaseModel):
    """DTO for batch commission calculation response"""
    comisiones: List[ComisionCalculada] = Field(..., description="List of calculated commissions")
    total_usd: Decimal = Field(..., description="Total commission amount in USD")
    total_mxn: Decimal = Field(..., description="Total commission amount in MXN")
    guardadas: bool = Field(default=False, description="Whether commissions were saved to database")


class ComisionListResponse(BaseModel):
    """DTO for paginated commission list response"""
    comisiones: List[ComisionCalculada]
    total: int
    periodo_mes: int
    periodo_anio: int


class ComisionResumenBroker(BaseModel):
    """DTO for broker commission summary by period"""
    broker_id: str = Field(..., description="UUID of the broker")
    broker_nombre: str = Field(..., description="Broker name")
    periodo_mes: int = Field(..., ge=1, le=12, description="Period month")
    periodo_anio: int = Field(..., ge=2020, description="Period year")
    total_apertura_usd: Decimal = Field(default=Decimal("0"), description="Total apertura commission in USD")
    total_apertura_mxn: Decimal = Field(default=Decimal("0"), description="Total apertura commission in MXN")
    total_operativa_usd: Decimal = Field(default=Decimal("0"), description="Total operativa commission in USD")
    total_operativa_mxn: Decimal = Field(default=Decimal("0"), description="Total operativa commission in MXN")
    total_usd: Decimal = Field(default=Decimal("0"), description="Grand total in USD")
    total_mxn: Decimal = Field(default=Decimal("0"), description="Grand total in MXN")
    num_comisiones: int = Field(default=0, description="Number of commission records")

    class Config:
        from_attributes = True


class ComisionEstadoUpdate(BaseModel):
    """DTO for updating commission status"""
    estado: EstadoComision = Field(..., description="New commission status")


# ==================== Payment DTOs ====================

class EstadoPago(str, Enum):
    """Payment status enum"""
    PENDIENTE = "pendiente"
    PROGRAMADO = "programado"
    PAGADO = "pagado"


class PagoBase(BaseModel):
    """Base payment data model"""
    broker_id: str = Field(..., description="UUID of the broker")
    periodo_mes: int = Field(..., ge=1, le=12, description="Period month (1-12)")
    periodo_anio: int = Field(..., ge=2020, description="Period year")
    total_usd: Decimal = Field(..., ge=0, description="Total payment amount in USD")
    total_mxn: Decimal = Field(..., ge=0, description="Total payment amount in MXN")
    tipo_cambio: Decimal = Field(..., gt=0, description="Exchange rate used")
    fecha_programada: Optional[date] = Field(None, description="Scheduled payment date")
    fecha_pago: Optional[date] = Field(None, description="Actual payment date")
    estado: EstadoPago = Field(default=EstadoPago.PENDIENTE, description="Payment status")
    comprobante_url: Optional[str] = Field(None, description="URL to payment receipt")
    factura_broker_url: Optional[str] = Field(None, description="URL to broker invoice")
    notas: Optional[str] = Field(None, description="Additional notes")

    @validator('total_usd', 'total_mxn', 'tipo_cambio', pre=True)
    def coerce_decimal(cls, v):
        """Convert string or float to Decimal for numeric fields"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        raise ValueError(f'Invalid type for decimal: {type(v)}')

    @validator('fecha_programada', 'fecha_pago', pre=True)
    def parse_date(cls, v):
        """Parse date string to date object"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise ValueError(f'Invalid type for date: {type(v)}')


class PagoCreate(PagoBase):
    """DTO for creating a new payment"""
    approved_by: Optional[str] = Field(None, description="UUID of user who approved")


class PagoResponse(BaseModel):
    """DTO for payment API response"""
    id: str
    broker_id: str
    broker_nombre: Optional[str] = None
    periodo_mes: int
    periodo_anio: int
    total_usd: float
    total_mxn: float
    tipo_cambio: float
    fecha_programada: Optional[str] = None
    fecha_pago: Optional[str] = None
    estado: EstadoPago
    comprobante_url: Optional[str] = None
    factura_broker_url: Optional[str] = None
    notas: Optional[str] = None
    created_at: str
    approved_by: Optional[str] = None

    class Config:
        from_attributes = True


class PagoListResponse(BaseModel):
    """DTO for paginated payment list response"""
    pagos: List[PagoResponse]
    total: int
    limit: int = 50
    offset: int = 0


class PagoEstadoUpdate(BaseModel):
    """DTO for updating payment status"""
    estado: EstadoPago = Field(..., description="New payment status")
    fecha_pago: Optional[date] = Field(None, description="Payment date (required for estado=pagado)")
    comprobante_url: Optional[str] = Field(None, description="URL to payment receipt")

    @validator('fecha_pago', pre=True)
    def parse_date(cls, v):
        """Parse date string to date object"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise ValueError(f'Invalid type for date: {type(v)}')


class ComisionAprobacionRequest(BaseModel):
    """DTO for commission approval request"""
    periodo_mes: int = Field(..., ge=1, le=12, description="Period month (1-12)")
    periodo_anio: int = Field(..., ge=2020, description="Period year")


class ComisionAprobacionResponse(BaseModel):
    """DTO for commission approval response summary"""
    periodo_mes: int
    periodo_anio: int
    comisiones_aprobadas: int = Field(..., description="Number of commissions approved")
    pagos_creados: int = Field(..., description="Number of payment records created")
    total_usd: float = Field(..., description="Total payment amount in USD")
    total_mxn: float = Field(..., description="Total payment amount in MXN")
    brokers_ids: List[str] = Field(default_factory=list, description="List of broker IDs with payments")
    message: str = Field(default="Comisiones aprobadas exitosamente")
