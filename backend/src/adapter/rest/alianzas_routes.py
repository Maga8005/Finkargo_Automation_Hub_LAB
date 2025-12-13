"""
Alianzas (Partnerships) API Routes.

Provides endpoints for broker management, commission tracking, and payments.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Path
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import date
import logging

from src.adapter.rest.rbac_dependencies import require_roles
from src.config.supabase_config import get_supabase_client
from src.repositorio.broker_repository import BrokerRepository
from src.repositorio.comision_repository import ComisionRepository
from src.repositorio.pago_repository import PagoRepository
from src.core.servicios.broker_service import BrokerService
from src.core.servicios.comision_service import ComisionService
from src.core.servicios.comision_excel_service import ComisionExcelService, get_comision_excel_service
from src.core.servicios.contract_extractor_service import ContractExtractorService
from src.core.servicios.landingai_contract_parser_service import LandingAIContractParserService
from src.core.servicios.banxico_service import BanxicoService
from src.interface.alianzas_dtos import (
    BrokerCreate,
    BrokerUpdate,
    BrokerResponse,
    BrokerSearchRequest,
    BrokerWithSubBrokers,
    BrokerContractData,
    TipoBroker,
    EstadoBroker,
    TipoCambioResponse,
    # Commission DTOs
    ComisionInput,
    ComisionCalculada,
    ComisionBatchInput,
    ComisionBatchResponse,
    ComisionListResponse,
    ComisionResumenBroker,
    ComisionEstadoUpdate,
    ComisionAprobacionRequest,
    ComisionAprobacionResponse,
    TipoComision,
    # Payment DTOs
    PagoResponse,
    PagoListResponse,
    PagoEstadoUpdate,
    EstadoPago,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/alianzas",
    tags=["Alianzas - Partnerships"]
)

# RBAC dependency - allows alianzas role and admin (admin bypass is default)
require_alianzas_role = require_roles(['alianzas'])


# ==================== Dependency Injection ====================

def get_broker_repository() -> BrokerRepository:
    """Get broker repository instance"""
    supabase = get_supabase_client()
    return BrokerRepository(supabase.admin_client)


def get_broker_service(
    repo: BrokerRepository = Depends(get_broker_repository)
) -> BrokerService:
    """Get broker service instance"""
    return BrokerService(repo)


def get_contract_extractor_service() -> ContractExtractorService:
    """Get contract extractor service instance"""
    return ContractExtractorService()


def get_landingai_contract_parser() -> LandingAIContractParserService:
    """Get LandingAI contract parser service instance"""
    return LandingAIContractParserService()


def get_banxico_service() -> BanxicoService:
    """Get Banxico service instance for exchange rate lookups"""
    return BanxicoService()


def get_comision_repository() -> ComisionRepository:
    """Get commission repository instance"""
    supabase = get_supabase_client()
    return ComisionRepository(supabase.admin_client)


def get_pago_repository() -> PagoRepository:
    """Get payment repository instance"""
    supabase = get_supabase_client()
    return PagoRepository(supabase.admin_client)


def get_comision_service(
    broker_repo: BrokerRepository = Depends(get_broker_repository),
    comision_repo: ComisionRepository = Depends(get_comision_repository),
    banxico_service: BanxicoService = Depends(get_banxico_service),
    pago_repo: PagoRepository = Depends(get_pago_repository)
) -> ComisionService:
    """Get commission service instance with all dependencies"""
    return ComisionService(broker_repo, comision_repo, banxico_service, pago_repo)


# ==================== Health Check ====================

@router.get(
    "/health",
    summary="Health check for Alianzas module",
    description="Returns health status of the Alianzas API module."
)
async def health_check(
    current_user: dict = Depends(require_alianzas_role)
):
    """
    Health check endpoint for the Alianzas module.

    Args:
        current_user: Authenticated user with alianzas role

    Returns:
        Health status and module information
    """
    logger.info(f"Alianzas health check by user {current_user.get('id')}")

    return {
        "status": "healthy",
        "module": "alianzas"
    }


# ==================== Broker CRUD Endpoints ====================

@router.post(
    "/brokers",
    response_model=BrokerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new broker",
    description="Create a new broker partner with commission rates and contract information."
)
async def create_broker(
    data: BrokerCreate,
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    Create a new broker.

    Args:
        data: BrokerCreate DTO with broker information
        current_user: Authenticated user with alianzas role
        service: BrokerService instance

    Returns:
        BrokerResponse: Created broker data
    """
    try:
        user_id = current_user.get('id')
        logger.info(f"Creating broker '{data.nombre}' by user {user_id}")

        broker = await service.create_broker(data, user_id)
        return broker

    except ValueError as e:
        logger.warning(f"Broker creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating broker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear broker"
        )


