"""
Declaration Payment Matcher for Treasury Declaration-Historial Matching.

Uses fuzzy string matching to match payment groups to exchange declarations.
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from rapidfuzz import fuzz

from src.interface.treasury_matching_dtos import (
    PaymentGroup,
    DeclarationItem,
    MatchConfig,
    MatchResult,
    MatchStatus,
    MatchingStatistics,
)

logger = logging.getLogger(__name__)


class DeclarationPaymentMatcher:
    """
    Service for matching payment groups to exchange declarations.

    Uses configurable tolerance for:
    - Customer name (fuzzy matching)
    - Date (±N days)
    - Amount (±$X.XX)
    """

    def match_payments_to_declarations(
        self,
        payment_groups: List[PaymentGroup],
        declarations: List[DeclarationItem],
        config: MatchConfig
    ) -> Tuple[List[MatchResult], MatchingStatistics]:
        """
        Match payment groups to declarations using configured tolerance.

        Args:
            payment_groups: List of aggregated payment groups
            declarations: List of available declarations
            config: Matching configuration

        Returns:
            Tuple of (match results, statistics)
        """
        logger.info(
            f"Matching {len(payment_groups)} payment groups to {len(declarations)} declarations. "
            f"Config: date_tolerance={config.date_tolerance_days}d, "
            f"amount_tolerance=${config.amount_tolerance}, "
            f"customer_threshold={config.customer_match_threshold}"
        )

        results: List[MatchResult] = []
        used_declarations: set = set()

        for group in payment_groups:
            result = self._find_best_match(
                group=group,
                declarations=declarations,
                config=config,
                used_declarations=used_declarations
            )
            results.append(result)

            # Mark declaration as used if matched
            if result.declaration:
                used_declarations.add(result.declaration.declaration_id)

        # Calculate statistics
        statistics = self._calculate_statistics(results, declarations, used_declarations)

        logger.info(
            f"Matching complete: {statistics.matched_groups}/{statistics.total_payment_groups} matched "
            f"({statistics.match_percentage:.1f}%), avg confidence: {statistics.average_confidence:.2f}"
        )

        return results, statistics

    def _find_best_match(
        self,
        group: PaymentGroup,
        declarations: List[DeclarationItem],
        config: MatchConfig,
        used_declarations: set
    ) -> MatchResult:
        """
        Find the best matching declaration for a payment group.

        Args:
            group: Payment group to match
            declarations: Available declarations
            config: Matching configuration
            used_declarations: Set of already-used declaration IDs

        Returns:
            MatchResult with best match or unmatched status
        """
        candidates: List[Tuple[DeclarationItem, float, float, int, float]] = []

        for declaration in declarations:
            # Skip already-used declarations
            if declaration.declaration_id in used_declarations:
                continue

            # Calculate customer name similarity
            if config.customer_match_strict:
                # Exact match required
                if group.cliente_normalized != declaration.customer_name_normalized:
                    continue
                customer_similarity = 1.0
            else:
                # Fuzzy match
                customer_similarity = fuzz.ratio(
                    group.cliente_normalized,
                    declaration.customer_name_normalized
                ) / 100.0

                if customer_similarity * 100 < config.customer_match_threshold:
                    continue

            # Check date tolerance
            try:
                payment_date = datetime.strptime(group.fecha_pago, "%Y-%m-%d")
                declaration_date = datetime.strptime(declaration.fecha, "%Y-%m-%d")
                date_diff_days = abs((payment_date - declaration_date).days)

                if date_diff_days > config.date_tolerance_days:
                    continue
            except ValueError as e:
                logger.warning(f"Date parsing error: {e}")
                continue

            # Check amount tolerance
            amount_diff = abs(group.total_capital - declaration.amount)
            if amount_diff > config.amount_tolerance:
                continue

            # Calculate confidence score
            confidence = self._calculate_confidence(
                customer_similarity=customer_similarity,
                date_diff_days=date_diff_days,
                date_tolerance=config.date_tolerance_days,
                amount_diff=amount_diff,
                amount_tolerance=config.amount_tolerance
            )

            candidates.append((
                declaration,
                confidence,
                customer_similarity,
                date_diff_days,
                amount_diff
            ))

        # No matches found
        if not candidates:
            return MatchResult(
                group_id=group.group_id,
                payment_group=group,
                declaration=None,
                match_status=MatchStatus.UNMATCHED,
                match_confidence=0.0,
                customer_similarity=None,
                date_difference_days=None,
                amount_difference=None,
                conflict_declarations=None
            )

        # Sort by confidence (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Check for conflicts (multiple high-confidence matches)
        high_confidence_threshold = 0.9
        high_confidence_matches = [c for c in candidates if c[1] >= high_confidence_threshold]

        if len(high_confidence_matches) > 1:
            # Conflict - multiple declarations match equally well
            best = candidates[0]
            conflict_declarations = [c[0] for c in high_confidence_matches[1:]]

            return MatchResult(
                group_id=group.group_id,
                payment_group=group,
                declaration=best[0],
                match_status=MatchStatus.CONFLICT,
                match_confidence=best[1],
                customer_similarity=best[2],
                date_difference_days=best[3],
                amount_difference=best[4],
                conflict_declarations=conflict_declarations
            )

        # Best match found
        best = candidates[0]

        # Determine status based on confidence
        if best[1] >= 0.95:
            status = MatchStatus.MATCHED
        elif best[1] >= 0.70:
            status = MatchStatus.MATCHED
        else:
            status = MatchStatus.PARTIAL

        return MatchResult(
            group_id=group.group_id,
            payment_group=group,
            declaration=best[0],
            match_status=status,
            match_confidence=best[1],
            customer_similarity=best[2],
            date_difference_days=best[3],
            amount_difference=best[4],
            conflict_declarations=None
        )

    def _calculate_confidence(
        self,
        customer_similarity: float,
        date_diff_days: int,
        date_tolerance: int,
        amount_diff: float,
        amount_tolerance: float
    ) -> float:
        """
        Calculate overall confidence score from individual factors.

        Weights:
        - Customer name similarity: 40%
        - Date proximity: 30%
        - Amount proximity: 30%

        Args:
            customer_similarity: 0.0 to 1.0
            date_diff_days: Days difference
            date_tolerance: Max days tolerance
            amount_diff: Amount difference in USD
            amount_tolerance: Max amount tolerance

        Returns:
            Confidence score 0.0 to 1.0
        """
        # Customer similarity score (40%)
        customer_score = customer_similarity * 0.40

        # Date proximity score (30%)
        # Perfect match = 1.0, at tolerance limit = 0.0
        date_score = (1.0 - (date_diff_days / max(date_tolerance, 1))) * 0.30

        # Amount proximity score (30%)
        # Perfect match = 1.0, at tolerance limit = 0.0
        amount_score = (1.0 - (amount_diff / max(amount_tolerance, 0.01))) * 0.30

        total = customer_score + date_score + amount_score

        # Clamp to [0, 1]
        return max(0.0, min(1.0, total))

    def _calculate_statistics(
        self,
        results: List[MatchResult],
        declarations: List[DeclarationItem],
        used_declarations: set
    ) -> MatchingStatistics:
        """
        Calculate statistics from matching results.

        Args:
            results: List of match results
            declarations: All available declarations
            used_declarations: Set of declaration IDs that were used

        Returns:
            MatchingStatistics
        """
        total = len(results)
        matched = sum(1 for r in results if r.match_status == MatchStatus.MATCHED)
        partial = sum(1 for r in results if r.match_status == MatchStatus.PARTIAL)
        unmatched = sum(1 for r in results if r.match_status == MatchStatus.UNMATCHED)
        conflicts = sum(1 for r in results if r.match_status == MatchStatus.CONFLICT)

        # Calculate average confidence for matched/partial results
        confidence_sum = sum(
            r.match_confidence for r in results
            if r.match_status in [MatchStatus.MATCHED, MatchStatus.PARTIAL, MatchStatus.CONFLICT]
        )
        confidence_count = matched + partial + conflicts
        avg_confidence = confidence_sum / max(confidence_count, 1)

        match_percentage = ((matched + partial + conflicts) / max(total, 1)) * 100

        return MatchingStatistics(
            total_payment_groups=total,
            matched_groups=matched,
            partial_matches=partial,
            unmatched_groups=unmatched,
            conflict_groups=conflicts,
            match_percentage=round(match_percentage, 1),
            average_confidence=round(avg_confidence, 3),
            total_declarations=len(declarations),
            declarations_used=len(used_declarations),
            declarations_unused=len(declarations) - len(used_declarations)
        )

    def manual_override(
        self,
        results: List[MatchResult],
        group_id: str,
        declaration: Optional[DeclarationItem]
    ) -> List[MatchResult]:
        """
        Manually override a match result.

        Args:
            results: Current list of match results
            group_id: Payment group ID to override
            declaration: Declaration to assign (None to clear)

        Returns:
            Updated list of match results
        """
        for result in results:
            if result.group_id == group_id:
                if declaration:
                    result.declaration = declaration
                    result.match_status = MatchStatus.MATCHED
                    result.match_confidence = 1.0  # Manual override = 100% confidence
                    result.customer_similarity = None
                    result.date_difference_days = None
                    result.amount_difference = None
                    result.conflict_declarations = None
                else:
                    result.declaration = None
                    result.match_status = MatchStatus.UNMATCHED
                    result.match_confidence = 0.0
                    result.customer_similarity = None
                    result.date_difference_days = None
                    result.amount_difference = None
                    result.conflict_declarations = None
                break

        return results


# Singleton instance
declaration_payment_matcher = DeclarationPaymentMatcher()
