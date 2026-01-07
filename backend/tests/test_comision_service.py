"""
Unit tests for ComisionService - Broker commission calculation logic
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.servicios.comision_service import ComisionService
from src.interface.alianzas_dtos import (
    ComisionInput,
    ComisionBatchInput,
    TipoComision,
    EstadoComision,
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_broker_repo():
    """Create a mock BrokerRepository"""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
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
def mock_banxico_service():
    """Create a mock BanxicoService"""
    service = MagicMock()
    service.get_tipo_cambio = AsyncMock()
    service.get_tipo_cambio_actual = AsyncMock()
    return service


@pytest.fixture
def comision_service(mock_broker_repo, mock_comision_repo, mock_banxico_service):
    """Create ComisionService with mocked dependencies"""
    return ComisionService(mock_broker_repo, mock_comision_repo, mock_banxico_service)


@pytest.fixture
def sample_broker():
    """Sample broker data"""
    return {
        'id': 'broker-uuid-123',
        'nombre': 'Test Broker',
        'porcentaje_apertura': Decimal('60.00'),  # 60%
        'porcentaje_operativa': Decimal('0.10'),  # 0.10%
        'estado': 'activo',
    }


@pytest.fixture
def sample_exchange_rate():
    """Sample exchange rate"""
    return Decimal('17.5000')


# ==================== Apertura Commission Tests ====================

@pytest.mark.asyncio
async def test_calcular_apertura_success(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test successful apertura commission calculation"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    # Execute
    result = await comision_service.calcular_comision_apertura(
        broker_id='broker-uuid-123',
        linea_credito=Decimal('100000'),  # $100,000 USD credit line
        porcentaje_comision_cliente=Decimal('2.5'),  # 2.5% client commission
        cliente_pago_pct=Decimal('100'),  # 100% paid
        fecha_tipo_cambio=date(2025, 1, 10),
        cliente_nombre='Test Client',
        cliente_nit='900123456-7',
        periodo_mes=1,
        periodo_anio=2025,
    )

    # Verify
    assert result.broker_id == 'broker-uuid-123'
    assert result.broker_nombre == 'Test Broker'
    assert result.tipo_comision == TipoComision.APERTURA
    assert result.linea_credito == Decimal('100000')
    assert result.porcentaje_comision_cliente == Decimal('2.5')

    # monto_comision_cliente = 100000 * 0.025 = 2500
    assert result.monto_comision_cliente == Decimal('2500.00')

    # monto_broker_usd = 2500 * 0.60 * 1.0 = 1500
    assert result.monto_broker_usd == Decimal('1500.00')

    # monto_broker_mxn = 1500 * 17.50 = 26250
    assert result.monto_broker_mxn == Decimal('26250.00')

    assert result.tipo_cambio == sample_exchange_rate
    assert result.estado == EstadoComision.CALCULADO


@pytest.mark.asyncio
async def test_calcular_apertura_partial_payment(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test apertura commission with partial client payment (50%)"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    # Execute
    result = await comision_service.calcular_comision_apertura(
        broker_id='broker-uuid-123',
        linea_credito=Decimal('100000'),
        porcentaje_comision_cliente=Decimal('2.5'),
        cliente_pago_pct=Decimal('50'),  # Only 50% paid
    )

    # monto_comision_cliente = 100000 * 0.025 = 2500
    # monto_broker_usd = 2500 * 0.60 * 0.50 = 750
    assert result.monto_broker_usd == Decimal('750.00')

    # monto_broker_mxn = 750 * 17.50 = 13125
    assert result.monto_broker_mxn == Decimal('13125.00')


@pytest.mark.asyncio
async def test_calcular_apertura_min_payment_validation(comision_service):
    """Test that apertura commission rejects < 50% client payment"""
    # Execute & Verify
    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_comision_apertura(
            broker_id='broker-uuid-123',
            linea_credito=Decimal('100000'),
            porcentaje_comision_cliente=Decimal('2.5'),
            cliente_pago_pct=Decimal('49'),  # Below 50% threshold
        )

    assert "50%" in str(exc_info.value)
    assert "49%" in str(exc_info.value)


@pytest.mark.asyncio
async def test_calcular_apertura_broker_not_found(comision_service, mock_broker_repo):
    """Test that apertura commission raises ValueError when broker not found"""
    # Setup
    mock_broker_repo.get_by_id.return_value = None

    # Execute & Verify
    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_comision_apertura(
            broker_id='nonexistent-broker',
            linea_credito=Decimal('100000'),
            porcentaje_comision_cliente=Decimal('2.5'),
            cliente_pago_pct=Decimal('50'),
        )

    assert "no encontrado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_calcular_apertura_no_percentage_configured(comision_service, mock_broker_repo):
    """Test that apertura commission raises ValueError when broker has no apertura percentage"""
    # Setup
    broker_without_percentage = {
        'id': 'broker-uuid-123',
        'nombre': 'Test Broker',
        'porcentaje_apertura': None,
        'porcentaje_operativa': Decimal('0.10'),
    }
    mock_broker_repo.get_by_id.return_value = broker_without_percentage

    # Execute & Verify
    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_comision_apertura(
            broker_id='broker-uuid-123',
            linea_credito=Decimal('100000'),
            porcentaje_comision_cliente=Decimal('2.5'),
            cliente_pago_pct=Decimal('50'),
        )

    assert "porcentaje de apertura" in str(exc_info.value)


# ==================== Operativa Commission Tests ====================

@pytest.mark.asyncio
async def test_calcular_operativa_success(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test successful operativa commission calculation"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    # Execute
    result = await comision_service.calcular_comision_operativa(
        broker_id='broker-uuid-123',
        operaciones_mes=Decimal('500000'),  # $500,000 USD monthly disbursements
        fecha_tipo_cambio=date(2025, 1, 10),
        cliente_nombre='Test Client',
        cliente_nit='900123456-7',
        periodo_mes=1,
        periodo_anio=2025,
    )

    # Verify
    assert result.broker_id == 'broker-uuid-123'
    assert result.broker_nombre == 'Test Broker'
    assert result.tipo_comision == TipoComision.OPERATIVA
    assert result.operaciones_mes == Decimal('500000')

    # monto_broker_usd = 500000 * 0.001 = 500
    assert result.monto_broker_usd == Decimal('500.00')

    # monto_broker_mxn = 500 * 17.50 = 8750
    assert result.monto_broker_mxn == Decimal('8750.00')

    assert result.tipo_cambio == sample_exchange_rate
    assert result.estado == EstadoComision.CALCULADO


@pytest.mark.asyncio
async def test_calcular_operativa_broker_not_found(comision_service, mock_broker_repo):
    """Test that operativa commission raises ValueError when broker not found"""
    # Setup
    mock_broker_repo.get_by_id.return_value = None

    # Execute & Verify
    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_comision_operativa(
            broker_id='nonexistent-broker',
            operaciones_mes=Decimal('500000'),
        )

    assert "no encontrado" in str(exc_info.value)


@pytest.mark.asyncio
async def test_calcular_operativa_no_percentage_configured(comision_service, mock_broker_repo):
    """Test that operativa commission raises ValueError when broker has no operativa percentage"""
    # Setup
    broker_without_percentage = {
        'id': 'broker-uuid-123',
        'nombre': 'Test Broker',
        'porcentaje_apertura': Decimal('60.00'),
        'porcentaje_operativa': None,
    }
    mock_broker_repo.get_by_id.return_value = broker_without_percentage

    # Execute & Verify
    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_comision_operativa(
            broker_id='broker-uuid-123',
            operaciones_mes=Decimal('500000'),
        )

    assert "porcentaje operativo" in str(exc_info.value)


# ==================== Currency Conversion Tests ====================

@pytest.mark.asyncio
async def test_currency_conversion_with_fallback(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker
):
    """Test that service falls back to most recent rate when specific date unavailable"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker

    # First call raises ValueError (date not available), second returns current rate
    mock_banxico_service.get_tipo_cambio.side_effect = ValueError("No rate for this date")
    mock_banxico_service.get_tipo_cambio_actual.return_value = (
        Decimal('17.25'),
        date(2025, 1, 8)
    )

    # Execute
    result = await comision_service.calcular_comision_operativa(
        broker_id='broker-uuid-123',
        operaciones_mes=Decimal('100000'),
        fecha_tipo_cambio=date(2025, 1, 11),  # Weekend, no rate available
    )

    # Verify fallback was used
    assert result.tipo_cambio == Decimal('17.25')
    mock_banxico_service.get_tipo_cambio_actual.assert_called_once()


