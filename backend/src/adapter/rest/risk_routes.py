"""
Risk Management Routes - API endpoints for fraud detection and risk assessment
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
import logging

from src.config.supabase_config import get_supabase_client
from src.adapter.rest.rbac_dependencies import require_roles
from src.repositorio.risk_repository import (
    RiskAssessmentRepository,
    FraudRulesRepository,
    BlacklistRepository,
    AlertRepository,
    DocumentExtractionRepository,
    CrossValidationRepository,
    ExternalContactRepository,
    EmailChainRepository,
)
from src.repositorio.client_repository import ClientRepository
from src.core.servicios.risk.fraud_detection_service import FraudDetectionService
from src.core.servicios.risk.risk_scoring_service import RiskScoringService
from src.core.servicios.risk.alert_service import AlertService
from src.core.servicios.risk.document_extraction_service import DocumentExtractionService
from src.core.servicios.risk.cross_validation_service import CrossValidationService
from src.core.servicios.risk.external_contact_service import ExternalContactService
from src.core.servicios.risk.email_chain_service import EmailChainService
from src.interface.risk_dtos import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskAssessmentDetail,
    RiskDecisionRequest,
    RiskStatsResponse,
    FraudDetectionRuleResponse,
    RuleUpdateRequest,
    BlacklistEntryRequest,
    BlacklistEntryResponse,
    RiskAlertResponse,
    AssessmentStatus,
    RiskLevel,
    EntityType,
    FraudIndicator,
    ClientInfo,
    DocumentType,
    ExtractionStatus,
    DocumentUploadResponse,
    DocumentExtractionResponse,
    DocumentExtractionListResponse,
    CrossValidationResult,
    CrossValidationResponse,
    TriggerExtractionResponse,
    DiscrepancySeverity,
    ValidationType,
    VerificationStatus,
    ExternalContactRequest,
    ExternalContactResponse,
    ExternalContactListResponse,
    ExternalContactValidationStatus,
    EmailValidationResult,
    EmailChainValidationStatus,
    EmailChainResponse,
    EmailChainListResponse,
    EmailChainParsedData,
    EmailChainValidationResult,
    EmailMessage,
    ExtractedMentions,
    EmailChainDiscrepancy,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/risk", tags=["Risk Management"])


# ==================== Dependency Factories ====================

def get_supabase():
    """Get Supabase client"""
    return get_supabase_client()


def get_risk_repo():
    """Get risk assessment repository"""
    supabase = get_supabase()
    return RiskAssessmentRepository(supabase.admin_client)


def get_rules_repo():
    """Get fraud rules repository"""
    supabase = get_supabase()
    return FraudRulesRepository(supabase.admin_client)


def get_blacklist_repo():
    """Get blacklist repository"""
    supabase = get_supabase()
    return BlacklistRepository(supabase.admin_client)


def get_alert_repo():
    """Get alert repository"""
    supabase = get_supabase()
    return AlertRepository(supabase.admin_client)


def get_client_repo():
    """Get client repository"""
    supabase = get_supabase()
    return ClientRepository(supabase.admin_client)


def get_alert_service():
    """Get alert service"""
    return AlertService(get_alert_repo())


def get_scoring_service():
    """Get risk scoring service"""
    return RiskScoringService(get_rules_repo())


def get_extraction_repo():
    """Get document extraction repository"""
    supabase = get_supabase()
    return DocumentExtractionRepository(supabase.admin_client)


def get_validation_repo():
    """Get cross-validation repository"""
    supabase = get_supabase()
    return CrossValidationRepository(supabase.admin_client)


def get_extraction_service():
    """Get document extraction service"""
    return DocumentExtractionService()


def get_cross_validation_service():
    """Get cross-validation service"""
    return CrossValidationService()


def get_fraud_service():
    """Get fraud detection service with all dependencies"""
    return FraudDetectionService(
        risk_repo=get_risk_repo(),
        rules_repo=get_rules_repo(),
        blacklist_repo=get_blacklist_repo(),
        client_repo=get_client_repo(),
        scoring_service=get_scoring_service(),
        alert_service=get_alert_service(),
    )


def get_external_contact_repo():
    """Get external contact repository"""
    supabase = get_supabase()
    return ExternalContactRepository(supabase.admin_client)


def get_external_contact_service():
    """Get external contact service"""
    return ExternalContactService(get_external_contact_repo())


def get_email_chain_repo():
    """Get email chain repository"""
    supabase = get_supabase()
    return EmailChainRepository(supabase.admin_client)


def get_email_chain_service():
    """Get email chain service"""
    return EmailChainService(
        chain_repo=get_email_chain_repo(),
        assessment_repo=get_risk_repo(),
        extraction_repo=get_extraction_repo(),
    )


# ==================== Dashboard Endpoints ====================

@router.get("/dashboard", response_model=RiskStatsResponse)
async def get_dashboard_stats(
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Get risk dashboard statistics.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Dashboard stats requested by user {current_user.get('id')}")

    repo = get_risk_repo()
    stats = await repo.get_stats()

    # Compute pass/fail counts by checking each assessment's cross-validation results
    validation_repo = get_validation_repo()
    all_assessments = await repo.search({'limit': 1000})  # Get all assessments

    pass_count = 0
    requires_verification_count = 0

    for assessment in all_assessments:
        results = await validation_repo.get_by_assessment(assessment['id'])
        has_discrepancy = any(r.get('is_discrepancy', False) for r in results)

        if has_discrepancy:
            requires_verification_count += 1
        else:
            pass_count += 1

    stats['pass_count'] = pass_count
    stats['requires_verification_count'] = requires_verification_count

    return RiskStatsResponse(**stats)


# ==================== Evaluation Endpoints ====================

@router.get("/evaluations", response_model=List[RiskAssessmentDetail])
async def list_evaluations(
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status (pass, requires_manual_verification)"),
    client_nit: Optional[str] = Query(None, description="Filter by client NIT"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    limit: int = Query(50, le=100, ge=1),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    List risk evaluations with optional filters.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Listing evaluations with filters: status={status}, risk_level={risk_level}, verification_status={verification_status}")

    filters = {
        'status': status,
        'risk_level': risk_level,
        'client_nit': client_nit,
        'limit': limit,
        'offset': offset,
    }

    if date_from:
        filters['date_from'] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
    if date_to:
        filters['date_to'] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

    repo = get_risk_repo()
    evaluations = await repo.search(filters)

    # Compute verification info for each evaluation
    results = []
    for eval_data in evaluations:
        verification_info = await _compute_verification_info_async(eval_data['id'])

        # Apply verification_status filter if specified
        if verification_status:
            if verification_info['verification_status'].value != verification_status:
                continue

        results.append(_map_to_detail(eval_data, verification_info))

    return results


@router.get("/evaluations/{id}", response_model=RiskAssessmentDetail)
async def get_evaluation(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Get detailed risk evaluation by ID.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Getting evaluation {id}")

    repo = get_risk_repo()
    evaluation = await repo.get_by_id(id)

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    # Compute verification info
    verification_info = await _compute_verification_info_async(id)

    return _map_to_detail(evaluation, verification_info)


@router.post("/evaluate", response_model=RiskAssessmentResponse)
async def create_evaluation(
    request: RiskAssessmentRequest,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Create a new risk evaluation for a client.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Creating evaluation for NIT: {request.client_nit}")

    user_id = current_user.get('id')

    try:
        fraud_service = get_fraud_service()
        assessment = await fraud_service.evaluate_client(
            client_nit=request.client_nit,
            user_id=user_id,
            # NOTE: assessment_type removed - all evaluations use comprehensive workflow
        )

        return _map_to_response(assessment)
    except Exception as e:
        logger.error(f"Error creating evaluation for NIT {request.client_nit}: {e}", exc_info=True)
        # Re-raise as HTTPException to ensure proper error response with CORS headers
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating evaluation: {str(e)}"
        )


@router.put("/evaluations/{id}/decision", response_model=RiskAssessmentDetail)
async def submit_decision(
    id: str,
    request: RiskDecisionRequest,
    current_user: dict = Depends(require_roles(['risk_manager']))
):
    """
    Submit a decision on a risk evaluation.
    Only risk_manager can make decisions.
    """
    logger.info(f"Submitting decision for evaluation {id}: {request.status.value}")

    user_id = current_user.get('id')

    repo = get_risk_repo()

    # Get current evaluation
    evaluation = await repo.get_by_id(id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    # Update evaluation with decision
    updates = {
        'status': request.status.value,
        'reviewed_by': user_id,
        'reviewed_at': datetime.utcnow().isoformat(),
    }

    if request.notes:
        updates['review_notes'] = request.notes

    updated = await repo.update(id, updates)

    # Create escalation alert if escalated
    if request.status == AssessmentStatus.ESCALATED:
        alert_service = get_alert_service()
        await alert_service.create_escalation_alert(
            assessment_id=id,
            client_nit=evaluation['client_nit'],
            escalated_by=user_id,
            notes=request.notes
        )

    # Compute verification info
    verification_info = await _compute_verification_info_async(id)

    return _map_to_detail(updated, verification_info)


# ==================== Rules Endpoints ====================

@router.get("/rules", response_model=List[FraudDetectionRuleResponse])
async def list_rules(
    current_user: dict = Depends(require_roles(['risk_manager']))
):
    """
    List all fraud detection rules.
    Only risk_manager can access.
    """
    logger.info("Listing fraud detection rules")

    repo = get_rules_repo()
    rules = await repo.list_all()

    return [_map_to_rule_response(rule) for rule in rules]


@router.put("/rules/{id}", response_model=FraudDetectionRuleResponse)
async def update_rule(
    id: str,
    request: RuleUpdateRequest,
    current_user: dict = Depends(require_roles(['risk_manager']))
):
    """
    Update a fraud detection rule.
    Only risk_manager can update rules.
    """
    logger.info(f"Updating rule {id}")

    repo = get_rules_repo()

    # Get current rule
    rule = await repo.get_by_id(id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {id} not found"
        )

    # Build updates
    updates = {}
    if request.weight is not None:
        updates['weight'] = float(request.weight)
    if request.threshold is not None:
        updates['threshold'] = float(request.threshold)
    if request.is_active is not None:
        updates['is_active'] = request.is_active
    if request.config is not None:
        updates['config'] = request.config

    updated = await repo.update(id, updates)

    return _map_to_rule_response(updated)


# ==================== Blacklist Endpoints ====================

@router.get("/blacklist", response_model=List[BlacklistEntryResponse])
async def list_blacklist(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(50, le=100, ge=1),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    List blacklist entries.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Listing blacklist: entity_type={entity_type}, is_active={is_active}")

    filters = {
        'entity_type': entity_type,
        'is_active': is_active,
        'limit': limit,
        'offset': offset,
    }

    repo = get_blacklist_repo()
    entries = await repo.search(filters)

    return [_map_to_blacklist_response(entry) for entry in entries]


@router.post("/blacklist", response_model=BlacklistEntryResponse)
async def add_to_blacklist(
    request: BlacklistEntryRequest,
    current_user: dict = Depends(require_roles(['risk_manager']))
):
    """
    Add entry to blacklist.
    Only risk_manager can add entries.
    """
    logger.info(f"Adding to blacklist: {request.entity_type.value} = {request.entity_value}")

    user_id = current_user.get('id')

    repo = get_blacklist_repo()

    # Check if already exists
    existing = await repo.is_blacklisted(request.entity_type.value, request.entity_value)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Entity already blacklisted: {request.entity_type.value} = {request.entity_value}"
        )

    entry_data = {
        'entity_type': request.entity_type.value,
        'entity_value': request.entity_value.lower(),
        'reason': request.reason,
        'added_by': user_id,
        'source': 'manual',
        'is_active': True,
    }

    entry = await repo.add(entry_data)

    return _map_to_blacklist_response(entry)


@router.delete("/blacklist/{id}")
async def remove_from_blacklist(
    id: str,
    current_user: dict = Depends(require_roles(['risk_manager']))
):
    """
    Remove entry from blacklist (soft delete).
    Only risk_manager can remove entries.
    """
    logger.info(f"Removing from blacklist: {id}")

    repo = get_blacklist_repo()
    success = await repo.remove(id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blacklist entry {id} not found"
        )

    return {"message": "Entry removed from blacklist"}


# ==================== Alert Endpoints ====================

@router.get("/alerts", response_model=List[RiskAlertResponse])
async def list_alerts(
    include_read: bool = Query(False, description="Include read alerts"),
    limit: int = Query(20, le=100, ge=1),
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    List risk alerts.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Listing alerts: include_read={include_read}")

    service = get_alert_service()
    alerts = await service.get_all_alerts(limit=limit, include_read=include_read)

    return [_map_to_alert_response(alert) for alert in alerts]


@router.put("/alerts/{id}/read")
async def mark_alert_read(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Mark alert as read.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Marking alert {id} as read")

    user_id = current_user.get('id')

    service = get_alert_service()
    success = await service.mark_alert_read(id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {id} not found"
        )

    return {"message": "Alert marked as read"}


# ==================== Helper Functions ====================

def _compute_verification_info(assessment_id: str) -> dict:
    """
    Compute verification status from cross-validation results.
    This is called synchronously as helper for mapping functions.

    Args:
        assessment_id: The assessment ID to look up

    Returns:
        Dict with verification_status, has_discrepancies, discrepancy_count
    """
    import asyncio

    async def _get_verification_info():
        validation_repo = get_validation_repo()
        results = await validation_repo.get_by_assessment(assessment_id)

        discrepancy_count = sum(1 for r in results if r.get('is_discrepancy', False))
        has_discrepancies = discrepancy_count > 0
        verification_status = (
            VerificationStatus.REQUIRES_MANUAL_VERIFICATION
            if has_discrepancies
            else VerificationStatus.PASS
        )

        return {
            'verification_status': verification_status,
            'has_discrepancies': has_discrepancies,
            'discrepancy_count': discrepancy_count,
        }

    # Try to run in existing event loop, or create new one
    try:
        asyncio.get_running_loop()
        # If there's a running loop, we can't use run_until_complete
        # Return default values for now - the async endpoint will handle this
        return {
            'verification_status': VerificationStatus.PASS,
            'has_discrepancies': False,
            'discrepancy_count': 0,
        }
    except RuntimeError:
        # No running loop, safe to create one
        return asyncio.run(_get_verification_info())


async def _compute_verification_info_async(assessment_id: str) -> dict:
    """
    Compute verification status from cross-validation results asynchronously.

    Args:
        assessment_id: The assessment ID to look up

    Returns:
        Dict with verification_status, has_discrepancies, discrepancy_count
    """
    validation_repo = get_validation_repo()
    results = await validation_repo.get_by_assessment(assessment_id)

    discrepancy_count = sum(1 for r in results if r.get('is_discrepancy', False))
    has_discrepancies = discrepancy_count > 0
    verification_status = (
        VerificationStatus.REQUIRES_MANUAL_VERIFICATION
        if has_discrepancies
        else VerificationStatus.PASS
    )

    return {
        'verification_status': verification_status,
        'has_discrepancies': has_discrepancies,
        'discrepancy_count': discrepancy_count,
    }


def _map_to_response(data: dict, verification_info: dict = None) -> RiskAssessmentResponse:
    """Map database record to response model"""
    indicators = data.get('fraud_indicators', [])
    if isinstance(indicators, list):
        indicators = [_map_indicator(ind) for ind in indicators]

    # Use provided verification info or defaults
    if verification_info is None:
        verification_info = {
            'verification_status': VerificationStatus.PASS,
            'has_discrepancies': False,
            'discrepancy_count': 0,
        }

    return RiskAssessmentResponse(
        id=data['id'],
        assessment_id=data.get('assessment_id', ''),
        client_nit=data['client_nit'],
        risk_level=RiskLevel(data['risk_level']),
        risk_score=data['risk_score'],
        fraud_indicators=indicators,
        status=AssessmentStatus(data['status']),
        assessment_type=data.get('assessment_type', 'comprehensive'),
        created_at=_parse_datetime(data.get('created_at')),
        verification_status=verification_info['verification_status'],
        has_discrepancies=verification_info['has_discrepancies'],
        discrepancy_count=verification_info['discrepancy_count'],
    )


def _map_to_detail(data: dict, verification_info: dict = None) -> RiskAssessmentDetail:
    """Map database record to detail model"""
    indicators = data.get('fraud_indicators', [])
    if isinstance(indicators, list):
        indicators = [_map_indicator(ind) for ind in indicators]

    # Extract client info from snapshot (handle None case)
    snapshot = data.get('client_data_snapshot') or {}
    client_info = None
    if snapshot:
        client_info = ClientInfo(
            nit=snapshot.get('nit', data['client_nit']),
            nombre_importador=snapshot.get('nombre_importador'),
            representante_legal=snapshot.get('representante_legal'),
            ciudad_domicilio=snapshot.get('ciudad_domicilio'),
            cupo_plataforma=snapshot.get('cupo_plataforma'),
        )

    # Use provided verification info or defaults
    if verification_info is None:
        verification_info = {
            'verification_status': VerificationStatus.PASS,
            'has_discrepancies': False,
            'discrepancy_count': 0,
        }

    return RiskAssessmentDetail(
        id=data['id'],
        assessment_id=data.get('assessment_id', ''),
        client_nit=data['client_nit'],
        risk_level=RiskLevel(data['risk_level']),
        risk_score=data['risk_score'],
        fraud_indicators=indicators,
        status=AssessmentStatus(data['status']),
        assessment_type=data.get('assessment_type', 'comprehensive'),
        created_at=_parse_datetime(data.get('created_at')),
        assessed_by=data.get('assessed_by'),
        assessed_at=_parse_datetime(data.get('assessed_at')),
        reviewed_by=data.get('reviewed_by'),
        reviewed_at=_parse_datetime(data.get('reviewed_at')),
        review_notes=data.get('review_notes'),
        client_info=client_info,
        client_data_snapshot=snapshot,
        updated_at=_parse_datetime(data.get('updated_at')),
        verification_status=verification_info['verification_status'],
        has_discrepancies=verification_info['has_discrepancies'],
        discrepancy_count=verification_info['discrepancy_count'],
    )


def _map_indicator(data: dict) -> FraudIndicator:
    """Map indicator dict to model"""
    severity = data.get('severity', 'low')
    if isinstance(severity, str):
        severity = RiskLevel(severity)

    return FraudIndicator(
        indicator_name=data.get('indicator_name', ''),
        indicator_value=data.get('indicator_value', False),
        severity=severity,
        evidence=data.get('evidence'),
        score_impact=data.get('score_impact', 0),
    )


def _map_to_rule_response(data: dict) -> FraudDetectionRuleResponse:
    """Map rule data to response model"""
    return FraudDetectionRuleResponse(
        id=data['id'],
        rule_name=data['rule_name'],
        rule_type=data['rule_type'],
        description=data.get('description'),
        weight=data['weight'],
        threshold=data['threshold'],
        is_active=data['is_active'],
        config=data.get('config'),
        created_at=_parse_datetime(data.get('created_at')),
        updated_at=_parse_datetime(data.get('updated_at')),
    )


def _map_to_blacklist_response(data: dict) -> BlacklistEntryResponse:
    """Map blacklist data to response model"""
    return BlacklistEntryResponse(
        id=data['id'],
        entity_type=EntityType(data['entity_type']),
        entity_value=data['entity_value'],
        reason=data['reason'],
        source=data.get('source', 'manual'),
        added_by=data.get('added_by'),
        added_at=_parse_datetime(data.get('added_at')),
        expires_at=_parse_datetime(data.get('expires_at')),
        is_active=data['is_active'],
    )


def _map_to_alert_response(data: dict) -> RiskAlertResponse:
    """Map alert data to response model"""
    return RiskAlertResponse(
        id=data['id'],
        assessment_id=data.get('assessment_id'),
        alert_type=data['alert_type'],
        severity=data['severity'],
        title=data['title'],
        message=data['message'],
        is_read=data['is_read'],
        read_by=data.get('read_by'),
        read_at=_parse_datetime(data.get('read_at')),
        created_at=_parse_datetime(data.get('created_at')),
    )


def _parse_datetime(value) -> datetime:
    """Parse datetime from various formats"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    return None


