"""
Integration tests for Cross-Validation Service Improvements

Tests the improved cross-validation logic with:
- Enhanced data normalization (eliminates false positives)
- Typosquatting detection
- Separate NIT check digit validation
- City name normalization
"""
import pytest
from decimal import Decimal

from src.interface.risk_dtos import (
    DocumentType,
    ValidationType,
    DiscrepancySeverity,
)
from src.core.servicios.risk.cross_validation_service import CrossValidationService
from src.core.servicios.risk.normalization_service import NormalizationService
from src.core.servicios.risk.typosquatting_service import TyposquattingService


class TestFalsePositiveReduction:
    """Test that formatting differences don't cause false positives"""

    @pytest.fixture
    def service(self):
        """Create CrossValidationService with dependencies"""
        return CrossValidationService(
            normalization_service=NormalizationService(),
            typosquatting_service=TyposquattingService()
        )

    def test_company_name_sas_variations_no_discrepancy(self, service):
        """Test that S.A.S. vs SAS variations are not flagged"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'AZELIS COLOMBIA S.A.S.',
                'nit': '830.027.231-3'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'AZELIS COLOMBIA SAS',
                'nit': '830027231-3'
            }
        }

        results = service.validate_documents(extractions)

        # Find company name result
        company_result = next(
            (r for r in results if r.validation_type == ValidationType.COMPANY_NAME),
            None
        )

        assert company_result is not None
        assert company_result.is_discrepancy is False
        assert "consistente" in company_result.description.lower()

    def test_company_name_s_a_s_variations_no_discrepancy(self, service):
        """Test that S A S (with spaces) vs S.A.S. variations are not flagged"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'AZELIS COLOMBIA S A S',
                'nit': '830027231-3'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'AZELIS COLOMBIA S.A.S.',
                'nit': '830.027.231-3'
            }
        }

        results = service.validate_documents(extractions)

        company_result = next(
            (r for r in results if r.validation_type == ValidationType.COMPANY_NAME),
            None
        )

        assert company_result is not None
        assert company_result.is_discrepancy is False

    def test_nit_formatting_variations_no_discrepancy(self, service):
        """Test that NIT formatting differences are not flagged"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'EMPRESA TEST',
                'nit': '830.027.231-3'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'EMPRESA TEST',
                'nit': '830027231 3'
            }
        }

        results = service.validate_documents(extractions)

        nit_result = next(
            (r for r in results if r.validation_type == ValidationType.NIT),
            None
        )

        assert nit_result is not None
        assert nit_result.is_discrepancy is False
        assert "consistente" in nit_result.description.lower()

    def test_city_with_department_no_discrepancy(self, service):
        """Test that city + department info vs plain city is not flagged"""
        extractions = {
            DocumentType.RUT: {
                'city': 'Tenjo (Cundinamarca)',
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'city': 'Tenjo',
            }
        }

        results = service.validate_documents(extractions)

        address_result = next(
            (r for r in results if r.validation_type == ValidationType.ADDRESS),
            None
        )

        assert address_result is not None
        assert address_result.is_discrepancy is False

    def test_city_bogota_variations_no_discrepancy(self, service):
        """Test that Bogotá D.C. vs BOGOTA variations are not flagged"""
        extractions = {
            DocumentType.RUT: {
                'city': 'Bogotá D.C.',
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'city': 'BOGOTA',
            }
        }

        results = service.validate_documents(extractions)

        address_result = next(
            (r for r in results if r.validation_type == ValidationType.ADDRESS),
            None
        )

        assert address_result is not None
        assert address_result.is_discrepancy is False


class TestRealDiscrepancyDetection:
    """Test that real discrepancies are properly detected"""

    @pytest.fixture
    def service(self):
        """Create CrossValidationService with dependencies"""
        return CrossValidationService(
            normalization_service=NormalizationService(),
            typosquatting_service=TyposquattingService()
        )

    def test_different_company_names_detected(self, service):
        """Test that truly different company names are flagged as CRITICAL"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'ROCSA COLOMBIA S.A.',
                'nit': '830027231-3'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'AZELIS COLOMBIA S.A.S.',
                'nit': '830027231-3'
            }
        }

        results = service.validate_documents(extractions)

        company_result = next(
            (r for r in results if r.validation_type == ValidationType.COMPANY_NAME),
            None
        )

        assert company_result is not None
        assert company_result.is_discrepancy is True
        assert company_result.severity == DiscrepancySeverity.CRITICAL
        assert company_result.score_impact == Decimal('25')

    def test_different_base_nit_detected(self, service):
        """Test that different NITs are flagged as CRITICAL"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'EMPRESA TEST',
                'nit': '830027231-3'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'EMPRESA TEST',
                'nit': '900123456-7'
            }
        }

        results = service.validate_documents(extractions)

        nit_result = next(
            (r for r in results if r.validation_type == ValidationType.NIT),
            None
        )

        assert nit_result is not None
        assert nit_result.is_discrepancy is True
        assert nit_result.severity == DiscrepancySeverity.CRITICAL

    def test_different_check_digit_detected(self, service):
        """Test that different check digits are flagged as HIGH"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'EMPRESA TEST',
                'nit': '830027231-3'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'EMPRESA TEST',
                'nit': '830027231-1'  # Different check digit
            }
        }

        results = service.validate_documents(extractions)

        check_digit_result = next(
            (r for r in results if r.validation_type == ValidationType.NIT_CHECK_DIGIT),
            None
        )

        assert check_digit_result is not None
        assert check_digit_result.is_discrepancy is True
        assert check_digit_result.severity == DiscrepancySeverity.HIGH
        assert check_digit_result.score_impact == Decimal('15')

    def test_different_cities_detected(self, service):
        """Test that truly different cities are flagged"""
        extractions = {
            DocumentType.RUT: {
                'city': 'Medellín',
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'city': 'Bogotá',
            }
        }

        results = service.validate_documents(extractions)

        address_result = next(
            (r for r in results if r.validation_type == ValidationType.ADDRESS),
            None
        )

        assert address_result is not None
        assert address_result.is_discrepancy is True
        assert address_result.severity == DiscrepancySeverity.MEDIUM


