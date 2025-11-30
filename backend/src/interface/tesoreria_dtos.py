"""
DTOs for Tesorería (Treasury) module - Payment Template Conversion.

This module contains all Pydantic models for request/response validation
in the Treasury department endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class CountryCode(str, Enum):
    """Supported countries for payment template conversion."""
    COLOMBIA = "colombia"
    MEXICO = "mexico"


class ConceptType(str, Enum):
    """
    Payment concept types for NetSuite template.

    Each concept represents a different type of payment that may have
    its own AR account mapping.
    """
    # Common concepts
    CAPITAL = "CAPITAL"
    SEGUROS = "SEGUROS"
    INTERESES = "INTERESES"
    MORATORIOS = "MORATORIOS"
    COSTOS_ADICIONALES = "COSTOS_ADICIONALES"

    # Colombia-specific concepts
    CUATRO_POR_MIL = "4X1000"
    FONDO_GARANTIAS = "FONDO_GARANTIAS"
    IVA_FONDO_GARANTIAS = "IVA_FONDO_GARANTIAS"
    SERVICIO_ORIGINACION = "SERVICIO_ORIGINACION"
    SERVICIO_GIRO = "SERVICIO_GIRO"

    # México-specific concepts
    COMISION_DESEMBOLSO = "COMISION_DESEMBOLSO"
    COMISION_DISPOSICION = "COMISION_DISPOSICION"
    COMISION_SWIFT = "COMISION_SWIFT"
    COMISION_ADMINISTRACION = "COMISION_ADMINISTRACION"
    COMISION_APERTURA = "COMISION_APERTURA"


class HistorialValidationError(BaseModel):
    """
    Represents a validation error found in the Historial de Pagos file.

    Attributes:
        row: Row number where the error occurred (1-indexed, 0 for header errors)
        column: Column name where the error occurred
        message: Human-readable error message in Spanish
    """
    row: int = Field(..., ge=0, description="Número de fila con error (0 para errores de encabezado)")
    column: str = Field(..., description="Nombre de la columna con error")
    message: str = Field(..., description="Mensaje de error")


class ColumnValidationStatus(BaseModel):
    """
    Status of column validation for a required column.

    Attributes:
        column_name: Name of the column
        found: Whether the column was found in the file
        source_column: Name of the column in the source file (if found)
    """
    column_name: str = Field(..., description="Nombre de la columna requerida")
    found: bool = Field(..., description="Si la columna fue encontrada")
    source_column: Optional[str] = Field(None, description="Nombre en el archivo fuente")


class ConceptStats(BaseModel):
    """
    Statistics for a concept type in the file.

    Attributes:
        concept_type: Type of payment concept
        count: Number of rows with non-zero values
        total_amount: Sum of values for this concept
    """
    concept_type: str = Field(..., description="Tipo de concepto de pago")
    count: int = Field(..., ge=0, description="Cantidad de filas con valores no cero")
    total_amount: float = Field(..., description="Suma de valores para este concepto")


class HistorialValidationResponse(BaseModel):
    """
    Response from Historial de Pagos upload and validation endpoint.

    Attributes:
        success: Whether validation passed without critical errors
        country: Country for which validation was performed
        total_rows: Total number of data rows in the Excel
        valid_rows: Number of rows that passed validation
        estimated_output_rows: Estimated number of output rows after conversion
        column_status: Validation status for each required column
        errors: List of validation errors found
        preview_data: First few rows of parsed data for preview
    """
    success: bool = Field(..., description="Si la validación fue exitosa")
    country: str = Field(..., description="País para el que se validó")
    total_rows: int = Field(..., ge=0, description="Total de filas en el Excel")
    valid_rows: int = Field(..., ge=0, description="Filas válidas")
    estimated_output_rows: int = Field(..., ge=0, description="Filas estimadas en el archivo de salida")
    column_status: List[ColumnValidationStatus] = Field(
        default_factory=list,
        description="Estado de validación de columnas requeridas"
    )
    concept_stats: List[ConceptStats] = Field(
        default_factory=list,
        description="Estadísticas por tipo de concepto"
    )
    errors: List[HistorialValidationError] = Field(
        default_factory=list,
        description="Lista de errores de validación"
    )
    preview_data: Optional[List[Dict]] = Field(
        None,
        description="Primeras filas de datos parseados para previsualización"
    )


class ConversionStats(BaseModel):
    """
    Statistics from the payment template conversion.

    Attributes:
        source_rows: Number of source rows processed
        output_rows: Number of output rows generated
        concepts_breakdown: Count of rows per concept type
        skipped_rows: Number of rows skipped (no non-zero concepts)
        errors_count: Number of rows with errors
    """
    source_rows: int = Field(..., ge=0, description="Filas fuente procesadas")
    output_rows: int = Field(..., ge=0, description="Filas de salida generadas")
    concepts_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Conteo de filas por tipo de concepto"
    )
    skipped_rows: int = Field(default=0, ge=0, description="Filas omitidas (sin conceptos)")
    errors_count: int = Field(default=0, ge=0, description="Filas con errores")


class ConversionResponse(BaseModel):
    """
    Response from payment template conversion endpoint.

    Note: The actual file is returned as a StreamingResponse,
    this model is used for error responses or when returning metadata.

    Attributes:
        success: Whether conversion was successful
        filename: Name of the generated file
        stats: Conversion statistics
        message: Optional message about the conversion
    """
    success: bool = Field(..., description="Si la conversión fue exitosa")
    filename: str = Field(..., description="Nombre del archivo generado")
    stats: ConversionStats = Field(..., description="Estadísticas de conversión")
    message: Optional[str] = Field(None, description="Mensaje opcional sobre la conversión")


class OutputTemplateRow(BaseModel):
    """
    Represents a single row in the NetSuite output template.

    This is the target format for payment application in NetSuite.

    Attributes:
        payment_date: Date of payment (dd/mm/yyyy format)
        customer_external_id: Client NIT/RFC
        payment_ref: Payment reference (Código de recaudo)
        invoice_core_id: Invoice ID (Código de desembolso)
        concept_type: Type of payment concept
        payment_amount: Amount for this concept
        currency: Currency code (COP, MXN, USD)
        exchangerate: Exchange rate (for certain payment types)
        araccount: AR account ID from catalog lookup
        memo: Optional memo/notes
    """
    payment_date: str = Field(..., description="Fecha de pago")
    customer_external_id: str = Field(..., description="ID externo del cliente (NIT/RFC)")
    payment_ref: str = Field(..., description="Referencia de pago")
    invoice_core_id: str = Field(..., description="ID del desembolso")
    concept_type: str = Field(..., description="Tipo de concepto")
    payment_amount: float = Field(..., description="Monto del pago")
    currency: str = Field(..., description="Moneda")
    exchangerate: Optional[float] = Field(None, description="Tasa de cambio")
    araccount: int = Field(..., description="ID de cuenta AR")
    memo: Optional[str] = Field(None, description="Notas/Memo")
