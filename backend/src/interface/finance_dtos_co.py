"""
DTOs for Colombia (CO) Finance Operations.

This module contains data transfer objects for the Colombia invoicing
automation, including file uploads, processing, and report generation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date
from enum import Enum


class FileType(str, Enum):
    """Types of files that can be uploaded for CO processing."""
    NETSUITE = "netsuite"
    NETSUITE_NC = "netsuite_nc"
    NOOVA_FACTURAS = "noova_facturas"
    NOOVA_NC = "noova_notas_credito"


class SheetDestination(str, Enum):
    """Destination sheets for processed invoices."""
    COSTOS_FIJOS = "Relacion facturas Costos Fijos"
    MANDATO = "Relación facturas mandato"


class ProductCategory(str, Enum):
    """Product classification categories."""
    COSTOS_FIJOS = "costos_fijos"
    SEGURO_IVA = "seguro_iva"
    INTERESES_CORRIENTE = "intereses_corriente"
    INTERESES_MORA = "intereses_mora"
    OTROS = "otros"


class NetsuiteRecord(BaseModel):
    """
    Record from Netsuite Excel files.

    Represents data from "VistapredeterminadaTransaccin" sheet with
    columns mapped from Spanish headers to standardized field names.
    """
    numero_factura: str = Field(..., description="Número de documento")
    moneda: str = Field(..., description="Moneda (USD, COP, etc.)")
    valor: float = Field(..., description="Importe en moneda extranjera")

    class Config:
        json_schema_extra = {
            "example": {
                "numero_factura": "FE-12345",
                "moneda": "COP",
                "valor": 1500000.00
            }
        }


class NoovaRecord(BaseModel):
    """
    Record from Noova Excel files.

    Represents data from "Documentos" sheet with columns mapped
    from Spanish headers to standardized field names.
    """
    fecha: date = Field(..., description="Fecha de recepción")
    numero_factura: str = Field(..., description="Número de factura")
    nit: str = Field(..., description="Código del tercero (NIT)")
    nombre_cliente: str = Field(..., description="Nombre del tercero")
    email: str = Field(..., description="Email del tercero")
    estado: str = Field(..., description="Estado del documento")
    envio: str = Field(..., description="Estado de envío al tercero")
    codigo_operacion: str = Field(..., description="Orden de compra / código operación")
    codigo_producto: str = Field(..., description="Código del producto (101-500)")
    concepto: str = Field(..., description="Nombre del producto / concepto")

    class Config:
        json_schema_extra = {
            "example": {
                "fecha": "2025-08-15",
                "numero_factura": "FE-12345",
                "nit": "900123456",
                "nombre_cliente": "Cliente Ejemplo S.A.S.",
                "email": "cliente@ejemplo.com",
                "estado": "Aceptado",
                "envio": "Enviado",
                "codigo_operacion": "OP-2025-001",
                "codigo_producto": "101",
                "concepto": "Interes corriente"
            }
        }


class ConsolidatedRecord(BaseModel):
    """
    Consolidated record from LEFT JOIN of Noova + Netsuite.

    This is the intermediate format after merging Noova (main) with
    Netsuite (supplementary) data by numero_factura.
    """
    # From Noova (always present)
    # fecha and numero_factura are required for data integrity
    fecha: date
    numero_factura: str
    # Other Noova fields default to empty string to handle None from empty Excel cells
    nit: str = ""
    nombre_cliente: str = ""
    email: str = ""
    estado: str = ""
    envio: str = ""
    codigo_operacion: str = ""
    codigo_producto: str = ""
    concepto: str = ""

    # From Netsuite (may be None if not matched)
    moneda: Optional[str] = None
    valor_netsuite: Optional[float] = None

    # Classification (added during processing)
    categoria: Optional[ProductCategory] = None
    hoja_destino: Optional[SheetDestination] = None
    tipo_factura: Optional[str] = None  # FE, NCFE, ITPA, etc.


class COFileUploadRequest(BaseModel):
    """
    Request model for uploading 4 Excel files for CO processing.

    All 4 files are required for consolidation.
    """
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking (auto-generated if not provided)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "co_session_20250824_123456"
            }
        }


class COProcessingStats(BaseModel):
    """Statistics from CO file processing."""
    total_records_noova: int = Field(..., description="Total records from Noova files")
    total_records_netsuite: int = Field(..., description="Total records from Netsuite files")
    total_consolidated: int = Field(..., description="Total consolidated records")
    matched_with_netsuite: int = Field(..., description="Records matched with Netsuite")
    unmatched_noova: int = Field(..., description="Noova records without Netsuite match")
    costos_fijos_count: int = Field(..., description="Records in Costos Fijos sheet")
    mandato_count: int = Field(..., description="Records in Mandato sheet")
    errors: List[str] = Field(default_factory=list, description="Processing errors")


class COReportSheet(BaseModel):
    """
    Represents one sheet in the CO report Excel.

    Contains the sheet name and column structure information.
    """
    sheet_name: SheetDestination
    column_count: int
    row_count: int
    columns: List[str]


class COProcessingResponse(BaseModel):
    """
    Response from CO file processing endpoint.

    Returns session ID, statistics, and download information.
    """
    success: bool
    session_id: str = Field(..., description="Session ID for tracking")
    stats: COProcessingStats
    sheets: List[COReportSheet] = Field(
        ...,
        description="Information about generated sheets"
    )
    download_url: Optional[str] = Field(
        default=None,
        description="URL to download generated Excel report"
    )
    drive_uploaded: bool = Field(
        default=False,
        description="Whether the report was uploaded to Google Drive"
    )
    drive_url: Optional[str] = Field(
        default=None,
        description="Google Drive URL for the uploaded report"
    )
    message: str = Field(default="Procesamiento completado exitosamente")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "co_session_20250824_123456",
                "stats": {
                    "total_records_noova": 1250,
                    "total_records_netsuite": 1100,
                    "total_consolidated": 1250,
                    "matched_with_netsuite": 1100,
                    "unmatched_noova": 150,
                    "costos_fijos_count": 800,
                    "mandato_count": 450,
                    "errors": []
                },
                "sheets": [
                    {
                        "sheet_name": "Relacion facturas Costos Fijos",
                        "column_count": 18,
                        "row_count": 800,
                        "columns": ["Fecha", "Número factura", "..."]
                    },
                    {
                        "sheet_name": "Relación facturas mandato",
                        "column_count": 16,
                        "row_count": 450,
                        "columns": ["Fecha", "Número factura", "..."]
                    }
                ],
                "download_url": "/api/finance/co/download/co_session_20250824_123456",
                "message": "Procesamiento completado exitosamente"
            }
        }


class COValidationError(BaseModel):
    """Validation error during CO file processing."""
    file_type: FileType
    row: Optional[int] = None
    column: Optional[str] = None
    message: str
    value: Optional[str] = None


class COValidationResponse(BaseModel):
    """
    Response from CO file validation.

    Returns before processing starts to check file structure.
    """
    valid: bool
    errors: List[COValidationError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    file_stats: Dict[FileType, Dict[str, int]] = Field(
        default_factory=dict,
        description="Basic stats per file (row count, column count)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "errors": [],
                "warnings": [
                    "5 registros en Noova sin coincidencia en Netsuite"
                ],
                "file_stats": {
                    "netsuite": {"rows": 500, "columns": 3},
                    "netsuite_nc": {"rows": 50, "columns": 3},
                    "noova_facturas": {"rows": 450, "columns": 10},
                    "noova_notas_credito": {"rows": 55, "columns": 10}
                }
            }
        }


# Output sheet column definitions
COSTOS_FIJOS_COLUMNS = [
    "Codigo del desembolso",
    "Valor Costos Fijos",
    "Seguro + Iva",
    "Int. Corriente Facturado FK",
    "Int. Mora Facturado FK",
    "(-) Retencion en la Fuente",
    "Valor Neto Facturado",
    "Fecha Facturacion",
    "# Factura",
    "Moneda",
    "Nit",
    "Otros Valor"
]

MANDATO_COLUMNS = [
    "Codigo del desembolso",
    "Mes facturacion",
    "Interes Corriente Facturado",
    "Interes Mora Facturado Mandato",
    "Valor Neto Facturado",
    "Fecha Factura",
    "# Factura",
    "Moneda",
    "Nit",
    "Otros Valor"
]


# ============================================================================
# Filter DTOs for Querying Drive Master Excel
# ============================================================================

class COFilterRequest(BaseModel):
    """
    Request model for filtering/querying the CO Drive master Excel.

    Supports filtering by:
    - operaciones: One or more operation codes
    - nit: Client tax ID (partial or exact match)
    - fecha_inicio / fecha_fin: Date range

    All filters can be combined.
    """
    operaciones: Optional[List[str]] = Field(
        default=None,
        description="List of operation codes to filter by (codigo_operacion)"
    )
    nit: Optional[str] = Field(
        default=None,
        description="Client NIT to filter by (exact or partial match)"
    )
    fecha_inicio: Optional[date] = Field(
        default=None,
        description="Start date for date range filter (inclusive)"
    )
    fecha_fin: Optional[date] = Field(
        default=None,
        description="End date for date range filter (inclusive)"
    )
    hoja: Optional[str] = Field(
        default=None,
        description="Sheet to filter: 'costos_fijos' or 'mandato' (default: both)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "operaciones": ["OP-2025-001", "OP-2025-002"],
                "nit": "900123456",
                "fecha_inicio": "2025-01-01",
                "fecha_fin": "2025-12-31",
                "hoja": "costos_fijos"
            }
        }


class COFilteredRecord(BaseModel):
    """
    A single filtered record from the CO Drive master Excel.

    Note: alias are defined for documentation purposes only.
    Serialization uses field names (not aliases) for frontend compatibility.
    """
    codigo_operacion: Optional[str] = Field(None, description="Codigo del desembolso")
    fecha: Optional[str] = Field(None, description="Fecha Facturacion")
    numero_factura: Optional[str] = Field(None, description="# Factura")
    nit: Optional[str] = Field(None, description="Nit")
    moneda: Optional[str] = Field(None, description="Moneda")
    valor_costos_fijos: Optional[float] = Field(None, description="Valor Costos Fijos")
    seguro_iva: Optional[float] = Field(None, description="Seguro + Iva")
    int_corriente: Optional[float] = Field(None, description="Int. Corriente Facturado FK")
    int_mora: Optional[float] = Field(None, description="Int. Mora Facturado FK")
    retencion_fuente: Optional[float] = Field(None, description="(-) Retencion en la Fuente")
    valor_neto: Optional[float] = Field(None, description="Valor Neto Facturado")
    otros_valor: Optional[float] = Field(None, description="Otros Valor")
    hoja_origen: Optional[str] = Field(None, description="Sheet where record was found")

    class Config:
        json_schema_extra = {
            "example": {
                "codigo_operacion": "OP-2025-001",
                "fecha": "2025-08-15",
                "numero_factura": "FE-12345",
                "nit": "900123456",
                "moneda": "COP",
                "valor_costos_fijos": 1500000.00,
                "valor_neto": 1400000.00,
                "hoja_origen": "Relacion facturas Costos Fijos"
            }
        }


class COFilterResponse(BaseModel):
    """
    Response model for CO filter queries.
    """
    success: bool
    total_records: int = Field(..., description="Total number of matching records")
    records: List[COFilteredRecord] = Field(default_factory=list)
    filters_applied: Dict[str, str] = Field(
        default_factory=dict,
        description="Summary of filters that were applied"
    )
    sheets_searched: List[str] = Field(
        default_factory=list,
        description="Sheets that were searched"
    )
    message: str = Field(default="Consulta completada exitosamente")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_records": 25,
                "records": [],
                "filters_applied": {
                    "operaciones": "OP-2025-001, OP-2025-002",
                    "fecha_rango": "2025-01-01 a 2025-12-31"
                },
                "sheets_searched": ["Relacion facturas Costos Fijos", "Relación facturas mandato"],
                "message": "Se encontraron 25 registros"
            }
        }


class CODistinctValuesResponse(BaseModel):
    """
    Response model for getting distinct values from a column.
    Used for autocomplete/dropdown in filter UI.
    """
    success: bool
    field: str = Field(..., description="Field name queried")
    values: List[str] = Field(default_factory=list, description="Unique values found")
    count: int = Field(..., description="Number of unique values")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "field": "nit",
                "values": ["900123456", "900654321", "800111222"],
                "count": 3
            }
        }
