"""
Broker Incentive Extraction Service Tests

Tests for the broker contract scanning and incentive extraction services.
Tests cover:
1. Directory scanner functionality
2. Incentive extractor regex patterns
3. Excel generator output
4. End-to-end workflow
"""
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.core.servicios.broker_contract_scanner import BrokerContractScanner, BrokerFolder
from src.core.servicios.broker_incentive_extractor import BrokerIncentiveExtractor
from src.core.servicios.broker_incentive_excel_generator import BrokerIncentiveExcelGenerator
from src.interface.broker_incentive_dtos import (
    BrokerIncentiveData,
    BrokerContractScanConfigDTO,
    ContractType,
)


# ==================== Test Fixtures ====================

@pytest.fixture
def scanner():
    """Create a BrokerContractScanner instance."""
    return BrokerContractScanner()


@pytest.fixture
def extractor():
    """Create a BrokerIncentiveExtractor instance."""
    return BrokerIncentiveExtractor()


@pytest.fixture
def excel_generator():
    """Create a BrokerIncentiveExcelGenerator instance."""
    return BrokerIncentiveExcelGenerator()


@pytest.fixture
def sample_broker_folder():
    """Create a sample BrokerFolder object."""
    return BrokerFolder(
        folder_path="/test/20240515 Broker XYZ",
        folder_name="20240515 Broker XYZ",
        broker_name="Broker XYZ",
        contract_date="2024-05-15",
        pdf_files=["/test/20240515 Broker XYZ/contrato.pdf"]
    )


@pytest.fixture
def sample_incentive_records():
    """Create sample BrokerIncentiveData records for testing."""
    return [
        BrokerIncentiveData(
            broker_name="Broker Alpha",
            contract_date="2024-05-15",
            rfc="XAXX010101000",
            signatory_name="Juan Perez",
            credit_line_incentive_pct=2.5,
            operations_incentive_pct=1.0,
            contract_type=ContractType.BONO,
            pdf_path="/path/to/alpha/contrato.pdf",
            extraction_date=datetime.now().isoformat(),
            warnings=[],
            extraction_confidence=1.0
        ),
        BrokerIncentiveData(
            broker_name="Broker Beta",
            contract_date="2024-06-20",
            rfc=None,
            signatory_name="Maria Garcia",
            credit_line_incentive_pct=3.0,
            operations_incentive_pct=None,
            contract_type=ContractType.INCENTIVOS,
            pdf_path="/path/to/beta/contrato.pdf",
            extraction_date=datetime.now().isoformat(),
            warnings=["RFC not found in document"],
            extraction_confidence=0.6
        ),
        BrokerIncentiveData(
            broker_name="Broker Gamma",
            contract_date=None,
            rfc=None,
            signatory_name=None,
            credit_line_incentive_pct=None,
            operations_incentive_pct=None,
            contract_type=ContractType.UNKNOWN,
            pdf_path="/path/to/gamma/contrato.pdf",
            extraction_date=datetime.now().isoformat(),
            warnings=["Could not determine contract type", "Credit line incentive not found"],
            extraction_confidence=0.0
        ),
    ]


# ==================== Scanner Tests ====================

