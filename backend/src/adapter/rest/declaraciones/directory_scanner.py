"""
Local Directory Scanner - FastAPI REST Controller

Provides REST API endpoints for scanning local directory structures and generating
inventory Excel files.

Endpoints:
- POST /api/v1/declaraciones/directory-scanner/scan - Trigger directory scan
- GET /api/v1/declaraciones/directory-scanner/inventory-files - List inventory files
- GET /api/v1/declaraciones/directory-scanner/inventory-files/{filename} - Download inventory file

Author: Finkargo Engineering
Date: 2025-11-03
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from typing import List
from pathlib import Path
from datetime import datetime
import time
import os

from src.interface.directory_scanner_dtos import (
    LocalDirectoryScanConfigDTO,
    LocalDirectoryScanResultDTO,
    InventoryFileMetadataDTO
)
from src.core.servicios.declaraciones.local_directory_scanner import LocalDirectoryScanner
from src.core.servicios.declaraciones.local_pdf_extractor import LocalPDFExtractor
from src.core.servicios.declaraciones.inventory_excel_generator import InventoryExcelGenerator
from src.config.supabase_config import get_supabase_client
from supabase import Client


def get_supabase_admin_client() -> Client:
    """Dependency to get Supabase admin client for directory scanning."""
    supabase = get_supabase_client()
    return supabase.admin_client

router = APIRouter(
    prefix="/api/v1/treasury/directory-scanner",
    tags=["Treasury - Directory Scanner"]
)

# Configuration for inventory file storage
INVENTORY_OUTPUT_DIR = os.getenv(
    "INVENTORY_OUTPUT_DIR",
    "C:/Users/Usuario/Finkargo_Automation_Hub/Exchange Declarations and Legalization Process/Inventory Output"
)


@router.post("/scan", response_model=LocalDirectoryScanResultDTO, status_code=status.HTTP_200_OK)
async def scan_local_directory(
    config: LocalDirectoryScanConfigDTO,
    supabase_client: Client = Depends(get_supabase_admin_client)
):
    """
    Scan local directory structure and generate inventory Excel file.

    This endpoint:
    1. Scans the specified directory for PDF files
    2. Extracts metadata from folder structure
    3. Optionally extracts declaration numbers from PDFs
    4. Generates a formatted Excel inventory file
    5. Returns scan results and statistics

    Args:
        config: Scan configuration (directory path, output path, options)
        supabase_client: Supabase client for PDF extraction

    Returns:
        Scan results with statistics and output file path

    Raises:
        HTTPException 400: Invalid directory path
        HTTPException 500: Scan or extraction failed
    """
    try:
        print(f"INFO [DirectoryScannerEndpoint]: Starting directory scan for '{config.directory_path}'")

        start_time = time.time()

        # Initialize scanner
        scanner = LocalDirectoryScanner(pdf_extensions=config.pdf_extensions)

        # Scan directory
        try:
            inventory_records = scanner.scan_directory(
                root_path=config.directory_path,
                recursive=config.recursive
            )
        except ValueError as e:
            print(f"ERROR [DirectoryScannerEndpoint]: Invalid directory path: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid directory path: {str(e)}"
            )

        total_pdfs = len(inventory_records)
        print(f"INFO [DirectoryScannerEndpoint]: Found {total_pdfs} PDFs")

        # Extract declaration numbers if requested
        successful_extractions = 0
        failed_extractions = 0

        if config.extract_declaration_numbers and total_pdfs > 0:
            print(f"INFO [DirectoryScannerEndpoint]: Extracting declaration numbers from {total_pdfs} PDFs")

            extractor = LocalPDFExtractor(supabase_client)

            for record in inventory_records:
                try:
                    # Extract from PDF
                    extraction_result = extractor.extract_from_local_file(record.pdf_file_path)

                    # Update record with extraction results
                    record.declaration_number = extraction_result.get('declaration_number')
                    record.extraction_status = extraction_result.get('extraction_status', 'failed')
                    record.extraction_error = extraction_result.get('error_message')

                    if extraction_result['extraction_status'] in ['success', 'partial']:
                        successful_extractions += 1
                    else:
                        failed_extractions += 1

                except Exception as e:
                    print(f"ERROR [DirectoryScannerEndpoint]: Extraction failed for '{record.pdf_file_name}': {str(e)}")
                    record.extraction_status = 'failed'
                    record.extraction_error = str(e)
                    failed_extractions += 1

            print(f"INFO [DirectoryScannerEndpoint]: Extraction complete: {successful_extractions} successful, {failed_extractions} failed")
        else:
            print("INFO [DirectoryScannerEndpoint]: Skipping declaration number extraction")

        # Generate output file path if not provided
        # Check if output_file_path is None or empty string (type-safe checking)
        print(f"DEBUG [DirectoryScannerEndpoint]: config.output_file_path = {repr(config.output_file_path)}")
        print(f"DEBUG [DirectoryScannerEndpoint]: INVENTORY_OUTPUT_DIR = {repr(INVENTORY_OUTPUT_DIR)}")

        if config.output_file_path is None or (isinstance(config.output_file_path, str) and config.output_file_path.strip() == ""):
            # Ensure output directory exists
            Path(INVENTORY_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file_path = os.path.join(
                INVENTORY_OUTPUT_DIR,
                f"inventory_{timestamp}.xlsx"
            )
            print(f"INFO [DirectoryScannerEndpoint]: Auto-generated output file path: '{output_file_path}'")
        else:
            # Use provided path, but ensure it has .xlsx extension
            output_file_path = config.output_file_path.strip()

            # Ensure the file path is in the inventory output directory and has .xlsx extension
            if not output_file_path.lower().endswith('.xlsx'):
                output_file_path = output_file_path + '.xlsx'

            # If path doesn't include directory, prepend inventory output directory
            if not os.path.isabs(output_file_path) and not os.path.dirname(output_file_path):
                Path(INVENTORY_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                output_file_path = os.path.join(INVENTORY_OUTPUT_DIR, output_file_path)

            print(f"INFO [DirectoryScannerEndpoint]: Using provided output file path: '{output_file_path}'")

        # Validate output_file_path before Excel generation
        if not output_file_path or not output_file_path.strip():
            error_msg = f"CRITICAL: output_file_path is empty! Value: '{output_file_path}', Type: {type(output_file_path)}"
            print(f"ERROR [DirectoryScannerEndpoint]: {error_msg}")
            raise ValueError(error_msg)

        # Generate Excel inventory
        print(f"INFO [DirectoryScannerEndpoint]: Generating Excel inventory at '{output_file_path}'")
        print(f"DEBUG [DirectoryScannerEndpoint]: output_file_path length: {len(output_file_path)}, repr: {repr(output_file_path)}")

        generator = InventoryExcelGenerator()
        output_path = generator.generate_inventory_excel(
            records=inventory_records,
            output_path=output_file_path
        )

        # Calculate statistics
        unique_customers = len(set(r.customer_name for r in inventory_records))
        unique_dates = len(set(r.date_folder for r in inventory_records))
        amounts = [r.parsed_amount for r in inventory_records if r.parsed_amount]
        total_amount = sum(amounts) if amounts else 0

        statistics = {
            'unique_customers': unique_customers,
            'unique_dates': unique_dates,
            'total_amount': total_amount,
            'average_amount': total_amount / len(amounts) if amounts else 0
        }

        # Calculate duration
        scan_duration = time.time() - start_time

        # Build response
        result = LocalDirectoryScanResultDTO(
            total_pdfs_found=total_pdfs,
            successful_extractions=successful_extractions,
            failed_extractions=failed_extractions,
            output_file_path=output_path,
            scan_duration_seconds=scan_duration,
            statistics=statistics
        )

        print(f"SUCCESS [DirectoryScannerEndpoint]: Scan completed in {scan_duration:.2f}s")
        print(f"SUCCESS [DirectoryScannerEndpoint]: Inventory file generated at '{output_path}'")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR [DirectoryScannerEndpoint]: Directory scan failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Directory scan failed: {str(e)}"
        )


@router.get("/inventory-files", response_model=List[InventoryFileMetadataDTO])
async def list_inventory_files():
    """
    List all available inventory Excel files.

    Returns:
        List of inventory file metadata (filename, size, creation date, etc.)

    Raises:
        HTTPException 500: Failed to list files
    """
    try:
        print(f"INFO [DirectoryScannerEndpoint]: Listing inventory files from '{INVENTORY_OUTPUT_DIR}'")

        # Ensure output directory exists
        output_dir = Path(INVENTORY_OUTPUT_DIR)
        if not output_dir.exists():
            print("WARN [DirectoryScannerEndpoint]: Output directory does not exist, creating it")
            output_dir.mkdir(parents=True, exist_ok=True)
            return []

        # Find all Excel files
        inventory_files = []
        for file_path in output_dir.glob("inventory_*.xlsx"):
            try:
                stats = file_path.stat()

                metadata = InventoryFileMetadataDTO(
                    file_name=file_path.name,
                    file_path=str(file_path.absolute()),
                    created_at=datetime.fromtimestamp(stats.st_ctime),
                    file_size_bytes=stats.st_size,
                    record_count=None  # Could be extracted from Excel if needed
                )

                inventory_files.append(metadata)

            except Exception as e:
                print(f"WARN [DirectoryScannerEndpoint]: Failed to read file metadata for '{file_path.name}': {str(e)}")
                continue

        # Sort by creation date (newest first)
        inventory_files.sort(key=lambda x: x.created_at, reverse=True)

        print(f"SUCCESS [DirectoryScannerEndpoint]: Found {len(inventory_files)} inventory files")

        return inventory_files

    except Exception as e:
        print(f"ERROR [DirectoryScannerEndpoint]: Failed to list inventory files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inventory files: {str(e)}"
        )


@router.get("/inventory-files/{filename}")
async def download_inventory_file(filename: str):
    """
    Download a specific inventory Excel file.

    Args:
        filename: Name of the inventory file to download

    Returns:
        FileResponse with Excel file

    Raises:
        HTTPException 400: Invalid filename (directory traversal attempt)
        HTTPException 404: File not found
        HTTPException 500: Download failed
    """
    try:
        print(f"INFO [DirectoryScannerEndpoint]: Download requested for '{filename}'")

        # Validate filename to prevent directory traversal attacks
        if ".." in filename or "/" in filename or "\\" in filename:
            print(f"ERROR [DirectoryScannerEndpoint]: Invalid filename (directory traversal attempt): '{filename}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )

        # Ensure filename matches expected pattern
        if not filename.startswith("inventory_") or not filename.endswith(".xlsx"):
            print(f"ERROR [DirectoryScannerEndpoint]: Invalid filename format: '{filename}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename format"
            )

        # Build file path
        file_path = Path(INVENTORY_OUTPUT_DIR) / filename

        # Check if file exists
        if not file_path.exists():
            print(f"ERROR [DirectoryScannerEndpoint]: File not found: '{file_path}'")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory file '{filename}' not found"
            )

        print(f"SUCCESS [DirectoryScannerEndpoint]: Serving file '{filename}'")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR [DirectoryScannerEndpoint]: Download failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )
