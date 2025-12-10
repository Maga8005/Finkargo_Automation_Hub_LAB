"""
Broker Service - Business logic for broker management
"""
from typing import List, Optional
import logging

from src.repositorio.broker_repository import BrokerRepository
from src.interface.alianzas_dtos import (
    BrokerCreate,
    BrokerUpdate,
    BrokerSearchRequest,
    BrokerResponse,
    BrokerWithSubBrokers,
    TipoBroker,
    EstadoBroker,
)

logger = logging.getLogger(__name__)


class BrokerService:
    """Service layer for broker business logic"""

    def __init__(self, broker_repo: BrokerRepository):
        """
        Initialize service with repository

        Args:
            broker_repo: BrokerRepository instance
        """
        self.repo = broker_repo

    def _to_response(self, broker_data: dict) -> BrokerResponse:
        """
        Convert database dict to BrokerResponse DTO

        Args:
            broker_data: Raw database record

        Returns:
            BrokerResponse: Validated response DTO
        """
        return BrokerResponse(
            id=broker_data['id'],
            nombre=broker_data['nombre'],
            tipo_broker=broker_data['tipo_broker'],
            master_broker_id=broker_data.get('master_broker_id'),
            porcentaje_apertura=float(broker_data['porcentaje_apertura']) if broker_data.get('porcentaje_apertura') else None,
            porcentaje_operativa=float(broker_data['porcentaje_operativa']) if broker_data.get('porcentaje_operativa') else None,
            cuenta_bancaria=broker_data.get('cuenta_bancaria'),
            banco=broker_data.get('banco'),
            rfc=broker_data.get('rfc'),
            fecha_contrato=broker_data.get('fecha_contrato'),
            vigencia_contrato=broker_data.get('vigencia_contrato'),
            estado=broker_data['estado'],
            link_expediente=broker_data.get('link_expediente'),
            notas=broker_data.get('notas'),
            created_at=broker_data['created_at'],
            updated_at=broker_data['updated_at'],
            created_by=broker_data.get('created_by'),
        )

    async def create_broker(
        self,
        data: BrokerCreate,
        user_id: str
    ) -> BrokerResponse:
        """
        Create a new broker with business rule validation

        Args:
            data: BrokerCreate DTO
            user_id: UUID of the user creating the broker

        Returns:
            BrokerResponse: Created broker

        Raises:
            ValueError: If business rules are violated
        """
        # Business rule: Check if nombre already exists
        if await self.repo.check_nombre_exists(data.nombre):
            raise ValueError(f"Ya existe un broker con el nombre '{data.nombre}'")

        # Business rule: master_broker_id validation
        if data.master_broker_id:
            # Verify master_broker_id references a valid master broker
            master = await self.repo.get_by_id(data.master_broker_id)
            if not master:
                raise ValueError(f"Master broker con ID '{data.master_broker_id}' no encontrado")
            if master['tipo_broker'] != TipoBroker.MASTER_BROKER.value:
                raise ValueError(
                    f"El broker referenciado no es un master_broker. "
                    f"Tipo actual: {master['tipo_broker']}"
                )

            # Business rule: Only certain tipos can have a master_broker_id
            allowed_sub_tipos = [
                TipoBroker.INDEPENDIENTE,
                TipoBroker.ALIADO_LOGISTICO,
                TipoBroker.CONSULTORIA,
            ]
            if data.tipo_broker not in allowed_sub_tipos:
                raise ValueError(
                    f"El tipo '{data.tipo_broker.value}' no puede tener un master_broker. "
                    f"Tipos permitidos: {[t.value for t in allowed_sub_tipos]}"
                )

        # Business rule: master_broker type cannot have master_broker_id
        if data.tipo_broker == TipoBroker.MASTER_BROKER and data.master_broker_id:
            raise ValueError("Un master_broker no puede tener otro master_broker asignado")

        logger.info(f"Creating broker: {data.nombre} by user {user_id}")

        broker = await self.repo.create(data, user_id)
        return self._to_response(broker)

    async def update_broker(
        self,
        broker_id: str,
        data: BrokerUpdate
    ) -> BrokerResponse:
        """
        Update an existing broker with validation

        Args:
            broker_id: UUID of the broker to update
            data: BrokerUpdate DTO with fields to update

        Returns:
            BrokerResponse: Updated broker

        Raises:
            ValueError: If broker not found or business rules violated
        """
        # Check broker exists
        existing = await self.repo.get_by_id(broker_id)
        if not existing:
            raise ValueError(f"Broker con ID '{broker_id}' no encontrado")

        # Business rule: Check if new nombre already exists (if changing nombre)
        if data.nombre and data.nombre != existing['nombre']:
            if await self.repo.check_nombre_exists(data.nombre, exclude_id=broker_id):
                raise ValueError(f"Ya existe un broker con el nombre '{data.nombre}'")

        # Determine the final tipo_broker
        new_tipo = data.tipo_broker.value if data.tipo_broker else existing['tipo_broker']

        # Business rule: master_broker_id validation
        new_master_id = data.master_broker_id if data.master_broker_id is not None else existing.get('master_broker_id')
        if new_master_id:
            master = await self.repo.get_by_id(new_master_id)
            if not master:
                raise ValueError(f"Master broker con ID '{new_master_id}' no encontrado")
            if master['tipo_broker'] != TipoBroker.MASTER_BROKER.value:
                raise ValueError(
                    f"El broker referenciado no es un master_broker. "
                    f"Tipo actual: {master['tipo_broker']}"
                )

            # Business rule: Only certain tipos can have a master_broker_id
            allowed_sub_tipos = ['independiente', 'aliado_logistico', 'consultoria']
            if new_tipo not in allowed_sub_tipos:
                raise ValueError(
                    f"El tipo '{new_tipo}' no puede tener un master_broker. "
                    f"Tipos permitidos: {allowed_sub_tipos}"
                )

        # Business rule: master_broker type cannot have master_broker_id
        if new_tipo == 'master_broker' and new_master_id:
            raise ValueError("Un master_broker no puede tener otro master_broker asignado")

        logger.info(f"Updating broker {broker_id}")

        broker = await self.repo.update(broker_id, data)
        if not broker:
            raise ValueError(f"Error al actualizar broker '{broker_id}'")

        return self._to_response(broker)

    async def get_broker(self, broker_id: str) -> BrokerResponse:
        """
        Get a broker by ID

        Args:
            broker_id: UUID of the broker

        Returns:
            BrokerResponse: Broker data

        Raises:
            ValueError: If broker not found
        """
        broker = await self.repo.get_by_id(broker_id)
        if not broker:
            raise ValueError(f"Broker con ID '{broker_id}' no encontrado")

        return self._to_response(broker)

    async def delete_broker(self, broker_id: str) -> bool:
        """
        Soft delete a broker (set estado to inactivo)

        Args:
            broker_id: UUID of the broker to delete

        Returns:
            bool: True if deleted

        Raises:
            ValueError: If broker not found
        """
        # Check broker exists
        existing = await self.repo.get_by_id(broker_id)
        if not existing:
            raise ValueError(f"Broker con ID '{broker_id}' no encontrado")

        logger.info(f"Soft deleting broker {broker_id}")

        return await self.repo.delete(broker_id)

    async def search_brokers(
        self,
        params: BrokerSearchRequest
    ) -> List[BrokerResponse]:
        """
        Search brokers by various criteria

        Args:
            params: BrokerSearchRequest with search parameters

        Returns:
            List[BrokerResponse]: Matching brokers
        """
        brokers = await self.repo.search(params)
        return [self._to_response(b) for b in brokers]

    async def list_brokers(
        self,
        active_only: bool = True,
        tipo_broker: Optional[str] = None,
        estado: Optional[str] = None
    ) -> List[BrokerResponse]:
        """
        List all brokers with optional filters

        Args:
            active_only: If True, only return active brokers
            tipo_broker: Optional filter by broker type
            estado: Optional filter by status

        Returns:
            List[BrokerResponse]: List of brokers
        """
        filters = {}
        if tipo_broker:
            filters['tipo_broker'] = tipo_broker
        if estado:
            filters['estado'] = estado

        brokers = await self.repo.get_all(filters=filters, active_only=active_only)
        return [self._to_response(b) for b in brokers]

    async def get_broker_with_sub_brokers(
        self,
        broker_id: str
    ) -> BrokerWithSubBrokers:
        """
        Get a broker with its sub-brokers

        Args:
            broker_id: UUID of the broker

        Returns:
            BrokerWithSubBrokers: Broker with sub-brokers list

        Raises:
            ValueError: If broker not found
        """
        broker = await self.repo.get_by_id(broker_id)
        if not broker:
            raise ValueError(f"Broker con ID '{broker_id}' no encontrado")

        sub_brokers_data = await self.repo.list_by_master_broker(broker_id)
        sub_brokers = [self._to_response(sb) for sb in sub_brokers_data]

        broker_response = self._to_response(broker)

        return BrokerWithSubBrokers(
            **broker_response.model_dump(),
            sub_brokers=sub_brokers
        )

    async def get_master_brokers(self) -> List[dict]:
        """
        Get all master brokers (for dropdown selection)

        Returns:
            List[dict]: List of master broker records with id and nombre
        """
        return await self.repo.get_master_brokers()
