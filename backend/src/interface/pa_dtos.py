"""
DTOs for PA (Patrimonio Autónomo) Classification feature.

This module contains all Pydantic models for request/response validation
in the PA Report Classification endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class PAProcessingStatus(str, Enum):
    """Status of PA processing session."""
    UPLOADING = "uploading"
    CLEANING = "cleaning"
    CLEANED = "cleaned"
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"
    FAILED = "failed"


class RuleUploadType(str, Enum):
    """Types of rule files that can be uploaded."""
    CATALOG = "catalog"
    CLASSIFICATION = "classification"
    CLASIFICACION_CUENTA = "clasificacion_cuenta"
    NEXO = "nexo"


# =============================================================================
# Account Catalog DTOs
# =============================================================================

class PAAccountCatalogEntry(BaseModel):
    """Single entry in the PA account catalog."""
    id: Optional[str] = None
    cuenta_finkargo: str = Field(..., description="Account number from Finkargo/NetSuite")
    cuenta_homologacion: str = Field(..., description="Homologated account number")
    nombre_homologacion: str = Field(..., description="Homologated account name")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PAAccountCatalogResponse(BaseModel):
    """Response containing PA account catalog entries."""
    entries: List[PAAccountCatalogEntry] = Field(default_factory=list)
    total_count: int = Field(default=0)


class PAAccountCatalogUploadResponse(BaseModel):
    """Response from uploading PA account catalog."""
    success: bool
    entries_uploaded: int = Field(default=0)
    entries_updated: int = Field(default=0)
    entries_skipped: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)
    message: str = Field(default="")


# =============================================================================
# Classification Rule DTOs
# =============================================================================

class PAClassificationRuleEntry(BaseModel):
    """Single classification rule entry."""
    id: Optional[str] = None
    tipo_transaccion: str = Field(..., description="Transaction type (e.g., Asiento, Factura de venta)")
    tipo_comprobante: str = Field(..., description="Document type (e.g., Ajustes Contables)")
    numero_documento_patron: Optional[str] = Field(None, description="Pattern for document number matching")
    categoria: str = Field(..., description="Output category")
    subcategoria_base: Optional[str] = Field(None, description="Base subcategory")
    clasificacion_default: Optional[str] = Field(None, description="Default classification")
    prioridad: int = Field(default=100, description="Priority for rule matching")
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PAClassificationRulesResponse(BaseModel):
    """Response containing PA classification rules."""
    rules: List[PAClassificationRuleEntry] = Field(default_factory=list)
    total_count: int = Field(default=0)


class PAClassificationRulesUploadResponse(BaseModel):
    """Response from uploading PA classification rules."""
    success: bool
    rules_uploaded: int = Field(default=0)
    rules_updated: int = Field(default=0)
    rules_skipped: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)
    message: str = Field(default="")


# =============================================================================
# Clasificación Cuenta Rule DTOs
# =============================================================================

class PAClasificacionCuentaRuleEntry(BaseModel):
    """Single clasificación cuenta rule entry."""
    id: Optional[str] = None
    cuenta_nombre_patron: str = Field(..., description="Account name pattern to match")
    clasificacion: str = Field(..., description="Output classification")
    categoria_aplicable: Optional[str] = Field(None, description="Restrict to specific category")
    prioridad: int = Field(default=100)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None


class PAClasificacionCuentaRulesResponse(BaseModel):
    """Response containing clasificación cuenta rules."""
    rules: List[PAClasificacionCuentaRuleEntry] = Field(default_factory=list)
    total_count: int = Field(default=0)


class PAClasificacionCuentaRulesUploadResponse(BaseModel):
    """Response from uploading clasificación cuenta rules."""
    success: bool
    rules_uploaded: int = Field(default=0)
    rules_updated: int = Field(default=0)
    rules_skipped: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)
    message: str = Field(default="")


# =============================================================================
# Nexo Rule DTOs
# =============================================================================

class PANexoRuleEntry(BaseModel):
    """Single nexo rule entry."""
    id: Optional[str] = None
    cuenta_nombre_patron: str = Field(..., description="Account name pattern to match")
    nexo: str = Field(..., description="Nexo value (e.g., 1, 2, 3, 4, 13)")
    prioridad: int = Field(default=100)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None


class PANexoRulesResponse(BaseModel):
    """Response containing nexo rules."""
    rules: List[PANexoRuleEntry] = Field(default_factory=list)
    total_count: int = Field(default=0)


class PANexoRulesUploadResponse(BaseModel):
    """Response from uploading nexo rules."""
    success: bool
    rules_uploaded: int = Field(default=0)
    rules_updated: int = Field(default=0)
    rules_skipped: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)
    message: str = Field(default="")


# =============================================================================
# Rules Summary DTOs
# =============================================================================

class PARulesSummary(BaseModel):
    """Summary of all PA rules currently loaded."""
    catalog_count: int = Field(default=0, description="Number of account catalog entries")
    classification_rules_count: int = Field(default=0, description="Number of classification rules")
    clasificacion_cuenta_rules_count: int = Field(default=0, description="Number of clasificación cuenta rules")
    nexo_rules_count: int = Field(default=0, description="Number of nexo rules")
    last_catalog_update: Optional[datetime] = None
    last_classification_update: Optional[datetime] = None
    last_clasificacion_cuenta_update: Optional[datetime] = None
    last_nexo_update: Optional[datetime] = None


# =============================================================================
# Processing DTOs
# =============================================================================

class PAProcessingStats(BaseModel):
    """Statistics from PA report processing."""
    total_rows: int = Field(default=0, description="Total rows in source file")
    pa_rows: int = Field(default=0, description="Rows matching PA accounts")
    non_pa_rows: int = Field(default=0, description="Rows not matching PA accounts")

    # Balance validation
    debito_sum: float = Field(default=0.0, description="Sum of débito column")
    credito_sum: float = Field(default=0.0, description="Sum of crédito column")
    valor_cop_sum: float = Field(default=0.0, description="Sum of Valor COP (should be 0)")
    valor_usd_sum: float = Field(default=0.0, description="Sum of Valor USD (should be 0)")
    balance_valid: bool = Field(default=False, description="Whether balance sums to 0")

    # Classification stats (after classification step)
    classified_count: int = Field(default=0, description="Rows with complete classification")
    unclassified_count: int = Field(default=0, description="Rows missing classification")
    missing_homologacion_count: int = Field(default=0, description="Rows missing homologation")

    # Warnings
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")


class PAUploadResponse(BaseModel):
    """Response from uploading NetSuite file."""
    success: bool
    session_id: str = Field(..., description="Unique session ID for subsequent operations")
    filename: str = Field(..., description="Original filename")
    total_rows: int = Field(default=0)
    pa_rows: int = Field(default=0)
    message: str = Field(default="")
    errors: List[str] = Field(default_factory=list)


class PACleanedPreview(BaseModel):
    """Preview of cleaned PA data."""
    session_id: str
    status: PAProcessingStatus
    stats: PAProcessingStats
    sample_rows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sample of cleaned rows (first 10)"
    )
    column_headers: List[str] = Field(
        default_factory=list,
        description="Column headers in output file"
    )


class PAClassifiedPreview(BaseModel):
    """Preview of classified PA data."""
    session_id: str
    status: PAProcessingStatus
    stats: PAProcessingStats
    sample_rows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sample of classified rows (first 10)"
    )
    column_headers: List[str] = Field(
        default_factory=list,
        description="Column headers in output file"
    )
    classification_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of records by category"
    )


# =============================================================================
# History DTOs
# =============================================================================

class PAProcessingHistoryEntry(BaseModel):
    """Single entry in processing history."""
    id: str
    session_id: str
    status: PAProcessingStatus
    original_filename: Optional[str] = None
    original_file_size: Optional[int] = None
    stats: PAProcessingStats
    cleaned_file_url: Optional[str] = None
    classified_file_url: Optional[str] = None
    error_message: Optional[str] = None
    processed_by: Optional[str] = None
    processed_by_email: Optional[str] = None
    started_at: datetime
    cleaned_at: Optional[datetime] = None
    classified_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PAProcessingHistoryFilter(BaseModel):
    """Filter parameters for processing history."""
    status: Optional[PAProcessingStatus] = None
    processed_by: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PAProcessingHistoryResponse(BaseModel):
    """Response containing processing history."""
    entries: List[PAProcessingHistoryEntry] = Field(default_factory=list)
    total_count: int = Field(default=0)
    limit: int
    offset: int


# =============================================================================
# Source Record DTO (for internal processing)
# =============================================================================

class PASourceRecord(BaseModel):
    """
    Represents a single row from the NetSuite source file.
    Maps to columns A-Z in the source Excel.
    """
    # Column A: Cuenta (línea): Número
    cuenta_linea_numero: str = Field(..., alias="cuenta_linea_numero")

    # Column B: Cuenta (línea): Nombre
    cuenta_linea_nombre: str = Field(..., alias="cuenta_linea_nombre")

    # Column C: Fecha
    fecha: Optional[date] = None

    # Column D: Fecha de creación
    fecha_creacion: Optional[date] = None

    # Column E: Tipo de Transacción
    tipo_transaccion: Optional[str] = None

    # Column F: Tipo de comprobante
    tipo_comprobante: Optional[str] = None

    # Column G: Número de documento
    numero_documento: Optional[str] = None

    # Additional columns H-N (entity, notes, etc.)
    entidad: Optional[str] = None
    notas: Optional[str] = None

    # Column O: Débito
    debito: float = Field(default=0.0)

    # Column P: Crédito
    credito: float = Field(default=0.0)

    # Column Q: Saldo (will be renamed to Valor COP)
    saldo: float = Field(default=0.0)

    # Column S: Moneda: Nombre
    moneda_nombre: Optional[str] = None

    # Column T: Tipo de cambio
    tipo_cambio: Optional[float] = None

    # Column U: Importe (moneda extranjera) (will be renamed to Valor USD)
    importe_moneda_extranjera: float = Field(default=0.0)

    # Row number for error reporting
    row_number: Optional[int] = None

    class Config:
        populate_by_name = True


class PAClassifiedRecord(BaseModel):
    """
    Represents a classified PA record with all output columns.
    This is the final output format.
    """
    # Original source columns
    cuenta_linea_numero: str
    cuenta_linea_nombre: str
    fecha: Optional[date] = None
    fecha_creacion: Optional[date] = None
    tipo_transaccion: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    numero_documento: Optional[str] = None
    debito: float = Field(default=0.0)
    credito: float = Field(default=0.0)
    valor_cop: float = Field(default=0.0)  # Renamed from Saldo
    moneda_nombre: Optional[str] = None
    tipo_cambio: Optional[float] = None
    valor_usd: float = Field(default=0.0)  # Renamed from Importe moneda extranjera

    # New output columns (AA-AH)
    pa: str = Field(default="X", description="PA marker")
    categoria: Optional[str] = Field(None, description="Main category")
    subcategoria: Optional[str] = Field(None, description="Sub-category")
    clasificacion: Optional[str] = Field(None, description="Classification")
    nexo: Optional[str] = Field(None, description="Nexo value")
    comprobacion_saldos: Optional[str] = Field(None, description="Balance verification")
    cuenta_homologacion: Optional[str] = Field(None, description="Homologation account number")
    nombre_homologacion: Optional[str] = Field(None, description="Homologation account name")