@pytest.mark.asyncio
async def test_decimal_precision_maintained(
    comision_service, mock_broker_repo, mock_banxico_service
):
    """Test that Decimal precision is maintained throughout calculation"""
    # Setup
    broker = {
        'id': 'broker-uuid-123',
        'nombre': 'Test Broker',
        'porcentaje_apertura': Decimal('33.33'),  # Tricky percentage
        'porcentaje_operativa': Decimal('0.123'),
    }
    mock_broker_repo.get_by_id.return_value = broker
    mock_banxico_service.get_tipo_cambio.return_value = Decimal('17.3456')

    # Execute
    result = await comision_service.calcular_comision_operativa(
        broker_id='broker-uuid-123',
        operaciones_mes=Decimal('123456.78'),
    )

    # Verify result is Decimal with proper precision (2 decimal places)
    assert isinstance(result.monto_broker_usd, Decimal)
    assert isinstance(result.monto_broker_mxn, Decimal)

    # Check rounding to 2 decimal places
    assert result.monto_broker_usd == result.monto_broker_usd.quantize(Decimal('0.01'))
    assert result.monto_broker_mxn == result.monto_broker_mxn.quantize(Decimal('0.01'))


# ==================== Batch Calculation Tests ====================

@pytest.mark.asyncio
async def test_calcular_lote_without_save(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test batch calculation without saving to database"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    batch_input = ComisionBatchInput(
        comisiones=[
            ComisionInput(
                broker_id='broker-uuid-123',
                tipo_comision=TipoComision.APERTURA,
                linea_credito=Decimal('100000'),
                porcentaje_comision_cliente=Decimal('2.5'),
                cliente_pago_pct=Decimal('100'),
            ),
            ComisionInput(
                broker_id='broker-uuid-123',
                tipo_comision=TipoComision.OPERATIVA,
                operaciones_mes=Decimal('500000'),
            ),
        ],
        guardar=False,
    )

    # Execute
    result = await comision_service.calcular_lote(batch_input, user_id=None)

    # Verify
    assert len(result.comisiones) == 2
    assert result.guardadas is False

    # Total should be sum of both commissions
    # apertura: 1500 USD, operativa: 500 USD
    assert result.total_usd == Decimal('2000.00')

    # mxn: 26250 + 8750 = 35000
    assert result.total_mxn == Decimal('35000.00')


