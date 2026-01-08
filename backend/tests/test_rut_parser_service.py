"""
Unit tests for RUT Parser Service

Tests parsing of Colombian RUT documents to extract custodian information.
Covers different RUT formats including GAMALOG format with columnar data layout.
"""
import os
import pytest
from pathlib import Path

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.servicios.rut_parser_service import RUTParserService


class TestRUTParserService:
    """Test cases for RUTParserService"""

    @pytest.fixture
    def parser(self):
        """Create a RUT parser instance"""
        return RUTParserService()

    @pytest.fixture
    def gamalog_rut_path(self):
        """Path to GAMALOG RUT test file"""
        # The file is in the Example Files for Reqs directory
        base_path = Path(__file__).parent.parent.parent
        return base_path / "Example FIles for Reqs" / "4 RUT COMPLETO 30 07 2024.pdf"

    def test_parse_gamalog_rut_all_fields(self, parser, gamalog_rut_path):
        """
        Test parsing GAMALOG S.A.S RUT format

        This RUT has a specific format where:
        - NIT digits appear as individual lines
        - Multiple legal representatives appear in columnar format
        - Names and IDs for each rep are interleaved

        Expected values:
        - Company: GAMALOG S.A.S
        - NIT: 900026089-2
        - Legal Rep: GALVIS FRANCO GABRIEL IGNACIO
        - Legal Rep ID: 73094097
        - City: Bogotá, D.C.
        - Email: gerencia.logistica@redgama.com
        """
        if not gamalog_rut_path.exists():
            pytest.skip(f"Test file not found: {gamalog_rut_path}")

        with open(gamalog_rut_path, 'rb') as f:
            rut_bytes = f.read()

        result = parser.parse_rut_pdf(rut_bytes)

        # Verify all extracted fields
        # Allow for minor whitespace variations in company name
        assert result.nombre_operador_custodio.replace('  ', ' ') == "GAMALOG S.A.S", \
            f"Expected 'GAMALOG S.A.S', got '{result.nombre_operador_custodio}'"

        assert result.nit_operador_custodio == "900026089-2", \
            f"Expected '900026089-2', got '{result.nit_operador_custodio}'"

        assert result.nombre_representante_legal_custodio == "GALVIS FRANCO GABRIEL IGNACIO", \
            f"Expected 'GALVIS FRANCO GABRIEL IGNACIO', got '{result.nombre_representante_legal_custodio}'"

        assert result.cc_representante_legal_custodio == "73094097", \
            f"Expected '73094097', got '{result.cc_representante_legal_custodio}'"

        assert result.ciudad_domicilio_custodio == "Bogotá, D.C.", \
            f"Expected 'Bogotá, D.C.', got '{result.ciudad_domicilio_custodio}'"

        assert result.email_operador_custodio == "gerencia.logistica@redgama.com", \
            f"Expected 'gerencia.logistica@redgama.com', got '{result.email_operador_custodio}'"

    def test_parse_gamalog_rut_nit_extraction(self, parser, gamalog_rut_path):
        """Test NIT extraction from GAMALOG format (newline-separated digits)"""
        if not gamalog_rut_path.exists():
            pytest.skip(f"Test file not found: {gamalog_rut_path}")

        with open(gamalog_rut_path, 'rb') as f:
            rut_bytes = f.read()

        result = parser.parse_rut_pdf(rut_bytes)

        # NIT should be in format XXXXXXXXX-X
        assert '-' in result.nit_operador_custodio
        nit_parts = result.nit_operador_custodio.split('-')
        assert len(nit_parts) == 2
        assert len(nit_parts[0]) == 9  # 9 digit NIT
        assert len(nit_parts[1]) == 1  # 1 digit DV

    def test_parse_gamalog_rut_legal_rep_id_extraction(self, parser, gamalog_rut_path):
        """Test legal representative ID extraction from GAMALOG columnar format"""
        if not gamalog_rut_path.exists():
            pytest.skip(f"Test file not found: {gamalog_rut_path}")

        with open(gamalog_rut_path, 'rb') as f:
            rut_bytes = f.read()

        result = parser.parse_rut_pdf(rut_bytes)

        # ID should be 8 digits for Colombian cedula
        assert result.cc_representante_legal_custodio.isdigit()
        assert 7 <= len(result.cc_representante_legal_custodio) <= 10

    def test_parse_gamalog_rut_legal_rep_name_extraction(self, parser, gamalog_rut_path):
        """Test legal representative name extraction from GAMALOG columnar format"""
        if not gamalog_rut_path.exists():
            pytest.skip(f"Test file not found: {gamalog_rut_path}")

        with open(gamalog_rut_path, 'rb') as f:
            rut_bytes = f.read()

        result = parser.parse_rut_pdf(rut_bytes)

        # Name should have 4 parts: primer apellido, segundo apellido, primer nombre, otros nombres
        name_parts = result.nombre_representante_legal_custodio.split()
        assert len(name_parts) == 4, f"Expected 4 name parts, got {len(name_parts)}"

        # All parts should be uppercase
        for part in name_parts:
            assert part.isupper(), f"Name part '{part}' should be uppercase"

    def test_parse_invalid_pdf_raises_error(self, parser):
        """Test that invalid PDF content raises appropriate error"""
        invalid_bytes = b"This is not a PDF"

        with pytest.raises(ValueError) as exc_info:
            parser.parse_rut_pdf(invalid_bytes)

        assert "Invalid PDF" in str(exc_info.value) or "Error parsing" in str(exc_info.value)

    def test_parse_empty_pdf_raises_error(self, parser):
        """Test that empty PDF content raises appropriate error"""
        empty_bytes = b""

        with pytest.raises(ValueError):
            parser.parse_rut_pdf(empty_bytes)

    def test_custodian_data_model_validation(self, parser, gamalog_rut_path):
        """Test that returned CustodianData model has all required fields"""
        if not gamalog_rut_path.exists():
            pytest.skip(f"Test file not found: {gamalog_rut_path}")

        with open(gamalog_rut_path, 'rb') as f:
            rut_bytes = f.read()

        result = parser.parse_rut_pdf(rut_bytes)

        # Verify all required attributes exist
        required_fields = [
            'nombre_operador_custodio',
            'nit_operador_custodio',
            'nombre_representante_legal_custodio',
            'cc_representante_legal_custodio',
            'ciudad_domicilio_custodio',
            'email_operador_custodio',
            'tipo_identificacion_representante_legal_custodio'
        ]

        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"
            value = getattr(result, field)
            assert value is not None, f"Field {field} is None"
            assert value.strip() != '', f"Field {field} is empty"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
