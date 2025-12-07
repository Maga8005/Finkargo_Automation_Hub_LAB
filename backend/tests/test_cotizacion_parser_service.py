"""
Unit tests for Cotización Parser Service

Tests parsing of Colombian Cotización de Desembolso PDF documents to extract:
- Quote number (numero_cotizacion)
- Dates (cotización, contrato de crédito)
- Anexo I table items (acreedor, numero_instrumento, monto)
- Total amount calculation
"""
import pytest
from pathlib import Path
from decimal import Decimal

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.servicios.cotizacion_parser_service import CotizacionParserService


class TestCotizacionParserService:
    """Test cases for CotizacionParserService"""

    @pytest.fixture
    def parser(self):
        """Create a Cotización parser instance"""
        return CotizacionParserService()

    @pytest.fixture
    def cotizacion_pdf_path(self):
        """Path to Cotización test file"""
        base_path = Path(__file__).parent.parent.parent
        return base_path / "Example FIles for Reqs" / "Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf"

    def test_parse_cotizacion_all_fields(self, parser, cotizacion_pdf_path):
        """
        Test parsing Cotización de Desembolso PDF

        Expected values:
        - Numero Cotizacion: CO:900436389:1:2:DOM
        - Fecha Cotizacion: 2025-11-10
        - Fecha Contrato Credito: 2025-11-06
        - 3 Anexo items with total 739,860 COP
        """
        if not cotizacion_pdf_path.exists():
            pytest.skip(f"Test file not found: {cotizacion_pdf_path}")

        with open(cotizacion_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_cotizacion(pdf_bytes)

        # Verify numero_cotizacion
        assert result.numero_cotizacion == "CO:900436389:1:2:DOM", \
            f"Expected 'CO:900436389:1:2:DOM', got '{result.numero_cotizacion}'"

        # Verify fecha_cotizacion
        assert result.fecha_cotizacion == "2025-11-10", \
            f"Expected '2025-11-10', got '{result.fecha_cotizacion}'"

        # Verify fecha_contrato_credito (different from fecha_cotizacion)
        assert result.fecha_contrato_credito == "2025-11-06", \
            f"Expected '2025-11-06', got '{result.fecha_contrato_credito}'"

    def test_parse_cotizacion_anexo_items_count(self, parser, cotizacion_pdf_path):
        """Test that exactly 3 Anexo I items are extracted"""
        if not cotizacion_pdf_path.exists():
            pytest.skip(f"Test file not found: {cotizacion_pdf_path}")

        with open(cotizacion_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_cotizacion(pdf_bytes)

        assert len(result.anexo_items) == 3, \
            f"Expected 3 anexo items, got {len(result.anexo_items)}"

    def test_parse_cotizacion_anexo_items_values(self, parser, cotizacion_pdf_path):
        """Test that Anexo I items have correct values"""
        if not cotizacion_pdf_path.exists():
            pytest.skip(f"Test file not found: {cotizacion_pdf_path}")

        with open(cotizacion_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_cotizacion(pdf_bytes)

        # Expected items
        expected_items = [
            ("Entidad de pago de Impuestos", "1003887257", Decimal("407001.00")),
            ("Entidad de pago de Impuestos", "1003887254", Decimal("290000.00")),
            ("Entidad de pago de Impuestos", "1003887815", Decimal("42859.00")),
        ]

        for i, (expected_acreedor, expected_numero, expected_monto) in enumerate(expected_items):
            actual_item = result.anexo_items[i]
            assert actual_item.acreedor == expected_acreedor, \
                f"Item {i}: Expected acreedor '{expected_acreedor}', got '{actual_item.acreedor}'"
            assert actual_item.numero_instrumento == expected_numero, \
                f"Item {i}: Expected numero '{expected_numero}', got '{actual_item.numero_instrumento}'"
            assert actual_item.monto == expected_monto, \
                f"Item {i}: Expected monto {expected_monto}, got {actual_item.monto}"

    def test_parse_cotizacion_monto_total(self, parser, cotizacion_pdf_path):
        """Test that monto_total equals 739,860 COP"""
        if not cotizacion_pdf_path.exists():
            pytest.skip(f"Test file not found: {cotizacion_pdf_path}")

        with open(cotizacion_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_cotizacion(pdf_bytes)

        # Total should be 407,001 + 290,000 + 42,859 = 739,860
        expected_total = Decimal("739860.00")
        assert result.monto_total == expected_total, \
            f"Expected monto_total {expected_total}, got {result.monto_total}"

    def test_parse_cotizacion_fecha_contrato_credito(self, parser, cotizacion_pdf_path):
        """
        Test that fecha_contrato_credito is correctly extracted from the
        'Contrato de Crédito en Pesos de fecha' phrase in the first paragraph.

        Expected: 2025-11-06 (NOT 2025-11-10 which is the cotización date)
        """
        if not cotizacion_pdf_path.exists():
            pytest.skip(f"Test file not found: {cotizacion_pdf_path}")

        with open(cotizacion_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_cotizacion(pdf_bytes)

        # The credit contract date should be 2025-11-06
        assert result.fecha_contrato_credito == "2025-11-06", \
            f"Expected fecha_contrato_credito '2025-11-06', got '{result.fecha_contrato_credito}'"

    def test_fecha_contrato_credito_different_from_cotizacion(self, parser, cotizacion_pdf_path):
        """
        Test that fecha_contrato_credito is different from fecha_cotizacion.

        In the test PDF:
        - Fecha de Cotización de Desembolso: 10 de noviembre de 2025
        - Contrato de Crédito en Pesos de fecha: 6 de noviembre de 2025
        """
        if not cotizacion_pdf_path.exists():
            pytest.skip(f"Test file not found: {cotizacion_pdf_path}")

        with open(cotizacion_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_cotizacion(pdf_bytes)

        # The two dates should be different
        assert result.fecha_cotizacion != result.fecha_contrato_credito, \
            f"fecha_cotizacion ({result.fecha_cotizacion}) should differ from " \
            f"fecha_contrato_credito ({result.fecha_contrato_credito})"

        # Verify the specific values
        assert result.fecha_cotizacion == "2025-11-10"
        assert result.fecha_contrato_credito == "2025-11-06"

    def test_parse_spanish_date_string(self, parser):
        """Test parsing Spanish date strings to ISO format"""
        # Normal date
        result = parser._parse_spanish_date_string("6 de noviembre de 2025")
        assert result == "2025-11-06"

        # Double-digit day
        result = parser._parse_spanish_date_string("10 de noviembre de 2025")
        assert result == "2025-11-10"

        # Different month
        result = parser._parse_spanish_date_string("15 de enero de 2024")
        assert result == "2024-01-15"

        # Invalid month
        result = parser._parse_spanish_date_string("6 de invalidmonth de 2025")
        assert result is None

        # Invalid format
        result = parser._parse_spanish_date_string("invalid date string")
        assert result is None

    def test_parse_cop_amount_with_thousands_separator(self, parser):
        """Test parsing Colombian peso amount with period as thousands separator"""
        # Format: 407.001,00 means 407,001.00
        result = parser._parse_cop_amount("COP 407.001,00")
        assert result == Decimal("407001.00")

    def test_parse_cop_amount_with_whitespace(self, parser):
        """Test parsing COP amount with large whitespace padding"""
        result = parser._parse_cop_amount(" COP                              407.001,00 ")
        assert result == Decimal("407001.00")

    def test_parse_cop_amount_empty(self, parser):
        """Test that empty/dash amount returns None"""
        result = parser._parse_cop_amount("COP -")
        assert result is None

        result = parser._parse_cop_amount("-")
        assert result is None

        result = parser._parse_cop_amount("")
        assert result is None

    def test_parse_cop_amount_zero(self, parser):
        """Test that zero amount returns None (invalid for AnexoItem)"""
        result = parser._parse_cop_amount("COP 0,00")
        assert result is None

    def test_parse_cop_amount_no_decimals(self, parser):
        """Test parsing amount without decimal separator"""
        result = parser._parse_cop_amount("COP 739.860")
        # 739.860 with period as thousands separator = 739860
        assert result == Decimal("739860")

    def test_parse_invalid_pdf_raises_error(self, parser):
        """Test that invalid PDF content raises appropriate error"""
        invalid_bytes = b"This is not a PDF"

        with pytest.raises(ValueError) as exc_info:
            parser.parse_cotizacion(invalid_bytes)

        assert "Invalid PDF" in str(exc_info.value) or "Error parsing" in str(exc_info.value)

    def test_parse_empty_pdf_raises_error(self, parser):
        """Test that empty PDF content raises appropriate error"""
        empty_bytes = b""

        with pytest.raises(ValueError):
            parser.parse_cotizacion(empty_bytes)

    def test_cotizacion_data_model_has_required_fields(self, parser, cotizacion_pdf_path):
        """Test that returned CotizacionData model has all required fields"""
        if not cotizacion_pdf_path.exists():
            pytest.skip(f"Test file not found: {cotizacion_pdf_path}")

        with open(cotizacion_pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        result = parser.parse_cotizacion(pdf_bytes)

        # Verify all required attributes exist
        required_fields = [
            'numero_cotizacion',
            'fecha_cotizacion',
            'fecha_contrato_credito',
            'anexo_items',
            'monto_total'
        ]

        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"

        # numero_cotizacion is critical and must not be empty
        assert result.numero_cotizacion, "numero_cotizacion cannot be empty"

        # monto_total must be positive
        assert result.monto_total > 0, "monto_total must be positive"

        # anexo_items must have at least one item
        assert len(result.anexo_items) > 0, "anexo_items must have at least one item"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