@pytest.mark.asyncio
async def test_calcular_lote_with_save(
    comision_service, mock_broker_repo, mock_comision_repo, mock_banxico_service,
    sample_broker, sample_exchange_rate
):
    """Test batch calculation with save to database"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    # Mock batch create to return records with IDs
    mock_comision_repo.create_batch.return_value = [
        {'id': 'comision-1', 'created_at': '2025-01-10T10:00:00Z', 'created_by': 'user-123'},
        {'id': 'comision-2', 'created_at': '2025-01-10T10:00:00Z', 'created_by': 'user-123'},
    ]

    batch_input = ComisionBatchInput(
        comisiones=[
            ComisionInput(
                broker_id='broker-uuid-123',
                tipo_comision=TipoComision.APERTURA,
                linea_credito=Decimal('100000'),
                porcentaje_comision_cliente=Decimal('2.5'),
                cliente_pago_pct=Decimal('100'),
            ),
            ComisionInput(
                broker_id='broker-uuid-123',
                tipo_comision=TipoComision.OPERATIVA,
                operaciones_mes=Decimal('500000'),
            ),
        ],
        guardar=True,
    )

    # Execute
    result = await comision_service.calcular_lote(batch_input, user_id='user-123')

    # Verify
    assert result.guardadas is True
    assert len(result.comisiones) == 2

    # Verify IDs were set from database response
    assert result.comisiones[0].id == 'comision-1'
    assert result.comisiones[1].id == 'comision-2'

    # Verify create_batch was called
    mock_comision_repo.create_batch.assert_called_once()


@pytest.mark.asyncio
async def test_calcular_lote_requires_user_id_for_save(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test that batch save requires user_id"""
    # Setup - need to mock dependencies for the calculation to succeed first
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    batch_input = ComisionBatchInput(
        comisiones=[
            ComisionInput(
                broker_id='broker-uuid-123',
                tipo_comision=TipoComision.OPERATIVA,
                operaciones_mes=Decimal('500000'),
            ),
        ],
        guardar=True,
    )

    # Execute & Verify
    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_lote(batch_input, user_id=None)

    assert "user_id es requerido" in str(exc_info.value)


