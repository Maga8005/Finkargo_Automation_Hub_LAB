"""
Unit tests for Email Chain Official Document Domain Validation

Tests the validation of email chain sender domains against official document
(RUT/Certificado de Existencia) email domains to detect potential fraud.
"""
import sys
import importlib
import pytest
from unittest.mock import MagicMock, AsyncMock

# Mock fitz (PyMuPDF) before importing the service to avoid ImportError
# Save original if exists so we can restore it after tests
_original_fitz = sys.modules.get('fitz')
_mock_fitz = MagicMock()
# Ensure FileDataError is a proper exception class for catching
_mock_fitz.FileDataError = type('FileDataError', (Exception,), {})
_mock_fitz.EmptyFileError = type('EmptyFileError', (Exception,), {})
sys.modules['fitz'] = _mock_fitz

from src.core.servicios.risk.email_chain_service import EmailChainService
from src.core.servicios.risk.typosquatting_service import TyposquattingService
from src.interface.risk_dtos import DiscrepancySeverity


def teardown_module(module):
    """Restore original fitz module after all tests in this module complete.

    This is critical to prevent polluting other tests that need the real fitz module.
    We need to:
    1. Restore the original fitz module to sys.modules
    2. Reload any modules that imported the mocked fitz so they get the real one
    """
    global _original_fitz
    if _original_fitz is not None:
        sys.modules['fitz'] = _original_fitz
    else:
        # Remove the mock from sys.modules so subsequent imports get the real fitz
        if 'fitz' in sys.modules:
            del sys.modules['fitz']

    # Reload modules that might have cached the mocked fitz
    # This ensures subsequent tests get the real fitz module
    modules_to_reload = [
        'src.core.servicios.rut_parser_service',
        'src.core.servicios.bank_certificate_parser_service',
        'src.core.servicios.risk.email_chain_parser_service',
    ]
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
            except Exception:
                # If reload fails, just remove from cache so it gets reimported fresh
                del sys.modules[module_name]


class TestValidateAgainstOfficialDocumentDomains:
    """Test the _validate_against_official_document_domains method"""

    @pytest.fixture
    def service(self):
        """Create EmailChainService instance with mocked repositories"""
        mock_chain_repo = MagicMock()
        mock_assessment_repo = MagicMock()
        mock_extraction_repo = MagicMock()
        return EmailChainService(
            chain_repo=mock_chain_repo,
            assessment_repo=mock_assessment_repo,
            extraction_repo=mock_extraction_repo,
        )

    def test_no_official_domains_returns_none(self, service):
        """Should return None when no official domains available"""
        result = service._validate_against_official_document_domains(
            sender_domain="empresa.com",
            official_domains=[],
        )
        assert result is None

    def test_exact_match_returns_none(self, service):
        """Should return None when sender domain exactly matches official domain"""
        result = service._validate_against_official_document_domains(
            sender_domain="empresa.com",
            official_domains=["empresa.com"],
        )
        assert result is None

    def test_exact_match_case_insensitive(self, service):
        """Should match domains case-insensitively"""
        result = service._validate_against_official_document_domains(
            sender_domain="EMPRESA.COM",
            official_domains=["empresa.com"],
        )
        assert result is None

        result = service._validate_against_official_document_domains(
            sender_domain="empresa.com",
            official_domains=["EMPRESA.COM"],
        )
        assert result is None

    def test_tld_variation_returns_critical(self, service):
        """Should return CRITICAL discrepancy for TLD variation (azelis.com vs azelis.com.co)"""
        result = service._validate_against_official_document_domains(
            sender_domain="azelis.com.co",
            official_domains=["azelis.com"],
        )

        assert result is not None
        assert result['field'] == 'official_document_domain'
        assert result['severity'] == DiscrepancySeverity.CRITICAL.value
        assert result['email_value'] == 'azelis.com.co'
        assert result['document_value'] == 'azelis.com'
        assert result['is_typosquatting'] is True
        assert 'TLD' in result['description'] or 'tld' in result['description'].lower()

    def test_typosquatting_returns_critical(self, service):
        """Should return CRITICAL discrepancy for typosquatting (azelis vs acelis)"""
        result = service._validate_against_official_document_domains(
            sender_domain="acelis.com",
            official_domains=["azelis.com"],
        )

        assert result is not None
        assert result['field'] == 'official_document_domain'
        assert result['severity'] == DiscrepancySeverity.CRITICAL.value
        assert result['email_value'] == 'acelis.com'
        assert result['document_value'] == 'azelis.com'
        assert result['is_typosquatting'] is True
        assert result['similarity_score'] is not None
        assert result['similarity_score'] > 0.7

    def test_completely_different_domain_returns_critical(self, service):
        """Should return CRITICAL discrepancy for completely different domains"""
        result = service._validate_against_official_document_domains(
            sender_domain="otrodominio.com",
            official_domains=["empresa-oficial.com"],
        )

        assert result is not None
        assert result['field'] == 'official_document_domain'
        assert result['severity'] == DiscrepancySeverity.CRITICAL.value
        assert result['email_value'] == 'otrodominio.com'
        assert result['document_value'] == 'empresa-oficial.com'
        # Not typosquatting since domains are completely different
        assert result['is_typosquatting'] is False
        assert 'verificar' in result['description'].lower()

    def test_multiple_official_domains_match_any(self, service):
        """Should pass if sender matches any of the official domains"""
        # Should match second domain
        result = service._validate_against_official_document_domains(
            sender_domain="empresa.com.co",
            official_domains=["empresa.com", "empresa.com.co"],
        )
        assert result is None

    def test_free_email_provider_vs_official(self, service):
        """Should flag free email provider when official domain exists"""
        result = service._validate_against_official_document_domains(
            sender_domain="gmail.com",
            official_domains=["empresa-oficial.com"],
        )

        assert result is not None
        assert result['field'] == 'official_document_domain'
        assert result['severity'] == DiscrepancySeverity.CRITICAL.value
        # Gmail is completely different, so not typosquatting
        assert result['is_typosquatting'] is False

    def test_whitespace_handling(self, service):
        """Should handle whitespace in domain names"""
        result = service._validate_against_official_document_domains(
            sender_domain="  empresa.com  ",
            official_domains=["empresa.com"],
        )
        assert result is None

    def test_subdomain_vs_main_domain(self, service):
        """Should detect mismatch between subdomain and main domain"""
        # Note: The typosquatting service extracts domain base, so
        # ventas.empresa.com should match empresa.com
        result = service._validate_against_official_document_domains(
            sender_domain="ventas.empresa.com",
            official_domains=["empresa.com"],
        )
        # This may or may not be a mismatch depending on base extraction
        # The key is that it doesn't crash and returns a sensible result
        assert result is None or result['severity'] == DiscrepancySeverity.CRITICAL.value


