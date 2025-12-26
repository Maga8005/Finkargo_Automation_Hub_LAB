"""
Normalization Service - Data normalization for fraud detection cross-validation

Provides robust normalization functions for company names, NITs, cities, and person names
to eliminate false positives caused by formatting differences.

Based on the Azelis fraud case analysis:
- Company names like "AZELIS COLOMBIA S.A.S." vs "AZELIS COLOMBIA S A S" should be treated as equal
- NITs like "830.027.231-3" vs "830027231 3" should be treated as equal
- Cities like "Tenjo (Cundinamarca)" vs "Tenjo" should be treated as equal
"""
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Tuple, Optional


class NormalizationService:
    """
    Service for normalizing data fields before comparison.

    Eliminates false positives from formatting differences while
    preserving semantic differences that indicate potential fraud.
    """

    # Comprehensive list of legal suffix variations to remove
    # Order matters - longer/more specific patterns should come first
    LEGAL_SUFFIXES = [
        # SAS variations
        r'\bS\s*\.\s*A\s*\.\s*S\s*\.',  # S.A.S.
        r'\bS\s*\.\s*A\s*\.\s*S\b',      # S.A.S
        r'\bS\s+A\s+S\b',                # S A S
        r'\bSAS\b',                       # SAS
        # SA variations
        r'\bS\s*\.\s*A\s*\.',            # S.A.
        r'\bS\s*\.\s*A\b',               # S.A
        r'\bS\s+A\b',                    # S A
        r'\bSA\b',                        # SA
        # LTDA variations
        r'\bLTDA\s*\.',                  # LTDA.
        r'\bLTDA\b',                      # LTDA
        r'\bLIMITADA\b',                  # LIMITADA
        r'\bLTD\s*\.',                   # LTD.
        r'\bLTD\b',                       # LTD
        # EU variations (Empresa Unipersonal)
        r'\bE\s*\.\s*U\s*\.',            # E.U.
        r'\bE\s*\.\s*U\b',               # E.U
        r'\bE\s+U\b',                    # E U
        r'\bEU\b',                        # EU
        # Other legal forms
        r'\bY\s+CIA\s*\.',               # Y CIA.
        r'\bY\s+CIA\b',                  # Y CIA
        r'\b&\s*CIA\s*\.',               # & CIA.
        r'\b&\s*CIA\b',                  # & CIA
        r'\bY\s+COMPANIA\b',             # Y COMPANIA
        r'\bY\s+COMPAÑIA\b',             # Y COMPAÑÍA
        r'\bCIA\s*\.',                   # CIA.
        r'\bCIA\b',                       # CIA
        r'\bINC\s*\.',                   # INC.
        r'\bINC\b',                       # INC
        r'\bCORP\s*\.',                  # CORP.
        r'\bCORP\b',                      # CORP
        r'\bLLC\b',                       # LLC
        r'\bGMBH\b',                      # GMBH
        # Colombian specific
        r'\bSOCIEDAD\s+ANONIMA\s+SIMPLIFICADA\b',
        r'\bSOCIEDAD\s+ANONIMA\b',
        r'\bSOCIEDAD\s+LIMITADA\b',
    ]

    # Common accent/character replacements
    ACCENT_MAP = {
        'Á': 'A', 'À': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ñ': 'N',
        'Ç': 'C',
    }

    # Department/region patterns to remove from city names
    DEPARTMENT_PATTERNS = [
        r'\s*\([^)]+\)\s*$',          # (Cundinamarca), (Antioquia), etc.
        r'\s*-\s*[A-Z][a-záéíóú]+$',  # - Cundinamarca (lowercase department)
        r',\s*[A-Z][a-záéíóú]+$',     # , Cundinamarca
    ]

    # City abbreviations and variations
    CITY_NORMALIZATIONS = {
        'BOGOTA': ['BOGOTA', 'BOGOTÁ', 'BOGOTA D.C.', 'BOGOTA DC', 'SANTAFE DE BOGOTA', 'BOGOTA D.C'],
        'MEDELLIN': ['MEDELLÍN', 'MEDELLIN'],
        'CALI': ['CALI', 'SANTIAGO DE CALI'],
        'BARRANQUILLA': ['BARRANQUILLA', 'BQUILLA'],
        'CARTAGENA': ['CARTAGENA', 'CARTAGENA DE INDIAS'],
        'BUCARAMANGA': ['BUCARAMANGA', 'BCARAMANGA'],
    }

    def normalize_company_name(self, name: str) -> str:
        """
        Normalize company name for comparison.

        Removes all legal suffix variations and normalizes punctuation/whitespace.

        Examples:
            "AZELIS COLOMBIA S.A.S." → "AZELIS COLOMBIA"
            "AZELIS COLOMBIA S A S" → "AZELIS COLOMBIA"
            "ROCSA COLOMBIA S.A." → "ROCSA COLOMBIA"
            "EMPRESA S.A.S. LTDA." → "EMPRESA" (handles malformed data)

        Args:
            name: Raw company name

        Returns:
            Normalized company name (uppercase, no legal suffixes, clean whitespace)
        """
        if not name:
            return ''

        # Convert to uppercase and strip
        normalized = name.upper().strip()

        # Remove accents
        normalized = self._remove_accents(normalized)

        # Apply legal suffix removal patterns (in order, from most to least specific)
        for pattern in self.LEGAL_SUFFIXES:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Remove any remaining punctuation except spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)

        # Normalize whitespace (multiple spaces to single, trim)
        normalized = ' '.join(normalized.split())

        return normalized

    def normalize_nit(self, nit: str) -> Tuple[str, Optional[str]]:
        """
        Normalize NIT and separate base digits from check digit.

        Colombian NIT format: XXX.XXX.XXX-X or XXXXXXXXX-X
        The check digit is the last digit after the separator.

        Colombian NITs are always structured as 9 base digits + 1 check digit.
        When a 10-digit NIT is provided without a separator (e.g., from AI extraction
        of Certificados de Existencia where NITs appear as "901854687 2" and get
        concatenated to "9018546872"), the last digit is inferred as the check digit.

        Examples:
            "830.027.231-3" → ("830027231", "3")
            "830027231 3" → ("830027231", "3")
            "830027231-1" → ("830027231", "1")
            "830027231" → ("830027231", None)
            "8300272313" → ("830027231", "3")  # 10 digits: infer last as check digit

        Args:
            nit: Raw NIT string

        Returns:
            Tuple of (base_digits, check_digit) where check_digit may be None
        """
        if not nit:
            return ('', None)

        # Remove all non-digit characters except the potential check digit separator
        # First, clean up dots and spaces within the base number
        cleaned = nit.strip()

        # Find the check digit separator (usually - or space at the end)
        # Pattern: digits followed by separator and single digit
        check_digit_match = re.search(r'[-\s](\d)$', cleaned)

        if check_digit_match:
            check_digit = check_digit_match.group(1)
            # Get everything before the check digit separator
            base_part = cleaned[:check_digit_match.start()]
        else:
            check_digit = None
            base_part = cleaned

        # Extract only digits from the base part
        base_digits = re.sub(r'[^\d]', '', base_part)

        # Handle 10-digit NITs without separator: infer last digit as check digit
        # Colombian NITs are always 9 base digits + 1 check digit
        if check_digit is None and len(base_digits) == 10:
            check_digit = base_digits[-1]
            base_digits = base_digits[:-1]

        return (base_digits, check_digit)

    def are_nits_equivalent(
        self,
        nit1: str,
        nit2: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Compare two NITs and determine if they are equivalent.

        Returns match status and reason:
        - Base digits match → True (formatting difference only)
        - Check digits differ → Partial match (potential data entry error)
        - Base digits differ → False (different NITs)

        Args:
            nit1: First NIT
            nit2: Second NIT

        Returns:
            Tuple of (is_match, reason, discrepancy_type)
            discrepancy_type: None if match, 'check_digit' or 'base_nit' if mismatch
        """
        base1, check1 = self.normalize_nit(nit1)
        base2, check2 = self.normalize_nit(nit2)

        # Empty NITs
        if not base1 or not base2:
            return (False, "NIT vacío o inválido", "base_nit")

        # Base digits must match
        if base1 != base2:
            return (
                False,
                f"NITs base diferentes: {base1} vs {base2}",
                "base_nit"
            )

        # Base matches - check if check digits differ
        if check1 is not None and check2 is not None:
            if check1 != check2:
                return (
                    True,  # Still considered a match for base comparison
                    f"Dígitos de verificación diferentes: {check1} vs {check2}",
                    "check_digit"
                )

        # Full match (or one/both missing check digit)
        return (True, "NITs equivalentes", None)

    def normalize_city(self, city: str) -> str:
        """
        Normalize city name for comparison.

        Removes department info, normalizes accents, and handles common variations.

        Examples:
            "Tenjo (Cundinamarca)" → "TENJO"
            "Bogotá D.C." → "BOGOTA"
            "MEDELLÍN" → "MEDELLIN"
            "Cartagena de Indias" → "CARTAGENA"

        Args:
            city: Raw city name

        Returns:
            Normalized city name (uppercase, no department info, no accents)
        """
        if not city:
            return ''

        normalized = city.strip()

        # Remove department patterns
        for pattern in self.DEPARTMENT_PATTERNS:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Convert to uppercase
        normalized = normalized.upper().strip()

        # Remove accents
        normalized = self._remove_accents(normalized)

        # Check for known city variations
        for canonical, variations in self.CITY_NORMALIZATIONS.items():
            for variation in variations:
                if normalized == self._remove_accents(variation.upper()):
                    return canonical

        # Remove common suffixes like D.C.
        normalized = re.sub(r'\s*D\s*\.\s*C\s*\.?\s*$', '', normalized)

        # Clean up any remaining punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    def normalize_person_name(self, name: str) -> str:
        """
        Normalize person name for comparison.

        Handles accents, case, and extra whitespace.

        Examples:
            "MARÍA JOSÉ GARCÍA" → "MARIA JOSE GARCIA"
            "  Juan   Carlos  " → "JUAN CARLOS"

        Args:
            name: Raw person name

        Returns:
            Normalized name (uppercase, no accents, clean whitespace)
        """
        if not name:
            return ''

        normalized = name.upper().strip()

        # Remove accents
        normalized = self._remove_accents(normalized)

        # Remove non-letter/space characters (but keep spaces between words)
        normalized = re.sub(r'[^A-Z\s]', '', normalized)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized

    def normalize_name(self, name: str) -> str:
        """
        Alias for normalize_person_name() for backward compatibility.

        Args:
            name: Raw person name

        Returns:
            Normalized name (uppercase, no accents, clean whitespace)
        """
        return self.normalize_person_name(name)

    def normalize_email(self, email: str) -> str:
        """
        Normalize email address for comparison.

        Lowercases and strips whitespace.

        Args:
            email: Raw email address

        Returns:
            Normalized email (lowercase, stripped)
        """
        if not email:
            return ''

        return email.lower().strip()

    def extract_email_domain(self, email: str) -> Optional[str]:
        """
        Extract domain from email address.

        Args:
            email: Email address

        Returns:
            Domain part of email (lowercase), or None if invalid
        """
        if not email or '@' not in email:
            return None

        parts = email.split('@')
        if len(parts) != 2:
            return None

        return parts[1].lower().strip()

    def _remove_accents(self, text: str) -> str:
        """
        Remove accents from text while preserving base characters.

        Uses character map for common Spanish accents and falls back to
        Unicode normalization for other characters.

        Args:
            text: Text with potential accents

        Returns:
            Text with accents removed
        """
        # First apply the explicit map
        for accented, base in self.ACCENT_MAP.items():
            text = text.replace(accented, base)
            text = text.replace(accented.lower(), base.lower())

        # Then use Unicode normalization for any remaining
        # NFD decomposes characters, we then filter out combining characters
        normalized = unicodedata.normalize('NFD', text)
        result = ''.join(c for c in normalized if not unicodedata.combining(c))

        return result

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity using SequenceMatcher.

        Used for comparing normalized strings (company names, person names)
        to detect potential fraud through name variations.

        Args:
            s1: First string (normalized)
            s2: Second string (normalized)

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        if not s1 or not s2:
            return 0.0

        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
