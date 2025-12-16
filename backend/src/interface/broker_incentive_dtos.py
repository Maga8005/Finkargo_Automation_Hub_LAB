"""
Broker Incentive Extraction DTOs

This module defines Pydantic DTOs for the broker contract incentive extraction feature.
Used by the Alianzas department to scan directories and extract incentive percentages
from broker contracts.

Author: Finkargo Automation Hub
Date: 2025-12-16
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ContractType(str, Enum):
    """Type of broker contract."""
    BONO = "bono"
    INCENTIVOS = "incentivos"
    UNKNOWN = "unknown"


class SignatoryInfo(BaseModel):
    """
    Information about a contract signatory.

    Extracted from the signature section of broker contracts.
    """
    name: Optional[str] = Field(
        None,
        description="Signatory name extracted from contract"
    )
    rfc: Optional[str] = Field(
        None,
        description="RFC (Mexican tax ID) of the signatory"
    )

    model_config = {"from_attributes": True}


class BrokerIncentiveData(BaseModel):
    """
    Extracted incentive data from a broker contract.

    Contains all fields extracted from a single PDF contract,
    including broker identification, incentive percentages, and metadata.

    Example:
        {
            "broker_name": "Broker XYZ",
            "contract_date": "2024-05-15",
            "rfc": "XAXX010101000",
            "signatory_name": "Juan Pérez",
            "credit_line_incentive_pct": 2.5,
            "operations_incentive_pct": 1.0,
            "contract_type": "bono",
            "pdf_path": "/path/to/contract.pdf",
            "extraction_date": "2025-12-16T10:30:00",
            "warnings": ["RFC not found in document"]
        }
    """
    broker_name: str = Field(
        ...,
        description="Broker name extracted from folder name"
    )
    contract_date: Optional[str] = Field(
        None,
        description="Contract date extracted from folder name (YYYY-MM-DD format)"
    )
    rfc: Optional[str] = Field(
        None,
        description="RFC (Mexican tax ID) extracted from contract signature section"
    )
    signatory_name: Optional[str] = Field(
        None,
        description="Signatory name extracted from contract signature section"
    )
    credit_line_incentive_pct: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Credit line opening incentive percentage (Bono apertura)"
    )
    operations_incentive_pct: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Operations incentive percentage"
    )
    contract_type: ContractType = Field(
        default=ContractType.UNKNOWN,
        description="Type of contract (bono, incentivos, or unknown)"
    )
    pdf_path: str = Field(
        ...,
        description="Full path to the source PDF file"
    )
    extraction_date: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp when extraction was performed"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings encountered during extraction"
    )
    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for extraction (0.0-1.0)"
    )

    model_config = {"from_attributes": True}


class BrokerContractScanConfigDTO(BaseModel):
    """
    Configuration for broker contract directory scanning.

    Defines parameters for scanning a local file system directory structure
    to extract incentive data from broker contract PDFs.

    Example:
        {
            "directory_path": "/Users/alianzas/Brokers",
            "include_subfolders": true,
            "output_file_path": "/tmp/broker_incentives_20251216.xlsx"
        }
    """
    directory_path: str = Field(
        ...,
        min_length=1,
        description="Root directory path containing broker folders"
    )
    include_subfolders: bool = Field(
        default=True,
        description="Whether to scan subfolders within the root directory"
    )
    output_file_path: Optional[str] = Field(
        None,
        description="Output path for Excel file. If None, auto-generates name."
    )
    request_timeout_seconds: int = Field(
        default=1800,
        ge=60,
        le=3600,
        description="Request timeout in seconds (default: 1800 = 30 minutes, max: 3600 = 1 hour)"
    )

    model_config = {"from_attributes": True}


class BrokerContractScanResultDTO(BaseModel):
    """
    Results from a broker contract directory scan operation.

    Provides statistics about the scan and path to generated Excel file.

    Example:
        {
            "total_folders_found": 25,
            "total_pdfs_processed": 22,
            "successful_extractions": 18,
            "failed_extractions": 4,
            "output_file_path": "/tmp/broker_incentives_20251216.xlsx",
            "scan_duration_seconds": 45.3,
            "records": [...],
            "statistics": {
                "bono_contracts": 12,
                "incentivos_contracts": 6,
                "unknown_contracts": 4,
                "average_credit_line_pct": 2.1,
                "average_operations_pct": 1.5
            }
        }
    """
    total_folders_found: int = Field(
        ...,
        description="Total number of broker folders found"
    )
    total_pdfs_processed: int = Field(
        ...,
        description="Total number of PDF files processed"
    )
    successful_extractions: int = Field(
        default=0,
        description="Number of successful incentive extractions"
    )
    failed_extractions: int = Field(
        default=0,
        description="Number of failed extractions"
    )
    output_file_path: str = Field(
        ...,
        description="Path to generated Excel file"
    )
    scan_duration_seconds: float = Field(
        ...,
        description="Total scan duration in seconds"
    )
    records: List[BrokerIncentiveData] = Field(
        default_factory=list,
        description="List of extracted broker incentive records"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics (contract types, averages, etc.)"
    )

    model_config = {"from_attributes": True}
