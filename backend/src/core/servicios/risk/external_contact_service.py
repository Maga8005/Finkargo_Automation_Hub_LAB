"""
External Contact Service - Email domain validation for fraud detection

Validates external contact emails against company information to detect
potential typosquatting fraud attempts.
"""
from typing import Optional, List
from datetime import datetime, timezone
import logging
import re

from src.repositorio.risk_repository import ExternalContactRepository
from src.core.servicios.risk.typosquatting_service import TyposquattingService
from src.core.servicios.risk.domain_validation_service import DomainValidationService
from src.interface.risk_dtos import (
    ExternalContactRequest,
    EmailValidationResult,
    ExternalContactValidationStatus,
)

logger = logging.getLogger(__name__)


class ExternalContactService:
    """
    Service for managing external contacts and validating email domains.

    Detects potential fraud by comparing email domains against:
    - Company names derived from documents
    - Known legitimate domains
    - Free email provider lists
    """

    def __init__(self, contact_repo: ExternalContactRepository):
        """
        Initialize service with repository dependency.

        Args:
            contact_repo: Repository for external contact CRUD operations
        """
        self.contact_repo = contact_repo
        self.typosquatting_service = TyposquattingService()
        self.domain_validator = DomainValidationService()

    async def create_contact(
        self,
        assessment_id: str,
        request: ExternalContactRequest,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Create a new external contact for an assessment.

        Args:
            assessment_id: The assessment UUID to associate the contact with
            request: External contact request data
            user_id: ID of the user creating the contact

        Returns:
            dict: Created contact record
        """
        logger.info(f"Creating external contact for assessment {assessment_id}: {request.email}")

        contact_data = {
            'assessment_id': assessment_id,
            'email': request.email.lower().strip(),
            'sender_name': request.sender_name,
            'source': request.source,
            'notes': request.notes,
            'validation_status': ExternalContactValidationStatus.PENDING.value,
            'created_by': user_id,
        }

        return await self.contact_repo.create(contact_data)

    async def get_contacts(self, assessment_id: str) -> List[dict]:
        """
        Get all external contacts for an assessment.

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: List of contact records
        """
        return await self.contact_repo.get_by_assessment(assessment_id)

    async def get_contact(self, contact_id: str) -> Optional[dict]:
        """
        Get a single external contact by ID.

        Args:
            contact_id: Contact UUID

        Returns:
            Optional[dict]: Contact record or None
        """
        return await self.contact_repo.get_by_id(contact_id)

    async def validate_email(
        self,
        contact_id: str,
        company_name: Optional[str] = None,
        known_domains: Optional[List[str]] = None
    ) -> dict:
        """
        Validate an external contact's email domain for typosquatting.

        Args:
            contact_id: Contact UUID to validate
            company_name: Company name to derive expected domain
            known_domains: Additional known legitimate domains

        Returns:
            dict: Updated contact record with validation result
        """
        logger.info(f"Validating email for contact {contact_id}")

        contact = await self.contact_repo.get_by_id(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")

        email = contact['email']
        domain = self._extract_domain(email)

        if not domain:
            # Invalid email format
            validation_result = EmailValidationResult(
                is_suspicious=True,
                similar_domain=None,
                similarity_score=0.0,
                levenshtein_distance=0,
                detection_type='invalid_format',
                description='Formato de email inválido',
                is_free_provider=False,
            )
            validation_status = ExternalContactValidationStatus.CRITICAL
        else:
            # Check if it's a free email provider
            is_free_provider = self.typosquatting_service.is_free_email_provider(domain)

            # Run typosquatting check
            typo_result = self.typosquatting_service.check_domain_typosquatting(
                domain=domain,
                known_domains=known_domains,
                company_name=company_name
            )

            # Run domain validation (DNS and WHOIS)
            domain_exists = None
            domain_age_days = None
            domain_creation_date = None
            age_lookup_status = "pending"
            domain_registrar = None

            # Skip domain validation for free providers
            if not is_free_provider:
                existence_result = self.domain_validator.check_domain_existence(domain)
                domain_exists = existence_result.exists

                if existence_result.exists:
                    age_result = self.domain_validator.get_domain_age(domain)
                    domain_age_days = age_result.age_days
                    domain_creation_date = age_result.creation_date
                    age_lookup_status = age_result.lookup_status
                    domain_registrar = age_result.registrar

            # Determine detection type and suspicion level including domain age
            final_is_suspicious = typo_result.is_suspicious or is_free_provider
            final_detection_type = typo_result.detection_type if not is_free_provider else 'provider_domain'

            # Check for domain existence issues
            if domain_exists is False:
                final_is_suspicious = True
                final_detection_type = 'domain_not_found'

            # Check for young domain
            if domain_age_days is not None and domain_age_days < 90:
                final_is_suspicious = True
                # Only override detection type if not already more severe
                if final_detection_type not in ['typosquatting', 'domain_not_found']:
                    final_detection_type = 'young_domain'

            # Build validation result
            validation_result = EmailValidationResult(
                is_suspicious=final_is_suspicious,
                similar_domain=typo_result.similar_domain,
                similarity_score=typo_result.similarity_score,
                levenshtein_distance=typo_result.levenshtein_distance,
                detection_type=final_detection_type,
                description=self._build_description(typo_result, is_free_provider, domain, domain_exists, domain_age_days),
                is_free_provider=is_free_provider,
                domain_exists=domain_exists,
                domain_age_days=domain_age_days,
                domain_creation_date=domain_creation_date,
                age_lookup_status=age_lookup_status,
                domain_registrar=domain_registrar,
            )

            # Determine validation status
            validation_status = self._determine_status(typo_result, is_free_provider, domain_exists, domain_age_days)

        # Update contact with validation result
        updates = {
            'validation_status': validation_status.value,
            'validation_result': validation_result.model_dump(mode='json'),
            'validated_at': datetime.now(timezone.utc).isoformat(),
        }

        updated_contact = await self.contact_repo.update(contact_id, updates)

        if not updated_contact:
            raise ValueError(f"Failed to update contact {contact_id}")

        logger.info(f"Email validation complete for contact {contact_id}: status={validation_status.value}")

        return updated_contact

    async def delete_contact(self, contact_id: str) -> bool:
        """
        Soft delete an external contact.

        Args:
            contact_id: Contact UUID

        Returns:
            bool: True if successful
        """
        logger.info(f"Deleting external contact {contact_id}")
        return await self.contact_repo.delete(contact_id)

    async def get_suspicious_count(self, assessment_id: str) -> int:
        """
        Get count of suspicious or critical contacts for an assessment.

        Args:
            assessment_id: Assessment UUID

        Returns:
            int: Count of suspicious/critical contacts
        """
        return await self.contact_repo.get_suspicious_count(assessment_id)

    def _extract_domain(self, email: str) -> Optional[str]:
        """
        Extract domain from email address.

        Args:
            email: Email address

        Returns:
            Optional[str]: Domain or None if invalid
        """
        if not email or '@' not in email:
            return None

        try:
            domain = email.split('@')[1].lower().strip()
            # Basic validation
            if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$', domain):
                return None
            return domain
        except (IndexError, AttributeError):
            return None

    def _determine_status(
        self,
        typo_result,
        is_free_provider: bool,
        domain_exists: Optional[bool] = None,
        domain_age_days: Optional[int] = None
    ) -> ExternalContactValidationStatus:
        """
        Determine validation status based on typosquatting, free provider, and domain age checks.

        Args:
            typo_result: Result from TyposquattingService
            is_free_provider: Whether domain is a free email provider
            domain_exists: Whether domain resolves via DNS (None = unknown)
            domain_age_days: Age of domain in days (None = unknown)

        Returns:
            ExternalContactValidationStatus: Appropriate status
        """
        # Critical: Domain doesn't exist
        if domain_exists is False:
            return ExternalContactValidationStatus.CRITICAL

        # Critical: Typosquatting detected (similar but not exact match)
        if typo_result.detection_type == 'typosquatting':
            return ExternalContactValidationStatus.CRITICAL

        # Suspicious: Very young domain (< 90 days)
        if domain_age_days is not None and domain_age_days < 90:
            return ExternalContactValidationStatus.SUSPICIOUS

        # Suspicious: TLD variation or suspicious TLD
        if typo_result.detection_type in ['tld_variation', 'suspicious_tld']:
            return ExternalContactValidationStatus.SUSPICIOUS

        # Suspicious: Free email provider for business contact
        if is_free_provider:
            return ExternalContactValidationStatus.SUSPICIOUS

        # Suspicious: Young domain (< 1 year)
        if domain_age_days is not None and domain_age_days < 365:
            return ExternalContactValidationStatus.SUSPICIOUS

        # Validated: Exact match or no concerning signals
        if typo_result.detection_type == 'exact_match':
            return ExternalContactValidationStatus.VALIDATED

        # Default: Validated (no match found, but not suspicious)
        return ExternalContactValidationStatus.VALIDATED

    def _build_description(
        self,
        typo_result,
        is_free_provider: bool,
        domain: str,
        domain_exists: Optional[bool] = None,
        domain_age_days: Optional[int] = None
    ) -> str:
        """
        Build human-readable description of validation result.

        Args:
            typo_result: Result from TyposquattingService
            is_free_provider: Whether domain is a free email provider
            domain: The email domain being validated
            domain_exists: Whether domain resolves via DNS (None = unknown)
            domain_age_days: Age of domain in days (None = unknown)

        Returns:
            str: Description in Spanish
        """
        # Critical: Domain doesn't exist
        if domain_exists is False:
            return (
                f"ALERTA CRÍTICA: El dominio '{domain}' no existe o no resuelve (DNS). "
                f"Posible dominio fraudulento."
            )

        if is_free_provider and not typo_result.is_suspicious:
            return f"Proveedor de email gratuito: {domain}. Para contactos comerciales, se espera un dominio corporativo."

        if typo_result.detection_type == 'exact_match':
            age_info = ""
            if domain_age_days is not None:
                age_info = f" Antigüedad: {domain_age_days} días."
            return f"Dominio verificado: coincidencia exacta con {typo_result.similar_domain}.{age_info}"

        if typo_result.detection_type == 'typosquatting':
            return (
                f"ALERTA: Posible typosquatting detectado. '{domain}' es similar a "
                f"'{typo_result.similar_domain}' (similitud: {typo_result.similarity_score:.0%})"
            )

        if typo_result.detection_type == 'tld_variation':
            return (
                f"ADVERTENCIA: Variación de TLD detectada. '{domain}' vs "
                f"'{typo_result.similar_domain}'. Verifique que sea el dominio correcto."
            )

        if typo_result.detection_type == 'suspicious_tld':
            return f"ADVERTENCIA: El dominio '{domain}' usa un TLD sospechoso frecuentemente asociado con fraude."

        # Young domain warning
        if domain_age_days is not None and domain_age_days < 90:
            return (
                f"ADVERTENCIA: El dominio '{domain}' tiene solo {domain_age_days} días de antigüedad "
                f"(menos de 90 días). Posible dominio fraudulento reciente."
            )

        if domain_age_days is not None and domain_age_days < 365:
            return (
                f"NOTA: El dominio '{domain}' tiene {domain_age_days} días de antigüedad "
                f"(menos de 1 año). Verifique que sea legítimo."
            )

        if is_free_provider:
            return (
                f"ADVERTENCIA: El dominio '{domain}' es un proveedor de email gratuito "
                f"Y podría ser similar a '{typo_result.similar_domain}'."
            )

        return typo_result.description
