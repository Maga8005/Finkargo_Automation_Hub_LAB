"""
Operations Department - FastAPI Routes
Handles contract generation requests and approved contract downloads
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import io

from src.config.supabase_config import get_supabase_client
from src.repositorio.client_repository import ClientRepository
from src.repositorio.contract_repository import ContractRepository
from src.repositorio.template_repository import TemplateRepository
from src.core.servicios.contract_service import ContractService
from src.core.servicios.document_service import DocumentService
from src.core.servicios.rut_parser_service import RUTParserService
from src.core.servicios.landingai_rut_parser_service import LandingAIRUTParserService
from src.core.servicios.cotizacion_parser_service import CotizacionParserService
from src.core.servicios.bank_certificate_parser_service import BankCertificateParserService
from src.adapter.rest.rbac_dependencies import require_operations_role
from src.interface.legal_dtos import (
    ContractGenerationRequest,
    ContractGenerationResponse,
    ContractGenerationDetail,
    ContractType,
    CotizacionData,
    SolicitudDesembolsoRequest,
    BankCertificateData,
    InstruccionMandatoRequest,
    DIANMandatoRequest,
)

router = APIRouter(prefix="/api/operations", tags=["Operations"])


# Dependency to get repositories
def get_client_repo():
    """Get client repository with admin client (bypasses RLS)"""
    supabase = get_supabase_client()
    return ClientRepository(supabase.admin_client)


def get_contract_repo():
    """Get contract repository with admin client (bypasses RLS)"""
    supabase = get_supabase_client()
    return ContractRepository(supabase.admin_client)


def get_template_repo():
    """Get template repository with admin client (bypasses RLS)"""
    supabase = get_supabase_client()
    return TemplateRepository(supabase.admin_client)


def get_contract_service(
    client_repo: ClientRepository = Depends(get_client_repo),
    contract_repo: ContractRepository = Depends(get_contract_repo),
    template_repo: TemplateRepository = Depends(get_template_repo),
):
    """Get contract service with document service"""
    supabase = get_supabase_client()
    document_service = DocumentService(supabase_client=supabase.admin_client)
    return ContractService(client_repo, contract_repo, template_repo, document_service)


# ==================== Contract Generation Endpoints ====================

@router.post("/contracts/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def request_contract_generation(
    client_nit: str = Form(..., description="Client NIT"),
    contract_type: str = Form(..., description="Contract type (activos, otrosi, inventario_bodega)"),
    rut_file: Optional[UploadFile] = File(None, description="RUT PDF document (required for inventario_bodega)"),
    use_ai_extraction: Optional[bool] = Form(False, description="Use LandingAI for AI-powered RUT extraction (for scanned PDFs)"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_operations_role)
):
    """
    Request a new contract generation (Operations role or Admin required)

    This creates a contract in UNDER_REVIEW status for Legal to approve.

    For Inventario Bodega contracts, a RUT document must be uploaded to extract custodian information.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Log incoming request
    logger.info(f"Contract generation request received - NIT: {client_nit}, Type: {contract_type}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Get user_id from authenticated user (dict)
        user_id = current_user['id']

        # Validate contract type
        try:
            contract_type_enum = ContractType(contract_type)
        except ValueError as e:
            logger.error(f"Invalid contract type '{contract_type}' for NIT {client_nit}: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid contract type: {contract_type}. Must be one of: activos, otrosi, inventario_bodega"
            )

        # Parse custodian data from RUT if Inventario Bodega
        custodian_data = None
        if contract_type_enum == ContractType.INVENTARIO_BODEGA:
            if not rut_file:
                raise HTTPException(
                    status_code=400,
                    detail="RUT document is required for Inventario Bodega contracts"
                )

            # Validate file type
            if rut_file.content_type != 'application/pdf':
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {rut_file.content_type}. Only PDF files are allowed"
                )

            # Validate file size (5MB limit)
            rut_bytes = await rut_file.read()
            if len(rut_bytes) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="RUT file size exceeds 5MB limit"
                )

            # Parse RUT document - use AI extraction if requested
            logger.info(f"Parsing RUT document: {rut_file.filename}, AI extraction: {use_ai_extraction}")

            try:
                if use_ai_extraction:
                    logger.info("Using LandingAI for RUT extraction (user requested AI mode)")
                    parser = LandingAIRUTParserService()
                else:
                    logger.info("Using standard text-based RUT extraction")
                    parser = RUTParserService()

                custodian_data = parser.parse_rut_pdf(rut_bytes)
                logger.info(f"RUT parsed successfully for custodian: {custodian_data.nombre_operador_custodio}")
            except ValueError as e:
                logger.error(f"RUT parsing failed: {e}")
                extraction_method = "AI extraction" if use_ai_extraction else "Text extraction"
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing RUT document ({extraction_method}): {str(e)}"
                )
            except Exception as e:
                logger.error(f"Unexpected error parsing RUT: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse RUT document: {str(e)}"
                )

        # Create request object
        request = ContractGenerationRequest(
            client_nit=client_nit,
            contract_type=contract_type_enum,
            custodian_data=custodian_data
        )

        contract = await service.generate_contract(request, user_id)
        # Handle both dict and object response types
        contract_id = contract.contract_id if hasattr(contract, 'contract_id') else contract.get('contract_id', 'unknown')
        logger.info(f"Contract generated successfully - Contract ID: {contract_id}, NIT: {client_nit}, Type: {contract_type}")
        return contract
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error for NIT {client_nit}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating contract for NIT {client_nit}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Solicitud de Desembolso Endpoints ====================

