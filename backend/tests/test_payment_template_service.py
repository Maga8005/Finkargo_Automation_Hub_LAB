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
        """Manual USD payment with only CAPITAL should NOT create separate SPREAD row.

        Note: Manual USD payments have no spread (only Manual COP has spread via TRM).
        """
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:8:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",  # USD - no spread for manual USD
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
        # Manual USD has no spread (only Manual COP has spread via TRM)
        assert result[0]["Spread FK"] is None
        assert result[0]["Spread PA"] is None

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
        """Spread should go to INTERESES when CAPITAL + INTERESES exist (Pago en línea)."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:11:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",  # Pago en línea to test spread assignment
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
            "Médio de pago": "Pago en línea",  # Use Pago en línea to test spread + comision_banco
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

        # Only CAPITAL row, Manual USD has no spread (TRM-based spread only for Manual COP)
        assert len(result) == 1
        assert result[0]["concept_type"] == "CAPITAL"
        assert result[0]["Spread FK"] is None  # Manual USD = no spread
        assert result[0]["Spread PA"] is None


# ==================== Tests for Manual Payment Exchange Rate Behavior ====================

class TestManualPaymentExchangeRate:
    """Tests for exchange rate clearing on Manual payments."""

    def test_manual_payment_cop_has_no_exchange_rate(self, service):
        """Manual payment in COP should have exchangerate = None."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:14:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1234.56,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 3854.70815,  # Should be ignored
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
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

        assert len(result) >= 1
        assert result[0]["exchangerate"] is None

    def test_manual_payment_usd_has_no_exchange_rate(self, service):
        """Manual payment in USD should have exchangerate = None."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:15:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 3854.70815,  # Should be ignored
            "Spread": 10,
            "Total pagado [USD]": 1000,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
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

        assert len(result) >= 1
        assert result[0]["exchangerate"] is None

    def test_pago_en_linea_cop_has_adjusted_exchange_rate(self, service):
        """Pago en linea in COP should have exchangerate = (tasa_fincargo - spread)."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:16:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
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

        assert len(result) >= 1
        # Expected: 3854.70815 - 10 = 3844.70815
        assert result[0]["exchangerate"] == pytest.approx(3844.70815, rel=1e-4)

    def test_pago_en_linea_usd_has_unadjusted_exchange_rate(self, service):
        """Pago en linea in USD should have exchangerate = tasa_fincargo (no adjustment)."""
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:17:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",
            "Capital": 1000.00,
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

        assert len(result) >= 1
        # Expected: 3854.70815 (no adjustment for USD)
        assert result[0]["exchangerate"] == pytest.approx(3854.70815, rel=1e-4)

    def test_manual_payment_case_insensitive(self, service):
        """Manual payment detection should be case-insensitive."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        for manual_variant in ["Manual", "MANUAL", "manual", "MaNuAl"]:
            row_data = {
                "Cliente": "Test Client",
                "Identificación del cliente": "123456789",
                "Código de desembolso": "CO:900759388:1:18:PAG",
                "Código de recaudo": "REC-001",
                "Fecha de pago": "2025-12-01",
                "Moneda": "COP",
                "Capital": 1000.00,
                "Banco remitente": "Test Bank",
                "Médio de pago": manual_variant,
                "Tasa de cambio de FK/en línea": 3854.70815,
                "Spread": 10,
                "Total pagado [USD]": 1000,
                "NT": "",
                "4x1000": 0,
                "Fondo de garantías": 0,
                "IVA Fondo de garantías": 0,
                "Seguro + IVA": 0,
                "Intereses Corrientes": 0,
                "Cuenta Remitente": "60100001091",
            }

            row = pd.Series(row_data)
            df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

            assert result[0]["exchangerate"] is None, f"Failed for variant: {manual_variant}"


# ==================== Tests for Payment Group-Level SPREAD Decision ====================

class TestPaymentGroupLevelSpreadDecision:
    """
    Tests for the payment group-level SPREAD line decision logic.

    The decision to create a separate SPREAD line must be made at the PAYMENT GROUP LEVEL
    (all rows with the same payment_ref), NOT at the individual row level.
    """

    def test_is_capital_only_pago_en_linea_for_group_capital_only(self, service):
        """Group with only CAPITAL concept should return True for Pago en línea."""
        group_concepts = {"CAPITAL"}
        result = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Pago en línea",
            group_concepts=group_concepts,
            country="colombia"
        )
        assert result is True

    def test_is_capital_only_pago_en_linea_for_group_mixed_concepts(self, service):
        """Group with mixed concepts should return False."""
        group_concepts = {"CAPITAL", "INTERESES"}
        result = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Pago en línea",
            group_concepts=group_concepts,
            country="colombia"
        )
        assert result is False

    def test_is_capital_only_pago_en_linea_for_group_manual_payment(self, service):
        """Manual payment should return False regardless of concepts."""
        group_concepts = {"CAPITAL"}
        result = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Manual",
            group_concepts=group_concepts,
            country="colombia"
        )
        assert result is False

    def test_is_capital_only_pago_en_linea_for_group_mexico(self, service):
        """México should always return False."""
        group_concepts = {"CAPITAL"}
        result = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Pago en línea",
            group_concepts=group_concepts,
            country="mexico"
        )
        assert result is False

    def test_is_capital_only_pago_en_linea_for_group_empty_concepts(self, service):
        """Empty concepts set should return False."""
        group_concepts = set()
        result = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Pago en línea",
            group_concepts=group_concepts,
            country="colombia"
        )
        assert result is False

    def test_is_capital_only_pago_en_linea_for_group_only_non_capital(self, service):
        """Group with only non-CAPITAL concepts should return False."""
        group_concepts = {"INTERESES", "COSTOS_FIJOS"}
        result = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Pago en línea",
            group_concepts=group_concepts,
            country="colombia"
        )
        assert result is False


class TestPaymentGroupPreProcessing:
    """Tests for the payment group pre-processing phase."""

    def test_collect_group_info_single_row_capital_only(self, service):
        """Single row with only CAPITAL should have concepts = {'CAPITAL'}."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Intereses Corrientes": 0,
            "Médio de pago": "Pago en línea",
            "Spread": 10,
            "Total pagado [USD]": 500,
            "Tasa de cambio de FK/en línea": 4000.0,
            "Cuenta Remitente": "",
        }

        df = pd.DataFrame([row_data])
        df_columns_normalized = {col.lower().strip(): col for col in df.columns}

        group_info = service._collect_payment_group_info(
            df=df,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized
        )

        # Should have one group
        assert len(group_info) == 1

        # Get the first (and only) group
        group_key = list(group_info.keys())[0]
        info = group_info[group_key]

        assert info["concepts"] == {"CAPITAL"}
        assert info["medio_pago"] == "Pago en línea"
        assert info["total_pagado_usd"] == 500

    def test_collect_group_info_multi_row_mixed_concepts(self, service):
        """Multi-row group with mixed concepts should aggregate all concepts."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Same payment group (same customer, date, currency, rate)
        row1 = {
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Intereses Corrientes": 0,  # No interest in row 1
            "Médio de pago": "Pago en línea",
            "Spread": 10,
            "Total pagado [USD]": 500,
            "Tasa de cambio de FK/en línea": 4000.0,
            "Cuenta Remitente": "",
        }

        row2 = {
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:002",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 0,  # No capital in row 2
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Intereses Corrientes": 50.00,  # Has interest
            "Médio de pago": "Pago en línea",
            "Spread": 10,
            "Total pagado [USD]": 500,
            "Tasa de cambio de FK/en línea": 4000.0,
            "Cuenta Remitente": "",
        }

        df = pd.DataFrame([row1, row2])
        df_columns_normalized = {col.lower().strip(): col for col in df.columns}

        group_info = service._collect_payment_group_info(
            df=df,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized
        )

        # Should have one group (same payment_ref)
        assert len(group_info) == 1

        group_key = list(group_info.keys())[0]
        info = group_info[group_key]

        # Should have both CAPITAL and INTERESES (aggregated from both rows)
        assert "CAPITAL" in info["concepts"]
        assert "INTERESES" in info["concepts"]
        assert info["total_pagado_usd"] == 1000  # 500 + 500


class TestProcessRowWithGroupContext:
    """Tests for _process_row using group context for SPREAD decision."""

    def test_multi_row_group_capital_row_with_intereses_in_group_no_spread_line(self, service):
        """
        Row 1 has only CAPITAL, but Row 2 in same group has INTERESES.
        Group should NOT create separate SPREAD line because group has mixed concepts.
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Row 1: Only has CAPITAL
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:001",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 10,
            "Total pagado [USD]": 500,
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

        # Group info indicates another row in the group has INTERESES
        group_info = {
            "concepts": {"CAPITAL", "INTERESES"},  # Mixed concepts at group level
            "medio_pago": "Pago en línea",
            "total_pagado_usd": 1000,
            "spread_assigned": False,
            "first_cop_non_capital_row_idx": None,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True,
            group_info=group_info
        )

        # Should have only CAPITAL row, NO separate SPREAD row
        assert len(result) == 1
        assert result[0]["concept_type"] == "CAPITAL"

        # CAPITAL should NOT have spread (it goes to non-CAPITAL row which is in another input row)
        # Since this row has no non-CAPITAL concepts, spread should not be here
        assert result[0]["Spread FK"] is None

    def test_single_row_group_capital_only_creates_spread_line(self, service):
        """
        Single-row group with only CAPITAL (Pago en línea) should create separate SPREAD line.
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:001",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 10,
            "Total pagado [USD]": 500,
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

        # Group info: only CAPITAL concept in entire group
        group_info = {
            "concepts": {"CAPITAL"},  # Only CAPITAL at group level
            "medio_pago": "Pago en línea",
            "total_pagado_usd": 500,
            "spread_assigned": False,
            "first_cop_non_capital_row_idx": None,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True,
            group_info=group_info
        )

        # Should have 2 rows: CAPITAL and SPREAD
        assert len(result) == 2
        assert result[0]["concept_type"] == "CAPITAL"
        assert result[1]["concept_type"] == "SPREAD"
        assert result[1]["payment_amount"] == 5000.00  # 10 * 500

    def test_multi_row_all_capital_creates_spread_line(self, service):
        """
        Multi-row group where ALL rows have only CAPITAL (Pago en línea)
        should create separate SPREAD line.
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:001",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 10,
            "Total pagado [USD]": 500,
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

        # Group info: only CAPITAL even across multiple rows
        group_info = {
            "concepts": {"CAPITAL"},  # All rows only have CAPITAL
            "medio_pago": "Pago en línea",
            "total_pagado_usd": 1000,  # Sum from multiple rows
            "spread_assigned": False,
            "first_cop_non_capital_row_idx": None,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True,
            group_info=group_info
        )

        # Should create SPREAD line because group is capital-only
        assert len(result) == 2
        concept_types = [r["concept_type"] for r in result]
        assert "CAPITAL" in concept_types
        assert "SPREAD" in concept_types