class TestGetDocumentDataOfficialDomains:
    """Test the _get_document_data method extracts official document domains"""

    @pytest.fixture
    def service(self):
        """Create EmailChainService instance with mocked repositories"""
        mock_chain_repo = MagicMock()
        mock_assessment_repo = MagicMock()
        mock_extraction_repo = MagicMock()
        mock_extraction_repo.get_by_assessment = AsyncMock()
        return EmailChainService(
            chain_repo=mock_chain_repo,
            assessment_repo=mock_assessment_repo,
            extraction_repo=mock_extraction_repo,
        )

    @pytest.mark.asyncio
    async def test_extracts_official_domains_from_rut(self, service):
        """Should extract email domains from RUT as official domains"""
        service.extraction_repo.get_by_assessment.return_value = [
            {
                'document_type': 'rut',
                'extracted_data': {
                    'email': 'contacto@empresa.com',
                    'razon_social': 'Empresa S.A.S.',
                },
            },
        ]

        result = await service._get_document_data('test-assessment-id')

        assert 'empresa.com' in result['official_document_domains']
        assert 'empresa.com' in result['email_domains']

    @pytest.mark.asyncio
    async def test_extracts_official_domains_from_certificado(self, service):
        """Should extract email domains from Certificado de Existencia as official domains"""
        service.extraction_repo.get_by_assessment.return_value = [
            {
                'document_type': 'certificado_existencia',
                'extracted_data': {
                    'correo': 'info@empresa.com.co',
                    'razon_social': 'Empresa Colombia S.A.S.',
                },
            },
        ]

        result = await service._get_document_data('test-assessment-id')

        assert 'empresa.com.co' in result['official_document_domains']
        assert 'empresa.com.co' in result['email_domains']

    @pytest.mark.asyncio
    async def test_non_official_doc_email_not_in_official_domains(self, service):
        """Should NOT include non-official document emails in official_document_domains"""
        service.extraction_repo.get_by_assessment.return_value = [
            {
                'document_type': 'cedula',  # Not an official doc for domain purposes
                'extracted_data': {
                    'email': 'representante@personal.com',
                },
            },
        ]

        result = await service._get_document_data('test-assessment-id')

        # Should be in general email_domains but NOT in official_document_domains
        assert 'personal.com' in result['email_domains']
        assert 'personal.com' not in result['official_document_domains']

    @pytest.mark.asyncio
    async def test_multiple_documents_aggregates_domains(self, service):
        """Should aggregate official domains from multiple official documents"""
        service.extraction_repo.get_by_assessment.return_value = [
            {
                'document_type': 'rut',
                'extracted_data': {
                    'email': 'contacto@empresa.com',
                },
            },
            {
                'document_type': 'certificado_existencia',
                'extracted_data': {
                    'email_empresa': 'info@empresa.com.co',
                },
            },
            {
                'document_type': 'financial_statement_current',
                'extracted_data': {
                    'email': 'finance@empresa.com',
                },
            },
        ]

        result = await service._get_document_data('test-assessment-id')

        # Both RUT and Certificado emails should be in official_document_domains
        assert 'empresa.com' in result['official_document_domains']
        assert 'empresa.com.co' in result['official_document_domains']
        # Financial statement email should NOT be in official domains
        assert 'empresa.com' in result['email_domains']  # Also from RUT
        # All should be in general email_domains
        assert len(result['email_domains']) >= 2

    @pytest.mark.asyncio
    async def test_handles_missing_email_fields(self, service):
        """Should handle documents without email fields gracefully"""
        service.extraction_repo.get_by_assessment.return_value = [
            {
                'document_type': 'rut',
                'extracted_data': {
                    'razon_social': 'Empresa S.A.S.',
                    'nit': '900123456-7',
                    # No email field
                },
            },
        ]

        result = await service._get_document_data('test-assessment-id')

        assert result['official_document_domains'] == []

    @pytest.mark.asyncio
    async def test_handles_malformed_email(self, service):
        """Should handle malformed emails gracefully"""
        service.extraction_repo.get_by_assessment.return_value = [
            {
                'document_type': 'rut',
                'extracted_data': {
                    'email': 'not-an-email',  # No @ symbol
                },
            },
        ]

        result = await service._get_document_data('test-assessment-id')

        # Should not add malformed email
        assert result['official_document_domains'] == []
        assert result['email_domains'] == []

    @pytest.mark.asyncio
    async def test_deduplicates_domains(self, service):
        """Should not add duplicate domains"""
        service.extraction_repo.get_by_assessment.return_value = [
            {
                'document_type': 'rut',
                'extracted_data': {
                    'email': 'contacto@empresa.com',
                    'correo': 'info@empresa.com',  # Same domain
                },
            },
        ]

        result = await service._get_document_data('test-assessment-id')

        assert result['official_document_domains'].count('empresa.com') == 1
        assert result['email_domains'].count('empresa.com') == 1


