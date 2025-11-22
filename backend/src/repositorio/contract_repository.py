"""
Contract Repository - Database operations for contract generations
"""
from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime, date
from src.interface.legal_dtos import ContractStatus, ContractHistoryFilter


class ContractRepository:
    """Repository for contract generation operations"""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client

        Args:
            supabase_client: Supabase client instance
        """
        self.db = supabase_client

    async def generate_contract_id(self, contract_type: str = 'activos') -> str:
        """
        Generate next contract ID using database function

        Args:
            contract_type: Type of contract ('activos' or 'otrosi')

        Returns:
            str: Generated contract ID (e.g., ACT-2025-001 or OTRO-2025-001)
        """
        response = self.db.rpc('generate_contract_id', {'p_contract_type': contract_type}).execute()
        return response.data if response.data else None

    async def create(self, contract_data: dict) -> dict:
        """
        Create new contract generation record

        Args:
            contract_data: Contract generation data

        Returns:
            dict: Created contract record
        """
        response = self.db.table('contract_generations')\
            .insert(contract_data)\
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, contract_id: str) -> Optional[dict]:
        """
        Get contract by UUID

        Args:
            contract_id: Contract UUID

        Returns:
            Optional[dict]: Contract record
        """
        response = self.db.table('contract_generations')\
            .select('*')\
            .eq('id', contract_id)\
            .execute()

        return response.data[0] if response.data else None

    async def get_by_contract_id(self, contract_id: str) -> Optional[dict]:
        """
        Get contract by contract ID (e.g., ACT-2025-001)

        Args:
            contract_id: Business contract ID

        Returns:
            Optional[dict]: Contract record
        """
        response = self.db.table('contract_generations')\
            .select('*')\
            .eq('contract_id', contract_id)\
            .execute()

        return response.data[0] if response.data else None

    async def update_status(
        self,
        contract_id: str,
        status: ContractStatus,
        reviewed_by: Optional[str] = None,
        review_notes: Optional[str] = None,
        approved_document_url: Optional[str] = None
    ) -> Optional[dict]:
        """
        Update contract status (for review workflow)

        Args:
            contract_id: Contract UUID
            status: New status
            reviewed_by: User ID of reviewer
            review_notes: Review notes/comments
            approved_document_url: Supabase Storage URL for approved PDF

        Returns:
            Optional[dict]: Updated contract record
        """
        update_data = {
            'status': status.value,
            'updated_at': datetime.utcnow().isoformat()
        }

        if reviewed_by:
            update_data['reviewed_by'] = reviewed_by
            update_data['reviewed_at'] = datetime.utcnow().isoformat()

        if review_notes:
            update_data['review_notes'] = review_notes

        if approved_document_url:
            update_data['approved_document_url'] = approved_document_url

        response = self.db.table('contract_generations')\
            .update(update_data)\
            .eq('id', contract_id)\
            .execute()

        return response.data[0] if response.data else None

    async def update_pdf_url(self, contract_id: str, pdf_url: str, storage_path: str) -> Optional[dict]:
        """
        Update contract with PDF URL after generation

        Args:
            contract_id: Contract UUID
            pdf_url: Public URL to PDF
            storage_path: Storage path in Supabase

        Returns:
            Optional[dict]: Updated contract record
        """
        response = self.db.table('contract_generations')\
            .update({
                'pdf_url': pdf_url,
                'pdf_storage_path': storage_path
            })\
            .eq('id', contract_id)\
            .execute()

        return response.data[0] if response.data else None

    async def get_pending_review(self, contract_type: Optional[str] = None) -> List[dict]:
        """
        Get all contracts pending legal review, optionally filtered by contract type

        Args:
            contract_type: Optional filter by contract type ('activos' or 'otrosi')

        Returns:
            List[dict]: Contracts with status 'under_review'
        """
        query = self.db.table('contract_generations')\
            .select('*')\
            .eq('status', 'under_review')

        # Filter by contract type if specified
        if contract_type:
            query = query.eq('contract_type', contract_type)

        response = query.order('generated_at', desc=True).execute()

        return response.data if response.data else []

    async def get_approved_contracts(
        self,
        contract_type: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        client_name: Optional[str] = None,
        client_nit: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        cupo_min: Optional[float] = None,
        cupo_max: Optional[float] = None
    ) -> List[dict]:
        """
        Get all approved contracts with document URLs for Operations team, with optional filters

        Args:
            contract_type: Optional filter by contract type ('activos', 'otrosi', or 'inventario_bodega')
            sort_by: Optional field to sort by (contract_id, contract_type, client_nit, reviewed_at, or JSONB fields)
            sort_order: Optional sort order ('asc' or 'desc', defaults to 'desc')
            client_name: Optional filter by client name (nombre_importador) - partial match, case-insensitive
            client_nit: Optional filter by NIT - partial match
            date_from: Optional filter by approval date >= this date (ISO 8601 format)
            date_to: Optional filter by approval date <= this date (ISO 8601 format)
            cupo_min: Optional filter by credit limit >= this value
            cupo_max: Optional filter by credit limit <= this value

        Returns:
            List[dict]: Approved contracts with document URLs
        """
        query = self.db.table('contract_generations')\
            .select('*')\
            .eq('status', 'approved')

        # Filter by contract type if specified
        if contract_type:
            query = query.eq('contract_type', contract_type)

        # Filter by client name (JSONB field, partial match, case-insensitive)
        if client_name:
            query = query.ilike('data_snapshot->nombre_importador', f'%{client_name}%')

        # Filter by client NIT (partial match)
        if client_nit:
            query = query.ilike('client_nit', f'%{client_nit}%')

        # Filter by date range
        if date_from:
            query = query.gte('reviewed_at', date_from)
        if date_to:
            query = query.lte('reviewed_at', date_to)

        # Filter by credit limit range (JSONB field, numeric comparison)
        if cupo_min is not None:
            # Cast JSONB field to numeric and compare
            query = query.gte('data_snapshot->cupo_plataforma', cupo_min)
        if cupo_max is not None:
            query = query.lte('data_snapshot->cupo_plataforma', cupo_max)

        # Apply sorting
        # Allowed sort fields (whitelist to prevent SQL injection)
        allowed_sort_fields = [
            'contract_id',
            'contract_type',
            'client_nit',
            'reviewed_at',
            'data_snapshot->nombre_importador',
            'data_snapshot->cupo_plataforma'
        ]

        # Determine sort field and order
        if sort_by and sort_by in allowed_sort_fields:
            sort_field = sort_by
        else:
            # Default to reviewed_at if invalid or not provided
            sort_field = 'reviewed_at'

        # Validate sort order
        is_descending = sort_order != 'asc'  # Default to descending

        response = query.order(sort_field, desc=is_descending).execute()

        return response.data if response.data else []

    async def get_history(self, filters: ContractHistoryFilter) -> List[dict]:
        """
        Get contract generation history with filters

        Args:
            filters: Filter parameters

        Returns:
            List[dict]: Filtered contract records
        """
        query = self.db.table('contract_generations').select('*')

        # Filter by status
        if filters.status:
            query = query.eq('status', filters.status.value)

        # Filter by client NIT
        if filters.client_nit:
            query = query.eq('client_nit', filters.client_nit)

        # Filter by date range
        if filters.date_from:
            query = query.gte('generated_at', filters.date_from.isoformat())

        if filters.date_to:
            query = query.lte('generated_at', filters.date_to.isoformat())

        # Apply pagination
        query = query.range(filters.offset, filters.offset + filters.limit - 1)

        # Order by most recent first
        query = query.order('generated_at', desc=True)

        response = query.execute()
        return response.data if response.data else []

    async def get_stats(self) -> Dict[str, int]:
        """
        Get contract generation statistics

        Returns:
            Dict[str, int]: Statistics including counts by status and time periods
        """
        today = date.today()

        # Total generated
        total_response = self.db.table('contract_generations')\
            .select('id', count='exact')\
            .execute()

        # By status
        pending_response = self.db.table('contract_generations')\
            .select('id', count='exact')\
            .eq('status', 'under_review')\
            .execute()

        approved_response = self.db.table('contract_generations')\
            .select('id', count='exact')\
            .eq('status', 'approved')\
            .execute()

        rejected_response = self.db.table('contract_generations')\
            .select('id', count='exact')\
            .eq('status', 'rejected')\
            .execute()

        # Today
        today_response = self.db.table('contract_generations')\
            .select('id', count='exact')\
            .gte('generated_at', today.isoformat())\
            .execute()

        return {
            'total_generated': total_response.count or 0,
            'pending_review': pending_response.count or 0,
            'approved': approved_response.count or 0,
            'rejected': rejected_response.count or 0,
            'generated_today': today_response.count or 0,
        }

    async def get_recent_by_client(self, client_nit: str, limit: int = 5) -> List[dict]:
        """
        Get recent contracts for a specific client

        Args:
            client_nit: Client tax ID
            limit: Number of records to return

        Returns:
            List[dict]: Recent contracts for client
        """
        response = self.db.table('contract_generations')\
            .select('*')\
            .eq('client_nit', client_nit)\
            .order('generated_at', desc=True)\
            .limit(limit)\
            .execute()

        return response.data if response.data else []