# ==================== Tests for Aggregated Total Pagado USD ====================

class TestSpreadAggregatedTotalPagadoUSD:
    """
    Tests for the spread calculation using aggregated Total Pagado [USD] at payment group level.

    The spread amount must be calculated using the SUM of Total Pagado [USD] across ALL rows
    in the same payment group, not the individual row value.
    """

    def test_spread_uses_aggregated_total_pagado_usd_from_group(self, service):
        """
        Spread should be calculated using GROUP-LEVEL aggregated total_pagado_usd,
        NOT row-level value.

        Setup:
        - Row 1: Total Pagado USD = 50, only CAPITAL
        - Row 2: Total Pagado USD = 500, INTERESES + COSTOS_FIJOS
        - Same payment group (same payment_ref)
        - Spread rate = 10

        Expected:
        - Aggregated total = 550 (50 + 500)
        - Spread amount = 10 × 550 = 5500
        - Spread goes to first non-CAPITAL row (INTERESES row)
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Row 2: Has non-CAPITAL concepts (INTERESES via Intereses Corrientes)
        # This row has Total Pagado USD = 500, but group total is 550
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:20:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 0,  # No capital in this row
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",  # Use Pago en línea to test aggregated totals
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 10,  # Spread rate = 10
            "Total pagado [USD]": 500,  # Row-level total (should NOT be used)
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 150,  # Non-CAPITAL concept
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Group info with AGGREGATED total_pagado_usd = 550 (50 from row 1 + 500 from row 2)
        group_info = {
            "concepts": {"CAPITAL", "INTERESES"},  # Mixed concepts at group level
            "medio_pago": "Pago en línea",
            "total_pagado_usd": 550,  # AGGREGATED: 50 + 500
            "spread_assigned": False,
            "first_cop_non_capital_row_idx": 1,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=False,  # This is row 2
            group_info=group_info
        )

        # Should have 1 row: INTERESES
        assert len(result) == 1
        intereses_row = result[0]
        assert intereses_row["concept_type"] == "INTERESES"

        # Spread should use AGGREGATED total (550), not row total (500)
        # Expected: 10 × 550 = 5500
        assert intereses_row["Spread FK"] == 5500.00, \
            f"Expected spread = 5500 (10 × 550 aggregated), got {intereses_row['Spread FK']}"

    def test_spread_assigned_only_once_per_group_via_flag(self, service):
        """
        Verify that spread_assigned flag prevents duplicate spread assignment.

        When group_info["spread_assigned"] is True, no spread should be assigned.
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Row with non-CAPITAL concept
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:21:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 0,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 10,
            "Total pagado [USD]": 500,
            "NT": "",
            "4x1000": 100,  # Creates COSTOS_FIJOS
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Group info with spread_assigned = True (spread already assigned to another row)
        group_info = {
            "concepts": {"CAPITAL", "COSTOS_FIJOS"},
            "medio_pago": "Manual",
            "total_pagado_usd": 1000,
            "spread_assigned": True,  # Already assigned!
            "first_cop_non_capital_row_idx": 0,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=False,
            group_info=group_info
        )

        # Should have COSTOS_FIJOS row
        assert len(result) == 1
        costos_fijos_row = result[0]
        assert costos_fijos_row["concept_type"] == "COSTOS_FIJOS"

        # Spread should be None because it was already assigned to another row
        assert costos_fijos_row["Spread FK"] is None, \
            f"Expected Spread FK = None (already assigned), got {costos_fijos_row['Spread FK']}"
        assert costos_fijos_row["Spread PA"] is None

    def test_spread_assignment_sets_flag_to_true(self, service):
        """
        Verify that group_info["spread_assigned"] is set to True after spread assignment.
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Row with non-CAPITAL concept (Pago en línea)
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:22:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 0,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",  # Use Pago en línea to test flag behavior
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 10,
            "Total pagado [USD]": 500,
            "NT": "",
            "4x1000": 100,  # Creates COSTOS_FIJOS
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Group info with spread_assigned = False (not yet assigned)
        group_info = {
            "concepts": {"COSTOS_FIJOS"},
            "medio_pago": "Pago en línea",
            "total_pagado_usd": 500,
            "spread_assigned": False,  # Not yet assigned
            "first_cop_non_capital_row_idx": 0,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True,
            group_info=group_info
        )

        # Should have COSTOS_FIJOS row with spread
        assert len(result) == 1
        assert result[0]["Spread FK"] == 5000.00  # 10 × 500

        # Flag should now be True
        assert group_info["spread_assigned"] is True, \
            "spread_assigned flag should be True after spread assignment"

    def test_separate_spread_line_uses_aggregated_total(self, service):
        """
        Separate SPREAD line should use aggregated total_pagado_usd from group.
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Row with only CAPITAL (Pago en línea) - will create separate SPREAD line
        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:23:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,  # Only CAPITAL
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",  # This triggers separate SPREAD line
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 10,  # Spread rate
            "Total pagado [USD]": 200,  # Row total (should NOT be used)
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

        # Group info: capital-only group (all rows have only CAPITAL)
        # Aggregated total = 800 (200 from this row + 600 from other rows)
        group_info = {
            "concepts": {"CAPITAL"},  # Capital-only group
            "medio_pago": "Pago en línea",
            "total_pagado_usd": 800,  # AGGREGATED total (not row total of 200)
            "spread_assigned": False,
            "first_cop_non_capital_row_idx": None,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True,
            group_info=group_info
        )

        # Should have 2 rows: CAPITAL and SPREAD
        assert len(result) == 2
        concept_types = [r["concept_type"] for r in result]
        assert "CAPITAL" in concept_types
        assert "SPREAD" in concept_types

        # SPREAD line amount should use AGGREGATED total
        # Expected: 10 × 800 = 8000
        spread_row = next(r for r in result if r["concept_type"] == "SPREAD")
        assert spread_row["payment_amount"] == 8000.00, \
            f"Expected SPREAD amount = 8000 (10 × 800 aggregated), got {spread_row['payment_amount']}"

    def test_single_row_group_uses_same_value(self, service):
        """
        For single-row groups, aggregated total equals row total (backward compatible).
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:24:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",  # Test aggregated totals for Pago en línea
            "Tasa de cambio de FK/en línea": 4000.0,
            "Spread": 5,
            "Total pagado [USD]": 300,  # Row total
            "NT": "",
            "4x1000": 50,  # Creates COSTOS_FIJOS
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Single-row group: aggregated = row total
        group_info = {
            "concepts": {"CAPITAL", "COSTOS_FIJOS"},
            "medio_pago": "Pago en línea",
            "total_pagado_usd": 300,  # Same as row total
            "spread_assigned": False,
            "first_cop_non_capital_row_idx": 0,
        }

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True,
            group_info=group_info
        )

        # Should have 2 rows: CAPITAL and COSTOS_FIJOS
        assert len(result) == 2

        # COSTOS_FIJOS should have spread (first non-CAPITAL)
        costos_fijos_row = next(r for r in result if r["concept_type"] == "COSTOS_FIJOS")
        assert costos_fijos_row["Spread FK"] == 1500.00, \
            f"Expected spread = 1500 (5 × 300), got {costos_fijos_row['Spread FK']}"


# ==================== Tests for Manual COP Spread Calculation ====================

class TestManualCOPSpreadCalculation:
    """Tests for manual COP payment spread calculation with TRM integration."""

    @pytest.fixture
    def service(self):
        """Create a PaymentTemplateService instance."""
        return PaymentTemplateService()

    def test_calculate_manual_cop_spread_valid_inputs(self, service):
        """Test spread calculation with valid inputs."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=4150.25,
            total_pagado_usd=1000.00
        )

        # Expected: (4200.00 - 4150.25) × 1000 = 49750.00
        assert result == 49750.00

    def test_calculate_manual_cop_spread_none_tasa_fincargo(self, service):
        """Test spread calculation with missing tasa_fincargo."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=None,
            tasa_trm=4150.25,
            total_pagado_usd=1000.00
        )
        assert result is None

    def test_calculate_manual_cop_spread_none_tasa_trm(self, service):
        """Test spread calculation with missing tasa_trm."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=None,
            total_pagado_usd=1000.00
        )
        assert result is None

    def test_calculate_manual_cop_spread_none_total_usd(self, service):
        """Test spread calculation with missing total_pagado_usd."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=4150.25,
            total_pagado_usd=None
        )
        assert result is None

    def test_calculate_manual_cop_spread_zero_total_usd(self, service):
        """Test spread calculation with zero total_pagado_usd."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=4150.25,
            total_pagado_usd=0.0
        )
        assert result is None

    def test_calculate_manual_cop_spread_negative_total_usd(self, service):
        """Test spread calculation with negative total_pagado_usd."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=4150.25,
            total_pagado_usd=-100.00
        )
        assert result is None

    def test_calculate_manual_cop_spread_negative_spread(self, service):
        """Test spread calculation when TRM > Fincargo rate (negative spread)."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4100.00,
            tasa_trm=4150.25,
            total_pagado_usd=1000.00
        )

        # Expected: (4100.00 - 4150.25) × 1000 = -50250.00
        assert result == -50250.00

    def test_calculate_manual_cop_spread_rounding(self, service):
        """Test spread calculation rounds to 2 decimal places."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.12345,
            tasa_trm=4150.98765,
            total_pagado_usd=100.00
        )

        # Expected: (4200.12345 - 4150.98765) × 100 = 4913.58 (rounded)
        assert result == 4913.58


class TestManualCOPSpreadIntegration:
    """Integration tests for manual COP spread with TRM service."""

    @pytest.fixture
    def service(self):
        """Create a PaymentTemplateService instance."""
        return PaymentTemplateService()

    def test_manual_cop_payment_with_trm_calculates_spread(self, service):
        """Manual COP payment with TRM available calculates spread to Spread FK (NT empty)."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:30:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,  # Fincargo rate
            "Spread": 10,  # Not used for manual (TRM formula used instead)
            "Total pagado [USD]": 1000.00,
            "NT": "",  # Empty NT = not cedida -> Spread FK
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Mock TRM service to return a fixed rate
        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 1
        capital_row = result[0]

        # Spread FK should be calculated: (4200.00 - 4150.25) × 1000 = 49750.00
        # Goes to FK because NT is empty (not cedida)
        assert capital_row["Spread FK"] == 49750.00
        assert capital_row["Spread PA"] is None
        # Exchange rate should be None for manual payments
        assert capital_row["exchangerate"] is None

    def test_manual_cop_payment_trm_unavailable_no_spread(self, service):
        """Manual COP payment with TRM unavailable skips spread."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:31:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Mock TRM service to return None (API error or no data)
        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = None

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 1
        capital_row = result[0]

        # No spread when TRM unavailable
        assert capital_row["Spread PA"] is None
        assert capital_row["Spread FK"] is None

    def test_manual_usd_payment_no_spread(self, service):
        """Manual USD payment should have no spread regardless of TRM."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:32:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",  # USD payment
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # TRM service should NOT be called for USD payments
        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

            # TRM should not be called for USD
            mock_trm.get_trm_for_date.assert_not_called()

        assert len(result) >= 1
        capital_row = result[0]

        # No spread for USD payments
        assert capital_row["Spread PA"] is None
        assert capital_row["Spread FK"] is None

    def test_pago_en_linea_unchanged_with_trm_integration(self, service):
        """Pago en línea payments should still use original spread logic."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:33:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 0,  # Only INTERESES
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",  # Online payment
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,  # Spread rate for online payments
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 500.00,  # Has interest
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # TRM service should NOT be called for Pago en línea
        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

            # TRM should not be called for Pago en línea
            mock_trm.get_trm_for_date.assert_not_called()

        assert len(result) >= 1
        intereses_row = result[0]

        # Pago en línea uses Spread FK with original formula
        assert intereses_row["Spread FK"] == 10000.00  # 10 × 1000
        assert intereses_row["Spread PA"] is None

    def test_manual_cop_spread_goes_to_non_capital_when_mixed(self, service):
        """Manual COP spread should go to first non-CAPITAL concept when mixed."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:34:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 100,  # Has 4x1000 -> COSTOS_FIJOS
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        # Should have CAPITAL and COSTOS_FIJOS
        assert len(result) == 2
        concept_types = [r["concept_type"] for r in result]
        assert "CAPITAL" in concept_types
        assert "COSTOS_FIJOS" in concept_types

        # CAPITAL should NOT have spread
        capital_row = next(r for r in result if r["concept_type"] == "CAPITAL")
        assert capital_row["Spread PA"] is None
        assert capital_row["Spread FK"] is None

        # COSTOS_FIJOS should have Spread FK (first non-CAPITAL)
        # NT is empty so spread goes to FK column
        costos_fijos_row = next(r for r in result if r["concept_type"] == "COSTOS_FIJOS")
        # Expected: (4200.00 - 4150.25) × 1000 = 49750.00
        assert costos_fijos_row["Spread FK"] == 49750.00
        assert costos_fijos_row["Spread PA"] is None

    def test_manual_cop_missing_exchange_rate_no_spread(self, service):
        """Manual COP with missing exchange rate should have no spread."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:35:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": None,  # Missing exchange rate
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 1
        capital_row = result[0]

        # No spread when exchange rate is missing
        assert capital_row["Spread PA"] is None
        assert capital_row["Spread FK"] is None

    def test_manual_cop_missing_total_usd_no_spread(self, service):
        """Manual COP with missing total_pagado_usd should have no spread."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:36:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": None,  # Missing total USD
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 1
        capital_row = result[0]

        # No spread when total USD is missing
        assert capital_row["Spread PA"] is None
        assert capital_row["Spread FK"] is None

    def test_manual_cop_case_insensitive_detection(self, service):
        """Manual payment detection should be case-insensitive."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        for manual_variant in ["Manual", "MANUAL", "manual", "MaNuAl"]:
            row_data = {
                "Cliente": "Test Client",
                "Identificación del cliente": "123456789",
                "Código de desembolso": "CO:900759388:1:37:PAG",
                "Código de recaudo": "REC-001",
                "Fecha de pago": "2025-12-01",
                "Moneda": "COP",
                "Capital": 5000000.00,
                "Banco remitente": "Test Bank",
                "Médio de pago": manual_variant,
                "Tasa de cambio de FK/en línea": 4200.00,
                "Spread": 10,
                "Total pagado [USD]": 1000.00,
                "NT": "",
                "4x1000": 0,
                "Fondo de garantías": 0,
                "IVA Fondo de garantías": 0,
                "Seguro + IVA": 0,
                "Intereses Corrientes": 0,
                "Cuenta Remitente": "60100001091",
            }

            row = pd.Series(row_data)
            df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

            with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
                mock_trm.get_trm_for_date.return_value = 4150.25

                result = service._process_row(
                    row=row,
                    country="colombia",
                    required_columns=required_columns,
                    concept_columns=concept_columns,
                    optional_columns=optional_columns,
                    df_columns_normalized=df_columns_normalized,
                    is_first_row_in_group=True
                )

            capital_row = result[0]
            # All variants should calculate spread (goes to FK since NT is empty)
            assert capital_row["Spread FK"] == 49750.00, f"Failed for variant: {manual_variant}"

    def test_manual_cop_nt_flag_routes_to_spread_pa(self, service):
        """Manual COP payment with NT flag should route spread to Spread PA."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:38:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "NT",  # NT flag present -> Spread PA
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 1
        capital_row = result[0]

        # NT flag present -> Spread PA
        # Expected: (4200.00 - 4150.25) × 1000 = 49750.00
        assert capital_row["Spread PA"] == 49750.00
        assert capital_row["Spread FK"] is None


