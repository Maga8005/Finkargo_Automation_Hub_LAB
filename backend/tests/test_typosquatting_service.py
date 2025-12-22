"""
Unit tests for Typosquatting Detection Service
Tests domain similarity and typosquatting detection
"""
import pytest

from src.core.servicios.risk.typosquatting_service import TyposquattingService


class TestTyposquattingDetection:
    """Test typosquatting detection"""

    @pytest.fixture
    def service(self):
        """Create TyposquattingService instance"""
        return TyposquattingService()

    def test_detect_acelis_vs_azelis(self, service):
        """Test detection of Azelis fraud case pattern"""
        # The actual fraud case: acelis.com.co vs azelis.com
        result = service.check_domain_typosquatting("acelis.com.co", ["azelis.com"])

        assert result.is_suspicious is True
        assert result.detection_type == "typosquatting"
        assert result.similar_domain == "azelis.com"
        assert result.similarity_score > 0.7
        assert result.levenshtein_distance <= 2

    def test_detect_tld_variation(self, service):
        """Test detection of TLD variations"""
        # Same company, different TLD
        result = service.check_domain_typosquatting("azelis.com.co", ["azelis.com"])

        assert result.is_suspicious is True
        assert result.detection_type == "tld_variation"
        assert result.similar_domain == "azelis.com"

    def test_exact_match_not_suspicious(self, service):
        """Test that exact match is not flagged"""
        result = service.check_domain_typosquatting("azelis.com", ["azelis.com"])

        assert result.is_suspicious is False
        # When checking a domain against itself, it's not suspicious
        # The detection_type may be 'no_match' or 'exact_match' depending on logic
        assert result.detection_type in ("exact_match", "no_match")

    def test_completely_different_domain(self, service):
        """Test that completely different domains are not flagged"""
        result = service.check_domain_typosquatting("google.com", ["azelis.com"])

        assert result.is_suspicious is False
        assert result.detection_type == "no_match"

    def test_detect_california_davis_typosquatting(self, service):
        """Test detection of similar domain names"""
        # Adding 'inc' to the domain
        result = service.check_domain_typosquatting(
            "californiadavisinc.com",
            ["californiadavis.com"]
        )

        # Should be detected due to high similarity
        assert result.similarity_score > 0.7

    def test_default_known_domains(self, service):
        """Test that default known domains are checked"""
        # Check against default list (includes azelis.com)
        result = service.check_domain_typosquatting("acelis.com")

        assert result.is_suspicious is True
        assert "azelis" in result.similar_domain.lower()

    def test_company_derived_domain(self, service):
        """Test domain derived from company name"""
        result = service.check_domain_typosquatting(
            "aselis.com",
            company_name="AZELIS COLOMBIA S.A.S."
        )

        # Should detect similarity to derived 'azelis.com'
        assert result.is_suspicious is True


class TestLevenshteinDistance:
    """Test Levenshtein distance calculation"""

    @pytest.fixture
    def service(self):
        """Create TyposquattingService instance"""
        return TyposquattingService()

    def test_identical_strings(self, service):
        """Test distance for identical strings"""
        assert service.calculate_levenshtein_distance("azelis", "azelis") == 0

    def test_single_substitution(self, service):
        """Test single character substitution"""
        # z -> c
        assert service.calculate_levenshtein_distance("azelis", "acelis") == 1

    def test_single_insertion(self, service):
        """Test single character insertion"""
        assert service.calculate_levenshtein_distance("azelis", "azzelis") == 1

    def test_single_deletion(self, service):
        """Test single character deletion"""
        assert service.calculate_levenshtein_distance("azelis", "azlis") == 1

    def test_multiple_edits(self, service):
        """Test multiple edits"""
        assert service.calculate_levenshtein_distance("azelis", "basf") > 2

    def test_empty_strings(self, service):
        """Test with empty strings"""
        assert service.calculate_levenshtein_distance("", "") == 0
        assert service.calculate_levenshtein_distance("azelis", "") == 6
        assert service.calculate_levenshtein_distance("", "azelis") == 6


