"""
Alianzas Module Test Fixtures

This module provides sample broker, commission, and payment data for testing
the Alianzas (Partnerships) module. All calculation examples include expected
results based on the business formulas.

Commission Calculation Formulas:
================================

Apertura Commission:
    monto_comision_cliente = linea_credito * (porcentaje_comision_cliente / 100)
    monto_broker_usd = monto_comision_cliente * (porcentaje_broker / 100) * (cliente_pago_pct / 100)
    monto_broker_mxn = monto_broker_usd * tipo_cambio

Operativa Commission:
    monto_broker_usd = operaciones_mes * (porcentaje_operativa / 100)
    monto_broker_mxn = monto_broker_usd * tipo_cambio

Business Rules:
===============
- cliente_pago_pct must be >= 50% for apertura commissions
- tipo_cambio is fetched from Banxico API (USD/MXN FIX rate)
- All monetary amounts are rounded to 2 decimal places
"""
from decimal import Decimal
from datetime import date
from typing import Dict, Any, List


# ==================== Exchange Rate Fixtures ====================

SAMPLE_TIPO_CAMBIO = Decimal("17.5000")
SAMPLE_TIPO_CAMBIO_DATE = date(2025, 1, 10)


# ==================== Broker Fixtures ====================

SAMPLE_BROKER_MASTER: Dict[str, Any] = {
    "id": "broker-master-uuid-001",
    "nombre": "Test Master Broker",
    "tipo_broker": "master_broker",
    "master_broker_id": None,
    "porcentaje_apertura": Decimal("60.00"),  # 60% of client commission
    "porcentaje_operativa": Decimal("0.10"),  # 0.10% of monthly operations
    "cuenta_bancaria": "012345678901234567",
    "banco": "BBVA Mexico",
    "rfc": "TMB010101ABC",
    "fecha_contrato": "2024-01-01",
    "vigencia_contrato": "2025-12-31",
    "estado": "activo",
    "link_expediente": "https://drive.google.com/folders/test-master",
    "notas": "Master broker for testing",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "created_by": "user-uuid-001",
}

SAMPLE_BROKER_SUB: Dict[str, Any] = {
    "id": "broker-sub-uuid-001",
    "nombre": "Test Sub Broker",
    "tipo_broker": "independiente",
    "master_broker_id": "broker-master-uuid-001",
    "porcentaje_apertura": Decimal("30.00"),  # 30% of client commission
    "porcentaje_operativa": Decimal("0.05"),  # 0.05% of monthly operations
    "cuenta_bancaria": "098765432109876543",
    "banco": "Santander",
    "rfc": "TSB020202XYZ",
    "fecha_contrato": "2024-06-01",
    "vigencia_contrato": "2025-12-31",
    "estado": "activo",
    "link_expediente": "https://drive.google.com/folders/test-sub",
    "notas": "Sub-broker for testing",
    "created_at": "2024-06-01T10:00:00Z",
    "updated_at": "2024-06-01T10:00:00Z",
    "created_by": "user-uuid-001",
}

SAMPLE_BROKER_NO_APERTURA: Dict[str, Any] = {
    "id": "broker-no-apertura-uuid-001",
    "nombre": "Operations Only Broker",
    "tipo_broker": "aliado_logistico",
    "master_broker_id": None,
    "porcentaje_apertura": None,  # No apertura commission
    "porcentaje_operativa": Decimal("0.15"),  # 0.15% of monthly operations
    "cuenta_bancaria": "111111111111111111",
    "banco": "Banorte",
    "rfc": "AOB030303DEF",
    "estado": "activo",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
}

SAMPLE_BROKER_NO_OPERATIVA: Dict[str, Any] = {
    "id": "broker-no-operativa-uuid-001",
    "nombre": "Apertura Only Broker",
    "tipo_broker": "consultoria",
    "master_broker_id": None,
    "porcentaje_apertura": Decimal("50.00"),
    "porcentaje_operativa": None,  # No operativa commission
    "cuenta_bancaria": "222222222222222222",
    "banco": "HSBC",
    "rfc": "AOB040404GHI",
    "estado": "activo",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
}


# ==================== Apertura Commission Fixtures ====================

SAMPLE_COMISION_APERTURA: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "apertura",
    "cliente_nombre": "Test Client S.A. de C.V.",
    "cliente_nit": "TCSA123456ABC",
    "linea_credito": Decimal("100000.00"),  # $100,000 USD credit line
    "porcentaje_comision_cliente": Decimal("2.50"),  # 2.5% client commission
    "cliente_pago_pct": Decimal("100.00"),  # 100% paid
    "periodo_mes": 12,
    "periodo_anio": 2025,
    # Expected calculation with SAMPLE_BROKER_MASTER (60% apertura) and SAMPLE_TIPO_CAMBIO (17.50):
    # monto_comision_cliente = 100000 * 0.025 = 2500.00
    # monto_broker_usd = 2500 * 0.60 * 1.0 = 1500.00
    # monto_broker_mxn = 1500 * 17.50 = 26250.00
    "expected_monto_comision_cliente": Decimal("2500.00"),
    "expected_monto_broker_usd": Decimal("1500.00"),
    "expected_monto_broker_mxn": Decimal("26250.00"),
}

