"""
DTOs for Finance Report History.

Data transfer objects for tracking and querying finance report generation
history for both Colombia (CO) and Mexico (MX) operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ReportCountry(str, Enum):
    """Supported countries for finance reports."""
    CO = "CO"
    MX = "MX"


class ReportType(str, Enum):
    """Types of finance reports."""
    FACTURACION = "facturacion"  # Upload and process files
    CONSULTA = "consulta"  # Filter/query existing data
    ZIP_DOWNLOAD = "zip_download"  # Download with PDFs


class ReportStatus(str, Enum):
    """Status of a finance report."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DOWNLOADED = "downloaded"


class FinanceReportCreate(BaseModel):
    """DTO for creating a new finance report record."""
    country: ReportCountry
    report_type: ReportType = ReportType.FACTURACION
    stats: Dict[str, Any] = Field(default_factory=dict)
    filters_applied: Optional[Dict[str, Any]] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    drive_uploaded: bool = False
    drive_url: Optional[str] = None
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "country": "CO",
                "report_type": "facturacion",
                "stats": {
                    "total_records_noova": 100,
                    "total_records_netsuite": 95,
                    "costos_fijos_count": 80,
                    "mandato_count": 20
                },
                "file_name": "Reporte_Facturacion_CO_2025.xlsx",
                "drive_uploaded": True
            }
        }


class FinanceReportDetail(BaseModel):
    """Detailed finance report record for display."""
    id: str
    report_id: str  # FIN-CO-2025-0001
    country: ReportCountry
    report_type: ReportType
    status: ReportStatus
    generated_by: Optional[str] = None
    generated_by_email: Optional[str] = None  # For display
    generated_at: datetime
    stats: Dict[str, Any]
    filters_applied: Optional[Dict[str, Any]] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    drive_uploaded: bool = False
    drive_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "report_id": "FIN-CO-2025-0001",
                "country": "CO",
                "report_type": "facturacion",
                "status": "completed",
                "generated_by": "user-uuid",
                "generated_by_email": "usuario@finkargo.com",
                "generated_at": "2025-11-28T10:30:00Z",
                "stats": {
                    "total_records_noova": 100,
                    "costos_fijos_count": 80,
                    "mandato_count": 20
                },
                "file_name": "Reporte_Facturacion_CO_2025.xlsx",
                "drive_uploaded": True,
                "created_at": "2025-11-28T10:30:00Z",
                "updated_at": "2025-11-28T10:30:00Z"
            }
        }


class FinanceReportSummary(BaseModel):
    """Summary view for report list."""
    id: str
    report_id: str
    country: ReportCountry
    report_type: ReportType
    status: ReportStatus
    generated_by_email: Optional[str] = None
    generated_at: datetime
    stats_summary: str  # Human-readable summary
    drive_uploaded: bool = False

    class Config:
        from_attributes = True


class FinanceHistoryFilter(BaseModel):
    """Filter parameters for querying report history."""
    country: Optional[ReportCountry] = None
    report_type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    generated_by: Optional[str] = None
    limit: int = Field(default=50, le=100, ge=1)
    offset: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "country": "CO",
                "report_type": "facturacion",
                "date_from": "2025-01-01T00:00:00Z",
                "limit": 50,
                "offset": 0
            }
        }


class FinanceReportStats(BaseModel):
    """Statistics for finance reports dashboard."""
    total_reports: int = 0
    reports_today: int = 0
    reports_this_week: int = 0
    reports_this_month: int = 0

    # By country
    co_reports: int = 0
    mx_reports: int = 0

    # By type
    facturacion_count: int = 0
    consulta_count: int = 0
    zip_download_count: int = 0

    # By status
    completed_count: int = 0
    failed_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "total_reports": 150,
                "reports_today": 5,
                "reports_this_week": 25,
                "reports_this_month": 80,
                "co_reports": 100,
                "mx_reports": 50,
                "facturacion_count": 60,
                "consulta_count": 70,
                "zip_download_count": 20,
                "completed_count": 145,
                "failed_count": 5
            }
        }


class FinanceHistoryResponse(BaseModel):
    """Response for history list endpoint."""
    success: bool = True
    total: int
    reports: List[FinanceReportSummary]
    page: int
    page_size: int
    has_more: bool

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total": 150,
                "reports": [],
                "page": 1,
                "page_size": 50,
                "has_more": True
            }
        }
