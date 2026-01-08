"""
DTOs for Mexico (MX) Filter functionality.

Data transfer objects for querying and filtering the MX master Excel file.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date


class MXFilterRequest(BaseModel):
    """Request for filtering MX master Excel data."""
    operaciones: Optional[List[str]] = Field(
        default=None,
        description="Lista de códigos de operación a filtrar"
    )
    rfc: Optional[str] = Field(
        default=None,
        description="RFC del receptor (búsqueda parcial)"
    )
    fecha_inicio: Optional[date] = Field(
        default=None,
        description="Fecha inicio del rango (YYYY-MM-DD)"
    )
    fecha_fin: Optional[date] = Field(
        default=None,
        description="Fecha fin del rango (YYYY-MM-DD)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "operaciones": ["OP-001", "OP-002"],
                "rfc": "XAXX010101000",
                "fecha_inicio": "2025-01-01",
                "fecha_fin": "2025-12-31"
            }
        }


class MXFilteredRecord(BaseModel):
    """A single filtered record from MX master Excel."""
    uuid: Optional[str] = None
    codigo_operacion: Optional[str] = None
    conceptos: Optional[str] = None
    fecha_emision: Optional[str] = None
    rfc_receptor: Optional[str] = None
    razon_receptor: Optional[str] = None
    subtotal: Optional[float] = None
    iva_trasladado: Optional[float] = None
    iva_exento: Optional[float] = None
    total: Optional[float] = None
    uuid_relacionados: Optional[str] = None
    tipo_comprobante: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "uuid": "ABC123-DEF456-GHI789",
                "codigo_operacion": "OP-001",
                "conceptos": "Intereses por Préstamo",
                "fecha_emision": "2025-01-15",
                "rfc_receptor": "XAXX010101000",
                "razon_receptor": "Empresa S.A. de C.V.",
                "subtotal": 1000.00,
                "iva_trasladado": 160.00,
                "iva_exento": 0.00,
                "total": 1160.00,
                "uuid_relacionados": "XYZ789-ABC123",
                "tipo_comprobante": "Ingreso"
            }
        }


class MXFilterResponse(BaseModel):
    """Response for MX filter operation."""
    success: bool = True
    total_records: int = 0
    records: List[MXFilteredRecord] = Field(default_factory=list)
    filters_applied: Dict[str, str] = Field(default_factory=dict)
    total_amount: float = 0.0
    total_subtotal: float = 0.0
    total_iva: float = 0.0
    message: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_records": 50,
                "records": [],
                "filters_applied": {"operaciones": "OP-001, OP-002"},
                "total_amount": 58000.00,
                "total_subtotal": 50000.00,
                "total_iva": 8000.00,
                "message": "Se encontraron 50 registros"
            }
        }


class MXDistinctValuesResponse(BaseModel):
    """Response for distinct values query."""
    success: bool = True
    field: str = ""
    values: List[str] = Field(default_factory=list)
    count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "field": "rfc",
                "values": ["XAXX010101000", "XEXX010101000"],
                "count": 2
            }
        }
