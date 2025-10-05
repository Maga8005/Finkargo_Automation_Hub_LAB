"""
Template Repository - Database operations for contract templates
"""
from typing import List, Optional
from supabase import Client


class TemplateRepository:
    """Repository for contract template operations"""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client

        Args:
            supabase_client: Supabase client instance
        """
        self.db = supabase_client

    async def get_active_template(self, contract_type: str = 'activos') -> Optional[dict]:
        """
        Get the active template for a contract type

        Args:
            contract_type: Type of contract (default: 'activos')

        Returns:
            Optional[dict]: Active template or None
        """
        response = self.db.table('contract_templates')\
            .select('*')\
            .eq('contract_type', contract_type)\
            .eq('active', True)\
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, template_id: str) -> Optional[dict]:
        """
        Get template by ID

        Args:
            template_id: Template UUID

        Returns:
            Optional[dict]: Template record
        """
        response = self.db.table('contract_templates')\
            .select('*')\
            .eq('id', template_id)\
            .execute()

        return response.data[0] if response.data else None

    async def create(self, template_data: dict) -> dict:
        """
        Create new template version

        Args:
            template_data: Template data

        Returns:
            dict: Created template record
        """
        response = self.db.table('contract_templates')\
            .insert(template_data)\
            .execute()

        return response.data[0] if response.data else None

    async def set_active(self, template_id: str, contract_type: str) -> dict:
        """
        Set a template as active (deactivates others of same type)

        Args:
            template_id: Template UUID to activate
            contract_type: Contract type

        Returns:
            dict: Updated template record
        """
        # First, deactivate all templates of this type
        self.db.table('contract_templates')\
            .update({'active': False})\
            .eq('contract_type', contract_type)\
            .execute()

        # Then activate the specified template
        response = self.db.table('contract_templates')\
            .update({'active': True})\
            .eq('id', template_id)\
            .execute()

        return response.data[0] if response.data else None

    async def list_versions(self, contract_type: str = 'activos') -> List[dict]:
        """
        List all template versions for a contract type

        Args:
            contract_type: Type of contract

        Returns:
            List[dict]: List of template versions
        """
        response = self.db.table('contract_templates')\
            .select('*')\
            .eq('contract_type', contract_type)\
            .order('created_at', desc=True)\
            .execute()

        return response.data if response.data else []
