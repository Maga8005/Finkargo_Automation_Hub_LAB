"""
Domain Validation Service - DNS and WHOIS validation for fraud detection

Provides domain existence verification (DNS lookup) and domain age validation
(WHOIS lookup) to detect recently-registered fraudulent domains used for typosquatting.

Key features:
- DNS lookup to verify domain existence
- WHOIS lookup to get domain registration date
- Domain age comparison against company registration date
- In-memory caching to avoid rate limiting
- Graceful timeout and error handling
"""
import socket
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from threading import Lock

# Try to import whois (optional dependency, gracefully handle if not installed)
try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    whois = None  # type: ignore
    WHOIS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ==================== Configuration Constants ====================

# Timeouts
DNS_TIMEOUT = 5  # seconds
WHOIS_TIMEOUT = 10  # seconds

# Cache TTL (24 hours in seconds)
CACHE_TTL = 86400

# Age thresholds
VERY_YOUNG_THRESHOLD = 90  # days - domain < 90 days is HIGH severity
YOUNG_THRESHOLD = 365  # days - domain < 1 year
SUSPICIOUS_AGE_RATIO = 0.1  # domain age < 10% of company age is suspicious


# ==================== Result Dataclasses ====================

@dataclass
class DomainExistenceResult:
    """Result of DNS lookup for domain existence check."""
    domain: str
    exists: bool
    ip_address: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class DomainAgeResult:
    """Result of WHOIS lookup for domain age."""
    domain: str
    creation_date: Optional[datetime] = None
    age_days: Optional[int] = None
    registrar: Optional[str] = None
    lookup_status: str = "pending"  # 'success', 'failed', 'unavailable', 'pending'
    error_message: Optional[str] = None


@dataclass
class DomainCompanyAgeComparison:
    """Result of comparing domain age against company age."""
    domain: str
    domain_age_days: Optional[int]
    company_age_days: Optional[int]
    company_registration_date: Optional[datetime]
    is_suspicious: bool
    severity: Optional[str]  # 'critical', 'high', 'medium', None
    reason: str
    score_impact: int


# ==================== Cache Implementation ====================

class DomainCache:
    """Thread-safe in-memory cache with TTL for WHOIS results."""

    def __init__(self, ttl: int = CACHE_TTL):
        self._cache: dict = {}
        self._lock = Lock()
        self._ttl = ttl

    def get(self, domain: str) -> Optional[DomainAgeResult]:
        """Get cached result if not expired."""
        with self._lock:
            if domain in self._cache:
                result, timestamp = self._cache[domain]
                if datetime.now(timezone.utc) - timestamp < timedelta(seconds=self._ttl):
                    logger.debug(f"Cache hit for domain: {domain}")
                    return result
                else:
                    # Expired, remove from cache
                    del self._cache[domain]
            return None

    def set(self, domain: str, result: DomainAgeResult) -> None:
        """Store result in cache with current timestamp."""
        with self._lock:
            self._cache[domain] = (result, datetime.now(timezone.utc))
            logger.debug(f"Cached WHOIS result for domain: {domain}")

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()


# ==================== Domain Validation Service ====================

