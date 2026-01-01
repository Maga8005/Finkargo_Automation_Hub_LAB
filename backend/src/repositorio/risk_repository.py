"""
Risk Repository - Database operations for risk management
"""
from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class RiskAssessmentRepository:
    """Repository for risk assessment operations"""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client

        Args:
            supabase_client: Supabase client instance
        """
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new risk assessment record

        Args:
            data: Risk assessment data

        Returns:
            dict: Created assessment record
        """
        logger.info(f"Creating risk assessment for NIT: {data.get('client_nit')}")

        response = self.db.table('risk_assessments') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get risk assessment by UUID

        Args:
            id: Assessment UUID

        Returns:
            Optional[dict]: Assessment record
        """
        response = self.db.table('risk_assessments') \
            .select('*') \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_assessment_id(self, assessment_id: str) -> Optional[dict]:
        """
        Get risk assessment by business ID (e.g., RISK-2025-001)

        Args:
            assessment_id: Business assessment ID

        Returns:
            Optional[dict]: Assessment record
        """
        response = self.db.table('risk_assessments') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .execute()

        return response.data[0] if response.data else None

    async def search(self, filters: dict) -> List[dict]:
        """
        Search risk assessments with filters

        Args:
            filters: Filter parameters (status, risk_level, client_nit, date_from, date_to, limit, offset)

        Returns:
            List[dict]: Matching assessment records
        """
        query = self.db.table('risk_assessments').select('*')

        # Apply filters
        if filters.get('status'):
            query = query.eq('status', filters['status'])

        if filters.get('risk_level'):
            query = query.eq('risk_level', filters['risk_level'])

        if filters.get('client_nit'):
            query = query.ilike('client_nit', f"%{filters['client_nit']}%")

        if filters.get('date_from'):
            date_from = filters['date_from']
            if isinstance(date_from, datetime):
                date_from = date_from.isoformat()
            query = query.gte('created_at', date_from)

        if filters.get('date_to'):
            date_to = filters['date_to']
            if isinstance(date_to, datetime):
                date_to = date_to.isoformat()
            query = query.lte('created_at', date_to)

        if filters.get('assessed_by'):
            query = query.eq('assessed_by', filters['assessed_by'])

        # Apply pagination
        limit = filters.get('limit', 50)
        offset = filters.get('offset', 0)
        query = query.range(offset, offset + limit - 1)

        # Order by most recent first
        query = query.order('created_at', desc=True)

        response = query.execute()
        return response.data if response.data else []

    async def update(self, id: str, updates: dict) -> Optional[dict]:
        """
        Update risk assessment

        Args:
            id: Assessment UUID
            updates: Fields to update

        Returns:
            Optional[dict]: Updated assessment record
        """
        updates['updated_at'] = datetime.utcnow().isoformat()

        response = self.db.table('risk_assessments') \
            .update(updates) \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get risk assessment statistics

        Returns:
            Dict[str, Any]: Statistics including counts by status and risk level
        """
        today = date.today()
        week_ago = today - timedelta(days=7)

        # Total assessments
        total_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .execute()

        # By status
        pending_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('status', 'pending') \
            .execute()

        in_progress_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('status', 'in_progress') \
            .execute()

        completed_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('status', 'completed') \
            .execute()

        escalated_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('status', 'escalated') \
            .execute()

        approved_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('status', 'approved') \
            .execute()

        rejected_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('status', 'rejected') \
            .execute()

        # By risk level
        low_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('risk_level', 'low') \
            .execute()

        medium_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('risk_level', 'medium') \
            .execute()

        high_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('risk_level', 'high') \
            .execute()

        critical_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .eq('risk_level', 'critical') \
            .execute()

        # Today's assessments
        today_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .gte('created_at', today.isoformat()) \
            .execute()

        # This week's assessments
        week_response = self.db.table('risk_assessments') \
            .select('id', count='exact') \
            .gte('created_at', week_ago.isoformat()) \
            .execute()

        total = total_response.count or 0
        approved = approved_response.count or 0
        rejected = rejected_response.count or 0

        # Calculate rates
        decided = approved + rejected
        approval_rate = round((approved / decided) * 100, 2) if decided > 0 else None
        rejection_rate = round((rejected / decided) * 100, 2) if decided > 0 else None

        return {
            'total_assessments': total,
            'pending_review': pending_response.count or 0,
            'in_progress': in_progress_response.count or 0,
            'completed': completed_response.count or 0,
            'escalated': escalated_response.count or 0,
            'approved': approved,
            'rejected': rejected,
            'low_risk_count': low_response.count or 0,
            'medium_risk_count': medium_response.count or 0,
            'high_risk_count': high_response.count or 0,
            'critical_risk_count': critical_response.count or 0,
            'assessed_today': today_response.count or 0,
            'assessed_this_week': week_response.count or 0,
            'approval_rate': approval_rate,
            'rejection_rate': rejection_rate,
        }

    async def get_recent_by_client(self, client_nit: str, limit: int = 5) -> List[dict]:
        """
        Get recent assessments for a specific client

        Args:
            client_nit: Client NIT
            limit: Number of records to return

        Returns:
            List[dict]: Recent assessments for client
        """
        response = self.db.table('risk_assessments') \
            .select('*') \
            .eq('client_nit', client_nit) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []


