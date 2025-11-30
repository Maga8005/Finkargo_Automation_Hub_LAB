"""
Tesorería (Treasury) API Routes.

Provides endpoints for payment template conversion from Historial de Pagos
to NetSuite-compatible format.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from typing import Literal
import io
import logging
from datetime import datetime

from src.adapter.rest.rbac_dependencies import require_roles
from src.interface.tesoreria_dtos import HistorialValidationResponse
from src.core.servicios.payment_template_service import payment_template_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/tesoreria",
    tags=["Tesorería - Treasury"]
)

# RBAC dependency - allows tesoreria role and admin (admin bypass is default)
require_tesoreria_role = require_roles(['tesoreria'])


@router.post(
    "/validate/{country}",
    response_model=HistorialValidationResponse,
    summary="Validate Historial de Pagos file",
    description="Upload and validate a Historial de Pagos Excel file for the specified country."
)
async def validate_historial(
    country: Literal["colombia", "mexico"],
    file: UploadFile = File(..., description="Excel file (.xlsx) with payment history"),
    current_user: dict = Depends(require_tesoreria_role)
):
    """
    Validate an uploaded Historial de Pagos Excel file.

    Args:
        country: Target country ('colombia' or 'mexico')
        file: Excel file to validate
        current_user: Authenticated user with tesoreria role

    Returns:
        Validation response with column status, errors, and preview

    Raises:
        HTTPException: 400 if file format is invalid
        HTTPException: 403 if user lacks required role
    """
    logger.info(f"Validate request for {country} by user {current_user.get('id')}")

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo requerido"
        )

    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo inválido. Solo se aceptan archivos .xlsx"
        )

    try:
        response = await payment_template_service.validate_historial(file, country)
        return response

    except Exception as e:
        logger.error(f"Error validating file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al validar archivo: {str(e)}"
        )


@router.post(
    "/convert/{country}",
    summary="Convert Historial de Pagos to NetSuite template",
    description="Convert an uploaded Historial de Pagos Excel file to NetSuite payment application format."
)
async def convert_to_netsuite(
    country: Literal["colombia", "mexico"],
    file: UploadFile = File(..., description="Excel file (.xlsx) with payment history"),
    current_user: dict = Depends(require_tesoreria_role)
):
    """
    Convert Historial de Pagos to NetSuite payment template format.

    Generates an Excel file with one row per payment concept type,
    with appropriate AR account lookups based on country.

    Args:
        country: Target country ('colombia' or 'mexico')
        file: Excel file to convert
        current_user: Authenticated user with tesoreria role

    Returns:
        StreamingResponse with the converted Excel file

    Raises:
        HTTPException: 400 if file format is invalid
        HTTPException: 403 if user lacks required role
        HTTPException: 500 if conversion fails
    """
    logger.info(f"Convert request for {country} by user {current_user.get('id')}")

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo requerido"
        )

    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo inválido. Solo se aceptan archivos .xlsx"
        )

    try:
        # Convert file
        output_bytes, stats = await payment_template_service.convert_to_netsuite_template(
            file, country
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        country_upper = country.upper()[:2]
        output_filename = f"Aplicacion_Pagos_{country_upper}_{timestamp}.xlsx"

        logger.info(
            f"Conversion complete: {stats.source_rows} -> {stats.output_rows} rows, "
            f"file: {output_filename}"
        )

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(output_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "X-Conversion-Stats": (
                    f"source={stats.source_rows};"
                    f"output={stats.output_rows};"
                    f"skipped={stats.skipped_rows};"
                    f"errors={stats.errors_count}"
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error converting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al convertir archivo: {str(e)}"
        )


@router.get(
    "/catalogs/{country}",
    summary="Get AR account catalog for country",
    description="Retrieve the AR account catalog for payment concept lookups."
)
async def get_catalogs(
    country: Literal["colombia", "mexico"],
    current_user: dict = Depends(require_tesoreria_role)
):
    """
    Get AR account catalog for a country.

    Returns the mapping of concept types to AR account IDs.

    Args:
        country: Target country ('colombia' or 'mexico')
        current_user: Authenticated user with tesoreria role

    Returns:
        Dictionary with catalog data
    """
    from src.core.servicios.catalogs.payment_catalogs import (
        COLOMBIA_AR_ACCOUNTS,
        COLOMBIA_NT_AR_ACCOUNTS,
        MEXICO_AR_ACCOUNTS,
    )

    if country == "colombia":
        return {
            "country": country,
            "standard_accounts": COLOMBIA_AR_ACCOUNTS,
            "nt_accounts": COLOMBIA_NT_AR_ACCOUNTS,
            "description": "Colombia AR accounts with standard and Operaciones Cedidas (NT) variants"
        }
    else:
        return {
            "country": country,
            "accounts": MEXICO_AR_ACCOUNTS,
            "description": "México AR accounts for payment concepts"
        }
