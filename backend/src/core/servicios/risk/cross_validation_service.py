"""
Cross-Validation Service - Document discrepancy detection for fraud prevention

Compares extracted data from multiple documents to identify inconsistencies
that may indicate document manipulation or fraud attempts.

Based on the Azelis fraud case analysis, validates:
- Company name consistency across documents
- NIT matching across all documents
- Legal representative identity validation
- Shareholder composition alignment
- Financial statement continuity
- Email domain verification with typosquatting detection

IMPROVEMENTS (Fraud Detection Cross-Validation):
- Enhanced data normalization to eliminate false positives from formatting differences
- Typosquatting detection using similarity algorithms
- NIT check digit separate validation
- City normalization with department/region removal
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from difflib import SequenceMatcher

from src.interface.risk_dtos import (
    DocumentType,
    ValidationType,
    DiscrepancySeverity,
    CrossValidationResult,
)
from .normalization_service import NormalizationService
from .typosquatting_service import TyposquattingService
from .domain_validation_service import DomainValidationService

logger = logging.getLogger(__name__)


class CrossValidationService:
    """
    Service for cross-validating extracted document data.

    Identifies discrepancies between documents that may indicate:
    - Identity fraud (company name mismatch)
    - NIT manipulation
    - Fake legal representative documents
    - Shareholder falsification
    - Financial statement manipulation
    - Email typosquatting

    Uses NormalizationService to eliminate false positives from formatting
    differences and TyposquattingService for domain similarity detection.
    """

    # Score impact by severity
    SCORE_IMPACT = {
        DiscrepancySeverity.CRITICAL: Decimal('25'),
        DiscrepancySeverity.HIGH: Decimal('15'),
        DiscrepancySeverity.MEDIUM: Decimal('8'),
        DiscrepancySeverity.LOW: Decimal('3'),
    }

    def __init__(
        self,
        normalization_service: Optional[NormalizationService] = None,
        typosquatting_service: Optional[TyposquattingService] = None,
        domain_validation_service: Optional[DomainValidationService] = None
    ):
        """
        Initialize cross-validation service.

        Args:
            normalization_service: Service for data normalization (auto-created if None)
            typosquatting_service: Service for typosquatting detection (auto-created if None)
            domain_validation_service: Service for domain DNS/WHOIS validation (auto-created if None)
        """
        self.normalizer = normalization_service or NormalizationService()
        self.typosquatting = typosquatting_service or TyposquattingService()
        self.domain_validator = domain_validation_service or DomainValidationService()

    def validate_documents(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> List[CrossValidationResult]:
        """
        Run all cross-validation checks on extracted document data.

        Args:
            extractions: Dictionary mapping DocumentType to extracted data

        Returns:
            List[CrossValidationResult]: All validation results including discrepancies
        """
        logger.info(f"Starting cross-validation for {len(extractions)} documents")

        results = []

        # 1. Company name validation across all documents
        company_result = self._validate_company_names(extractions)
        if company_result:
            results.append(company_result)

        # 2. NIT consistency validation (enhanced with check digit detection)
        nit_results = self._validate_nit_consistency(extractions)
        results.extend(nit_results)

        # 3. Legal representative validation
        legal_rep_results = self._validate_legal_representative(extractions)
        results.extend(legal_rep_results)

        # 4. Shareholder vs certificate validation
        shareholder_result = self._validate_shareholders_vs_certificate(extractions)
        if shareholder_result:
            results.append(shareholder_result)

        # 5. Financial statement continuity
        financial_results = self._validate_financial_statements(extractions)
        results.extend(financial_results)

        # 6. Email domain validation (enhanced with typosquatting detection)
        email_results = self._validate_email_domain(extractions)
        results.extend(email_results)

        # 7. Domain age validation (DNS lookup and WHOIS age check)
        domain_age_results = self._validate_domain_age(extractions)
        results.extend(domain_age_results)

        # 8. Address consistency validation (enhanced with normalization)
        address_result = self._validate_address_consistency(extractions)
        if address_result:
            results.append(address_result)

        discrepancy_count = sum(1 for r in results if r.is_discrepancy)
        logger.info(f"Cross-validation complete: {len(results)} checks, {discrepancy_count} discrepancies")

        return results

    def _validate_company_names(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> Optional[CrossValidationResult]:
        """
        Check company name consistency across all documents.

        Uses enhanced normalization to eliminate false positives from
        formatting differences (e.g., "S.A.S." vs "SAS" vs "S A S").

        Only flags as discrepancy when the NORMALIZED names differ,
        indicating potentially different companies.
        """
        company_names = {}
        normalized_names = {}

        for doc_type, data in extractions.items():
            if data and data.get('company_name'):
                raw_name = data['company_name']
                company_names[doc_type.value] = raw_name
                normalized_names[doc_type.value] = self.normalizer.normalize_company_name(raw_name)

        if len(normalized_names) < 2:
            return None

        # Find unique normalized names
        unique_normalized = set(normalized_names.values())
        documents_compared = list(normalized_names.keys())

        if len(unique_normalized) == 1:
            # All normalized names match - formatting difference only
            return CrossValidationResult(
                validation_type=ValidationType.COMPANY_NAME,
                documents_compared=documents_compared,
                field_compared="company_name",
                values_found={
                    k: company_names.get(k, '') for k in documents_compared
                },
                is_discrepancy=False,
                severity=None,
                description="Nombre de empresa consistente en todos los documentos (diferencias de formato ignoradas)",
                score_impact=Decimal('0')
            )

        # Found real discrepancy - normalized names differ
        return CrossValidationResult(
            validation_type=ValidationType.COMPANY_NAME,
            documents_compared=documents_compared,
            field_compared="company_name",
            values_found={
                k: company_names.get(k, '') for k in documents_compared
            },
            is_discrepancy=True,
            severity=DiscrepancySeverity.CRITICAL,
            description=f"ALERTA: Nombres de empresa diferentes detectados (después de normalización): "
                       f"{', '.join(unique_normalized)}",
            score_impact=self.SCORE_IMPACT[DiscrepancySeverity.CRITICAL]
        )

    def _validate_nit_consistency(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> List[CrossValidationResult]:
        """
        Check NIT consistency across all documents.

        Enhanced validation:
        - Separates base NIT digits from check digit
        - Ignores formatting differences (dots, dashes, spaces)
        - Flags CRITICAL if base NIT differs
        - Flags HIGH if only check digit differs (possible data entry error)
        """
        results = []
        nit_data = {}

        for doc_type, data in extractions.items():
            if data and data.get('nit'):
                raw_nit = data['nit']
                base, check = self.normalizer.normalize_nit(raw_nit)
                nit_data[doc_type.value] = {
                    'raw': raw_nit,
                    'base': base,
                    'check': check
                }

        if len(nit_data) < 2:
            return results

        documents_compared = list(nit_data.keys())

        # Check base NIT consistency
        unique_bases = set(d['base'] for d in nit_data.values())
        raw_nits = {k: nit_data[k]['raw'] for k in documents_compared}

        if len(unique_bases) > 1:
            # Base NITs differ - CRITICAL
            results.append(CrossValidationResult(
                validation_type=ValidationType.NIT,
                documents_compared=documents_compared,
                field_compared="nit",
                values_found=raw_nits,
                is_discrepancy=True,
                severity=DiscrepancySeverity.CRITICAL,
                description=f"ALERTA CRÍTICA: NITs base diferentes: {', '.join(unique_bases)}",
                score_impact=self.SCORE_IMPACT[DiscrepancySeverity.CRITICAL]
            ))
        else:
            # Base NITs match - check for check digit discrepancy
            check_digits = {
                k: v['check'] for k, v in nit_data.items()
                if v['check'] is not None
            }

            if len(check_digits) >= 2:
                unique_checks = set(check_digits.values())

                if len(unique_checks) > 1:
                    # Check digits differ - HIGH severity (data entry error)
                    results.append(CrossValidationResult(
                        validation_type=ValidationType.NIT_CHECK_DIGIT,
                        documents_compared=list(check_digits.keys()),
                        field_compared="nit_check_digit",
                        values_found={
                            k: f"DV: {check_digits[k]}" for k in check_digits
                        },
                        is_discrepancy=True,
                        severity=DiscrepancySeverity.HIGH,
                        description=f"Dígitos de verificación NIT diferentes: {', '.join(unique_checks)} "
                                   "(posible error de digitación)",
                        score_impact=self.SCORE_IMPACT[DiscrepancySeverity.HIGH]
                    ))
                else:
                    # All match
                    results.append(CrossValidationResult(
                        validation_type=ValidationType.NIT,
                        documents_compared=documents_compared,
                        field_compared="nit",
                        values_found=raw_nits,
                        is_discrepancy=False,
                        severity=None,
                        description="NIT consistente en todos los documentos (diferencias de formato ignoradas)",
                        score_impact=Decimal('0')
                    ))
            else:
                # Not enough check digits to compare, but bases match
                results.append(CrossValidationResult(
                    validation_type=ValidationType.NIT,
                    documents_compared=documents_compared,
                    field_compared="nit",
                    values_found=raw_nits,
                    is_discrepancy=False,
                    severity=None,
                    description="NIT base consistente en todos los documentos",
                    score_impact=Decimal('0')
                ))

        return results

    def _validate_legal_representative(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> List[CrossValidationResult]:
        """
        Validate legal representative identity across Cedula, RUT, and Certificado.

        Enhanced to support multiple legal representatives (principal and suplente).
        The Cedula document is checked against ALL representatives in RUT and Certificado,
        not just the principal one. This prevents false positives when the uploaded
        Cedula belongs to a Representante Legal Suplente.

        Uses enhanced normalization for name comparison.
        """
        results = []

        # Get legal rep data from relevant documents
        cedula_data = extractions.get(DocumentType.CEDULA, {}) or {}
        rut_data = extractions.get(DocumentType.RUT, {}) or {}
        cert_data = extractions.get(DocumentType.CERTIFICADO_EXISTENCIA, {}) or {}

        # Extract Cedula person info (the person we need to verify)
        cedula_name = cedula_data.get('full_name', '')
        cedula_id = cedula_data.get('document_number', '')

        if not cedula_name and not cedula_id:
            # No Cedula data to validate
            return results

        normalized_cedula_name = self.normalizer.normalize_person_name(cedula_name) if cedula_name else ''
        normalized_cedula_id = self._normalize_id(cedula_id) if cedula_id else ''

        # Extract ALL legal representatives from RUT (supports multiple)
        rut_representatives = self._extract_all_representatives(rut_data, 'rut')

        # Extract ALL legal representatives from Certificado (supports multiple)
        cert_representatives = self._extract_all_representatives(cert_data, 'certificado_existencia')

        # Validate name: Check if Cedula person matches ANY representative
        name_result = self._validate_cedula_against_representatives(
            cedula_name=cedula_name,
            normalized_cedula_name=normalized_cedula_name,
            rut_representatives=rut_representatives,
            cert_representatives=cert_representatives,
            field_type='name'
        )
        if name_result:
            results.append(name_result)

        # Validate ID: Check if Cedula ID matches ANY representative
        id_result = self._validate_cedula_against_representatives(
            cedula_name=cedula_id,  # Reuse param for the value
            normalized_cedula_name=normalized_cedula_id,  # Reuse param for normalized value
            rut_representatives=rut_representatives,
            cert_representatives=cert_representatives,
            field_type='id'
        )
        if id_result:
            results.append(id_result)

        return results

    def _extract_all_representatives(
        self,
        doc_data: dict,
        source: str
    ) -> List[Dict[str, Any]]:
        """
        Extract all legal representatives from a document.

        Supports both the new `legal_representatives` array and the legacy
        single `legal_representative_name`/`legal_representative_id` fields
        for backward compatibility.

        Args:
            doc_data: Extracted document data
            source: Source document name for logging

        Returns:
            List of representative dicts with normalized name/id and role
        """
        representatives = []

        # First, try to get from the new legal_representatives array
        legal_reps_array = doc_data.get('legal_representatives', [])
        if legal_reps_array and isinstance(legal_reps_array, list):
            for rep in legal_reps_array:
                if isinstance(rep, dict):
                    name = rep.get('name', '')
                    id_num = rep.get('id_number', '')
                    role = rep.get('role', 'principal')  # Default to principal if not specified

                    if name or id_num:
                        representatives.append({
                            'name': name,
                            'normalized_name': self.normalizer.normalize_person_name(name) if name else '',
                            'id_number': id_num,
                            'normalized_id': self._normalize_id(id_num) if id_num else '',
                            'role': role,
                            'source': source
                        })

        # Fallback: Use legacy single representative fields if array is empty
        if not representatives:
            legacy_name = doc_data.get('legal_representative_name', '')
            legacy_id = doc_data.get('legal_representative_id', '')

            if legacy_name or legacy_id:
                representatives.append({
                    'name': legacy_name,
                    'normalized_name': self.normalizer.normalize_person_name(legacy_name) if legacy_name else '',
                    'id_number': legacy_id,
                    'normalized_id': self._normalize_id(legacy_id) if legacy_id else '',
                    'role': 'principal',  # Legacy data assumed to be principal
                    'source': source
                })

        logger.debug(f"Extracted {len(representatives)} representatives from {source}")
        return representatives

    def _validate_cedula_against_representatives(
        self,
        cedula_name: str,
        normalized_cedula_name: str,
        rut_representatives: List[Dict[str, Any]],
        cert_representatives: List[Dict[str, Any]],
        field_type: str  # 'name' or 'id'
    ) -> Optional[CrossValidationResult]:
        """
        Check if Cedula data matches ANY representative in RUT or Certificado.

        Args:
            cedula_name: Raw Cedula value (name or ID depending on field_type)
            normalized_cedula_name: Normalized Cedula value
            rut_representatives: List of representatives from RUT
            cert_representatives: List of representatives from Certificado
            field_type: Either 'name' or 'id'

        Returns:
            CrossValidationResult or None if no documents to compare
        """
        if not normalized_cedula_name:
            return None

        if not rut_representatives and not cert_representatives:
            return None

        # Determine which field to compare
        if field_type == 'name':
            field_compared = "legal_representative_name"
            cedula_label = "Nombre"
            match_key = 'normalized_name'
            raw_key = 'name'
        else:
            field_compared = "legal_representative_id"
            cedula_label = "Cédula"
            match_key = 'normalized_id'
            raw_key = 'id_number'

        # Check for match in RUT representatives
        rut_match = None
        rut_all_values = []
        for rep in rut_representatives:
            rut_all_values.append(f"{rep[raw_key]} ({rep['role']})")
            if rep[match_key] and self._values_match(normalized_cedula_name, rep[match_key], field_type):
                rut_match = rep

        # Check for match in Certificado representatives
        cert_match = None
        cert_all_values = []
        for rep in cert_representatives:
            cert_all_values.append(f"{rep[raw_key]} ({rep['role']})")
            if rep[match_key] and self._values_match(normalized_cedula_name, rep[match_key], field_type):
                cert_match = rep

        # Build documents compared list
        documents_compared = ['cedula']
        if rut_representatives:
            documents_compared.append('rut')
        if cert_representatives:
            documents_compared.append('certificado_existencia')

        # Build values_found dict
        values_found = {'cedula': cedula_name}
        if rut_representatives:
            values_found['rut_representatives'] = rut_all_values
        if cert_representatives:
            values_found['certificado_representatives'] = cert_all_values

        # Determine result
        if rut_match or cert_match:
            # Found a match!
            matched_role = (rut_match or cert_match)['role']
            matched_name = (rut_match or cert_match)[raw_key]
            matched_sources = []
            if rut_match:
                matched_sources.append('RUT')
            if cert_match:
                matched_sources.append('Certificado')

            role_display = "Principal" if matched_role == 'principal' else "Suplente"

            return CrossValidationResult(
                validation_type=ValidationType.LEGAL_REPRESENTATIVE,
                documents_compared=documents_compared,
                field_compared=field_compared,
                values_found=values_found,
                is_discrepancy=False,
                severity=None,
                description=f"{cedula_label} del representante legal verificado: {matched_name} ({role_display}) - "
                           f"Coincide con {', '.join(matched_sources)}",
                score_impact=Decimal('0')
            )
        else:
            # No match found - this is a discrepancy
            all_rep_names = []
            for rep in rut_representatives + cert_representatives:
                rep_info = f"{rep[raw_key]} ({rep['role']}, {rep['source']})"
                if rep_info not in all_rep_names:
                    all_rep_names.append(rep_info)

            return CrossValidationResult(
                validation_type=ValidationType.LEGAL_REPRESENTATIVE,
                documents_compared=documents_compared,
                field_compared=field_compared,
                values_found=values_found,
                is_discrepancy=True,
                severity=DiscrepancySeverity.HIGH,
                description=f"{cedula_label} en cédula ({cedula_name}) no coincide con ningún representante legal. "
                           f"Representantes encontrados: {', '.join(all_rep_names) if all_rep_names else 'ninguno'}",
                score_impact=self.SCORE_IMPACT[DiscrepancySeverity.HIGH]
            )

    def _values_match(self, value1: str, value2: str, field_type: str) -> bool:
        """
        Check if two values match based on field type.

        For names, uses fuzzy matching. For IDs, uses exact match after normalization.
        """
        if not value1 or not value2:
            return False

        if field_type == 'name':
            # Use fuzzy matching for names
            return self._names_match(value1, value2)
        else:
            # Use exact match for IDs (already normalized)
            return value1 == value2

    def _validate_shareholders_vs_certificate(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> Optional[CrossValidationResult]:
        """
        Check if majority shareholder appears in board of directors.
        """
        comp_data = extractions.get(DocumentType.COMPOSICION_ACCIONARIA, {}) or {}
        cert_data = extractions.get(DocumentType.CERTIFICADO_EXISTENCIA, {}) or {}

        majority_shareholder = comp_data.get('majority_shareholder_name', '')
        shareholders = comp_data.get('shareholders', [])
        board_members = cert_data.get('board_members', [])

        if not majority_shareholder and shareholders:
            # Find majority from list
            if isinstance(shareholders, list) and shareholders:
                max_percentage = 0
                for sh in shareholders:
                    if isinstance(sh, dict) and sh.get('percentage', 0) > max_percentage:
                        max_percentage = sh.get('percentage', 0)
                        majority_shareholder = sh.get('name', '')

        if not majority_shareholder or not board_members:
            return None

        # Check if majority shareholder is on board using normalized names
        board_names = [
            self.normalizer.normalize_person_name(m.get('name', ''))
            for m in board_members if isinstance(m, dict)
        ]
        normalized_majority = self.normalizer.normalize_person_name(majority_shareholder)

        found_on_board = any(
            self._names_match(normalized_majority, bn) for bn in board_names
        )

        return CrossValidationResult(
            validation_type=ValidationType.SHAREHOLDERS,
            documents_compared=['composicion_accionaria', 'certificado_existencia'],
            field_compared="majority_shareholder",
            values_found={
                'majority_shareholder': majority_shareholder,
                'board_members': [m.get('name', '') for m in board_members if isinstance(m, dict)]
            },
            is_discrepancy=not found_on_board,
            severity=DiscrepancySeverity.MEDIUM if not found_on_board else None,
            description="Accionista mayoritario verificado en junta directiva" if found_on_board else
                       f"Accionista mayoritario '{majority_shareholder}' no aparece en junta directiva",
            score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM] if not found_on_board else Decimal('0')
        )

    def _validate_financial_statements(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> List[CrossValidationResult]:
        """
        Validate year-over-year financial continuity.
        """
        results = []

        current = extractions.get(DocumentType.FINANCIAL_STATEMENT_CURRENT, {}) or {}
        prior = extractions.get(DocumentType.FINANCIAL_STATEMENT_PRIOR, {}) or {}

        if not current or not prior:
            return results

        # Check fiscal year sequence
        current_year = current.get('fiscal_year')
        prior_year = prior.get('fiscal_year')

        if current_year and prior_year:
            if current_year - prior_year != 1:
                results.append(CrossValidationResult(
                    validation_type=ValidationType.FINANCIAL_CONTINUITY,
                    documents_compared=['financial_statement_current', 'financial_statement_prior'],
                    field_compared="fiscal_year",
                    values_found={'current': current_year, 'prior': prior_year},
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.MEDIUM,
                    description=f"Años fiscales no consecutivos: {prior_year} → {current_year}",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
                ))

        # Check revenue growth (flag >500% as suspicious)
        current_revenue = current.get('revenue')
        prior_revenue = prior.get('revenue')

        if current_revenue and prior_revenue and prior_revenue > 0:
            growth_rate = (current_revenue - prior_revenue) / prior_revenue * 100

            if growth_rate > 500:
                results.append(CrossValidationResult(
                    validation_type=ValidationType.FINANCIAL_CONTINUITY,
                    documents_compared=['financial_statement_current', 'financial_statement_prior'],
                    field_compared="revenue",
                    values_found={
                        'current': current_revenue,
                        'prior': prior_revenue,
                        'growth_pct': round(growth_rate, 1)
                    },
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.MEDIUM,
                    description=f"Crecimiento de ingresos anómalo: {round(growth_rate, 1)}% año a año",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
                ))
            elif growth_rate < -80:
                results.append(CrossValidationResult(
                    validation_type=ValidationType.FINANCIAL_CONTINUITY,
                    documents_compared=['financial_statement_current', 'financial_statement_prior'],
                    field_compared="revenue",
                    values_found={
                        'current': current_revenue,
                        'prior': prior_revenue,
                        'growth_pct': round(growth_rate, 1)
                    },
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.MEDIUM,
                    description=f"Caída de ingresos anómala: {round(growth_rate, 1)}% año a año",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
                ))

        return results

    def _validate_email_domain(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> List[CrossValidationResult]:
        """
        Check email domain for typosquatting and validity.

        Enhanced validation using TyposquattingService:
        - Detects domain similarity (e.g., acelis.com.co vs azelis.com)
        - Detects TLD variations
        - Flags free email providers for business use
        - Validates against company name-derived expected domain
        """
        results = []

        rut_data = extractions.get(DocumentType.RUT, {}) or {}
        email = rut_data.get('email', '')

        if not email or '@' not in email:
            return results

        domain = self.normalizer.extract_email_domain(email)
        if not domain:
            return results

        # Build known domains list - only use DEFAULT_KNOWN_DOMAINS
        # NOTE: We do NOT derive a domain from company_name because the RUT email
        # domain IS the official domain. Previously, deriving "company.com" from the
        # company name caused false positives when the RUT had a different TLD like
        # "company.com.co" (the actual official domain from the government document).
        known_domains = list(self.typosquatting.DEFAULT_KNOWN_DOMAINS)

        # Check for typosquatting against known legitimate domains only
        # Do NOT pass company_name - the RUT domain is authoritative
        typo_result = self.typosquatting.check_domain_typosquatting(
            domain,
            known_domains=known_domains
        )

        if typo_result.is_suspicious:
            if typo_result.detection_type == 'typosquatting':
                # High severity - likely fraud attempt
                results.append(CrossValidationResult(
                    validation_type=ValidationType.TYPOSQUATTING,
                    documents_compared=['rut'],
                    field_compared="email_domain",
                    values_found={
                        'email': email,
                        'domain': domain,
                        'similar_to': typo_result.similar_domain,
                        'similarity': f"{typo_result.similarity_score:.0%}",
                        'levenshtein_distance': typo_result.levenshtein_distance
                    },
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.CRITICAL,
                    description=typo_result.description,
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.CRITICAL]
                ))
            elif typo_result.detection_type == 'tld_variation':
                # Medium severity - needs verification
                results.append(CrossValidationResult(
                    validation_type=ValidationType.EMAIL_DOMAIN,
                    documents_compared=['rut'],
                    field_compared="email_domain",
                    values_found={
                        'email': email,
                        'domain': domain,
                        'expected_domain': typo_result.similar_domain
                    },
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.MEDIUM,
                    description=f"Variación de TLD detectada: {domain} vs {typo_result.similar_domain}",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
                ))
            elif typo_result.detection_type == 'suspicious_tld':
                results.append(CrossValidationResult(
                    validation_type=ValidationType.EMAIL_DOMAIN,
                    documents_compared=['rut'],
                    field_compared="email_domain",
                    values_found={
                        'email': email,
                        'domain': domain
                    },
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.HIGH,
                    description=typo_result.description,
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.HIGH]
                ))

        # Check for free email provider used for business
        if self.typosquatting.is_free_email_provider(domain):
            results.append(CrossValidationResult(
                validation_type=ValidationType.PROVIDER_DOMAIN,
                documents_compared=['rut'],
                field_compared="email_domain",
                values_found={
                    'email': email,
                    'domain': domain,
                    'provider_type': 'free_email'
                },
                is_discrepancy=True,
                severity=DiscrepancySeverity.MEDIUM,
                description=f"Uso de proveedor de email gratuito ({domain}) para cuenta empresarial",
                score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
            ))

        # If no issues found, add success result
        if not results:
            results.append(CrossValidationResult(
                validation_type=ValidationType.EMAIL_DOMAIN,
                documents_compared=['rut'],
                field_compared="email",
                values_found={'email': email, 'domain': domain},
                is_discrepancy=False,
                severity=None,
                description="Dominio de email verificado - sin indicadores de typosquatting",
                score_impact=Decimal('0')
            ))

        return results

    def _validate_domain_age(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> List[CrossValidationResult]:
        """
        Validate domain existence (DNS) and age (WHOIS) against company age.

        Detects potentially fraudulent domains by:
        - Checking if the domain exists (DNS resolution)
        - Looking up domain registration date via WHOIS
        - Comparing domain age against company constitution/registration date

        Uses company dates from Certificado or RUT for age comparison.
        """
        results = []

        # Get email domain from RUT
        rut_data = extractions.get(DocumentType.RUT, {}) or {}
        email = rut_data.get('email', '')

        if not email or '@' not in email:
            return results

        domain = self.normalizer.extract_email_domain(email)
        if not domain:
            return results

        # Get company dates for age comparison
        cert_data = extractions.get(DocumentType.CERTIFICADO_EXISTENCIA, {}) or {}

        # Prefer constitution date from certificate, fallback to registration date from RUT
        company_constitution_date = None
        company_registration_date = None

        # Try to extract from certificate
        constitution_str = cert_data.get('constitution_date') or cert_data.get('fecha_constitucion')
        if constitution_str:
            company_constitution_date = self._parse_date(constitution_str)

        # Fallback to RUT registration date
        registration_str = rut_data.get('registration_date') or rut_data.get('fecha_inscripcion_rut')
        if registration_str:
            company_registration_date = self._parse_date(registration_str)

        # Perform domain age validation
        comparison = self.domain_validator.compare_domain_vs_company_age(
            domain=domain,
            company_registration_date=company_registration_date,
            company_constitution_date=company_constitution_date
        )

        # Determine validation type based on result
        if not comparison.is_suspicious:
            # Domain is OK, but still record the check for audit purposes
            values_found = {
                'email': email,
                'domain': domain,
                'domain_age_days': comparison.domain_age_days,
            }
            if comparison.company_age_days:
                values_found['company_age_days'] = comparison.company_age_days

            results.append(CrossValidationResult(
                validation_type=ValidationType.DOMAIN_AGE,
                documents_compared=['rut'] + (['certificado_existencia'] if company_constitution_date else []),
                field_compared="email_domain_age",
                values_found=values_found,
                is_discrepancy=False,
                severity=None,
                description=comparison.reason,
                score_impact=Decimal('0')
            ))
        else:
            # Domain is suspicious
            if comparison.severity == 'critical':
                # Domain doesn't exist - use DOMAIN_EXISTENCE type
                results.append(CrossValidationResult(
                    validation_type=ValidationType.DOMAIN_EXISTENCE,
                    documents_compared=['rut'],
                    field_compared="email_domain",
                    values_found={'email': email, 'domain': domain},
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.CRITICAL,
                    description=comparison.reason,
                    score_impact=Decimal(str(comparison.score_impact))
                ))
            else:
                # Domain age issue - use DOMAIN_AGE type
                severity = DiscrepancySeverity.HIGH if comparison.severity == 'high' else DiscrepancySeverity.MEDIUM
                values_found = {
                    'email': email,
                    'domain': domain,
                    'domain_age_days': comparison.domain_age_days,
                }
                if comparison.company_age_days:
                    values_found['company_age_days'] = comparison.company_age_days
                if comparison.company_registration_date:
                    values_found['company_registration_date'] = comparison.company_registration_date.isoformat()

                results.append(CrossValidationResult(
                    validation_type=ValidationType.DOMAIN_AGE,
                    documents_compared=['rut'] + (['certificado_existencia'] if company_constitution_date else []),
                    field_compared="email_domain_age",
                    values_found=values_found,
                    is_discrepancy=True,
                    severity=severity,
                    description=comparison.reason,
                    score_impact=Decimal(str(comparison.score_impact))
                ))

        return results

    def _parse_date(self, date_str: str) -> Optional["datetime"]:
        """
        Parse a date string into datetime.

        Supports common formats from document extraction.
        """
        from datetime import datetime as dt, timezone as tz
        if not date_str:
            return None

        # Already a datetime
        if isinstance(date_str, dt):
            if date_str.tzinfo is None:
                return date_str.replace(tzinfo=tz.utc)
            return date_str

        # Common date formats from Colombian documents
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%d de %B de %Y',  # Spanish format
        ]

        for fmt in formats:
            try:
                parsed = dt.strptime(str(date_str).strip(), fmt)
                return parsed.replace(tzinfo=tz.utc)
            except ValueError:
                continue

        logger.debug(f"Could not parse date: {date_str}")
        return None

    def _validate_address_consistency(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> Optional[CrossValidationResult]:
        """
        Check address consistency between RUT and Certificate.

        Uses enhanced city normalization to handle:
        - Parenthetical department info (Tenjo (Cundinamarca) → TENJO)
        - Accent variations (Medellín → MEDELLIN)
        - Common city name variations (Bogotá D.C. → BOGOTA)
        """
        rut_data = extractions.get(DocumentType.RUT, {}) or {}
        cert_data = extractions.get(DocumentType.CERTIFICADO_EXISTENCIA, {}) or {}

        rut_city = rut_data.get('city', '')
        cert_city = cert_data.get('city', '')

        if not rut_city or not cert_city:
            return None

        normalized_rut_city = self.normalizer.normalize_city(rut_city)
        normalized_cert_city = self.normalizer.normalize_city(cert_city)

        if normalized_rut_city == normalized_cert_city:
            return CrossValidationResult(
                validation_type=ValidationType.ADDRESS,
                documents_compared=['rut', 'certificado_existencia'],
                field_compared="city",
                values_found={'rut': rut_city, 'certificado': cert_city},
                is_discrepancy=False,
                severity=None,
                description="Ciudad de registro consistente (diferencias de formato ignoradas)",
                score_impact=Decimal('0')
            )

        # Real city difference
        return CrossValidationResult(
            validation_type=ValidationType.ADDRESS,
            documents_compared=['rut', 'certificado_existencia'],
            field_compared="city",
            values_found={
                'rut': rut_city,
                'certificado': cert_city,
                'normalized_rut': normalized_rut_city,
                'normalized_cert': normalized_cert_city
            },
            is_discrepancy=True,
            severity=DiscrepancySeverity.MEDIUM,
            description=f"Ciudades diferentes: RUT indica '{rut_city}', Certificado indica '{cert_city}'",
            score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
        )

    def calculate_total_score_impact(
        self,
        results: List[CrossValidationResult]
    ) -> Decimal:
        """Calculate total score impact from all discrepancies."""
        total = Decimal('0')
        for result in results:
            if result.is_discrepancy and result.score_impact:
                total += result.score_impact
        return min(total, Decimal('100'))  # Cap at 100

    # ==================== Helper Methods ====================

    def _normalize_id(self, id_num: str) -> str:
        """Normalize ID number for comparison."""
        if not id_num:
            return ''
        # Remove all non-alphanumeric, keep uppercase
        import re
        return re.sub(r'[^\w]', '', id_num.upper())

    def _names_match(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """Check if two names match with fuzzy matching."""
        if not name1 or not name2:
            return False
        if name1 == name2:
            return True
        similarity = SequenceMatcher(None, name1, name2).ratio()
        return similarity >= threshold
