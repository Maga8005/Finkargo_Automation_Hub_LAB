"""Tests for Colombia File Processor Service."""
import pytest
from datetime import date
from src.interface.finance_dtos_co import ConsolidatedRecord, NoovaRecord


class TestConsolidatedRecordNoneHandling:
    """Test suite for ConsolidatedRecord handling of None values."""

    def test_consolidated_record_accepts_empty_codigo_operacion(self):
        """Test that ConsolidatedRecord accepts empty string for codigo_operacion."""
        record = ConsolidatedRecord(
            fecha=date(2025, 1, 8),
            numero_factura="FE-12345",
            nit="",
            nombre_cliente="",
            email="",
            estado="",
            envio="",
            codigo_operacion="",
            codigo_producto="",
            concepto=""
        )
        assert record.codigo_operacion == ""
        assert record.numero_factura == "FE-12345"

    def test_consolidated_record_with_all_empty_strings(self):
        """Test ConsolidatedRecord with all Noova fields as empty strings."""
        record = ConsolidatedRecord(
            fecha=date(2025, 1, 8),
            numero_factura="FE-99999",
            nit="",
            nombre_cliente="",
            email="",
            estado="",
            envio="",
            codigo_operacion="",
            codigo_producto="",
            concepto=""
        )
        assert record.nit == ""
        assert record.nombre_cliente == ""
        assert record.email == ""
        assert record.estado == ""
        assert record.envio == ""
        assert record.codigo_operacion == ""
        assert record.codigo_producto == ""
        assert record.concepto == ""

    def test_consolidated_record_with_valid_data(self):
        """Test ConsolidatedRecord with fully populated data."""
        record = ConsolidatedRecord(
            fecha=date(2025, 1, 8),
            numero_factura="FE-12345",
            nit="900123456",
            nombre_cliente="Cliente Ejemplo S.A.S.",
            email="cliente@ejemplo.com",
            estado="Aceptado",
            envio="Enviado",
            codigo_operacion="OP-2025-001",
            codigo_producto="101",
            concepto="Interes corriente"
        )
        assert record.codigo_operacion == "OP-2025-001"
        assert record.nit == "900123456"

    def test_consolidated_record_uses_defaults_when_fields_omitted(self):
        """Test that ConsolidatedRecord uses default empty strings when optional fields are omitted."""
        # Only provide required fields (fecha, numero_factura)
        record = ConsolidatedRecord(
            fecha=date(2025, 1, 8),
            numero_factura="FE-12345"
        )
        # All optional string fields should default to empty string
        assert record.nit == ""
        assert record.nombre_cliente == ""
        assert record.email == ""
        assert record.estado == ""
        assert record.envio == ""
        assert record.codigo_operacion == ""
        assert record.codigo_producto == ""
        assert record.concepto == ""


class TestOrEmptyPatternSimulation:
    """Test the 'or empty string' pattern used in consolidate_data."""

    def test_or_pattern_handles_none_value(self):
        """Test that 'or empty string' pattern handles None values."""
        noova_dict = {
            "codigo_operacion": None,  # Simulates empty Excel cell
            "nit": "900123456"
        }

        # This is what the fix does - use 'or ""' instead of get() default
        codigo_operacion = noova_dict.get("codigo_operacion") or ""
        nit = noova_dict.get("nit") or ""

        assert codigo_operacion == ""
        assert nit == "900123456"

    def test_or_pattern_handles_missing_key(self):
        """Test that 'or empty string' pattern handles missing keys."""
        noova_dict = {"nit": "900123456"}

        codigo_operacion = noova_dict.get("codigo_operacion") or ""

        assert codigo_operacion == ""

    def test_get_default_does_not_handle_none_value(self):
        """Demonstrate that get() default doesn't work for None values."""
        noova_dict = {"codigo_operacion": None}

        # This is the BUG - get() returns None, not the default
        result = noova_dict.get("codigo_operacion", "default")

        # The key exists with None value, so get() returns None, not "default"
        assert result is None  # This is why the bug occurs

    def test_or_pattern_preserves_valid_strings(self):
        """Test that 'or empty string' pattern preserves valid non-empty strings."""
        noova_dict = {
            "codigo_operacion": "OP-2025-001",
            "nit": "900123456"
        }

        codigo_operacion = noova_dict.get("codigo_operacion") or ""
        nit = noova_dict.get("nit") or ""

        assert codigo_operacion == "OP-2025-001"
        assert nit == "900123456"

    def test_or_pattern_handles_empty_string_value(self):
        """Test that 'or empty string' pattern handles explicit empty string values."""
        noova_dict = {
            "codigo_operacion": "",  # Explicit empty string (not None)
            "nit": "900123456"
        }

        codigo_operacion = noova_dict.get("codigo_operacion") or ""
        nit = noova_dict.get("nit") or ""

        # Empty string is falsy, so 'or ""' returns "", which is correct
        assert codigo_operacion == ""
        assert nit == "900123456"
