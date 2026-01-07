"""
Unit tests for Colombia Recompra AR Account Selection feature.

Tests the AR account selection logic when operations are repurchased (recomprada)
from Patrimonio Autónomo back to Fincargo Colombia.

AR Account Decision Matrix:
- NT empty → Fincargo Colombia accounts (302, 258, 1387)
- NT populated AND NOT recomprada → Patrimonio Autónomo accounts (304, 259, 310, 1474)
- NT populated AND recomprada → Fincargo Colombia accounts (302, 258, 1387)
"""
import pytest

from src.core.servicios.catalogs.payment_catalogs import (
    get_ar_account,
    COLOMBIA_AR_ACCOUNTS,
    COLOMBIA_NT_AR_ACCOUNTS,
    COLOMBIA_OPTIONAL_COLUMNS,
)


# ==================== Tests for get_ar_account with is_recomprada ====================

class TestGetArAccountRecompra:
    """Tests for the get_ar_account function with recompra parameter."""

    # ==================== Normal Operations (NT empty) ====================

    def test_normal_operation_capital_uses_fincargo_accounts(self):
        """Normal operation (NT empty) should use Fincargo Colombia CAPITAL account."""
        result = get_ar_account("CAPITAL", "colombia", is_nt=False, is_recomprada=False)
        assert result == 302  # Fincargo Colombia CAPITAL

    def test_normal_operation_intereses_uses_fincargo_accounts(self):
        """Normal operation (NT empty) should use Fincargo Colombia INTERESES account."""
        result = get_ar_account("INTERESES", "colombia", is_nt=False, is_recomprada=False)
        assert result == 258  # Fincargo Colombia INTERESES

    def test_normal_operation_seguros_uses_fincargo_accounts(self):
        """Normal operation (NT empty) should use Fincargo Colombia SEGUROS account."""
        result = get_ar_account("SEGUROS", "colombia", is_nt=False, is_recomprada=False)
        assert result == 1387  # Fincargo Colombia SEGUROS

    def test_normal_operation_costos_fijos_uses_fincargo_accounts(self):
        """Normal operation (NT empty) should use Fincargo Colombia COSTOS_FIJOS account."""
        result = get_ar_account("COSTOS_FIJOS", "colombia", is_nt=False, is_recomprada=False)
        assert result == 258  # Fincargo Colombia COSTOS_FIJOS

    def test_normal_operation_moratorios_uses_fincargo_accounts(self):
        """Normal operation (NT empty) should use Fincargo Colombia MORATORIOS account."""
        result = get_ar_account("MORATORIOS", "colombia", is_nt=False, is_recomprada=False)
        assert result == 258  # Fincargo Colombia MORATORIOS

    # ==================== Cedida Operations (NT populated, NOT recomprada) ====================

    def test_cedida_not_recomprada_capital_uses_patrimonio_accounts(self):
        """Cedida operation (NT populated, NOT recomprada) should use Patrimonio CAPITAL account."""
        result = get_ar_account("CAPITAL", "colombia", is_nt=True, is_recomprada=False)
        assert result == 304  # Patrimonio Autónomo CAPITAL

    def test_cedida_not_recomprada_intereses_uses_patrimonio_accounts(self):
        """Cedida operation (NT populated, NOT recomprada) should use Patrimonio INTERESES account."""
        result = get_ar_account("INTERESES", "colombia", is_nt=True, is_recomprada=False)
        assert result == 259  # Patrimonio Autónomo INTERESES

    def test_cedida_not_recomprada_seguros_uses_patrimonio_accounts(self):
        """Cedida operation (NT populated, NOT recomprada) should use Patrimonio SEGUROS account."""
        result = get_ar_account("SEGUROS", "colombia", is_nt=True, is_recomprada=False)
        assert result == 1474  # Patrimonio Autónomo SEGUROS

    def test_cedida_not_recomprada_costos_fijos_uses_patrimonio_accounts(self):
        """Cedida operation (NT populated, NOT recomprada) should use Patrimonio COSTOS_FIJOS account."""
        result = get_ar_account("COSTOS_FIJOS", "colombia", is_nt=True, is_recomprada=False)
        assert result == 310  # Patrimonio Autónomo COSTOS_FIJOS

    def test_cedida_not_recomprada_moratorios_uses_patrimonio_accounts(self):
        """Cedida operation (NT populated, NOT recomprada) should use Patrimonio MORATORIOS account."""
        result = get_ar_account("MORATORIOS", "colombia", is_nt=True, is_recomprada=False)
        assert result == 259  # Patrimonio Autónomo MORATORIOS

    # ==================== Recomprada Operations (NT populated AND recomprada) ====================

    def test_cedida_recomprada_capital_uses_fincargo_accounts(self):
        """Recomprada operation (NT populated + recomprada) should use Fincargo Colombia CAPITAL account."""
        result = get_ar_account("CAPITAL", "colombia", is_nt=True, is_recomprada=True)
        assert result == 302  # Fincargo Colombia CAPITAL (reverted from Patrimonio)

    def test_cedida_recomprada_intereses_uses_fincargo_accounts(self):
        """Recomprada operation (NT populated + recomprada) should use Fincargo Colombia INTERESES account."""
        result = get_ar_account("INTERESES", "colombia", is_nt=True, is_recomprada=True)
        assert result == 258  # Fincargo Colombia INTERESES (reverted from Patrimonio)

    def test_cedida_recomprada_seguros_uses_fincargo_accounts(self):
        """Recomprada operation (NT populated + recomprada) should use Fincargo Colombia SEGUROS account."""
        result = get_ar_account("SEGUROS", "colombia", is_nt=True, is_recomprada=True)
        assert result == 1387  # Fincargo Colombia SEGUROS (reverted from Patrimonio)

    def test_cedida_recomprada_costos_fijos_uses_fincargo_accounts(self):
        """Recomprada operation (NT populated + recomprada) should use Fincargo Colombia COSTOS_FIJOS account."""
        result = get_ar_account("COSTOS_FIJOS", "colombia", is_nt=True, is_recomprada=True)
        assert result == 258  # Fincargo Colombia COSTOS_FIJOS (reverted from Patrimonio)

    def test_cedida_recomprada_moratorios_uses_fincargo_accounts(self):
        """Recomprada operation (NT populated + recomprada) should use Fincargo Colombia MORATORIOS account."""
        result = get_ar_account("MORATORIOS", "colombia", is_nt=True, is_recomprada=True)
        assert result == 258  # Fincargo Colombia MORATORIOS (reverted from Patrimonio)

    # ==================== Mexico Operations (unaffected by recompra) ====================

    def test_mexico_unaffected_by_recompra_capital(self):
        """Mexico CAPITAL should be unaffected by is_recomprada parameter."""
        result_normal = get_ar_account("CAPITAL", "mexico", is_nt=False, is_recomprada=False)
        result_recomprada = get_ar_account("CAPITAL", "mexico", is_nt=False, is_recomprada=True)
        assert result_normal == 2114
        assert result_recomprada == 2114

    def test_mexico_unaffected_by_recompra_intereses(self):
        """Mexico INTERESES should be unaffected by is_recomprada parameter."""
        result_normal = get_ar_account("INTERESES", "mexico", is_nt=False, is_recomprada=False)
        result_recomprada = get_ar_account("INTERESES", "mexico", is_nt=False, is_recomprada=True)
        assert result_normal == 2115
        assert result_recomprada == 2115

    def test_mexico_unaffected_by_is_nt_and_recompra(self):
        """Mexico should be unaffected by both is_nt and is_recomprada parameters."""
        result = get_ar_account("CAPITAL", "mexico", is_nt=True, is_recomprada=True)
        assert result == 2114  # Mexico has no NT concept

    # ==================== Edge Cases ====================

    def test_recomprada_true_with_nt_false_uses_fincargo(self):
        """When is_nt=False but is_recomprada=True, should still use Fincargo accounts."""
        # This is an edge case - operation not cedida but marked as recomprada
        result = get_ar_account("CAPITAL", "colombia", is_nt=False, is_recomprada=True)
        assert result == 302  # Fincargo Colombia CAPITAL

    def test_unknown_concept_returns_none(self):
        """Unknown concept type should return None."""
        result = get_ar_account("UNKNOWN_CONCEPT", "colombia", is_nt=True, is_recomprada=True)
        assert result is None

    def test_default_parameters_maintain_backward_compatibility(self):
        """Default parameters (is_nt=False, is_recomprada=False) should work correctly."""
        result = get_ar_account("CAPITAL", "colombia")
        assert result == 302  # Fincargo Colombia (default behavior)