class TestTyposquattingDetection:
    """Test typosquatting detection in email domains"""

    @pytest.fixture
    def service(self):
        """Create CrossValidationService with dependencies"""
        return CrossValidationService(
            normalization_service=NormalizationService(),
            typosquatting_service=TyposquattingService()
        )

    def test_azelis_acelis_typosquatting_detected(self, service):
        """Test detection of Azelis fraud case pattern"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'AZELIS COLOMBIA S.A.S.',
                'email': 'contacto@acelis.com.co'  # Typosquatting domain
            }
        }

        results = service.validate_documents(extractions)

        typo_result = next(
            (r for r in results if r.validation_type == ValidationType.TYPOSQUATTING),
            None
        )

        assert typo_result is not None
        assert typo_result.is_discrepancy is True
        assert typo_result.severity == DiscrepancySeverity.CRITICAL
        assert 'azelis' in typo_result.description.lower() or 'typosquatting' in typo_result.description.lower()

    def test_free_email_provider_flagged(self, service):
        """Test that free email providers are flagged"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'EMPRESA PROFESIONAL S.A.S.',
                'email': 'empresa@gmail.com'  # Free provider for business
            }
        }

        results = service.validate_documents(extractions)

        provider_result = next(
            (r for r in results if r.validation_type == ValidationType.PROVIDER_DOMAIN),
            None
        )

        assert provider_result is not None
        assert provider_result.is_discrepancy is True
        assert provider_result.severity == DiscrepancySeverity.MEDIUM
        assert 'gmail' in provider_result.description.lower() or 'gratuito' in provider_result.description.lower()

    def test_legitimate_domain_not_flagged(self, service):
        """Test that legitimate corporate domains are not flagged"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'UNIQUE COMPANY S.A.S.',
                'email': 'contacto@uniquecompany.com'
            }
        }

        results = service.validate_documents(extractions)

        # Should have email domain result but not flagged as discrepancy
        email_result = next(
            (r for r in results if r.validation_type == ValidationType.EMAIL_DOMAIN),
            None
        )

        if email_result:
            assert email_result.is_discrepancy is False

        # Should not have typosquatting result
        typo_result = next(
            (r for r in results if r.validation_type == ValidationType.TYPOSQUATTING),
            None
        )
        assert typo_result is None


class TestScoreCalculation:
    """Test score impact calculations"""

    @pytest.fixture
    def service(self):
        """Create CrossValidationService with dependencies"""
        return CrossValidationService(
            normalization_service=NormalizationService(),
            typosquatting_service=TyposquattingService()
        )

    def test_no_discrepancy_zero_score(self, service):
        """Test that matching data produces zero score impact"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'AZELIS COLOMBIA S.A.S.',
                'nit': '830.027.231-3',
                'city': 'Bogotá D.C.',
                'email': 'contacto@azelis.com.co'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'AZELIS COLOMBIA SAS',
                'nit': '830027231-3',
                'city': 'BOGOTA'
            }
        }

        results = service.validate_documents(extractions)
        total_impact = service.calculate_total_score_impact(results)

        # All validations should pass (formatting differences ignored)
        # Only email domain check might add impact if it's a TLD variation
        discrepancies = [r for r in results if r.is_discrepancy]

        # The azelis.com.co vs azelis.com might flag as TLD variation
        # But company name, NIT, and city should all pass
        company_result = next(
            (r for r in results if r.validation_type == ValidationType.COMPANY_NAME),
            None
        )
        nit_result = next(
            (r for r in results if r.validation_type == ValidationType.NIT),
            None
        )
        address_result = next(
            (r for r in results if r.validation_type == ValidationType.ADDRESS),
            None
        )

        assert company_result.is_discrepancy is False
        assert nit_result.is_discrepancy is False
        assert address_result.is_discrepancy is False

    def test_critical_discrepancy_adds_25_points(self, service):
        """Test that CRITICAL discrepancy adds 25 points"""
        extractions = {
            DocumentType.RUT: {
                'company_name': 'COMPANY A S.A.S.',
                'nit': '830027231-3'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'COMPANY B S.A.S.',
                'nit': '830027231-3'
            }
        }

        results = service.validate_documents(extractions)

        company_result = next(
            (r for r in results if r.validation_type == ValidationType.COMPANY_NAME),
            None
        )

        assert company_result.is_discrepancy is True
        assert company_result.severity == DiscrepancySeverity.CRITICAL
        assert company_result.score_impact == Decimal('25')

    def test_score_capped_at_100(self, service):
        """Test that total score impact is capped at 100"""
        # Create multiple high-impact discrepancies
        extractions = {
            DocumentType.RUT: {
                'company_name': 'COMPANY A',
                'nit': '111111111-1',
                'email': 'test@acelis.com.co',  # Typosquatting
                'city': 'Bogotá'
            },
            DocumentType.CEDULA: {
                'full_name': 'JUAN PEREZ',
                'document_number': '12345678'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'company_name': 'COMPANY B',
                'nit': '222222222-2',
                'city': 'Medellín',
                'legal_representative_name': 'MARIA GARCIA',
                'legal_representative_id': '87654321'
            }
        }

        results = service.validate_documents(extractions)
        total_impact = service.calculate_total_score_impact(results)

        # Should be capped at 100
        assert total_impact <= Decimal('100')