class FraudRulesRepository:
    """Repository for fraud detection rules"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def list_active(self) -> List[dict]:
        """
        Get active fraud detection rules ordered by weight

        Returns:
            List[dict]: Active rules ordered by weight (descending)
        """
        response = self.db.table('fraud_detection_rules') \
            .select('*') \
            .eq('is_active', True) \
            .order('weight', desc=True) \
            .execute()

        return response.data if response.data else []

    async def list_all(self) -> List[dict]:
        """
        Get all fraud detection rules

        Returns:
            List[dict]: All rules
        """
        response = self.db.table('fraud_detection_rules') \
            .select('*') \
            .order('weight', desc=True) \
            .execute()

        return response.data if response.data else []

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get rule by UUID

        Args:
            id: Rule UUID

        Returns:
            Optional[dict]: Rule record
        """
        response = self.db.table('fraud_detection_rules') \
            .select('*') \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_name(self, rule_name: str) -> Optional[dict]:
        """
        Get rule by name

        Args:
            rule_name: Rule name

        Returns:
            Optional[dict]: Rule record
        """
        response = self.db.table('fraud_detection_rules') \
            .select('*') \
            .eq('rule_name', rule_name) \
            .execute()

        return response.data[0] if response.data else None

    async def update(self, id: str, updates: dict) -> Optional[dict]:
        """
        Update fraud detection rule

        Args:
            id: Rule UUID
            updates: Fields to update

        Returns:
            Optional[dict]: Updated rule record
        """
        updates['updated_at'] = datetime.utcnow().isoformat()

        response = self.db.table('fraud_detection_rules') \
            .update(updates) \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def create(self, data: dict) -> dict:
        """
        Create new fraud detection rule

        Args:
            data: Rule data

        Returns:
            dict: Created rule record
        """
        response = self.db.table('fraud_detection_rules') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None


