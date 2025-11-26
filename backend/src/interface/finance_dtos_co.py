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
    fecha: date
    numero_factura: str
    nit: str
    nombre_cliente: str
    email: str
    estado: str
    envio: str
    codigo_operacion: str
    codigo_producto: str
    concepto: str

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
