"""
Unit tests for Bank Certificate Parser Service

Tests parsing of Colombian Bank Certificate PDF documents to extract:
- Company name (razon_social)
- NIT (tax ID)
- Bank name (banco)
- Account type (tipo_cuenta)
- Account number (numero_cuenta)
"""
import pytest
from pathlib import Path
import io

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.servicios.bank_certificate_parser_service import BankCertificateParserService


class TestBankCertificateParserService:
    """Test cases for BankCertificateParserService"""

    @pytest.fixture
    def parser(self):
        """Create a Bank Certificate parser instance"""
        return BankCertificateParserService()

    @pytest.fixture
    def bank_cert_pdf_path(self):
        """Path to Bank Certificate test file"""
        base_path = Path(__file__).parent.parent.parent
        return base_path / "Example FIles for Reqs" / "certificado bancario.pdf"

    def test_parse_valid_bank_certificate(self, parser, bank_cert_pdf_path):
        """
        Test parsing valid Bank Certificate PDF

        This test validates that all critical fields are extracted
        """
        if not bank_cert_pdf_path.exists():
            pytest.skip(f"Test file not found: {bank_cert_pdf_path}")

        with open(bank_cert_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_bank_certificate(pdf_bytes)

        # Verify critical fields are present
        assert result.razon_social is not None and len(result.razon_social) > 0, \
            "razon_social should not be empty"

        assert result.nit is not None and len(result.nit) >= 7, \
            f"NIT should be at least 7 digits, got '{result.nit}'"

        assert result.banco is not None and len(result.banco) > 0, \
            "banco should not be empty"

        assert result.tipo_cuenta is not None and len(result.tipo_cuenta) > 0, \
            "tipo_cuenta should not be empty"

        assert result.numero_cuenta is not None and len(result.numero_cuenta) >= 10, \
            f"numero_cuenta should be at least 10 digits, got '{result.numero_cuenta}'"

    def test_parse_bank_certificate_tipo_cuenta_validation(self, parser, bank_cert_pdf_path):
        """Test that tipo_cuenta is one of the expected values"""
        if not bank_cert_pdf_path.exists():
            pytest.skip(f"Test file not found: {bank_cert_pdf_path}")

        with open(bank_cert_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_bank_certificate(pdf_bytes)

        valid_types = ['CUENTA DE AHORROS', 'CUENTA CORRIENTE', 'Ahorros', 'Corriente', 'PCE']
        assert result.tipo_cuenta in valid_types or 'CUENTA' in result.tipo_cuenta or 'AHORR' in result.tipo_cuenta, \
            f"Expected tipo_cuenta to be a valid account type, got '{result.tipo_cuenta}'"

    def test_parse_invalid_pdf_raises_error(self, parser):
        """Test that invalid PDF content raises ValueError"""
        invalid_pdf_bytes = b"This is not a valid PDF file"

        with pytest.raises(ValueError) as exc_info:
            parser.parse_bank_certificate(invalid_pdf_bytes)

        assert "Invalid PDF" in str(exc_info.value) or "format" in str(exc_info.value)

    def test_parse_empty_pdf_raises_error(self, parser):
        """Test that empty PDF raises ValueError"""
        # Create a minimal invalid PDF
        empty_bytes = b""

        with pytest.raises(ValueError):
            parser.parse_bank_certificate(empty_bytes)

    def test_extract_razon_social_patterns(self, parser):
        """Test razon_social extraction with various text patterns"""
        test_cases = [
            ("BANCOLOMBIA S.A. se permite informar que EMPRESA EJEMPLO SAS identificado(a) con NIT 900123456",
             "EMPRESA EJEMPLO SAS"),
            ("certifica que COMERCIALIZADORA ABC LTDA identificado con NIT 800456789",
             "COMERCIALIZADORA ABC LTDA"),
        ]

        for text, expected in test_cases:
            result = parser._extract_razon_social(text)
            assert result is not None, f"Failed to extract razon_social from: {text[:50]}..."
            assert expected in result, f"Expected '{expected}' in result, got '{result}'"

    def test_extract_nit_patterns(self, parser):
        """Test NIT extraction with various text patterns"""
        test_cases = [
            ("identificado con NIT 900436389", "900436389"),
            ("NIT: 800.197.268-4", "8001972684"),
            ("con NIT 901599856", "901599856"),
        ]

        for text, expected in test_cases:
            result = parser._extract_nit(text)
            assert result == expected, f"Expected '{expected}', got '{result}' from text: {text}"

    def test_extract_banco_detection(self, parser):
        """Test bank name auto-detection"""
        test_cases = [
            ("BANCOLOMBIA S.A. Certificado Bancario", "BANCOLOMBIA"),
            ("BBVA Colombia certifica que", "BBVA"),
            ("BANCO DAVIVIENDA S.A.", "DAVIVIENDA"),
        ]

        for text, expected_bank in test_cases:
            result = parser._extract_banco(text)
            assert result == expected_bank, f"Expected '{expected_bank}', got '{result}'"

    def test_extract_tipo_cuenta_patterns(self, parser):
        """Test account type extraction"""
        test_cases = [
            ("Producto: CUENTA DE AHORROS No. 12345678901", "CUENTA DE AHORROS"),
            ("Tipo: CUENTA CORRIENTE Estado: ACTIVA", "CUENTA CORRIENTE"),
        ]

        for text, expected_type in test_cases:
            result = parser._extract_tipo_cuenta(text)
            assert result == expected_type, f"Expected '{expected_type}', got '{result}'"

    def test_extract_numero_cuenta_patterns(self, parser):
        """Test account number extraction"""
        test_cases = [
            ("No. Producto | 77500002334 | Fecha Apertura", "77500002334"),
            ("Cuenta: 12345678901234", "12345678901234"),
        ]

        for text, expected_cuenta in test_cases:
            result = parser._extract_numero_cuenta(text)
            assert result == expected_cuenta, f"Expected '{expected_cuenta}', got '{result}'"
