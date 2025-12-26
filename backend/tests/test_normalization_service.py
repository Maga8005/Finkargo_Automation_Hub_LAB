"""
Unit tests for Normalization Service
Tests data normalization for fraud detection cross-validation
"""
import pytest

from src.core.servicios.risk.normalization_service import NormalizationService


class TestCompanyNameNormalization:
    """Test company name normalization"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_normalize_sas_variations(self, service):
        """Test normalization of S.A.S. variations"""
        # All these should normalize to the same value
        variations = [
            "AZELIS COLOMBIA S.A.S.",
            "AZELIS COLOMBIA S.A.S",
            "AZELIS COLOMBIA SAS",
            "AZELIS COLOMBIA S A S",
            "AZELIS COLOMBIA S. A. S.",
        ]

        expected = "AZELIS COLOMBIA"
        for variant in variations:
            result = service.normalize_company_name(variant)
            assert result == expected, f"Failed for variant: '{variant}' -> '{result}'"

    def test_normalize_sa_variations(self, service):
        """Test normalization of S.A. variations"""
        variations = [
            "ROCSA COLOMBIA S.A.",
            "ROCSA COLOMBIA S.A",
            "ROCSA COLOMBIA SA",
            "ROCSA COLOMBIA S A",
        ]

        expected = "ROCSA COLOMBIA"
        for variant in variations:
            result = service.normalize_company_name(variant)
            assert result == expected, f"Failed for variant: '{variant}' -> '{result}'"

    def test_normalize_ltda_variations(self, service):
        """Test normalization of LTDA variations"""
        variations = [
            "EMPRESA EJEMPLO LTDA.",
            "EMPRESA EJEMPLO LTDA",
            "EMPRESA EJEMPLO LIMITADA",
        ]

        expected = "EMPRESA EJEMPLO"
        for variant in variations:
            result = service.normalize_company_name(variant)
            assert result == expected, f"Failed for variant: '{variant}' -> '{result}'"

    def test_normalize_eu_variations(self, service):
        """Test normalization of E.U. variations"""
        variations = [
            "CONSULTORIA E.U.",
            "CONSULTORIA E.U",
            "CONSULTORIA EU",
            "CONSULTORIA E U",
        ]

        expected = "CONSULTORIA"
        for variant in variations:
            result = service.normalize_company_name(variant)
            assert result == expected, f"Failed for variant: '{variant}' -> '{result}'"

    def test_normalize_multiple_suffixes(self, service):
        """Test normalization of malformed data with multiple suffixes"""
        # Edge case: company with multiple legal suffixes (malformed data)
        result = service.normalize_company_name("EMPRESA S.A.S. LTDA.")
        assert result == "EMPRESA"

    def test_normalize_company_with_accents(self, service):
        """Test normalization preserves meaning while removing accents"""
        result = service.normalize_company_name("QUÍMICOS INDUSTRIALES S.A.S.")
        assert result == "QUIMICOS INDUSTRIALES"

    def test_normalize_cia_variations(self, service):
        """Test normalization of Y CIA variations"""
        variations = [
            "PEREZ Y CIA.",
            "PEREZ Y CIA",
            "PEREZ & CIA.",
            "PEREZ & CIA",
        ]

        for variant in variations:
            result = service.normalize_company_name(variant)
            assert "PEREZ" in result, f"Failed for variant: '{variant}'"
            assert "CIA" not in result, f"CIA not removed for: '{variant}'"

    def test_normalize_empty_input(self, service):
        """Test normalization of empty or None input"""
        assert service.normalize_company_name("") == ""
        assert service.normalize_company_name(None) == ""

    def test_normalize_whitespace(self, service):
        """Test normalization handles extra whitespace"""
        result = service.normalize_company_name("  AZELIS   COLOMBIA   S.A.S.  ")
        assert result == "AZELIS COLOMBIA"


class TestNITNormalization:
    """Test NIT normalization"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_normalize_nit_with_dots_and_dash(self, service):
        """Test NIT with dots and dash format"""
        base, check = service.normalize_nit("830.027.231-3")
        assert base == "830027231"
        assert check == "3"

    def test_normalize_nit_with_spaces(self, service):
        """Test NIT with space before check digit"""
        base, check = service.normalize_nit("830027231 3")
        assert base == "830027231"
        assert check == "3"

    def test_normalize_nit_with_dash_only(self, service):
        """Test NIT with dash only"""
        base, check = service.normalize_nit("830027231-1")
        assert base == "830027231"
        assert check == "1"

    def test_normalize_nit_without_check_digit(self, service):
        """Test NIT without check digit"""
        base, check = service.normalize_nit("830027231")
        assert base == "830027231"
        assert check is None

    def test_normalize_nit_various_formats(self, service):
        """Test that all NIT formats normalize to same base"""
        nit_formats = [
            "830.027.231-3",
            "830027231-3",
            "830027231 3",
            "830.027.231 3",
        ]

        expected_base = "830027231"
        expected_check = "3"

        for nit in nit_formats:
            base, check = service.normalize_nit(nit)
            assert base == expected_base, f"Failed for NIT: '{nit}'"
            assert check == expected_check, f"Check digit failed for NIT: '{nit}'"

    def test_normalize_nit_empty(self, service):
        """Test NIT normalization with empty input"""
        base, check = service.normalize_nit("")
        assert base == ""
        assert check is None

    def test_normalize_nit_none(self, service):
        """Test NIT normalization with None input"""
        base, check = service.normalize_nit(None)
        assert base == ""
        assert check is None


