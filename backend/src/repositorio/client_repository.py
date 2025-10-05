"""
Client Repository - Database operations for clients
"""
from typing import List, Optional
from supabase import Client
from src.interface.legal_dtos import ClientCreate, ClientUpdate, ClientSearchRequest
from datetime import datetime


class ClientRepository:
    """Repository for client data operations"""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client

        Args:
            supabase_client: Supabase client instance
        """
        self.db = supabase_client

    async def create(self, client_data: ClientCreate, user_id: str) -> dict:
        """
        Create a new client record

        Args:
            client_data: Client data to create
            user_id: ID of user creating the record (optional)

        Returns:
            dict: Created client record
        """
        data = client_data.model_dump()
        # Only set imported_by if user_id is provided
        if user_id:
            data['imported_by'] = user_id

        response = self.db.table('clients').insert(data).execute()
        return response.data[0] if response.data else None

    async def get_by_nit(self, nit: str) -> Optional[dict]:
        """
        Get client by NIT

        Args:
            nit: Client tax ID

        Returns:
            Optional[dict]: Client record or None
        """
        response = self.db.table('clients')\
            .select('*')\
            .eq('nit', nit)\
            .eq('is_active', True)\
            .execute()

        return response.data[0] if response.data else None

    async def get_by_id(self, client_id: str) -> Optional[dict]:
        """
        Get client by ID

        Args:
            client_id: Client UUID

        Returns:
            Optional[dict]: Client record or None
        """
        response = self.db.table('clients')\
            .select('*')\
            .eq('id', client_id)\
            .execute()

        return response.data[0] if response.data else None

    async def search(self, search_params: ClientSearchRequest) -> List[dict]:
        """
        Search clients by various criteria

        Args:
            search_params: Search parameters

        Returns:
            List[dict]: List of matching clients
        """
        query = self.db.table('clients').select('*')

        # Filter by active status
        if search_params.is_active is not None:
            query = query.eq('is_active', search_params.is_active)

        # Search by NIT
        if search_params.nit:
            query = query.ilike('nit', f'%{search_params.nit}%')

        # Search by name
        if search_params.nombre:
            query = query.ilike('nombre_importador', f'%{search_params.nombre}%')

        # General query search (NIT or name)
        if search_params.query:
            # Use OR condition for query
            query = query.or_(
                f'nit.ilike.%{search_params.query}%,'
                f'nombre_importador.ilike.%{search_params.query}%'
            )

        # Order by name
        query = query.order('nombre_importador')

        response = query.execute()
        return response.data if response.data else []

    async def update(self, client_id: str, client_data: ClientUpdate) -> Optional[dict]:
        """
        Update client record

        Args:
            client_id: Client UUID
            client_data: Updated client data

        Returns:
            Optional[dict]: Updated client record
        """
        data = client_data.model_dump(exclude_unset=True)

        if not data:
            return await self.get_by_id(client_id)

        response = self.db.table('clients')\
            .update(data)\
            .eq('id', client_id)\
            .execute()

        return response.data[0] if response.data else None

    async def bulk_upsert(self, clients: List[dict], user_id: str) -> dict:
        """
        Bulk insert or update clients from CSV import

        Args:
            clients: List of client data dictionaries
            user_id: ID of user importing data

        Returns:
            dict: Import results with counts
        """
        successful = 0
        failed = 0
        errors = []

        for client in clients:
            try:
                # Only set imported_by if user_id is provided
                if user_id:
                    client['imported_by'] = user_id
                # Otherwise, don't include the field at all to avoid NULL constraint issues

                # Try to upsert (insert or update on conflict)
                response = self.db.table('clients')\
                    .upsert(client, on_conflict='nit')\
                    .execute()

                if response.data:
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Failed to import NIT {client.get('nit', 'unknown')}")

            except Exception as e:
                failed += 1
                error_msg = str(e)
                # Extract just the relevant part of the error
                if 'violates foreign key constraint' in error_msg:
                    errors.append(f"Error importing NIT {client.get('nit', 'unknown')}: Authentication required")
                else:
                    errors.append(f"Error importing NIT {client.get('nit', 'unknown')}: {error_msg}")

        return {
            'total': len(clients),
            'successful': successful,
            'failed': failed,
            'errors': errors
        }

    async def list_all(self, active_only: bool = True) -> List[dict]:
        """
        List all clients

        Args:
            active_only: If True, only return active clients

        Returns:
            List[dict]: List of clients
        """
        query = self.db.table('clients').select('*')

        if active_only:
            query = query.eq('is_active', True)

        query = query.order('nombre_importador')

        response = query.execute()
        return response.data if response.data else []