class BlacklistRepository:
    """Repository for risk blacklist operations"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def is_blacklisted(self, entity_type: str, entity_value: str) -> bool:
        """
        Check if an entity is blacklisted

        Args:
            entity_type: Type of entity (nit, email_domain, etc.)
            entity_value: Value to check

        Returns:
            bool: True if blacklisted, False otherwise
        """
        response = self.db.table('risk_blacklist') \
            .select('id') \
            .eq('entity_type', entity_type) \
            .eq('entity_value', entity_value.lower()) \
            .eq('is_active', True) \
            .execute()

        return len(response.data) > 0 if response.data else False

    async def check_any_blacklisted(self, checks: List[Dict[str, str]]) -> Optional[dict]:
        """
        Check if any of the provided entities are blacklisted

        Args:
            checks: List of dicts with entity_type and entity_value

        Returns:
            Optional[dict]: First matching blacklist entry, or None
        """
        for check in checks:
            entity_type = check.get('entity_type')
            entity_value = check.get('entity_value', '').lower()

            if not entity_type or not entity_value:
                continue

            response = self.db.table('risk_blacklist') \
                .select('*') \
                .eq('entity_type', entity_type) \
                .eq('entity_value', entity_value) \
                .eq('is_active', True) \
                .execute()

            if response.data:
                return response.data[0]

        return None

    async def search(self, filters: dict) -> List[dict]:
        """
        Search blacklist entries with filters

        Args:
            filters: Filter parameters

        Returns:
            List[dict]: Matching blacklist entries
        """
        query = self.db.table('risk_blacklist').select('*')

        if filters.get('entity_type'):
            query = query.eq('entity_type', filters['entity_type'])

        if filters.get('is_active') is not None:
            query = query.eq('is_active', filters['is_active'])

        # Apply pagination
        limit = filters.get('limit', 50)
        offset = filters.get('offset', 0)
        query = query.range(offset, offset + limit - 1)

        query = query.order('added_at', desc=True)

        response = query.execute()
        return response.data if response.data else []

    async def add(self, data: dict) -> dict:
        """
        Add entry to blacklist

        Args:
            data: Blacklist entry data

        Returns:
            dict: Created blacklist entry
        """
        # Normalize entity_value to lowercase
        if 'entity_value' in data:
            data['entity_value'] = data['entity_value'].lower()

        response = self.db.table('risk_blacklist') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def remove(self, id: str) -> bool:
        """
        Soft delete blacklist entry (set is_active to False)

        Args:
            id: Blacklist entry UUID

        Returns:
            bool: True if successful
        """
        response = self.db.table('risk_blacklist') \
            .update({'is_active': False}) \
            .eq('id', id) \
            .execute()

        return len(response.data) > 0 if response.data else False

    async def hard_delete(self, id: str) -> bool:
        """
        Permanently delete blacklist entry

        Args:
            id: Blacklist entry UUID

        Returns:
            bool: True if successful
        """
        self.db.table('risk_blacklist') \
            .delete() \
            .eq('id', id) \
            .execute()

        return True


class DocumentExtractionRepository:
    """Repository for document extraction operations"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new document extraction record

        Args:
            data: Extraction data

        Returns:
            dict: Created extraction record
        """
        logger.info(f"Creating document extraction for assessment: {data.get('assessment_id')}")

        response = self.db.table('risk_document_extractions') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get document extraction by UUID

        Args:
            id: Extraction UUID

        Returns:
            Optional[dict]: Extraction record
        """
        response = self.db.table('risk_document_extractions') \
            .select('*') \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all document extractions for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Extraction records
        """
        response = self.db.table('risk_document_extractions') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .order('created_at', desc=False) \
            .execute()

        return response.data if response.data else []

    async def get_by_assessment_and_type(
        self,
        assessment_id: str,
        document_type: str
    ) -> Optional[dict]:
        """
        Get document extraction by assessment and type

        Args:
            assessment_id: Assessment UUID
            document_type: Document type

        Returns:
            Optional[dict]: Extraction record
        """
        response = self.db.table('risk_document_extractions') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .eq('document_type', document_type) \
            .execute()

        return response.data[0] if response.data else None

    async def update(self, id: str, updates: dict) -> Optional[dict]:
        """
        Update document extraction

        Args:
            id: Extraction UUID
            updates: Fields to update

        Returns:
            Optional[dict]: Updated extraction record
        """
        from datetime import datetime
        updates['updated_at'] = datetime.utcnow().isoformat()

        response = self.db.table('risk_document_extractions') \
            .update(updates) \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def update_status(
        self,
        id: str,
        status: str,
        extracted_data: Optional[dict] = None,
        errors: Optional[List[str]] = None,
        confidence: Optional[float] = None
    ) -> Optional[dict]:
        """
        Update extraction status and data

        Args:
            id: Extraction UUID
            status: New status
            extracted_data: Extracted data (if completed)
            errors: Error messages (if failed)
            confidence: Extraction confidence score

        Returns:
            Optional[dict]: Updated extraction record
        """
        from datetime import datetime
        updates = {
            'extraction_status': status,
            'updated_at': datetime.utcnow().isoformat()
        }

        if extracted_data is not None:
            updates['extracted_data'] = extracted_data
        if errors is not None:
            updates['extraction_errors'] = errors
        if confidence is not None:
            updates['extraction_confidence'] = float(confidence)

        response = self.db.table('risk_document_extractions') \
            .update(updates) \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def delete(self, id: str) -> bool:
        """
        Delete document extraction

        Args:
            id: Extraction UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('risk_document_extractions') \
            .delete() \
            .eq('id', id) \
            .execute()

        return True

    async def delete_by_assessment(self, assessment_id: str) -> bool:
        """
        Delete all extractions for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('risk_document_extractions') \
            .delete() \
            .eq('assessment_id', assessment_id) \
            .execute()

        return True


class CrossValidationRepository:
    """Repository for cross-validation result operations"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new cross-validation result

        Args:
            data: Validation result data

        Returns:
            dict: Created result record
        """
        response = self.db.table('risk_cross_validation_results') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def create_batch(self, results: List[dict]) -> List[dict]:
        """
        Create multiple cross-validation results

        Args:
            results: List of validation result data

        Returns:
            List[dict]: Created result records
        """
        if not results:
            return []

        response = self.db.table('risk_cross_validation_results') \
            .insert(results) \
            .execute()

        return response.data if response.data else []

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all cross-validation results for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Validation result records
        """
        response = self.db.table('risk_cross_validation_results') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .order('created_at', desc=False) \
            .execute()

        return response.data if response.data else []

    async def get_discrepancies(self, assessment_id: str) -> List[dict]:
        """
        Get only discrepancy results for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Discrepancy records
        """
        response = self.db.table('risk_cross_validation_results') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .eq('is_discrepancy', True) \
            .order('severity', desc=True) \
            .execute()

        return response.data if response.data else []

    async def delete_by_assessment(self, assessment_id: str) -> bool:
        """
        Delete all validation results for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('risk_cross_validation_results') \
            .delete() \
            .eq('assessment_id', assessment_id) \
            .execute()

        return True


class AlertRepository:
    """Repository for risk alert operations"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new alert

        Args:
            data: Alert data

        Returns:
            dict: Created alert record
        """
        response = self.db.table('risk_alerts') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_unread(self, limit: int = 20) -> List[dict]:
        """
        Get unread alerts ordered by severity and date

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List[dict]: Unread alerts
        """
        response = self.db.table('risk_alerts') \
            .select('*') \
            .eq('is_read', False) \
            .order('severity', desc=True) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []

    async def get_all(self, limit: int = 50, include_read: bool = False) -> List[dict]:
        """
        Get all alerts

        Args:
            limit: Maximum number of alerts to return
            include_read: Include read alerts

        Returns:
            List[dict]: Alert records
        """
        query = self.db.table('risk_alerts').select('*')

        if not include_read:
            query = query.eq('is_read', False)

        response = query \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()

        return response.data if response.data else []

    async def mark_read(self, id: str, user_id: str) -> bool:
        """
        Mark alert as read

        Args:
            id: Alert UUID
            user_id: User who read the alert

        Returns:
            bool: True if successful
        """
        response = self.db.table('risk_alerts') \
            .update({
                'is_read': True,
                'read_by': user_id,
                'read_at': datetime.utcnow().isoformat()
            }) \
            .eq('id', id) \
            .execute()

        return len(response.data) > 0 if response.data else False

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all alerts for a specific assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Alerts for the assessment
        """
        response = self.db.table('risk_alerts') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .order('created_at', desc=True) \
            .execute()

        return response.data if response.data else []