# ==================== Input Validation Tests ====================

@pytest.mark.asyncio
async def test_calcular_comision_apertura_missing_fields(comision_service):
    """Test that calcular_comision validates required fields for apertura"""
    input_data = ComisionInput(
        broker_id='broker-uuid-123',
        tipo_comision=TipoComision.APERTURA,
        # Missing linea_credito, porcentaje_comision_cliente, cliente_pago_pct
    )

    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_comision(input_data)

    assert "linea_credito" in str(exc_info.value) or "requerido" in str(exc_info.value)


@pytest.mark.asyncio
async def test_calcular_comision_operativa_missing_fields(comision_service):
    """Test that calcular_comision validates required fields for operativa"""
    input_data = ComisionInput(
        broker_id='broker-uuid-123',
        tipo_comision=TipoComision.OPERATIVA,
        # Missing operaciones_mes
    )

    with pytest.raises(ValueError) as exc_info:
        await comision_service.calcular_comision(input_data)

    assert "operaciones_mes" in str(exc_info.value) or "requerido" in str(exc_info.value)


# ==================== Edge Cases ====================

@pytest.mark.asyncio
async def test_apertura_exactly_50_percent_boundary(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test apertura commission at exactly 50% boundary"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    # Execute - exactly 50% should pass
    result = await comision_service.calcular_comision_apertura(
        broker_id='broker-uuid-123',
        linea_credito=Decimal('100000'),
        porcentaje_comision_cliente=Decimal('2.5'),
        cliente_pago_pct=Decimal('50'),  # Exactly at boundary
    )

    # Verify it worked
    assert result.cliente_pago_pct == Decimal('50')
    assert result.monto_broker_usd > 0


@pytest.mark.asyncio
async def test_large_credit_line_precision(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test calculation with very large credit line maintains precision"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    # Execute with large amount
    result = await comision_service.calcular_comision_apertura(
        broker_id='broker-uuid-123',
        linea_credito=Decimal('10000000'),  # $10 million
        porcentaje_comision_cliente=Decimal('2.5'),
        cliente_pago_pct=Decimal('100'),
    )

    # monto_comision_cliente = 10000000 * 0.025 = 250000
    # monto_broker_usd = 250000 * 0.60 * 1.0 = 150000
    assert result.monto_broker_usd == Decimal('150000.00')

    # monto_broker_mxn = 150000 * 17.50 = 2625000
    assert result.monto_broker_mxn == Decimal('2625000.00')


@pytest.mark.asyncio
async def test_zero_operations_returns_zero_commission(
    comision_service, mock_broker_repo, mock_banxico_service, sample_broker, sample_exchange_rate
):
    """Test that zero operations results in zero commission"""
    # Setup
    mock_broker_repo.get_by_id.return_value = sample_broker
    mock_banxico_service.get_tipo_cambio.return_value = sample_exchange_rate

    # Execute with zero operations
    result = await comision_service.calcular_comision_operativa(
        broker_id='broker-uuid-123',
        operaciones_mes=Decimal('0'),
    )

    assert result.monto_broker_usd == Decimal('0.00')
    assert result.monto_broker_mxn == Decimal('0.00')
