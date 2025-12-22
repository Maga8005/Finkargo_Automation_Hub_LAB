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
)
from src.repositorio.client_repository import ClientRepository
from src.core.servicios.risk.fraud_detection_service import FraudDetectionService
from src.core.servicios.risk.risk_scoring_service import RiskScoringService
from src.core.servicios.risk.alert_service import AlertService
from src.core.servicios.risk.document_extraction_service import DocumentExtractionService
from src.core.servicios.risk.cross_validation_service import CrossValidationService
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
    TriggerValidationResponse,
    DiscrepancySeverity,
    ValidationType,
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

    return RiskStatsResponse(**stats)


# ==================== Evaluation Endpoints ====================

@router.get("/evaluations", response_model=List[RiskAssessmentDetail])
async def list_evaluations(
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
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
    logger.info(f"Listing evaluations with filters: status={status}, risk_level={risk_level}")

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

    return [_map_to_detail(eval_data) for eval_data in evaluations]


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

    return _map_to_detail(evaluation)


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

    fraud_service = get_fraud_service()
    assessment = await fraud_service.evaluate_client(
        client_nit=request.client_nit,
        user_id=user_id,
        assessment_type=request.assessment_type.value
    )

    return _map_to_response(assessment)


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

    return _map_to_detail(updated)


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

def _map_to_response(data: dict) -> RiskAssessmentResponse:
    """Map database record to response model"""
    indicators = data.get('fraud_indicators', [])
    if isinstance(indicators, list):
        indicators = [_map_indicator(ind) for ind in indicators]

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
    )


def _map_to_detail(data: dict) -> RiskAssessmentDetail:
    """Map database record to detail model"""
    indicators = data.get('fraud_indicators', [])
    if isinstance(indicators, list):
        indicators = [_map_indicator(ind) for ind in indicators]

    # Extract client info from snapshot
    snapshot = data.get('client_data_snapshot', {})
    client_info = None
    if snapshot:
        client_info = ClientInfo(
            nit=snapshot.get('nit', data['client_nit']),
            nombre_importador=snapshot.get('nombre_importador'),
            representante_legal=snapshot.get('representante_legal'),
            ciudad_domicilio=snapshot.get('ciudad_domicilio'),
            cupo_plataforma=snapshot.get('cupo_plataforma'),
        )

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
