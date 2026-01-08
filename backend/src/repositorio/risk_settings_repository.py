"""
Risk Settings Repository - Database operations for risk module settings
"""
from typing import List, Optional, Any
from supabase import Client
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class RiskSettingsRepository:
    """Repository for risk settings CRUD operations"""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client

        Args:
            supabase_client: Supabase client instance
        """
        self.db = supabase_client

    async def get_setting(self, key: str) -> Optional[dict]:
        """
        Get a setting by key

        Args:
            key: Setting key (e.g., 'ai_email_extraction_enabled')

        Returns:
            Optional[dict]: Setting record with id, setting_key, setting_value, value_type, description
        """
        response = self.db.table('risk_settings') \
            .select('*') \
            .eq('setting_key', key) \
            .execute()

        return response.data[0] if response.data else None

    async def get_all_settings(self) -> List[dict]:
        """
        Get all risk settings

        Returns:
            List[dict]: All settings records
        """
        response = self.db.table('risk_settings') \
            .select('*') \
            .order('setting_key') \
            .execute()

        return response.data if response.data else []

    async def update_setting(
        self,
        key: str,
        value: Any,
        user_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Update a setting value

        Args:
            key: Setting key
            value: New value (will be serialized to JSONB)
            user_id: UUID of user making the update

        Returns:
            Optional[dict]: Updated setting record
        """
        # Serialize value to JSON for JSONB storage
        updates = {
            'setting_value': json.dumps(value) if not isinstance(value, str) else value,
            'updated_at': datetime.utcnow().isoformat()
        }

        if user_id:
            updates['updated_by'] = user_id

        logger.info(f"Updating risk setting '{key}' to: {value}")

        response = self.db.table('risk_settings') \
            .update(updates) \
            .eq('setting_key', key) \
            .execute()

        return response.data[0] if response.data else None

    async def is_ai_extraction_enabled(self) -> bool:
        """
        Check if AI extraction is enabled

        Returns:
            bool: True if AI extraction is enabled, False otherwise
        """
        setting = await self.get_setting('ai_email_extraction_enabled')

        if not setting:
            return False

        setting_value = setting.get('setting_value')

        # Handle JSONB value - could be boolean, string 'true'/'false', or JSON string
        if isinstance(setting_value, bool):
            return setting_value
        elif isinstance(setting_value, str):
            # Try to parse JSON string
            try:
                parsed = json.loads(setting_value)
                if isinstance(parsed, bool):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            # Handle string 'true'/'false'
            return setting_value.lower() == 'true'

        return False

    async def create_setting(
        self,
        key: str,
        value: Any,
        value_type: str = 'boolean',
        description: Optional[str] = None
    ) -> Optional[dict]:
        """
        Create a new setting

        Args:
            key: Setting key
            value: Setting value
            value_type: Type of value ('boolean', 'number', 'text', 'json')
            description: Optional description

        Returns:
            Optional[dict]: Created setting record
        """
        data = {
            'setting_key': key,
            'setting_value': json.dumps(value) if not isinstance(value, str) else value,
            'value_type': value_type,
            'description': description
        }

        logger.info(f"Creating risk setting: {key}")

        response = self.db.table('risk_settings') \
            .insert(data) \
            .execute()

        return response.data[0] if response.data else None