class TestNITEquivalence:
    """Test NIT equivalence comparison"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_nits_equivalent_formatting_only(self, service):
        """Test NITs that differ only in formatting are equivalent"""
        is_match, reason, discrepancy = service.are_nits_equivalent(
            "830.027.231-3",
            "830027231-3"
        )
        assert is_match is True
        assert discrepancy is None

    def test_nits_different_check_digits(self, service):
        """Test NITs with different check digits"""
        is_match, reason, discrepancy = service.are_nits_equivalent(
            "830027231-3",
            "830027231-1"
        )
        # Base matches, but check digit differs
        assert is_match is True  # Still considered a match for base
        assert discrepancy == "check_digit"
        assert "diferentes" in reason.lower()

    def test_nits_different_base(self, service):
        """Test NITs with different base numbers"""
        is_match, reason, discrepancy = service.are_nits_equivalent(
            "830027231-3",
            "900123456-7"
        )
        assert is_match is False
        assert discrepancy == "base_nit"

    def test_nits_empty_input(self, service):
        """Test NIT equivalence with empty input"""
        is_match, reason, discrepancy = service.are_nits_equivalent("", "830027231")
        assert is_match is False
        assert discrepancy == "base_nit"


class TestCityNormalization:
    """Test city name normalization"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_normalize_city_with_department(self, service):
        """Test city with parenthetical department info"""
        result = service.normalize_city("Tenjo (Cundinamarca)")
        assert result == "TENJO"

    def test_normalize_bogota_variations(self, service):
        """Test Bogotá variations"""
        variations = [
            "Bogotá D.C.",
            "BOGOTA DC",
            "Bogotá",
            "BOGOTA D.C",
        ]

        for variant in variations:
            result = service.normalize_city(variant)
            assert result == "BOGOTA", f"Failed for: '{variant}' -> '{result}'"

    def test_normalize_medellin_accents(self, service):
        """Test Medellín accent removal"""
        result = service.normalize_city("MEDELLÍN")
        assert result == "MEDELLIN"

    def test_normalize_cartagena_de_indias(self, service):
        """Test Cartagena de Indias normalization"""
        result = service.normalize_city("Cartagena de Indias")
        assert result == "CARTAGENA"

    def test_normalize_city_empty(self, service):
        """Test city normalization with empty input"""
        assert service.normalize_city("") == ""
        assert service.normalize_city(None) == ""


