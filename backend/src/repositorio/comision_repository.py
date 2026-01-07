"""
Comision Repository - Database operations for broker commission management
"""
from typing import List, Optional, Dict, Any
from supabase import Client
from decimal import Decimal
import logging

from src.interface.alianzas_dtos import TipoComision

logger = logging.getLogger(__name__)


class ComisionRepository:
    """Repository for broker_comisiones database operations"""

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

    async def create(self, data: Dict[str, Any]) -> dict:
        """
        Create a new commission record

        Args:
            data: Dictionary with commission data

        Returns:
            dict: Created commission record
        """
        # Serialize for database
        commission_data = self._serialize_for_db(data)

        logger.info(f"Creating commission for broker {commission_data.get('broker_id')}")

        response = self.db.table('broker_comisiones')\
            .insert(commission_data)\
            .execute()

        if not response.data:
            raise ValueError("Failed to create commission record")

        return response.data[0]

    async def create_batch(self, comisiones: List[Dict[str, Any]]) -> List[dict]:
        """
        Create multiple commission records in batch

        Args:
            comisiones: List of commission data dictionaries

        Returns:
            List[dict]: List of created commission records
        """
        # Serialize all records
        serialized_data = [self._serialize_for_db(c) for c in comisiones]

        logger.info(f"Creating batch of {len(serialized_data)} commission records")

        response = self.db.table('broker_comisiones')\
            .insert(serialized_data)\
            .execute()

        if not response.data:
            raise ValueError("Failed to create commission records")

        return response.data

    async def get_by_id(self, comision_id: str) -> Optional[dict]:
        """
        Get commission by UUID

        Args:
            comision_id: Commission UUID

        Returns:
            Optional[dict]: Commission record or None
        """
        response = self.db.table('broker_comisiones')\
            .select('*')\
            .eq('id', comision_id)\
            .execute()

        return response.data[0] if response.data else None

    async def get_by_periodo(
        self,
        mes: int,
        anio: int,
        tipo_comision: Optional[str] = None
    ) -> List[dict]:
        """
        Get all commissions for a specific period

        Args:
            mes: Period month (1-12)
            anio: Period year
            tipo_comision: Optional filter by commission type

        Returns:
            List[dict]: List of commission records
        """
        query = self.db.table('broker_comisiones')\
            .select('*')\
            .eq('periodo_mes', mes)\
            .eq('periodo_anio', anio)

        if tipo_comision:
            query = query.eq('tipo_comision', tipo_comision)

        response = query.order('created_at', desc=True).execute()
        return response.data if response.data else []

    async def get_by_broker(
        self,
        broker_id: str,
        mes: Optional[int] = None,
        anio: Optional[int] = None
    ) -> List[dict]:
        """
        Get commissions for a specific broker, optionally filtered by period

        Args:
            broker_id: Broker UUID
            mes: Optional period month (1-12)
            anio: Optional period year

        Returns:
            List[dict]: List of commission records
        """
        query = self.db.table('broker_comisiones')\
            .select('*')\
            .eq('broker_id', broker_id)

        if mes is not None:
            query = query.eq('periodo_mes', mes)
        if anio is not None:
            query = query.eq('periodo_anio', anio)

        response = query.order('periodo_anio', desc=True)\
            .order('periodo_mes', desc=True)\
            .order('created_at', desc=True)\
            .execute()

        return response.data if response.data else []

    async def update_estado(
        self,
        comision_id: str,
        estado: str
    ) -> Optional[dict]:
        """
        Update commission status

        Args:
            comision_id: Commission UUID
            estado: New status value

        Returns:
            Optional[dict]: Updated commission record or None
        """
        logger.info(f"Updating commission {comision_id} to estado: {estado}")

        response = self.db.table('broker_comisiones')\
            .update({'estado': estado})\
            .eq('id', comision_id)\
            .execute()

        return response.data[0] if response.data else None

    async def get_resumen_por_broker(
        self,
        mes: int,
        anio: int
    ) -> List[dict]:
        """
        Get commission summary aggregated by broker for a period.

        Since Supabase doesn't support GROUP BY directly, we fetch all records
        and aggregate in Python.

        Args:
            mes: Period month (1-12)
            anio: Period year

        Returns:
            List[dict]: List of broker summaries with totals
        """
        # Get all commissions for the period with broker info
        response = self.db.table('broker_comisiones')\
            .select('*, brokers(id, nombre)')\
            .eq('periodo_mes', mes)\
            .eq('periodo_anio', anio)\
            .execute()

        if not response.data:
            return []

        # Aggregate by broker
        broker_summaries: Dict[str, Dict[str, Any]] = {}

        for record in response.data:
            broker_id = record['broker_id']
            broker_info = record.get('brokers', {})
            broker_nombre = broker_info.get('nombre', 'Unknown') if broker_info else 'Unknown'

            if broker_id not in broker_summaries:
                broker_summaries[broker_id] = {
                    'broker_id': broker_id,
                    'broker_nombre': broker_nombre,
                    'periodo_mes': mes,
                    'periodo_anio': anio,
                    'total_apertura_usd': Decimal('0'),
                    'total_apertura_mxn': Decimal('0'),
                    'total_operativa_usd': Decimal('0'),
                    'total_operativa_mxn': Decimal('0'),
                    'total_usd': Decimal('0'),
                    'total_mxn': Decimal('0'),
                    'num_comisiones': 0,
                }

            summary = broker_summaries[broker_id]
            monto_usd = Decimal(str(record.get('monto_broker_usd') or 0))
            monto_mxn = Decimal(str(record.get('monto_broker_mxn') or 0))

            if record['tipo_comision'] == TipoComision.APERTURA.value:
                summary['total_apertura_usd'] += monto_usd
                summary['total_apertura_mxn'] += monto_mxn
            else:
                summary['total_operativa_usd'] += monto_usd
                summary['total_operativa_mxn'] += monto_mxn

            summary['total_usd'] += monto_usd
            summary['total_mxn'] += monto_mxn
            summary['num_comisiones'] += 1

        # Convert to list and serialize decimals
        result = []
        for summary in broker_summaries.values():
            serialized = {
                k: float(v) if isinstance(v, Decimal) else v
                for k, v in summary.items()
            }
            result.append(serialized)

        return sorted(result, key=lambda x: x['broker_nombre'])

    async def delete(self, comision_id: str) -> bool:
        """
        Delete a commission record

        Args:
            comision_id: Commission UUID

        Returns:
            bool: True if deleted, False otherwise
        """
        response = self.db.table('broker_comisiones')\
            .delete()\
            .eq('id', comision_id)\
            .execute()

        return bool(response.data)

    async def delete_by_periodo(
        self,
        broker_id: str,
        mes: int,
        anio: int,
        tipo_comision: Optional[str] = None
    ) -> int:
        """
        Delete commission records for a broker in a specific period

        Args:
            broker_id: Broker UUID
            mes: Period month (1-12)
            anio: Period year
            tipo_comision: Optional filter by commission type

        Returns:
            int: Number of records deleted
        """
        query = self.db.table('broker_comisiones')\
            .delete()\
            .eq('broker_id', broker_id)\
            .eq('periodo_mes', mes)\
            .eq('periodo_anio', anio)

        if tipo_comision:
            query = query.eq('tipo_comision', tipo_comision)

        response = query.execute()
        return len(response.data) if response.data else 0