SAMPLE_COMISION_APERTURA_PARTIAL_PAYMENT: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "apertura",
    "cliente_nombre": "Partial Payment Client",
    "cliente_nit": "PPC789012DEF",
    "linea_credito": Decimal("100000.00"),
    "porcentaje_comision_cliente": Decimal("2.50"),
    "cliente_pago_pct": Decimal("50.00"),  # Only 50% paid (minimum allowed)
    "periodo_mes": 12,
    "periodo_anio": 2025,
    # Expected calculation:
    # monto_comision_cliente = 100000 * 0.025 = 2500.00
    # monto_broker_usd = 2500 * 0.60 * 0.50 = 750.00
    # monto_broker_mxn = 750 * 17.50 = 13125.00
    "expected_monto_comision_cliente": Decimal("2500.00"),
    "expected_monto_broker_usd": Decimal("750.00"),
    "expected_monto_broker_mxn": Decimal("13125.00"),
}

SAMPLE_COMISION_APERTURA_BELOW_MINIMUM: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "apertura",
    "cliente_nombre": "Below Minimum Client",
    "linea_credito": Decimal("100000.00"),
    "porcentaje_comision_cliente": Decimal("2.50"),
    "cliente_pago_pct": Decimal("49.00"),  # Below 50% - should fail validation
    "periodo_mes": 12,
    "periodo_anio": 2025,
    # Expected: ValueError - minimum 50% payment required
    "expected_error": "El cliente debe haber pagado al menos 50%",
}

SAMPLE_COMISION_APERTURA_LARGE_CREDIT_LINE: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "apertura",
    "cliente_nombre": "Large Credit Line Client",
    "cliente_nit": "LCL345678GHI",
    "linea_credito": Decimal("10000000.00"),  # $10 million
    "porcentaje_comision_cliente": Decimal("2.50"),
    "cliente_pago_pct": Decimal("100.00"),
    "periodo_mes": 1,
    "periodo_anio": 2025,
    # Expected calculation:
    # monto_comision_cliente = 10000000 * 0.025 = 250000.00
    # monto_broker_usd = 250000 * 0.60 * 1.0 = 150000.00
    # monto_broker_mxn = 150000 * 17.50 = 2625000.00
    "expected_monto_comision_cliente": Decimal("250000.00"),
    "expected_monto_broker_usd": Decimal("150000.00"),
    "expected_monto_broker_mxn": Decimal("2625000.00"),
}


# ==================== Operativa Commission Fixtures ====================

SAMPLE_COMISION_OPERATIVA: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "operativa",
    "cliente_nombre": "Operations Client S.A.",
    "cliente_nit": "OCS456789JKL",
    "operaciones_mes": Decimal("500000.00"),  # $500,000 USD monthly disbursements
    "periodo_mes": 12,
    "periodo_anio": 2025,
    # Expected calculation with SAMPLE_BROKER_MASTER (0.10% operativa) and SAMPLE_TIPO_CAMBIO (17.50):
    # monto_broker_usd = 500000 * 0.001 = 500.00
    # monto_broker_mxn = 500 * 17.50 = 8750.00
    "expected_monto_broker_usd": Decimal("500.00"),
    "expected_monto_broker_mxn": Decimal("8750.00"),
}

SAMPLE_COMISION_OPERATIVA_ZERO: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "operativa",
    "cliente_nombre": "Zero Operations Client",
    "operaciones_mes": Decimal("0.00"),  # Zero operations
    "periodo_mes": 12,
    "periodo_anio": 2025,
    # Expected: Zero commission
    "expected_monto_broker_usd": Decimal("0.00"),
    "expected_monto_broker_mxn": Decimal("0.00"),
}

SAMPLE_COMISION_OPERATIVA_LARGE: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "operativa",
    "cliente_nombre": "Large Operations Client",
    "cliente_nit": "LOC567890MNO",
    "operaciones_mes": Decimal("5000000.00"),  # $5 million monthly
    "periodo_mes": 6,
    "periodo_anio": 2025,
    # Expected calculation:
    # monto_broker_usd = 5000000 * 0.001 = 5000.00
    # monto_broker_mxn = 5000 * 17.50 = 87500.00
    "expected_monto_broker_usd": Decimal("5000.00"),
    "expected_monto_broker_mxn": Decimal("87500.00"),
}


# ==================== Batch Commission Fixtures ====================