# ==================== Tests for Recompra AR Account Selection ====================

class TestRecompraARAccountSelection:
    """Integration tests for recompra AR account selection in _process_row."""

    @pytest.fixture
    def service(self):
        """Create a PaymentTemplateService instance."""
        return PaymentTemplateService()

    def test_normal_operation_uses_fincargo_ar_accounts(self, service):
        """Normal operation (NT empty) should use Fincargo Colombia AR accounts."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:40:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "",  # Empty NT = normal operation
            "Recomprado": "",  # No recompra flag
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 100.00,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 2  # CAPITAL and INTERESES

        # Find CAPITAL and INTERESES rows
        capital_row = next(r for r in result if r["concept_type"] == "CAPITAL")
        intereses_row = next(r for r in result if r["concept_type"] == "INTERESES")

        # Normal operation -> Fincargo Colombia AR accounts
        assert capital_row["araccount"] == 302  # CAPITAL: 302
        assert intereses_row["araccount"] == 258  # INTERESES: 258

    def test_cedida_not_recomprada_uses_patrimonio_ar_accounts(self, service):
        """Cedida operation (NT populated, NOT recomprada) should use Patrimonio AR accounts."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:41:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "NT-12345",  # NT populated = cedida operation
            "Recomprado": "",  # NOT recomprada
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 100.00,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 2  # CAPITAL and INTERESES

        # Find CAPITAL and INTERESES rows
        capital_row = next(r for r in result if r["concept_type"] == "CAPITAL")
        intereses_row = next(r for r in result if r["concept_type"] == "INTERESES")

        # Cedida not recomprada -> Patrimonio Autónomo AR accounts
        assert capital_row["araccount"] == 304  # CAPITAL: 304
        assert intereses_row["araccount"] == 259  # INTERESES: 259

    def test_cedida_recomprada_uses_fincargo_ar_accounts(self, service):
        """Recomprada operation (NT populated + recomprada) should use Fincargo Colombia AR accounts."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:42:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "NT-12345",  # NT populated = cedida operation
            "Recomprado": "Si",  # RECOMPRADA
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 100.00,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 2  # CAPITAL and INTERESES

        # Find CAPITAL and INTERESES rows
        capital_row = next(r for r in result if r["concept_type"] == "CAPITAL")
        intereses_row = next(r for r in result if r["concept_type"] == "INTERESES")

        # Recomprada -> Fincargo Colombia AR accounts (reverted from Patrimonio)
        assert capital_row["araccount"] == 302  # CAPITAL: 302 (reverted from 304)
        assert intereses_row["araccount"] == 258  # INTERESES: 258 (reverted from 259)

    def test_recomprada_with_various_truthy_values(self, service):
        """Recomprada detection should work with various truthy values."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Test various truthy values for recompra
        truthy_values = ["Si", "SÍ", "sí", "YES", "yes", "True", "true", "1", "Recomprada", "RECOMPRADA"]

        for recompra_value in truthy_values:
            row_data = {
                "Cliente": "Test Client",
                "Identificación del cliente": "123456789",
                "Código de desembolso": "CO:900759388:1:43:PAG",
                "Código de recaudo": "REC-001",
                "Fecha de pago": "2025-12-01",
                "Moneda": "COP",
                "Capital": 5000000.00,
                "Banco remitente": "Test Bank",
                "Médio de pago": "Manual",
                "Tasa de cambio de FK/en línea": 4200.00,
                "Spread": 10,
                "Total pagado [USD]": 1000.00,
                "NT": "NT-12345",  # NT populated
                "Recomprado": recompra_value,  # Various truthy values
                "4x1000": 0,
                "Fondo de garantías": 0,
                "IVA Fondo de garantías": 0,
                "Seguro + IVA": 0,
                "Intereses Corrientes": 0,
                "Cuenta Remitente": "60100001091",
            }

            row = pd.Series(row_data)
            df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

            with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
                mock_trm.get_trm_for_date.return_value = 4150.25

                result = service._process_row(
                    row=row,
                    country="colombia",
                    required_columns=required_columns,
                    concept_columns=concept_columns,
                    optional_columns=optional_columns,
                    df_columns_normalized=df_columns_normalized,
                    is_first_row_in_group=True
                )

            assert len(result) >= 1
            capital_row = result[0]

            # Recomprada -> Fincargo Colombia AR accounts
            assert capital_row["araccount"] == 302, f"Failed for recompra value: {recompra_value}"

    def test_recomprada_with_falsy_values_uses_patrimonio(self, service):
        """Falsy recompra values should result in Patrimonio accounts for cedida operations."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Test various falsy values for recompra
        falsy_values = ["No", "NO", "no", "False", "false", "0", "", "N/A", "Maybe"]

        for recompra_value in falsy_values:
            row_data = {
                "Cliente": "Test Client",
                "Identificación del cliente": "123456789",
                "Código de desembolso": "CO:900759388:1:44:PAG",
                "Código de recaudo": "REC-001",
                "Fecha de pago": "2025-12-01",
                "Moneda": "COP",
                "Capital": 5000000.00,
                "Banco remitente": "Test Bank",
                "Médio de pago": "Manual",
                "Tasa de cambio de FK/en línea": 4200.00,
                "Spread": 10,
                "Total pagado [USD]": 1000.00,
                "NT": "NT-12345",  # NT populated = cedida
                "Recomprado": recompra_value,  # Various falsy values
                "4x1000": 0,
                "Fondo de garantías": 0,
                "IVA Fondo de garantías": 0,
                "Seguro + IVA": 0,
                "Intereses Corrientes": 0,
                "Cuenta Remitente": "60100001091",
            }

            row = pd.Series(row_data)
            df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

            with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
                mock_trm.get_trm_for_date.return_value = 4150.25

                result = service._process_row(
                    row=row,
                    country="colombia",
                    required_columns=required_columns,
                    concept_columns=concept_columns,
                    optional_columns=optional_columns,
                    df_columns_normalized=df_columns_normalized,
                    is_first_row_in_group=True
                )

            assert len(result) >= 1
            capital_row = result[0]

            # Falsy recompra value -> Patrimonio AR accounts
            assert capital_row["araccount"] == 304, f"Failed for recompra value: '{recompra_value}'"

    def test_all_concept_types_affected_by_recompra(self, service):
        """All concept types should be affected by the recompra flag."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:45:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "NT-12345",  # NT populated
            "Recomprado": "Si",  # Recomprada
            "4x1000": 50.00,  # COSTOS_FIJOS component
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 100.00,  # SEGUROS
            "Intereses Corrientes": 75.00,  # INTERESES
            "Cuenta Remitente": "60100001091",
            "Intereses de Mora (Tasa corriente) PAR 60": 25.00,  # MORATORIOS component
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        # Expected Fincargo Colombia AR accounts (due to recompra):
        expected_accounts = {
            "CAPITAL": 302,
            "COSTOS_FIJOS": 258,
            "SEGUROS": 1387,
            "INTERESES": 258,
            "MORATORIOS": 258,
        }

        for row_result in result:
            concept_type = row_result["concept_type"]
            if concept_type in expected_accounts:
                assert row_result["araccount"] == expected_accounts[concept_type], \
                    f"{concept_type}: Expected {expected_accounts[concept_type]}, got {row_result['araccount']}"