@router.get(
    "/brokers",
    response_model=List[BrokerResponse],
    summary="List all brokers",
    description="Get a list of all brokers with optional filters."
)
async def list_brokers(
    active_only: bool = Query(True, description="Only return active brokers"),
    tipo_broker: Optional[str] = Query(None, description="Filter by broker type"),
    estado: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    List all brokers with optional filters.

    Args:
        active_only: If True, only return active brokers
        tipo_broker: Optional filter by broker type
        estado: Optional filter by status
        current_user: Authenticated user with alianzas role
        service: BrokerService instance

    Returns:
        List[BrokerResponse]: List of brokers
    """
    try:
        brokers = await service.list_brokers(
            active_only=active_only,
            tipo_broker=tipo_broker,
            estado=estado
        )
        return brokers

    except Exception as e:
        logger.error(f"Error listing brokers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener lista de brokers"
        )


@router.get(
    "/brokers/search",
    response_model=List[BrokerResponse],
    summary="Search brokers",
    description="Search brokers by name, type, status, or RFC."
)
async def search_brokers(
    nombre: Optional[str] = Query(None, description="Search by name (partial match)"),
    tipo_broker: Optional[TipoBroker] = Query(None, description="Filter by broker type"),
    estado: Optional[EstadoBroker] = Query(None, description="Filter by status"),
    rfc: Optional[str] = Query(None, description="Search by RFC (partial match)"),
    active_only: bool = Query(True, description="Only return active brokers"),
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    Search brokers by various criteria.

    Args:
        nombre: Search by name (partial match, case-insensitive)
        tipo_broker: Filter by broker type
        estado: Filter by status
        rfc: Search by RFC (partial match)
        active_only: Only return active brokers
        current_user: Authenticated user with alianzas role
        service: BrokerService instance

    Returns:
        List[BrokerResponse]: Matching brokers
    """
    try:
        params = BrokerSearchRequest(
            nombre=nombre,
            tipo_broker=tipo_broker,
            estado=estado,
            rfc=rfc,
            active_only=active_only
        )
        brokers = await service.search_brokers(params)
        return brokers

    except Exception as e:
        logger.error(f"Error searching brokers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al buscar brokers"
        )


@router.get(
    "/brokers/master-brokers",
    response_model=List[dict],
    summary="Get master brokers for dropdown",
    description="Get all master brokers for form dropdown selection."
)
async def get_master_brokers(
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    Get all master brokers for dropdown selection.

    Args:
        current_user: Authenticated user with alianzas role
        service: BrokerService instance

    Returns:
        List[dict]: List of master broker records with id and nombre
    """
    try:
        master_brokers = await service.get_master_brokers()
        return master_brokers

    except Exception as e:
        logger.error(f"Error getting master brokers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener master brokers"
        )


@router.get(
    "/brokers/{broker_id}",
    response_model=BrokerResponse,
    summary="Get broker by ID",
    description="Get a specific broker by its UUID."
)
async def get_broker(
    broker_id: str,
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    Get a broker by ID.

    Args:
        broker_id: UUID of the broker
        current_user: Authenticated user with alianzas role
        service: BrokerService instance

    Returns:
        BrokerResponse: Broker data
    """
    try:
        broker = await service.get_broker(broker_id)
        return broker

    except ValueError as e:
        logger.warning(f"Broker not found: {broker_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting broker {broker_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener broker"
        )


@router.get(
    "/brokers/{broker_id}/sub-brokers",
    response_model=BrokerWithSubBrokers,
    summary="Get broker with sub-brokers",
    description="Get a broker with its sub-brokers list."
)
async def get_broker_with_sub_brokers(
    broker_id: str,
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    Get a broker with its sub-brokers.

    Args:
        broker_id: UUID of the broker
        current_user: Authenticated user with alianzas role
        service: BrokerService instance

    Returns:
        BrokerWithSubBrokers: Broker with sub-brokers list
    """
    try:
        broker = await service.get_broker_with_sub_brokers(broker_id)
        return broker

    except ValueError as e:
        logger.warning(f"Broker not found: {broker_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting broker with sub-brokers {broker_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener broker con sub-brokers"
        )


@router.put(
    "/brokers/{broker_id}",
    response_model=BrokerResponse,
    summary="Update a broker",
    description="Update an existing broker's information."
)
async def update_broker(
    broker_id: str,
    data: BrokerUpdate,
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    Update a broker.

    Args:
        broker_id: UUID of the broker to update
        data: BrokerUpdate DTO with fields to update
        current_user: Authenticated user with alianzas role
        service: BrokerService instance

    Returns:
        BrokerResponse: Updated broker data
    """
    try:
        logger.info(f"Updating broker {broker_id} by user {current_user.get('id')}")

        broker = await service.update_broker(broker_id, data)
        return broker

    except ValueError as e:
        logger.warning(f"Broker update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating broker {broker_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar broker"
        )


@router.delete(
    "/brokers/{broker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a broker",
    description="Soft delete a broker by setting its status to inactive."
)
async def delete_broker(
    broker_id: str,
    current_user: dict = Depends(require_alianzas_role),
    service: BrokerService = Depends(get_broker_service)
):
    """
    Soft delete a broker (set estado to inactivo).

    Args:
        broker_id: UUID of the broker to delete
        current_user: Authenticated user with alianzas role
        service: BrokerService instance
    """
    try:
        logger.info(f"Deleting broker {broker_id} by user {current_user.get('id')}")

        await service.delete_broker(broker_id)
        return None

    except ValueError as e:
        logger.warning(f"Broker delete failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting broker {broker_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar broker"
        )


# ==================== Contract Extraction Endpoints ====================

# Maximum file size: 10MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}


@router.post(
    "/brokers/extract-contract",
    response_model=BrokerContractData,
    summary="Extract data from broker contract",
    description="Upload a broker contract (PDF or DOCX) and extract commercial terms using regex patterns."
)
async def extract_contract_data(
    file: UploadFile = File(..., description="Contract file (PDF or DOCX)"),
    current_user: dict = Depends(require_alianzas_role),
    extractor: ContractExtractorService = Depends(get_contract_extractor_service)
):
    """
    Extract broker contract data from an uploaded file.

    Supports:
    - DOCX files: Text extracted using python-docx
    - PDF files: Text extracted using PyMuPDF (requires selectable text)

    Args:
        file: Uploaded contract file (PDF or DOCX)
        current_user: Authenticated user with alianzas role
        extractor: ContractExtractorService instance

    Returns:
        BrokerContractData: Extracted contract data with confidence score
    """
    try:
        logger.info(f"Contract extraction requested by user {current_user.get('id')}")

        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archivo sin nombre"
            )

        file_ext = '.' + file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de archivo no soportado: {file_ext}. Use PDF o DOCX."
            )

        # Read file content
        file_bytes = await file.read()

        # Validate file size
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo muy grande. Máximo: 10MB. Tamaño: {len(file_bytes) / (1024*1024):.2f}MB"
            )

        # Validate file is not empty
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archivo vacío"
            )

        logger.info(f"Processing file: {file.filename} ({len(file_bytes)} bytes)")

        # Extract based on file type
        if file_ext == '.docx':
            result = extractor.extract_from_docx(file_bytes)
        else:  # .pdf
            result = extractor.extract_from_pdf(file_bytes)

        logger.info(f"Extraction complete. Confidence: {result.extraction_confidence:.2f}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting contract data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el contrato: {str(e)}"
        )