# ==================== Document Extraction Endpoints ====================

@router.post("/evaluations/{id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Upload a document for AI extraction.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Uploading document for evaluation {id}: type={document_type}, file={file.filename}")

    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type: {document_type}"
        )

    # Check file type
    extraction_service = get_extraction_service()
    doc_info = extraction_service.get_document_type_info(doc_type)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    file_ext = file.filename.lower().split('.')[-1]
    if file_ext not in doc_info.get('accepted_formats', ['pdf']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Accepted: {', '.join(doc_info['accepted_formats'])}"
        )

    # Check file size
    content = await file.read()
    max_size_bytes = doc_info.get('max_size_mb', 10) * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum: {doc_info['max_size_mb']}MB"
        )

    # Get risk repository to verify assessment exists
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    # Check if document already exists for this type
    extraction_repo = get_extraction_repo()
    existing = await extraction_repo.get_by_assessment_and_type(id, document_type)

    if existing:
        # Update existing record
        updates = {
            'document_filename': file.filename,
            'extraction_status': ExtractionStatus.PENDING.value,
            'extracted_data': None,
            'extraction_errors': None,
            'extraction_confidence': None,
        }
        extraction = await extraction_repo.update(existing['id'], updates)
    else:
        # Create new extraction record
        extraction_data = {
            'assessment_id': id,
            'document_type': document_type,
            'document_filename': file.filename,
            'extraction_status': ExtractionStatus.PENDING.value,
            'extraction_method': 'landingai',
        }
        extraction = await extraction_repo.create(extraction_data)

    # Store file bytes in memory for later extraction (in production, use storage)
    # For now, we'll process immediately during the extract endpoint

    return DocumentUploadResponse(
        id=extraction['id'],
        assessment_id=id,
        document_type=doc_type,
        document_filename=file.filename,
        extraction_status=ExtractionStatus.PENDING,
        created_at=_parse_datetime(extraction.get('created_at')) or datetime.utcnow()
    )


