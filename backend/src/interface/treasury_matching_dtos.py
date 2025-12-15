"""
DTOs for Treasury Declaration-Historial Matching Feature.

This module contains all Pydantic models for the Exchange Declaration
to Historial de Pagos matching workflow.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from decimal import Decimal


class MatchStatus(str, Enum):
    """Match status for a payment group."""
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"
    CONFLICT = "conflict"


class HistorialRecord(BaseModel):
    """
    Single row from Historial de Pagos Excel file.

    Represents one payment record before grouping.
    """
    row_number: int = Field(..., description="Original Excel row number (1-indexed)")
    cliente: str = Field(..., description="Customer name")
    cliente_normalized: Optional[str] = Field(None, description="Normalized customer name for matching")
    identificacion_cliente: str = Field(..., description="Customer NIT/identification")
    codigo_desembolso: Optional[str] = Field(None, description="Disbursement code")
    codigo_recaudo: Optional[str] = Field(None, description="Collection code")
    numero_factura: Optional[str] = Field(None, description="Invoice number")
    fecha_desembolso: Optional[str] = Field(None, description="Disbursement date")
    fecha_vencimiento: Optional[str] = Field(None, description="Due date")
    valor_desembolso: Optional[float] = Field(None, description="Disbursement value")
    estado_desembolso: Optional[str] = Field(None, description="Disbursement status")
    fecha_pago: str = Field(..., description="Payment date (key for grouping)")
    total_pagado: Optional[float] = Field(None, description="Total paid")
    moneda: Optional[str] = Field(None, description="Currency (COP/USD)")
    medio_pago: Optional[str] = Field(None, description="Payment method")
    tasa_cambio: Optional[float] = Field(None, description="Exchange rate")
    total_pagado_usd: Optional[float] = Field(None, description="Total paid in USD")
    capital: float = Field(..., description="Capital amount (key for grouping)")
    declaracion_cambio_numero: Optional[str] = Field(None, description="Declaration number (output)")
    dc_nombre: Optional[str] = Field(None, description="Declaration PDF name (output)")
    dim: Optional[str] = Field(None, description="DIM value")
    factura_final: Optional[str] = Field(None, description="Final invoice")


class PaymentGroup(BaseModel):
    """
    Aggregated group of payment records.

    Groups records by (cliente_normalized, fecha_pago) and sums capital.
    """
    group_id: str = Field(..., description="Unique group identifier (UUID)")
    cliente: str = Field(..., description="Customer name (from first record)")
    cliente_normalized: str = Field(..., description="Normalized customer name for matching")
    identificacion_cliente: str = Field(..., description="Customer NIT (from first record)")
    fecha_pago: str = Field(..., description="Payment date (ISO format)")
    total_capital: float = Field(..., description="Sum of capital across all records")
    record_count: int = Field(..., description="Number of records in group")
    record_row_numbers: List[int] = Field(..., description="Original Excel row numbers")
    moneda: Optional[str] = Field(None, description="Currency")


class DeclarationItem(BaseModel):
    """
    Declaration information from inventory/scanned folder.

    Represents a single exchange declaration that can be matched.
    """
    declaration_id: str = Field(..., description="Unique declaration identifier")
    declaration_number: str = Field(..., description="Official declaration number")
    customer_name: str = Field(..., description="Customer name from folder")
    customer_name_normalized: str = Field(..., description="Normalized customer name")
    fecha: str = Field(..., description="Declaration date (ISO format)")
    amount: float = Field(..., description="Declaration amount in USD")
    pdf_file_name: str = Field(..., description="PDF filename")
    folder_path: Optional[str] = Field(None, description="Full folder path")


class MatchConfig(BaseModel):
    """
    Configuration for the matching algorithm.
    """
    date_tolerance_days: int = Field(default=7, ge=1, le=14, description="Days tolerance for date matching")
    amount_tolerance: float = Field(default=2.0, ge=0.5, le=5.0, description="USD tolerance for amount matching")
    customer_match_threshold: int = Field(default=85, ge=50, le=100, description="Fuzzy match threshold (0-100)")
    customer_match_strict: bool = Field(default=False, description="Require exact customer name match")


class MatchResult(BaseModel):
    """
    Result of matching a payment group to a declaration.
    """
    group_id: str = Field(..., description="Payment group ID")
    payment_group: PaymentGroup = Field(..., description="Payment group details")
    declaration: Optional[DeclarationItem] = Field(None, description="Matched declaration (if any)")
    match_status: MatchStatus = Field(..., description="Match status")
    match_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    customer_similarity: Optional[float] = Field(None, description="Customer name similarity score")
    date_difference_days: Optional[int] = Field(None, description="Days difference between dates")
    amount_difference: Optional[float] = Field(None, description="Amount difference in USD")
    conflict_declarations: Optional[List[DeclarationItem]] = Field(None, description="Multiple matching declarations (conflict)")


class ColumnValidationStatus(BaseModel):
    """Status of column validation for a required column."""
    column_name: str = Field(..., description="Expected column name")
    found: bool = Field(..., description="Whether column was found")
    source_column: Optional[str] = Field(None, description="Actual column name in file")


class HistorialUploadResponse(BaseModel):
    """
    Response from uploading and parsing Historial de Pagos Excel.
    """
    success: bool = Field(..., description="Whether parsing was successful")
    session_id: str = Field(..., description="Session ID for subsequent operations")
    total_rows: int = Field(default=0, description="Total rows in Excel")
    valid_rows: int = Field(default=0, description="Rows that passed validation")
    payment_groups: List[PaymentGroup] = Field(default_factory=list, description="Grouped payments")
    group_count: int = Field(default=0, description="Number of payment groups")
    column_status: List[ColumnValidationStatus] = Field(default_factory=list, description="Column validation status")
    errors: List[str] = Field(default_factory=list, description="Parsing errors")
    preview_data: Optional[List[Dict]] = Field(None, description="Preview of first rows")


class MatchingStatistics(BaseModel):
    """
    Statistics summary of matching results.
    """
    total_payment_groups: int = Field(default=0)
    matched_groups: int = Field(default=0)
    partial_matches: int = Field(default=0)
    unmatched_groups: int = Field(default=0)
    conflict_groups: int = Field(default=0)
    match_percentage: float = Field(default=0.0)
    average_confidence: float = Field(default=0.0)
    total_declarations: int = Field(default=0)
    declarations_used: int = Field(default=0)
    declarations_unused: int = Field(default=0)


class MatchingSessionResponse(BaseModel):
    """
    Full matching session response with results and statistics.
    """
    session_id: str = Field(..., description="Session ID")
    success: bool = Field(..., description="Whether matching completed successfully")
    config: MatchConfig = Field(..., description="Matching configuration used")
    results: List[MatchResult] = Field(default_factory=list, description="Match results")
    statistics: MatchingStatistics = Field(..., description="Matching statistics")
    errors: List[str] = Field(default_factory=list, description="Any errors during matching")


class ManualOverrideRequest(BaseModel):
    """
    Request to manually override a match.
    """
    session_id: str = Field(..., description="Session ID")
    group_id: str = Field(..., description="Payment group ID to override")
    declaration_id: Optional[str] = Field(None, description="Declaration ID to assign (null to clear)")


class ManualOverrideResponse(BaseModel):
    """
    Response from manual override operation.
    """
    success: bool
    message: str
    updated_result: Optional[MatchResult] = None


class DeclarationInventoryUploadResponse(BaseModel):
    """
    Response from uploading declaration inventory Excel.
    """
    success: bool = Field(..., description="Whether upload was successful")
    session_id: str = Field(..., description="Session ID for subsequent operations")
    total_declarations: int = Field(default=0, description="Total declarations loaded")
    declarations: List[DeclarationItem] = Field(default_factory=list, description="Loaded declarations")
    errors: List[str] = Field(default_factory=list, description="Loading errors")
