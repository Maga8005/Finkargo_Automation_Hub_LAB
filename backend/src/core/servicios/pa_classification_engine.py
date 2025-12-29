"""
PA Classification Engine - Rule-based classification logic for PA records.

This engine applies classification rules to NetSuite records to determine:
- Categoría
- Subcategoría
- Clasificación
- Nexo
- Comprobación Saldos
- Cuenta/Nombre Homologación
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import date
import re

logger = logging.getLogger(__name__)


class PAClassificationEngine:
    """
    Engine to classify PA records based on uploaded rules.

    The engine applies rules in this priority order:
    1. Account Catalog - for homologation mapping
    2. Main Classification Rules - for categoria/subcategoria
    3. Clasificación Cuenta Rules - for account-based classification
    4. Nexo Rules - for nexo determination
    """

    # Accounts that should get "Cartera PA" in comprobacion_saldos
    CARTERA_PA_ACCOUNTS = {"13050530", "13050590", "13700530", "13809530", "13809531"}

    def __init__(
        self,
        account_catalog: Dict[str, Dict],
        classification_rules: List[Dict],
        clasificacion_cuenta_rules: List[Dict],
        nexo_rules: List[Dict]
    ):
        """
        Initialize engine with rules.

        Args:
            account_catalog: Dict of cuenta_finkargo -> catalog entry
            classification_rules: List of classification rules (sorted by priority)
            clasificacion_cuenta_rules: List of cuenta classification rules
            nexo_rules: List of nexo rules
        """
        self.account_catalog = account_catalog
        self.classification_rules = classification_rules
        self.clasificacion_cuenta_rules = clasificacion_cuenta_rules
        self.nexo_rules = nexo_rules

    def classify_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all classification rules to a single record.

        Args:
            record: Dict with source columns (cuenta_linea_numero, cuenta_linea_nombre,
                    tipo_transaccion, tipo_comprobante, numero_documento, fecha)

        Returns:
            Dict with output columns (pa, categoria, subcategoria, clasificacion,
                    nexo, comprobacion_saldos, cuenta_homologacion, nombre_homologacion)
        """
        cuenta_numero = str(record.get("cuenta_linea_numero", "")).strip()
        cuenta_nombre = str(record.get("cuenta_linea_nombre", "")).strip()
        tipo_transaccion = str(record.get("tipo_transaccion", "")).strip()
        tipo_comprobante = str(record.get("tipo_comprobante", "")).strip()
        numero_documento = str(record.get("numero_documento", "")).strip()
        fecha = record.get("fecha")

        # 1. Get homologation from account catalog
        catalog_entry = self.account_catalog.get(cuenta_numero, {})
        cuenta_homologacion = catalog_entry.get("cuenta_homologacion")
        nombre_homologacion = catalog_entry.get("nombre_homologacion")

        # 2. Find matching main classification rule
        main_rule = self._find_classification_rule(tipo_transaccion, tipo_comprobante, numero_documento)

        categoria = main_rule.get("categoria") if main_rule else None
        subcategoria_base = main_rule.get("subcategoria_base") if main_rule else None
        clasificacion_default = main_rule.get("clasificacion_default") if main_rule else None

        # 3. Determine subcategoria (with date logic if needed)
        subcategoria = self._apply_date_logic(fecha, subcategoria_base, categoria)

        # 4. Determine clasificacion (hierarchical check)
        clasificacion = self._determine_clasificacion(cuenta_nombre, categoria, clasificacion_default)

        # 5. Determine nexo from nexo rules
        nexo = self._find_nexo(cuenta_nombre)

        # 6. Determine comprobacion_saldos
        comprobacion_saldos = self._determine_comprobacion_saldos(cuenta_numero, categoria)

        # 7. Apply special homologation override (Acreedores Fiduciarios)
        if cuenta_homologacion == "3505" and categoria in ["Cesiones", "Sustituciones", "DisaumAporte"]:
            cuenta_homologacion = "35051500101001"

        return {
            "pa": "X",
            "categoria": categoria,
            "subcategoria": subcategoria,
            "clasificacion": clasificacion,
            "nexo": nexo,
            "comprobacion_saldos": comprobacion_saldos,
            "cuenta_homologacion": cuenta_homologacion,
            "nombre_homologacion": nombre_homologacion
        }

    def _find_classification_rule(
        self,
        tipo_transaccion: str,
        tipo_comprobante: str,
        numero_documento: str
    ) -> Optional[Dict]:
        """
        Find matching classification rule.

        Rules are matched by:
        - tipo_transaccion (exact match)
        - tipo_comprobante (exact match)
        - numero_documento_patron (pattern match, if specified)

        Returns first matching rule (sorted by priority).
        """
        for rule in self.classification_rules:
            # Check tipo_transaccion
            if rule.get("tipo_transaccion") and rule["tipo_transaccion"] != tipo_transaccion:
                continue

            # Check tipo_comprobante
            if rule.get("tipo_comprobante") and rule["tipo_comprobante"] != tipo_comprobante:
                continue

            # Check numero_documento pattern (if specified)
            patron = rule.get("numero_documento_patron")
            if patron:
                # Convert SQL LIKE pattern to regex
                regex_pattern = self._like_to_regex(patron)
                if not re.match(regex_pattern, numero_documento, re.IGNORECASE):
                    continue

            return rule

        return None

    def _like_to_regex(self, pattern: str) -> str:
        """Convert SQL LIKE pattern to regex pattern."""
        # Escape special regex characters except % and _
        escaped = re.escape(pattern)
        # Convert SQL wildcards to regex
        escaped = escaped.replace(r"\%", ".*")
        escaped = escaped.replace(r"\_", ".")
        return f"^{escaped}$"

    def _apply_date_logic(
        self,
        fecha: Optional[date],
        subcategoria_base: Optional[str],
        categoria: Optional[str]
    ) -> Optional[str]:
        """
        Apply date-based subcategoria logic.

        For certain categories, the subcategoria changes based on whether
        the transaction date is the 1st day of the month.
        """
        if not subcategoria_base:
            return None

        if not fecha:
            return subcategoria_base

        # Check if this category uses date logic
        date_logic_categories = ["Diferencia en cambio", "Recaudo"]

        if categoria not in date_logic_categories:
            return subcategoria_base

        is_first_day = fecha.day == 1

        # Apply date logic based on category
        if categoria == "Recaudo":
            if is_first_day:
                if "Recaudos en tránsito" in (subcategoria_base or ""):
                    return "Legalizacion Recaudos en Transito mes Ant."
                return "Reversión mes Ant."
            else:
                if "Recaudos en tránsito" in (subcategoria_base or ""):
                    return "Recaudos en tránsito del mes"
                return "Del mes"
        elif categoria == "Diferencia en cambio":
            if is_first_day:
                return "Reversión mes Ant."
            return "Del mes"

        return subcategoria_base

    def _determine_clasificacion(
        self,
        cuenta_nombre: str,
        categoria: Optional[str],
        clasificacion_default: Optional[str]
    ) -> Optional[str]:
        """
        Hierarchical clasificacion determination.

        Priority:
        1. Check account name contains "No Realizada" or "Realizada"
        2. Check specific account rules (clasificacion_cuenta_rules)
        3. Fall back to default from main rule
        """
        # 1. Check account name keywords first
        if "No Realizada" in cuenta_nombre:
            return "No Realizada"
        if "Realizada" in cuenta_nombre:
            return "Realizada"

        # 2. Check specific account rules
        for rule in self.clasificacion_cuenta_rules:
            patron = rule.get("cuenta_nombre_patron", "")
            categoria_aplicable = rule.get("categoria_aplicable")

            # Check if rule applies to this category (if restricted)
            if categoria_aplicable and categoria_aplicable != categoria:
                continue

            # Check pattern match
            if self._pattern_matches(cuenta_nombre, patron):
                return rule.get("clasificacion")

        # 3. Fall back to default
        return clasificacion_default

    def _find_nexo(self, cuenta_nombre: str) -> Optional[str]:
        """
        Find nexo value from nexo rules.

        Args:
            cuenta_nombre: Account name to match.

        Returns:
            Nexo value or None.
        """
        for rule in self.nexo_rules:
            patron = rule.get("cuenta_nombre_patron", "")
            if self._pattern_matches(cuenta_nombre, patron):
                return rule.get("nexo")
        return None

    def _pattern_matches(self, value: str, pattern: str) -> bool:
        """
        Check if value matches pattern.

        Supports:
        - Exact match
        - Contains match (if pattern has no wildcards)
        - SQL LIKE pattern (with %)
        """
        if not pattern:
            return False

        # Check for SQL LIKE wildcards
        if "%" in pattern:
            regex_pattern = self._like_to_regex(pattern)
            return bool(re.match(regex_pattern, value, re.IGNORECASE))

        # Check for contains match (pattern is part of account name)
        return pattern.lower() in value.lower()

    def _determine_comprobacion_saldos(
        self,
        cuenta_numero: str,
        categoria: Optional[str]
    ) -> Optional[str]:
        """
        Determine comprobacion_saldos value.

        Returns "Cartera PA" for specific accounts.
        """
        if cuenta_numero in self.CARTERA_PA_ACCOUNTS:
            return "Cartera PA"
        return None


def create_classification_engine(
    catalog_entries: List[Dict],
    classification_rules: List[Dict],
    clasificacion_cuenta_rules: List[Dict],
    nexo_rules: List[Dict]
) -> PAClassificationEngine:
    """
    Factory function to create classification engine.

    Args:
        catalog_entries: List of catalog entry dicts.
        classification_rules: List of classification rules.
        clasificacion_cuenta_rules: List of cuenta classification rules.
        nexo_rules: List of nexo rules.

    Returns:
        Configured PAClassificationEngine instance.
    """
    # Convert catalog list to dict keyed by cuenta_finkargo
    catalog_dict = {
        entry["cuenta_finkargo"]: entry
        for entry in catalog_entries
    }

    return PAClassificationEngine(
        account_catalog=catalog_dict,
        classification_rules=classification_rules,
        clasificacion_cuenta_rules=clasificacion_cuenta_rules,
        nexo_rules=nexo_rules
    )
