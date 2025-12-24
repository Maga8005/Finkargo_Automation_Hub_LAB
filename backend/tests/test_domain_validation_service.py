"""
Unit tests for DomainValidationService

Tests DNS lookup, WHOIS lookup, domain age validation, and caching functionality.
Uses mocks for network calls to ensure reliable, fast tests.
"""
import pytest
import socket
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.core.servicios.risk.domain_validation_service import (
    DomainValidationService,
    DomainCache,
    DomainExistenceResult,
    DomainAgeResult,
    DomainCompanyAgeComparison,
)


# ==================== DomainCache Tests ====================

class TestDomainCache:
    """Tests for the DomainCache class."""

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = DomainCache(ttl=3600)
        result = DomainAgeResult(
            domain="example.com",
            creation_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
            age_days=1500,
            lookup_status="success"
        )

        cache.set("example.com", result)
        cached = cache.get("example.com")

        assert cached is not None
        assert cached.domain == "example.com"
        assert cached.age_days == 1500

    def test_cache_miss(self):
        """Test cache returns None for unknown domain."""
        cache = DomainCache()
        result = cache.get("unknown.com")
        assert result is None

    def test_cache_clear(self):
        """Test cache clear operation."""
        cache = DomainCache()
        result = DomainAgeResult(domain="test.com", lookup_status="success")
        cache.set("test.com", result)

        cache.clear()
        assert cache.get("test.com") is None


# ==================== DomainValidationService Tests ====================

