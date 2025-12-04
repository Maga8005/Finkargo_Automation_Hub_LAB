"""
DTOs for Finance module - Facturación MX automation.

This module contains all Pydantic models for request/response validation
in the Finance department endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import date
from enum import Enum
import re


class SearchType(str, Enum):
    """Types of search available for invoice filtering."""
    CODIGO_OPERACION = "codigo_operacion"
    RFC = "rfc"
    FECHA = "fecha"


class ArchivoEstado(str, Enum):
    """Status of file availability in Google Drive."""
    DISPONIBLE = "Disponible"
    NO_DISPONIBLE = "No disponible"
    PENDIENTE = "Pendiente"


class InvoiceRecord(BaseModel):
    """
    Represents a single invoice record from the master Excel file.

    Attributes:
        uuid: Unique identifier for the invoice (used to find files in Drive)
        codigo_operacion: Operation code for grouping invoices
        conceptos: Description of the invoice items
        fecha_emision: Date when the invoice was issued
        rfc_receptor: Mexican tax ID of the receiver
        razon_receptor: Legal name of the receiver
        subtotal: Subtotal amount in USD (before taxes)
        iva_trasladado: Transferred VAT amount in USD
        iva_exento: Exempt VAT amount in USD
        total: Total amount in USD
        uuid_relacionados: Related document UUIDs
        tipo_comprobante: Fiscal document type
    """
    uuid: str = Field(..., min_length=1, max_length=100, description="UUID del documento fiscal")
    codigo_operacion: str = Field(..., min_length=1, max_length=50, description="Código de operación")
    conceptos: str = Field(..., max_length=500, description="Descripción de conceptos")
    fecha_emision: date = Field(..., description="Fecha de emisión")
    rfc_receptor: str = Field(..., min_length=12, max_length=13, description="RFC del receptor")
    razon_receptor: str = Field(..., max_length=255, description="Razón social del receptor")
    subtotal: float = Field(..., description="Subtotal en USD (puede ser negativo para egresos)")
    iva_trasladado: float = Field(default=0.0, ge=0, description="IVA Trasladado en USD")
    iva_exento: float = Field(default=0.0, ge=0, description="IVA Exento en USD")
    total: float = Field(..., description="Total en USD (puede ser negativo para egresos)")
    uuid_relacionados: Optional[str] = Field(
        default=None,
        max_length=500,
        description="UUIDs de documentos relacionados"
    )
    tipo_comprobante: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Tipo de comprobante fiscal"
    )

    @field_validator('rfc_receptor')
    @classmethod
    def validate_rfc(cls, v: str) -> str:
        """
        Validate Mexican RFC format.

        RFC can be 12 characters (persona moral) or 13 characters (persona física).
        """
        pattern = r'^[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}$'
        if not re.match(pattern, v.upper()):
            raise ValueError('RFC inválido. Debe tener formato válido de 12 o 13 caracteres.')
        return v.upper()

    @field_validator('uuid')
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Ensure UUID is trimmed and uppercase."""
        return v.strip().upper()


class ExcelValidationError(BaseModel):
    """
    Represents a validation error found in the Excel file.

    Attributes:
        row: Row number where the error occurred (1-indexed)
        column: Column name where the error occurred
        message: Human-readable error message in Spanish
    """
    row: int = Field(..., ge=1, description="Número de fila con error")
    column: str = Field(..., description="Nombre de la columna con error")
    message: str = Field(..., description="Mensaje de error")


class ExcelValidationResponse(BaseModel):
    """
    Response from Excel upload and validation endpoint.

    Attributes:
        success: Whether validation passed without critical errors
        total_rows: Total number of data rows in the Excel
        valid_rows: Number of rows that passed validation
        errors: List of validation errors found
        data: List of valid invoice records
        session_id: Unique session ID for subsequent operations
        drive_sync_stats: Statistics from Drive master sync (new, updated, unchanged records)
    """
    success: bool = Field(..., description="Si la validación fue exitosa")
    total_rows: int = Field(..., ge=0, description="Total de filas en el Excel")
    valid_rows: int = Field(..., ge=0, description="Filas válidas")
    errors: List[ExcelValidationError] = Field(default_factory=list, description="Lista de errores")
    data: List[InvoiceRecord] = Field(default_factory=list, description="Registros válidos")
    session_id: str = Field(..., description="ID de sesión para operaciones subsecuentes")
    drive_sync_stats: Optional[Dict] = Field(
        default=None,
        description="Estadísticas de sincronización con Drive (new, updated, unchanged)"
    )