@router.post(
    "/brokers/extract-contract-ai",
    response_model=BrokerContractData,
    summary="Extract data from broker contract using AI",
    description=(
        "Upload a scanned/image-based PDF contract and extract commercial terms "
        "using LandingAI's Agentic Document Extraction. "
        "This method is slower (30-60 seconds) but works with scanned documents."
    )
)
async def extract_contract_ai(
    contract_file: UploadFile = File(..., description="Contrato PDF del broker (escaneado)"),
    current_user: dict = Depends(require_alianzas_role),
    parser: LandingAIContractParserService = Depends(get_landingai_contract_parser)
):
    """
    Extract broker contract data from an uploaded PDF using AI.

    This endpoint uses LandingAI's ADE API for AI-powered extraction,
    suitable for scanned PDFs where standard text extraction fails.

    Args:
        contract_file: Uploaded contract PDF file
        current_user: Authenticated user with alianzas role
        parser: LandingAIContractParserService instance

    Returns:
        BrokerContractData: Extracted contract data with confidence score
    """
    try:
        logger.info(
            f"AI contract extraction requested by user {current_user.get('id')}"
        )

        # Validate file type (PDF only for AI extraction)
        if not contract_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archivo sin nombre"
            )

        file_ext = (
            '.' + contract_file.filename.lower().split('.')[-1]
            if '.' in contract_file.filename
            else ''
        )
        if file_ext != '.pdf':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Tipo de archivo no soportado: {file_ext}. "
                    "La extracción IA solo soporta archivos PDF."
                )
            )

        # Read file content
        file_bytes = await contract_file.read()

        # Validate file size (max 10MB)
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Archivo muy grande. Máximo: 10MB. "
                    f"Tamaño: {len(file_bytes) / (1024 * 1024):.2f}MB"
                )
            )

        # Validate file is not empty
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archivo vacío"
            )

        logger.info(
            f"Processing file with AI: {contract_file.filename} ({len(file_bytes)} bytes)"
        )

        # Extract using LandingAI
        result = parser.parse_contract_pdf(file_bytes)

        logger.info(
            f"AI extraction complete. Confidence: {result.extraction_confidence:.2f}"
        )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        # ValueError from the service contains user-friendly messages
        logger.warning(f"AI contract extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in AI contract extraction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en extracción IA del contrato: {str(e)}"
        )