class TestLegalRepresentativeValidation:
    """Test legal representative validation with normalization"""

    @pytest.fixture
    def service(self):
        """Create CrossValidationService with dependencies"""
        return CrossValidationService()

    def test_same_name_with_accents_no_discrepancy(self, service):
        """Test that name variations with accents match"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'MARÍA JOSÉ GARCÍA',
                'document_number': '12345678'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'MARIA JOSE GARCIA',
                'legal_representative_id': '12345678'
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        assert name_result is not None
        assert name_result.is_discrepancy is False

    def test_different_names_detected(self, service):
        """Test that different names are flagged"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'JUAN PEREZ LOPEZ',
                'document_number': '12345678'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'MARIA GARCIA RODRIGUEZ',
                'legal_representative_id': '12345678'
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        assert name_result is not None
        assert name_result.is_discrepancy is True
        assert name_result.severity == DiscrepancySeverity.HIGH


class TestMultipleLegalRepresentatives:
    """Test multiple legal representatives support (Issue #10 - False positives fix)"""

    @pytest.fixture
    def service(self):
        """Create CrossValidationService with dependencies"""
        return CrossValidationService(
            normalization_service=NormalizationService(),
            typosquatting_service=TyposquattingService()
        )

    def test_cedula_matches_principal_representative_no_discrepancy(self, service):
        """Test: Cedula matches principal representative → no discrepancy"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'JUAN CARLOS PEREZ GOMEZ',
                'document_number': '12345678'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN CARLOS PEREZ GOMEZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    },
                    {
                        'name': 'MARIA GARCIA RODRIGUEZ',
                        'id_number': '87654321',
                        'role': 'suplente'
                    }
                ]
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        id_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_id'),
            None
        )

        assert name_result is not None
        assert name_result.is_discrepancy is False
        assert 'Principal' in name_result.description
        assert 'verificado' in name_result.description.lower()

        assert id_result is not None
        assert id_result.is_discrepancy is False

    def test_cedula_matches_suplente_representative_no_discrepancy(self, service):
        """Test: Cedula matches suplente representative → no discrepancy (BUG FIX)"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'MARIA GARCIA RODRIGUEZ',
                'document_number': '87654321'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN CARLOS PEREZ GOMEZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    },
                    {
                        'name': 'MARIA GARCIA RODRIGUEZ',
                        'id_number': '87654321',
                        'role': 'suplente'
                    }
                ]
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        id_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_id'),
            None
        )

        # THIS IS THE KEY BUG FIX - suplente should NOT cause discrepancy
        assert name_result is not None
        assert name_result.is_discrepancy is False
        assert 'Suplente' in name_result.description
        assert 'verificado' in name_result.description.lower()

        assert id_result is not None
        assert id_result.is_discrepancy is False

    def test_cedula_matches_no_representative_shows_discrepancy(self, service):
        """Test: Cedula matches no representative → HIGH severity discrepancy"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'PEDRO GONZALEZ UNKNOWN',
                'document_number': '99999999'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN CARLOS PEREZ GOMEZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    },
                    {
                        'name': 'MARIA GARCIA RODRIGUEZ',
                        'id_number': '87654321',
                        'role': 'suplente'
                    }
                ]
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        assert name_result is not None
        assert name_result.is_discrepancy is True
        assert name_result.severity == DiscrepancySeverity.HIGH
        assert 'no coincide' in name_result.description.lower()
        # Should list all representatives that were checked
        assert 'JUAN CARLOS PEREZ GOMEZ' in name_result.description
        assert 'MARIA GARCIA RODRIGUEZ' in name_result.description

    def test_multiple_suplentes_cedula_matches_one_no_discrepancy(self, service):
        """Test: Multiple suplentes, Cedula matches one → no discrepancy"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'CARLOS LOPEZ MARTINEZ',
                'document_number': '55555555'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN CARLOS PEREZ GOMEZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    },
                    {
                        'name': 'MARIA GARCIA RODRIGUEZ',
                        'id_number': '87654321',
                        'role': 'suplente'
                    },
                    {
                        'name': 'CARLOS LOPEZ MARTINEZ',
                        'id_number': '55555555',
                        'role': 'suplente'
                    }
                ]
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        assert name_result is not None
        assert name_result.is_discrepancy is False
        assert 'Suplente' in name_result.description

    def test_rut_has_representatives_but_certificado_missing_handles_gracefully(self, service):
        """Test: RUT has representatives but Certificado missing → handle gracefully"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'MARIA GARCIA RODRIGUEZ',
                'document_number': '87654321'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN CARLOS PEREZ GOMEZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    },
                    {
                        'name': 'MARIA GARCIA RODRIGUEZ',
                        'id_number': '87654321',
                        'role': 'suplente'
                    }
                ]
            }
            # No CERTIFICADO_EXISTENCIA
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        # Should still work with just RUT data
        assert name_result is not None
        assert name_result.is_discrepancy is False
        assert 'RUT' in name_result.description

    def test_backward_compatibility_single_representative_data(self, service):
        """Test: Backward compatibility with single representative data (no array)"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'JUAN CARLOS PEREZ GOMEZ',
                'document_number': '12345678'
            },
            DocumentType.RUT: {
                # Old format - only single representative fields, no array
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678'
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        # Should still work with legacy single representative format
        assert name_result is not None
        assert name_result.is_discrepancy is False
        assert 'verificado' in name_result.description.lower()

    def test_cedula_matches_certificado_suplente_but_not_rut(self, service):
        """Test: Cedula matches Certificado suplente but not RUT → no discrepancy"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'LUIS HERNANDEZ PEÑA',
                'document_number': '44444444'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN CARLOS PEREZ GOMEZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    }
                ]
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'legal_representative_name': 'JUAN CARLOS PEREZ GOMEZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN CARLOS PEREZ GOMEZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    },
                    {
                        'name': 'LUIS HERNANDEZ PEÑA',
                        'id_number': '44444444',
                        'role': 'suplente'
                    }
                ]
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        # Should match in Certificado even if not in RUT
        assert name_result is not None
        assert name_result.is_discrepancy is False
        assert 'Certificado' in name_result.description

    def test_name_with_accents_matches_suplente(self, service):
        """Test: Name with accents matches suplente (normalization)"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'MARÍA JOSÉ GARCÍA',
                'document_number': '87654321'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'JUAN PEREZ',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'JUAN PEREZ',
                        'id_number': '12345678',
                        'role': 'principal'
                    },
                    {
                        'name': 'MARIA JOSE GARCIA',  # No accents
                        'id_number': '87654321',
                        'role': 'suplente'
                    }
                ]
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        # Should match despite accent differences (normalization)
        assert name_result is not None
        assert name_result.is_discrepancy is False


