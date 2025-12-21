"""
Fraud Detection Service
Core fraud detection logic for evaluating client risk
"""
import re
import logging
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from src.interface.risk_dtos import (
    FraudIndicator,
    RiskLevel,
    AssessmentStatus,
    AlertType,
    AlertSeverity,
)
from src.repositorio.risk_repository import (
    RiskAssessmentRepository,
    FraudRulesRepository,
    BlacklistRepository,
)
from src.repositorio.client_repository import ClientRepository
from .risk_scoring_service import RiskScoringService
from .alert_service import AlertService

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """
    Service for detecting fraud indicators and evaluating client risk.

    Implements validation rules for:
    - Identity consistency (company name matching across documents)
    - Email domain validation (typosquatting detection)
    - NIT format validation (Colombian format)
    - Document metadata analysis
    - Company history verification
    - Address consistency checks
    """

    # Known legitimate company domains for typosquatting detection
    KNOWN_DOMAINS = [
        'azelis.com',
        'basf.com',
        'dow.com',
        'dupont.com',
        'evonik.com',
        'lanxess.com',
        'brenntag.com',
        'univar.com',
    ]

    # Suspicious TLDs that may indicate fraud
    SUSPICIOUS_TLDS = ['.xyz', '.top', '.tk', '.ml', '.ga', '.cf', '.gq', '.work', '.click']

    def __init__(
        self,
        risk_repo: RiskAssessmentRepository,
        rules_repo: FraudRulesRepository,
        blacklist_repo: BlacklistRepository,
        client_repo: ClientRepository,
        scoring_service: RiskScoringService,
        alert_service: AlertService,
    ):
        """
        Initialize fraud detection service with dependencies

        Args:
            risk_repo: Risk assessment repository
            rules_repo: Fraud detection rules repository
            blacklist_repo: Blacklist repository
            client_repo: Client data repository
            scoring_service: Risk scoring service
            alert_service: Alert notification service
        """
        self.risk_repo = risk_repo
        self.rules_repo = rules_repo
        self.blacklist_repo = blacklist_repo
        self.client_repo = client_repo
        self.scoring_service = scoring_service
        self.alert_service = alert_service

    async def evaluate_client(
        self,
        client_nit: str,
        user_id: str,
        assessment_type: str = 'comprehensive'
    ) -> dict:
        """
        Evaluate client fraud risk

        Args:
            client_nit: Client NIT to evaluate
            user_id: ID of user performing evaluation
            assessment_type: Type of assessment (comprehensive or quick)

        Returns:
            dict: Assessment result with risk score and indicators
        """
        logger.info(f"Starting fraud evaluation for client NIT: {client_nit}")

        # 1. Fetch client data
        client_data = await self._get_client_data(client_nit)
        if not client_data:
            logger.warning(f"Client not found for NIT: {client_nit}")
            # Create assessment with error state
            return await self._create_error_assessment(
                client_nit,
                user_id,
                assessment_type,
                "Cliente no encontrado en el sistema"
            )

        # 2. Check blacklist first (immediate critical if found)
        blacklist_match = await self._check_blacklist(client_data)
        if blacklist_match:
            logger.warning(f"Blacklist match found for NIT: {client_nit}")
            return await self._create_blacklist_assessment(
                client_nit,
                user_id,
                client_data,
                blacklist_match
            )

        # 3. Get active detection rules
        rules = await self.rules_repo.list_active()

        # 4. Run all validation checks
        indicators = await self._run_all_checks(client_data, rules)

        # 5. Calculate risk score and level
        risk_score, risk_level = await self.scoring_service.calculate_score(indicators, rules)

        # 6. Create assessment record
        assessment_data = {
            'client_nit': client_nit,
            'risk_level': risk_level.value,
            'risk_score': float(risk_score),
            'fraud_indicators': [self._indicator_to_dict(ind) for ind in indicators],
            'status': self._determine_initial_status(risk_level),
            'assessment_type': assessment_type,
            'assessed_by': user_id,
            'assessed_at': datetime.utcnow().isoformat(),
            'client_data_snapshot': client_data,
        }

        assessment = await self.risk_repo.create(assessment_data)

        # 7. Create alerts for high/critical risk
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            await self._create_risk_alerts(assessment, risk_level, indicators)

        logger.info(f"Completed evaluation for NIT: {client_nit}, Score: {risk_score}, Level: {risk_level.value}")

        return assessment

    async def _get_client_data(self, client_nit: str) -> Optional[dict]:
        """Fetch client data from repository"""
        try:
            client = await self.client_repo.get_by_nit(client_nit)
            return client
        except Exception as e:
            logger.error(f"Error fetching client data: {e}")
            return None

    async def _check_blacklist(self, client_data: dict) -> Optional[dict]:
        """Check if any client attributes are blacklisted"""
        checks = []

        # Check NIT
        if client_data.get('nit'):
            checks.append({'entity_type': 'nit', 'entity_value': client_data['nit']})

        # Check company name
        if client_data.get('nombre_importador'):
            checks.append({'entity_type': 'company_name', 'entity_value': client_data['nombre_importador']})

        # Check email domain
        if client_data.get('kam_email'):
            domain = self._extract_domain(client_data['kam_email'])
            if domain:
                checks.append({'entity_type': 'email_domain', 'entity_value': domain})

        # Check person ID
        if client_data.get('cedula_representante'):
            checks.append({'entity_type': 'person_id', 'entity_value': client_data['cedula_representante']})

        return await self.blacklist_repo.check_any_blacklisted(checks)

    async def _run_all_checks(self, client_data: dict, rules: List[dict]) -> List[FraudIndicator]:
        """Run all fraud detection checks"""
        indicators = []

        # Map rule types to check functions
        check_functions = {
            'identity': self._check_identity_consistency,
            'email': self._check_email_domain,
            'nit': self._check_nit_format,
            'document': self._check_document_metadata,
            'history': self._check_company_history,
            'address': self._check_address_verification,
        }

        for rule in rules:
            rule_type = rule.get('rule_type')
            if rule_type in check_functions:
                try:
                    indicator = await check_functions[rule_type](client_data, rule)
                    if indicator:
                        indicators.append(indicator)
                except Exception as e:
                    logger.error(f"Error running check {rule_type}: {e}")
                    # Add error indicator
                    indicators.append(FraudIndicator(
                        indicator_name=f"{rule_type}_error",
                        indicator_value=False,
                        severity=RiskLevel.LOW,
                        evidence=f"Error durante verificación: {str(e)}",
                        score_impact=Decimal('0'),
                    ))

        return indicators

    async def _check_identity_consistency(self, client_data: dict, rule: dict) -> FraudIndicator:
        """
        Check identity consistency across documents.
        Detects cases like ROCSA vs AZELIS where company names don't match.
        """
        company_name = client_data.get('nombre_importador', '').upper().strip()
        issues = []

        # In a full implementation, we would compare across multiple documents
        # For now, we check for suspicious patterns in the company name

        # Check for name that might be similar to known companies
        for known_domain in self.KNOWN_DOMAINS:
            known_company = known_domain.split('.')[0].upper()
            if self._is_similar_name(company_name, known_company) and known_company not in company_name:
                issues.append(f"Nombre similar a empresa conocida: {known_company}")

        # Check for inconsistencies in representative name
        rep_name = client_data.get('representante_legal', '').upper().strip()
        if rep_name and len(rep_name) < 5:
            issues.append("Nombre del representante legal demasiado corto")

        triggered = len(issues) > 0
        severity = RiskLevel.HIGH if triggered else RiskLevel.LOW
        weight = Decimal(str(rule.get('weight', 0.35)))

        return FraudIndicator(
            indicator_name="identity_consistency",
            indicator_value=triggered,
            severity=severity,
            evidence="; ".join(issues) if issues else "Identidad consistente",
            score_impact=weight * Decimal('100') if triggered else Decimal('0'),
        )

    async def _check_email_domain(self, client_data: dict, rule: dict) -> FraudIndicator:
        """
        Check email domain for typosquatting or suspicious patterns.
        Detects cases like acelis.com.co vs azelis.com
        """
        email = client_data.get('kam_email') or client_data.get('destinatario_email') or ''
        issues = []

        if not email:
            return FraudIndicator(
                indicator_name="email_domain_validation",
                indicator_value=False,
                severity=RiskLevel.LOW,
                evidence="No hay email para validar",
                score_impact=Decimal('0'),
            )

        domain = self._extract_domain(email)

        if domain:
            # Check for suspicious TLDs
            for tld in self.SUSPICIOUS_TLDS:
                if domain.endswith(tld):
                    issues.append(f"Dominio con TLD sospechoso: {tld}")

            # Check for typosquatting of known domains
            for known_domain in self.KNOWN_DOMAINS:
                known_base = known_domain.split('.')[0]
                domain_base = domain.split('.')[0]

                # Skip if exact match
                if known_base == domain_base:
                    continue

                # Check for similar names (potential typosquatting)
                if self._levenshtein_distance(known_base, domain_base) <= 2:
                    issues.append(f"Posible typosquatting de {known_domain}: {domain}")

            # Check for recently registered free email providers
            free_providers = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com']
            if domain in free_providers:
                issues.append("Uso de proveedor de email gratuito para cuenta empresarial")

        triggered = len(issues) > 0
        severity = RiskLevel.HIGH if triggered and 'typosquatting' in str(issues) else RiskLevel.MEDIUM if triggered else RiskLevel.LOW
        weight = Decimal(str(rule.get('weight', 0.25)))

        return FraudIndicator(
            indicator_name="email_domain_validation",
            indicator_value=triggered,
            severity=severity,
            evidence="; ".join(issues) if issues else f"Dominio válido: {domain}",
            score_impact=weight * Decimal('100') if triggered else Decimal('0'),
        )

    async def _check_nit_format(self, client_data: dict, rule: dict) -> FraudIndicator:
        """
        Validate Colombian NIT format and check digit.
        Format: XXX.XXX.XXX-X or XXXXXXXXX-X
        """
        nit = client_data.get('nit', '')
        issues = []

        if not nit:
            return FraudIndicator(
                indicator_name="nit_format_validation",
                indicator_value=True,
                severity=RiskLevel.HIGH,
                evidence="NIT no proporcionado",
                score_impact=Decimal(str(rule.get('weight', 0.10))) * Decimal('100'),
            )

        # Clean NIT - remove dots, spaces, dashes except last one
        clean_nit = re.sub(r'[.\s]', '', nit)

        # Check format: should be digits with optional check digit
        nit_pattern = r'^(\d{9,10})(-(\d))?$'
        match = re.match(nit_pattern, clean_nit)

        if not match:
            issues.append(f"Formato de NIT inválido: {nit}")
        else:
            # Extract base number and check digit
            base_number = match.group(1)
            provided_check_digit = match.group(3)

            if provided_check_digit:
                # Validate check digit
                calculated_digit = self._calculate_nit_check_digit(base_number)
                if calculated_digit != int(provided_check_digit):
                    issues.append(f"Dígito de verificación incorrecto: esperado {calculated_digit}, recibido {provided_check_digit}")

        triggered = len(issues) > 0
        severity = RiskLevel.HIGH if triggered else RiskLevel.LOW
        weight = Decimal(str(rule.get('weight', 0.10)))

        return FraudIndicator(
            indicator_name="nit_format_validation",
            indicator_value=triggered,
            severity=severity,
            evidence="; ".join(issues) if issues else "NIT válido",
            score_impact=weight * Decimal('100') if triggered else Decimal('0'),
        )

    async def _check_document_metadata(self, client_data: dict, rule: dict) -> FraudIndicator:
        """
        Check document metadata for manipulation signs.
        In a full implementation, this would analyze uploaded PDF metadata.
        """
        # Placeholder - in production, this would analyze actual document metadata
        issues = []

        # Check for missing required documents
        required_fields = ['representante_legal', 'cedula_representante', 'ciudad_domicilio']
        missing = [f for f in required_fields if not client_data.get(f)]

        if missing:
            issues.append(f"Campos requeridos faltantes: {', '.join(missing)}")

        triggered = len(issues) > 0
        severity = RiskLevel.MEDIUM if triggered else RiskLevel.LOW
        weight = Decimal(str(rule.get('weight', 0.10)))

        return FraudIndicator(
            indicator_name="document_metadata",
            indicator_value=triggered,
            severity=severity,
            evidence="; ".join(issues) if issues else "Documentación completa",
            score_impact=weight * Decimal('100') if triggered else Decimal('0'),
        )

    async def _check_company_history(self, client_data: dict, rule: dict) -> FraudIndicator:
        """
        Check company history and time in business.
        Newer companies may pose higher risk.
        """
        issues = []

        # Check if there are previous assessments for this client
        previous = await self.risk_repo.get_recent_by_client(client_data.get('nit', ''), limit=10)

        if not previous:
            issues.append("Primera evaluación para este cliente - sin historial previo")

        # Check credit limit - very high limits for new clients may be suspicious
        cupo = client_data.get('cupo_plataforma')
        if cupo and float(cupo) > 500000000 and not previous:  # > 500M COP for new client
            issues.append("Cupo muy alto para cliente sin historial")

        triggered = len(issues) > 0
        severity = RiskLevel.MEDIUM if 'Cupo muy alto' in str(issues) else RiskLevel.LOW
        weight = Decimal(str(rule.get('weight', 0.10)))

        return FraudIndicator(
            indicator_name="company_history",
            indicator_value=triggered,
            severity=severity,
            evidence="; ".join(issues) if issues else f"Historial: {len(previous)} evaluaciones previas",
            score_impact=weight * Decimal('50') if triggered else Decimal('0'),  # Reduced impact for history
        )

    async def _check_address_verification(self, client_data: dict, rule: dict) -> FraudIndicator:
        """
        Verify address consistency.
        Check if city and address are consistent.
        """
        issues = []

        city = client_data.get('ciudad_domicilio', '').strip()
        address = client_data.get('direccion_comercial', '').strip()

        if not city:
            issues.append("Ciudad de domicilio no especificada")

        if address:
            # Check if address contains city reference and they match
            address_lower = address.lower()
            city_lower = city.lower() if city else ''

            # Colombian cities to check
            major_cities = ['bogota', 'medellin', 'cali', 'barranquilla', 'cartagena']

            for major_city in major_cities:
                if major_city in address_lower and city_lower and major_city not in city_lower:
                    issues.append(f"Inconsistencia: dirección menciona {major_city} pero ciudad es {city}")

        triggered = len(issues) > 0
        severity = RiskLevel.MEDIUM if triggered else RiskLevel.LOW
        weight = Decimal(str(rule.get('weight', 0.10)))

        return FraudIndicator(
            indicator_name="address_verification",
            indicator_value=triggered,
            severity=severity,
            evidence="; ".join(issues) if issues else "Dirección verificada",
            score_impact=weight * Decimal('100') if triggered else Decimal('0'),
        )

    def _determine_initial_status(self, risk_level: RiskLevel) -> str:
        """Determine initial assessment status based on risk level"""
        if risk_level == RiskLevel.LOW:
            return AssessmentStatus.COMPLETED.value  # Auto-complete low risk
        elif risk_level == RiskLevel.CRITICAL:
            return AssessmentStatus.ESCALATED.value  # Auto-escalate critical
        else:
            return AssessmentStatus.PENDING.value  # Manual review for medium/high

    async def _create_risk_alerts(
        self,
        assessment: dict,
        risk_level: RiskLevel,
        indicators: List[FraudIndicator]
    ):
        """Create alerts for high/critical risk assessments"""
        if risk_level == RiskLevel.CRITICAL:
            await self.alert_service.create_alert(
                assessment_id=assessment['id'],
                alert_type=AlertType.NEW_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                title=f"CRÍTICO: Evaluación de alto riesgo - {assessment['client_nit']}",
                message=f"Se detectó un cliente con nivel de riesgo crítico (score: {assessment['risk_score']}). "
                        f"Requiere revisión inmediata."
            )
        elif risk_level == RiskLevel.HIGH:
            await self.alert_service.create_alert(
                assessment_id=assessment['id'],
                alert_type=AlertType.REVIEW_REQUIRED,
                severity=AlertSeverity.WARNING,
                title=f"Alto riesgo detectado - {assessment['client_nit']}",
                message=f"Evaluación con riesgo alto (score: {assessment['risk_score']}). "
                        f"Requiere revisión manual."
            )

    async def _create_error_assessment(
        self,
        client_nit: str,
        user_id: str,
        assessment_type: str,
        error_message: str
    ) -> dict:
        """Create an assessment record for error cases"""
        assessment_data = {
            'client_nit': client_nit,
            'risk_level': RiskLevel.HIGH.value,
            'risk_score': 75.0,  # High score due to inability to verify
            'fraud_indicators': [{
                'indicator_name': 'system_error',
                'indicator_value': True,
                'severity': RiskLevel.HIGH.value,
                'evidence': error_message,
                'score_impact': 75.0,
            }],
            'status': AssessmentStatus.PENDING.value,
            'assessment_type': assessment_type,
            'assessed_by': user_id,
            'assessed_at': datetime.utcnow().isoformat(),
        }

        return await self.risk_repo.create(assessment_data)

    async def _create_blacklist_assessment(
        self,
        client_nit: str,
        user_id: str,
        client_data: dict,
        blacklist_match: dict
    ) -> dict:
        """Create an assessment for blacklisted entities"""
        assessment_data = {
            'client_nit': client_nit,
            'risk_level': RiskLevel.CRITICAL.value,
            'risk_score': 100.0,  # Maximum score for blacklisted
            'fraud_indicators': [{
                'indicator_name': 'blacklist_match',
                'indicator_value': True,
                'severity': RiskLevel.CRITICAL.value,
                'evidence': f"Entidad en lista negra: {blacklist_match['entity_type']} = {blacklist_match['entity_value']}. "
                           f"Razón: {blacklist_match['reason']}",
                'score_impact': 100.0,
            }],
            'status': AssessmentStatus.REJECTED.value,  # Auto-reject blacklisted
            'assessment_type': 'comprehensive',
            'assessed_by': user_id,
            'assessed_at': datetime.utcnow().isoformat(),
            'client_data_snapshot': client_data,
        }

        assessment = await self.risk_repo.create(assessment_data)

        # Create critical alert
        await self.alert_service.create_alert(
            assessment_id=assessment['id'],
            alert_type=AlertType.BLACKLIST_MATCH,
            severity=AlertSeverity.CRITICAL,
            title=f"BLACKLIST: Entidad bloqueada detectada - {client_nit}",
            message=f"El cliente {client_nit} coincide con una entrada en la lista negra: "
                    f"{blacklist_match['entity_type']} = {blacklist_match['entity_value']}"
        )

        return assessment

    # ==================== Helper Methods ====================

    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if not email or '@' not in email:
            return None
        return email.split('@')[1].lower()

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _is_similar_name(self, name1: str, name2: str, threshold: int = 3) -> bool:
        """Check if two names are similar using Levenshtein distance"""
        # Normalize names
        n1 = re.sub(r'[^a-zA-Z0-9]', '', name1.lower())
        n2 = re.sub(r'[^a-zA-Z0-9]', '', name2.lower())

        if not n1 or not n2:
            return False

        distance = self._levenshtein_distance(n1, n2)
        return distance <= threshold

    def _calculate_nit_check_digit(self, base_number: str) -> int:
        """
        Calculate Colombian NIT check digit.
        Algorithm: Weighted sum with prime multipliers, mod 11
        """
        # Ensure base number is 9 digits
        base = base_number.zfill(9)[:9]

        # Weights for each position (right to left)
        weights = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]

        # Calculate weighted sum
        total = 0
        for i, digit in enumerate(reversed(base)):
            if i < len(weights):
                total += int(digit) * weights[i]

        # Calculate check digit
        remainder = total % 11

        if remainder == 0:
            return 0
        elif remainder == 1:
            return 1
        else:
            return 11 - remainder

    def _indicator_to_dict(self, indicator: FraudIndicator) -> dict:
        """Convert FraudIndicator to dict for storage"""
        return {
            'indicator_name': indicator.indicator_name,
            'indicator_value': indicator.indicator_value,
            'severity': indicator.severity.value if isinstance(indicator.severity, RiskLevel) else indicator.severity,
            'evidence': indicator.evidence,
            'score_impact': float(indicator.score_impact),
        }
