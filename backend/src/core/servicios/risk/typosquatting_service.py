"""
Typosquatting Detection Service - Domain similarity and typosquatting detection

Detects potential typosquatting attacks where fraudsters register domains
that are visually similar to legitimate company domains.

Based on the Azelis fraud case:
- `acelis.com.co` was used to impersonate `azelis.com`
- Single character substitution (z → c) created a convincing fake domain
"""
import re
from difflib import SequenceMatcher
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TyposquattingResult:
    """Result of typosquatting analysis."""
    is_suspicious: bool
    similar_domain: Optional[str]
    similarity_score: float
    levenshtein_distance: int
    detection_type: str  # 'typosquatting', 'tld_variation', 'provider_domain', 'exact_match', 'no_match'
    description: str


class TyposquattingService:
    """
    Service for detecting typosquatting and domain similarity.

    Uses multiple detection methods:
    1. SequenceMatcher similarity ratio (70-95% = suspicious)
    2. Levenshtein distance (distance <= 2 = suspicious)
    3. TLD variation detection (.com vs .com.co)
    4. Provider domain validation
    """

    # Known legitimate company domains for typosquatting detection
    # Dynamically expanded with company-specific domains
    DEFAULT_KNOWN_DOMAINS = [
        'azelis.com',
        'basf.com',
        'dow.com',
        'dupont.com',
        'evonik.com',
        'lanxess.com',
        'brenntag.com',
        'univar.com',
        'clariant.com',
        'solvay.com',
        'huntsman.com',
        'ashland.com',
    ]

    # Common TLD variations for Latin American markets
    TLD_VARIATIONS = {
        '.com': ['.com.co', '.com.mx', '.com.br', '.com.ar', '.co', '.mx'],
        '.co': ['.com', '.com.co'],
        '.com.co': ['.com', '.co'],
        '.com.mx': ['.com', '.mx'],
    }

    # Free email providers that may indicate fraud when used for business
    FREE_EMAIL_PROVIDERS = [
        'gmail.com',
        'hotmail.com',
        'outlook.com',
        'yahoo.com',
        'live.com',
        'icloud.com',
        'protonmail.com',
        'mail.com',
        'yandex.com',
        'aol.com',
    ]

    # Suspicious TLDs often used for fraud
    SUSPICIOUS_TLDS = [
        '.xyz', '.top', '.tk', '.ml', '.ga', '.cf', '.gq',
        '.work', '.click', '.link', '.info', '.biz', '.online',
    ]

    # Similarity thresholds
    TYPOSQUATTING_MIN_SIMILARITY = 0.7  # 70% - below this, names are too different
    TYPOSQUATTING_MAX_SIMILARITY = 0.95  # 95% - above this, likely intentional variation
    MAX_LEVENSHTEIN_DISTANCE = 2  # Max edit distance to flag as typosquatting

    def check_domain_typosquatting(
        self,
        domain: str,
        known_domains: Optional[List[str]] = None,
        company_name: Optional[str] = None
    ) -> TyposquattingResult:
        """
        Check if a domain appears to be typosquatting a known domain.

        Args:
            domain: The domain to check
            known_domains: Optional list of known legitimate domains
            company_name: Optional company name to derive expected domain

        Returns:
            TyposquattingResult with analysis details
        """
        if not domain:
            return TyposquattingResult(
                is_suspicious=False,
                similar_domain=None,
                similarity_score=0.0,
                levenshtein_distance=0,
                detection_type='no_match',
                description='Dominio vacío'
            )

        domain = domain.lower().strip()

        # Build list of domains to check against
        check_domains = list(self.DEFAULT_KNOWN_DOMAINS)
        if known_domains:
            check_domains.extend(known_domains)

        # Add company-derived domain if provided
        if company_name:
            derived_domain = self._derive_domain_from_company(company_name)
            if derived_domain:
                check_domains.append(derived_domain)

        # Check against each known domain
        best_match: Optional[TyposquattingResult] = None
        highest_similarity = 0.0

        for known_domain in check_domains:
            result = self._compare_domains(domain, known_domain)

            if result.is_suspicious and result.similarity_score > highest_similarity:
                highest_similarity = result.similarity_score
                best_match = result

        if best_match:
            return best_match

        # Check for suspicious TLD
        if self._has_suspicious_tld(domain):
            return TyposquattingResult(
                is_suspicious=True,
                similar_domain=None,
                similarity_score=0.0,
                levenshtein_distance=0,
                detection_type='suspicious_tld',
                description=f"Dominio usa TLD sospechoso: {domain}"
            )

        return TyposquattingResult(
            is_suspicious=False,
            similar_domain=None,
            similarity_score=0.0,
            levenshtein_distance=0,
            detection_type='no_match',
            description='No se detectó typosquatting'
        )

    def _compare_domains(self, domain: str, known_domain: str) -> TyposquattingResult:
        """
        Compare a domain against a known legitimate domain.

        Args:
            domain: Domain to check
            known_domain: Known legitimate domain

        Returns:
            TyposquattingResult with comparison details
        """
        domain_base = self.extract_domain_base(domain)
        known_base = self.extract_domain_base(known_domain)

        # Exact base match - check for TLD variation
        if domain_base == known_base:
            domain_tld = self._extract_tld(domain)
            known_tld = self._extract_tld(known_domain)

            if domain_tld == known_tld:
                return TyposquattingResult(
                    is_suspicious=False,
                    similar_domain=known_domain,
                    similarity_score=1.0,
                    levenshtein_distance=0,
                    detection_type='exact_match',
                    description=f'Coincidencia exacta con {known_domain}'
                )
            else:
                # TLD variation (e.g., azelis.com vs azelis.com.co)
                return TyposquattingResult(
                    is_suspicious=True,
                    similar_domain=known_domain,
                    similarity_score=1.0,
                    levenshtein_distance=0,
                    detection_type='tld_variation',
                    description=f"Variación de TLD: {domain} vs {known_domain}"
                )

        # Calculate similarity
        similarity = self.calculate_similarity(domain_base, known_base)
        lev_distance = self.calculate_levenshtein_distance(domain_base, known_base)

        # Check if it's in the suspicious range
        is_typosquatting = (
            (self.TYPOSQUATTING_MIN_SIMILARITY <= similarity <= self.TYPOSQUATTING_MAX_SIMILARITY) or
            (lev_distance <= self.MAX_LEVENSHTEIN_DISTANCE and lev_distance > 0)
        )

        if is_typosquatting:
            return TyposquattingResult(
                is_suspicious=True,
                similar_domain=known_domain,
                similarity_score=similarity,
                levenshtein_distance=lev_distance,
                detection_type='typosquatting',
                description=f"POSIBLE TYPOSQUATTING: '{domain}' similar a '{known_domain}' "
                           f"(similitud: {similarity:.0%}, distancia: {lev_distance})"
            )

        return TyposquattingResult(
            is_suspicious=False,
            similar_domain=known_domain if similarity > 0.5 else None,
            similarity_score=similarity,
            levenshtein_distance=lev_distance,
            detection_type='no_match',
            description=f'No hay coincidencia significativa con {known_domain}'
        )

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity using SequenceMatcher.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        if not s1 or not s2:
            return 0.0

        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

    def calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein (edit) distance between two strings.

        The minimum number of single-character edits (insertions,
        deletions, substitutions) needed to transform s1 into s2.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance (0 = identical)
        """
        if not s1:
            return len(s2) if s2 else 0
        if not s2:
            return len(s1)

        s1 = s1.lower()
        s2 = s2.lower()

        if len(s1) < len(s2):
            s1, s2 = s2, s1

        previous_row = list(range(len(s2) + 1))

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def extract_domain_base(self, domain: str) -> str:
        """
        Extract the base name from a domain (without TLD).

        Examples:
            'azelis.com' → 'azelis'
            'azelis.com.co' → 'azelis'
            'subdomain.azelis.com' → 'azelis'

        Args:
            domain: Full domain

        Returns:
            Base domain name
        """
        if not domain:
            return ''

        domain = domain.lower().strip()

        # Remove common TLD combinations
        # Order matters - check longer patterns first
        tld_patterns = [
            r'\.com\.\w{2}$',  # .com.co, .com.mx, etc.
            r'\.org\.\w{2}$',
            r'\.net\.\w{2}$',
            r'\.edu\.\w{2}$',
            r'\.\w{2,4}$',     # .com, .org, .co, etc.
        ]

        base = domain
        for pattern in tld_patterns:
            base = re.sub(pattern, '', base)
            if base != domain:
                break

        # If there's still a dot (subdomain), get the main part
        parts = base.split('.')
        if len(parts) > 1:
            # Return the second-to-last part (main domain)
            return parts[-1] if parts[-1] else parts[-2] if len(parts) > 1 else parts[0]

        return parts[0] if parts else ''

    def _extract_tld(self, domain: str) -> str:
        """
        Extract the TLD from a domain.

        Examples:
            'azelis.com' → '.com'
            'azelis.com.co' → '.com.co'

        Args:
            domain: Full domain

        Returns:
            TLD including the dot
        """
        if not domain:
            return ''

        domain = domain.lower().strip()

        # Check for compound TLDs first
        compound_tlds = ['.com.co', '.com.mx', '.com.br', '.com.ar', '.org.co']
        for tld in compound_tlds:
            if domain.endswith(tld):
                return tld

        # Extract simple TLD
        match = re.search(r'(\.[a-z]{2,})$', domain)
        return match.group(1) if match else ''

    def _has_suspicious_tld(self, domain: str) -> bool:
        """
        Check if domain uses a suspicious TLD.

        Args:
            domain: Domain to check

        Returns:
            True if TLD is suspicious
        """
        domain = domain.lower()
        return any(domain.endswith(tld) for tld in self.SUSPICIOUS_TLDS)

    def _derive_domain_from_company(self, company_name: str) -> Optional[str]:
        """
        Derive expected domain from company name.

        Examples:
            'AZELIS COLOMBIA S.A.S.' → 'azelis.com'
            'BASF Quimica' → 'basf.com'

        Args:
            company_name: Company name

        Returns:
            Expected domain or None
        """
        if not company_name:
            return None

        # Clean company name
        name = company_name.upper().strip()

        # Remove common legal suffixes and country names
        remove_patterns = [
            r'\s*S\s*\.\s*A\s*\.\s*S\s*\.?\s*$',
            r'\s*S\s*\.\s*A\s*\.?\s*$',
            r'\s*LTDA\.?\s*$',
            r'\s*COLOMBIA\s*$',
            r'\s*MEXICO\s*$',
            r'\s*LATAM\s*$',
        ]

        for pattern in remove_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)

        # Get the first word (usually the company's main name)
        words = name.split()
        if words:
            base_name = words[0].lower()
            # Remove non-alphanumeric
            base_name = re.sub(r'[^a-z0-9]', '', base_name)
            if len(base_name) >= 3:  # Minimum length for a valid domain base
                return f"{base_name}.com"

        return None

    def is_free_email_provider(self, domain: str) -> bool:
        """
        Check if domain is a free email provider.

        Args:
            domain: Email domain to check

        Returns:
            True if it's a free provider
        """
        if not domain:
            return False

        return domain.lower().strip() in self.FREE_EMAIL_PROVIDERS

    def get_tld_variations(self, domain: str) -> List[str]:
        """
        Get possible TLD variations for a domain.

        Args:
            domain: Domain to check

        Returns:
            List of possible TLD variations
        """
        tld = self._extract_tld(domain)
        base = self.extract_domain_base(domain)

        if not base:
            return []

        variations = []
        if tld in self.TLD_VARIATIONS:
            for var_tld in self.TLD_VARIATIONS[tld]:
                variations.append(f"{base}{var_tld}")

        return variations

    def is_similar_domain(
        self,
        domain1: str,
        domain2: str,
        threshold: float = 0.7
    ) -> Tuple[bool, float]:
        """
        Check if two domains are similar.

        Args:
            domain1: First domain
            domain2: Second domain
            threshold: Similarity threshold (default 0.7)

        Returns:
            Tuple of (is_similar, similarity_score)
        """
        base1 = self.extract_domain_base(domain1)
        base2 = self.extract_domain_base(domain2)

        similarity = self.calculate_similarity(base1, base2)
        return (similarity >= threshold, similarity)
