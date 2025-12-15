"""
Directory Scanner Module - Data Transfer Objects (DTOs)

This module defines Pydantic DTOs for the local directory scanning feature.
Used to scan local filesystem directories for PDF declaration files and
generate inventory Excel reports.

Author: Finkargo Automation Hub
Date: 2025-12-15
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class LocalDirectoryScanConfigDTO(BaseModel):
    """
    Configuration for local directory scanning.

    Defines parameters for scanning a local file system directory structure
    to build an inventory of PDF declaration files.

    Example:
        {
            "directory_path": "C:/Exchange Declarations/FINKARGO DCS",
            "output_file_path": "C:/Output/inventory_20251103.xlsx",
            "extract_declaration_numbers": true,
            "recursive": true,
            "pdf_extensions": [".pdf", ".PDF"]
        }
    """
    directory_path: str = Field(
        ...,
        min_length=1,
        description="Root directory path to scan for PDFs"
    )
    output_file_path: Optional[str] = Field(
        None,
        description="Output path for inventory Excel file. If None, auto-generates name."
    )
    extract_declaration_numbers: bool = Field(
        default=True,
        description="Whether to extract declaration numbers from PDFs (slower but more complete)"
    )
    recursive: bool = Field(
        default=True,
        description="Whether to scan subdirectories recursively"
    )
    pdf_extensions: List[str] = Field(
        default=['.pdf', '.PDF'],
        description="List of PDF file extensions to scan"
    )
    request_timeout_seconds: int = Field(
        default=600,
        ge=60,
        le=1800,
        description="Request timeout in seconds (default: 600 = 10 minutes, max: 1800 = 30 minutes)"
    )

    model_config = {"from_attributes": True}


class InventoryRecordDTO(BaseModel):
    """
    Single inventory record for a PDF file with extracted metadata.

    Represents one row in the inventory Excel file with folder structure
    metadata and optional extracted declaration data.

    Example:
        {
            "customer_name": "BIIRTUALSCORE SAS",
            "date_folder": "12-09-2025",
            "amount_folder": "11.081,50",
            "pdf_file_path": "C:/FINKARGO DCS/BIIRTUALSCORE SAS/12-09-2025/11.081,50/DC 11.081,50.pdf",
            "pdf_file_name": "DC 11.081,50.pdf",
            "declaration_number": "123456789",
            "extraction_status": "success",
            "extraction_error": null,
            "parsed_date": "2025-09-12T00:00:00",
            "parsed_amount": 11081.50
        }
    """
    customer_name: str = Field(..., description="Customer name from folder structure")
    date_folder: str = Field(..., description="Date folder name (DD-MM-YYYY or month name)")
    amount_folder: str = Field(..., description="Amount folder name")
    pdf_file_path: str = Field(..., description="Absolute path to PDF file")
    pdf_file_name: str = Field(..., description="PDF file name")
    declaration_number: Optional[str] = Field(
        None,
        description="Extracted declaration number (if extraction was performed)"
    )
    extraction_status: str = Field(
        default="pending",
        description="Extraction status: pending, success, partial, failed"
    )
    extraction_error: Optional[str] = Field(
        None,
        description="Error message if extraction failed"
    )
    parsed_date: Optional[datetime] = Field(
        None,
        description="Parsed date from folder name"
    )
    parsed_amount: Optional[float] = Field(
        None,
        description="Parsed amount from folder name"
    )

    model_config = {"from_attributes": True}


class LocalDirectoryScanResultDTO(BaseModel):
    """
    Results from a local directory scan operation.

    Provides statistics about the scan and path to generated inventory file.

    Example:
        {
            "total_pdfs_found": 150,
            "successful_extractions": 142,
            "failed_extractions": 8,
            "output_file_path": "C:/Output/inventory_20251103.xlsx",
            "scan_duration_seconds": 45.3,
            "statistics": {
                "unique_customers": 25,
                "unique_dates": 30,
                "total_amount": 1250000.00,
                "average_amount": 8333.33
            }
        }
    """
    total_pdfs_found: int = Field(..., description="Total number of PDF files found")
    successful_extractions: int = Field(
        default=0,
        description="Number of successful declaration number extractions"
    )
    failed_extractions: int = Field(
        default=0,
        description="Number of failed declaration number extractions"
    )
    output_file_path: str = Field(..., description="Path to generated inventory Excel file")
    scan_duration_seconds: float = Field(..., description="Total scan duration in seconds")
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional statistics (unique customers, dates, amounts)"
    )

    model_config = {"from_attributes": True}


class InventoryFileMetadataDTO(BaseModel):
    """
    Metadata about an inventory Excel file.

    Used to list available inventory files for download.

    Example:
        {
            "file_name": "inventory_20251103_143052.xlsx",
            "file_path": "C:/Output/inventory_20251103_143052.xlsx",
            "created_at": "2025-11-03T14:30:52Z",
            "file_size_bytes": 45678,
            "record_count": 150
        }
    """
    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="Full file path")
    created_at: datetime = Field(..., description="File creation timestamp")
    file_size_bytes: int = Field(..., description="File size in bytes")
    record_count: Optional[int] = Field(
        None,
        description="Number of records in the inventory (if available)"
    )

    model_config = {"from_attributes": True}