@router.post("/contracts/solicitud-desembolso/parse-cotizacion", response_model=CotizacionData)
async def parse_cotizacion_pdf(
    file: UploadFile = File(..., description="Cotización PDF document"),
    current_user: dict = Depends(require_operations_role)
):
    """
    Parse Cotización PDF and extract disbursement request data (Operations role or Admin required)

    This endpoint extracts structured data from Cotización PDFs including:
    - Quote number (numero_cotizacion)
    - Credit contract date
    - Legal representative information
    - Anexo I table items with amounts
    - Total amount

    Returns extracted data for form pre-population
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Cotización PDF parse request - File: {file.filename}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Validate file type
        if file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed"
            )

        # Validate file size (5MB limit)
        pdf_bytes = await file.read()
        if len(pdf_bytes) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="PDF file size exceeds 5MB limit"
            )

        # Parse Cotización document
        logger.info(f"Parsing Cotización document: {file.filename}")
        parser = CotizacionParserService()

        try:
            cotizacion_data = parser.parse_cotizacion(pdf_bytes)
            logger.info(f"Cotización parsed successfully - Quote: {cotizacion_data.numero_cotizacion}, Items: {len(cotizacion_data.anexo_items)}")
            return cotizacion_data
        except ValueError as e:
            logger.error(f"Cotización parsing failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Error parsing Cotización document: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing Cotización: {e}", exc_info=True)
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse Cotización document: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Cotización PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/solicitud-desembolso/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_solicitud_desembolso(
    request: SolicitudDesembolsoRequest,
    service: ContractService = Depends(get_contract_service),
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Generate Solicitud de Desembolso contract (Operations role or Admin required)

    This creates a Solicitud de Desembolso contract in UNDER_REVIEW status for Legal approval.

    The request must include:
    - client_nit: Client NIT for database lookup
    - numero_cotizacion_desembolso: Quote number
    - fecha_contrato_credito: Credit contract date (ISO format)
    - monto: Total disbursement amount
    - dias_plazo: Term in days (30-180)
    - anexo_items: List of Anexo I table items

    Returns the created contract with ID format: PLSD-YYYY-XXX
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Solicitud de Desembolso generation request - NIT: {request.client_nit}, Quote: {request.numero_cotizacion_desembolso}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Get user_id from authenticated user
        user_id = current_user['id']

        # Validate client exists
        client = await client_repo.get_by_nit(request.client_nit)
        if not client:
            logger.error(f"Client not found with NIT: {request.client_nit}")
            raise HTTPException(
                status_code=404,
                detail=f"Client with NIT {request.client_nit} not found"
            )

        # Build data snapshot combining client data + solicitud data
        from decimal import Decimal
        cupo = client.get('cupo_plataforma')
        data_snapshot = {
            # Client data (client is a dict from repository)
            "nit": client['nit'],
            "nombre_importador": client['nombre_importador'],
            "representante_legal": client['representante_legal'],
            "cedula_representante": client['cedula_representante'],
            "ciudad_domicilio": client['ciudad_domicilio'],
            "cupo_plataforma": float(cupo) if cupo is not None and isinstance(cupo, (Decimal, int, float, str)) else cupo,
            "direccion_comercial": client.get('direccion_comercial'),
            "tipo_identificacion_representante": client.get('tipo_identificacion_representante'),
            # Solicitud de Desembolso specific data
            "numero_cotizacion_desembolso": request.numero_cotizacion_desembolso,
            "fecha_contrato_credito": request.fecha_contrato_credito,
            "monto": float(request.monto),
            "dias_plazo": request.dias_plazo,
            "anexo_items": [
                {
                    "acreedor": item.acreedor,
                    "numero_instrumento": item.numero_instrumento,
                    "monto": float(item.monto)
                }
                for item in request.anexo_items
            ]
        }

        # Create contract generation request
        contract_request = ContractGenerationRequest(
            client_nit=request.client_nit,
            contract_type=ContractType.PL_CO_SOLICITUD_DESEMBOLSO,
            custodian_data=None  # Not needed for Solicitud de Desembolso
        )

        # Generate contract with custom data snapshot
        contract = await service.generate_contract(
            request=contract_request,
            user_id=user_id,
            custom_data_snapshot=data_snapshot
        )

        contract_id = contract.contract_id if hasattr(contract, 'contract_id') else contract.get('contract_id', 'unknown')
        logger.info(f"Solicitud de Desembolso generated successfully - Contract ID: {contract_id}, NIT: {request.client_nit}, Quote: {request.numero_cotizacion_desembolso}")
        return contract

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error for NIT {request.client_nit}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating Solicitud de Desembolso for NIT {request.client_nit}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/approved", response_model=List[ContractGenerationDetail])
async def get_approved_contracts(
    contract_type: Optional[str] = None,
    contract_types: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    client_name: Optional[str] = None,
    client_nit: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    cupo_min: Optional[float] = None,
    cupo_max: Optional[float] = None,
    contract_repo: ContractRepository = Depends(get_contract_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Get all approved contracts for Operations team (Operations role or Admin required)

    Query Parameters:
        contract_type: Optional filter by single contract type
        contract_types: Optional filter by multiple contract types (comma-separated)
        sort_by: Optional field to sort by (contract_id, contract_type, client_nit, reviewed_at,
                 data_snapshot->nombre_importador, data_snapshot->cupo_plataforma)
        sort_order: Optional sort order ('asc' or 'desc', defaults to 'desc')
        client_name: Optional filter by client name (partial match, case-insensitive)
        client_nit: Optional filter by NIT (partial match)
        date_from: Optional filter by approval date >= this date (ISO 8601 format)
        date_to: Optional filter by approval date <= this date (ISO 8601 format)
        cupo_min: Optional filter by credit limit >= this value
        cupo_max: Optional filter by credit limit <= this value

    Returns contracts with approved status and document URLs for download
    """
    try:
        # Validate sort_order
        validated_sort_order = sort_order if sort_order in ['asc', 'desc'] else 'desc'

        # Validate date range
        if date_from and date_to:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                if from_date > to_date:
                    raise HTTPException(
                        status_code=400,
                        detail="date_from must be less than or equal to date_to"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                )

        # Validate credit limit range
        if cupo_min is not None and cupo_max is not None:
            if cupo_min > cupo_max:
                raise HTTPException(
                    status_code=400,
                    detail="cupo_min must be less than or equal to cupo_max"
                )

        # Parse contract_types if provided (comma-separated string)
        contract_types_list: Optional[List[str]] = None
        if contract_types:
            contract_types_list = [ct.strip() for ct in contract_types.split(',') if ct.strip()]
        elif contract_type:
            # Single contract_type for backward compatibility
            contract_types_list = [contract_type]

        contracts = await contract_repo.get_approved_contracts(
            contract_types=contract_types_list,
            sort_by=sort_by,
            sort_order=validated_sort_order,
            client_name=client_name,
            client_nit=client_nit,
            date_from=date_from,
            date_to=date_to,
            cupo_min=cupo_min,
            cupo_max=cupo_max
        )
        return contracts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}", response_model=ContractGenerationDetail)