# ==================== Exchange Rate Endpoints ====================

@router.get(
    "/tipo-cambio",
    response_model=TipoCambioResponse,
    summary="Get current USD/MXN exchange rate",
    description=(
        "Fetch the current official USD/MXN FIX exchange rate from Banco de México. "
        "Falls back to previous business days if today's rate is not yet published "
        "(weekends, holidays, or before daily publication time)."
    )
)
async def get_tipo_cambio_actual(
    current_user: dict = Depends(require_alianzas_role),
    service: BanxicoService = Depends(get_banxico_service)
):
    """
    Get the current USD/MXN FIX exchange rate.

    The rate is fetched from Banco de México's SIE API. If today's rate
    is not available (weekends, holidays, or before ~12:00 PM Mexico City time),
    it falls back to the most recent available rate.

    Args:
        current_user: Authenticated user with alianzas role
        service: BanxicoService instance

    Returns:
        TipoCambioResponse: Exchange rate with date and source
    """
    try:
        logger.info(f"Exchange rate requested by user {current_user.get('id')}")

        rate, rate_date = await service.get_tipo_cambio_actual()

        return TipoCambioResponse(
            tipo_cambio=float(rate),
            fecha=rate_date.isoformat(),
            fuente="Banco de México (Banxico)"
        )

    except ValueError as e:
        logger.warning(f"No exchange rate available: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Error fetching exchange rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching exchange rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener tipo de cambio"
        )


@router.get(
    "/tipo-cambio/{fecha}",
    response_model=TipoCambioResponse,
    summary="Get USD/MXN exchange rate for specific date",
    description=(
        "Fetch the official USD/MXN FIX exchange rate from Banco de México "
        "for a specific date. Note that rates are not published on weekends "
        "or Mexican holidays."
    )
)
async def get_tipo_cambio_fecha(
    fecha: date = Path(
        ...,
        description="Date to get exchange rate for (YYYY-MM-DD format)",
        example="2025-01-10"
    ),
    current_user: dict = Depends(require_alianzas_role),
    service: BanxicoService = Depends(get_banxico_service)
):
    """
    Get USD/MXN FIX exchange rate for a specific date.

    Args:
        fecha: Date to get exchange rate for (ISO format YYYY-MM-DD)
        current_user: Authenticated user with alianzas role
        service: BanxicoService instance

    Returns:
        TipoCambioResponse: Exchange rate with date and source
    """
    try:
        logger.info(
            f"Exchange rate for {fecha} requested by user {current_user.get('id')}"
        )

        rate = await service.get_tipo_cambio(fecha)

        return TipoCambioResponse(
            tipo_cambio=float(rate),
            fecha=fecha.isoformat(),
            fuente="Banco de México (Banxico)"
        )

    except ValueError as e:
        logger.warning(f"No exchange rate available for {fecha}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Error fetching exchange rate for {fecha}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching exchange rate for {fecha}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener tipo de cambio"
        )


# ==================== Commission Calculation Endpoints ====================

@router.post(
    "/comisiones/calcular",
    response_model=ComisionCalculada,
    summary="Calculate a single commission (preview)",
    description=(
        "Calculate a broker commission without saving to database. "
        "Use this for previewing calculations before batch processing."
    )
)
async def calcular_comision_preview(
    data: ComisionInput,
    current_user: dict = Depends(require_alianzas_role),
    service: ComisionService = Depends(get_comision_service)
):
    """
    Calculate a single commission for preview (not saved to database).

    Args:
        data: ComisionInput with calculation parameters
        current_user: Authenticated user with alianzas role
        service: ComisionService instance

    Returns:
        ComisionCalculada: Calculated commission details
    """
    try:
        logger.info(
            f"Commission preview requested by user {current_user.get('id')} "
            f"for broker {data.broker_id}"
        )

        comision = await service.calcular_comision(data)
        return comision

    except ValueError as e:
        logger.warning(f"Commission calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Runtime error in commission calculation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in commission calculation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al calcular comisión"
        )


