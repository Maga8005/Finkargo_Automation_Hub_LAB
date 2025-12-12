"""
Payment Catalogs for Treasury Module.

Contains AR account mappings and column definitions for Colombia and México
payment template conversion.

Based on the template definition in:
'Example Files for Reqs/FIN_ Definicion Template para Aplicación de pagos.xlsx'
"""

from typing import Dict, Optional

# =============================================================================
# COLOMBIA AR ACCOUNT MAPPINGS
# =============================================================================

# Standard AR accounts for Colombia (non-NT operations)
COLOMBIA_AR_ACCOUNTS: Dict[str, int] = {
    "CAPITAL": 302,
    "COSTOS_FIJOS": 258,  # 4x1000, Fondo garantías, IVA Fondo, Servicio Originación, Servicio Giro
    "4X1000": 258,
    "FONDO_GARANTIAS": 258,
    "IVA_FONDO_GARANTIAS": 258,
    "SERVICIO_ORIGINACION": 258,
    "SERVICIO_GIRO": 258,
    "COSTOS_ADICIONALES": 258,
    "SEGUROS": 1387,
    "INTERESES": 258,
    "MORATORIOS": 258,
}

# AR accounts for Colombia Operaciones Cedidas (NT column populated)
COLOMBIA_NT_AR_ACCOUNTS: Dict[str, int] = {
    "CAPITAL": 304,
    "COSTOS_FIJOS": 310,
    "4X1000": 310,
    "FONDO_GARANTIAS": 310,
    "IVA_FONDO_GARANTIAS": 310,
    "SERVICIO_ORIGINACION": 310,
    "SERVICIO_GIRO": 310,
    "COSTOS_ADICIONALES": 310,
    "SEGUROS": 1474,
    "INTERESES": 259,
    "MORATORIOS": 259,
}


# =============================================================================
# COLOMBIA BANK ACCOUNT MAPPINGS (Cuenta Remitente -> NetSuite Internal ID)
# =============================================================================

# Maps bank account numbers (Cuenta Remitente) to NetSuite internal account IDs
# Used to populate the 'account' field in the output template
COLOMBIA_BANK_ACCOUNT_MAPPING: Dict[str, int] = {
    "60100001091": 230,
    "60100005374": 2346,
    "42861435": 231,
    "60100004638": 1439,
    "2600000313": 2439,
    "1250001972": 232,
    "36449096": 235,
    "3644-6725": 236,
    "709396827": 2441,
    "3304261649": 1493,
    "5089889016": 239,
    "3304296965": 1492,
    "9562345678749720": 2418,
    "8482979559": 2498,
}


# =============================================================================
# MÉXICO AR ACCOUNT MAPPINGS
# =============================================================================

# Uses space-separated concept type names to match output format
MEXICO_AR_ACCOUNTS: Dict[str, int] = {
    "CAPITAL": 2114,
    "SEGUROS": 2114,
    "COMISION DESEMBOLSO": 2114,
    "COMISION DISPOSICION": 2114,
    "COMISION SWIFT": 2114,
    "COMISION ADMINISTRACION": 2114,
    "COMISION APERTURA": 2114,
    "COSTOS ADICIONALES": 2114,
    "INTERESES": 2115,
    "MORATORIOS": 2117,
}


# =============================================================================
# MÉXICO BANK ACCOUNT MAPPINGS (Cuenta Remitente -> NetSuite Internal ID)
# =============================================================================

# Maps bank account numbers (Cuenta Remitente) to NetSuite internal account IDs
# Used to populate the 'account' field in the output template for México
# Note: Include both with and without leading zeros since Excel may store as integer (no leading zeros)
MEXICO_BANK_ACCOUNT_MAPPING: Dict[str, int] = {
    # With leading zeros (as provided)
    "0123270165": 2322,
    "0123375153": 2320,
    "0118970882": 2111,
    # Without leading zeros (as Excel stores integers)
    "123270165": 2322,
    "123375153": 2320,
    "118970882": 2111,
    # No leading zero variant
    "669555222": 2110,
}


# =============================================================================
# COLUMN DEFINITIONS
# =============================================================================

# Required columns for Colombia Historial de Pagos
# Maps internal name -> expected column letter/name in source file
COLOMBIA_REQUIRED_COLUMNS: Dict[str, str] = {
    "cliente": "Cliente",
    "customer_external_id": "Identificación del cliente",
    "invoice_core_id": "Código de desembolso",
    "payment_ref": "Código de recaudo",
    "payment_date": "Fecha de pago",
    "currency": "Moneda",
    "capital": "Capital",
    "banco_remitente": "Banco remitente",
}

# Optional columns for Colombia
COLOMBIA_OPTIONAL_COLUMNS: Dict[str, str] = {
    "exchangerate": "Tasa de cambio de FK/en línea",
    "nt_flag": "NT",  # Operaciones Cedidas flag (also used for spread routing)
    "recompra": "Recomprado",  # Indicates if cedida operation was repurchased by Fincargo Colombia
    "spread": "Spread",  # Spread value from input (column AX)
    "medio_pago": "Médio de pago",  # Payment method: Manual, Pago en línea, etc. (Note: accented 'é' in source file)
    "total_pagado_usd": "Total pagado [USD]",  # Total paid in USD for spread calculations
    "referencia_bancaria": "Referencia bancaria",  # Bank reference (for comision_banco)
    "short_code": "Short Code",  # Payment provider identifier (SUPRA vs PA)
    "cuenta_remitente": "Cuenta Remitente",  # Sender account (for account lookup)
}

