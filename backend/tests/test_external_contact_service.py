"""
Unit tests for External Contact Service

Tests email domain validation, typosquatting detection,
and external contact management functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.servicios.risk.external_contact_service import ExternalContactService
from src.interface.risk_dtos import ExternalContactRequest, ExternalContactValidationStatus


class TestExternalContactService:
    """Test suite for ExternalContactService"""

    @pytest.fixture
    def mock_repo(self):
        """Create mock repository"""
        repo = MagicMock()
        repo.create = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_assessment = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        repo.get_suspicious_count = AsyncMock()
        return repo

    @pytest.fixture
    def service(self, mock_repo):
        """Create service with mocked repository"""
        return ExternalContactService(mock_repo)

    @pytest.mark.asyncio
    async def test_create_contact_success(self, service, mock_repo):
        """Test creating a new external contact"""
        mock_repo.create.return_value = {
            'id': 'test-uuid',
            'assessment_id': 'assessment-123',
            'email': 'test@example.com',
            'sender_name': 'John Doe',
            'source': 'comercial_team',
            'validation_status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
        }

        request = ExternalContactRequest(
            email='test@example.com',
            sender_name='John Doe',
            source='comercial_team',
            notes='Test contact'
        )

        result = await service.create_contact('assessment-123', request, 'user-123')

        assert result['id'] == 'test-uuid'
        assert result['email'] == 'test@example.com'
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contacts(self, service, mock_repo):
        """Test getting all contacts for an assessment"""
        mock_repo.get_by_assessment.return_value = [
            {'id': '1', 'email': 'test1@example.com', 'validation_status': 'pending'},
            {'id': '2', 'email': 'test2@example.com', 'validation_status': 'validated'},
        ]

        result = await service.get_contacts('assessment-123')

        assert len(result) == 2
        mock_repo.get_by_assessment.assert_called_once_with('assessment-123')

    @pytest.mark.asyncio
    async def test_validate_email_not_found(self, service, mock_repo):
        """Test validation when contact not found"""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Contact .* not found"):
            await service.validate_email('nonexistent-id')

    @pytest.mark.asyncio
    async def test_validate_email_typosquatting_detection(self, service, mock_repo):
        """Test validation detects typosquatting"""
        mock_repo.get_by_id.return_value = {
            'id': 'contact-123',
            'email': 'contact@azelis.com.co',
            'validation_status': 'pending',
        }
        mock_repo.update.return_value = {
            'id': 'contact-123',
            'email': 'contact@azelis.com.co',
            'validation_status': 'suspicious',
            'validation_result': {
                'is_suspicious': True,
                'similar_domain': 'azelis.com',
                'detection_type': 'tld_variation',
            },
        }

        result = await service.validate_email(
            'contact-123',
            company_name='Azelis SA',
            known_domains=['azelis.com']
        )

        assert result['validation_status'] == 'suspicious'
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_email_free_provider(self, service, mock_repo):
        """Test validation flags free email providers"""
        mock_repo.get_by_id.return_value = {
            'id': 'contact-123',
            'email': 'contact@gmail.com',
            'validation_status': 'pending',
        }
        mock_repo.update.return_value = {
            'id': 'contact-123',
            'email': 'contact@gmail.com',
            'validation_status': 'suspicious',
            'validation_result': {
                'is_suspicious': True,
                'is_free_provider': True,
                'detection_type': 'provider_domain',
            },
        }

        result = await service.validate_email('contact-123')

        # Should flag as suspicious for free provider
        mock_repo.update.assert_called_once()
        call_args = mock_repo.update.call_args[0]
        updates = call_args[1]
        assert updates['validation_status'] == 'suspicious'

    @pytest.mark.asyncio
    async def test_delete_contact(self, service, mock_repo):
        """Test soft deleting a contact"""
        mock_repo.delete.return_value = True

        result = await service.delete_contact('contact-123')

        assert result is True
        mock_repo.delete.assert_called_once_with('contact-123')

    @pytest.mark.asyncio
    async def test_get_suspicious_count(self, service, mock_repo):
        """Test getting suspicious contact count"""
        mock_repo.get_suspicious_count.return_value = 3

        result = await service.get_suspicious_count('assessment-123')

        assert result == 3
        mock_repo.get_suspicious_count.assert_called_once_with('assessment-123')

    def test_extract_domain_valid(self, service):
        """Test domain extraction from valid email"""
        result = service._extract_domain('test@example.com')
        assert result == 'example.com'

    def test_extract_domain_with_subdomain(self, service):
        """Test domain extraction with subdomain"""
        result = service._extract_domain('test@mail.example.com')
        assert result == 'mail.example.com'

    def test_extract_domain_invalid(self, service):
        """Test domain extraction from invalid email"""
        result = service._extract_domain('invalid-email')
        assert result is None

    def test_extract_domain_empty(self, service):
        """Test domain extraction from empty string"""
        result = service._extract_domain('')
        assert result is None

    def test_extract_domain_none(self, service):
        """Test domain extraction from None"""
        result = service._extract_domain(None)
        assert result is None

    def test_determine_status_typosquatting(self, service):
        """Test status determination for typosquatting"""
        mock_result = MagicMock()
        mock_result.detection_type = 'typosquatting'

        status = service._determine_status(mock_result, False)

        assert status == ExternalContactValidationStatus.CRITICAL

    def test_determine_status_tld_variation(self, service):
        """Test status determination for TLD variation"""
        mock_result = MagicMock()
        mock_result.detection_type = 'tld_variation'

        status = service._determine_status(mock_result, False)

        assert status == ExternalContactValidationStatus.SUSPICIOUS

    def test_determine_status_free_provider(self, service):
        """Test status determination for free provider"""
        mock_result = MagicMock()
        mock_result.detection_type = 'no_match'

        status = service._determine_status(mock_result, True)

        assert status == ExternalContactValidationStatus.SUSPICIOUS

    def test_determine_status_exact_match(self, service):
        """Test status determination for exact match"""
        mock_result = MagicMock()
        mock_result.detection_type = 'exact_match'

        status = service._determine_status(mock_result, False)

        assert status == ExternalContactValidationStatus.VALIDATED


class TestExternalContactRequest:
    """Test ExternalContactRequest validation"""

    def test_valid_email(self):
        """Test valid email passes validation"""
        request = ExternalContactRequest(
            email='test@example.com',
            source='comercial_team'
        )
        assert request.email == 'test@example.com'

    def test_email_normalized(self):
        """Test email is normalized to lowercase"""
        request = ExternalContactRequest(
            email='  TEST@EXAMPLE.COM  ',
            source='comercial_team'
        )
        assert request.email == 'test@example.com'

    def test_invalid_email_raises_error(self):
        """Test invalid email raises validation error"""
        with pytest.raises(ValueError):
            ExternalContactRequest(
                email='invalid-email',
                source='comercial_team'
            )

    def test_empty_email_raises_error(self):
        """Test empty email raises validation error"""
        with pytest.raises(ValueError):
            ExternalContactRequest(
                email='',
                source='comercial_team'
            )
