"""
Alianzas Service Integration Tests

This test module uses the test fixtures from fixtures/alianzas_test_data.py
to test the commission calculation business logic with realistic data.

These tests complement the unit tests in test_comision_service.py by:
1. Using standardized test fixtures
2. Testing fixture data validation
3. Testing complete calculation workflows
4. Verifying expected results against documented formulas
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from src.core.servicios.comision_service import ComisionService
from src.core.servicios.broker_service import BrokerService
from src.interface.alianzas_dtos import (
    ComisionInput,
    ComisionBatchInput,
    TipoComision,
    EstadoComision,
    BrokerCreate,
    TipoBroker,
    EstadoBroker,
)

# Import test fixtures
from tests.fixtures.alianzas_test_data import (
    SAMPLE_BROKER_MASTER,
    SAMPLE_BROKER_SUB,
    SAMPLE_BROKER_NO_APERTURA,
    SAMPLE_BROKER_NO_OPERATIVA,
    SAMPLE_COMISION_APERTURA,
    SAMPLE_COMISION_APERTURA_PARTIAL_PAYMENT,
    SAMPLE_COMISION_APERTURA_BELOW_MINIMUM,
    SAMPLE_COMISION_APERTURA_LARGE_CREDIT_LINE,
    SAMPLE_COMISION_OPERATIVA,
    SAMPLE_COMISION_OPERATIVA_ZERO,
    SAMPLE_COMISION_OPERATIVA_LARGE,
    SAMPLE_COMISION_BATCH,
    SAMPLE_COMISION_BATCH_EXPECTED_TOTAL_USD,
    SAMPLE_COMISION_BATCH_EXPECTED_TOTAL_MXN,
    SAMPLE_TIPO_CAMBIO,
    EDGE_CASE_ZERO_PORCENTAJE_BROKER,
    get_apertura_commission_inputs,
    get_operativa_commission_inputs,
)


# ==================== Pytest Fixtures ====================

@pytest.fixture
def mock_broker_repo():
    """Create a mock BrokerRepository"""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    repo.check_nombre_exists = AsyncMock(return_value=False)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.search = AsyncMock()
    repo.get_all = AsyncMock()
    return repo


@pytest.fixture
def mock_comision_repo():
    """Create a mock ComisionRepository"""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.create_batch = AsyncMock()
    repo.get_by_periodo = AsyncMock()
    repo.get_by_broker = AsyncMock()
    repo.update_estado = AsyncMock()
    repo.get_resumen_por_broker = AsyncMock()
    return repo


@pytest.fixture
def mock_pago_repo():
    """Create a mock PagoRepository"""
    repo = MagicMock()
    repo.create_batch = AsyncMock()
    repo.exists_for_periodo = AsyncMock(return_value=False)
    return repo


@pytest.fixture
def mock_banxico_service():
    """Create a mock BanxicoService returning standard test exchange rate"""
    service = MagicMock()
    service.get_tipo_cambio = AsyncMock(return_value=SAMPLE_TIPO_CAMBIO)
    service.get_tipo_cambio_actual = AsyncMock(
        return_value=(SAMPLE_TIPO_CAMBIO, date(2025, 1, 10))
    )
    return service


@pytest.fixture
def comision_service(mock_broker_repo, mock_comision_repo, mock_banxico_service, mock_pago_repo):
    """Create ComisionService with all mocked dependencies"""
    return ComisionService(
        mock_broker_repo,
        mock_comision_repo,
        mock_banxico_service,
        mock_pago_repo
    )


@pytest.fixture
def broker_service(mock_broker_repo):
    """Create BrokerService with mocked repository"""
    return BrokerService(mock_broker_repo)


# ==================== Fixture Data Validation Tests ====================

class TestFixtureDataIntegrity:
    """Tests to verify fixture data is correctly structured"""

    def test_sample_broker_master_has_required_fields(self):
        """Verify master broker fixture has all required fields"""
        required_fields = [
            'id', 'nombre', 'tipo_broker', 'porcentaje_apertura',
            'porcentaje_operativa', 'estado'
        ]
        for field in required_fields:
            assert field in SAMPLE_BROKER_MASTER, f"Missing field: {field}"

    def test_sample_broker_percentages_are_decimal(self):
        """Verify broker percentages are Decimal type"""
        assert isinstance(SAMPLE_BROKER_MASTER['porcentaje_apertura'], Decimal)
        assert isinstance(SAMPLE_BROKER_MASTER['porcentaje_operativa'], Decimal)

    def test_sample_comision_apertura_has_expected_results(self):
        """Verify apertura commission fixture includes expected calculation results"""
        assert 'expected_monto_broker_usd' in SAMPLE_COMISION_APERTURA
        assert 'expected_monto_broker_mxn' in SAMPLE_COMISION_APERTURA
        assert isinstance(SAMPLE_COMISION_APERTURA['expected_monto_broker_usd'], Decimal)

    def test_sample_tipo_cambio_is_decimal(self):
        """Verify exchange rate is Decimal type"""
        assert isinstance(SAMPLE_TIPO_CAMBIO, Decimal)
        assert SAMPLE_TIPO_CAMBIO > 0


# ==================== Apertura Commission Tests with Fixtures ====================

class TestAperturaCommissionWithFixtures:
    """Test apertura commission calculations using fixture data"""

    @pytest.mark.asyncio
    async def test_apertura_100_percent_payment(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test apertura calculation with 100% client payment using fixture data"""
        # Setup
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        fixture = SAMPLE_COMISION_APERTURA

        # Execute
        result = await comision_service.calcular_comision_apertura(
            broker_id=fixture['broker_id'],
            linea_credito=fixture['linea_credito'],
            porcentaje_comision_cliente=fixture['porcentaje_comision_cliente'],
            cliente_pago_pct=fixture['cliente_pago_pct'],
            cliente_nombre=fixture['cliente_nombre'],
            cliente_nit=fixture['cliente_nit'],
            periodo_mes=fixture['periodo_mes'],
            periodo_anio=fixture['periodo_anio'],
        )

        # Verify against expected fixture results
        assert result.monto_comision_cliente == fixture['expected_monto_comision_cliente']
        assert result.monto_broker_usd == fixture['expected_monto_broker_usd']
        assert result.monto_broker_mxn == fixture['expected_monto_broker_mxn']
        assert result.tipo_comision == TipoComision.APERTURA
        assert result.estado == EstadoComision.CALCULADO

    @pytest.mark.asyncio
    async def test_apertura_50_percent_payment_boundary(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test apertura calculation with exactly 50% payment (boundary case)"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        fixture = SAMPLE_COMISION_APERTURA_PARTIAL_PAYMENT

        result = await comision_service.calcular_comision_apertura(
            broker_id=fixture['broker_id'],
            linea_credito=fixture['linea_credito'],
            porcentaje_comision_cliente=fixture['porcentaje_comision_cliente'],
            cliente_pago_pct=fixture['cliente_pago_pct'],
        )

        assert result.monto_broker_usd == fixture['expected_monto_broker_usd']
        assert result.monto_broker_mxn == fixture['expected_monto_broker_mxn']

    @pytest.mark.asyncio
    async def test_apertura_below_minimum_payment_fails(self, comision_service):
        """Test that apertura with < 50% payment raises ValueError"""
        fixture = SAMPLE_COMISION_APERTURA_BELOW_MINIMUM

        with pytest.raises(ValueError) as exc_info:
            await comision_service.calcular_comision_apertura(
                broker_id=fixture['broker_id'],
                linea_credito=fixture['linea_credito'],
                porcentaje_comision_cliente=fixture['porcentaje_comision_cliente'],
                cliente_pago_pct=fixture['cliente_pago_pct'],
            )

        assert "50%" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_apertura_large_credit_line(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test apertura with large credit line maintains precision"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        fixture = SAMPLE_COMISION_APERTURA_LARGE_CREDIT_LINE

        result = await comision_service.calcular_comision_apertura(
            broker_id=fixture['broker_id'],
            linea_credito=fixture['linea_credito'],
            porcentaje_comision_cliente=fixture['porcentaje_comision_cliente'],
            cliente_pago_pct=fixture['cliente_pago_pct'],
        )

        assert result.monto_broker_usd == fixture['expected_monto_broker_usd']
        assert result.monto_broker_mxn == fixture['expected_monto_broker_mxn']

    @pytest.mark.asyncio
    async def test_apertura_broker_without_apertura_percentage(
        self, comision_service, mock_broker_repo
    ):
        """Test apertura fails when broker has no apertura percentage configured"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_NO_APERTURA

        with pytest.raises(ValueError) as exc_info:
            await comision_service.calcular_comision_apertura(
                broker_id=SAMPLE_BROKER_NO_APERTURA['id'],
                linea_credito=Decimal('100000'),
                porcentaje_comision_cliente=Decimal('2.5'),
                cliente_pago_pct=Decimal('100'),
            )

        assert "porcentaje de apertura" in str(exc_info.value)


# ==================== Operativa Commission Tests with Fixtures ====================

class TestOperativaCommissionWithFixtures:
    """Test operativa commission calculations using fixture data"""

    @pytest.mark.asyncio
    async def test_operativa_standard_calculation(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test operativa calculation with standard fixture data"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        fixture = SAMPLE_COMISION_OPERATIVA

        result = await comision_service.calcular_comision_operativa(
            broker_id=fixture['broker_id'],
            operaciones_mes=fixture['operaciones_mes'],
            cliente_nombre=fixture['cliente_nombre'],
            cliente_nit=fixture['cliente_nit'],
            periodo_mes=fixture['periodo_mes'],
            periodo_anio=fixture['periodo_anio'],
        )

        assert result.monto_broker_usd == fixture['expected_monto_broker_usd']
        assert result.monto_broker_mxn == fixture['expected_monto_broker_mxn']
        assert result.tipo_comision == TipoComision.OPERATIVA

    @pytest.mark.asyncio
    async def test_operativa_zero_operations(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test operativa with zero operations returns zero commission"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        fixture = SAMPLE_COMISION_OPERATIVA_ZERO

        result = await comision_service.calcular_comision_operativa(
            broker_id=fixture['broker_id'],
            operaciones_mes=fixture['operaciones_mes'],
        )

        assert result.monto_broker_usd == fixture['expected_monto_broker_usd']
        assert result.monto_broker_mxn == fixture['expected_monto_broker_mxn']

    @pytest.mark.asyncio
    async def test_operativa_large_operations(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test operativa with large operations amount"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        fixture = SAMPLE_COMISION_OPERATIVA_LARGE

        result = await comision_service.calcular_comision_operativa(
            broker_id=fixture['broker_id'],
            operaciones_mes=fixture['operaciones_mes'],
        )

        assert result.monto_broker_usd == fixture['expected_monto_broker_usd']
        assert result.monto_broker_mxn == fixture['expected_monto_broker_mxn']

    @pytest.mark.asyncio
    async def test_operativa_broker_without_operativa_percentage(
        self, comision_service, mock_broker_repo
    ):
        """Test operativa fails when broker has no operativa percentage"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_NO_OPERATIVA

        with pytest.raises(ValueError) as exc_info:
            await comision_service.calcular_comision_operativa(
                broker_id=SAMPLE_BROKER_NO_OPERATIVA['id'],
                operaciones_mes=Decimal('500000'),
            )

        assert "porcentaje operativo" in str(exc_info.value)


# ==================== Batch Commission Tests with Fixtures ====================

class TestBatchCommissionWithFixtures:
    """Test batch commission calculations using fixture data"""

    @pytest.mark.asyncio
    async def test_batch_calculation_totals(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test batch calculation with fixture data matches expected totals"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        # Build batch input from fixtures
        comisiones = []
        for item in SAMPLE_COMISION_BATCH:
            if item['tipo_comision'] == 'apertura':
                comisiones.append(ComisionInput(
                    broker_id=item['broker_id'],
                    tipo_comision=TipoComision.APERTURA,
                    cliente_nombre=item['cliente_nombre'],
                    linea_credito=item['linea_credito'],
                    porcentaje_comision_cliente=item['porcentaje_comision_cliente'],
                    cliente_pago_pct=item['cliente_pago_pct'],
                    periodo_mes=item['periodo_mes'],
                    periodo_anio=item['periodo_anio'],
                ))
            else:
                comisiones.append(ComisionInput(
                    broker_id=item['broker_id'],
                    tipo_comision=TipoComision.OPERATIVA,
                    cliente_nombre=item['cliente_nombre'],
                    operaciones_mes=item['operaciones_mes'],
                    periodo_mes=item['periodo_mes'],
                    periodo_anio=item['periodo_anio'],
                ))

        batch_input = ComisionBatchInput(comisiones=comisiones, guardar=False)

        result = await comision_service.calcular_lote(batch_input)

        assert len(result.comisiones) == 2
        assert result.total_usd == SAMPLE_COMISION_BATCH_EXPECTED_TOTAL_USD
        assert result.total_mxn == SAMPLE_COMISION_BATCH_EXPECTED_TOTAL_MXN
        assert result.guardadas is False


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_broker_with_zero_percentage_fails(
        self, comision_service, mock_broker_repo
    ):
        """Test that broker with 0% commission rate fails appropriately"""
        mock_broker_repo.get_by_id.return_value = EDGE_CASE_ZERO_PORCENTAJE_BROKER

        with pytest.raises(ValueError) as exc_info:
            await comision_service.calcular_comision_apertura(
                broker_id=EDGE_CASE_ZERO_PORCENTAJE_BROKER['id'],
                linea_credito=Decimal('100000'),
                porcentaje_comision_cliente=Decimal('2.5'),
                cliente_pago_pct=Decimal('100'),
            )

        assert "porcentaje" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_broker_fails(self, comision_service, mock_broker_repo):
        """Test that non-existent broker ID raises ValueError"""
        mock_broker_repo.get_by_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await comision_service.calcular_comision_apertura(
                broker_id='nonexistent-broker-uuid',
                linea_credito=Decimal('100000'),
                porcentaje_comision_cliente=Decimal('2.5'),
                cliente_pago_pct=Decimal('100'),
            )

        assert "no encontrado" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_exchange_rate_fallback(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test fallback to most recent exchange rate when specific date unavailable"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_MASTER

        # First call fails (specific date), second call returns fallback
        mock_banxico_service.get_tipo_cambio.side_effect = ValueError("No rate")
        mock_banxico_service.get_tipo_cambio_actual.return_value = (
            Decimal('17.25'),
            date(2025, 1, 8)
        )

        result = await comision_service.calcular_comision_operativa(
            broker_id=SAMPLE_BROKER_MASTER['id'],
            operaciones_mes=Decimal('100000'),
            fecha_tipo_cambio=date(2025, 1, 11),  # Weekend - no rate
        )

        assert result.tipo_cambio == Decimal('17.25')
        mock_banxico_service.get_tipo_cambio_actual.assert_called_once()


# ==================== Sub-Broker Tests ====================

class TestSubBrokerCommissions:
    """Test commission calculations for sub-brokers"""

    @pytest.mark.asyncio
    async def test_sub_broker_apertura_calculation(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test apertura calculation for a sub-broker with lower rate"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_SUB
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        # Sub-broker has 30% apertura (vs master's 60%)
        result = await comision_service.calcular_comision_apertura(
            broker_id=SAMPLE_BROKER_SUB['id'],
            linea_credito=Decimal('100000'),
            porcentaje_comision_cliente=Decimal('2.5'),
            cliente_pago_pct=Decimal('100'),
        )

        # monto_comision_cliente = 100000 * 0.025 = 2500
        # monto_broker_usd = 2500 * 0.30 * 1.0 = 750
        # monto_broker_mxn = 750 * 17.50 = 13125
        assert result.monto_broker_usd == Decimal('750.00')
        assert result.monto_broker_mxn == Decimal('13125.00')

    @pytest.mark.asyncio
    async def test_sub_broker_operativa_calculation(
        self, comision_service, mock_broker_repo, mock_banxico_service
    ):
        """Test operativa calculation for a sub-broker with lower rate"""
        mock_broker_repo.get_by_id.return_value = SAMPLE_BROKER_SUB
        mock_banxico_service.get_tipo_cambio.return_value = SAMPLE_TIPO_CAMBIO

        # Sub-broker has 0.05% operativa (vs master's 0.10%)
        result = await comision_service.calcular_comision_operativa(
            broker_id=SAMPLE_BROKER_SUB['id'],
            operaciones_mes=Decimal('500000'),
        )

        # monto_broker_usd = 500000 * 0.0005 = 250
        # monto_broker_mxn = 250 * 17.50 = 4375
        assert result.monto_broker_usd == Decimal('250.00')
        assert result.monto_broker_mxn == Decimal('4375.00')


# ==================== Approval Flow Tests ====================

class TestApprovalFlow:
    """Test commission approval workflow"""

    @pytest.mark.asyncio
    async def test_approve_creates_payment_records(
        self, comision_service, mock_comision_repo, mock_pago_repo
    ):
        """Test that approval creates payment records for each broker"""
        # Setup mock data
        calculated_comisions = [
            {
                'id': 'comision-uuid-1',
                'broker_id': SAMPLE_BROKER_MASTER['id'],
                'periodo_mes': 12,
                'periodo_anio': 2025,
                'monto_broker_usd': '1500.00',
                'monto_broker_mxn': '26250.00',
                'tipo_cambio': '17.50',
                'estado': 'calculado',
            },
            {
                'id': 'comision-uuid-2',
                'broker_id': SAMPLE_BROKER_MASTER['id'],
                'periodo_mes': 12,
                'periodo_anio': 2025,
                'monto_broker_usd': '500.00',
                'monto_broker_mxn': '8750.00',
                'tipo_cambio': '17.50',
                'estado': 'calculado',
            },
        ]
        mock_comision_repo.get_by_periodo.return_value = calculated_comisions
        mock_pago_repo.exists_for_periodo.return_value = False

        result = await comision_service.aprobar_comisiones_periodo(
            mes=12,
            anio=2025,
            user_id='user-uuid-001'
        )

        assert result.comisiones_aprobadas == 2
        assert result.pagos_creados == 1  # One broker, one payment
        assert result.total_usd == 2000.0  # 1500 + 500
        assert result.total_mxn == 35000.0  # 26250 + 8750
        mock_pago_repo.create_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_no_commissions_returns_message(
        self, comision_service, mock_comision_repo
    ):
        """Test approval with no pending commissions"""
        mock_comision_repo.get_by_periodo.return_value = []

        result = await comision_service.aprobar_comisiones_periodo(
            mes=12,
            anio=2025,
            user_id='user-uuid-001'
        )

        assert result.comisiones_aprobadas == 0
        assert result.pagos_creados == 0
        assert "pendientes" in result.message.lower()

    @pytest.mark.asyncio
    async def test_approve_without_pago_repo_fails(self, mock_broker_repo, mock_comision_repo, mock_banxico_service):
        """Test that approval fails if PagoRepository not configured"""
        # Create service without pago_repo
        service = ComisionService(
            mock_broker_repo,
            mock_comision_repo,
            mock_banxico_service,
            pago_repo=None
        )

        with pytest.raises(ValueError) as exc_info:
            await service.aprobar_comisiones_periodo(
                mes=12,
                anio=2025,
                user_id='user-uuid-001'
            )

        assert "PagoRepository" in str(exc_info.value)


# ==================== Period Listing Tests ====================

class TestPeriodListing:
    """Test commission listing by period"""

    @pytest.mark.asyncio
    async def test_list_by_period_returns_all_commissions(
        self, comision_service, mock_comision_repo
    ):
        """Test listing commissions by period"""
        mock_records = [
            {
                'id': 'comision-1',
                'broker_id': SAMPLE_BROKER_MASTER['id'],
                'periodo_mes': 12,
                'periodo_anio': 2025,
                'tipo_comision': 'apertura',
                'monto_broker_usd': '1500.00',
                'monto_broker_mxn': '26250.00',
                'tipo_cambio': '17.50',
                'porcentaje_broker': '60.00',
                'estado': 'calculado',
            },
        ]
        mock_comision_repo.get_by_periodo.return_value = mock_records

        result = await comision_service.listar_por_periodo(mes=12, anio=2025)

        assert result.total == 1
        assert result.periodo_mes == 12
        assert result.periodo_anio == 2025
        mock_comision_repo.get_by_periodo.assert_called_once_with(12, 2025, None)