class TestBrokerContractScanner:
    """Tests for BrokerContractScanner."""

    def test_parse_folder_name_valid_yyyymmdd(self, scanner):
        """Test parsing folder name with YYYYMMDD format."""
        broker_name, contract_date = scanner.parse_folder_name("20240515 Broker XYZ")
        assert broker_name == "Broker XYZ"
        assert contract_date == "2024-05-15"

    def test_parse_folder_name_valid_dashed(self, scanner):
        """Test parsing folder name with YYYY-MM-DD format."""
        broker_name, contract_date = scanner.parse_folder_name("2024-05-15 Broker ABC")
        assert broker_name == "Broker ABC"
        assert contract_date == "2024-05-15"

    def test_parse_folder_name_invalid(self, scanner):
        """Test parsing folder name with invalid format."""
        broker_name, contract_date = scanner.parse_folder_name("Random Folder Name")
        assert broker_name is None
        assert contract_date is None

    def test_parse_folder_name_no_space(self, scanner):
        """Test parsing folder name without space after date."""
        broker_name, contract_date = scanner.parse_folder_name("20240515BrokerXYZ")
        assert broker_name is None
        assert contract_date is None

    def test_parse_folder_name_invalid_date(self, scanner):
        """Test parsing folder name with invalid date."""
        broker_name, contract_date = scanner.parse_folder_name("20241350 Broker XYZ")
        # Invalid month (13), should still extract name but no valid date
        assert broker_name == "Broker XYZ"
        assert contract_date is None

    def test_sanitize_path_traversal_blocked(self, scanner):
        """Test that path traversal is blocked."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            scanner._sanitize_path("/root/../etc/passwd")

    def test_sanitize_path_valid(self, scanner):
        """Test that valid paths are accepted."""
        result = scanner._sanitize_path("/Users/alianzas/Brokers")
        assert result == "/Users/alianzas/Brokers"

    def test_scan_directory_not_exists(self, scanner):
        """Test scanning non-existent directory."""
        with pytest.raises(ValueError, match="does not exist"):
            scanner.scan_directory("/nonexistent/path/12345")

    def test_find_contract_pdf_by_pattern(self, scanner):
        """Test finding contract PDF by naming pattern."""
        folder = BrokerFolder(
            folder_path="/test",
            folder_name="20240515 Broker",
            broker_name="Broker",
            contract_date="2024-05-15",
            pdf_files=[
                "/test/readme.pdf",
                "/test/contrato_broker.pdf",
                "/test/other.pdf"
            ]
        )
        result = scanner.find_contract_pdf(folder)
        assert result == "/test/contrato_broker.pdf"

    def test_find_contract_pdf_first_fallback(self, scanner):
        """Test finding contract PDF falls back to first PDF."""
        folder = BrokerFolder(
            folder_path="/test",
            folder_name="20240515 Broker",
            broker_name="Broker",
            contract_date="2024-05-15",
            pdf_files=[
                "/test/document1.pdf",
                "/test/document2.pdf"
            ]
        )
        result = scanner.find_contract_pdf(folder)
        assert result == "/test/document1.pdf"


# ==================== Extractor Tests ====================

class TestBrokerIncentiveExtractor:
    """Tests for BrokerIncentiveExtractor."""

    def test_identify_contract_type_bono(self, extractor):
        """Test identifying Bono contract type."""
        text = """
        ANEXO A
        La empresa pagará un bono de apertura por cada línea de crédito
        y un bono equivalente al 2.5% por operaciones elegibles.
        """
        result = extractor.identify_contract_type(text)
        assert result == ContractType.BONO

    def test_identify_contract_type_incentivos(self, extractor):
        """Test identifying Incentivos contract type."""
        text = """
        CONTRATO DE INCENTIVOS
        Artículo 3: Finkargo reconocerá un incentivo de 2.5% sobre las operaciones.
        """
        result = extractor.identify_contract_type(text)
        assert result == ContractType.INCENTIVOS

    def test_identify_contract_type_unknown(self, extractor):
        """Test identifying unknown contract type."""
        text = "Este es un documento genérico sin indicadores de tipo."
        result = extractor.identify_contract_type(text)
        assert result == ContractType.UNKNOWN

    def test_extract_credit_line_incentive(self, extractor):
        """Test extracting credit line incentive percentage."""
        text = """
        La empresa pagará un bono equivalente al 2.5% del monto colocado
        a cliente como bono de apertura de línea de crédito.
        """
        result = extractor.extract_credit_line_incentive(text)
        assert result == 2.5

    def test_extract_credit_line_incentive_comma_decimal(self, extractor):
        """Test extracting credit line with comma decimal."""
        text = """
        bono equivalente al 2,75% del monto colocado como bono de apertura
        """
        result = extractor.extract_credit_line_incentive(text)
        assert result == 2.75

    def test_extract_operations_incentive(self, extractor):
        """Test extracting operations incentive percentage."""
        text = """
        Adicionalmente, un bono equivalente al 1.5% por operaciones elegibles
        realizadas durante el período.
        """
        result = extractor.extract_operations_incentive(text)
        assert result == 1.5

    def test_extract_signatory_info_rfc(self, extractor):
        """Test extracting RFC from contract text."""
        text = """
        Por el Broker:
        Juan Pérez García
        R.F.C.: PEGJ800101ABC
        """
        result = extractor.extract_signatory_info(text)
        assert result.rfc == "PEGJ800101ABC"

    def test_extract_signatory_info_name(self, extractor):
        """Test extracting signatory name from contract text."""
        text = """
        Por El Broker:
        María García López
        R.F.C.: GALM900515XYZ
        """
        result = extractor.extract_signatory_info(text)
        assert result.name == "María García López"

    def test_parse_percentage_standard(self, extractor):
        """Test parsing standard percentage value."""
        assert extractor._parse_percentage("2.5") == 2.5
        assert extractor._parse_percentage("10") == 10.0

    def test_parse_percentage_comma(self, extractor):
        """Test parsing percentage with comma decimal."""
        assert extractor._parse_percentage("2,5") == 2.5
        assert extractor._parse_percentage("3,75") == 3.75

    def test_parse_percentage_invalid(self, extractor):
        """Test parsing invalid percentage value."""
        assert extractor._parse_percentage(None) is None
        assert extractor._parse_percentage("invalid") is None


# ==================== Excel Generator Tests ====================

class TestBrokerIncentiveExcelGenerator:
    """Tests for BrokerIncentiveExcelGenerator."""

    def test_generate_excel_success(self, excel_generator, sample_incentive_records):
        """Test successful Excel generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.xlsx")

            result = excel_generator.generate_excel(
                records=sample_incentive_records,
                output_path=output_path
            )

            assert os.path.exists(result)
            assert result.endswith(".xlsx")

            # Check file size (should be non-empty)
            file_size = os.path.getsize(result)
            assert file_size > 0

    def test_generate_excel_empty_records(self, excel_generator):
        """Test Excel generation with empty records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "empty_output.xlsx")

            result = excel_generator.generate_excel(
                records=[],
                output_path=output_path
            )

            assert os.path.exists(result)

    def test_generate_excel_invalid_directory(self, excel_generator, sample_incentive_records):
        """Test Excel generation with invalid output directory."""
        with pytest.raises(ValueError, match="does not exist"):
            excel_generator.generate_excel(
                records=sample_incentive_records,
                output_path="/nonexistent/path/output.xlsx"
            )

    def test_calculate_statistics(self, excel_generator, sample_incentive_records):
        """Test statistics calculation."""
        stats = excel_generator._calculate_statistics(sample_incentive_records)

        assert stats['total_records'] == 3
        assert stats['bono_contracts'] == 1
        assert stats['incentivos_contracts'] == 1
        assert stats['unknown_contracts'] == 1
        assert stats['rfc_found'] == 1
        assert stats['rfc_missing'] == 2

    def test_format_contract_type(self, excel_generator):
        """Test contract type formatting."""
        assert excel_generator._format_contract_type(ContractType.BONO) == "Bono"
        assert excel_generator._format_contract_type(ContractType.INCENTIVOS) == "Incentivos"
        assert excel_generator._format_contract_type(ContractType.UNKNOWN) == "Desconocido"


# ==================== Integration Tests ====================

class TestBrokerIncentiveIntegration:
    """Integration tests for the full workflow."""

    def test_dto_serialization(self):
        """Test that DTOs serialize correctly."""
        config = BrokerContractScanConfigDTO(
            directory_path="/test/path",
            include_subfolders=True,
            output_file_path="/tmp/output.xlsx"
        )

        # Convert to dict (simulates JSON serialization)
        config_dict = config.model_dump()

        assert config_dict['directory_path'] == "/test/path"
        assert config_dict['include_subfolders'] is True
        assert config_dict['output_file_path'] == "/tmp/output.xlsx"

    def test_incentive_data_with_warnings(self):
        """Test BrokerIncentiveData with warnings."""
        data = BrokerIncentiveData(
            broker_name="Test Broker",
            pdf_path="/test/path.pdf",
            warnings=["Warning 1", "Warning 2"],
            extraction_confidence=0.5
        )

        assert len(data.warnings) == 2
        assert data.extraction_confidence == 0.5
        assert data.contract_type == ContractType.UNKNOWN

    def test_confidence_calculation(self, extractor):
        """Test extraction confidence is calculated correctly."""
        # Mock the PDF text extraction
        sample_text = """
        ANEXO A
        bono equivalente al 2.5% del monto colocado como bono de apertura
        bono equivalente al 1.0% por operaciones elegibles
        R.F.C.: ABCD123456XYZ
        Por El Broker:
        Juan Pérez García
        """

        with patch.object(extractor, '_extract_pdf_text', return_value=sample_text):
            result = extractor.extract_from_pdf(
                pdf_path="/fake/path.pdf",
                broker_name="Test Broker",
                contract_date="2024-05-15"
            )

            # Should have high confidence with all fields extracted
            assert result.extraction_confidence >= 0.8


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_pdf_text(self, extractor):
        """Test handling of empty PDF text."""
        with patch.object(extractor, '_extract_pdf_text', return_value=""):
            result = extractor.extract_from_pdf(
                pdf_path="/fake/path.pdf",
                broker_name="Test Broker"
            )

            assert result.extraction_confidence == 0.0
            assert len(result.warnings) > 0

    def test_special_characters_in_broker_name(self, scanner):
        """Test handling special characters in broker name."""
        broker_name, contract_date = scanner.parse_folder_name("20240515 Broker & Co.")
        assert broker_name == "Broker & Co."

    def test_very_long_folder_name(self, scanner):
        """Test handling very long folder names."""
        long_name = "20240515 " + "A" * 200
        broker_name, contract_date = scanner.parse_folder_name(long_name)
        assert broker_name == "A" * 200
        assert contract_date == "2024-05-15"

    def test_unicode_in_broker_name(self, scanner):
        """Test handling Unicode characters in broker name."""
        broker_name, contract_date = scanner.parse_folder_name("20240515 Compañía Española S.A.")
        assert broker_name == "Compañía Española S.A."