class ExternalContactRepository:
    """Repository for external contact operations (email validation)"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new external contact record

        Args:
            data: External contact data

        Returns:
            dict: Created contact record
        """
        logger.info(f"Creating external contact for assessment: {data.get('assessment_id')}")

        response = self.db.table('risk_external_contacts') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get external contact by UUID

        Args:
            id: Contact UUID

        Returns:
            Optional[dict]: Contact record
        """
        response = self.db.table('risk_external_contacts') \
            .select('*') \
            .eq('id', id) \
            .eq('is_active', True) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all external contacts for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Contact records
        """
        response = self.db.table('risk_external_contacts') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .order('created_at', desc=False) \
            .execute()

        return response.data if response.data else []

    async def update(self, id: str, updates: dict) -> Optional[dict]:
        """
        Update external contact

        Args:
            id: Contact UUID
            updates: Fields to update

        Returns:
            Optional[dict]: Updated contact record
        """
        response = self.db.table('risk_external_contacts') \
            .update(updates) \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def delete(self, id: str) -> bool:
        """
        Soft delete external contact (set is_active to False)

        Args:
            id: Contact UUID

        Returns:
            bool: True if successful
        """
        response = self.db.table('risk_external_contacts') \
            .update({'is_active': False}) \
            .eq('id', id) \
            .execute()

        return len(response.data) > 0 if response.data else False

    async def get_suspicious_count(self, assessment_id: str) -> int:
        """
        Get count of suspicious or critical contacts for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            int: Count of suspicious/critical contacts
        """
        response = self.db.table('risk_external_contacts') \
            .select('id', count='exact') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .in_('validation_status', ['suspicious', 'critical']) \
            .execute()

        return response.count or 0


