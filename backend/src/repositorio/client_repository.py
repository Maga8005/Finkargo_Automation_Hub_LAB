"""
Client Repository - Database operations for clients
"""
from typing import List, Optional
from supabase import Client
from src.interface.legal_dtos import ClientCreate, ClientUpdate, ClientSearchRequest
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
        from decimal import Decimal

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
        clients = response.data if response.data else []

        # Defensive type coercion for cupo_plataforma
        for client in clients:
            if 'cupo_plataforma' in client and client['cupo_plataforma'] is not None:
                cupo = client['cupo_plataforma']
                if not isinstance(cupo, Decimal):
                    # Convert string or float to Decimal
                    try:
                        if isinstance(cupo, (int, float)):
                            client['cupo_plataforma'] = Decimal(str(cupo))
                        elif isinstance(cupo, str):
                            client['cupo_plataforma'] = Decimal(cupo)
                        else:
                            logger.warning(f"Unexpected type for cupo_plataforma in client {client.get('nit')}: {type(cupo)}")
                    except Exception as e:
                        logger.error(f"Error converting cupo_plataforma for client {client.get('nit')}: {e}")

        return clients

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
        try:
            # Add imported_by to all clients
            for client in clients:
                if user_id:
                    client['imported_by'] = user_id

            # Perform bulk upsert in a single operation
            response = self.db.table('clients')\
                .upsert(clients, on_conflict='nit')\
                .execute()

            if response.data:
                successful = len(response.data)
                failed = len(clients) - successful
                errors = []

                if failed > 0:
                    errors.append(f"{failed} records failed to import")

                return {
                    'total': len(clients),
                    'successful': successful,
                    'failed': failed,
                    'errors': errors
                }
            else:
                return {
                    'total': len(clients),
                    'successful': 0,
                    'failed': len(clients),
                    'errors': ['Bulk upsert returned no data']
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Bulk upsert failed: {error_msg}", exc_info=True)

            return {
                'total': len(clients),
                'successful': 0,
                'failed': len(clients),
                'errors': [f"Bulk import failed: {error_msg}"]
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