class TestSimilarity:
    """Test similarity calculation"""

    @pytest.fixture
    def service(self):
        """Create TyposquattingService instance"""
        return TyposquattingService()

    def test_identical_strings_similarity(self, service):
        """Test similarity for identical strings"""
        assert service.calculate_similarity("azelis", "azelis") == 1.0

    def test_similar_strings(self, service):
        """Test similarity for similar strings"""
        similarity = service.calculate_similarity("azelis", "acelis")
        assert 0.7 < similarity < 1.0

    def test_different_strings(self, service):
        """Test similarity for different strings"""
        similarity = service.calculate_similarity("azelis", "google")
        assert similarity < 0.5

    def test_empty_strings_similarity(self, service):
        """Test similarity with empty strings"""
        assert service.calculate_similarity("", "") == 0.0
        assert service.calculate_similarity("azelis", "") == 0.0


class TestDomainBasExtraction:
    """Test domain base extraction"""

    @pytest.fixture
    def service(self):
        """Create TyposquattingService instance"""
        return TyposquattingService()

    def test_extract_simple_domain(self, service):
        """Test extracting base from simple domain"""
        assert service.extract_domain_base("azelis.com") == "azelis"

    def test_extract_compound_tld(self, service):
        """Test extracting base from compound TLD"""
        assert service.extract_domain_base("azelis.com.co") == "azelis"
        assert service.extract_domain_base("azelis.com.mx") == "azelis"

    def test_extract_country_tld(self, service):
        """Test extracting base from country TLD"""
        assert service.extract_domain_base("azelis.co") == "azelis"

    def test_extract_subdomain(self, service):
        """Test extracting base from subdomain"""
        # When there's a subdomain, get the main domain
        result = service.extract_domain_base("mail.azelis.com")
        # Should be 'azelis', not 'mail'
        assert "azelis" in result or result == "azelis"


class TestFreeEmailProviders:
    """Test free email provider detection"""

    @pytest.fixture
    def service(self):
        """Create TyposquattingService instance"""
        return TyposquattingService()

    def test_detect_gmail(self, service):
        """Test Gmail detection"""
        assert service.is_free_email_provider("gmail.com") is True

    def test_detect_hotmail(self, service):
        """Test Hotmail detection"""
        assert service.is_free_email_provider("hotmail.com") is True

    def test_detect_outlook(self, service):
        """Test Outlook detection"""
        assert service.is_free_email_provider("outlook.com") is True

    def test_detect_yahoo(self, service):
        """Test Yahoo detection"""
        assert service.is_free_email_provider("yahoo.com") is True

    def test_corporate_domain_not_free(self, service):
        """Test corporate domain is not flagged"""
        assert service.is_free_email_provider("azelis.com") is False

    def test_empty_domain(self, service):
        """Test empty domain handling"""
        assert service.is_free_email_provider("") is False
        assert service.is_free_email_provider(None) is False


class TestTLDVariations:
    """Test TLD variation detection"""

    @pytest.fixture
    def service(self):
        """Create TyposquattingService instance"""
        return TyposquattingService()

    def test_get_variations_for_com(self, service):
        """Test TLD variations for .com"""
        variations = service.get_tld_variations("azelis.com")

        assert "azelis.com.co" in variations
        assert "azelis.com.mx" in variations

    def test_get_variations_for_com_co(self, service):
        """Test TLD variations for .com.co"""
        variations = service.get_tld_variations("azelis.com.co")

        assert "azelis.com" in variations

    def test_similar_domains(self, service):
        """Test is_similar_domain function"""
        is_similar, score = service.is_similar_domain("acelis.com", "azelis.com")
        assert is_similar is True
        assert score > 0.7

        is_similar, score = service.is_similar_domain("google.com", "azelis.com")
        assert is_similar is False


class TestSuspiciousTLD:
    """Test suspicious TLD detection"""

    @pytest.fixture
    def service(self):
        """Create TyposquattingService instance"""
        return TyposquattingService()

    def test_detect_suspicious_xyz(self, service):
        """Test detection of .xyz TLD"""
        result = service.check_domain_typosquatting("example.xyz")
        # Should flag suspicious TLD even if no typosquatting
        assert result.is_suspicious is True
        assert result.detection_type == "suspicious_tld"

    def test_detect_suspicious_tk(self, service):
        """Test detection of .tk TLD"""
        result = service.check_domain_typosquatting("example.tk")
        assert result.is_suspicious is True

    def test_normal_tld_not_flagged(self, service):
        """Test that normal TLDs are not flagged for TLD alone"""
        result = service.check_domain_typosquatting("uniquecompanyname123.com")
        # Only suspicious TLDs should be flagged, not just any .com
        assert result.detection_type != "suspicious_tld"