class EmailChainRepository:
    """Repository for email chain operations (cross-validation)"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new email chain record

        Args:
            data: Email chain data

        Returns:
            dict: Created email chain record
        """
        logger.info(f"Creating email chain for assessment: {data.get('assessment_id')}")

        response = self.db.table('email_chains') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get email chain by UUID

        Args:
            id: Email chain UUID

        Returns:
            Optional[dict]: Email chain record
        """
        response = self.db.table('email_chains') \
            .select('*') \
            .eq('id', id) \
            .eq('is_active', True) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all email chains for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Email chain records
        """
        response = self.db.table('email_chains') \
            .select('*') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .order('created_at', desc=False) \
            .execute()

        return response.data if response.data else []

    async def update(self, id: str, updates: dict) -> Optional[dict]:
        """
        Update email chain

        Args:
            id: Email chain UUID
            updates: Fields to update

        Returns:
            Optional[dict]: Updated email chain record
        """
        response = self.db.table('email_chains') \
            .update(updates) \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def delete(self, id: str) -> bool:
        """
        Soft delete email chain (set is_active to False)

        Args:
            id: Email chain UUID

        Returns:
            bool: True if successful
        """
        response = self.db.table('email_chains') \
            .update({'is_active': False}) \
            .eq('id', id) \
            .execute()

        return len(response.data) > 0 if response.data else False

    async def get_suspicious_count(self, assessment_id: str) -> int:
        """
        Get count of suspicious or critical email chains for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            int: Count of suspicious/critical chains
        """
        response = self.db.table('email_chains') \
            .select('id', count='exact') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .in_('validation_status', ['suspicious', 'critical']) \
            .execute()

        return response.count or 0