SAMPLE_COMISION_BATCH: List[Dict[str, Any]] = [
    {
        "broker_id": "broker-master-uuid-001",
        "tipo_comision": "apertura",
        "cliente_nombre": "Batch Client 1",
        "linea_credito": Decimal("50000.00"),
        "porcentaje_comision_cliente": Decimal("3.00"),
        "cliente_pago_pct": Decimal("100.00"),
        "periodo_mes": 12,
        "periodo_anio": 2025,
        # Expected: 50000 * 0.03 * 0.60 * 1.0 = 900.00 USD
        "expected_monto_broker_usd": Decimal("900.00"),
    },
    {
        "broker_id": "broker-master-uuid-001",
        "tipo_comision": "operativa",
        "cliente_nombre": "Batch Client 2",
        "operaciones_mes": Decimal("200000.00"),
        "periodo_mes": 12,
        "periodo_anio": 2025,
        # Expected: 200000 * 0.001 = 200.00 USD
        "expected_monto_broker_usd": Decimal("200.00"),
    },
]
# Batch totals: 900 + 200 = 1100.00 USD, 1100 * 17.50 = 19250.00 MXN
SAMPLE_COMISION_BATCH_EXPECTED_TOTAL_USD = Decimal("1100.00")
SAMPLE_COMISION_BATCH_EXPECTED_TOTAL_MXN = Decimal("19250.00")


# ==================== Payment Fixtures ====================

SAMPLE_PAGO: Dict[str, Any] = {
    "id": "pago-uuid-001",
    "broker_id": "broker-master-uuid-001",
    "broker_nombre": "Test Master Broker",
    "periodo_mes": 12,
    "periodo_anio": 2025,
    "total_usd": Decimal("2000.00"),
    "total_mxn": Decimal("35000.00"),
    "tipo_cambio": Decimal("17.50"),
    "fecha_programada": None,
    "fecha_pago": None,
    "estado": "pendiente",
    "comprobante_url": None,
    "factura_broker_url": None,
    "notas": None,
    "created_at": "2025-01-15T10:00:00Z",
    "approved_by": "user-uuid-001",
}


# ==================== Edge Case Data ====================

EDGE_CASE_ZERO_PORCENTAJE_BROKER: Dict[str, Any] = {
    "id": "broker-zero-pct-uuid",
    "nombre": "Zero Percentage Broker",
    "tipo_broker": "independiente",
    "porcentaje_apertura": Decimal("0.00"),  # 0% - should fail validation
    "porcentaje_operativa": Decimal("0.00"),
    "estado": "activo",
}

EDGE_CASE_PRECISION_TEST: Dict[str, Any] = {
    "broker_id": "broker-master-uuid-001",
    "tipo_comision": "operativa",
    "operaciones_mes": Decimal("123456.78"),  # Non-round amount
    "expected_tipo_cambio": Decimal("17.3456"),  # Non-round rate
    # Expected: 123456.78 * 0.001 = 123.45678 -> rounded to 123.46 USD
    # MXN: 123.46 * 17.3456 = 2141.38 (approx)
}


# ==================== Contract Extraction Fixtures ====================

SAMPLE_CONTRACT_EXTRACTED_DATA: Dict[str, Any] = {
    "nombre_broker": "Extracted Broker S.A.",
    "porcentaje_comision_apertura": 55.0,
    "porcentaje_comision_operativa": 0.12,
    "fecha_contrato": "2025-01-01",
    "vigencia_meses": 24,
    "rfc_broker": "EBS010101AAA",
    "cuenta_bancaria": "012210001234567891",
    "banco": "BBVA Mexico",
    "extraction_method": "standard",
    "extraction_confidence": 0.85,
}


# ==================== Test User Fixtures ====================

SAMPLE_USER_ALIANZAS: Dict[str, Any] = {
    "id": "user-alianzas-uuid-001",
    "email": "test-alianzas@finkargo.com",
    "role": "alianzas",
}

SAMPLE_USER_ADMIN: Dict[str, Any] = {
    "id": "user-admin-uuid-001",
    "email": "test-admin@finkargo.com",
    "role": "admin",
}


# ==================== Utility Functions ====================

def get_apertura_commission_inputs() -> List[Dict[str, Any]]:
    """Return list of apertura commission test inputs."""
    return [
        SAMPLE_COMISION_APERTURA,
        SAMPLE_COMISION_APERTURA_PARTIAL_PAYMENT,
        SAMPLE_COMISION_APERTURA_LARGE_CREDIT_LINE,
    ]


def get_operativa_commission_inputs() -> List[Dict[str, Any]]:
    """Return list of operativa commission test inputs."""
    return [
        SAMPLE_COMISION_OPERATIVA,
        SAMPLE_COMISION_OPERATIVA_ZERO,
        SAMPLE_COMISION_OPERATIVA_LARGE,
    ]


def get_all_brokers() -> List[Dict[str, Any]]:
    """Return list of all sample brokers."""
    return [
        SAMPLE_BROKER_MASTER,
        SAMPLE_BROKER_SUB,
        SAMPLE_BROKER_NO_APERTURA,
        SAMPLE_BROKER_NO_OPERATIVA,
    ]