@router.post(
    "/comisiones/calcular-lote",
    response_model=ComisionBatchResponse,
    summary="Calculate commissions in batch",
    description=(
        "Calculate multiple broker commissions in a single request. "
        "Optionally save all calculated commissions to the database by "
        "setting guardar=true."
    )
)
async def calcular_comisiones_lote(
    data: ComisionBatchInput,
    current_user: dict = Depends(require_alianzas_role),
    service: ComisionService = Depends(get_comision_service)
):
    """
    Calculate commissions in batch with optional save.

    Args:
        data: ComisionBatchInput with list of inputs and save flag
        current_user: Authenticated user with alianzas role
        service: ComisionService instance

    Returns:
        ComisionBatchResponse: List of calculated commissions with totals
    """
    try:
        user_id = current_user.get('id')
        logger.info(
            f"Batch commission calculation requested by user {user_id} "
            f"({len(data.comisiones)} items, guardar={data.guardar})"
        )

        response = await service.calcular_lote(data, user_id if data.guardar else None)

        logger.info(
            f"Batch calculation complete: {len(response.comisiones)} commissions, "
            f"total: ${response.total_usd} USD / ${response.total_mxn} MXN"
        )

        return response

    except ValueError as e:
        logger.warning(f"Batch commission calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Runtime error in batch commission calculation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in batch commission calculation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al calcular comisiones"
        )


@router.get(
    "/comisiones/{periodo_anio}/{periodo_mes}",
    response_model=ComisionListResponse,
    summary="List commissions by period",
    description="Get all commissions for a specific month and year."
)
async def listar_comisiones_por_periodo(
    periodo_anio: int = Path(..., ge=2020, description="Period year"),
    periodo_mes: int = Path(..., ge=1, le=12, description="Period month (1-12)"),
    tipo_comision: Optional[TipoComision] = Query(
        None, description="Filter by commission type"
    ),
    current_user: dict = Depends(require_alianzas_role),
    service: ComisionService = Depends(get_comision_service)
):
    """
    List all commissions for a specific period.

    Args:
        periodo_anio: Period year (e.g., 2025)
        periodo_mes: Period month (1-12)
        tipo_comision: Optional filter by commission type
        current_user: Authenticated user with alianzas role
        service: ComisionService instance

    Returns:
        ComisionListResponse: List of commissions with total count
    """
    try:
        logger.info(
            f"Listing commissions for {periodo_mes}/{periodo_anio} "
            f"by user {current_user.get('id')}"
        )

        response = await service.listar_por_periodo(periodo_mes, periodo_anio, tipo_comision)
        return response

    except Exception as e:
        logger.error(f"Error listing commissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener lista de comisiones"
        )


@router.get(
    "/comisiones/resumen/{periodo_anio}/{periodo_mes}",
    response_model=List[ComisionResumenBroker],
    summary="Get commission summary by broker",
    description="Get commission totals aggregated by broker for a specific period."
)
async def obtener_resumen_comisiones(
    periodo_anio: int = Path(..., ge=2020, description="Period year"),
    periodo_mes: int = Path(..., ge=1, le=12, description="Period month (1-12)"),
    current_user: dict = Depends(require_alianzas_role),
    service: ComisionService = Depends(get_comision_service)
):
    """
    Get commission summary aggregated by broker for a period.

    Args:
        periodo_anio: Period year (e.g., 2025)
        periodo_mes: Period month (1-12)
        current_user: Authenticated user with alianzas role
        service: ComisionService instance

    Returns:
        List[ComisionResumenBroker]: List of broker summaries with totals
    """
    try:
        logger.info(
            f"Getting commission summary for {periodo_mes}/{periodo_anio} "
            f"by user {current_user.get('id')}"
        )

        summaries = await service.obtener_resumen_por_broker(periodo_mes, periodo_anio)
        return summaries

    except Exception as e:
        logger.error(f"Error getting commission summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener resumen de comisiones"
        )


@router.get(
    "/comisiones/broker/{broker_id}",
    response_model=List[ComisionCalculada],
    summary="List commissions by broker",
    description="Get all commissions for a specific broker, optionally filtered by period."
)
async def listar_comisiones_por_broker(
    broker_id: str = Path(..., description="Broker UUID"),
    periodo_mes: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    periodo_anio: Optional[int] = Query(None, ge=2020, description="Filter by year"),
    current_user: dict = Depends(require_alianzas_role),
    service: ComisionService = Depends(get_comision_service)
):
    """
    List commissions for a specific broker.

    Args:
        broker_id: Broker UUID
        periodo_mes: Optional period month filter
        periodo_anio: Optional period year filter
        current_user: Authenticated user with alianzas role
        service: ComisionService instance

    Returns:
        List[ComisionCalculada]: List of broker's commissions
    """
    try:
        logger.info(
            f"Listing commissions for broker {broker_id} "
            f"by user {current_user.get('id')}"
        )

        comisiones = await service.listar_por_broker(broker_id, periodo_mes, periodo_anio)
        return comisiones

    except Exception as e:
        logger.error(f"Error listing broker commissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener comisiones del broker"
        )


