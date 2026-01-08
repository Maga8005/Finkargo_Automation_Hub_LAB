"""
Pago Repository - Database operations for broker payment management
"""
from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PagoRepository:
    """Repository for broker_pagos database operations"""

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
        Create a new payment record

        Args:
            data: Dictionary with payment data

        Returns:
            dict: Created payment record
        """
        payment_data = self._serialize_for_db(data)

        logger.info(f"Creating payment for broker {payment_data.get('broker_id')}")

        response = self.db.table('broker_pagos')\
            .insert(payment_data)\
            .execute()

        if not response.data:
            raise ValueError("Failed to create payment record")

        return response.data[0]

    async def create_batch(self, pagos: List[Dict[str, Any]]) -> List[dict]:
        """
        Create multiple payment records in batch

        Args:
            pagos: List of payment data dictionaries

        Returns:
            List[dict]: List of created payment records
        """
        serialized_data = [self._serialize_for_db(p) for p in pagos]

        logger.info(f"Creating batch of {len(serialized_data)} payment records")

        response = self.db.table('broker_pagos')\
            .insert(serialized_data)\
            .execute()

        if not response.data:
            raise ValueError("Failed to create payment records")

        return response.data

    async def get_by_id(self, pago_id: str) -> Optional[dict]:
        """
        Get payment by UUID

        Args:
            pago_id: Payment UUID

        Returns:
            Optional[dict]: Payment record or None
        """
        response = self.db.table('broker_pagos')\
            .select('*, brokers(id, nombre)')\
            .eq('id', pago_id)\
            .execute()

        return response.data[0] if response.data else None

    async def get_by_periodo(
        self,
        mes: int,
        anio: int,
        broker_id: Optional[str] = None
    ) -> List[dict]:
        """
        Get all payments for a specific period

        Args:
            mes: Period month (1-12)
            anio: Period year
            broker_id: Optional filter by broker

        Returns:
            List[dict]: List of payment records
        """
        query = self.db.table('broker_pagos')\
            .select('*, brokers(id, nombre)')\
            .eq('periodo_mes', mes)\
            .eq('periodo_anio', anio)

        if broker_id:
            query = query.eq('broker_id', broker_id)

        response = query.order('created_at', desc=True).execute()
        return response.data if response.data else []

    async def get_by_broker(
        self,
        broker_id: str,
        mes: Optional[int] = None,
        anio: Optional[int] = None
    ) -> List[dict]:
        """
        Get payments for a specific broker, optionally filtered by period

        Args:
            broker_id: Broker UUID
            mes: Optional period month (1-12)
            anio: Optional period year

        Returns:
            List[dict]: List of payment records
        """
        query = self.db.table('broker_pagos')\
            .select('*, brokers(id, nombre)')\
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

    async def get_historial(
        self,
        broker_id: Optional[str] = None,
        estado: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        Get payment history with optional filters

        Args:
            broker_id: Optional filter by broker
            estado: Optional filter by status
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List[dict]: List of payment records
        """
        query = self.db.table('broker_pagos')\
            .select('*, brokers(id, nombre)')

        if broker_id:
            query = query.eq('broker_id', broker_id)
        if estado:
            query = query.eq('estado', estado)

        response = query.order('periodo_anio', desc=True)\
            .order('periodo_mes', desc=True)\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        return response.data if response.data else []

    async def count_historial(
        self,
        broker_id: Optional[str] = None,
        estado: Optional[str] = None
    ) -> int:
        """
        Count payment records with optional filters

        Args:
            broker_id: Optional filter by broker
            estado: Optional filter by status

        Returns:
            int: Count of matching records
        """
        query = self.db.table('broker_pagos')\
            .select('id', count='exact')

        if broker_id:
            query = query.eq('broker_id', broker_id)
        if estado:
            query = query.eq('estado', estado)

        response = query.execute()
        return response.count if response.count else 0

    async def update_estado(
        self,
        pago_id: str,
        estado: str,
        fecha_pago: Optional[date] = None,
        comprobante_url: Optional[str] = None
    ) -> Optional[dict]:
        """
        Update payment status

        Args:
            pago_id: Payment UUID
            estado: New status value
            fecha_pago: Optional payment date (for status 'pagado')
            comprobante_url: Optional payment receipt URL

        Returns:
            Optional[dict]: Updated payment record or None
        """
        logger.info(f"Updating payment {pago_id} to estado: {estado}")

        update_data: Dict[str, Any] = {'estado': estado}

        if fecha_pago:
            update_data['fecha_pago'] = fecha_pago.isoformat()
        if comprobante_url:
            update_data['comprobante_url'] = comprobante_url

        response = self.db.table('broker_pagos')\
            .update(update_data)\
            .eq('id', pago_id)\
            .execute()

        return response.data[0] if response.data else None

    async def exists_for_periodo(
        self,
        broker_id: str,
        mes: int,
        anio: int
    ) -> bool:
        """
        Check if a payment record exists for a broker in a specific period

        Args:
            broker_id: Broker UUID
            mes: Period month (1-12)
            anio: Period year

        Returns:
            bool: True if payment exists, False otherwise
        """
        response = self.db.table('broker_pagos')\
            .select('id')\
            .eq('broker_id', broker_id)\
            .eq('periodo_mes', mes)\
            .eq('periodo_anio', anio)\
            .execute()

        return bool(response.data)

    async def delete(self, pago_id: str) -> bool:
        """
        Delete a payment record

        Args:
            pago_id: Payment UUID

        Returns:
            bool: True if deleted, False otherwise
        """
        response = self.db.table('broker_pagos')\
            .delete()\
            .eq('id', pago_id)\
            .execute()

        return bool(response.data)
