"""
Email Chain Service - Email chain upload and cross-validation for fraud detection

Handles:
- Email chain upload (file or text)
- Parsing email content
- Cross-validation against document-extracted data
- Discrepancy detection with severity levels
"""
from typing import Optional, List
from datetime import datetime, timezone
import logging

from src.repositorio.risk_repository import (
    EmailChainRepository,
    RiskAssessmentRepository,
    DocumentExtractionRepository,
)
from src.core.servicios.risk.email_chain_parser_service import EmailChainParserService
from src.core.servicios.risk.typosquatting_service import TyposquattingService
from src.core.servicios.risk.normalization_service import NormalizationService
from src.core.servicios.risk.domain_validation_service import DomainValidationService
from src.interface.risk_dtos import (
    EmailChainValidationStatus,
    DiscrepancySeverity,
)

logger = logging.getLogger(__name__)


class EmailChainService:
    """
    Service for managing email chains and cross-validating against documents.

    Detects potential fraud by comparing email chain data against:
    - Company names from documents
    - NITs from documents
    - Representative names from documents
    - Email domains from documents
    """

    def __init__(
        self,
        chain_repo: EmailChainRepository,
        assessment_repo: RiskAssessmentRepository,
        extraction_repo: DocumentExtractionRepository,
    ):
        """
        Initialize service with repository dependencies.

        Args:
            chain_repo: Repository for email chain CRUD
            assessment_repo: Repository for assessment data
            extraction_repo: Repository for document extractions
        """
        self.chain_repo = chain_repo
        self.assessment_repo = assessment_repo
        self.extraction_repo = extraction_repo
        self.parser_service = EmailChainParserService()
        self.typosquatting_service = TyposquattingService()
        self.normalization_service = NormalizationService()
        self.domain_validator = DomainValidationService()

    async def upload_email_chain(
        self,
        assessment_id: str,
        file_content: Optional[bytes] = None,
        text_content: Optional[str] = None,
        filename: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Upload and parse an email chain.

        Args:
            assessment_id: Assessment UUID to associate with
            file_content: Raw bytes of .eml, .msg, or .pdf file
            text_content: Raw text content (copy-paste)
            filename: Original filename if file upload
            user_id: ID of uploading user

        Returns:
            dict: Created email chain record
        """
        logger.info(f"Uploading email chain for assessment {assessment_id}")

        # Verify assessment exists
        assessment = await self.assessment_repo.get_by_id(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Parse the email content
        if file_content:
            if filename and filename.lower().endswith('.msg'):
                logger.info(f"Parsing .msg file: {filename}")
                parsed_data = self.parser_service.parse_msg_file(file_content)
            elif filename and filename.lower().endswith('.pdf'):
                logger.info(f"Parsing .pdf file: {filename}")
                parsed_data = self.parser_service.parse_pdf_file(file_content)
            else:
                logger.info(f"Parsing .eml file: {filename}")
                parsed_data = self.parser_service.parse_eml_file(file_content)
            raw_content = None  # Don't store raw bytes for files
        elif text_content:
            parsed_data = self.parser_service.parse_raw_text(text_content)
            raw_content = text_content
        else:
            raise ValueError("Either file_content or text_content must be provided")

        # Create the database record
        chain_data = {
            'assessment_id': assessment_id,
            'original_filename': filename,
            'raw_content': raw_content,
            'parsed_data': parsed_data,
            'validation_status': EmailChainValidationStatus.PENDING.value,
            'created_by': user_id,
        }

        return await self.chain_repo.create(chain_data)

    async def get_email_chains(self, assessment_id: str) -> List[dict]:
        """
        Get all email chains for an assessment.

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Email chain records
        """
        return await self.chain_repo.get_by_assessment(assessment_id)

    async def get_email_chain(self, chain_id: str) -> Optional[dict]:
        """
        Get a single email chain by ID.

        Args:
            chain_id: Email chain UUID

        Returns:
            Optional[dict]: Email chain record or None
        """
        return await self.chain_repo.get_by_id(chain_id)

    async def validate_email_chain(self, chain_id: str) -> dict:
        """
        Validate an email chain against document-extracted data.

        Cross-validates:
        - Sender domains against document company domains
        - Company names mentioned in email against document company names
        - NITs mentioned in email against document NITs
        - Representative names mentioned against document representatives

        Args:
            chain_id: Email chain UUID

        Returns:
            dict: Updated email chain record with validation result
        """
        logger.info(f"Validating email chain {chain_id}")

        # Get the email chain
        chain = await self.chain_repo.get_by_id(chain_id)
        if not chain:
            raise ValueError(f"Email chain {chain_id} not found")

        assessment_id = chain['assessment_id']
        parsed_data = chain.get('parsed_data', {})

        if not parsed_data:
            raise ValueError("Email chain has no parsed data")

        # Get document extractions for comparison
        doc_data = await self._get_document_data(assessment_id)

        # Get client data snapshot from assessment
        assessment = await self.assessment_repo.get_by_id(assessment_id)
        client_snapshot = assessment.get('client_data_snapshot') or {}

        # Perform cross-validation
        discrepancies = []

        # Extract data from parsed email
        messages = parsed_data.get('messages', [])
        mentions = parsed_data.get('mentions', {})

        # 1. Validate sender domains
        sender_domains = set()
        for msg in messages:
            domain = msg.get('sender_domain', '')
            if domain:
                sender_domains.add(domain.lower())

        for domain in sender_domains:
            disc = self._validate_sender_domain(domain, doc_data, client_snapshot)
            if disc:
                discrepancies.append(disc)

        # 1b. Validate sender domains against official document domains (RUT/Certificado)
        official_domains = doc_data.get('official_document_domains', [])
        for domain in sender_domains:
            disc = self._validate_against_official_document_domains(domain, official_domains)
            if disc:
                discrepancies.append(disc)

        # 2. Validate company name mentions
        company_mentions = mentions.get('company_names', [])
        for company in company_mentions:
            disc = self._validate_company_mention(company, doc_data, client_snapshot)
            if disc:
                discrepancies.append(disc)

        # 3. Validate NIT mentions
        nit_mentions = mentions.get('nits', [])
        for nit in nit_mentions:
            disc = self._validate_nit_mention(nit, doc_data, client_snapshot)
            if disc:
                discrepancies.append(disc)

        # 4. Validate representative name mentions
        rep_mentions = mentions.get('representative_names', [])
        for rep_name in rep_mentions:
            disc = self._validate_rep_name_mention(rep_name, doc_data, client_snapshot)
            if disc:
                discrepancies.append(disc)

        # 5. Validate domain age (DNS/WHOIS) for sender domains
        for domain in sender_domains:
            disc = self._validate_domain_age(domain, doc_data)
            if disc:
                discrepancies.append(disc)

        # Build validation result
        info_count = sum(1 for d in discrepancies if d['severity'] == DiscrepancySeverity.INFO.value)
        critical_count = sum(1 for d in discrepancies if d['severity'] == DiscrepancySeverity.CRITICAL.value)
        high_count = sum(1 for d in discrepancies if d['severity'] == DiscrepancySeverity.HIGH.value)
        medium_count = sum(1 for d in discrepancies if d['severity'] == DiscrepancySeverity.MEDIUM.value)
        low_count = sum(1 for d in discrepancies if d['severity'] == DiscrepancySeverity.LOW.value)

        # Count only actual discrepancies (exclude INFO which is informational/positive status)
        actual_discrepancy_count = critical_count + high_count + medium_count + low_count

        # Determine overall status (INFO discrepancies don't affect status negatively)
        if critical_count > 0:
            validation_status = EmailChainValidationStatus.CRITICAL
            summary = f"ALERTA CRÍTICA: {critical_count} discrepancia(s) crítica(s) detectada(s). Posible intento de fraude."
        elif high_count > 0:
            validation_status = EmailChainValidationStatus.SUSPICIOUS
            summary = f"ADVERTENCIA: {high_count} discrepancia(s) de alta severidad. Requiere verificación manual."
        elif medium_count > 0 or low_count > 0:
            validation_status = EmailChainValidationStatus.SUSPICIOUS
            summary = f"Se encontraron {medium_count + low_count} discrepancia(s) menores. Revisar antes de proceder."
        else:
            validation_status = EmailChainValidationStatus.VALIDATED
            summary = "Validación completada. No se encontraron discrepancias significativas."

        validation_result = {
            'total_discrepancies': actual_discrepancy_count,
            'info_count': info_count,
            'critical_count': critical_count,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count,
            'discrepancies': discrepancies,
            'summary': summary,
            'validated_at': datetime.now(timezone.utc).isoformat(),
        }

        # Update the record
        updates = {
            'validation_status': validation_status.value,
            'validation_result': validation_result,
            'validated_at': datetime.now(timezone.utc).isoformat(),
        }

        updated_chain = await self.chain_repo.update(chain_id, updates)

        if not updated_chain:
            raise ValueError(f"Failed to update email chain {chain_id}")

        logger.info(
            f"Email chain validation complete for {chain_id}: "
            f"status={validation_status.value}, discrepancies={len(discrepancies)}"
        )

        return updated_chain

    async def delete_email_chain(self, chain_id: str) -> bool:
        """
        Soft delete an email chain.

        Args:
            chain_id: Email chain UUID

        Returns:
            bool: True if successful
        """
        logger.info(f"Deleting email chain {chain_id}")
        return await self.chain_repo.delete(chain_id)

    async def _get_document_data(self, assessment_id: str) -> dict:
        """
        Get extracted data from all documents for an assessment.

        Args:
            assessment_id: Assessment UUID

        Returns:
            dict: Aggregated document data for comparison
        """
        # Official document types that provide authoritative email domain information
        official_doc_types = ['rut', 'certificado_existencia']

        doc_data = {
            'company_names': [],
            'nits': [],
            'representative_names': [],
            'email_domains': [],
            'official_document_domains': [],  # Track official doc domains separately
        }

        extractions = await self.extraction_repo.get_by_assessment(assessment_id)

        for extraction in extractions:
            extracted = extraction.get('extracted_data') or {}
            doc_type = extraction.get('document_type', '')
            is_official_doc = doc_type in official_doc_types

            # Company names
            for field in ['razon_social', 'nombre_empresa', 'nombre_importador', 'empresa']:
                value = extracted.get(field)
                if value and value not in doc_data['company_names']:
                    doc_data['company_names'].append(value)

            # NITs
            for field in ['nit', 'nit_empresa', 'numero_identificacion']:
                value = extracted.get(field)
                if value:
                    # Normalize NIT for comparison - normalize_nit returns (base_digits, check_digit) tuple
                    base, check = self.normalization_service.normalize_nit(str(value))
                    if base:
                        # Join base and check digit into a single string
                        normalized = f"{base}-{check}" if check else base
                        if normalized not in doc_data['nits']:
                            doc_data['nits'].append(normalized)

            # Representative names
            for field in ['representante_legal', 'nombre_representante', 'gerente']:
                value = extracted.get(field)
                if value and value not in doc_data['representative_names']:
                    doc_data['representative_names'].append(value)

            # Email domains
            for field in ['email', 'correo', 'email_empresa']:
                value = extracted.get(field)
                if value and '@' in value:
                    domain = value.split('@')[1].lower().strip()
                    if domain:
                        if domain not in doc_data['email_domains']:
                            doc_data['email_domains'].append(domain)
                        # Also track as official document domain if from RUT/Certificado
                        if is_official_doc and domain not in doc_data['official_document_domains']:
                            doc_data['official_document_domains'].append(domain)

        return doc_data

    def _validate_sender_domain(
        self,
        domain: str,
        doc_data: dict,
        client_snapshot: dict,
    ) -> Optional[dict]:
        """
        Validate sender domain against document data.

        Args:
            domain: Email domain to validate
            doc_data: Data extracted from documents
            client_snapshot: Client data snapshot

        Returns:
            Optional[dict]: Discrepancy if found, None otherwise
        """
        # Skip free email providers - handled separately
        if self.parser_service.is_free_email_provider(domain):
            return {
                'field': 'sender_domain',
                'email_value': domain,
                'document_value': None,
                'severity': DiscrepancySeverity.MEDIUM.value,
                'description': f"El email utiliza un proveedor gratuito ({domain}) en lugar de un dominio corporativo.",
                'is_typosquatting': False,
                'similarity_score': None,
            }

        # Get known domains from documents
        known_domains = doc_data.get('email_domains', [])

        # Also try to derive domain from company name
        company_name = client_snapshot.get('nombre_importador')
        if company_name:
            # Use typosquatting service to check
            typo_result = self.typosquatting_service.check_domain_typosquatting(
                domain=domain,
                known_domains=known_domains,
                company_name=company_name,
            )

            if typo_result.is_suspicious:
                if typo_result.detection_type == 'typosquatting':
                    return {
                        'field': 'sender_domain',
                        'email_value': domain,
                        'document_value': typo_result.similar_domain,
                        'severity': DiscrepancySeverity.CRITICAL.value,
                        'description': (
                            f"ALERTA: Posible typosquatting detectado. "
                            f"'{domain}' es similar a '{typo_result.similar_domain}' "
                            f"(similitud: {typo_result.similarity_score:.0%})"
                        ),
                        'is_typosquatting': True,
                        'similarity_score': typo_result.similarity_score,
                    }
                elif typo_result.detection_type == 'tld_variation':
                    return {
                        'field': 'sender_domain',
                        'email_value': domain,
                        'document_value': typo_result.similar_domain,
                        'severity': DiscrepancySeverity.HIGH.value,
                        'description': (
                            f"ADVERTENCIA: Variación de TLD detectada. "
                            f"'{domain}' vs '{typo_result.similar_domain}'"
                        ),
                        'is_typosquatting': True,
                        'similarity_score': typo_result.similarity_score,
                    }

        # If domain is in known domains, it's fine
        if domain.lower() in [d.lower() for d in known_domains]:
            return None

        # Domain not recognized but not necessarily suspicious
        return None

    def _validate_against_official_document_domains(
        self,
        sender_domain: str,
        official_domains: List[str],
    ) -> Optional[dict]:
        """
        Validate sender domain against official document email domains.

        Compares the email chain sender domain against email domains extracted
        from RUT and Certificado de Existencia documents. These official documents
        provide authoritative email domain information for the company.

        Args:
            sender_domain: Email domain from email chain sender
            official_domains: Email domains extracted from RUT/Certificado de Existencia

        Returns:
            Optional[dict]: Discrepancy if mismatch found, None if match or no official domains
        """
        if not official_domains:
            # No official document domains available - skip this check
            return None

        sender_domain = sender_domain.lower().strip()

        # Check for exact match with any official domain
        for official_domain in official_domains:
            if sender_domain == official_domain.lower().strip():
                return None

        # No exact match - use typosquatting service to detect variations
        # Check against each official domain for typosquatting/TLD variations
        for official_domain in official_domains:
            typo_result = self.typosquatting_service.check_domain_typosquatting(
                domain=sender_domain,
                known_domains=[official_domain],
            )

            if typo_result.detection_type == 'exact_match':
                # Should not happen since we already checked, but handle gracefully
                return None

            if typo_result.detection_type == 'tld_variation':
                return {
                    'field': 'official_document_domain',
                    'email_value': sender_domain,
                    'document_value': official_domain,
                    'severity': DiscrepancySeverity.CRITICAL.value,
                    'description': (
                        f"ALERTA CRÍTICA: El dominio del remitente '{sender_domain}' "
                        f"difiere del dominio oficial del documento (RUT/Certificado) "
                        f"'{official_domain}' - Variación de TLD detectada. "
                        f"Posible suplantación de identidad."
                    ),
                    'is_typosquatting': True,
                    'similarity_score': typo_result.similarity_score,
                }

            if typo_result.detection_type == 'typosquatting':
                return {
                    'field': 'official_document_domain',
                    'email_value': sender_domain,
                    'document_value': official_domain,
                    'severity': DiscrepancySeverity.CRITICAL.value,
                    'description': (
                        f"ALERTA CRÍTICA: Posible typosquatting detectado. "
                        f"El dominio del remitente '{sender_domain}' es similar al "
                        f"dominio oficial del documento '{official_domain}' "
                        f"(similitud: {typo_result.similarity_score:.0%}). "
                        f"Posible suplantación de identidad."
                    ),
                    'is_typosquatting': True,
                    'similarity_score': typo_result.similarity_score,
                }

        # No typosquatting or TLD variation detected - domain is completely different
        # Still flag as critical since it doesn't match official document domains
        official_domains_str = ', '.join(official_domains)
        return {
            'field': 'official_document_domain',
            'email_value': sender_domain,
            'document_value': official_domains[0],
            'severity': DiscrepancySeverity.CRITICAL.value,
            'description': (
                f"ALERTA CRÍTICA: El dominio del remitente '{sender_domain}' "
                f"no coincide con el dominio oficial del documento (RUT/Certificado). "
                f"Dominio(s) oficial(es): {official_domains_str}. "
                f"Verificar identidad del remitente manualmente."
            ),
            'is_typosquatting': False,
            'similarity_score': None,
        }

    def _validate_company_mention(
        self,
        company: str,
        doc_data: dict,
        client_snapshot: dict,
    ) -> Optional[dict]:
        """
        Validate company name mention against documents.

        Args:
            company: Company name mentioned in email
            doc_data: Data extracted from documents
            client_snapshot: Client data snapshot

        Returns:
            Optional[dict]: Discrepancy if found, None otherwise
        """
        known_companies = doc_data.get('company_names', [])
        client_company = client_snapshot.get('nombre_importador')
        if client_company:
            known_companies.append(client_company)

        if not known_companies:
            return None

        # Normalize for comparison
        normalized_mention = self.normalization_service.normalize_company_name(company)

        for known in known_companies:
            normalized_known = self.normalization_service.normalize_company_name(known)
            similarity = self.normalization_service.calculate_similarity(
                normalized_mention, normalized_known
            )

            # High similarity = match
            if similarity >= 0.9:
                return None

            # Medium similarity = possible typo or variation
            if 0.7 <= similarity < 0.9:
                return {
                    'field': 'company_name',
                    'email_value': company,
                    'document_value': known,
                    'severity': DiscrepancySeverity.MEDIUM.value,
                    'description': (
                        f"El nombre de empresa '{company}' difiere del documento "
                        f"'{known}' (similitud: {similarity:.0%})"
                    ),
                    'is_typosquatting': False,
                    'similarity_score': similarity,
                }

        # Low similarity - potential fraud
        best_match = max(known_companies, key=lambda k: self.normalization_service.calculate_similarity(
            normalized_mention, self.normalization_service.normalize_company_name(k)
        ))
        best_similarity = self.normalization_service.calculate_similarity(
            normalized_mention, self.normalization_service.normalize_company_name(best_match)
        )

        if best_similarity < 0.5:
            return {
                'field': 'company_name',
                'email_value': company,
                'document_value': best_match,
                'severity': DiscrepancySeverity.HIGH.value,
                'description': (
                    f"El nombre de empresa '{company}' no coincide con los documentos. "
                    f"La empresa en documentos es '{best_match}'"
                ),
                'is_typosquatting': False,
                'similarity_score': best_similarity,
            }

        return None

    def _validate_nit_mention(
        self,
        nit: str,
        doc_data: dict,
        client_snapshot: dict,
    ) -> Optional[dict]:
        """
        Validate NIT mention against documents.

        Args:
            nit: NIT mentioned in email
            doc_data: Data extracted from documents
            client_snapshot: Client data snapshot

        Returns:
            Optional[dict]: Discrepancy if found, None otherwise
        """
        known_nits = doc_data.get('nits', [])
        client_nit = client_snapshot.get('nit')
        if client_nit:
            # normalize_nit returns (base_digits, check_digit) tuple
            base, check = self.normalization_service.normalize_nit(str(client_nit))
            if base:
                normalized_client_nit = f"{base}-{check}" if check else base
                if normalized_client_nit not in known_nits:
                    known_nits.append(normalized_client_nit)

        if not known_nits:
            return None

        # Normalize the mentioned NIT - normalize_nit returns (base_digits, check_digit) tuple
        base_mention, check_mention = self.normalization_service.normalize_nit(nit)
        normalized_mention = f"{base_mention}-{check_mention}" if check_mention else base_mention

        # Check for exact match
        if normalized_mention in known_nits:
            return None

        # Check for check digit mismatch (base digits same, check digit different)
        for known_nit in known_nits:
            # Extract base from known_nit (format: "base-check" or just "base")
            known_parts = known_nit.split('-')
            base_known = known_parts[0] if known_parts else known_nit

            if base_mention == base_known:
                return {
                    'field': 'nit',
                    'email_value': nit,
                    'document_value': known_nit,
                    'severity': DiscrepancySeverity.HIGH.value,
                    'description': (
                        f"El dígito de verificación del NIT no coincide. "
                        f"Email: {nit}, Documento: {known_nit}"
                    ),
                    'is_typosquatting': False,
                    'similarity_score': None,
                }

        # Completely different NIT
        return {
            'field': 'nit',
            'email_value': nit,
            'document_value': known_nits[0] if known_nits else None,
            'severity': DiscrepancySeverity.CRITICAL.value,
            'description': (
                f"ALERTA: El NIT '{nit}' mencionado en el email no coincide "
                f"con el NIT de los documentos '{known_nits[0]}'"
            ),
            'is_typosquatting': False,
            'similarity_score': None,
        }

    def _validate_rep_name_mention(
        self,
        rep_name: str,
        doc_data: dict,
        client_snapshot: dict,
    ) -> Optional[dict]:
        """
        Validate representative name mention against documents.

        Args:
            rep_name: Representative name mentioned in email
            doc_data: Data extracted from documents
            client_snapshot: Client data snapshot

        Returns:
            Optional[dict]: Discrepancy if found, None otherwise
        """
        known_reps = doc_data.get('representative_names', [])
        client_rep = client_snapshot.get('representante_legal')
        if client_rep and client_rep not in known_reps:
            known_reps.append(client_rep)

        if not known_reps:
            return None

        # Normalize for comparison
        normalized_mention = self.normalization_service.normalize_name(rep_name)

        for known in known_reps:
            normalized_known = self.normalization_service.normalize_name(known)
            similarity = self.normalization_service.calculate_similarity(
                normalized_mention, normalized_known
            )

            # High similarity = match
            if similarity >= 0.85:
                return None

            # Medium similarity = possible typo
            if 0.6 <= similarity < 0.85:
                return {
                    'field': 'representative_name',
                    'email_value': rep_name,
                    'document_value': known,
                    'severity': DiscrepancySeverity.MEDIUM.value,
                    'description': (
                        f"El nombre del representante '{rep_name}' difiere del documento "
                        f"'{known}' (similitud: {similarity:.0%})"
                    ),
                    'is_typosquatting': False,
                    'similarity_score': similarity,
                }

        # Low similarity - different person
        best_match = max(known_reps, key=lambda k: self.normalization_service.calculate_similarity(
            normalized_mention, self.normalization_service.normalize_name(k)
        ))
        best_similarity = self.normalization_service.calculate_similarity(
            normalized_mention, self.normalization_service.normalize_name(best_match)
        )

        return {
            'field': 'representative_name',
            'email_value': rep_name,
            'document_value': best_match,
            'severity': DiscrepancySeverity.HIGH.value,
            'description': (
                f"El representante legal '{rep_name}' no coincide con los documentos. "
                f"El representante en documentos es '{best_match}'"
            ),
            'is_typosquatting': False,
            'similarity_score': best_similarity,
        }

    def _validate_domain_age(
        self,
        domain: str,
        doc_data: dict,
    ) -> Optional[dict]:
        """
        Validate domain age using DNS and WHOIS lookups.

        Detects potentially fraudulent domains by:
        - Checking if the domain exists (DNS resolution)
        - Looking up domain registration date via WHOIS
        - Flagging domains less than 90 days old

        Args:
            domain: Email domain to validate
            doc_data: Data extracted from documents

        Returns:
            Optional[dict]: Discrepancy if domain is suspicious, None otherwise
        """
        # Skip free email providers - they don't need age validation
        if self.parser_service.is_free_email_provider(domain):
            return None

        # Check domain existence
        existence_result = self.domain_validator.check_domain_existence(domain)
        if not existence_result.exists:
            return {
                'field': 'domain_existence',
                'email_value': domain,
                'document_value': None,
                'severity': DiscrepancySeverity.CRITICAL.value,
                'description': (
                    f"ALERTA CRÍTICA: El dominio '{domain}' no existe o no resuelve (DNS). "
                    f"Posible dominio fraudulento."
                ),
                'is_typosquatting': False,
                'similarity_score': None,
                'domain_age_days': None,
                'domain_exists': False,
            }

        # Get domain age via WHOIS
        age_result = self.domain_validator.get_domain_age(domain)

        if age_result.lookup_status == 'success' and age_result.age_days is not None:
            # Domain < 90 days is HIGH severity
            if age_result.age_days < 90:
                return {
                    'field': 'domain_age',
                    'email_value': domain,
                    'document_value': None,
                    'severity': DiscrepancySeverity.HIGH.value,
                    'description': (
                        f"ADVERTENCIA: El dominio '{domain}' tiene solo {age_result.age_days} días "
                        f"de antigüedad (menos de 90 días). Posible dominio fraudulento reciente."
                    ),
                    'is_typosquatting': False,
                    'similarity_score': None,
                    'domain_age_days': age_result.age_days,
                    'domain_exists': True,
                    'domain_creation_date': age_result.creation_date.isoformat() if age_result.creation_date else None,
                    'domain_registrar': age_result.registrar,
                }
            # Domain < 1 year is MEDIUM severity
            elif age_result.age_days < 365:
                return {
                    'field': 'domain_age',
                    'email_value': domain,
                    'document_value': None,
                    'severity': DiscrepancySeverity.MEDIUM.value,
                    'description': (
                        f"NOTA: El dominio '{domain}' tiene {age_result.age_days} días "
                        f"de antigüedad (menos de 1 año). Verifique que sea legítimo."
                    ),
                    'is_typosquatting': False,
                    'similarity_score': None,
                    'domain_age_days': age_result.age_days,
                    'domain_exists': True,
                    'domain_creation_date': age_result.creation_date.isoformat() if age_result.creation_date else None,
                    'domain_registrar': age_result.registrar,
                }

        # Domain exists and is old enough - return positive status (INFO severity)
        if age_result.lookup_status == 'success' and age_result.age_days is not None:
            description = (
                f"Dominio '{domain}' verificado correctamente. "
                f"Existe y tiene {age_result.age_days} días de antigüedad."
            )
        else:
            description = f"Dominio '{domain}' existe (DNS verificado). Antigüedad no disponible."

        return {
            'field': 'domain_age',
            'email_value': domain,
            'document_value': None,
            'severity': DiscrepancySeverity.INFO.value,
            'description': description,
            'is_typosquatting': False,
            'similarity_score': None,
            'domain_age_days': age_result.age_days if age_result.lookup_status == 'success' else None,
            'domain_exists': True,
            'domain_creation_date': age_result.creation_date.isoformat() if age_result.creation_date else None,
            'domain_registrar': age_result.registrar if age_result.lookup_status == 'success' else None,
        }
