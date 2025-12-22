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
- Email domain verification
"""
import re
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from difflib import SequenceMatcher

from src.interface.risk_dtos import (
    DocumentType,
    ValidationType,
    DiscrepancySeverity,
    CrossValidationResult,
)

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
    """

    # Known legitimate company domains for typosquatting detection
    KNOWN_DOMAINS = [
        'azelis.com', 'basf.com', 'dow.com', 'dupont.com',
        'evonik.com', 'lanxess.com', 'brenntag.com', 'univar.com',
    ]

    # Score impact by severity
    SCORE_IMPACT = {
        DiscrepancySeverity.CRITICAL: Decimal('25'),
        DiscrepancySeverity.HIGH: Decimal('15'),
        DiscrepancySeverity.MEDIUM: Decimal('8'),
        DiscrepancySeverity.LOW: Decimal('3'),
    }

    def __init__(self):
        """Initialize cross-validation service."""
        pass

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

        # 2. NIT consistency validation
        nit_result = self._validate_nit_consistency(extractions)
        if nit_result:
            results.append(nit_result)

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

        # 6. Email domain validation
        email_result = self._validate_email_domain(extractions)
        if email_result:
            results.append(email_result)

        # 7. Address consistency validation
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

        This is a CRITICAL check - the Azelis case showed company names
        like "ROCSA COLOMBIA S.A." vs "AZELIS COLOMBIA S.A.S."
        """
        company_names = {}
        for doc_type, data in extractions.items():
            if data and data.get('company_name'):
                company_names[doc_type.value] = self._normalize_company_name(data['company_name'])

        if len(company_names) < 2:
            return None

        # Find unique normalized names
        unique_names = set(company_names.values())
        documents_compared = list(company_names.keys())

        if len(unique_names) == 1:
            # All names match
            return CrossValidationResult(
                validation_type=ValidationType.COMPANY_NAME,
                documents_compared=documents_compared,
                field_compared="company_name",
                values_found={k: extractions[DocumentType(k)].get('company_name', '') for k in documents_compared if DocumentType(k) in extractions},
                is_discrepancy=False,
                severity=None,
                description="Nombre de empresa consistente en todos los documentos",
                score_impact=Decimal('0')
            )

        # Found discrepancy - CRITICAL severity
        raw_names = {k: extractions[DocumentType(k)].get('company_name', '') for k in documents_compared if DocumentType(k) in extractions}

        return CrossValidationResult(
            validation_type=ValidationType.COMPANY_NAME,
            documents_compared=documents_compared,
            field_compared="company_name",
            values_found=raw_names,
            is_discrepancy=True,
            severity=DiscrepancySeverity.CRITICAL,
            description=f"ALERTA: Nombres de empresa diferentes detectados: {', '.join(set(raw_names.values()))}",
            score_impact=self.SCORE_IMPACT[DiscrepancySeverity.CRITICAL]
        )

    def _validate_nit_consistency(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> Optional[CrossValidationResult]:
        """
        Check NIT consistency across all documents.

        CRITICAL check - NIT should be identical across all documents.
        """
        nits = {}
        for doc_type, data in extractions.items():
            if data and data.get('nit'):
                nits[doc_type.value] = self._normalize_nit(data['nit'])

        if len(nits) < 2:
            return None

        unique_nits = set(nits.values())
        documents_compared = list(nits.keys())

        if len(unique_nits) == 1:
            return CrossValidationResult(
                validation_type=ValidationType.NIT,
                documents_compared=documents_compared,
                field_compared="nit",
                values_found={k: extractions[DocumentType(k)].get('nit', '') for k in documents_compared if DocumentType(k) in extractions},
                is_discrepancy=False,
                severity=None,
                description="NIT consistente en todos los documentos",
                score_impact=Decimal('0')
            )

        # Found discrepancy - CRITICAL
        raw_nits = {k: extractions[DocumentType(k)].get('nit', '') for k in documents_compared if DocumentType(k) in extractions}

        return CrossValidationResult(
            validation_type=ValidationType.NIT,
            documents_compared=documents_compared,
            field_compared="nit",
            values_found=raw_nits,
            is_discrepancy=True,
            severity=DiscrepancySeverity.CRITICAL,
            description=f"ALERTA CRÍTICA: NITs diferentes detectados en documentos: {', '.join(set(raw_nits.values()))}",
            score_impact=self.SCORE_IMPACT[DiscrepancySeverity.CRITICAL]
        )

    def _validate_legal_representative(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> List[CrossValidationResult]:
        """
        Validate legal representative identity across Cedula, RUT, and Certificado.

        HIGH severity check - name and ID must match across documents.
        """
        results = []

        # Get legal rep data from relevant documents
        cedula_data = extractions.get(DocumentType.CEDULA, {}) or {}
        rut_data = extractions.get(DocumentType.RUT, {}) or {}
        cert_data = extractions.get(DocumentType.CERTIFICADO_EXISTENCIA, {}) or {}

        # Extract names
        names = {}
        if cedula_data.get('full_name'):
            names['cedula'] = self._normalize_name(cedula_data['full_name'])
        if rut_data.get('legal_representative_name'):
            names['rut'] = self._normalize_name(rut_data['legal_representative_name'])
        if cert_data.get('legal_representative_name'):
            names['certificado_existencia'] = self._normalize_name(cert_data['legal_representative_name'])

        # Check name consistency
        if len(names) >= 2:
            unique_names = set(names.values())
            raw_names = {
                'cedula': cedula_data.get('full_name', ''),
                'rut': rut_data.get('legal_representative_name', ''),
                'certificado_existencia': cert_data.get('legal_representative_name', '')
            }
            raw_names = {k: v for k, v in raw_names.items() if v}

            if len(unique_names) == 1:
                results.append(CrossValidationResult(
                    validation_type=ValidationType.LEGAL_REPRESENTATIVE,
                    documents_compared=list(names.keys()),
                    field_compared="legal_representative_name",
                    values_found=raw_names,
                    is_discrepancy=False,
                    severity=None,
                    description="Nombre del representante legal consistente",
                    score_impact=Decimal('0')
                ))
            else:
                results.append(CrossValidationResult(
                    validation_type=ValidationType.LEGAL_REPRESENTATIVE,
                    documents_compared=list(names.keys()),
                    field_compared="legal_representative_name",
                    values_found=raw_names,
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.HIGH,
                    description=f"Nombres de representante legal no coinciden: {', '.join(raw_names.values())}",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.HIGH]
                ))

        # Extract IDs
        ids = {}
        if cedula_data.get('document_number'):
            ids['cedula'] = self._normalize_id(cedula_data['document_number'])
        if rut_data.get('legal_representative_id'):
            ids['rut'] = self._normalize_id(rut_data['legal_representative_id'])
        if cert_data.get('legal_representative_id'):
            ids['certificado_existencia'] = self._normalize_id(cert_data['legal_representative_id'])

        # Check ID consistency
        if len(ids) >= 2:
            unique_ids = set(ids.values())
            raw_ids = {
                'cedula': cedula_data.get('document_number', ''),
                'rut': rut_data.get('legal_representative_id', ''),
                'certificado_existencia': cert_data.get('legal_representative_id', '')
            }
            raw_ids = {k: v for k, v in raw_ids.items() if v}

            if len(unique_ids) == 1:
                results.append(CrossValidationResult(
                    validation_type=ValidationType.LEGAL_REPRESENTATIVE,
                    documents_compared=list(ids.keys()),
                    field_compared="legal_representative_id",
                    values_found=raw_ids,
                    is_discrepancy=False,
                    severity=None,
                    description="Cédula del representante legal consistente",
                    score_impact=Decimal('0')
                ))
            else:
                results.append(CrossValidationResult(
                    validation_type=ValidationType.LEGAL_REPRESENTATIVE,
                    documents_compared=list(ids.keys()),
                    field_compared="legal_representative_id",
                    values_found=raw_ids,
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.HIGH,
                    description=f"Cédulas del representante legal no coinciden: {', '.join(raw_ids.values())}",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.HIGH]
                ))

        return results

    def _validate_shareholders_vs_certificate(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> Optional[CrossValidationResult]:
        """
        Check if majority shareholder appears in board of directors.

        MEDIUM severity - ghost shareholders may indicate fraud.
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

        # Check if majority shareholder is on board
        board_names = [self._normalize_name(m.get('name', '')) for m in board_members if isinstance(m, dict)]
        normalized_majority = self._normalize_name(majority_shareholder)

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

        MEDIUM severity - extreme changes may indicate manipulation.
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
                    values_found={'current': current_revenue, 'prior': prior_revenue, 'growth_pct': round(growth_rate, 1)},
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
                    values_found={'current': current_revenue, 'prior': prior_revenue, 'growth_pct': round(growth_rate, 1)},
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.MEDIUM,
                    description=f"Caída de ingresos anómala: {round(growth_rate, 1)}% año a año",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
                ))

        return results

    def _validate_email_domain(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> Optional[CrossValidationResult]:
        """
        Check email domain for typosquatting against known companies.

        HIGH severity - the Azelis case used acelis.com.co vs azelis.com
        """
        rut_data = extractions.get(DocumentType.RUT, {}) or {}
        email = rut_data.get('email', '')

        if not email or '@' not in email:
            return None

        domain = email.split('@')[1].lower()
        company_name = rut_data.get('company_name', '')

        # Check for typosquatting of known domains
        for known_domain in self.KNOWN_DOMAINS:
            known_base = known_domain.split('.')[0]
            domain_base = domain.split('.')[0]

            # Skip if exact match
            if known_base == domain_base:
                continue

            # Check for similar names (potential typosquatting)
            similarity = SequenceMatcher(None, known_base, domain_base).ratio()
            if similarity > 0.7 and similarity < 1.0:
                return CrossValidationResult(
                    validation_type=ValidationType.EMAIL_DOMAIN,
                    documents_compared=['rut'],
                    field_compared="email",
                    values_found={
                        'email': email,
                        'domain': domain,
                        'similar_to': known_domain,
                        'similarity': round(similarity * 100, 1)
                    },
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.HIGH,
                    description=f"POSIBLE TYPOSQUATTING: Dominio '{domain}' similar a '{known_domain}' ({round(similarity * 100)}% similitud)",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.HIGH]
                )

        # Check if email domain matches company name pattern
        if company_name:
            company_base = self._extract_company_domain_base(company_name)
            if company_base and company_base not in domain:
                return CrossValidationResult(
                    validation_type=ValidationType.EMAIL_DOMAIN,
                    documents_compared=['rut'],
                    field_compared="email",
                    values_found={
                        'email': email,
                        'company_name': company_name,
                        'expected_domain_contains': company_base
                    },
                    is_discrepancy=True,
                    severity=DiscrepancySeverity.MEDIUM,
                    description=f"Dominio de email '{domain}' no parece corresponder a la empresa '{company_name}'",
                    score_impact=self.SCORE_IMPACT[DiscrepancySeverity.MEDIUM]
                )

        return CrossValidationResult(
            validation_type=ValidationType.EMAIL_DOMAIN,
            documents_compared=['rut'],
            field_compared="email",
            values_found={'email': email},
            is_discrepancy=False,
            severity=None,
            description="Dominio de email verificado",
            score_impact=Decimal('0')
        )

    def _validate_address_consistency(
        self,
        extractions: Dict[DocumentType, dict]
    ) -> Optional[CrossValidationResult]:
        """
        Check address consistency between RUT and Certificate.

        MEDIUM severity - different addresses may indicate fraud.
        """
        rut_data = extractions.get(DocumentType.RUT, {}) or {}
        cert_data = extractions.get(DocumentType.CERTIFICADO_EXISTENCIA, {}) or {}

        rut_city = rut_data.get('city', '')
        cert_city = cert_data.get('city', '')

        if not rut_city or not cert_city:
            return None

        normalized_rut_city = self._normalize_city(rut_city)
        normalized_cert_city = self._normalize_city(cert_city)

        if normalized_rut_city == normalized_cert_city:
            return CrossValidationResult(
                validation_type=ValidationType.ADDRESS,
                documents_compared=['rut', 'certificado_existencia'],
                field_compared="city",
                values_found={'rut': rut_city, 'certificado': cert_city},
                is_discrepancy=False,
                severity=None,
                description="Ciudad de registro consistente",
                score_impact=Decimal('0')
            )

        return CrossValidationResult(
            validation_type=ValidationType.ADDRESS,
            documents_compared=['rut', 'certificado_existencia'],
            field_compared="city",
            values_found={'rut': rut_city, 'certificado': cert_city},
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

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison."""
        if not name:
            return ''
        # Remove common suffixes and normalize
        normalized = name.upper().strip()
        for suffix in ['S.A.S.', 'S.A.S', 'SAS', 'S.A.', 'S.A', 'SA', 'LTDA', 'LTDA.', 'E.U.', 'EU']:
            normalized = normalized.replace(suffix, '')
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = ' '.join(normalized.split())
        return normalized

    def _normalize_nit(self, nit: str) -> str:
        """Normalize NIT for comparison."""
        if not nit:
            return ''
        # Remove all non-digits
        return re.sub(r'[^\d]', '', nit)

    def _normalize_name(self, name: str) -> str:
        """Normalize person name for comparison."""
        if not name:
            return ''
        normalized = name.upper().strip()
        # Remove accents
        replacements = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ñ': 'N'}
        for k, v in replacements.items():
            normalized = normalized.replace(k, v)
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        return normalized

    def _normalize_id(self, id_num: str) -> str:
        """Normalize ID number for comparison."""
        if not id_num:
            return ''
        # Remove all non-alphanumeric
        return re.sub(r'[^\w]', '', id_num.upper())

    def _normalize_city(self, city: str) -> str:
        """Normalize city name for comparison."""
        if not city:
            return ''
        normalized = city.upper().strip()
        # Remove accents
        replacements = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ñ': 'N'}
        for k, v in replacements.items():
            normalized = normalized.replace(k, v)
        # Common abbreviations
        normalized = normalized.replace('D.C.', '').replace('DC', '')
        normalized = normalized.replace('BOGOTA', 'BOGOTA')
        return normalized.strip()

    def _names_match(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """Check if two names match with fuzzy matching."""
        if not name1 or not name2:
            return False
        if name1 == name2:
            return True
        similarity = SequenceMatcher(None, name1, name2).ratio()
        return similarity >= threshold

    def _extract_company_domain_base(self, company_name: str) -> Optional[str]:
        """Extract expected domain base from company name."""
        if not company_name:
            return None
        # Remove legal suffixes
        normalized = self._normalize_company_name(company_name)
        # Take first word as base
        words = normalized.split()
        if words:
            return words[0].lower()
        return None
