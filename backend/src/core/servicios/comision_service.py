"""
Comision Service - Business logic for broker commission calculations

This service implements:
1. Apertura (opening) commission calculations based on credit lines and client payments
2. Operativa (operational) commission calculations based on monthly disbursements
3. USD to MXN conversion using Banxico exchange rates
4. Business rule validation and persistence
"""
from typing import List, Optional, Dict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import logging

from src.repositorio.broker_repository import BrokerRepository
from src.repositorio.comision_repository import ComisionRepository
from src.repositorio.pago_repository import PagoRepository
from src.core.servicios.banxico_service import BanxicoService
from src.interface.alianzas_dtos import (
    ComisionInput,
    ComisionCalculada,
    ComisionBatchInput,
    ComisionBatchResponse,
    ComisionListResponse,
    ComisionResumenBroker,
    ComisionAprobacionResponse,
    TipoComision,
    EstadoComision,
    EstadoPago,
)

logger = logging.getLogger(__name__)

# Precision for currency calculations (2 decimal places)
CURRENCY_PRECISION = Decimal('0.01')


class ComisionService:
    """Service layer for broker commission business logic"""

    # Minimum client payment percentage required for apertura commissions
    MIN_CLIENTE_PAGO_PCT = Decimal('50')

    def __init__(
        self,
        broker_repo: BrokerRepository,
        comision_repo: ComisionRepository,
        banxico_service: BanxicoService,
        pago_repo: Optional[PagoRepository] = None
    ):
        """
        Initialize service with required dependencies

        Args:
            broker_repo: BrokerRepository instance for broker data access
            comision_repo: ComisionRepository instance for commission data access
            banxico_service: BanxicoService instance for exchange rate lookups
            pago_repo: PagoRepository instance for payment data access (optional)
        """
        self.broker_repo = broker_repo
        self.comision_repo = comision_repo
        self.banxico = banxico_service
        self.pago_repo = pago_repo

    async def calcular_comision_apertura(
        self,
        broker_id: str,
        linea_credito: Decimal,
        porcentaje_comision_cliente: Decimal,
        cliente_pago_pct: Decimal,
        fecha_tipo_cambio: Optional[date] = None,
        cliente_nombre: Optional[str] = None,
        cliente_nit: Optional[str] = None,
        periodo_mes: Optional[int] = None,
        periodo_anio: Optional[int] = None,
        notas: Optional[str] = None,
    ) -> ComisionCalculada:
        """
        Calculate apertura (opening) commission for a broker.

        Business Rules:
        1. Client must have paid at least 50% (cliente_pago_pct >= 50)
        2. Broker commission = monto_comision_cliente * porcentaje_broker / 100 * cliente_pago_pct / 100
        3. Convert USD to MXN using Banxico exchange rate

        Formula:
            monto_comision_cliente = linea_credito * (porcentaje_comision_cliente / 100)
            monto_broker_usd = monto_comision_cliente * (porcentaje_broker / 100) * (cliente_pago_pct / 100)
            monto_broker_mxn = monto_broker_usd * tipo_cambio

        Args:
            broker_id: UUID of the broker
            linea_credito: Credit line amount in USD
            porcentaje_comision_cliente: Client commission percentage (0-100)
            cliente_pago_pct: Percentage the client has paid (0-100)
            fecha_tipo_cambio: Date to use for exchange rate (defaults to today)
            cliente_nombre: Optional client company name
            cliente_nit: Optional client tax ID
            periodo_mes: Period month (defaults to current month)
            periodo_anio: Period year (defaults to current year)
            notas: Optional notes

        Returns:
            ComisionCalculada: Calculated commission details

        Raises:
            ValueError: If broker not found or business rules violated
        """
        # Validate minimum client payment
        if cliente_pago_pct < self.MIN_CLIENTE_PAGO_PCT:
            raise ValueError(
                f"El cliente debe haber pagado al menos {self.MIN_CLIENTE_PAGO_PCT}% "
                f"para calcular comisión de apertura. Porcentaje actual: {cliente_pago_pct}%"
            )

        # Get broker data
        broker = await self.broker_repo.get_by_id(broker_id)
        if not broker:
            raise ValueError(f"Broker con ID '{broker_id}' no encontrado")

        # Get broker percentage
        porcentaje_broker = Decimal(str(broker.get('porcentaje_apertura') or 0))
        if porcentaje_broker <= 0:
            raise ValueError(
                f"El broker '{broker['nombre']}' no tiene configurado porcentaje de apertura"
            )

        # Calculate commission
        monto_comision_cliente = linea_credito * (porcentaje_comision_cliente / Decimal('100'))
        monto_broker_usd = (
            monto_comision_cliente
            * (porcentaje_broker / Decimal('100'))
            * (cliente_pago_pct / Decimal('100'))
        )

        # Round to 2 decimal places
        monto_comision_cliente = monto_comision_cliente.quantize(CURRENCY_PRECISION, ROUND_HALF_UP)
        monto_broker_usd = monto_broker_usd.quantize(CURRENCY_PRECISION, ROUND_HALF_UP)

        # Get exchange rate
        fecha_tc = fecha_tipo_cambio or date.today()
        try:
            tipo_cambio = await self.banxico.get_tipo_cambio(fecha_tc)
        except ValueError:
            # If specific date not available, get most recent rate
            tipo_cambio, fecha_tc = await self.banxico.get_tipo_cambio_actual()

        # Convert to MXN
        monto_broker_mxn = monto_broker_usd * tipo_cambio
        monto_broker_mxn = monto_broker_mxn.quantize(CURRENCY_PRECISION, ROUND_HALF_UP)

        # Determine period
        today = date.today()
        mes = periodo_mes or today.month
        anio = periodo_anio or today.year

        logger.info(
            f"Calculated apertura commission for broker {broker['nombre']}: "
            f"${monto_broker_usd} USD = ${monto_broker_mxn} MXN (TC: {tipo_cambio})"
        )

        return ComisionCalculada(
            broker_id=broker_id,
            broker_nombre=broker['nombre'],
            periodo_mes=mes,
            periodo_anio=anio,
            cliente_nombre=cliente_nombre,
            cliente_nit=cliente_nit,
            tipo_comision=TipoComision.APERTURA,
            linea_credito=linea_credito,
            porcentaje_comision_cliente=porcentaje_comision_cliente,
            monto_comision_cliente=monto_comision_cliente,
            cliente_pago_pct=cliente_pago_pct,
            porcentaje_broker=porcentaje_broker,
            monto_broker_usd=monto_broker_usd,
            tipo_cambio=tipo_cambio,
            monto_broker_mxn=monto_broker_mxn,
            estado=EstadoComision.CALCULADO,
            notas=notas,
        )

    async def calcular_comision_operativa(
        self,
        broker_id: str,
        operaciones_mes: Decimal,
        fecha_tipo_cambio: Optional[date] = None,
        cliente_nombre: Optional[str] = None,
        cliente_nit: Optional[str] = None,
        periodo_mes: Optional[int] = None,
        periodo_anio: Optional[int] = None,
        notas: Optional[str] = None,
    ) -> ComisionCalculada:
        """
        Calculate operativa (operational) commission for a broker.

        Formula:
            monto_broker_usd = operaciones_mes * (porcentaje_operativa / 100)
            monto_broker_mxn = monto_broker_usd * tipo_cambio

        Args:
            broker_id: UUID of the broker
            operaciones_mes: Monthly operation disbursements in USD
            fecha_tipo_cambio: Date to use for exchange rate (defaults to today)
            cliente_nombre: Optional client company name
            cliente_nit: Optional client tax ID
            periodo_mes: Period month (defaults to current month)
            periodo_anio: Period year (defaults to current year)
            notas: Optional notes

        Returns:
            ComisionCalculada: Calculated commission details

        Raises:
            ValueError: If broker not found or has no operativa percentage
        """
        # Get broker data
        broker = await self.broker_repo.get_by_id(broker_id)
        if not broker:
            raise ValueError(f"Broker con ID '{broker_id}' no encontrado")

        # Get broker percentage
        porcentaje_broker = Decimal(str(broker.get('porcentaje_operativa') or 0))
        if porcentaje_broker <= 0:
            raise ValueError(
                f"El broker '{broker['nombre']}' no tiene configurado porcentaje operativo"
            )

        # Calculate commission
        monto_broker_usd = operaciones_mes * (porcentaje_broker / Decimal('100'))
        monto_broker_usd = monto_broker_usd.quantize(CURRENCY_PRECISION, ROUND_HALF_UP)

        # Get exchange rate
        fecha_tc = fecha_tipo_cambio or date.today()
        try:
            tipo_cambio = await self.banxico.get_tipo_cambio(fecha_tc)
        except ValueError:
            # If specific date not available, get most recent rate
            tipo_cambio, fecha_tc = await self.banxico.get_tipo_cambio_actual()

        # Convert to MXN
        monto_broker_mxn = monto_broker_usd * tipo_cambio
        monto_broker_mxn = monto_broker_mxn.quantize(CURRENCY_PRECISION, ROUND_HALF_UP)

        # Determine period
        today = date.today()
        mes = periodo_mes or today.month
        anio = periodo_anio or today.year

        logger.info(
            f"Calculated operativa commission for broker {broker['nombre']}: "
            f"${monto_broker_usd} USD = ${monto_broker_mxn} MXN (TC: {tipo_cambio})"
        )

        return ComisionCalculada(
            broker_id=broker_id,
            broker_nombre=broker['nombre'],
            periodo_mes=mes,
            periodo_anio=anio,
            cliente_nombre=cliente_nombre,
            cliente_nit=cliente_nit,
            tipo_comision=TipoComision.OPERATIVA,
            operaciones_mes=operaciones_mes,
            porcentaje_broker=porcentaje_broker,
            monto_broker_usd=monto_broker_usd,
            tipo_cambio=tipo_cambio,
            monto_broker_mxn=monto_broker_mxn,
            estado=EstadoComision.CALCULADO,
            notas=notas,
        )

    async def calcular_comision(self, input_data: ComisionInput) -> ComisionCalculada:
        """
        Calculate commission based on input type.

        Delegates to calcular_comision_apertura or calcular_comision_operativa
        based on tipo_comision.

        Args:
            input_data: ComisionInput with calculation parameters

        Returns:
            ComisionCalculada: Calculated commission details

        Raises:
            ValueError: If required fields missing or validation fails
        """
        if input_data.tipo_comision == TipoComision.APERTURA:
            # Validate required fields for apertura
            if input_data.linea_credito is None:
                raise ValueError("linea_credito es requerido para comisión de apertura")
            if input_data.porcentaje_comision_cliente is None:
                raise ValueError("porcentaje_comision_cliente es requerido para comisión de apertura")
            if input_data.cliente_pago_pct is None:
                raise ValueError("cliente_pago_pct es requerido para comisión de apertura")

            return await self.calcular_comision_apertura(
                broker_id=input_data.broker_id,
                linea_credito=input_data.linea_credito,
                porcentaje_comision_cliente=input_data.porcentaje_comision_cliente,
                cliente_pago_pct=input_data.cliente_pago_pct,
                fecha_tipo_cambio=input_data.fecha_tipo_cambio,
                cliente_nombre=input_data.cliente_nombre,
                cliente_nit=input_data.cliente_nit,
                periodo_mes=input_data.periodo_mes,
                periodo_anio=input_data.periodo_anio,
                notas=input_data.notas,
            )
        else:  # OPERATIVA
            # Validate required fields for operativa
            if input_data.operaciones_mes is None:
                raise ValueError("operaciones_mes es requerido para comisión operativa")

            return await self.calcular_comision_operativa(
                broker_id=input_data.broker_id,
                operaciones_mes=input_data.operaciones_mes,
                fecha_tipo_cambio=input_data.fecha_tipo_cambio,
                cliente_nombre=input_data.cliente_nombre,
                cliente_nit=input_data.cliente_nit,
                periodo_mes=input_data.periodo_mes,
                periodo_anio=input_data.periodo_anio,
                notas=input_data.notas,
            )

    async def calcular_lote(
        self,
        batch_input: ComisionBatchInput,
        user_id: Optional[str] = None
    ) -> ComisionBatchResponse:
        """
        Calculate commissions for multiple inputs in batch.

        Args:
            batch_input: ComisionBatchInput with list of inputs and save flag
            user_id: Optional user ID for audit trail (required if guardar=True)

        Returns:
            ComisionBatchResponse: List of calculated commissions with totals
        """
        comisiones: List[ComisionCalculada] = []
        total_usd = Decimal('0')
        total_mxn = Decimal('0')

        for input_data in batch_input.comisiones:
            comision = await self.calcular_comision(input_data)
            comisiones.append(comision)
            total_usd += comision.monto_broker_usd
            total_mxn += comision.monto_broker_mxn

        # Save to database if requested
        guardadas = False
        if batch_input.guardar:
            if not user_id:
                raise ValueError("user_id es requerido para guardar comisiones")

            saved_comisiones = await self.guardar_comisiones(comisiones, user_id)
            comisiones = saved_comisiones
            guardadas = True

        return ComisionBatchResponse(
            comisiones=comisiones,
            total_usd=total_usd.quantize(CURRENCY_PRECISION, ROUND_HALF_UP),
            total_mxn=total_mxn.quantize(CURRENCY_PRECISION, ROUND_HALF_UP),
            guardadas=guardadas,
        )

    async def guardar_comision(
        self,
        comision: ComisionCalculada,
        user_id: str
    ) -> ComisionCalculada:
        """
        Save a single calculated commission to the database.

        Args:
            comision: Calculated commission to save
            user_id: UUID of the user creating the record

        Returns:
            ComisionCalculada: Saved commission with id and audit fields
        """
        # Prepare data for database
        data = {
            'broker_id': comision.broker_id,
            'periodo_mes': comision.periodo_mes,
            'periodo_anio': comision.periodo_anio,
            'cliente_nombre': comision.cliente_nombre,
            'cliente_nit': comision.cliente_nit,
            'tipo_comision': comision.tipo_comision.value,
            'linea_credito': comision.linea_credito,
            'porcentaje_comision_cliente': comision.porcentaje_comision_cliente,
            'monto_comision_cliente': comision.monto_comision_cliente,
            'porcentaje_broker': comision.porcentaje_broker,
            'monto_broker_usd': comision.monto_broker_usd,
            'operaciones_mes': comision.operaciones_mes,
            'tipo_cambio': comision.tipo_cambio,
            'monto_broker_mxn': comision.monto_broker_mxn,
            'cliente_pago_pct': comision.cliente_pago_pct,
            'estado': comision.estado.value,
            'notas': comision.notas,
            'created_by': user_id,
        }

        saved = await self.comision_repo.create(data)

        # Return updated model with database fields
        return ComisionCalculada(
            **comision.model_dump(exclude={'id', 'created_at', 'created_by'}),
            id=saved['id'],
            created_at=saved['created_at'],
            created_by=saved.get('created_by'),
        )

    async def guardar_comisiones(
        self,
        comisiones: List[ComisionCalculada],
        user_id: str
    ) -> List[ComisionCalculada]:
        """
        Save multiple calculated commissions to the database.

        Args:
            comisiones: List of calculated commissions to save
            user_id: UUID of the user creating the records

        Returns:
            List[ComisionCalculada]: Saved commissions with ids and audit fields
        """
        if not comisiones:
            return []

        # Prepare data for batch insert
        batch_data = []
        for comision in comisiones:
            data = {
                'broker_id': comision.broker_id,
                'periodo_mes': comision.periodo_mes,
                'periodo_anio': comision.periodo_anio,
                'cliente_nombre': comision.cliente_nombre,
                'cliente_nit': comision.cliente_nit,
                'tipo_comision': comision.tipo_comision.value,
                'linea_credito': comision.linea_credito,
                'porcentaje_comision_cliente': comision.porcentaje_comision_cliente,
                'monto_comision_cliente': comision.monto_comision_cliente,
                'porcentaje_broker': comision.porcentaje_broker,
                'monto_broker_usd': comision.monto_broker_usd,
                'operaciones_mes': comision.operaciones_mes,
                'tipo_cambio': comision.tipo_cambio,
                'monto_broker_mxn': comision.monto_broker_mxn,
                'cliente_pago_pct': comision.cliente_pago_pct,
                'estado': comision.estado.value,
                'notas': comision.notas,
                'created_by': user_id,
            }
            batch_data.append(data)

        saved_records = await self.comision_repo.create_batch(batch_data)

        # Map saved records back to models
        result = []
        for comision, saved in zip(comisiones, saved_records):
            result.append(ComisionCalculada(
                **comision.model_dump(exclude={'id', 'created_at', 'created_by'}),
                id=saved['id'],
                created_at=saved['created_at'],
                created_by=saved.get('created_by'),
            ))

        logger.info(f"Saved {len(result)} commission records to database")
        return result

    async def listar_por_periodo(
        self,
        mes: int,
        anio: int,
        tipo_comision: Optional[TipoComision] = None
    ) -> ComisionListResponse:
        """
        List all commissions for a specific period.

        Args:
            mes: Period month (1-12)
            anio: Period year
            tipo_comision: Optional filter by commission type

        Returns:
            ComisionListResponse: List of commissions with total count
        """
        tipo_str = tipo_comision.value if tipo_comision else None
        records = await self.comision_repo.get_by_periodo(mes, anio, tipo_str)

        comisiones = [self._record_to_model(r) for r in records]

        return ComisionListResponse(
            comisiones=comisiones,
            total=len(comisiones),
            periodo_mes=mes,
            periodo_anio=anio,
        )

    async def listar_por_broker(
        self,
        broker_id: str,
        mes: Optional[int] = None,
        anio: Optional[int] = None
    ) -> List[ComisionCalculada]:
        """
        List commissions for a specific broker.

        Args:
            broker_id: Broker UUID
            mes: Optional period month filter
            anio: Optional period year filter

        Returns:
            List[ComisionCalculada]: List of broker's commissions
        """
        records = await self.comision_repo.get_by_broker(broker_id, mes, anio)
        return [self._record_to_model(r) for r in records]

    async def obtener_resumen_por_broker(
        self,
        mes: int,
        anio: int
    ) -> List[ComisionResumenBroker]:
        """
        Get commission summary aggregated by broker for a period.

        Args:
            mes: Period month (1-12)
            anio: Period year

        Returns:
            List[ComisionResumenBroker]: List of broker summaries
        """
        summaries = await self.comision_repo.get_resumen_por_broker(mes, anio)

        return [
            ComisionResumenBroker(
                broker_id=s['broker_id'],
                broker_nombre=s['broker_nombre'],
                periodo_mes=s['periodo_mes'],
                periodo_anio=s['periodo_anio'],
                total_apertura_usd=Decimal(str(s['total_apertura_usd'])),
                total_apertura_mxn=Decimal(str(s['total_apertura_mxn'])),
                total_operativa_usd=Decimal(str(s['total_operativa_usd'])),
                total_operativa_mxn=Decimal(str(s['total_operativa_mxn'])),
                total_usd=Decimal(str(s['total_usd'])),
                total_mxn=Decimal(str(s['total_mxn'])),
                num_comisiones=s['num_comisiones'],
            )
            for s in summaries
        ]

    async def actualizar_estado(
        self,
        comision_id: str,
        estado: EstadoComision
    ) -> ComisionCalculada:
        """
        Update commission status.

        Args:
            comision_id: Commission UUID
            estado: New status

        Returns:
            ComisionCalculada: Updated commission

        Raises:
            ValueError: If commission not found
        """
        updated = await self.comision_repo.update_estado(comision_id, estado.value)

        if not updated:
            raise ValueError(f"Comisión con ID '{comision_id}' no encontrada")

        return self._record_to_model(updated)

    def _record_to_model(self, record: dict) -> ComisionCalculada:
        """
        Convert database record to ComisionCalculada model.

        Args:
            record: Database record dictionary

        Returns:
            ComisionCalculada: Model instance
        """
        return ComisionCalculada(
            id=record['id'],
            broker_id=record['broker_id'],
            broker_nombre=None,  # Not included in record, would need join
            periodo_mes=record['periodo_mes'],
            periodo_anio=record['periodo_anio'],
            cliente_nombre=record.get('cliente_nombre'),
            cliente_nit=record.get('cliente_nit'),
            tipo_comision=TipoComision(record['tipo_comision']),
            linea_credito=Decimal(str(record['linea_credito'])) if record.get('linea_credito') else None,
            porcentaje_comision_cliente=Decimal(str(record['porcentaje_comision_cliente'])) if record.get('porcentaje_comision_cliente') else None,
            monto_comision_cliente=Decimal(str(record['monto_comision_cliente'])) if record.get('monto_comision_cliente') else None,
            cliente_pago_pct=Decimal(str(record['cliente_pago_pct'])) if record.get('cliente_pago_pct') else None,
            operaciones_mes=Decimal(str(record['operaciones_mes'])) if record.get('operaciones_mes') else None,
            porcentaje_broker=Decimal(str(record['porcentaje_broker'])),
            monto_broker_usd=Decimal(str(record['monto_broker_usd'])),
            tipo_cambio=Decimal(str(record['tipo_cambio'])),
            monto_broker_mxn=Decimal(str(record['monto_broker_mxn'])),
            estado=EstadoComision(record['estado']),
            notas=record.get('notas'),
            created_at=record.get('created_at'),
            created_by=record.get('created_by'),
        )

    async def aprobar_comisiones_periodo(
        self,
        mes: int,
        anio: int,
        user_id: str
    ) -> ComisionAprobacionResponse:
        """
        Approve all calculated commissions for a period and create payment records.

        Business Logic:
        1. Get all commissions with estado='calculado' for the period
        2. Group commissions by broker
        3. Calculate totals per broker
        4. Create broker_pagos record for each broker
        5. Update commission status to 'aprobado'

        Args:
            mes: Period month (1-12)
            anio: Period year
            user_id: UUID of the user approving

        Returns:
            ComisionAprobacionResponse: Summary of approved commissions and payments

        Raises:
            ValueError: If no pago_repo is configured or no commissions to approve
        """
        if not self.pago_repo:
            raise ValueError("PagoRepository not configured for approval operations")

        # Get all calculated commissions for the period
        records = await self.comision_repo.get_by_periodo(mes, anio, 'calculado')

        if not records:
            return ComisionAprobacionResponse(
                periodo_mes=mes,
                periodo_anio=anio,
                comisiones_aprobadas=0,
                pagos_creados=0,
                total_usd=0,
                total_mxn=0,
                brokers_ids=[],
                message="No hay comisiones calculadas pendientes de aprobación"
            )

        # Group commissions by broker
        broker_groups: Dict[str, List[dict]] = {}
        for record in records:
            broker_id = record['broker_id']
            if broker_id not in broker_groups:
                broker_groups[broker_id] = []
            broker_groups[broker_id].append(record)

        # Create payment records and update commissions
        pagos_data = []
        total_usd = Decimal('0')
        total_mxn = Decimal('0')

        for broker_id, comisiones in broker_groups.items():
            # Check if payment already exists for this broker/period
            existing = await self.pago_repo.exists_for_periodo(broker_id, mes, anio)
            if existing:
                logger.warning(
                    f"Payment record already exists for broker {broker_id} "
                    f"period {mes}/{anio}, skipping"
                )
                continue

            # Calculate broker totals
            broker_usd = sum(Decimal(str(c['monto_broker_usd'])) for c in comisiones)
            broker_mxn = sum(Decimal(str(c['monto_broker_mxn'])) for c in comisiones)

            # Use first commission's exchange rate (all should be same for period)
            tipo_cambio = Decimal(str(comisiones[0]['tipo_cambio']))

            pago_data = {
                'broker_id': broker_id,
                'periodo_mes': mes,
                'periodo_anio': anio,
                'total_usd': float(broker_usd),
                'total_mxn': float(broker_mxn),
                'tipo_cambio': float(tipo_cambio),
                'estado': EstadoPago.PENDIENTE.value,
                'approved_by': user_id,
            }
            pagos_data.append(pago_data)

            total_usd += broker_usd
            total_mxn += broker_mxn

        # Create payment records in batch
        if pagos_data:
            await self.pago_repo.create_batch(pagos_data)

        # Update commission statuses to 'aprobado'
        comision_ids = [r['id'] for r in records]
        for comision_id in comision_ids:
            await self.comision_repo.update_estado(comision_id, EstadoComision.APROBADO.value)

        logger.info(
            f"Approved {len(records)} commissions for period {mes}/{anio}, "
            f"created {len(pagos_data)} payment records"
        )

        return ComisionAprobacionResponse(
            periodo_mes=mes,
            periodo_anio=anio,
            comisiones_aprobadas=len(records),
            pagos_creados=len(pagos_data),
            total_usd=float(total_usd),
            total_mxn=float(total_mxn),
            brokers_ids=list(broker_groups.keys()),
            message=f"Se aprobaron {len(records)} comisiones y se crearon {len(pagos_data)} registros de pago"
        )