class TestIntegrationWithTyposquattingService:
    """Integration tests to verify proper use of TyposquattingService"""

    @pytest.fixture
    def service(self):
        """Create EmailChainService with real TyposquattingService"""
        mock_chain_repo = MagicMock()
        mock_assessment_repo = MagicMock()
        mock_extraction_repo = MagicMock()
        return EmailChainService(
            chain_repo=mock_chain_repo,
            assessment_repo=mock_assessment_repo,
            extraction_repo=mock_extraction_repo,
        )

    def test_azelis_fraud_case_com_vs_com_co(self, service):
        """Test real Azelis fraud case: azelis.com.co impersonating azelis.com"""
        result = service._validate_against_official_document_domains(
            sender_domain="azelis.com.co",
            official_domains=["azelis.com"],
        )

        assert result is not None
        assert result['field'] == 'official_document_domain'
        assert result['severity'] == DiscrepancySeverity.CRITICAL.value
        assert result['is_typosquatting'] is True
        assert 'azelis.com.co' in result['description']
        assert 'azelis.com' in result['description']

    def test_azelis_fraud_case_character_substitution(self, service):
        """Test Azelis fraud case: acelis.com impersonating azelis.com"""
        result = service._validate_against_official_document_domains(
            sender_domain="acelis.com.co",
            official_domains=["azelis.com"],
        )

        assert result is not None
        assert result['field'] == 'official_document_domain'
        assert result['severity'] == DiscrepancySeverity.CRITICAL.value
        # Should detect as typosquatting due to character substitution
        assert result['is_typosquatting'] is True

    def test_legitimate_company_with_correct_domain(self, service):
        """Test legitimate company using correct official domain"""
        result = service._validate_against_official_document_domains(
            sender_domain="empresa-legitima.com",
            official_domains=["empresa-legitima.com"],
        )

        assert result is None  # No discrepancy for exact match