async def get_contract_details(
    contract_id: UUID = Path(..., description="Contract UUID"),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_operations_role)
):
    """Get contract details by ID (Operations role or Admin required)"""
    contract = await service.get_contract_details(str(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.get("/contracts/{contract_id}/download/pdf")
async def download_approved_contract_pdf(
    contract_id: UUID = Path(..., description="Contract UUID"),
    contract_repo: ContractRepository = Depends(get_contract_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Download approved contract PDF from storage (Operations role or Admin required)

    Args:
        contract_id: Contract UUID

    Returns:
        StreamingResponse with PDF file from Supabase Storage
    """
    try:
        # Get contract
        contract = await contract_repo.get_by_id(str(contract_id))
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Check if approved
        if contract['status'] != 'approved':
            raise HTTPException(
                status_code=400,
                detail=f"Contract is not approved. Current status: {contract['status']}"
            )

        # Check if PDF URL exists
        if not contract.get('approved_document_url'):
            raise HTTPException(
                status_code=404,
                detail="Approved PDF not available. Please contact Legal department."
            )

        # Get Supabase client
        supabase = get_supabase_client()

        # Download from storage
        # The approved_document_url is a public URL, so we can redirect
        # Or we can download and stream it
        from urllib.parse import urlparse
        pdf_url = contract['approved_document_url']

        # Extract bucket and path from URL
        # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
        parsed = urlparse(pdf_url)
        path_parts = parsed.path.split('/storage/v1/object/public/')
        if len(path_parts) < 2:
            raise HTTPException(status_code=500, detail="Invalid storage URL format")

        bucket_and_path = path_parts[1]
        bucket_name = bucket_and_path.split('/')[0]
        file_path = '/'.join(bucket_and_path.split('/')[1:])

        # Download file
        pdf_bytes = supabase.storage.from_(bucket_name).download(file_path)

        filename = f"{contract['contract_id']}_approved.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")


@router.get("/contracts/{contract_id}/download/docx")
async def download_approved_contract_docx(
    contract_id: UUID = Path(..., description="Contract UUID"),
    contract_repo: ContractRepository = Depends(get_contract_repo),
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_operations_role)
):
    """
    Download approved contract as DOCX file (Operations role or Admin required)

    Generates the Word document on-the-fly using the contract data snapshot.
    File is named using pattern: {contract_code}-{sanitized_client_name}.docx

    Args:
        contract_id: Contract UUID

    Returns:
        StreamingResponse with DOCX file
    """
    import logging
    import re
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting DOCX download for contract {contract_id}")

        # Get contract
        contract = await contract_repo.get_by_id(str(contract_id))
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Check if approved
        if contract['status'] != 'approved':
            raise HTTPException(
                status_code=400,
                detail=f"Contract is not approved. Current status: {contract['status']}"
            )

        # Generate DOCX using ContractService
        docx_bytes = await service.generate_contract_document(str(contract_id))
        logger.info(f"DOCX generated successfully for contract {contract_id}")

        # Build filename: {contract_code}-{sanitized_client_name}.docx
        contract_code = contract.get('contract_id', str(contract_id))
        data_snapshot = contract.get('data_snapshot', {})
        client_name = data_snapshot.get('nombre_importador', 'cliente')

        # Sanitize client name for filename
        # Replace spaces with underscores, remove special characters, truncate to 50 chars
        sanitized_name = re.sub(r'[^\w\s-]', '', client_name)  # Remove special chars
        sanitized_name = re.sub(r'\s+', '_', sanitized_name)  # Replace spaces with underscores
        sanitized_name = sanitized_name[:50]  # Truncate to 50 characters

        filename = f"{contract_code}-{sanitized_name}.docx"

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"ValueError in DOCX download: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in DOCX download: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating DOCX: {str(e)}")


# ==================== Instrucción de Mandato Endpoints ====================

@router.post("/contracts/instruccion-mandato/parse-cotizacion", response_model=CotizacionData)
async def parse_cotizacion_for_mandato(
    file: UploadFile = File(..., description="Cotización PDF document"),
    current_user: dict = Depends(require_operations_role)
):
    """
    Parse Cotización PDF for Instrucción de Mandato (Operations role or Admin required)

    This endpoint extracts structured data from Cotización PDFs including:
    - Quote number (numero_cotizacion)
    - Credit contract date
    - Anexo I table items (creditors)
    - Total amount

    Returns extracted data for form pre-population
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Cotización PDF parse request for Mandato - File: {file.filename}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Validate file type
        if file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed"
            )

        # Validate file size (5MB limit)
        pdf_bytes = await file.read()
        if len(pdf_bytes) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="PDF file size exceeds 5MB limit"
            )

        # Parse Cotización document
        logger.info(f"Parsing Cotización document: {file.filename}")
        parser = CotizacionParserService()

        try:
            cotizacion_data = parser.parse_cotizacion(pdf_bytes)
            logger.info(f"Cotización parsed successfully - Quote: {cotizacion_data.numero_cotizacion}, Items: {len(cotizacion_data.anexo_items)}")
            return cotizacion_data
        except ValueError as e:
            logger.error(f"Cotización parsing failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Error parsing Cotización document: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing Cotización: {e}", exc_info=True)
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse Cotización document: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Cotización PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/instruccion-mandato/parse-bank-certificate", response_model=BankCertificateData)
async def parse_bank_certificate(
    file: UploadFile = File(..., description="Bank Certificate PDF document"),
    current_user: dict = Depends(require_operations_role)
):
    """
    Parse Bank Certificate PDF and extract creditor bank account information (Operations role or Admin required)

    This endpoint extracts structured data from Bank Certificate PDFs including:
    - Company name (razon_social)
    - NIT (Colombian tax ID)
    - Bank name (banco)
    - Account type (tipo_cuenta)
    - Account number (numero_cuenta)

    Supports formats from major Colombian banks (Bancolombia, BBVA, etc.)

    Returns extracted data for form pre-population
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Bank Certificate PDF parse request - File: {file.filename}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Validate file type
        if file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed"
            )

        # Validate file size (5MB limit)
        pdf_bytes = await file.read()
        if len(pdf_bytes) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="PDF file size exceeds 5MB limit"
            )

        # Parse Bank Certificate document
        logger.info(f"Parsing Bank Certificate document: {file.filename}")
        parser = BankCertificateParserService()

        try:
            certificate_data = parser.parse_bank_certificate(pdf_bytes)
            logger.info(f"Bank Certificate parsed successfully - Company: {certificate_data.razon_social}, NIT: {certificate_data.nit}")
            return certificate_data
        except ValueError as e:
            logger.error(f"Bank Certificate parsing failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Error parsing Bank Certificate: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing Bank Certificate: {e}", exc_info=True)
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse Bank Certificate: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Bank Certificate PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/instruccion-mandato/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_instruccion_mandato(
    request: InstruccionMandatoRequest,
    service: ContractService = Depends(get_contract_service),
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Generate Instrucción de Mandato contract (Operations role or Admin required)

    This creates an Instrucción de Mandato contract in UNDER_REVIEW status for Legal approval.

    The request must include:
    - client_nit: Client NIT for database lookup
    - numero_cotizacion_desembolso: Quote number
    - fecha_contrato_mandato: Mandate contract date (ISO format)
    - monto: Total amount to transfer
    - acreedores: List of creditors (1-3) with bank account information

    Returns the created contract with ID format: ACT-YYYY-XXX
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Instrucción de Mandato generation request - NIT: {request.client_nit}, Quote: {request.numero_cotizacion_desembolso}, Creditors: {len(request.acreedores)}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Get user_id from authenticated user
        user_id = current_user['id']

        # Validate client exists
        client = await client_repo.get_by_nit(request.client_nit)
        if not client:
            logger.error(f"Client not found with NIT: {request.client_nit}")
            raise HTTPException(
                status_code=404,
                detail=f"Client with NIT {request.client_nit} not found"
            )

        # Build data snapshot combining client data + mandato data
        from decimal import Decimal
        cupo = client.get('cupo_plataforma')

        # Convert acreedores to list of dicts for storage
        acreedores_dicts = [
            {
                "razon_social": acreedor.razon_social,
                "nit": acreedor.nit,
                "banco": acreedor.banco,
                "tipo_cuenta": acreedor.tipo_cuenta,
                "numero_cuenta": acreedor.numero_cuenta,
            }
            for acreedor in request.acreedores
        ]

        data_snapshot = {
            # Client data (client is a dict from repository)
            "nit": client['nit'],
            "nombre_importador": client['nombre_importador'],
            "representante_legal": client['representante_legal'],
            "cedula_representante": client['cedula_representante'],
            "ciudad_domicilio": client['ciudad_domicilio'],
            "cupo_plataforma": float(cupo) if cupo is not None and isinstance(cupo, (Decimal, int, float, str)) else cupo,
            "direccion_comercial": client.get('direccion_comercial'),
            "tipo_identificacion_representante": client.get('tipo_identificacion_representante'),
            # Instrucción de Mandato specific data
            "numero_cotizacion_desembolso": request.numero_cotizacion_desembolso,
            "fecha_contrato_mandato": request.fecha_contrato_mandato,
            "monto": float(request.monto),
            "acreedores": acreedores_dicts,
        }

        logger.info(f"Prepared data snapshot with {len(acreedores_dicts)} creditors")

        # Create contract generation request
        contract_request = ContractGenerationRequest(
            client_nit=request.client_nit,
            contract_type=ContractType.PL_CO_MANDATO_IM,
            custodian_data=None  # Not needed for Instrucción de Mandato
        )

        # Generate contract with custom data snapshot
        contract = await service.generate_contract(
            request=contract_request,
            user_id=user_id,
            custom_data_snapshot=data_snapshot
        )

        contract_id = contract.get('contract_id', 'unknown')
        logger.info(f"Generated Instrucción de Mandato contract: {contract_id}")

        # Return response
        return ContractGenerationResponse(
            id=contract['id'],
            contract_id=contract['contract_id'],
            contract_type=contract['contract_type'],
            client_nit=contract['client_nit'],
            status=contract['status'],
            generated_at=contract['generated_at'],
            pdf_url=contract.get('pdf_url'),
            approved_document_url=contract.get('approved_document_url'),
            data_snapshot=contract['data_snapshot']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Instrucción de Mandato: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating contract: {str(e)}")


# ==================== DIAN Mandato (IM) Endpoints ====================

@router.post("/contracts/dian-mandato/parse-cotizacion", response_model=CotizacionData)
async def parse_cotizacion_for_dian_mandato(
    file: UploadFile = File(..., description="Cotización PDF document"),
    current_user: dict = Depends(require_operations_role)
):
    """
    Parse Cotización PDF for DIAN Mandato (IM) (Operations role or Admin required)

    This endpoint reuses the same Cotización parser as Instrucción de Mandato.
    Returns extracted data for form pre-population.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Cotización PDF parse request for DIAN Mandato - File: {file.filename}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Validate file type
        if file.content_type != 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed"
            )

        # Validate file size (5MB limit)
        pdf_bytes = await file.read()
        if len(pdf_bytes) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="PDF file size exceeds 5MB limit"
            )

        # Parse Cotización document
        logger.info(f"Parsing Cotización document: {file.filename}")
        parser = CotizacionParserService()

        try:
            cotizacion_data = parser.parse_cotizacion(pdf_bytes)
            logger.info(f"Cotización parsed successfully - Quote: {cotizacion_data.numero_cotizacion}")
            return cotizacion_data
        except ValueError as e:
            logger.error(f"Cotización parsing failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Error parsing Cotización document: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing Cotización: {e}", exc_info=True)
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse Cotización document: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Cotización PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts/dian-mandato/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_dian_mandato(
    request: DIANMandatoRequest,
    service: ContractService = Depends(get_contract_service),
    client_repo: ClientRepository = Depends(get_client_repo),
    current_user: dict = Depends(require_operations_role)
):
    """
    Generate DIAN Mandato (IM) contract (Operations role or Admin required)

    This is a simplified Mandato for DIAN payments - no creditors required.

    The request must include:
    - client_nit: Client NIT for database lookup
    - numero_cotizacion_desembolso: Quote number
    - fecha_contrato_mandato: Mandate contract date (ISO format)
    - monto: Total amount

    Returns the created contract with ID format: PLDI-YYYY-XXX
    """
    import logging
    from decimal import Decimal
    logger = logging.getLogger(__name__)

    logger.info(f"DIAN Mandato generation request - NIT: {request.client_nit}, Quote: {request.numero_cotizacion_desembolso}, User: {current_user.get('email', current_user.get('id'))}")

    try:
        # Get user_id from authenticated user
        user_id = current_user['id']

        # Validate client exists
        client = await client_repo.get_by_nit(request.client_nit)
        if not client:
            logger.error(f"Client not found with NIT: {request.client_nit}")
            raise HTTPException(
                status_code=404,
                detail=f"Client with NIT {request.client_nit} not found"
            )

        # Build data snapshot combining client data + DIAN mandato data
        cupo = client.get('cupo_plataforma')

        data_snapshot = {
            # Client data (client is a dict from repository)
            "nit": client['nit'],
            "nombre_importador": client['nombre_importador'],
            "representante_legal": client['representante_legal'],
            "cedula_representante": client['cedula_representante'],
            "ciudad_domicilio": client['ciudad_domicilio'],
            "cupo_plataforma": float(cupo) if cupo is not None and isinstance(cupo, (Decimal, int, float, str)) else cupo,
            "direccion_comercial": client.get('direccion_comercial'),
            "tipo_identificacion_representante": client.get('tipo_identificacion_representante'),
            # DIAN Mandato specific data
            "numero_cotizacion_desembolso": request.numero_cotizacion_desembolso,
            "fecha_contrato_mandato": request.fecha_contrato_mandato,
            "monto": float(request.monto),
            # No acreedores for DIAN
        }

        logger.info("Prepared data snapshot for DIAN Mandato")

        # Create contract generation request
        contract_request = ContractGenerationRequest(
            client_nit=request.client_nit,
            contract_type=ContractType.PL_CO_DIAN_MANDATO_IM,
            custodian_data=None
        )

        # Generate contract with custom data snapshot
        contract = await service.generate_contract(
            request=contract_request,
            user_id=user_id,
            custom_data_snapshot=data_snapshot
        )

        contract_id = contract.get('contract_id', 'unknown')
        logger.info(f"Generated DIAN Mandato contract: {contract_id}")

        # Return response
        return ContractGenerationResponse(
            id=contract['id'],
            contract_id=contract['contract_id'],
            contract_type=contract['contract_type'],
            client_nit=contract['client_nit'],
            status=contract['status'],
            generated_at=contract['generated_at'],
            pdf_url=contract.get('pdf_url'),
            approved_document_url=contract.get('approved_document_url'),
            data_snapshot=contract['data_snapshot']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating DIAN Mandato: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating contract: {str(e)}")
