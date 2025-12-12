"""
Constants for document generation services

This module contains static values and configuration constants used across
various document generation services, particularly for DIAN (Colombian Tax Authority)
creditor information.
"""

# DIAN Creditor Information
# Used for Instruccion de Mandato documents when payment is destined to DIAN
# (Direccion de Impuestos y Aduanas Nacionales - Colombian Tax Authority)
DIAN_CREDITOR_INFO = {
    "razon_social": "DIAN - Direccion de Impuestos y Aduanas Nacionales",
    "nit": "800.197.268-4",
    "banco": "PSE/Recaudo Electronico",
    "tipo_cuenta": "PSE",
    "numero_cuenta": "N/A - Pago Electronico"
}

# Keywords to detect DIAN-related creditors in Anexo I table
# Used to automatically identify when a creditor is DIAN and populate with static values
DIAN_KEYWORDS = [
    'dian',
    'entidad de pago de impuestos',
    'tributo',
    'aduanero',
    'impuesto',
    'direccion de impuestos',
    'aduanas nacionales',
    'tax authority',
    'customs'
]