class DiscrepancyValidationRepository:
    """Repository for discrepancy validation operations (mesa de control validations)"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new discrepancy validation record

        Args:
            data: Validation data

        Returns:
            dict: Created validation record
        """
        logger.info(f"Creating discrepancy validation for result: {data.get('cross_validation_result_id')}")

        response = self.db.table('discrepancy_validations') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get validation by UUID

        Args:
            id: Validation UUID

        Returns:
            Optional[dict]: Validation record
        """
        response = self.db.table('discrepancy_validations') \
            .select('*') \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_cross_validation_result_id(self, cross_validation_result_id: str) -> Optional[dict]:
        """
        Get validation by cross-validation result ID

        Args:
            cross_validation_result_id: Cross-validation result UUID

        Returns:
            Optional[dict]: Validation record
        """
        response = self.db.table('discrepancy_validations') \
            .select('*') \
            .eq('cross_validation_result_id', cross_validation_result_id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all validations for an assessment's discrepancies

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Validation records
        """
        # First get all cross-validation result IDs for this assessment
        cv_response = self.db.table('risk_cross_validation_results') \
            .select('id') \
            .eq('assessment_id', assessment_id) \
            .eq('is_discrepancy', True) \
            .execute()

        if not cv_response.data:
            return []

        cv_ids = [r['id'] for r in cv_response.data]

        # Then get validations for those results
        response = self.db.table('discrepancy_validations') \
            .select('*') \
            .in_('cross_validation_result_id', cv_ids) \
            .order('created_at', desc=False) \
            .execute()

        return response.data if response.data else []

    async def upsert(self, cross_validation_result_id: str, data: dict) -> dict:
        """
        Create or update validation for a cross-validation result

        Args:
            cross_validation_result_id: Cross-validation result UUID
            data: Validation data

        Returns:
            dict: Created or updated validation record
        """
        # Check if validation already exists
        existing = await self.get_by_cross_validation_result_id(cross_validation_result_id)

        if existing:
            # Update existing validation
            data['updated_at'] = datetime.utcnow().isoformat()
            response = self.db.table('discrepancy_validations') \
                .update(data) \
                .eq('id', existing['id']) \
                .execute()
            return response.data[0] if response.data else None
        else:
            # Create new validation
            data['cross_validation_result_id'] = cross_validation_result_id
            return await self.create(data)

    async def update(self, id: str, updates: dict) -> Optional[dict]:
        """
        Update validation record

        Args:
            id: Validation UUID
            updates: Fields to update

        Returns:
            Optional[dict]: Updated validation record
        """
        updates['updated_at'] = datetime.utcnow().isoformat()

        response = self.db.table('discrepancy_validations') \
            .update(updates) \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def delete(self, id: str) -> bool:
        """
        Delete validation record

        Args:
            id: Validation UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('discrepancy_validations') \
            .delete() \
            .eq('id', id) \
            .execute()

        return True

    async def delete_by_cross_validation_result(self, cross_validation_result_id: str) -> bool:
        """
        Delete validation for a specific cross-validation result

        Args:
            cross_validation_result_id: Cross-validation result UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('discrepancy_validations') \
            .delete() \
            .eq('cross_validation_result_id', cross_validation_result_id) \
            .execute()

        return True

    async def get_validation_progress(self, assessment_id: str) -> Dict[str, Any]:
        """
        Get validation progress for an assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            Dict with total_discrepancies, validated_count, pending_count, all_validated
        """
        # Get total discrepancies for assessment
        cv_response = self.db.table('risk_cross_validation_results') \
            .select('id', count='exact') \
            .eq('assessment_id', assessment_id) \
            .eq('is_discrepancy', True) \
            .execute()

        total_discrepancies = cv_response.count or 0

        if total_discrepancies == 0:
            return {
                'total_discrepancies': 0,
                'validated_count': 0,
                'pending_count': 0,
                'all_validated': True,
            }

        # Get validated count
        validations = await self.get_by_assessment(assessment_id)
        validated_count = sum(1 for v in validations if v.get('is_validated', False))

        return {
            'total_discrepancies': total_discrepancies,
            'validated_count': validated_count,
            'pending_count': total_discrepancies - validated_count,
            'all_validated': validated_count >= total_discrepancies,
        }