# Concept columns for Colombia (maps concept type -> source column name)
COLOMBIA_CONCEPT_COLUMNS: Dict[str, str] = {
    "CAPITAL": "Capital",
    "4X1000": "4x1000",
    "FONDO_GARANTIAS": "Fondo de garantías",
    "IVA_FONDO_GARANTIAS": "IVA Fondo de garantías",
    "SEGUROS": "Seguro + IVA",
    "SERVICIO_ORIGINACION": "Servicio de originación",
    "SERVICIO_GIRO": "Servicio de giro + IVA",
    "COSTOS_ADICIONALES": "Costos adicionales",
    "INTERESES_CORRIENTES": "Intereses Corrientes",
    # Interest mora columns - PAR 60/61 with Tasa corriente/Tasa restante
    "INTERESES_MORA_TASA_CORRIENTE_PAR_60": "Intereses de Mora (Tasa corriente) PAR 60",
    "INTERESES_MORA_TASA_RESTANTE_PAR_60": "Intereses de Mora (Tasa restante de mora) PAR 60",
    "INTERESES_MORA_TASA_CORRIENTE_PAR_61": "Intereses de Mora (Tasa corriente) PAR 61",
    "INTERESES_MORA_TASA_RESTANTE_PAR_61": "Intereses de Mora (Tasa restante de mora) PAR 61",
    # Discount and forgiveness columns
    "DESCUENTO_APLICADO": "Descuento aplicado",
    "CONDONACION_INTERESES_CORRIENTES": "Condonación intereses corrientes",
    "CONDONACION_MORA_TASA_CORRIENTE_PAR_60": "Condonación intereses de mora (Tasa corriente) Par 60",
    "CONDONACION_MORA_TASA_RESTANTE_PAR_60": "Condonación intereses de mora (Tasa restante de mora) Par 60",
    "CONDONACION_MORA_TASA_CORRIENTE_PAR_61": "Condonación intereses de mora (Tasa corriente) Par 61",
    "CONDONACION_MORA_TASA_RESTANTE_PAR_61": "Condonación intereses de mora (Tasa restante de mora) Par 61",
}

# Required columns for México Historial de Pagos
MEXICO_REQUIRED_COLUMNS: Dict[str, str] = {
    "cliente": "Cliente",
    "customer_external_id": "Identificación del cliente",
    "invoice_core_id": "Código de desembolso",
    "payment_ref": "Código de recaudo",
    "payment_date": "Fecha de pago",
    "currency": "Moneda",
    "capital": "Capital",
    "banco_remitente": "Banco remitente",
}

# Optional columns for México
MEXICO_OPTIONAL_COLUMNS: Dict[str, str] = {
    "exchangerate": "Tasa de cambio de FK/en línea",
    "medio_pago": "Médio de pago",  # Payment method: Manual, Pago en línea, etc. (Note: accented 'é' in source file)
    "total_pagado_usd": "Total pagado [USD]",  # Total paid in USD for spread calculations
    "referencia_bancaria": "Referencia bancaria",  # Bank reference (for comision_banco)
    "short_code": "Short Code",  # Payment provider identifier (SUPRA vs PA)
    "cuenta_remitente": "Cuenta Remitente",  # Sender account (for account lookup)
}

# Concept columns for México
# Uses space-separated concept type names for output (e.g., "COMISION DESEMBOLSO")
MEXICO_CONCEPT_COLUMNS: Dict[str, str] = {
    "CAPITAL": "Capital",
    "COMISION DESEMBOLSO": "Comisión del desembolso + IVA",
    "COMISION DISPOSICION": "Comisión por disposición de crédito",
    "COMISION SWIFT": "Comisión SWIFT",
    "COMISION ADMINISTRACION": "Comisión de administración y manejo",
    "COMISION APERTURA": "Comisión de apertura del cupo aprobado",
    "SEGUROS": "Seguro + IVA",
    "COSTOS ADICIONALES": "Costos adicionales",
    "INTERESES_CORRIENTES": "Intereses Corrientes",
    # Interest mora columns - PAR 60/61 with Tasa corriente/Tasa restante (same as Colombia)
    "INTERESES_MORA_TASA_CORRIENTE_PAR_60": "Intereses de Mora (Tasa corriente) PAR 60",
    "INTERESES_MORA_TASA_RESTANTE_PAR_60": "Intereses de Mora (Tasa restante de mora) PAR 60",
    "INTERESES_MORA_TASA_CORRIENTE_PAR_61": "Intereses de Mora (Tasa corriente) PAR 61",
    "INTERESES_MORA_TASA_RESTANTE_PAR_61": "Intereses de Mora (Tasa restante de mora) PAR 61",
    # Discount and forgiveness columns
    "DESCUENTO_APLICADO": "Descuento aplicado",
    "CONDONACION_INTERESES_CORRIENTES": "Condonación intereses corrientes",
    "CONDONACION_MORA_TASA_CORRIENTE_PAR_60": "Condonación intereses de mora (Tasa corriente) Par 60",
    "CONDONACION_MORA_TASA_RESTANTE_PAR_60": "Condonación intereses de mora (Tasa restante de mora) Par 60",
    "CONDONACION_MORA_TASA_CORRIENTE_PAR_61": "Condonación intereses de mora (Tasa corriente) Par 61",
    "CONDONACION_MORA_TASA_RESTANTE_PAR_61": "Condonación intereses de mora (Tasa restante de mora) Par 61",
}