class TestDomainValidationService:
    """Tests for the DomainValidationService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = DomainValidationService()

    # ==================== DNS Lookup Tests ====================

    @patch('socket.gethostbyname')
    def test_existing_domain_resolves(self, mock_dns):
        """Test that an existing domain returns exists=True."""
        mock_dns.return_value = "142.250.190.78"

        result = self.service.check_domain_existence("google.com")

        assert result.exists is True
        assert result.ip_address == "142.250.190.78"
        assert result.error_message is None
        mock_dns.assert_called_once_with("google.com")

    @patch('socket.gethostbyname')
    def test_nonexistent_domain_fails(self, mock_dns):
        """Test that a non-existent domain returns exists=False."""
        mock_dns.side_effect = socket.gaierror(11001, 'getaddrinfo failed')

        result = self.service.check_domain_existence("thisisnotarealdomain12345.com")

        assert result.exists is False
        assert result.ip_address is None
        assert result.error_message is not None
        assert "no resuelve" in result.error_message.lower()

    @patch('socket.gethostbyname')
    def test_dns_timeout_handled_gracefully(self, mock_dns):
        """Test that DNS timeout is handled gracefully."""
        mock_dns.side_effect = socket.timeout("DNS timeout")

        result = self.service.check_domain_existence("slow-domain.com")

        # On timeout, assume exists to avoid false negatives
        assert result.exists is True
        assert "timeout" in result.error_message.lower()

    def test_invalid_domain_format_returns_false(self):
        """Test that invalid domain format returns early without network call."""
        invalid_domains = [
            "",
            "   ",
            "a",
            "no-tld",
            "has spaces.com",
            "invalid..domain.com",
            "-startwithhyphen.com",
        ]

        for domain in invalid_domains:
            result = self.service.check_domain_existence(domain)
            assert result.exists is False
            assert "inválido" in result.error_message.lower()

    # ==================== WHOIS Lookup Tests ====================

    @patch('src.core.servicios.risk.domain_validation_service.whois')
    @patch('src.core.servicios.risk.domain_validation_service.WHOIS_AVAILABLE', True)
    def test_whois_returns_creation_date(self, mock_whois):
        """Test WHOIS lookup returns creation date correctly."""
        mock_response = Mock()
        mock_response.creation_date = datetime(2015, 6, 15, tzinfo=timezone.utc)
        mock_response.registrar = "GoDaddy"
        mock_whois.whois.return_value = mock_response

        result = self.service.get_domain_age("example.com")

        assert result.lookup_status == "success"
        assert result.creation_date == datetime(2015, 6, 15, tzinfo=timezone.utc)
        assert result.registrar == "GoDaddy"
        assert result.age_days is not None
        assert result.age_days > 0

    @patch('src.core.servicios.risk.domain_validation_service.whois')
    @patch('src.core.servicios.risk.domain_validation_service.WHOIS_AVAILABLE', True)
    def test_whois_failure_handled_gracefully(self, mock_whois):
        """Test WHOIS failure is handled gracefully."""
        mock_whois.whois.side_effect = Exception("WHOIS server error")

        result = self.service.get_domain_age("failing-whois.com")

        assert result.lookup_status == "failed"
        assert result.creation_date is None
        assert result.error_message is not None

    @patch('src.core.servicios.risk.domain_validation_service.whois')
    @patch('src.core.servicios.risk.domain_validation_service.WHOIS_AVAILABLE', True)
    def test_whois_privacy_handled(self, mock_whois):
        """Test that privacy-protected WHOIS returns unavailable status."""
        mock_whois.whois.side_effect = Exception("No WHOIS data available")

        result = self.service.get_domain_age("private-domain.com")

        assert result.lookup_status == "unavailable"
        assert result.creation_date is None

    @patch('src.core.servicios.risk.domain_validation_service.whois')
    @patch('src.core.servicios.risk.domain_validation_service.WHOIS_AVAILABLE', True)
    def test_whois_list_of_dates(self, mock_whois):
        """Test WHOIS with multiple creation dates takes earliest."""
        mock_response = Mock()
        mock_response.creation_date = [
            datetime(2018, 1, 1, tzinfo=timezone.utc),
            datetime(2015, 6, 15, tzinfo=timezone.utc),  # Earlier
            datetime(2020, 12, 31, tzinfo=timezone.utc),
        ]
        mock_response.registrar = "Namecheap"
        mock_whois.whois.return_value = mock_response

        result = self.service.get_domain_age("multi-date.com")

        assert result.lookup_status == "success"
        # Should use earliest date
        assert result.creation_date == datetime(2015, 6, 15, tzinfo=timezone.utc)

    # ==================== Cache Tests ====================

    @patch('src.core.servicios.risk.domain_validation_service.whois')
    @patch('src.core.servicios.risk.domain_validation_service.WHOIS_AVAILABLE', True)
    def test_cache_works(self, mock_whois):
        """Test that second call returns cached result without network call."""
        mock_response = Mock()
        mock_response.creation_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        mock_response.registrar = "Test Registrar"
        mock_whois.whois.return_value = mock_response

        # First call
        result1 = self.service.get_domain_age("cached-domain.com")
        assert result1.lookup_status == "success"
        assert mock_whois.whois.call_count == 1

        # Second call should use cache
        result2 = self.service.get_domain_age("cached-domain.com")
        assert result2.lookup_status == "success"
        assert result2.creation_date == result1.creation_date
        # WHOIS should NOT be called again
        assert mock_whois.whois.call_count == 1

    # ==================== Domain Age Comparison Tests ====================

    @patch.object(DomainValidationService, 'check_domain_existence')
    @patch.object(DomainValidationService, 'get_domain_age')
    def test_nonexistent_domain_is_critical(self, mock_age, mock_existence):
        """Test non-existent domain returns CRITICAL severity."""
        mock_existence.return_value = DomainExistenceResult(
            domain="fake.com",
            exists=False,
            error_message="Domain does not resolve"
        )

        result = self.service.compare_domain_vs_company_age("fake.com")

        assert result.is_suspicious is True
        assert result.severity == "critical"
        assert result.score_impact == 25
        assert "no existe" in result.reason.lower()

    @patch.object(DomainValidationService, 'check_domain_existence')
    @patch.object(DomainValidationService, 'get_domain_age')
    def test_young_domain_vs_old_company_flagged(self, mock_age, mock_existence):
        """Test domain < 90 days is HIGH severity regardless of company age."""
        mock_existence.return_value = DomainExistenceResult(
            domain="new-domain.com",
            exists=True
        )
        mock_age.return_value = DomainAgeResult(
            domain="new-domain.com",
            creation_date=datetime.now(timezone.utc) - timedelta(days=30),
            age_days=30,
            lookup_status="success"
        )

        # Company is 10 years old
        company_date = datetime.now(timezone.utc) - timedelta(days=3650)

        result = self.service.compare_domain_vs_company_age(
            "new-domain.com",
            company_constitution_date=company_date
        )

        assert result.is_suspicious is True
        assert result.severity == "high"
        assert result.score_impact == 15
        assert "30 días" in result.reason

    @patch.object(DomainValidationService, 'check_domain_existence')
    @patch.object(DomainValidationService, 'get_domain_age')
    def test_old_domain_ok(self, mock_age, mock_existence):
        """Test domain > 5 years returns no issues."""
        mock_existence.return_value = DomainExistenceResult(
            domain="established.com",
            exists=True
        )
        mock_age.return_value = DomainAgeResult(
            domain="established.com",
            creation_date=datetime.now(timezone.utc) - timedelta(days=2000),
            age_days=2000,
            lookup_status="success"
        )

        company_date = datetime.now(timezone.utc) - timedelta(days=3000)

        result = self.service.compare_domain_vs_company_age(
            "established.com",
            company_constitution_date=company_date
        )

        assert result.is_suspicious is False
        assert result.severity is None
        assert result.score_impact == 0

    @patch.object(DomainValidationService, 'check_domain_existence')
    @patch.object(DomainValidationService, 'get_domain_age')
    def test_domain_young_vs_company_age_ratio(self, mock_age, mock_existence):
        """Test domain < 1 year and < 10% of company age is HIGH severity."""
        mock_existence.return_value = DomainExistenceResult(
            domain="suspicious.com",
            exists=True
        )
        # Domain is 200 days old
        mock_age.return_value = DomainAgeResult(
            domain="suspicious.com",
            creation_date=datetime.now(timezone.utc) - timedelta(days=200),
            age_days=200,
            lookup_status="success"
        )

        # Company is 15 years old (5475 days)
        # 200 / 5475 = 3.6% < 10% threshold
        company_date = datetime.now(timezone.utc) - timedelta(days=5475)

        result = self.service.compare_domain_vs_company_age(
            "suspicious.com",
            company_constitution_date=company_date
        )

        assert result.is_suspicious is True
        assert result.severity == "high"
        assert result.score_impact == 15

    @patch.object(DomainValidationService, 'check_domain_existence')
    @patch.object(DomainValidationService, 'get_domain_age')
    def test_young_domain_no_company_date_is_medium(self, mock_age, mock_existence):
        """Test domain < 1 year with no company date is MEDIUM severity."""
        mock_existence.return_value = DomainExistenceResult(
            domain="unknown-company.com",
            exists=True
        )
        mock_age.return_value = DomainAgeResult(
            domain="unknown-company.com",
            creation_date=datetime.now(timezone.utc) - timedelta(days=200),
            age_days=200,
            lookup_status="success"
        )

        # No company dates provided
        result = self.service.compare_domain_vs_company_age("unknown-company.com")

        assert result.is_suspicious is True
        assert result.severity == "medium"
        assert result.score_impact == 8

    @patch.object(DomainValidationService, 'check_domain_existence')
    @patch.object(DomainValidationService, 'get_domain_age')
    def test_whois_unavailable_no_penalty(self, mock_age, mock_existence):
        """Test that WHOIS unavailable returns no penalty."""
        mock_existence.return_value = DomainExistenceResult(
            domain="private.com",
            exists=True
        )
        mock_age.return_value = DomainAgeResult(
            domain="private.com",
            lookup_status="unavailable",
            error_message="Privacy protection enabled"
        )

        result = self.service.compare_domain_vs_company_age("private.com")

        assert result.is_suspicious is False
        assert result.severity is None
        assert result.score_impact == 0

    # ==================== Domain Format Validation Tests ====================

    def test_valid_domain_formats(self):
        """Test various valid domain formats are accepted."""
        valid_domains = [
            "google.com",
            "sub.domain.co.uk",
            "example.com.co",
            "my-domain.org",
            "a1b2c3.net",
        ]

        for domain in valid_domains:
            assert self.service._validate_domain_format(domain) is True

    def test_invalid_domain_formats(self):
        """Test various invalid domain formats are rejected."""
        invalid_domains = [
            "",
            None,
            "   ",
            "nodot",
            ".com",
            "-.com",
            "has space.com",
            "double..dot.com",
            "a" * 300 + ".com",  # Too long
        ]

        for domain in invalid_domains:
            assert self.service._validate_domain_format(domain) is False


# ==================== Integration-style Tests (with real DNS) ====================

class TestDomainValidationIntegration:
    """
    Optional integration tests using real network calls.
    These are skipped by default - run with pytest -m integration.
    """

    @pytest.mark.integration
    def test_real_dns_lookup(self):
        """Test real DNS lookup for known domain."""
        service = DomainValidationService()
        result = service.check_domain_existence("google.com")

        assert result.exists is True
        assert result.ip_address is not None

    @pytest.mark.integration
    def test_real_whois_lookup(self):
        """Test real WHOIS lookup for known domain."""
        # Import to check if whois is available
        from src.core.servicios.risk.domain_validation_service import WHOIS_AVAILABLE
        if not WHOIS_AVAILABLE:
            pytest.skip("whois module not installed")

        service = DomainValidationService()
        result = service.get_domain_age("google.com")

        # Google.com should have WHOIS data available
        assert result.lookup_status in ["success", "unavailable"]
        if result.lookup_status == "success":
            assert result.creation_date is not None
            assert result.age_days > 5000  # Google is very old
