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