@router.post("/evaluations/{id}/extract", response_model=TriggerExtractionResponse)
async def trigger_extraction(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Trigger AI extraction for all uploaded documents.
    In a real implementation, this would queue jobs for async processing.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Triggering extraction for evaluation {id}")

    # Verify assessment exists
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    # Get pending extractions
    extraction_repo = get_extraction_repo()
    extractions = await extraction_repo.get_by_assessment(id)

    pending = [e for e in extractions if e['extraction_status'] == ExtractionStatus.PENDING.value]

    if not pending:
        return TriggerExtractionResponse(
            assessment_id=id,
            documents_queued=0,
            message="No pending documents to extract"
        )

    # Mark all as processing
    for ext in pending:
        await extraction_repo.update_status(ext['id'], ExtractionStatus.PROCESSING.value)

    # Update assessment to indicate document validation in progress
    await risk_repo.update(id, {
        'has_document_validation': True,
        'document_validation_status': 'extracting'
    })

    return TriggerExtractionResponse(
        assessment_id=id,
        documents_queued=len(pending),
        message=f"Extraction queued for {len(pending)} document(s). Processing may take 30-60 seconds per document."
    )


@router.post("/evaluations/{id}/extract-document/{extraction_id}")
async def process_single_extraction(
    id: str,
    extraction_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Process AI extraction for a single document.
    Upload the file and immediately process it.
    """
    logger.info(f"Processing extraction {extraction_id} for evaluation {id}")

    # Get extraction record
    extraction_repo = get_extraction_repo()
    extraction = await extraction_repo.get_by_id(extraction_id)

    if not extraction or extraction['assessment_id'] != id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction {extraction_id} not found"
        )

    # Mark as processing
    await extraction_repo.update_status(extraction_id, ExtractionStatus.PROCESSING.value)

    try:
        # Read file content
        content = await file.read()

        # Get document type
        doc_type = DocumentType(extraction['document_type'])

        # Run extraction
        extraction_service = get_extraction_service()
        result = await extraction_service.extract_document(
            doc_type,
            content,
            file.filename or extraction['document_filename']
        )

        # Update extraction record
        if result['status'] == ExtractionStatus.COMPLETED.value:
            await extraction_repo.update_status(
                extraction_id,
                ExtractionStatus.COMPLETED.value,
                extracted_data=result['extracted_data'],
                confidence=float(result['confidence']) if result.get('confidence') else None
            )
        else:
            await extraction_repo.update_status(
                extraction_id,
                ExtractionStatus.FAILED.value,
                errors=result.get('errors', ['Extraction failed'])
            )

        # Get updated record
        updated = await extraction_repo.get_by_id(extraction_id)

        return _map_to_extraction_response(updated)

    except Exception as e:
        logger.error(f"Extraction error: {e}", exc_info=True)
        await extraction_repo.update_status(
            extraction_id,
            ExtractionStatus.FAILED.value,
            errors=[str(e)]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )


@router.get("/evaluations/{id}/extractions", response_model=DocumentExtractionListResponse)
async def get_extractions(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Get all document extractions for an assessment.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Getting extractions for evaluation {id}")

    extraction_repo = get_extraction_repo()
    extractions = await extraction_repo.get_by_assessment(id)

    # Count by status
    pending = sum(1 for e in extractions if e['extraction_status'] == 'pending')
    processing = sum(1 for e in extractions if e['extraction_status'] == 'processing')
    completed = sum(1 for e in extractions if e['extraction_status'] == 'completed')
    failed = sum(1 for e in extractions if e['extraction_status'] == 'failed')

    return DocumentExtractionListResponse(
        assessment_id=id,
        total_documents=len(extractions),
        pending_count=pending,
        processing_count=processing,
        completed_count=completed,
        failed_count=failed,
        extractions=[_map_to_extraction_response(e) for e in extractions]
    )


@router.post("/evaluations/{id}/cross-validate", response_model=CrossValidationResponse)
async def trigger_cross_validation(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Run cross-validation on extracted data.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Triggering cross-validation for evaluation {id}")

    # Verify assessment exists
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    # Get completed extractions
    extraction_repo = get_extraction_repo()
    extractions = await extraction_repo.get_by_assessment(id)

    completed = [e for e in extractions if e['extraction_status'] == 'completed']

    if len(completed) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 completed extractions required for cross-validation"
        )

    # Build extraction dict for validation
    extraction_dict = {}
    for ext in completed:
        doc_type = DocumentType(ext['document_type'])
        extraction_dict[doc_type] = ext.get('extracted_data', {})

    # Run cross-validation
    validation_service = get_cross_validation_service()
    results = validation_service.validate_documents(extraction_dict)

    # Delete previous validation results
    validation_repo = get_validation_repo()
    await validation_repo.delete_by_assessment(id)

    # Save new results
    result_records = []
    for result in results:
        record = {
            'assessment_id': id,
            'validation_type': result.validation_type.value,
            'documents_compared': result.documents_compared,
            'field_compared': result.field_compared,
            'values_found': result.values_found,
            'is_discrepancy': result.is_discrepancy,
            'severity': result.severity.value if result.severity else None,
            'description': result.description,
            'score_impact': float(result.score_impact),
        }
        result_records.append(record)

    if result_records:
        await validation_repo.create_batch(result_records)

    # Calculate summary
    discrepancies = [r for r in results if r.is_discrepancy]
    critical_count = sum(1 for r in discrepancies if r.severity == DiscrepancySeverity.CRITICAL)
    high_count = sum(1 for r in discrepancies if r.severity == DiscrepancySeverity.HIGH)
    medium_count = sum(1 for r in discrepancies if r.severity == DiscrepancySeverity.MEDIUM)
    low_count = sum(1 for r in discrepancies if r.severity == DiscrepancySeverity.LOW)
    total_impact = validation_service.calculate_total_score_impact(results)

    # Update assessment validation status
    await risk_repo.update(id, {
        'document_validation_status': 'completed'
    })

    # Finalize evaluation with cross-validation results
    # This calculates the final risk score incorporating discrepancy impacts
    fraud_service = get_fraud_service()
    await fraud_service.finalize_evaluation(
        assessment_id=id,
        cross_validation_results=result_records
    )

    logger.info(f"Cross-validation complete for assessment {id}. Discrepancies: {len(discrepancies)}, Score impact: {total_impact}")

    return CrossValidationResponse(
        assessment_id=id,
        total_discrepancies=len(discrepancies),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        total_score_impact=total_impact,
        results=[_map_to_validation_result(r) for r in results],
        validated_at=datetime.utcnow()
    )


@router.get("/evaluations/{id}/discrepancies", response_model=CrossValidationResponse)
async def get_discrepancies(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """
    Get cross-validation discrepancies for an assessment.
    Requires risk_analyst or risk_manager role.
    """
    logger.info(f"Getting discrepancies for evaluation {id}")

    validation_repo = get_validation_repo()
    results = await validation_repo.get_by_assessment(id)

    discrepancies = [r for r in results if r.get('is_discrepancy')]
    critical_count = sum(1 for r in discrepancies if r.get('severity') == 'critical')
    high_count = sum(1 for r in discrepancies if r.get('severity') == 'high')
    medium_count = sum(1 for r in discrepancies if r.get('severity') == 'medium')
    low_count = sum(1 for r in discrepancies if r.get('severity') == 'low')
    total_impact = sum(float(r.get('score_impact', 0)) for r in discrepancies)

    return CrossValidationResponse(
        assessment_id=id,
        total_discrepancies=len(discrepancies),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        total_score_impact=total_impact,
        results=[_map_db_to_validation_result(r) for r in results],
        validated_at=_parse_datetime(results[0].get('created_at')) if results else None
    )


# ==================== Document Extraction Helper Functions ====================

def _map_to_extraction_response(data: dict) -> DocumentExtractionResponse:
    """Map database record to extraction response model"""
    return DocumentExtractionResponse(
        id=data['id'],
        assessment_id=data['assessment_id'],
        document_type=DocumentType(data['document_type']),
        document_filename=data.get('document_filename', ''),
        extraction_status=ExtractionStatus(data['extraction_status']),
        extraction_method=data.get('extraction_method', 'landingai'),
        extraction_confidence=data.get('extraction_confidence'),
        extracted_data=data.get('extracted_data'),
        extraction_errors=data.get('extraction_errors'),
        created_at=_parse_datetime(data.get('created_at')) or datetime.utcnow(),
        updated_at=_parse_datetime(data.get('updated_at'))
    )


def _map_to_validation_result(result: CrossValidationResult) -> CrossValidationResult:
    """Pass through CrossValidationResult (already correct type)"""
    return result


def _map_db_to_validation_result(data: dict) -> CrossValidationResult:
    """Map database record to validation result model"""
    return CrossValidationResult(
        id=data.get('id'),
        validation_type=ValidationType(data['validation_type']),
        documents_compared=data.get('documents_compared', []),
        field_compared=data.get('field_compared'),
        values_found=data.get('values_found', {}),
        is_discrepancy=data.get('is_discrepancy', False),
        severity=DiscrepancySeverity(data['severity']) if data.get('severity') else None,
        description=data.get('description'),
        score_impact=data.get('score_impact', 0)
    )


# ==================== External Contact Endpoints ====================

@router.get("/evaluations/{id}/external-contacts", response_model=ExternalContactListResponse)
async def get_external_contacts(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Get all external contacts for an evaluation.
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Getting external contacts for evaluation {id}")

    # Verify assessment exists
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    service = get_external_contact_service()
    contacts = await service.get_contacts(id)

    # Count by status
    pending_count = sum(1 for c in contacts if c.get('validation_status') == 'pending')
    validated_count = sum(1 for c in contacts if c.get('validation_status') == 'validated')
    suspicious_count = sum(1 for c in contacts if c.get('validation_status') == 'suspicious')
    critical_count = sum(1 for c in contacts if c.get('validation_status') == 'critical')

    return ExternalContactListResponse(
        assessment_id=id,
        total_contacts=len(contacts),
        pending_count=pending_count,
        validated_count=validated_count,
        suspicious_count=suspicious_count,
        critical_count=critical_count,
        contacts=[_map_to_external_contact_response(c) for c in contacts]
    )


@router.post("/evaluations/{id}/external-contacts", response_model=ExternalContactResponse)
async def create_external_contact(
    id: str,
    request: ExternalContactRequest,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Create a new external contact for an evaluation.
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Creating external contact for evaluation {id}: {request.email}")

    # Verify assessment exists
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    user_id = current_user.get('id')

    try:
        service = get_external_contact_service()
        contact = await service.create_contact(id, request, user_id)
        return _map_to_external_contact_response(contact)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/evaluations/{id}/external-contacts/{contact_id}/validate", response_model=ExternalContactResponse)
async def validate_external_contact(
    id: str,
    contact_id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Validate an external contact's email domain for typosquatting.
    Compares against email domains extracted from uploaded documents (RUT, etc.).
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Validating external contact {contact_id} for evaluation {id}")

    # Verify assessment exists and get client info
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    # Get company name from client info (handle None case)
    client_snapshot = assessment.get('client_data_snapshot') or {}
    company_name = client_snapshot.get('nombre_importador')

    # Extract email domains from uploaded documents for comparison
    known_domains = []
    try:
        extraction_repo = get_extraction_repo()
        extractions = await extraction_repo.get_by_assessment(id)

        for extraction in extractions:
            extracted_data = extraction.get('extracted_data') or {}

            # Extract email from RUT document
            if extraction.get('document_type') == 'rut':
                rut_email = extracted_data.get('email', '')
                if rut_email and '@' in rut_email:
                    domain = rut_email.split('@')[1].lower().strip()
                    if domain and domain not in known_domains:
                        known_domains.append(domain)
                        logger.info(f"Added RUT email domain for comparison: {domain}")

            # Extract email from other documents if available
            for email_field in ['email', 'contact_email', 'empresa_email']:
                email_value = extracted_data.get(email_field, '')
                if email_value and '@' in email_value:
                    domain = email_value.split('@')[1].lower().strip()
                    if domain and domain not in known_domains:
                        known_domains.append(domain)

        logger.info(f"Found {len(known_domains)} known domains from documents: {known_domains}")

    except Exception as e:
        logger.warning(f"Could not extract domains from documents: {e}")
        # Continue without document domains - still use company name

    try:
        service = get_external_contact_service()
        contact = await service.validate_email(
            contact_id,
            company_name,
            known_domains=known_domains if known_domains else None
        )
        return _map_to_external_contact_response(contact)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error validating contact {contact_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating email: {str(e)}"
        )


@router.delete("/evaluations/{id}/external-contacts/{contact_id}")
async def delete_external_contact(
    id: str,
    contact_id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Delete an external contact (soft delete).
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Deleting external contact {contact_id}")

    service = get_external_contact_service()
    success = await service.delete_contact(contact_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"External contact {contact_id} not found"
        )

    return {"message": "Contact deleted successfully"}


# ==================== External Contact Helper Functions ====================

def _map_to_external_contact_response(data: dict) -> ExternalContactResponse:
    """Map database record to external contact response model"""
    validation_result = None
    if data.get('validation_result'):
        vr = data['validation_result']
        validation_result = EmailValidationResult(
            is_suspicious=vr.get('is_suspicious', False),
            similar_domain=vr.get('similar_domain'),
            similarity_score=vr.get('similarity_score', 0.0),
            levenshtein_distance=vr.get('levenshtein_distance', 0),
            detection_type=vr.get('detection_type', 'no_match'),
            description=vr.get('description', ''),
            is_free_provider=vr.get('is_free_provider', False),
        )

    return ExternalContactResponse(
        id=data['id'],
        assessment_id=data['assessment_id'],
        email=data['email'],
        sender_name=data.get('sender_name'),
        source=data.get('source', 'comercial_team'),
        validation_status=ExternalContactValidationStatus(data.get('validation_status', 'pending')),
        validation_result=validation_result,
        validated_at=_parse_datetime(data.get('validated_at')),
        created_at=_parse_datetime(data.get('created_at')) or datetime.utcnow(),
        created_by=data.get('created_by'),
        notes=data.get('notes'),
        is_active=data.get('is_active', True),
    )


# ==================== Email Chain Endpoints ====================

@router.get("/evaluations/{id}/email-chains", response_model=EmailChainListResponse)
async def get_email_chains(
    id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Get all email chains for an evaluation.
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Getting email chains for evaluation {id}")

    # Verify assessment exists
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    service = get_email_chain_service()
    chains = await service.get_email_chains(id)

    # Count by status
    pending_count = sum(1 for c in chains if c.get('validation_status') == 'pending')
    validated_count = sum(1 for c in chains if c.get('validation_status') == 'validated')
    suspicious_count = sum(1 for c in chains if c.get('validation_status') == 'suspicious')
    critical_count = sum(1 for c in chains if c.get('validation_status') == 'critical')

    return EmailChainListResponse(
        assessment_id=id,
        total_chains=len(chains),
        pending_count=pending_count,
        validated_count=validated_count,
        suspicious_count=suspicious_count,
        critical_count=critical_count,
        chains=[_map_to_email_chain_response(c) for c in chains]
    )


@router.post("/evaluations/{id}/email-chains", response_model=EmailChainResponse)
async def upload_email_chain(
    id: str,
    text_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Upload an email chain for an evaluation.
    Can upload either a file (.eml, .msg, or .pdf) or paste text content.
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Uploading email chain for evaluation {id}")

    # Verify assessment exists
    risk_repo = get_risk_repo()
    assessment = await risk_repo.get_by_id(id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation {id} not found"
        )

    # Validate input
    if not file and not text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file or text_content must be provided"
        )

    user_id = current_user.get('id')

    try:
        service = get_email_chain_service()

        if file:
            # Validate file type
            filename = file.filename or 'unknown'
            if not filename.lower().endswith(('.eml', '.msg', '.pdf')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be .eml, .msg, or .pdf format"
                )

            # Read and validate file size
            content = await file.read()
            max_size = 10 * 1024 * 1024  # 10MB
            if len(content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File too large. Maximum size is 10MB"
                )

            chain = await service.upload_email_chain(
                assessment_id=id,
                file_content=content,
                filename=filename,
                user_id=user_id,
            )
        else:
            # Validate text size
            max_text_size = 500 * 1024  # 500KB
            if len(text_content) > max_text_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Text content too large. Maximum size is 500KB"
                )

            chain = await service.upload_email_chain(
                assessment_id=id,
                text_content=text_content,
                user_id=user_id,
            )

        return _map_to_email_chain_response(chain)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading email chain: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading email chain: {str(e)}"
        )


@router.post("/evaluations/{id}/email-chains/{chain_id}/validate", response_model=EmailChainResponse)
async def validate_email_chain(
    id: str,
    chain_id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Validate an email chain against document-extracted data.
    Cross-validates sender domains, company names, NITs, and representative names.
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Validating email chain {chain_id} for evaluation {id}")

    try:
        service = get_email_chain_service()

        # Verify chain belongs to this evaluation
        chain = await service.get_email_chain(chain_id)
        if not chain or chain['assessment_id'] != id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email chain {chain_id} not found for evaluation {id}"
            )

        updated_chain = await service.validate_email_chain(chain_id)
        return _map_to_email_chain_response(updated_chain)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error validating email chain {chain_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating email chain: {str(e)}"
        )


@router.delete("/evaluations/{id}/email-chains/{chain_id}")
async def delete_email_chain(
    id: str,
    chain_id: str,
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control']))
):
    """
    Delete an email chain (soft delete).
    Requires risk_analyst, risk_manager, admin, or mesa_control role.
    """
    logger.info(f"Deleting email chain {chain_id}")

    service = get_email_chain_service()

    # Verify chain belongs to this evaluation
    chain = await service.get_email_chain(chain_id)
    if not chain or chain['assessment_id'] != id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email chain {chain_id} not found for evaluation {id}"
        )

    success = await service.delete_email_chain(chain_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email chain {chain_id} not found"
        )

    return {"message": "Email chain deleted successfully"}


# ==================== Email Chain Helper Functions ====================

def _map_to_email_chain_response(data: dict) -> EmailChainResponse:
    """Map database record to email chain response model"""
    parsed_data = None
    if data.get('parsed_data'):
        pd = data['parsed_data']

        # Map messages
        messages = []
        for msg in pd.get('messages', []):
            messages.append(EmailMessage(
                sender_email=msg.get('sender_email', ''),
                sender_name=msg.get('sender_name'),
                sender_domain=msg.get('sender_domain', ''),
                date=msg.get('date'),
                subject=msg.get('subject'),
                body_excerpt=msg.get('body_excerpt'),
            ))

        # Map mentions
        mentions_data = pd.get('mentions', {})
        mentions = ExtractedMentions(
            company_names=mentions_data.get('company_names', []),
            nits=mentions_data.get('nits', []),
            representative_names=mentions_data.get('representative_names', []),
            domains=mentions_data.get('domains', []),
        )

        parsed_data = EmailChainParsedData(
            messages=messages,
            mentions=mentions,
            parse_errors=pd.get('parse_errors', []),
        )

    validation_result = None
    if data.get('validation_result'):
        vr = data['validation_result']

        # Map discrepancies
        discrepancies = []
        for disc in vr.get('discrepancies', []):
            discrepancies.append(EmailChainDiscrepancy(
                field=disc.get('field', ''),
                email_value=disc.get('email_value', ''),
                document_value=disc.get('document_value'),
                severity=DiscrepancySeverity(disc.get('severity', 'low')),
                description=disc.get('description', ''),
                is_typosquatting=disc.get('is_typosquatting', False),
                similarity_score=disc.get('similarity_score'),
            ))

        validation_result = EmailChainValidationResult(
            total_discrepancies=vr.get('total_discrepancies', 0),
            critical_count=vr.get('critical_count', 0),
            high_count=vr.get('high_count', 0),
            medium_count=vr.get('medium_count', 0),
            low_count=vr.get('low_count', 0),
            discrepancies=discrepancies,
            summary=vr.get('summary', ''),
            validated_at=_parse_datetime(vr.get('validated_at')),
        )

    return EmailChainResponse(
        id=data['id'],
        assessment_id=data['assessment_id'],
        original_filename=data.get('original_filename'),
        parsed_data=parsed_data,
        validation_status=EmailChainValidationStatus(data.get('validation_status', 'pending')),
        validation_result=validation_result,
        validated_at=_parse_datetime(data.get('validated_at')),
        created_at=_parse_datetime(data.get('created_at')) or datetime.utcnow(),
        created_by=data.get('created_by'),
        is_active=data.get('is_active', True),
    )
