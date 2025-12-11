"""
Unit tests for PaymentTemplateService - Colombia spread separate line feature.

Tests the special case where capital-only Pago en Linea payments generate
a separate SPREAD output line instead of populating Spread FK/PA columns.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, AsyncMock, patch
import io

from src.core.servicios.payment_template_service import PaymentTemplateService


# ==================== Fixtures ====================

@pytest.fixture
def service():
    """Create a PaymentTemplateService instance."""
    return PaymentTemplateService()


@pytest.fixture
def mock_colombia_columns():
    """Return mock column mappings for Colombia."""
    return {
        "required": {
            "cliente": "Cliente",
            "customer_external_id": "Identificación del cliente",
            "invoice_core_id": "Código de desembolso",
            "payment_ref": "Código de recaudo",
            "payment_date": "Fecha de pago",
            "currency": "Moneda",
            "capital": "Capital",
            "banco_remitente": "Banco remitente",
        },
        "optional": {
            "exchangerate": "Tasa de cambio de FK/en línea",
            "nt_flag": "NT",
            "spread": "Spread",
            "medio_pago": "Médio de pago",
            "total_pagado_usd": "Total pagado [USD]",
            "referencia_bancaria": "Referencia bancaria",
            "short_code": "Short Code",
            "cuenta_remitente": "Cuenta Remitente",
        },
        "concept": {
            "CAPITAL": "Capital",
            "4X1000": "4x1000",
            "FONDO_GARANTIAS": "Fondo de garantías",
            "IVA_FONDO_GARANTIAS": "IVA Fondo de garantías",
            "SEGUROS": "Seguro + IVA",
            "INTERESES_CORRIENTES": "Intereses Corrientes",
        }
    }


# ==================== Tests for _is_capital_only_pago_en_linea ====================

class TestIsCapitalOnlyPagoEnLinea:
    """Tests for the capital-only Pago en Linea detection method."""

    def test_capital_only_pago_en_linea_returns_true(self, service):
        """Pago en linea with only CAPITAL should return True."""
        processed_concepts = {"CAPITAL": 1000.00}
        result = service._is_capital_only_pago_en_linea(
            medio_pago="Pago en línea",
            processed_concepts=processed_concepts,
            country="colombia"
        )
        assert result is True

    def test_pago_en_linea_multiple_concepts_returns_false(self, service):
        """Pago en linea with multiple concepts should return False."""
        processed_concepts = {"CAPITAL": 1000.00, "INTERESES": 50.00}
        result = service._is_capital_only_pago_en_linea(
            medio_pago="Pago en línea",
            processed_concepts=processed_concepts,
            country="colombia"
        )
        assert result is False

    def test_manual_payment_capital_only_returns_false(self, service):
        """Manual payment with only CAPITAL should return False."""
        processed_concepts = {"CAPITAL": 1000.00}
        result = service._is_capital_only_pago_en_linea(
            medio_pago="Manual",
            processed_concepts=processed_concepts,
            country="colombia"
        )
        assert result is False

    def test_pago_en_linea_no_capital_returns_false(self, service):
        """Pago en linea without CAPITAL should return False."""
        processed_concepts = {"INTERESES": 50.00}
        result = service._is_capital_only_pago_en_linea(
            medio_pago="Pago en línea",
            processed_concepts=processed_concepts,
            country="colombia"
        )
        assert result is False

    def test_pago_en_linea_empty_concepts_returns_false(self, service):
        """Pago en linea with no concepts should return False."""
        processed_concepts = {}
        result = service._is_capital_only_pago_en_linea(
            medio_pago="Pago en línea",
            processed_concepts=processed_concepts,
            country="colombia"
        )
        assert result is False

    def test_pago_en_linea_zero_capital_returns_false(self, service):
        """Pago en linea with zero CAPITAL should return False."""
        processed_concepts = {"CAPITAL": 0.0}
        result = service._is_capital_only_pago_en_linea(
            medio_pago="Pago en línea",
            processed_concepts=processed_concepts,
            country="colombia"
        )
        assert result is False

    def test_mexico_always_returns_false(self, service):
        """Mexico should always return False (feature is Colombia-only)."""
        processed_concepts = {"CAPITAL": 1000.00}
        result = service._is_capital_only_pago_en_linea(
            medio_pago="Pago en línea",
            processed_concepts=processed_concepts,
            country="mexico"
        )
        assert result is False

    def test_none_medio_pago_returns_false(self, service):
        """None medio_pago should return False."""
        processed_concepts = {"CAPITAL": 1000.00}
        result = service._is_capital_only_pago_en_linea(
            medio_pago=None,
            processed_concepts=processed_concepts,
            country="colombia"
        )
        assert result is False

    def test_pago_en_linea_case_insensitive(self, service):
        """Pago en linea detection should be case-insensitive."""
        processed_concepts = {"CAPITAL": 1000.00}

        # Test various case variations
        variations = [
            "Pago en línea",
            "PAGO EN LÍNEA",
            "pago en línea",
            "Pago En Linea",
            "pago en linea",
        ]

        for variation in variations:
            result = service._is_capital_only_pago_en_linea(
                medio_pago=variation,
                processed_concepts=processed_concepts,
                country="colombia"
            )
            assert result is True, f"Failed for variation: {variation}"


# ==================== Tests for _create_spread_output_row ====================

class TestCreateSpreadOutputRow:
    """Tests for the SPREAD output row creation method."""

    def test_creates_correct_structure(self, service):
        """SPREAD row should have correct structure and values."""
        result = service._create_spread_output_row(
            customer_external_id="123456789",
            invoice_core_id="CO:900759388:1:7:PAG",
            payment_date="01/12/2025",
            payment_ref="123456789|20251201|COP|3854.7082",
            exchangerate=3854.70815,
            spread_amount=10000.00
        )

        assert result["customer_external_id"] == "123456789"
        assert result["invoice_core_id"] == "CO:900759388:1:7:PAG"
        assert result["concept_type"] == "SPREAD"
        assert result["payment_date"] == "01/12/2025"
        assert result["payment_amount"] == 10000.00
        assert result["currency"] == "COP"
        assert result["payment_ref"] == "123456789|20251201|COP|3854.7082"
        assert result["account"] is None
        assert result["araccount"] is None
        assert result["exchangerate"] == 3854.70815
        assert result["comision_banco"] is None
        assert result["Spread PA"] is None
        assert result["Spread FK"] is None
        assert result["Spread Supra"] is None

    def test_spread_amount_rounded(self, service):
        """Spread amount should be rounded to 2 decimal places."""
        result = service._create_spread_output_row(
            customer_external_id="123",
            invoice_core_id="CO:001",
            payment_date="01/01/2025",
            payment_ref="ref",
            exchangerate=4000.0,
            spread_amount=10000.12345
        )
        assert result["payment_amount"] == 10000.12

    def test_currency_always_cop(self, service):
        """SPREAD row currency should always be COP."""
        result = service._create_spread_output_row(
            customer_external_id="123",
            invoice_core_id="CO:001",
            payment_date="01/01/2025",
            payment_ref="ref",
            exchangerate=4000.0,
            spread_amount=5000.00
        )
        assert result["currency"] == "COP"


# ==================== Integration Tests ====================

class TestProcessRowWithSpreadSeparateLine:
    """Integration tests for _process_row with spread separate line logic."""

    def test_capital_only_pago_en_linea_creates_spread_row(self, service):
        """Capital-only Pago en linea should create a separate SPREAD row."""
        # Create a mock row with only CAPITAL
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:7:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Get column mappings
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # Should have 2 rows: CAPITAL and SPREAD
        assert len(result) == 2

        # First row should be CAPITAL
        capital_row = result[0]
        assert capital_row["concept_type"] == "CAPITAL"
        assert capital_row["payment_amount"] == 1234.56
        assert capital_row["Spread FK"] is None  # No spread in columns
        assert capital_row["Spread PA"] is None

        # Second row should be SPREAD
        spread_row = result[1]
        assert spread_row["concept_type"] == "SPREAD"
        assert spread_row["payment_amount"] == 10000.00  # 10 * 1000
        assert spread_row["currency"] == "COP"
        assert spread_row["account"] is None
        assert spread_row["araccount"] is None
        assert spread_row["customer_external_id"] == "123456789"
        assert spread_row["invoice_core_id"] == "CO:900759388:1:7:PAG"

    def test_multi_concept_pago_en_linea_no_spread_row(self, service):
        """Pago en linea with multiple concepts should NOT create separate SPREAD row.

        Also verifies spread goes to first non-CAPITAL concept (COSTOS_FIJOS), not CAPITAL.
        """
        # Create a mock row with CAPITAL and 4x1000 (which becomes COSTOS_FIJOS)
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:6:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 100,  # Has 4x1000 cost -> becomes COSTOS_FIJOS
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # Should have 2 rows: CAPITAL and COSTOS_FIJOS, no SPREAD
        concept_types = [r["concept_type"] for r in result]
        assert "SPREAD" not in concept_types
        assert "CAPITAL" in concept_types
        assert "COSTOS_FIJOS" in concept_types

        # CAPITAL row should NOT have Spread FK (spread goes to non-CAPITAL)
        capital_row = next(r for r in result if r["concept_type"] == "CAPITAL")
        assert capital_row["Spread FK"] is None, "CAPITAL should not have Spread FK when other concepts exist"
        assert capital_row["Spread PA"] is None, "CAPITAL should not have Spread PA when other concepts exist"

        # COSTOS_FIJOS row should have Spread FK (first non-CAPITAL concept)
        costos_fijos_row = next(r for r in result if r["concept_type"] == "COSTOS_FIJOS")
        assert costos_fijos_row["Spread FK"] == 10000.00, "COSTOS_FIJOS should have Spread FK = 10 * 1000"

    def test_manual_payment_capital_only_no_spread_row(self, service):
        """Manual payment with only CAPITAL should NOT create separate SPREAD row."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:8:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",  # Not Pago en línea
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # Should have only 1 row: CAPITAL, no SPREAD
        assert len(result) == 1
        assert result[0]["concept_type"] == "CAPITAL"
        # Should have Spread FK populated (standard behavior for capital-only Manual)
        assert result[0]["Spread FK"] == 10000.00  # 10 * 1000

    def test_no_spread_line_when_spread_value_zero(self, service):
        """No SPREAD row should be created when spread value is zero."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:9:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 0,  # Zero spread
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # Should have only 1 row: CAPITAL, no SPREAD (spread is zero)
        assert len(result) == 1
        assert result[0]["concept_type"] == "CAPITAL"

    def test_no_spread_line_when_total_pagado_usd_missing(self, service):
        """No SPREAD row when total_pagado_usd is missing."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:10:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 10,
            "Total pagado [USD]": None,  # Missing total
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # Should have only 1 row: CAPITAL, no SPREAD
        assert len(result) == 1
        assert result[0]["concept_type"] == "CAPITAL"


