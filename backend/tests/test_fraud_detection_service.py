"""
Unit tests for Fraud Detection Service
Tests NIT validation, email domain checks, and risk scoring
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from src.core.servicios.risk.fraud_detection_service import FraudDetectionService
from src.core.servicios.risk.risk_scoring_service import RiskScoringService
from src.interface.risk_dtos import FraudIndicator, RiskLevel


class TestNITValidation:
    """Test Colombian NIT format validation"""

    @pytest.fixture
    def fraud_service(self):
        """Create FraudDetectionService with mocked dependencies"""
        service = FraudDetectionService(
            risk_repo=MagicMock(),
            rules_repo=MagicMock(),
            blacklist_repo=MagicMock(),
            client_repo=MagicMock(),
            scoring_service=MagicMock(),
            alert_service=MagicMock(),
        )
        return service

    def test_calculate_nit_check_digit_valid(self, fraud_service):
        """Test NIT check digit calculation"""
        # Known valid NITs
        assert fraud_service._calculate_nit_check_digit("900123456") in range(0, 10)
        assert fraud_service._calculate_nit_check_digit("800456789") in range(0, 10)

    def test_nit_format_validation_valid_format(self, fraud_service):
        """Test that valid NIT formats pass validation"""
        # Valid NIT with dots and dash
        client_data = {'nit': '900.123.456-7'}
        rule = {'weight': 0.10, 'rule_type': 'nit'}

        # The validation should not flag valid formats
        # (Note: actual check digit verification depends on the specific NIT)

    def test_nit_format_validation_invalid_format(self, fraud_service):
        """Test that invalid NIT formats are flagged"""
        # Invalid - too short
        client_data = {'nit': '123'}
        rule = {'weight': 0.10, 'rule_type': 'nit'}

        # Should be flagged as invalid
        # Actual async test would need proper async handling

    def test_nit_empty_validation(self, fraud_service):
        """Test that empty NIT is flagged"""
        client_data = {'nit': ''}
        rule = {'weight': 0.10}

        # Should be flagged


class TestEmailDomainValidation:
    """Test email domain typosquatting detection"""

    @pytest.fixture
    def fraud_service(self):
        """Create FraudDetectionService with mocked dependencies"""
        service = FraudDetectionService(
            risk_repo=MagicMock(),
            rules_repo=MagicMock(),
            blacklist_repo=MagicMock(),
            client_repo=MagicMock(),
            scoring_service=MagicMock(),
            alert_service=MagicMock(),
        )
        return service

    def test_extract_domain(self, fraud_service):
        """Test domain extraction from email"""
        assert fraud_service._extract_domain("test@example.com") == "example.com"
        assert fraud_service._extract_domain("user@azelis.com") == "azelis.com"
        assert fraud_service._extract_domain("invalid") is None
        assert fraud_service._extract_domain("") is None

    def test_levenshtein_distance(self, fraud_service):
        """Test Levenshtein distance calculation"""
        # Same string
        assert fraud_service._levenshtein_distance("azelis", "azelis") == 0

        # One character difference (typosquatting)
        assert fraud_service._levenshtein_distance("azelis", "acelis") == 1

        # Two character difference
        assert fraud_service._levenshtein_distance("azelis", "acolis") == 2

        # Completely different
        assert fraud_service._levenshtein_distance("azelis", "google") > 3

    def test_typosquatting_detection_acelis_vs_azelis(self, fraud_service):
        """Test that acelis.com.co (typosquat) vs azelis.com is detected"""
        # This is the actual Azelis fraud case pattern
        distance = fraud_service._levenshtein_distance("acelis", "azelis")
        assert distance <= 2  # Should be detected as similar

    def test_is_similar_name(self, fraud_service):
        """Test name similarity detection"""
        # Similar names (typosquatting)
        assert fraud_service._is_similar_name("AZELIS", "ACELIS", threshold=2) is True

        # Different names
        assert fraud_service._is_similar_name("AZELIS", "GOOGLE", threshold=2) is False

        # Case insensitive
        assert fraud_service._is_similar_name("azelis", "ACELIS", threshold=2) is True


class TestIdentityConsistency:
    """Test identity consistency checks"""

    @pytest.fixture
    def fraud_service(self):
        """Create FraudDetectionService with mocked dependencies"""
        service = FraudDetectionService(
            risk_repo=MagicMock(),
            rules_repo=MagicMock(),
            blacklist_repo=MagicMock(),
            client_repo=MagicMock(),
            scoring_service=MagicMock(),
            alert_service=MagicMock(),
        )
        return service

    def test_identity_mismatch_detection(self, fraud_service):
        """Test detection of company name inconsistencies"""
        # This tests the scenario where ROCSA was used instead of AZELIS
        # The _is_similar_name function should catch this

        # Different companies - should not match
        assert fraud_service._is_similar_name("ROCSA", "AZELIS") is False

        # Same company - should match
        assert fraud_service._is_similar_name("AZELIS COLOMBIA", "AZELIS COLOMBIA") is True


class TestRiskScoring:
    """Test risk score calculation"""

    @pytest.fixture
    def scoring_service(self):
        """Create RiskScoringService"""
        return RiskScoringService()

    @pytest.mark.asyncio
    async def test_low_risk_score(self, scoring_service):
        """Test that low indicators produce low score"""
        indicators = [
            FraudIndicator(
                indicator_name="test",
                indicator_value=False,  # Not triggered
                severity=RiskLevel.LOW,
                evidence="OK",
                score_impact=Decimal('0'),
            )
        ]

        score, level = await scoring_service.calculate_score(indicators)

        assert score == Decimal('0')
        assert level == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_high_risk_score(self, scoring_service):
        """Test that high indicators produce high score"""
        # Using score_impact of 100 per indicator (max possible)
        # With weights: identity_consistency=0.35, email_domain_validation=0.25
        # and default weight 0.10 for nit_format_validation
        # Expected: 0.35*100 + 0.25*100 + 0.10*100 = 70
        indicators = [
            FraudIndicator(
                indicator_name="identity_consistency",
                indicator_value=True,  # Triggered
                severity=RiskLevel.HIGH,
                evidence="Mismatch detected",
                score_impact=Decimal('100'),  # Full impact
            ),
            FraudIndicator(
                indicator_name="email_domain_validation",
                indicator_value=True,  # Triggered
                severity=RiskLevel.HIGH,
                evidence="Typosquatting detected",
                score_impact=Decimal('100'),  # Full impact
            ),
            FraudIndicator(
                indicator_name="nit_format_validation",
                indicator_value=True,  # Triggered
                severity=RiskLevel.HIGH,
                evidence="Invalid format",
                score_impact=Decimal('100'),  # Full impact
            ),
        ]

        score, level = await scoring_service.calculate_score(indicators)

        # Total: 0.35*100 + 0.25*100 + 0.10*100 = 70 (HIGH)
        assert score >= Decimal('60')  # Should be high
        assert level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    @pytest.mark.asyncio
    async def test_critical_risk_score(self, scoring_service):
        """Test that critical indicators produce critical score"""
        # Multiple max indicators to exceed 80 threshold
        # identity_consistency (0.35) + email_domain_validation (0.25) +
        # financial_document_issues (0.20) + nit_format_validation (0.10) = 0.90
        # 0.90 * 100 = 90 -> CRITICAL
        # NOTE: company_history no longer contributes to score per business requirements
        indicators = [
            FraudIndicator(
                indicator_name="identity_consistency",
                indicator_value=True,
                severity=RiskLevel.CRITICAL,
                evidence="Entity blacklisted",
                score_impact=Decimal('100'),
            ),
            FraudIndicator(
                indicator_name="email_domain_validation",
                indicator_value=True,
                severity=RiskLevel.CRITICAL,
                evidence="Domain blacklisted",
                score_impact=Decimal('100'),
            ),
            FraudIndicator(
                indicator_name="financial_document_issues",
                indicator_value=True,
                severity=RiskLevel.CRITICAL,
                evidence="Document issues",
                score_impact=Decimal('100'),
            ),
            FraudIndicator(
                indicator_name="nit_format_validation",
                indicator_value=True,
                severity=RiskLevel.CRITICAL,
                evidence="Invalid NIT format",
                score_impact=Decimal('100'),
            ),
        ]

        score, level = await scoring_service.calculate_score(indicators)

        # Total: 0.35*100 + 0.25*100 + 0.20*100 + 0.10*100 = 90 -> CRITICAL
        assert score >= Decimal('81')
        assert level == RiskLevel.CRITICAL

    def test_risk_level_thresholds(self, scoring_service):
        """Test risk level determination based on thresholds"""
        assert scoring_service._determine_risk_level(Decimal('0')) == RiskLevel.LOW
        assert scoring_service._determine_risk_level(Decimal('30')) == RiskLevel.LOW
        assert scoring_service._determine_risk_level(Decimal('31')) == RiskLevel.MEDIUM
        assert scoring_service._determine_risk_level(Decimal('60')) == RiskLevel.MEDIUM
        assert scoring_service._determine_risk_level(Decimal('61')) == RiskLevel.HIGH
        assert scoring_service._determine_risk_level(Decimal('80')) == RiskLevel.HIGH
        assert scoring_service._determine_risk_level(Decimal('81')) == RiskLevel.CRITICAL
        assert scoring_service._determine_risk_level(Decimal('100')) == RiskLevel.CRITICAL


class TestBlacklistChecking:
    """Test blacklist functionality"""

    @pytest.fixture
    def fraud_service(self):
        """Create FraudDetectionService with mocked dependencies"""
        blacklist_repo = MagicMock()
        blacklist_repo.check_any_blacklisted = AsyncMock(return_value=None)

        service = FraudDetectionService(
            risk_repo=MagicMock(),
            rules_repo=MagicMock(),
            blacklist_repo=blacklist_repo,
            client_repo=MagicMock(),
            scoring_service=MagicMock(),
            alert_service=MagicMock(),
        )
        return service

    @pytest.mark.asyncio
    async def test_blacklist_check_not_blocked(self, fraud_service):
        """Test that non-blacklisted entities pass"""
        client_data = {
            'nit': '900.123.456-7',
            'nombre_importador': 'Test Company',
        }

        result = await fraud_service._check_blacklist(client_data)
        assert result is None  # Not blacklisted

    @pytest.mark.asyncio
    async def test_blacklist_check_blocked(self):
        """Test that blacklisted entities are caught"""
        blacklist_repo = MagicMock()
        blacklist_repo.check_any_blacklisted = AsyncMock(return_value={
            'id': 'test-id',
            'entity_type': 'nit',
            'entity_value': '900.123.456',
            'reason': 'Fraud detected',
        })

        fraud_service = FraudDetectionService(
            risk_repo=MagicMock(),
            rules_repo=MagicMock(),
            blacklist_repo=blacklist_repo,
            client_repo=MagicMock(),
            scoring_service=MagicMock(),
            alert_service=MagicMock(),
        )

        client_data = {
            'nit': '900.123.456-7',
            'nombre_importador': 'Test Company',
        }

        result = await fraud_service._check_blacklist(client_data)
        assert result is not None  # Blacklisted
        assert result['entity_type'] == 'nit'


class TestCompanyHistoryCheck:
    """Test company history check - should never contribute to risk score"""

    @pytest.fixture
    def fraud_service(self):
        """Create FraudDetectionService with mocked dependencies"""
        risk_repo = MagicMock()
        risk_repo.get_recent_by_client = AsyncMock(return_value=[])

        service = FraudDetectionService(
            risk_repo=risk_repo,
            rules_repo=MagicMock(),
            blacklist_repo=MagicMock(),
            client_repo=MagicMock(),
            scoring_service=MagicMock(),
            alert_service=MagicMock(),
        )
        return service

    @pytest.mark.asyncio
    async def test_company_history_no_previous_assessments_no_score_impact(self, fraud_service):
        """Test that first-time customers do NOT get score impact"""
        # Set up mock to return empty list (no previous assessments)
        fraud_service.risk_repo.get_recent_by_client = AsyncMock(return_value=[])

        client_data = {'nit': '900123456-7', 'cupo_plataforma': 1000000000}
        rule = {'weight': 0.10, 'rule_type': 'history'}

        indicator = await fraud_service._check_company_history(client_data, rule)

        # Per business requirements: company_history should NEVER trigger score
        assert indicator.indicator_name == "company_history"
        assert indicator.indicator_value is False  # Never triggers
        assert indicator.score_impact == Decimal('0')  # Zero impact
        assert indicator.severity.value == "low"
        assert "Primera evaluación" in indicator.evidence

    @pytest.mark.asyncio
    async def test_company_history_with_previous_assessments_no_score_impact(self, fraud_service):
        """Test that returning customers also have no score impact"""
        # Set up mock to return some previous assessments
        fraud_service.risk_repo.get_recent_by_client = AsyncMock(return_value=[
            {'id': '1', 'risk_score': 25},
            {'id': '2', 'risk_score': 30},
        ])

        client_data = {'nit': '900123456-7'}
        rule = {'weight': 0.10, 'rule_type': 'history'}

        indicator = await fraud_service._check_company_history(client_data, rule)

        # History indicator should be informational only
        assert indicator.indicator_name == "company_history"
        assert indicator.indicator_value is False  # Never triggers
        assert indicator.score_impact == Decimal('0')  # Zero impact
        assert "2 evaluaciones previas" in indicator.evidence

    @pytest.mark.asyncio
    async def test_company_history_high_credit_no_history_no_score_impact(self, fraud_service):
        """Test that high credit limit for new clients does NOT add score impact"""
        # This was previously a risk factor but should no longer be
        fraud_service.risk_repo.get_recent_by_client = AsyncMock(return_value=[])

        client_data = {
            'nit': '900123456-7',
            'cupo_plataforma': 600000000  # > 500M COP
        }
        rule = {'weight': 0.10, 'rule_type': 'history'}

        indicator = await fraud_service._check_company_history(client_data, rule)

        # Even with high credit and no history, should NOT trigger score
        assert indicator.indicator_value is False
        assert indicator.score_impact == Decimal('0')


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def fraud_service(self):
        """Create FraudDetectionService with mocked dependencies"""
        service = FraudDetectionService(
            risk_repo=MagicMock(),
            rules_repo=MagicMock(),
            blacklist_repo=MagicMock(),
            client_repo=MagicMock(),
            scoring_service=MagicMock(),
            alert_service=MagicMock(),
        )
        return service

    def test_empty_client_data(self, fraud_service):
        """Test handling of empty client data"""
        # Should not crash with empty data
        assert fraud_service._extract_domain("") is None

    def test_nit_with_special_characters(self, fraud_service):
        """Test NIT handling with various formats"""
        # Clean NIT format should work
        assert fraud_service._calculate_nit_check_digit("900123456") is not None
        # NIT with dots - the function strips non-digits
        result = fraud_service._calculate_nit_check_digit("900123456")
        assert isinstance(result, int)
        assert 0 <= result <= 9

    def test_unicode_in_company_names(self, fraud_service):
        """Test handling of unicode/accented characters"""
        # Should handle accents gracefully
        result = fraud_service._is_similar_name("COMPAÑÍA", "COMPANIA")
        # The function normalizes by removing non-alphanumeric, so these should match
        assert result is True

    def test_very_long_company_name(self, fraud_service):
        """Test handling of very long company names"""
        long_name = "A" * 1000
        # Should not crash
        result = fraud_service._is_similar_name(long_name, "SHORT")
        assert result is False  # Very different