class EmailChainDiscrepancyValidationRepository:
    """Repository for email chain discrepancy validation operations"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new email chain discrepancy validation record

        Args:
            data: Validation data

        Returns:
            dict: Created validation record
        """
        logger.info(f"Creating email chain discrepancy validation for chain: {data.get('email_chain_id')}, index: {data.get('discrepancy_index')}")

        response = self.db.table('email_chain_discrepancy_validations') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get validation by UUID

        Args:
            id: Validation UUID

        Returns:
            Optional[dict]: Validation record
        """
        response = self.db.table('email_chain_discrepancy_validations') \
            .select('*') \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_email_chain_and_index(self, email_chain_id: str, discrepancy_index: int) -> Optional[dict]:
        """
        Get validation by email chain ID and discrepancy index

        Args:
            email_chain_id: Email chain UUID
            discrepancy_index: Index of discrepancy in validation_result.discrepancies array

        Returns:
            Optional[dict]: Validation record
        """
        response = self.db.table('email_chain_discrepancy_validations') \
            .select('*') \
            .eq('email_chain_id', email_chain_id) \
            .eq('discrepancy_index', discrepancy_index) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_email_chain(self, email_chain_id: str) -> List[dict]:
        """
        Get all validations for an email chain

        Args:
            email_chain_id: Email chain UUID

        Returns:
            List[dict]: Validation records
        """
        response = self.db.table('email_chain_discrepancy_validations') \
            .select('*') \
            .eq('email_chain_id', email_chain_id) \
            .order('discrepancy_index', desc=False) \
            .execute()

        return response.data if response.data else []

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all validations for an assessment's email chain discrepancies

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Validation records
        """
        # First get all email chain IDs for this assessment
        ec_response = self.db.table('email_chains') \
            .select('id') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .execute()

        if not ec_response.data:
            return []

        ec_ids = [r['id'] for r in ec_response.data]

        # Then get validations for those chains
        response = self.db.table('email_chain_discrepancy_validations') \
            .select('*') \
            .in_('email_chain_id', ec_ids) \
            .order('created_at', desc=False) \
            .execute()

        return response.data if response.data else []

    async def upsert(self, email_chain_id: str, discrepancy_index: int, data: dict) -> dict:
        """
        Create or update validation for an email chain discrepancy

        Args:
            email_chain_id: Email chain UUID
            discrepancy_index: Index of discrepancy
            data: Validation data

        Returns:
            dict: Created or updated validation record
        """
        # Check if validation already exists
        existing = await self.get_by_email_chain_and_index(email_chain_id, discrepancy_index)

        if existing:
            # Update existing validation
            data['updated_at'] = datetime.utcnow().isoformat()
            response = self.db.table('email_chain_discrepancy_validations') \
                .update(data) \
                .eq('id', existing['id']) \
                .execute()
            return response.data[0] if response.data else None
        else:
            # Create new validation
            data['email_chain_id'] = email_chain_id
            data['discrepancy_index'] = discrepancy_index
            return await self.create(data)

    async def delete(self, id: str) -> bool:
        """
        Delete validation record

        Args:
            id: Validation UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('email_chain_discrepancy_validations') \
            .delete() \
            .eq('id', id) \
            .execute()

        return True

    async def delete_by_email_chain_and_index(self, email_chain_id: str, discrepancy_index: int) -> bool:
        """
        Delete validation for a specific email chain discrepancy

        Args:
            email_chain_id: Email chain UUID
            discrepancy_index: Index of discrepancy

        Returns:
            bool: True if deleted
        """
        self.db.table('email_chain_discrepancy_validations') \
            .delete() \
            .eq('email_chain_id', email_chain_id) \
            .eq('discrepancy_index', discrepancy_index) \
            .execute()

        return True

    async def get_validation_progress(self, assessment_id: str) -> Dict[str, Any]:
        """
        Get validation progress for an assessment's email chain discrepancies

        Args:
            assessment_id: Assessment UUID

        Returns:
            Dict with total_discrepancies, validated_count, pending_count, all_validated
        """
        # Get all email chains with discrepancies for assessment
        ec_response = self.db.table('email_chains') \
            .select('id, validation_result') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .in_('validation_status', ['suspicious', 'critical']) \
            .execute()

        if not ec_response.data:
            return {
                'total_discrepancies': 0,
                'validated_count': 0,
                'pending_count': 0,
                'all_validated': True,
            }

        # Count total discrepancies across all chains
        total_discrepancies = 0
        for chain in ec_response.data:
            if chain.get('validation_result') and chain['validation_result'].get('discrepancies'):
                total_discrepancies += len(chain['validation_result']['discrepancies'])

        if total_discrepancies == 0:
            return {
                'total_discrepancies': 0,
                'validated_count': 0,
                'pending_count': 0,
                'all_validated': True,
            }

        # Get validated count
        validations = await self.get_by_assessment(assessment_id)
        validated_count = sum(1 for v in validations if v.get('is_validated', False))

        return {
            'total_discrepancies': total_discrepancies,
            'validated_count': validated_count,
            'pending_count': total_discrepancies - validated_count,
            'all_validated': validated_count >= total_discrepancies,
        }


class ExternalContactValidationRepository:
    """Repository for external contact validation operations"""

    def __init__(self, supabase_client: Client):
        """Initialize repository with Supabase client"""
        self.db = supabase_client

    async def create(self, data: dict) -> dict:
        """
        Create new external contact validation record

        Args:
            data: Validation data

        Returns:
            dict: Created validation record
        """
        logger.info(f"Creating external contact validation for contact: {data.get('external_contact_id')}")

        response = self.db.table('external_contact_validations') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, id: str) -> Optional[dict]:
        """
        Get validation by UUID

        Args:
            id: Validation UUID

        Returns:
            Optional[dict]: Validation record
        """
        response = self.db.table('external_contact_validations') \
            .select('*') \
            .eq('id', id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_external_contact_id(self, external_contact_id: str) -> Optional[dict]:
        """
        Get validation by external contact ID

        Args:
            external_contact_id: External contact UUID

        Returns:
            Optional[dict]: Validation record
        """
        response = self.db.table('external_contact_validations') \
            .select('*') \
            .eq('external_contact_id', external_contact_id) \
            .execute()

        return response.data[0] if response.data else None

    async def get_by_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all validations for an assessment's external contacts

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Validation records
        """
        # First get all external contact IDs for this assessment (suspicious or critical)
        ec_response = self.db.table('risk_external_contacts') \
            .select('id') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .in_('validation_status', ['suspicious', 'critical']) \
            .execute()

        if not ec_response.data:
            return []

        ec_ids = [r['id'] for r in ec_response.data]

        # Then get validations for those contacts
        response = self.db.table('external_contact_validations') \
            .select('*') \
            .in_('external_contact_id', ec_ids) \
            .order('created_at', desc=False) \
            .execute()

        return response.data if response.data else []

    async def upsert(self, external_contact_id: str, data: dict) -> dict:
        """
        Create or update validation for an external contact

        Args:
            external_contact_id: External contact UUID
            data: Validation data

        Returns:
            dict: Created or updated validation record
        """
        # Check if validation already exists
        existing = await self.get_by_external_contact_id(external_contact_id)

        if existing:
            # Update existing validation
            data['updated_at'] = datetime.utcnow().isoformat()
            response = self.db.table('external_contact_validations') \
                .update(data) \
                .eq('id', existing['id']) \
                .execute()
            return response.data[0] if response.data else None
        else:
            # Create new validation
            data['external_contact_id'] = external_contact_id
            return await self.create(data)

    async def delete(self, id: str) -> bool:
        """
        Delete validation record

        Args:
            id: Validation UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('external_contact_validations') \
            .delete() \
            .eq('id', id) \
            .execute()

        return True

    async def delete_by_external_contact_id(self, external_contact_id: str) -> bool:
        """
        Delete validation for a specific external contact

        Args:
            external_contact_id: External contact UUID

        Returns:
            bool: True if deleted
        """
        self.db.table('external_contact_validations') \
            .delete() \
            .eq('external_contact_id', external_contact_id) \
            .execute()

        return True

    async def get_validation_progress(self, assessment_id: str) -> Dict[str, Any]:
        """
        Get validation progress for an assessment's external contact alerts

        Args:
            assessment_id: Assessment UUID

        Returns:
            Dict with total_alerts, validated_count, pending_count, all_validated
        """
        # Get count of suspicious/critical contacts for assessment
        ec_response = self.db.table('risk_external_contacts') \
            .select('id', count='exact') \
            .eq('assessment_id', assessment_id) \
            .eq('is_active', True) \
            .in_('validation_status', ['suspicious', 'critical']) \
            .execute()

        total_alerts = ec_response.count or 0

        if total_alerts == 0:
            return {
                'total_alerts': 0,
                'validated_count': 0,
                'pending_count': 0,
                'all_validated': True,
            }

        # Get validated count
        validations = await self.get_by_assessment(assessment_id)
        validated_count = sum(1 for v in validations if v.get('is_validated', False))

        return {
            'total_alerts': total_alerts,
            'validated_count': validated_count,
            'pending_count': total_alerts - validated_count,
            'all_validated': validated_count >= total_alerts,
        }