class TestPersonNameNormalization:
    """Test person name normalization"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_normalize_name_with_accents(self, service):
        """Test name with Spanish accents"""
        result = service.normalize_person_name("MARÍA JOSÉ GARCÍA")
        assert result == "MARIA JOSE GARCIA"

    def test_normalize_name_whitespace(self, service):
        """Test name with extra whitespace"""
        result = service.normalize_person_name("  Juan   Carlos  ")
        assert result == "JUAN CARLOS"

    def test_normalize_name_case(self, service):
        """Test name case normalization"""
        result = service.normalize_person_name("juan carlos rodriguez")
        assert result == "JUAN CARLOS RODRIGUEZ"

    def test_normalize_name_empty(self, service):
        """Test name normalization with empty input"""
        assert service.normalize_person_name("") == ""
        assert service.normalize_person_name(None) == ""


class TestEmailNormalization:
    """Test email normalization"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_normalize_email_lowercase(self, service):
        """Test email is lowercased"""
        result = service.normalize_email("User@EXAMPLE.COM")
        assert result == "user@example.com"

    def test_normalize_email_whitespace(self, service):
        """Test email whitespace handling"""
        result = service.normalize_email("  user@example.com  ")
        assert result == "user@example.com"

    def test_extract_email_domain(self, service):
        """Test domain extraction"""
        result = service.extract_email_domain("user@azelis.com")
        assert result == "azelis.com"

    def test_extract_email_domain_invalid(self, service):
        """Test domain extraction with invalid email"""
        assert service.extract_email_domain("invalid-email") is None
        assert service.extract_email_domain("") is None
        assert service.extract_email_domain(None) is None


class TestStringSimilarity:
    """Test string similarity calculation"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_identical_strings_return_one(self, service):
        """Test identical strings return similarity of 1.0"""
        result = service.calculate_similarity("AZELIS", "AZELIS")
        assert result == 1.0

    def test_identical_strings_case_insensitive(self, service):
        """Test identical strings with different case return 1.0"""
        result = service.calculate_similarity("Azelis", "AZELIS")
        assert result == 1.0

    def test_completely_different_strings(self, service):
        """Test completely different strings return low similarity"""
        result = service.calculate_similarity("ABCD", "WXYZ")
        assert result < 0.5

    def test_similar_strings_typosquatting(self, service):
        """Test similar strings return medium-high similarity (e.g., AZELIS vs ACELIS)"""
        result = service.calculate_similarity("AZELIS", "ACELIS")
        # Single character difference should yield ~0.8-0.9 similarity
        assert 0.8 <= result <= 0.95

    def test_empty_first_string(self, service):
        """Test empty first string returns 0.0"""
        result = service.calculate_similarity("", "AZELIS")
        assert result == 0.0

    def test_empty_second_string(self, service):
        """Test empty second string returns 0.0"""
        result = service.calculate_similarity("AZELIS", "")
        assert result == 0.0

    def test_both_empty_strings(self, service):
        """Test both empty strings return 0.0"""
        result = service.calculate_similarity("", "")
        assert result == 0.0

    def test_none_first_string(self, service):
        """Test None first string returns 0.0"""
        result = service.calculate_similarity(None, "AZELIS")
        assert result == 0.0

    def test_none_second_string(self, service):
        """Test None second string returns 0.0"""
        result = service.calculate_similarity("AZELIS", None)
        assert result == 0.0

    def test_partial_match(self, service):
        """Test partial match returns medium similarity"""
        result = service.calculate_similarity("AZELIS COLOMBIA", "AZELIS MEXICO")
        # Partial match should be between 0.5 and 0.9
        assert 0.5 < result < 0.9


class TestNormalizeNameAlias:
    """Test normalize_name alias method"""

    @pytest.fixture
    def service(self):
        """Create NormalizationService instance"""
        return NormalizationService()

    def test_normalize_name_same_as_normalize_person_name(self, service):
        """Test normalize_name returns same result as normalize_person_name"""
        test_names = [
            "MARÍA JOSÉ GARCÍA",
            "  Juan   Carlos  ",
            "juan carlos rodriguez",
            "",
            None,
        ]

        for name in test_names:
            result_alias = service.normalize_name(name)
            result_original = service.normalize_person_name(name)
            assert result_alias == result_original, f"Results differ for: '{name}'"

    def test_normalize_name_with_accents(self, service):
        """Test normalize_name handles accents correctly"""
        result = service.normalize_name("JOSÉ PÉREZ MUÑOZ")
        assert result == "JOSE PEREZ MUNOZ"

    def test_normalize_name_with_special_chars(self, service):
        """Test normalize_name removes special characters"""
        result = service.normalize_name("Juan Carlos Jr.")
        assert result == "JUAN CARLOS JR"