@router.patch(
    "/comisiones/{comision_id}/estado",
    response_model=ComisionCalculada,
    summary="Update commission status",
    description="Update the status of a commission (calculado → aprobado → pagado)."
)
async def actualizar_estado_comision(
    comision_id: str = Path(..., description="Commission UUID"),
    data: ComisionEstadoUpdate = ...,
    current_user: dict = Depends(require_alianzas_role),
    service: ComisionService = Depends(get_comision_service)
):
    """
    Update commission status.

    Args:
        comision_id: Commission UUID
        data: ComisionEstadoUpdate with new status
        current_user: Authenticated user with alianzas role
        service: ComisionService instance

    Returns:
        ComisionCalculada: Updated commission
    """
    try:
        logger.info(
            f"Updating commission {comision_id} to estado {data.estado.value} "
            f"by user {current_user.get('id')}"
        )

        comision = await service.actualizar_estado(comision_id, data.estado)
        return comision

    except ValueError as e:
        logger.warning(f"Commission status update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating commission status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar estado de comisión"
        )


# ==================== Excel Export Endpoints ====================

@router.get(
    "/comisiones/export/{periodo_anio}/{periodo_mes}",
    summary="Export commissions to Excel",
    description=(
        "Generate an Excel file with commissions for a specific period. "
        "The file includes detail, summary by broker, and metadata sheets."
    )
)
async def exportar_comisiones_excel(
    periodo_anio: int = Path(..., ge=2020, description="Period year"),
    periodo_mes: int = Path(..., ge=1, le=12, description="Period month (1-12)"),
    current_user: dict = Depends(require_alianzas_role),
    comision_repo: ComisionRepository = Depends(get_comision_repository),
    excel_service: ComisionExcelService = Depends(get_comision_excel_service)
):
    """
    Export commissions for a period to Excel file.

    Args:
        periodo_anio: Period year (e.g., 2025)
        periodo_mes: Period month (1-12)
        current_user: Authenticated user with alianzas role
        comision_repo: ComisionRepository instance
        excel_service: ComisionExcelService instance

    Returns:
        StreamingResponse: Excel file download
    """
    try:
        logger.info(
            f"Exporting commissions for {periodo_mes}/{periodo_anio} "
            f"by user {current_user.get('id')}"
        )

        # Get commissions and summary data
        comisiones = await comision_repo.get_by_periodo(periodo_mes, periodo_anio)

        if not comisiones:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No hay comisiones para el período {periodo_mes}/{periodo_anio}"
            )

        # Get summary by broker
        resumen = await comision_repo.get_resumen_por_broker(periodo_mes, periodo_anio)

        # Get exchange rate from first commission
        tipo_cambio = float(comisiones[0].get('tipo_cambio', 0))

        # Generate Excel file
        excel_buffer = excel_service.generate_comisiones_excel(
            comisiones=comisiones,
            resumen=resumen,
            periodo_mes=periodo_mes,
            periodo_anio=periodo_anio,
            tipo_cambio=tipo_cambio
        )

        # Generate filename
        filename = f"comisiones_brokers_{periodo_anio}_{periodo_mes:02d}.xlsx"

        logger.info(f"Generated Excel file: {filename}")

        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting commissions to Excel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al exportar comisiones a Excel"
        )


# ==================== Commission Approval Endpoints ====================

@router.post(
    "/comisiones/aprobar",
    response_model=ComisionAprobacionResponse,
    summary="Approve commissions for payment",
    description=(
        "Approve all calculated commissions for a period and create payment records. "
        "This transitions commissions from 'calculado' to 'aprobado' status and "
        "creates aggregated payment records per broker."
    )
)
async def aprobar_comisiones(
    data: ComisionAprobacionRequest,
    current_user: dict = Depends(require_alianzas_role),
    service: ComisionService = Depends(get_comision_service)
):
    """
    Approve commissions for a period and create payment records.

    Args:
        data: ComisionAprobacionRequest with period month and year
        current_user: Authenticated user with alianzas role
        service: ComisionService instance

    Returns:
        ComisionAprobacionResponse: Summary of approved commissions and payments
    """
    try:
        user_id = current_user.get('id')
        logger.info(
            f"Approving commissions for {data.periodo_mes}/{data.periodo_anio} "
            f"by user {user_id}"
        )

        response = await service.aprobar_comisiones_periodo(
            mes=data.periodo_mes,
            anio=data.periodo_anio,
            user_id=user_id
        )

        logger.info(
            f"Approved {response.comisiones_aprobadas} commissions, "
            f"created {response.pagos_creados} payments"
        )

        return response

    except ValueError as e:
        logger.warning(f"Commission approval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error approving commissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al aprobar comisiones"
        )