class DomainValidationService:
    """
    Service for domain existence and age validation.

    Detects potential fraud by:
    - Verifying domains exist (resolve via DNS)
    - Checking domain registration age
    - Comparing domain age against company age from documents

    Fraudsters often register lookalike domains shortly before fraud attempts.
    A domain registered days ago for a company operating for 15 years is suspicious.
    """

    def __init__(self, cache: Optional[DomainCache] = None):
        """
        Initialize domain validation service.

        Args:
            cache: Optional custom cache instance. If None, creates new cache.
        """
        self._cache = cache or DomainCache()

    def check_domain_existence(self, domain: str) -> DomainExistenceResult:
        """
        Check if a domain exists by performing DNS lookup.

        Uses socket.gethostbyname() with timeout to resolve domain.
        Non-existent domains will fail to resolve.

        Args:
            domain: Domain name to check (e.g., "example.com")

        Returns:
            DomainExistenceResult with exists flag and IP if resolved
        """
        if not self._validate_domain_format(domain):
            return DomainExistenceResult(
                domain=domain,
                exists=False,
                error_message="Formato de dominio inválido"
            )

        # Set socket timeout
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(DNS_TIMEOUT)

        try:
            ip_address = socket.gethostbyname(domain)
            logger.info(f"Domain {domain} resolves to {ip_address}")
            return DomainExistenceResult(
                domain=domain,
                exists=True,
                ip_address=ip_address
            )
        except socket.gaierror as e:
            # DNS resolution failed - domain likely doesn't exist
            logger.info(f"Domain {domain} does not resolve: {e}")
            return DomainExistenceResult(
                domain=domain,
                exists=False,
                error_message=f"El dominio no resuelve (DNS): {str(e)}"
            )
        except socket.timeout:
            logger.warning(f"DNS lookup timeout for domain: {domain}")
            return DomainExistenceResult(
                domain=domain,
                exists=True,  # Assume exists on timeout (avoid false negatives)
                error_message="Timeout en búsqueda DNS"
            )
        except Exception as e:
            logger.error(f"Unexpected error in DNS lookup for {domain}: {e}")
            return DomainExistenceResult(
                domain=domain,
                exists=True,  # Assume exists on error (avoid false negatives)
                error_message=f"Error en búsqueda DNS: {str(e)}"
            )
        finally:
            socket.setdefaulttimeout(original_timeout)

    def get_domain_age(self, domain: str) -> DomainAgeResult:
        """
        Get domain creation date and age from WHOIS lookup.

        Uses python-whois library with caching to avoid rate limiting.
        Results are cached for 24 hours.

        Args:
            domain: Domain name to lookup (e.g., "example.com")

        Returns:
            DomainAgeResult with creation_date, age_days, registrar, and status
        """
        if not self._validate_domain_format(domain):
            return DomainAgeResult(
                domain=domain,
                lookup_status="failed",
                error_message="Formato de dominio inválido"
            )

        # Check cache first
        cached_result = self._cache.get(domain)
        if cached_result:
            return cached_result

        # Check if whois module is available
        if not WHOIS_AVAILABLE or whois is None:
            return DomainAgeResult(
                domain=domain,
                lookup_status="unavailable",
                error_message="Módulo WHOIS no disponible"
            )

        try:
            # Set timeout for WHOIS query (handled by library if supported)
            socket.setdefaulttimeout(WHOIS_TIMEOUT)

            whois_data = whois.whois(domain)

            if not whois_data:
                result = DomainAgeResult(
                    domain=domain,
                    lookup_status="unavailable",
                    error_message="No se encontró información WHOIS"
                )
                self._cache.set(domain, result)
                return result

            # Extract creation date (may be single datetime or list)
            creation_date = self._extract_creation_date(whois_data)

            # Calculate age
            age_days = None
            if creation_date:
                now = datetime.now(timezone.utc)
                # Handle timezone-naive datetimes
                if creation_date.tzinfo is None:
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                age_days = (now - creation_date).days

            # Extract registrar
            registrar = None
            if hasattr(whois_data, 'registrar') and whois_data.registrar:
                registrar = str(whois_data.registrar)

            result = DomainAgeResult(
                domain=domain,
                creation_date=creation_date,
                age_days=age_days,
                registrar=registrar,
                lookup_status="success" if creation_date else "unavailable"
            )

            logger.info(f"WHOIS lookup for {domain}: age={age_days} days, registrar={registrar}")
            self._cache.set(domain, result)
            return result

        except socket.timeout:
            logger.warning(f"WHOIS lookup timeout for domain: {domain}")
            result = DomainAgeResult(
                domain=domain,
                lookup_status="failed",
                error_message="Timeout en consulta WHOIS"
            )
            return result
        except Exception as e:
            error_str = str(e).lower()
            # Check for common WHOIS privacy/unavailable scenarios
            if any(x in error_str for x in ['no whois', 'not found', 'no match', 'rate limit']):
                logger.info(f"WHOIS unavailable for {domain}: {e}")
                result = DomainAgeResult(
                    domain=domain,
                    lookup_status="unavailable",
                    error_message=f"Información WHOIS no disponible: {str(e)}"
                )
            else:
                logger.error(f"WHOIS lookup error for {domain}: {e}")
                result = DomainAgeResult(
                    domain=domain,
                    lookup_status="failed",
                    error_message=f"Error en consulta WHOIS: {str(e)}"
                )
            self._cache.set(domain, result)
            return result
        finally:
            socket.setdefaulttimeout(None)

    def compare_domain_vs_company_age(
        self,
        domain: str,
        company_registration_date: Optional[datetime] = None,
        company_constitution_date: Optional[datetime] = None
    ) -> DomainCompanyAgeComparison:
        """
        Compare domain age against company age to detect suspicious domains.

        A domain registered recently for an established company is suspicious.
        Priority: use constitution_date (most reliable), fallback to registration_date.

        Severity levels:
        - CRITICAL (25 pts): Domain doesn't exist
        - HIGH (15 pts): Domain < 90 days old OR domain < 10% of company age
        - MEDIUM (8 pts): Domain < 1 year (no company date available)

        Args:
            domain: Domain name to check
            company_registration_date: Company registration date from RUT
            company_constitution_date: Company constitution date from Certificado

        Returns:
            DomainCompanyAgeComparison with severity and score impact
        """
        # First check if domain exists
        existence_result = self.check_domain_existence(domain)
        if not existence_result.exists:
            return DomainCompanyAgeComparison(
                domain=domain,
                domain_age_days=None,
                company_age_days=None,
                company_registration_date=company_constitution_date or company_registration_date,
                is_suspicious=True,
                severity="critical",
                reason=f"ALERTA CRÍTICA: El dominio '{domain}' no existe o no resuelve (DNS). Posible dominio fraudulento.",
                score_impact=25
            )

        # Get domain age
        age_result = self.get_domain_age(domain)

        # Use constitution_date preferentially, fallback to registration_date
        company_date = company_constitution_date or company_registration_date
        company_age_days = None

        if company_date:
            now = datetime.now(timezone.utc)
            if company_date.tzinfo is None:
                company_date = company_date.replace(tzinfo=timezone.utc)
            company_age_days = (now - company_date).days

        # If WHOIS lookup failed or unavailable, return with no penalty
        if age_result.lookup_status in ["failed", "unavailable"]:
            return DomainCompanyAgeComparison(
                domain=domain,
                domain_age_days=None,
                company_age_days=company_age_days,
                company_registration_date=company_date,
                is_suspicious=False,
                severity=None,
                reason=f"No se pudo obtener la antigüedad del dominio '{domain}'. {age_result.error_message or ''}",
                score_impact=0
            )

        domain_age_days = age_result.age_days

        # Check age thresholds
        if domain_age_days is not None:
            # Domain < 90 days is always HIGH severity
            if domain_age_days < VERY_YOUNG_THRESHOLD:
                return DomainCompanyAgeComparison(
                    domain=domain,
                    domain_age_days=domain_age_days,
                    company_age_days=company_age_days,
                    company_registration_date=company_date,
                    is_suspicious=True,
                    severity="high",
                    reason=f"ADVERTENCIA: El dominio '{domain}' tiene solo {domain_age_days} días de antigüedad (menos de 90 días). Posible dominio fraudulento reciente.",
                    score_impact=15
                )

            # Compare with company age if available
            if company_age_days is not None and company_age_days > 0:
                age_ratio = domain_age_days / company_age_days

                # Domain < 1 year AND < 10% of company age is HIGH severity
                if domain_age_days < YOUNG_THRESHOLD and age_ratio < SUSPICIOUS_AGE_RATIO:
                    return DomainCompanyAgeComparison(
                        domain=domain,
                        domain_age_days=domain_age_days,
                        company_age_days=company_age_days,
                        company_registration_date=company_date,
                        is_suspicious=True,
                        severity="high",
                        reason=f"ADVERTENCIA: El dominio '{domain}' ({domain_age_days} días) es muy joven comparado con la empresa ({company_age_days} días, {age_ratio:.0%}). La empresa fue constituida hace {company_age_days // 365} años pero el dominio tiene menos de {domain_age_days // 30} meses.",
                        score_impact=15
                    )

            # Domain < 1 year with no company date to compare is MEDIUM severity
            if domain_age_days < YOUNG_THRESHOLD and company_age_days is None:
                return DomainCompanyAgeComparison(
                    domain=domain,
                    domain_age_days=domain_age_days,
                    company_age_days=None,
                    company_registration_date=None,
                    is_suspicious=True,
                    severity="medium",
                    reason=f"NOTA: El dominio '{domain}' tiene {domain_age_days} días de antigüedad (menos de 1 año). Verifique manualmente si corresponde con la antigüedad de la empresa.",
                    score_impact=8
                )

        # No issues found
        return DomainCompanyAgeComparison(
            domain=domain,
            domain_age_days=domain_age_days,
            company_age_days=company_age_days,
            company_registration_date=company_date,
            is_suspicious=False,
            severity=None,
            reason=f"Dominio '{domain}' verificado. Antigüedad: {domain_age_days or 'desconocida'} días.",
            score_impact=0
        )

    def _validate_domain_format(self, domain: str) -> bool:
        """
        Validate domain format is acceptable for DNS/WHOIS lookup.

        Args:
            domain: Domain string to validate

        Returns:
            True if valid format, False otherwise
        """
        if not domain or not isinstance(domain, str):
            return False

        domain = domain.strip().lower()

        # Check length
        if len(domain) < 4 or len(domain) > 253:
            return False

        # Basic domain format pattern
        # Allows alphanumeric, hyphens, and dots
        pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}$'

        return bool(re.match(pattern, domain))

    def _extract_creation_date(self, whois_data) -> Optional[datetime]:
        """
        Extract creation date from WHOIS data.

        Handles cases where creation_date is:
        - A single datetime
        - A list of datetimes (returns earliest)
        - None or missing

        Args:
            whois_data: WHOIS response object

        Returns:
            datetime or None
        """
        creation_date = getattr(whois_data, 'creation_date', None)

        if creation_date is None:
            return None

        # Handle list of dates (take earliest)
        if isinstance(creation_date, list):
            valid_dates = [d for d in creation_date if isinstance(d, datetime)]
            if valid_dates:
                return min(valid_dates)
            return None

        # Single datetime
        if isinstance(creation_date, datetime):
            return creation_date

        return None

    def clear_cache(self) -> None:
        """Clear all cached WHOIS results."""
        self._cache.clear()
        logger.info("Domain validation cache cleared")