class InvoiceSearchRequest(BaseModel):
    """
    Request for searching invoices in a session.

    Supports combined filters for more precise searches:
    - codigo_operacion + date range (combined filter)
    - rfc + date range (combined filter)
    - date range only (fecha search type)

    Attributes:
        session_id: Session ID from Excel upload
        search_type: Type of search to perform
        codigo_operacion: Operation code(s) to search - comma separated for multiple (if search_type is codigo_operacion)
        rfc: RFC to search (if search_type is rfc)
        fecha_inicio: Start date for range search (optional for combined filters)
        fecha_fin: End date for range search (optional for combined filters)
    """
    session_id: str = Field(..., description="ID de sesión")
    search_type: SearchType = Field(..., description="Tipo de búsqueda")
    codigo_operacion: Optional[str] = Field(None, description="Código(s) de operación a buscar (separados por coma)")
    rfc: Optional[str] = Field(None, description="RFC a buscar")
    fecha_inicio: Optional[date] = Field(None, description="Fecha inicio del rango (opcional para filtros combinados)")
    fecha_fin: Optional[date] = Field(None, description="Fecha fin del rango (opcional para filtros combinados)")

    @field_validator('fecha_fin')
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure end date is after start date when both are provided."""
        fecha_inicio = info.data.get('fecha_inicio')
        if v and fecha_inicio and v < fecha_inicio:
            raise ValueError('Fecha fin debe ser mayor o igual a fecha inicio')
        return v


class InvoiceSearchResult(InvoiceRecord):
    """
    Invoice record with file availability status.

    Extends InvoiceRecord with archivo_estado field.
    """
    archivo_estado: ArchivoEstado = Field(
        default=ArchivoEstado.PENDIENTE,
        description="Estado del archivo en Drive"
    )


class InvoiceSearchResponse(BaseModel):
    """
    Response from invoice search endpoint.

    Attributes:
        results: List of matching invoices with file status
        total_found: Total number of matching records
        total_amount: Sum of totals for all matching records (USD)
    """
    results: List[InvoiceSearchResult] = Field(default_factory=list, description="Resultados")
    total_found: int = Field(..., ge=0, description="Total de registros encontrados")
    total_amount: float = Field(..., description="Suma total en USD (puede ser negativo)")


class ZipGenerationRequest(BaseModel):
    """
    Request for generating ZIP file with invoices.

    Attributes:
        session_id: Session ID from Excel upload
        uuids: Optional list of specific UUIDs to include (if not provided, uses search criteria)
        search_criteria: Optional search criteria to determine which invoices to include
        metadata: Optional metadata for naming and organizing the ZIP
    """
    session_id: str = Field(..., description="ID de sesión")
    uuids: Optional[List[str]] = Field(None, description="UUIDs específicos a incluir en el ZIP (opcional)")
    search_criteria: Optional[InvoiceSearchRequest] = Field(None, description="Criterios de búsqueda (opcional)")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Metadata para el ZIP (código operación, RFC, etc.)")


class ZipGenerationResponse(BaseModel):
    """
    Response from ZIP generation endpoint.

    Attributes:
        success: Whether ZIP generation was successful
        filename: Name of the generated ZIP file
        total_invoices: Total number of invoices in the ZIP
        pdfs_included: Number of PDFs included
        xmls_included: Number of XMLs included
        missing_files: Number of files not found in Drive
        size_bytes: Size of the ZIP file in bytes
    """
    success: bool = Field(..., description="Si la generación fue exitosa")
    filename: str = Field(..., description="Nombre del archivo ZIP")
    total_invoices: int = Field(..., ge=0, description="Total de facturas en el ZIP")
    pdfs_included: int = Field(..., ge=0, description="PDFs incluidos")
    xmls_included: int = Field(..., ge=0, description="XMLs incluidos")
    missing_files: int = Field(..., ge=0, description="Archivos no encontrados")
    size_bytes: int = Field(..., ge=0, description="Tamaño del ZIP en bytes")


class DriveStatusResponse(BaseModel):
    """
    Response from Drive connection status check.

    Attributes:
        connected: Whether connection to Drive is successful
        folder_id: ID of the configured folder
        folder_name: Name of the configured folder
        total_files: Number of files in the folder
        last_sync: Timestamp of last sync (if available)
    """
    connected: bool = Field(..., description="Si la conexión está activa")
    folder_id: str = Field(..., description="ID de la carpeta")
    folder_name: str = Field(default="", description="Nombre de la carpeta")
    total_files: int = Field(default=0, ge=0, description="Total de archivos")
    last_sync: Optional[str] = Field(None, description="Última sincronización")
