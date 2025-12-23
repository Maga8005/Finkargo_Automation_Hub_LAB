"""
Risk Scoring Service
Calculates risk scores based on fraud indicators and rule weights
"""
import logging
from typing import List, Tuple, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

from src.interface.risk_dtos import FraudIndicator, RiskLevel, VerificationStatus
from src.repositorio.risk_repository import FraudRulesRepository

logger = logging.getLogger(__name__)


class RiskScoringService:
    """
    Service for calculating risk scores using weighted algorithm.

    Risk Level Thresholds:
    - 0-30: LOW (auto-approve)
    - 31-60: MEDIUM (manual review)
    - 61-80: HIGH (detailed review + additional checks)
    - 81-100: CRITICAL (auto-reject + investigation)
    """

    # Default thresholds
    LOW_THRESHOLD = Decimal('30')
    MEDIUM_THRESHOLD = Decimal('60')
    HIGH_THRESHOLD = Decimal('80')
    MAX_SCORE = Decimal('100')

    # Default weights if rules not available
    DEFAULT_WEIGHTS = {
        'identity_consistency': Decimal('0.35'),
        'email_domain_validation': Decimal('0.25'),
        'financial_document_issues': Decimal('0.20'),
        'company_history': Decimal('0.10'),
        'address_verification': Decimal('0.10'),
    }

    def __init__(self, rules_repo: FraudRulesRepository = None):
        """
        Initialize scoring service

        Args:
            rules_repo: Optional fraud rules repository for dynamic weights
        """
        self.rules_repo = rules_repo

    async def calculate_score(
        self,
        indicators: List[FraudIndicator],
        rules: List[dict] = None
    ) -> Tuple[Decimal, RiskLevel]:
        """
        Calculate risk score from fraud indicators

        Args:
            indicators: List of fraud indicators from detection
            rules: Optional list of rule configurations with weights

        Returns:
            Tuple[Decimal, RiskLevel]: (score, risk_level)
        """
        if not indicators:
            return Decimal('0'), RiskLevel.LOW

        # Build weight map from rules or use defaults
        weights = self._build_weight_map(rules)

        # Calculate weighted score
        total_score = Decimal('0')
        total_weight = Decimal('0')

        for indicator in indicators:
            if indicator.indicator_value:  # Only count triggered indicators
                indicator_name = indicator.indicator_name
                weight = weights.get(indicator_name, Decimal('0.10'))
                impact = indicator.score_impact

                # Cap individual impact at 100
                impact = min(impact, Decimal('100'))

                weighted_impact = weight * impact
                total_score += weighted_impact
                total_weight += weight

                logger.debug(
                    f"Indicator {indicator_name}: weight={weight}, impact={impact}, "
                    f"weighted_impact={weighted_impact}"
                )

        # Normalize score to 0-100 range
        if total_weight > 0:
            # Don't divide by total_weight - indicators already contribute their weighted impact
            # Just ensure we don't exceed 100
            final_score = min(total_score, self.MAX_SCORE)
        else:
            final_score = Decimal('0')

        # Round to 2 decimal places
        final_score = final_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Determine risk level
        risk_level = self._determine_risk_level(final_score)

        logger.info(f"Risk score calculated: {final_score} -> {risk_level.value}")

        return final_score, risk_level

    def _build_weight_map(self, rules: List[dict] = None) -> Dict[str, Decimal]:
        """Build weight map from rules or defaults"""
        weight_map = {}

        if rules:
            for rule in rules:
                rule_name = rule.get('rule_name')
                weight = rule.get('weight', 0.10)

                # Convert to Decimal if needed
                if not isinstance(weight, Decimal):
                    weight = Decimal(str(weight))

                weight_map[rule_name] = weight

        # Fill in any missing with defaults
        for name, default_weight in self.DEFAULT_WEIGHTS.items():
            if name not in weight_map:
                weight_map[name] = default_weight

        return weight_map

    def _determine_risk_level(self, score: Decimal) -> RiskLevel:
        """
        Determine risk level based on score thresholds

        Args:
            score: Risk score (0-100)

        Returns:
            RiskLevel: Corresponding risk level
        """
        if score <= self.LOW_THRESHOLD:
            return RiskLevel.LOW
        elif score <= self.MEDIUM_THRESHOLD:
            return RiskLevel.MEDIUM
        elif score <= self.HIGH_THRESHOLD:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def get_thresholds(self) -> Dict[str, float]:
        """
        Get current threshold configuration

        Returns:
            Dict with threshold values
        """
        return {
            'low_max': float(self.LOW_THRESHOLD),
            'medium_max': float(self.MEDIUM_THRESHOLD),
            'high_max': float(self.HIGH_THRESHOLD),
            'critical_min': float(self.HIGH_THRESHOLD) + 0.01,
        }

    def update_thresholds(
        self,
        low_max: float = None,
        medium_max: float = None,
        high_max: float = None
    ):
        """
        Update threshold values (in-memory only)

        Args:
            low_max: Maximum score for LOW level
            medium_max: Maximum score for MEDIUM level
            high_max: Maximum score for HIGH level
        """
        if low_max is not None:
            self.LOW_THRESHOLD = Decimal(str(low_max))

        if medium_max is not None:
            self.MEDIUM_THRESHOLD = Decimal(str(medium_max))

        if high_max is not None:
            self.HIGH_THRESHOLD = Decimal(str(high_max))

        logger.info(
            f"Thresholds updated: LOW<={self.LOW_THRESHOLD}, "
            f"MEDIUM<={self.MEDIUM_THRESHOLD}, HIGH<={self.HIGH_THRESHOLD}"
        )

    def calculate_indicator_impact(
        self,
        indicator: FraudIndicator,
        rules: List[dict] = None
    ) -> Dict[str, Any]:
        """
        Calculate the impact of a single indicator

        Args:
            indicator: Fraud indicator
            rules: Rule configurations

        Returns:
            Dict with impact details
        """
        weights = self._build_weight_map(rules)
        weight = weights.get(indicator.indicator_name, Decimal('0.10'))

        raw_impact = indicator.score_impact if indicator.indicator_value else Decimal('0')
        weighted_impact = weight * raw_impact

        return {
            'indicator_name': indicator.indicator_name,
            'triggered': indicator.indicator_value,
            'severity': indicator.severity.value if isinstance(indicator.severity, RiskLevel) else indicator.severity,
            'raw_impact': float(raw_impact),
            'weight': float(weight),
            'weighted_impact': float(weighted_impact),
            'evidence': indicator.evidence,
        }

    def simulate_score(
        self,
        indicator_values: Dict[str, bool],
        rules: List[dict] = None
    ) -> Dict[str, Any]:
        """
        Simulate a risk score based on hypothetical indicator values.
        Useful for configuration testing.

        Args:
            indicator_values: Dict mapping indicator names to triggered status
            rules: Rule configurations

        Returns:
            Dict with simulated score and breakdown
        """
        weights = self._build_weight_map(rules)
        breakdown = []
        total_score = Decimal('0')

        for indicator_name, triggered in indicator_values.items():
            weight = weights.get(indicator_name, Decimal('0.10'))

            # Assume full impact (100) if triggered
            if triggered:
                impact = weight * Decimal('100')
                total_score += impact
            else:
                impact = Decimal('0')

            breakdown.append({
                'indicator': indicator_name,
                'triggered': triggered,
                'weight': float(weight),
                'impact': float(impact),
            })

        final_score = min(total_score, self.MAX_SCORE)
        risk_level = self._determine_risk_level(final_score)

        return {
            'score': float(final_score),
            'risk_level': risk_level.value,
            'breakdown': breakdown,
            'thresholds': self.get_thresholds(),
        }

    async def calculate_final_score(
        self,
        preliminary_score: Decimal,
        cross_validation_results: List[dict],
        rules: List[dict] = None
    ) -> Tuple[Decimal, RiskLevel]:
        """
        Calculate final risk score by combining preliminary score with cross-validation impacts.

        This method is called after document cross-validation completes to produce
        the final risk assessment score that incorporates discrepancies found
        between documents.

        Args:
            preliminary_score: Initial risk score from fraud indicators
            cross_validation_results: List of cross-validation results with score_impact
            rules: Optional list of rule configurations (unused currently, for future expansion)

        Returns:
            Tuple[Decimal, RiskLevel]: (final_score, risk_level)
        """
        if not isinstance(preliminary_score, Decimal):
            preliminary_score = Decimal(str(preliminary_score))

        # Sum up score impacts from cross-validation discrepancies
        cross_validation_impact = Decimal('0')

        for result in cross_validation_results:
            score_impact = result.get('score_impact', 0)
            if not isinstance(score_impact, Decimal):
                score_impact = Decimal(str(score_impact))

            # Only add positive impacts (discrepancies increase risk)
            if score_impact > 0:
                cross_validation_impact += score_impact
                logger.debug(
                    f"Cross-validation impact: type={result.get('validation_type')}, "
                    f"severity={result.get('severity')}, impact={score_impact}"
                )

        # Combine preliminary score with cross-validation impact
        combined_score = preliminary_score + cross_validation_impact

        # Cap at maximum score
        final_score = min(combined_score, self.MAX_SCORE)

        # Round to 2 decimal places
        final_score = final_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Determine final risk level
        risk_level = self._determine_risk_level(final_score)

        logger.info(
            f"Final score calculated: preliminary={preliminary_score}, "
            f"cross_validation_impact={cross_validation_impact}, "
            f"final={final_score} -> {risk_level.value}"
        )

        return final_score, risk_level

    def determine_verification_status(
        self,
        cross_validation_results: List[dict]
    ) -> VerificationStatus:
        """
        Determine binary verification status based on cross-validation results.

        The stakeholder requirement is clear: ANY discrepancy (regardless of severity)
        must result in REQUIRES_MANUAL_VERIFICATION. There is no threshold or scoring
        logic - it's a simple binary decision.

        Args:
            cross_validation_results: List of cross-validation results from validation

        Returns:
            VerificationStatus: PASS if no discrepancies, REQUIRES_MANUAL_VERIFICATION otherwise
        """
        if not cross_validation_results:
            return VerificationStatus.PASS

        # Check if ANY result has is_discrepancy=True
        has_any_discrepancy = any(
            result.get('is_discrepancy', False)
            for result in cross_validation_results
        )

        if has_any_discrepancy:
            logger.info("Verification status: REQUIRES_MANUAL_VERIFICATION (discrepancy found)")
            return VerificationStatus.REQUIRES_MANUAL_VERIFICATION

        logger.info("Verification status: PASS (no discrepancies)")
        return VerificationStatus.PASS

    def count_discrepancies(self, cross_validation_results: List[dict]) -> int:
        """
        Count the number of discrepancies in cross-validation results.

        Args:
            cross_validation_results: List of cross-validation results

        Returns:
            int: Count of results where is_discrepancy=True
        """
        if not cross_validation_results:
            return 0

        return sum(
            1 for result in cross_validation_results
            if result.get('is_discrepancy', False)
        )

    def get_verification_info(
        self,
        cross_validation_results: List[dict]
    ) -> Dict[str, Any]:
        """
        Get complete verification information from cross-validation results.

        Args:
            cross_validation_results: List of cross-validation results

        Returns:
            Dict with verification_status, has_discrepancies, and discrepancy_count
        """
        discrepancy_count = self.count_discrepancies(cross_validation_results)
        has_discrepancies = discrepancy_count > 0
        verification_status = (
            VerificationStatus.REQUIRES_MANUAL_VERIFICATION
            if has_discrepancies
            else VerificationStatus.PASS
        )

        return {
            'verification_status': verification_status,
            'has_discrepancies': has_discrepancies,
            'discrepancy_count': discrepancy_count,
        }
