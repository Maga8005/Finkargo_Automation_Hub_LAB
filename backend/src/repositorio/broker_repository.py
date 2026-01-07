"""
Broker Repository - Database operations for broker management
"""
from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime
from decimal import Decimal
import logging

from src.interface.alianzas_dtos import BrokerCreate, BrokerUpdate, BrokerSearchRequest, EstadoBroker

logger = logging.getLogger(__name__)


class BrokerRepository:
    """Repository for broker database operations"""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client

        Args:
            supabase_client: Supabase client instance
        """
        self.db = supabase_client

    def _serialize_for_db(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize Python types for database storage

        Args:
            data: Dictionary with data to serialize

        Returns:
            Dict with serialized values
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                result[key] = float(value)
            elif hasattr(value, 'isoformat'):
                result[key] = value.isoformat()
            elif hasattr(value, 'value'):  # Enum
                result[key] = value.value
            elif value is not None:
                result[key] = value
        return result

    async def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        active_only: bool = True
    ) -> List[dict]:
        """
        Get all brokers with optional filters

        Args:
            filters: Optional dictionary of filters
            active_only: If True, only return active brokers

        Returns:
            List[dict]: List of broker records
        """
        query = self.db.table('brokers').select('*')

        if active_only:
            query = query.eq('estado', 'activo')

        if filters:
            if filters.get('tipo_broker'):
                query = query.eq('tipo_broker', filters['tipo_broker'])
            if filters.get('estado'):
                query = query.eq('estado', filters['estado'])

        response = query.order('nombre', desc=False).execute()
        return response.data if response.data else []

    async def get_by_id(self, broker_id: str) -> Optional[dict]:
        """
        Get broker by UUID

        Args:
            broker_id: Broker UUID

        Returns:
            Optional[dict]: Broker record or None
        """
        response = self.db.table('brokers')\
            .select('*')\
            .eq('id', broker_id)\
            .execute()

        return response.data[0] if response.data else None

    async def create(self, data: BrokerCreate, user_id: str) -> dict:
        """
        Create a new broker record

        Args:
            data: BrokerCreate DTO with broker data
            user_id: UUID of the user creating the broker

        Returns:
            dict: Created broker record
        """
        # Convert Pydantic model to dict, excluding None values
        broker_data = data.model_dump(exclude_none=True, exclude_unset=True)

        # Serialize for database
        broker_data = self._serialize_for_db(broker_data)

        # Add audit fields
        broker_data['created_by'] = user_id
        broker_data['created_at'] = datetime.utcnow().isoformat()
        broker_data['updated_at'] = datetime.utcnow().isoformat()

        logger.info(f"Creating broker with data: {broker_data}")

        response = self.db.table('brokers')\
            .insert(broker_data)\
            .execute()

        if not response.data:
            raise ValueError("Failed to create broker")

        return response.data[0]

    async def update(self, broker_id: str, data: BrokerUpdate) -> Optional[dict]:
        """
        Update an existing broker record

        Args:
            broker_id: Broker UUID
            data: BrokerUpdate DTO with fields to update

        Returns:
            Optional[dict]: Updated broker record or None
        """
        # Convert Pydantic model to dict, excluding None and unset values
        update_data = data.model_dump(exclude_none=True, exclude_unset=True)

        if not update_data:
            # No fields to update, return current record
            return await self.get_by_id(broker_id)

        # Serialize for database
        update_data = self._serialize_for_db(update_data)

        # Add updated_at timestamp
        update_data['updated_at'] = datetime.utcnow().isoformat()

        logger.info(f"Updating broker {broker_id} with data: {update_data}")

        response = self.db.table('brokers')\
            .update(update_data)\
            .eq('id', broker_id)\
            .execute()

        return response.data[0] if response.data else None

    async def delete(self, broker_id: str) -> bool:
        """
        Soft delete a broker by setting estado to 'inactivo'

        Args:
            broker_id: Broker UUID

        Returns:
            bool: True if deleted, False otherwise
        """
        response = self.db.table('brokers')\
            .update({
                'estado': EstadoBroker.INACTIVO.value,
                'updated_at': datetime.utcnow().isoformat()
            })\
            .eq('id', broker_id)\
            .execute()

        return bool(response.data)

    async def search(self, params: BrokerSearchRequest) -> List[dict]:
        """
        Search brokers by various criteria

        Args:
            params: BrokerSearchRequest with search parameters

        Returns:
            List[dict]: List of matching broker records
        """
        query = self.db.table('brokers').select('*')

        # Filter by active status
        if params.active_only:
            query = query.eq('estado', 'activo')
        elif params.estado:
            query = query.eq('estado', params.estado.value)

        # Filter by tipo_broker
        if params.tipo_broker:
            query = query.eq('tipo_broker', params.tipo_broker.value)

        # Search by nombre (partial match, case-insensitive)
        if params.nombre:
            query = query.ilike('nombre', f'%{params.nombre}%')

        # Search by RFC (partial match, case-insensitive)
        if params.rfc:
            query = query.ilike('rfc', f'%{params.rfc}%')

        response = query.order('nombre', desc=False).execute()
        return response.data if response.data else []

    async def list_by_master_broker(self, master_broker_id: str) -> List[dict]:
        """
        Get all sub-brokers under a master broker

        Args:
            master_broker_id: UUID of the master broker

        Returns:
            List[dict]: List of sub-broker records
        """
        response = self.db.table('brokers')\
            .select('*')\
            .eq('master_broker_id', master_broker_id)\
            .order('nombre', desc=False)\
            .execute()

        return response.data if response.data else []

    async def get_master_brokers(self) -> List[dict]:
        """
        Get all brokers of type master_broker (for dropdown selection)

        Returns:
            List[dict]: List of master broker records
        """
        response = self.db.table('brokers')\
            .select('id, nombre, estado')\
            .eq('tipo_broker', 'master_broker')\
            .eq('estado', 'activo')\
            .order('nombre', desc=False)\
            .execute()

        return response.data if response.data else []

    async def check_nombre_exists(
        self,
        nombre: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """
        Check if a broker with the given name already exists

        Args:
            nombre: Broker name to check
            exclude_id: Optional broker ID to exclude from check (for updates)

        Returns:
            bool: True if name exists, False otherwise
        """
        query = self.db.table('brokers')\
            .select('id')\
            .eq('nombre', nombre)

        if exclude_id:
            query = query.neq('id', exclude_id)

        response = query.execute()
        return bool(response.data)