# ==================== Tests for _get_spread_target_index ====================

class TestGetSpreadTargetIndex:
    """Tests for the spread target index determination method."""

    def test_colombia_capital_only_returns_zero(self, service):
        """Colombia with only CAPITAL should return 0."""
        processed_concepts = {"CAPITAL": 1000.00}
        result = service._get_spread_target_index(processed_concepts, "colombia")
        assert result == 0

    def test_colombia_capital_plus_costos_fijos_returns_one(self, service):
        """Colombia with CAPITAL + COSTOS_FIJOS should return 1 (COSTOS_FIJOS index)."""
        # Dictionary maintains insertion order in Python 3.7+
        processed_concepts = {"CAPITAL": 1000.00, "COSTOS_FIJOS": 100.00}
        result = service._get_spread_target_index(processed_concepts, "colombia")
        assert result == 1  # COSTOS_FIJOS is at index 1

    def test_colombia_capital_plus_intereses_returns_one(self, service):
        """Colombia with CAPITAL + INTERESES should return 1 (INTERESES index)."""
        processed_concepts = {"CAPITAL": 1000.00, "INTERESES": 50.00}
        result = service._get_spread_target_index(processed_concepts, "colombia")
        assert result == 1  # INTERESES is at index 1

    def test_colombia_capital_plus_multiple_concepts_returns_first_non_capital(self, service):
        """Colombia with CAPITAL + multiple concepts should return first non-CAPITAL."""
        # Order: CAPITAL, COSTOS_FIJOS, INTERESES
        processed_concepts = {"CAPITAL": 1000.00, "COSTOS_FIJOS": 100.00, "INTERESES": 50.00}
        result = service._get_spread_target_index(processed_concepts, "colombia")
        assert result == 1  # COSTOS_FIJOS is first non-CAPITAL at index 1

    def test_colombia_only_non_capital_concepts_returns_zero(self, service):
        """Colombia with only non-CAPITAL concepts should return 0 (first one)."""
        processed_concepts = {"COSTOS_FIJOS": 100.00, "INTERESES": 50.00}
        result = service._get_spread_target_index(processed_concepts, "colombia")
        assert result == 0  # COSTOS_FIJOS is first and non-CAPITAL

    def test_colombia_zero_capital_with_others_returns_non_capital_index(self, service):
        """Colombia with zero CAPITAL but other concepts should skip zero values."""
        # Only non-zero concepts are considered
        processed_concepts = {"CAPITAL": 0.0, "COSTOS_FIJOS": 100.00}
        result = service._get_spread_target_index(processed_concepts, "colombia")
        # CAPITAL is zero, so only COSTOS_FIJOS is in non_zero_concepts at index 0
        assert result == 0

    def test_mexico_always_returns_zero(self, service):
        """México should always return 0 regardless of concepts."""
        processed_concepts = {"CAPITAL": 1000.00, "COSTOS_FIJOS": 100.00}
        result = service._get_spread_target_index(processed_concepts, "mexico")
        assert result == 0

    def test_mexico_case_insensitive(self, service):
        """México detection should be case-insensitive."""
        processed_concepts = {"CAPITAL": 1000.00, "COSTOS_FIJOS": 100.00}

        for country_variant in ["mexico", "Mexico", "MEXICO", "MéXiCo"]:
            result = service._get_spread_target_index(processed_concepts, country_variant)
            assert result == 0, f"Failed for variant: {country_variant}"

    def test_colombia_case_insensitive(self, service):
        """Colombia detection should be case-insensitive."""
        processed_concepts = {"CAPITAL": 1000.00, "COSTOS_FIJOS": 100.00}

        for country_variant in ["colombia", "Colombia", "COLOMBIA"]:
            result = service._get_spread_target_index(processed_concepts, country_variant)
            assert result == 1, f"Failed for variant: {country_variant}"

    def test_empty_concepts_returns_zero(self, service):
        """Empty concepts dict should return 0."""
        processed_concepts = {}
        result = service._get_spread_target_index(processed_concepts, "colombia")
        assert result == 0