# ==================== Payment Endpoints ====================

@router.get(
    "/pagos",
    response_model=PagoListResponse,
    summary="List payment history",
    description="Get payment history with optional filters for broker and status."
)
async def listar_pagos(
    broker_id: Optional[str] = Query(None, description="Filter by broker UUID"),
    estado: Optional[EstadoPago] = Query(None, description="Filter by payment status"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(require_alianzas_role),
    pago_repo: PagoRepository = Depends(get_pago_repository)
):
    """
    List payment history with optional filters.

    Args:
        broker_id: Optional filter by broker UUID
        estado: Optional filter by payment status
        limit: Number of records to return (max 100)
        offset: Number of records to skip for pagination
        current_user: Authenticated user with alianzas role
        pago_repo: PagoRepository instance

    Returns:
        PagoListResponse: List of payments with pagination info
    """
    try:
        logger.info(f"Listing payments by user {current_user.get('id')}")

        estado_str = estado.value if estado else None
        pagos = await pago_repo.get_historial(
            broker_id=broker_id,
            estado=estado_str,
            limit=limit,
            offset=offset
        )
        total = await pago_repo.count_historial(broker_id=broker_id, estado=estado_str)

        # Convert to response format
        pagos_response = []
        for pago in pagos:
            broker_info = pago.get('brokers', {})
            broker_nombre = broker_info.get('nombre') if broker_info else None

            pagos_response.append(PagoResponse(
                id=pago['id'],
                broker_id=pago['broker_id'],
                broker_nombre=broker_nombre,
                periodo_mes=pago['periodo_mes'],
                periodo_anio=pago['periodo_anio'],
                total_usd=float(pago['total_usd']),
                total_mxn=float(pago['total_mxn']),
                tipo_cambio=float(pago['tipo_cambio']),
                fecha_programada=pago.get('fecha_programada'),
                fecha_pago=pago.get('fecha_pago'),
                estado=EstadoPago(pago['estado']),
                comprobante_url=pago.get('comprobante_url'),
                factura_broker_url=pago.get('factura_broker_url'),
                notas=pago.get('notas'),
                created_at=pago['created_at'],
                approved_by=pago.get('approved_by'),
            ))

        return PagoListResponse(
            pagos=pagos_response,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener historial de pagos"
        )


@router.get(
    "/pagos/{periodo_anio}/{periodo_mes}",
    response_model=List[PagoResponse],
    summary="List payments by period",
    description="Get all payments for a specific month and year."
)
async def listar_pagos_por_periodo(
    periodo_anio: int = Path(..., ge=2020, description="Period year"),
    periodo_mes: int = Path(..., ge=1, le=12, description="Period month (1-12)"),
    broker_id: Optional[str] = Query(None, description="Filter by broker UUID"),
    current_user: dict = Depends(require_alianzas_role),
    pago_repo: PagoRepository = Depends(get_pago_repository)
):
    """
    List all payments for a specific period.

    Args:
        periodo_anio: Period year (e.g., 2025)
        periodo_mes: Period month (1-12)
        broker_id: Optional filter by broker UUID
        current_user: Authenticated user with alianzas role
        pago_repo: PagoRepository instance

    Returns:
        List[PagoResponse]: List of payments for the period
    """
    try:
        logger.info(
            f"Listing payments for {periodo_mes}/{periodo_anio} "
            f"by user {current_user.get('id')}"
        )

        pagos = await pago_repo.get_by_periodo(
            mes=periodo_mes,
            anio=periodo_anio,
            broker_id=broker_id
        )

        # Convert to response format
        pagos_response = []
        for pago in pagos:
            broker_info = pago.get('brokers', {})
            broker_nombre = broker_info.get('nombre') if broker_info else None

            pagos_response.append(PagoResponse(
                id=pago['id'],
                broker_id=pago['broker_id'],
                broker_nombre=broker_nombre,
                periodo_mes=pago['periodo_mes'],
                periodo_anio=pago['periodo_anio'],
                total_usd=float(pago['total_usd']),
                total_mxn=float(pago['total_mxn']),
                tipo_cambio=float(pago['tipo_cambio']),
                fecha_programada=pago.get('fecha_programada'),
                fecha_pago=pago.get('fecha_pago'),
                estado=EstadoPago(pago['estado']),
                comprobante_url=pago.get('comprobante_url'),
                factura_broker_url=pago.get('factura_broker_url'),
                notas=pago.get('notas'),
                created_at=pago['created_at'],
                approved_by=pago.get('approved_by'),
            ))

        return pagos_response

    except Exception as e:
        logger.error(f"Error listing payments by period: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener pagos del período"
        )


@router.get(
    "/pagos/{pago_id}",
    response_model=PagoResponse,
    summary="Get payment by ID",
    description="Get a specific payment record by its UUID."
)
async def obtener_pago(
    pago_id: str = Path(..., description="Payment UUID"),
    current_user: dict = Depends(require_alianzas_role),
    pago_repo: PagoRepository = Depends(get_pago_repository)
):
    """
    Get a payment by ID.

    Args:
        pago_id: Payment UUID
        current_user: Authenticated user with alianzas role
        pago_repo: PagoRepository instance

    Returns:
        PagoResponse: Payment data
    """
    try:
        pago = await pago_repo.get_by_id(pago_id)

        if not pago:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pago con ID '{pago_id}' no encontrado"
            )

        broker_info = pago.get('brokers', {})
        broker_nombre = broker_info.get('nombre') if broker_info else None

        return PagoResponse(
            id=pago['id'],
            broker_id=pago['broker_id'],
            broker_nombre=broker_nombre,
            periodo_mes=pago['periodo_mes'],
            periodo_anio=pago['periodo_anio'],
            total_usd=float(pago['total_usd']),
            total_mxn=float(pago['total_mxn']),
            tipo_cambio=float(pago['tipo_cambio']),
            fecha_programada=pago.get('fecha_programada'),
            fecha_pago=pago.get('fecha_pago'),
            estado=EstadoPago(pago['estado']),
            comprobante_url=pago.get('comprobante_url'),
            factura_broker_url=pago.get('factura_broker_url'),
            notas=pago.get('notas'),
            created_at=pago['created_at'],
            approved_by=pago.get('approved_by'),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment {pago_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener pago"
        )


@router.patch(
    "/pagos/{pago_id}/estado",
    response_model=PagoResponse,
    summary="Update payment status",
    description=(
        "Update the status of a payment (pendiente → programado → pagado). "
        "When marking as 'pagado', fecha_pago is required."
    )
)
async def actualizar_estado_pago(
    pago_id: str = Path(..., description="Payment UUID"),
    data: PagoEstadoUpdate = ...,
    current_user: dict = Depends(require_alianzas_role),
    pago_repo: PagoRepository = Depends(get_pago_repository)
):
    """
    Update payment status.

    Args:
        pago_id: Payment UUID
        data: PagoEstadoUpdate with new status and optional payment date
        current_user: Authenticated user with alianzas role
        pago_repo: PagoRepository instance

    Returns:
        PagoResponse: Updated payment
    """
    try:
        logger.info(
            f"Updating payment {pago_id} to estado {data.estado.value} "
            f"by user {current_user.get('id')}"
        )

        # Validate fecha_pago for 'pagado' status
        if data.estado == EstadoPago.PAGADO and not data.fecha_pago:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_pago es requerida cuando estado es 'pagado'"
            )

        pago = await pago_repo.update_estado(
            pago_id=pago_id,
            estado=data.estado.value,
            fecha_pago=data.fecha_pago,
            comprobante_url=data.comprobante_url
        )

        if not pago:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pago con ID '{pago_id}' no encontrado"
            )

        broker_info = pago.get('brokers', {})
        broker_nombre = broker_info.get('nombre') if broker_info else None

        return PagoResponse(
            id=pago['id'],
            broker_id=pago['broker_id'],
            broker_nombre=broker_nombre,
            periodo_mes=pago['periodo_mes'],
            periodo_anio=pago['periodo_anio'],
            total_usd=float(pago['total_usd']),
            total_mxn=float(pago['total_mxn']),
            tipo_cambio=float(pago['tipo_cambio']),
            fecha_programada=pago.get('fecha_programada'),
            fecha_pago=pago.get('fecha_pago'),
            estado=EstadoPago(pago['estado']),
            comprobante_url=pago.get('comprobante_url'),
            factura_broker_url=pago.get('factura_broker_url'),
            notas=pago.get('notas'),
            created_at=pago['created_at'],
            approved_by=pago.get('approved_by'),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar estado de pago"
        )