# ==================== Tests for Recompra Column Definition ====================

class TestRecompraColumnDefinition:
    """Tests for the recompra column definition in COLOMBIA_OPTIONAL_COLUMNS."""

    def test_recompra_column_defined(self):
        """Recompra column should be defined in COLOMBIA_OPTIONAL_COLUMNS."""
        assert "recompra" in COLOMBIA_OPTIONAL_COLUMNS

    def test_recompra_column_name_is_recomprado(self):
        """Recompra column should map to 'Recomprado' in source file."""
        assert COLOMBIA_OPTIONAL_COLUMNS["recompra"] == "Recomprado"


# ==================== Tests for All Concept Types ====================

class TestAllConceptTypesAffectedByRecompra:
    """Comprehensive test to verify all concept types are correctly affected by recompra."""

    @pytest.mark.parametrize("concept_type,fincargo_account,patrimonio_account", [
        ("CAPITAL", 302, 304),
        ("INTERESES", 258, 259),
        ("MORATORIOS", 258, 259),
        ("COSTOS_FIJOS", 258, 310),
        ("SEGUROS", 1387, 1474),
    ])
    def test_concept_type_ar_account_selection(
        self, concept_type, fincargo_account, patrimonio_account
    ):
        """
        Test AR account selection for each concept type across all scenarios:
        1. Normal (NT empty) → Fincargo
        2. Cedida not recomprada (NT populated, not recomprada) → Patrimonio
        3. Recomprada (NT populated, recomprada) → Fincargo
        """
        # Scenario 1: Normal operation
        normal_result = get_ar_account(concept_type, "colombia", is_nt=False, is_recomprada=False)
        assert normal_result == fincargo_account, f"{concept_type}: Normal should use Fincargo account"

        # Scenario 2: Cedida not recomprada
        cedida_result = get_ar_account(concept_type, "colombia", is_nt=True, is_recomprada=False)
        assert cedida_result == patrimonio_account, f"{concept_type}: Cedida should use Patrimonio account"

        # Scenario 3: Recomprada
        recomprada_result = get_ar_account(concept_type, "colombia", is_nt=True, is_recomprada=True)
        assert recomprada_result == fincargo_account, f"{concept_type}: Recomprada should revert to Fincargo account"