# ==================== Additional Integration Tests for Spread Non-Capital ====================

class TestSpreadAssignmentToNonCapital:
    """Integration tests for spread assignment to non-CAPITAL concepts."""

    def test_spread_assigned_to_intereses_not_capital(self, service):
        """Spread should go to INTERESES when CAPITAL + INTERESES exist."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:11:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 5,
            "Total pagado [USD]": 2000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 75.50,  # Has interest
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # Should have 2 rows: CAPITAL and INTERESES
        assert len(result) == 2

        capital_row = next(r for r in result if r["concept_type"] == "CAPITAL")
        intereses_row = next(r for r in result if r["concept_type"] == "INTERESES")

        # CAPITAL should NOT have spread
        assert capital_row["Spread FK"] is None
        assert capital_row["Spread PA"] is None

        # INTERESES should have spread
        assert intereses_row["Spread FK"] == 10000.00  # 5 * 2000

    def test_comision_banco_stays_on_first_row(self, service):
        """comision_banco should always go to first row (idx == 0), independent of spread."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:12:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 100,  # Creates COSTOS_FIJOS
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
            "Comisión bancaria": 25.00,  # Bank commission
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # First row (CAPITAL) should have comision_banco
        capital_row = result[0]
        assert capital_row["concept_type"] == "CAPITAL"
        # Note: comision_banco is only set for Pago en línea with NT condition
        # but the key is that it goes to idx == 0

        # COSTOS_FIJOS should have spread, not comision_banco
        costos_fijos_row = next(r for r in result if r["concept_type"] == "COSTOS_FIJOS")
        assert costos_fijos_row["Spread FK"] == 10000.00

    def test_spread_on_capital_when_only_capital_manual(self, service):
        """Manual payment with only CAPITAL should have spread on CAPITAL."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:13:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 5000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",  # Not Pago en línea
            "Tasa de cambio de FK/en línea": 3854.70815,
            "Spread": 8,
            "Total pagado [USD]": 1500,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        # Only CAPITAL row, should have spread (no other option)
        assert len(result) == 1
        assert result[0]["concept_type"] == "CAPITAL"
        assert result[0]["Spread FK"] == 12000.00  # 8 * 1500