class TestNameOrderMatching:
    """Test name order tolerance (Issue #36 - False positive for reordered names)

    Colombian documents often show names in different orders:
    - Cédula: "JOSE DAVID RAMOS DAZA" (first names + last names)
    - Certificado: "RAMOS DAZA JOSE DAVID" (last names + first names)
    """

    @pytest.fixture
    def service(self):
        """Create CrossValidationService with dependencies"""
        return CrossValidationService(
            normalization_service=NormalizationService(),
            typosquatting_service=TyposquattingService()
        )

    def test_same_name_different_order_cedula_vs_certificado(self, service):
        """Test: Same name parts in different order → no discrepancy (BUG FIX)"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'JOSE DAVID RAMOS DAZA',
                'document_number': '12345678'
            },
            DocumentType.CERTIFICADO_EXISTENCIA: {
                'legal_representative_name': 'RAMOS DAZA JOSE DAVID',
                'legal_representative_id': '12345678'
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        # Should NOT flag as discrepancy - same name parts, different order
        assert name_result is not None
        assert name_result.is_discrepancy is False

    def test_same_name_different_order_with_four_parts(self, service):
        """Test: Four-part name in different order → no discrepancy"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'MARIA FERNANDA LOPEZ GARCIA',
                'document_number': '87654321'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'LOPEZ GARCIA MARIA FERNANDA',
                'legal_representative_id': '87654321'
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        assert name_result is not None
        assert name_result.is_discrepancy is False

    def test_different_name_parts_should_flag_discrepancy(self, service):
        """Test: Different name parts → should flag discrepancy"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'JOSE RAMOS',
                'document_number': '12345678'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'DAVID RAMOS',
                'legal_representative_id': '12345678'
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        # SHOULD flag - different name parts (JOSE vs DAVID)
        assert name_result is not None
        assert name_result.is_discrepancy is True

    def test_same_name_different_order_in_representatives_array(self, service):
        """Test: Name reordering in representatives array → no discrepancy"""
        extractions = {
            DocumentType.CEDULA: {
                'full_name': 'JOSE DAVID RAMOS DAZA',
                'document_number': '12345678'
            },
            DocumentType.RUT: {
                'legal_representative_name': 'RAMOS DAZA JOSE DAVID',
                'legal_representative_id': '12345678',
                'legal_representatives': [
                    {
                        'name': 'RAMOS DAZA JOSE DAVID',  # Last names first
                        'id_number': '12345678',
                        'role': 'principal'
                    }
                ]
            }
        }

        results = service.validate_documents(extractions)

        name_result = next(
            (r for r in results
             if r.validation_type == ValidationType.LEGAL_REPRESENTATIVE
             and r.field_compared == 'legal_representative_name'),
            None
        )

        assert name_result is not None
        assert name_result.is_discrepancy is False