# =============================================================================
# OUTPUT TEMPLATE COLUMNS
# =============================================================================

# Column names for the NetSuite output template (14 columns in exact order)
OUTPUT_TEMPLATE_COLUMNS = [
    "customer_external_id",
    "invoice_core_id",
    "concept_type",
    "payment_date",
    "payment_amount",
    "currency",
    "payment_ref",
    "account",
    "araccount",
    "exchangerate",
    "comision_banco",
    "Spread PA",
    "Spread FK",
    "Spread Supra",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_ar_account(
    concept_type: str,
    country: str,
    is_nt: bool = False,
    is_recomprada: bool = False
) -> Optional[int]:
    """
    Get the AR account ID for a concept type.

    Args:
        concept_type: Type of payment concept (e.g., 'CAPITAL', 'INTERESES')
        country: Country code ('colombia' or 'mexico')
        is_nt: Whether this is an Operaciones Cedidas (NT) operation (Colombia only)
        is_recomprada: Whether this is a repurchased operation (Colombia only).
            When True, cedida operations use Fincargo Colombia accounts instead
            of Patrimonio Autónomo accounts.

    Returns:
        AR account ID or None if not found

    Note:
        For Colombia, the AR account selection logic is:
        - NT empty → Fincargo Colombia accounts (302, 258, 1387)
        - NT populated AND NOT recomprada → Patrimonio Autónomo accounts (304, 259, 310, 1474)
        - NT populated AND recomprada → Fincargo Colombia accounts (302, 258, 1387)
    """
    country_lower = country.lower()

    if country_lower == "colombia":
        # Use NT accounts only when is_nt=True AND is_recomprada=False
        # Recomprada operations revert to Fincargo Colombia accounts
        if is_nt and not is_recomprada:
            return COLOMBIA_NT_AR_ACCOUNTS.get(concept_type)
        return COLOMBIA_AR_ACCOUNTS.get(concept_type)

    elif country_lower == "mexico":
        return MEXICO_AR_ACCOUNTS.get(concept_type)

    return None


def get_required_columns(country: str) -> Dict[str, str]:
    """
    Get required column mappings for a country.

    Args:
        country: Country code ('colombia' or 'mexico')

    Returns:
        Dictionary mapping internal names to expected column names
    """
    country_lower = country.lower()

    if country_lower == "colombia":
        return COLOMBIA_REQUIRED_COLUMNS
    elif country_lower == "mexico":
        return MEXICO_REQUIRED_COLUMNS

    return {}


def get_concept_columns(country: str) -> Dict[str, str]:
    """
    Get concept column mappings for a country.

    Args:
        country: Country code ('colombia' or 'mexico')

    Returns:
        Dictionary mapping concept types to expected column names
    """
    country_lower = country.lower()

    if country_lower == "colombia":
        return COLOMBIA_CONCEPT_COLUMNS
    elif country_lower == "mexico":
        return MEXICO_CONCEPT_COLUMNS

    return {}


def get_optional_columns(country: str) -> Dict[str, str]:
    """
    Get optional column mappings for a country.

    Args:
        country: Country code ('colombia' or 'mexico')

    Returns:
        Dictionary mapping internal names to expected column names
    """
    country_lower = country.lower()

    if country_lower == "colombia":
        return COLOMBIA_OPTIONAL_COLUMNS
    elif country_lower == "mexico":
        return MEXICO_OPTIONAL_COLUMNS

    return {}


def get_bank_account_id(cuenta_remitente: Optional[str], country: str) -> Optional[int]:
    """
    Get the NetSuite internal account ID for a bank account number.

    Args:
        cuenta_remitente: Bank account number from 'Cuenta Remitente' column
        country: Country code ('colombia' or 'mexico')

    Returns:
        NetSuite internal account ID or None if not found
    """
    if not cuenta_remitente:
        return None

    country_lower = country.lower()

    if country_lower == "colombia":
        # Normalize the account number by stripping whitespace
        normalized = str(cuenta_remitente).strip()
        return COLOMBIA_BANK_ACCOUNT_MAPPING.get(normalized)

    elif country_lower == "mexico":
        # Normalize the account number by stripping whitespace
        normalized = str(cuenta_remitente).strip()
        return MEXICO_BANK_ACCOUNT_MAPPING.get(normalized)

    return None
