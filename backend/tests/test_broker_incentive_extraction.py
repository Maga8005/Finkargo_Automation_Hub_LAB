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
    ContractStatus,
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
            contract_status=ContractStatus.FOUND,
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
            contract_status=ContractStatus.FOUND,
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
            contract_status=ContractStatus.NOT_FOUND,
            pdf_path="/path/to/gamma/",
            extraction_date=datetime.now().isoformat(),
            warnings=["No PDF files found in folder"],
            extraction_confidence=0.0
        ),
        BrokerIncentiveData(
            broker_name="Broker Delta",
            contract_date="2024-07-10",
            rfc=None,
            signatory_name=None,
            credit_line_incentive_pct=None,
            operations_incentive_pct=None,
            contract_type=ContractType.UNKNOWN,
            contract_status=ContractStatus.ERROR,
            pdf_path="/path/to/delta/contrato.pdf",
            extraction_date=datetime.now().isoformat(),
            warnings=["Extraction error: PDF could not be parsed"],
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

    def test_find_contract_pdf_no_match_returns_none(self, scanner):
        """Test finding contract PDF returns None when no pattern matches."""
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
        # No PDFs match contract patterns, so should return None
        assert result is None

    def test_is_contract_pdf_docusign_pattern(self, scanner):
        """Test is_contract_pdf matches DocuSign patterns."""
        assert scanner.is_contract_pdf("Complete_con_Docusign_2024.pdf") is True
        assert scanner.is_contract_pdf("completado_con_docusign.pdf") is True
        assert scanner.is_contract_pdf("Complete_con_DocuSign_12345.pdf") is True

    def test_is_contract_pdf_contract_patterns(self, scanner):
        """Test is_contract_pdf matches contract patterns."""
        assert scanner.is_contract_pdf("contrato_broker.pdf") is True
        assert scanner.is_contract_pdf("CONTRATO_CORRETAJE.pdf") is True
        assert scanner.is_contract_pdf("corretaje_finkargo.pdf") is True
        assert scanner.is_contract_pdf("correta.pdf") is True
        assert scanner.is_contract_pdf("bono_2024.pdf") is True
        assert scanner.is_contract_pdf("incentivo_operaciones.pdf") is True
        assert scanner.is_contract_pdf("convenio_colaboracion.pdf") is True
        assert scanner.is_contract_pdf("acuerdo_comercial.pdf") is True

    def test_is_contract_pdf_no_match(self, scanner):
        """Test is_contract_pdf returns False for non-contract files."""
        assert scanner.is_contract_pdf("rut_empresa.pdf") is False
        assert scanner.is_contract_pdf("document.pdf") is False
        assert scanner.is_contract_pdf("foto_oficina.pdf") is False
        assert scanner.is_contract_pdf("anexo_fiscal.pdf") is False

    def test_has_contract_pdf_true(self, scanner):
        """Test has_contract_pdf returns True when folder has contract."""
        folder = BrokerFolder(
            folder_path="/test",
            folder_name="20240515 Broker",
            broker_name="Broker",
            contract_date="2024-05-15",
            pdf_files=[
                "/test/rut.pdf",
                "/test/contrato_2024.pdf",
                "/test/other.pdf"
            ]
        )
        assert scanner.has_contract_pdf(folder) is True

    def test_has_contract_pdf_false(self, scanner):
        """Test has_contract_pdf returns False when no contract pattern matches."""
        folder = BrokerFolder(
            folder_path="/test",
            folder_name="20240515 Broker",
            broker_name="Broker",
            contract_date="2024-05-15",
            pdf_files=[
                "/test/rut.pdf",
                "/test/document.pdf",
                "/test/other.pdf"
            ]
        )
        assert scanner.has_contract_pdf(folder) is False

    def test_has_contract_pdf_empty(self, scanner):
        """Test has_contract_pdf returns False when folder has no PDFs."""
        folder = BrokerFolder(
            folder_path="/test",
            folder_name="20240515 Broker",
            broker_name="Broker",
            contract_date="2024-05-15",
            pdf_files=[]
        )
        assert scanner.has_contract_pdf(folder) is False


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

    def test_extract_credit_line_jose_martin_gaspar_format(self, extractor):
        """Test extracting credit line from JOSE MARTIN GASPAR contract format."""
        text = '''
        ANEXO A
        ESPECIFICACIONES DEL BONO

        1. Bonos. Para efectos de lo previsto en la Cláusula II del Contrato...

        (a) Un Bono equivalente al 80% (ochenta por ciento) del monto cobrado a cada Nuevo
        Cliente por concepto de "Bono de Apertura" en el marco del Contrato de Crédito, con ocasión
        de la Primera Operación llevada a cabo por parte del Nuevo Cliente en mención (el "Bono Fijo").
        '''
        result = extractor.extract_credit_line_incentive(text)
        assert result == 80.0

    def test_extract_operations_jose_martin_gaspar_format(self, extractor):
        """Test extracting operations from JOSE MARTIN GASPAR contract format."""
        text = '''
        (b) Un Bono equivalente al 0.1% (cero punto uno por ciento) sobre el monto de cada
        Operación Elegible adelantada por cada Nuevo Cliente durante el Periodo de Pago de Bono Variable
        (como dicho término se define en el Numeral 2 del presente Anexo) aplicable respecto de dicho Nuevo
        Cliente (el "Bono Variable").
        '''
        result = extractor.extract_operations_incentive(text)
        assert result == 0.1

    def test_identify_contract_type_anexo_a_format(self, extractor):
        """Test contract type identification for Anexo A format."""
        text = '''
        ANEXO A
        ESPECIFICACIONES DEL BONO

        1. Bonos. Para efectos de lo previsto en la Cláusula II del Contrato...
        (a) Un Bono equivalente al 80% (ochenta por ciento) del monto cobrado...Bono de Apertura
        '''
        result = extractor.identify_contract_type(text)
        assert result == ContractType.BONO

    def test_identify_contract_type_colaboracion(self, extractor):
        """Test identifying COLABORACIÓN contract type."""
        text = """
        CONTRATO DE COLABORACIÓN

        ARTÍCULO III
        INCENTIVOS

        Sección 3.01    Descripción y condiciones para el ejercicio de Incentivos.

        (a)    Para efectos de lo previsto en la Sección 1.01, Finkargo reconocerá un incentivo
        equivalente al cero punto cero siete por ciento (0.07%) sobre el monto de cada Operación Elegible
        """
        result = extractor.identify_contract_type(text)
        assert result == ContractType.COLABORACION

    def test_extract_operations_colaboracion_format(self, extractor):
        """Test extracting operations incentive from COLABORACIÓN format."""
        text = """
        ARTÍCULO III
        INCENTIVOS

        Sección 3.01    Descripción y condiciones para el ejercicio de Incentivos.

        (a)    Para efectos de lo previsto en la Sección 1.01, Finkargo reconocerá un incentivo
        equivalente al cero punto cero siete por ciento (0.07%) sobre el monto de cada Operación Elegible
        adelantada por cada Nuevo Cliente durante el Término de Incentivos (el "Incentivo").
        """
        result = extractor._extract_colaboracion_operations_incentive(text)
        assert result == 0.07

    def test_extract_operations_colaboracion_0_10_format(self, extractor):
        """Test extracting operations incentive with 0.10% value."""
        text = """
        ARTÍCULO III
        INCENTIVOS

        Sección 3.01    Descripción y condiciones para el ejercicio de Incentivos.

        (a)    Para efectos de lo previsto en la Sección 1.01, Finkargo reconocerá un incentivo
        equivalente al cero punto diez por ciento (0.10%) sobre el monto de cada Operación Elegible
        """
        result = extractor._extract_colaboracion_operations_incentive(text)
        assert result == 0.10

    def test_extract_operations_colaboracion_0_05_format(self, extractor):
        """Test extracting operations incentive with 0.05% value."""
        text = """
        Finkargo reconocerá un incentivo equivalente al cero punto cero cinco por ciento (0.05%)
        sobre el monto de cada Operación Elegible adelantada por cada Nuevo Cliente
        """
        result = extractor._extract_colaboracion_operations_incentive(text)
        assert result == 0.05

    def test_extract_colaboracion_rfc_from_freelance_column(self, extractor):
        """Test extracting RFC from FREELANCE column in COLABORACIÓN contracts."""
        text = """
        FINKARGO,                                       FREELANCE,

        DocuSigned by:                                  DocuSigned by:
        Angélica Guzmán                                 Samuel Vera
        60FD2FFB9A464BF...                             7DDDC13CE92C4DB...

        Alma Angélica Guzmán Martínez                   Samuel Orval Vera de Luna
        RFC No. GUMA790902MR2                           RFC VELS720821EL1
        Representante Legal                             Por su propio derecho
        """
        result = extractor._extract_colaboracion_signatory_info(text)
        assert result.rfc == "VELS720821EL1"
        assert result.rfc != "GUMA790902MR2"  # Must NOT be Finkargo's RFC

    def test_extract_colaboracion_signatory_from_freelance_column(self, extractor):
        """Test extracting signatory name from FREELANCE column in COLABORACIÓN contracts."""
        text = """
        FINKARGO,                                       FREELANCE,

        DocuSigned by:                                  DocuSigned by:
        Angélica Guzmán                                 Samuel Vera
        60FD2FFB9A464BF...                             7DDDC13CE92C4DB...

        Alma Angélica Guzmán Martínez                   Samuel Orval Vera de Luna
        RFC No. GUMA790902MR2                           RFC VELS720821EL1
        Representante Legal                             Por su propio derecho
        """
        result = extractor._extract_colaboracion_signatory_info(text)
        assert result.name == "Samuel Orval Vera de Luna"
        assert result.name != "Alma Angélica Guzmán Martínez"  # Must NOT be Finkargo's rep

    def test_extract_colaboracion_signatory_info_complete(self, extractor):
        """Test extracting both name and RFC from COLABORACIÓN contract FREELANCE column."""
        text = """
        LEÍDO QUE FUE POR AMBAS PARTES EL PRESENTE INSTRUMENTO, Y
        CONOCIENDO SU VALOR, CONTENIDO Y ALCANCE LEGAL, SE FIRMA EN LA CIUDAD DE MÉXICO,
        EN LA FECHA DE FIRMA INDICADA EN EL RUBRO DEL PRESENTE INSTRUMENTO.

        FINKARGO,                                       FREELANCE,

        DocuSigned by:                                  DocuSigned by:
        Angélica Guzmán                                 Juan Garcia
        60FD2FFB9A464BF...                             7DDDC13CE92C4DB...

        Alma Angélica Guzmán Martínez                   Juan Garcia Ramirez
        RFC No. GUMA790902MR2                           RFC GARJ850101XYZ
        Representante Legal                             Por su propio derecho
        """
        result = extractor._extract_colaboracion_signatory_info(text)
        # Both name and RFC should be extracted from FREELANCE column
        assert result.name == "Juan Garcia Ramirez"
        assert result.rfc == "GARJ850101XYZ"

    def test_extract_colaboracion_signatory_excludes_finkargo_rfc(self, extractor):
        """Test that Finkargo's RFC is never extracted for COLABORACIÓN contracts."""
        text = """
        FINKARGO,

        Alma Angélica Guzmán Martínez
        RFC No. GUMA790902MR2
        Representante Legal
        """
        result = extractor._extract_colaboracion_signatory_info(text)
        # Should not extract Finkargo's RFC
        assert result.rfc != "GUMA790902MR2"
        # RFC should be None if only Finkargo's data is present
        assert result.rfc is None

    def test_extract_colaboracion_signatory_excludes_finkargo_name(self, extractor):
        """Test that Finkargo's representative name is never extracted for COLABORACIÓN contracts."""
        text = """
        FINKARGO,

        Alma Angélica Guzmán Martínez
        RFC No. GUMA790902MR2
        Representante Legal
        """
        result = extractor._extract_colaboracion_signatory_info(text)
        # Should not extract Finkargo's representative name
        assert result.name != "Alma Angélica Guzmán Martínez"
        # Name should be None if only Finkargo's data is present
        assert result.name is None

    def test_extract_signatory_info_with_colaboracion_contract_type(self, extractor):
        """Test that extract_signatory_info routes correctly for COLABORACIÓN contracts."""
        text = """
        FINKARGO,                                       FREELANCE,

        Alma Angélica Guzmán Martínez                   Maria Lopez Garcia
        RFC No. GUMA790902MR2                           RFC LOGM901215ABC
        Representante Legal                             Por su propio derecho
        """
        # Call with COLABORACION contract type
        result = extractor.extract_signatory_info(text, ContractType.COLABORACION)
        # Should use COLABORACIÓN-specific extraction
        assert result.rfc == "LOGM901215ABC"
        assert result.name == "Maria Lopez Garcia"


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

        assert stats['total_records'] == 4
        assert stats['bono_contracts'] == 1
        assert stats['incentivos_contracts'] == 1
        assert stats['unknown_contracts'] == 2
        assert stats['contracts_found'] == 2
        assert stats['contracts_not_found'] == 1
        assert stats['contracts_error'] == 1
        assert stats['rfc_found'] == 1
        assert stats['rfc_missing'] == 3

    def test_format_contract_type(self, excel_generator):
        """Test contract type formatting."""
        assert excel_generator._format_contract_type(ContractType.BONO) == "Bono"
        assert excel_generator._format_contract_type(ContractType.INCENTIVOS) == "Incentivos"
        assert excel_generator._format_contract_type(ContractType.COLABORACION) == "Colaboración"
        assert excel_generator._format_contract_type(ContractType.UNKNOWN) == "Desconocido"

    def test_format_contract_status(self, excel_generator):
        """Test contract status formatting."""
        assert excel_generator._format_contract_status(ContractStatus.FOUND) == "Encontrado"
        assert excel_generator._format_contract_status(ContractStatus.NOT_FOUND) == "Sin Contrato"
        assert excel_generator._format_contract_status(ContractStatus.ERROR) == "Error"


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

    def test_full_extraction_colaboracion_contract(self, extractor):
        """Test full extraction from a COLABORACIÓN contract."""
        sample_text = """
        CONTRATO DE COLABORACIÓN

        Entre las partes:
        Miguel Angel Perez Rodriguez
        R.F.C.: PERM850515ABC

        ARTÍCULO III
        INCENTIVOS

        Sección 3.01    Descripción y condiciones para el ejercicio de Incentivos.

        (a)    Para efectos de lo previsto en la Sección 1.01, Finkargo reconocerá un incentivo
        equivalente al cero punto cero siete por ciento (0.07%) sobre el monto de cada Operación Elegible
        adelantada por cada Nuevo Cliente durante el Término de Incentivos (el "Incentivo").

        (b)    El Incentivo se reconocerá por cada una de las Operaciones Elegibles adelantadas
        por el Nuevo Cliente durante el término de un (1) año.
        """

        with patch.object(extractor, '_extract_pdf_text', return_value=sample_text):
            result = extractor.extract_from_pdf(
                pdf_path="/fake/colaboracion.pdf",
                broker_name="Miguel Angel Perez",
                contract_date="2024-06-15"
            )

            # Verify contract type is COLABORACION
            assert result.contract_type == ContractType.COLABORACION

            # Verify operations incentive is extracted correctly
            assert result.operations_incentive_pct == 0.07

            # Credit line incentive may be None for COLABORACIÓN contracts (expected)
            # This should NOT generate a warning for COLABORACIÓN

            # Verify RFC is extracted
            assert result.rfc == "PERM850515ABC"

            # Confidence should be reasonable (at least contract type + operations)
            assert result.extraction_confidence >= 0.4

    def test_extract_from_folder_no_contract_pdf(self, extractor):
        """Test extraction from folder with no contract PDF returns NOT_FOUND status."""
        folder = BrokerFolder(
            folder_path="/test/20240515 Test Broker",
            folder_name="20240515 Test Broker",
            broker_name="Test Broker",
            contract_date="2024-05-15",
            pdf_files=[
                "/test/20240515 Test Broker/rut.pdf",
                "/test/20240515 Test Broker/cedula.pdf"
            ]
        )

        result = extractor.extract_from_folder(folder)

        # Status should be NOT_FOUND because no PDF matches contract patterns
        assert result.contract_status == ContractStatus.NOT_FOUND
        assert result.extraction_confidence == 0.0
        assert len(result.warnings) > 0
        assert "no contract file found" in result.warnings[0].lower()

    def test_extract_from_folder_empty(self, extractor):
        """Test extraction from folder with no PDFs returns NOT_FOUND status."""
        folder = BrokerFolder(
            folder_path="/test/20240515 Test Broker",
            folder_name="20240515 Test Broker",
            broker_name="Test Broker",
            contract_date="2024-05-15",
            pdf_files=[]
        )

        result = extractor.extract_from_folder(folder)

        # Status should be NOT_FOUND
        assert result.contract_status == ContractStatus.NOT_FOUND
        assert result.extraction_confidence == 0.0
        assert "No PDF files found" in result.warnings[0]


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
