"""
External Contact Service - Email domain validation for fraud detection

Validates external contact emails against company information to detect
potential typosquatting fraud attempts.
"""
from typing import Optional, List
from datetime import datetime
import logging
import re

from src.repositorio.risk_repository import ExternalContactRepository
from src.core.servicios.risk.typosquatting_service import TyposquattingService
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

            # Build validation result
            validation_result = EmailValidationResult(
                is_suspicious=typo_result.is_suspicious or is_free_provider,
                similar_domain=typo_result.similar_domain,
                similarity_score=typo_result.similarity_score,
                levenshtein_distance=typo_result.levenshtein_distance,
                detection_type=typo_result.detection_type if not is_free_provider else 'provider_domain',
                description=self._build_description(typo_result, is_free_provider, domain),
                is_free_provider=is_free_provider,
            )

            # Determine validation status
            validation_status = self._determine_status(typo_result, is_free_provider)

        # Update contact with validation result
        updates = {
            'validation_status': validation_status.value,
            'validation_result': validation_result.model_dump(),
            'validated_at': datetime.utcnow().isoformat(),
        }

        updated_contact = await self.contact_repo.update(contact_id, updates)
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
        is_free_provider: bool
    ) -> ExternalContactValidationStatus:
        """
        Determine validation status based on typosquatting and free provider checks.

        Args:
            typo_result: Result from TyposquattingService
            is_free_provider: Whether domain is a free email provider

        Returns:
            ExternalContactValidationStatus: Appropriate status
        """
        # Critical: Typosquatting detected (similar but not exact match)
        if typo_result.detection_type == 'typosquatting':
            return ExternalContactValidationStatus.CRITICAL

        # Suspicious: TLD variation or suspicious TLD
        if typo_result.detection_type in ['tld_variation', 'suspicious_tld']:
            return ExternalContactValidationStatus.SUSPICIOUS

        # Suspicious: Free email provider for business contact
        if is_free_provider:
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
        domain: str
    ) -> str:
        """
        Build human-readable description of validation result.

        Args:
            typo_result: Result from TyposquattingService
            is_free_provider: Whether domain is a free email provider
            domain: The email domain being validated

        Returns:
            str: Description in Spanish
        """
        if is_free_provider and not typo_result.is_suspicious:
            return f"Proveedor de email gratuito: {domain}. Para contactos comerciales, se espera un dominio corporativo."

        if typo_result.detection_type == 'exact_match':
            return f"Dominio verificado: coincidencia exacta con {typo_result.similar_domain}"

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

        if is_free_provider:
            return (
                f"ADVERTENCIA: El dominio '{domain}' es un proveedor de email gratuito "
                f"Y podría ser similar a '{typo_result.similar_domain}'."
            )

        return typo_result.description