# ==================== Tests for Multi-Currency Payment Group Grouping ====================

class TestMultiCurrencyPaymentGroupGrouping:
    """
    Tests for correct payment grouping when a single payment has multiple
    source rows with different currencies (USD and COP) but the same exchange rate.

    Bug context: Previously, currency was included in the payment_ref grouping key,
    causing USD and COP rows with the same exchange rate to be treated as separate
    payment groups. This led to:
    - A separate SPREAD row being created for USD-only CAPITAL rows
    - The COP row receiving spread in the column instead of receiving the full group spread

    Fix: Currency is no longer included in payment_ref generation. Payments with the
    same customer, date, cuenta_remitente, and exchange rate are grouped together.
    """

    def test_payment_ref_excludes_currency(self, service):
        """
        Payment ref should NOT include currency in the grouping key.

        USD and COP rows with same exchange rate should have the same payment_ref.
        """
        # Generate payment_ref for USD row
        usd_ref = service._generate_payment_ref(
            customer_external_id="901260586",
            payment_date_raw="2025-12-09",
            currency="USD",
            cuenta_remitente=None,
            exchangerate="3930.133136"
        )

        # Generate payment_ref for COP row with same exchange rate
        cop_ref = service._generate_payment_ref(
            customer_external_id="901260586",
            payment_date_raw="2025-12-09",
            currency="COP",
            cuenta_remitente=None,
            exchangerate="3930.133136"
        )

        # Both should have the same payment_ref since currency is excluded
        assert usd_ref == cop_ref, f"USD ref: {usd_ref}, COP ref: {cop_ref}"
        # Verify currency is not in the ref
        assert "USD" not in usd_ref
        assert "COP" not in cop_ref

    def test_different_exchange_rates_create_separate_groups(self, service):
        """
        Rows with different exchange rates should still be in separate groups.
        """
        ref_rate1 = service._generate_payment_ref(
            customer_external_id="901260586",
            payment_date_raw="2025-12-09",
            currency="USD",
            cuenta_remitente=None,
            exchangerate="3934.4617"
        )

        ref_rate2 = service._generate_payment_ref(
            customer_external_id="901260586",
            payment_date_raw="2025-12-09",
            currency="USD",
            cuenta_remitente=None,
            exchangerate="3930.1331"
        )

        # Different exchange rates should create different payment_refs
        assert ref_rate1 != ref_rate2

    def test_multi_currency_group_concepts_aggregated(self, service):
        """
        Test that _collect_payment_group_info correctly aggregates concepts
        from both USD and COP rows into the same payment group.
        """
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        # Create a DataFrame with USD CAPITAL and COP MORATORIOS rows
        # Same exchange rate = same payment group
        data = [
            {
                "Cliente": "CARDIOFIT STORE SAS",
                "Identificación del cliente": "901260586",
                "Código de desembolso": "CO:901260586:1:12:PAG",
                "Código de recaudo": "REC-001",
                "Fecha de pago": "2025-12-09",
                "Moneda": "USD",
                "Capital": 550.461,
                "Banco remitente": "Test Bank",
                "Médio de pago": "Pago en línea",
                "Tasa de cambio de FK/en línea": 3930.133136,
                "Spread": 50,
                "Total pagado [USD]": 550.461,
                "NT": "NT268",
                "4x1000": 0,
                "Fondo de garantías": 0,
                "IVA Fondo de garantías": 0,
                "Seguro + IVA": 0,
                "Intereses Corrientes": 0,
                "Intereses de Mora (Tasa corriente) PAR 60": 0,
                "Intereses de Mora (Tasa restante de mora) PAR 60": 0,
                "Intereses de Mora (Tasa corriente) PAR 61": 0,
                "Intereses de Mora (Tasa restante de mora) PAR 61": 0,
            },
            {
                "Cliente": "CARDIOFIT STORE SAS",
                "Identificación del cliente": "901260586",
                "Código de desembolso": "CO:901260586:1:12:PAG",
                "Código de recaudo": "REC-002",
                "Fecha de pago": "2025-12-09",
                "Moneda": "COP",  # Different currency, same exchange rate
                "Capital": 0,
                "Banco remitente": "Test Bank",
                "Médio de pago": "Pago en línea",
                "Tasa de cambio de FK/en línea": 3930.133136,  # Same exchange rate
                "Spread": 50,
                "Total pagado [USD]": 1.539,
                "NT": "NT268",
                "4x1000": 0,
                "Fondo de garantías": 0,
                "IVA Fondo de garantías": 0,
                "Seguro + IVA": 0,
                "Intereses Corrientes": 0,
                "Intereses de Mora (Tasa corriente) PAR 60": 1.464,  # MORATORIOS
                "Intereses de Mora (Tasa restante de mora) PAR 60": 0.075,
                "Intereses de Mora (Tasa corriente) PAR 61": 0,
                "Intereses de Mora (Tasa restante de mora) PAR 61": 0,
            },
        ]

        df = pd.DataFrame(data)
        df_columns_normalized = {col.lower().strip(): col for col in df.columns}

        # Collect payment group info
        group_info = service._collect_payment_group_info(
            df=df,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized
        )

        # Should only have one payment group (USD and COP rows combined)
        assert len(group_info) == 1, f"Expected 1 group, got {len(group_info)}"

        # Get the single group
        group_key = list(group_info.keys())[0]
        group = group_info[group_key]

        # Group should contain both CAPITAL and MORATORIOS concepts
        assert "CAPITAL" in group["concepts"], f"CAPITAL not in concepts: {group['concepts']}"
        assert "MORATORIOS" in group["concepts"], f"MORATORIOS not in concepts: {group['concepts']}"

        # Group total_pagado_usd should be sum of both rows
        expected_total_usd = 550.461 + 1.539
        assert abs(group["total_pagado_usd"] - expected_total_usd) < 0.01, \
            f"Expected total_pagado_usd ~{expected_total_usd}, got {group['total_pagado_usd']}"

    def test_multi_currency_group_no_separate_spread_line(self, service):
        """
        Test that when a payment group has mixed concepts (CAPITAL + MORATORIOS),
        no separate SPREAD line is created - spread goes to the column instead.

        This is the core bug fix validation.
        """
        # Test the group-level capital-only detection
        group_concepts_mixed = {"CAPITAL", "MORATORIOS"}

        result = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Pago en línea",
            group_concepts=group_concepts_mixed,
            country="colombia"
        )

        # Should NOT create separate spread line because group has non-CAPITAL concepts
        assert result is False, "Mixed concepts group should not create separate SPREAD line"

        # Test capital-only group (should create separate line)
        group_concepts_capital_only = {"CAPITAL"}

        result_capital_only = service._is_capital_only_pago_en_linea_for_group(
            medio_pago="Pago en línea",
            group_concepts=group_concepts_capital_only,
            country="colombia"
        )

        # Should create separate spread line because only CAPITAL
        assert result_capital_only is True, "Capital-only group should create separate SPREAD line"
