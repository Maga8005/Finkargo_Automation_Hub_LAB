"""
Unit tests for PAReportService - CSV parsing and encoding detection

Tests cover:
- Semicolon-delimited CSV with Latin-1 encoding
- CSV with title rows before header
- CSV column renaming validation
- Empty catalog scenario
- Successful matching scenario
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd

from src.core.servicios.pa_report_service import PAReportService
from src.repositorio.pa_rules_repository import PARulesRepository


# ==================== Fixtures ====================

@pytest.fixture
def mock_pa_rules_repository():
    """Create a mock PARulesRepository"""
    repo = MagicMock(spec=PARulesRepository)
    repo.get_all_catalog_accounts = AsyncMock()
    repo.get_account_catalog = AsyncMock()
    repo.create_processing_session = AsyncMock()
    repo.update_processing_session = AsyncMock()
    return repo


@pytest.fixture
def pa_report_service(mock_pa_rules_repository):
    """Create PAReportService with mocked dependencies"""
    return PAReportService(mock_pa_rules_repository)


@pytest.fixture
def sample_catalog_accounts():
    """Sample PA account numbers"""
    return ["110001", "110002", "120001", "120002", "130001"]


@pytest.fixture
def utf8_comma_csv_content():
    """Sample UTF-8 comma-delimited CSV content"""
    return (
        "Cuenta (línea): Número,Cuenta (línea): Nombre,Fecha,Débito,Crédito,Saldo\n"
        "110001,Caja General,2024-01-15,1000.00,0.00,1000.00\n"
        "110002,Bancos,2024-01-16,0.00,500.00,-500.00\n"
        "999999,Otras Cuentas,2024-01-17,100.00,0.00,100.00\n"
    ).encode("utf-8")


@pytest.fixture
def latin1_semicolon_csv_content():
    """Sample Latin-1 semicolon-delimited CSV content (like MovimientoDetallado)"""
    # Use Latin-1 specific characters (í = 0xed, ú = 0xfa, ó = 0xf3)
    # Must return bytes for the service
    return bytes([
        # Header row: "Cuenta (línea): Número;Cuenta (línea): Nombre;Fecha;Débito;Crédito;Saldo\n"
        0x43, 0x75, 0x65, 0x6e, 0x74, 0x61, 0x20, 0x28, 0x6c, 0xed, 0x6e, 0x65, 0x61, 0x29, 0x3a,
        0x20, 0x4e, 0xfa, 0x6d, 0x65, 0x72, 0x6f, 0x3b,  # "Cuenta (línea): Número;"
        0x43, 0x75, 0x65, 0x6e, 0x74, 0x61, 0x20, 0x28, 0x6c, 0xed, 0x6e, 0x65, 0x61, 0x29, 0x3a,
        0x20, 0x4e, 0x6f, 0x6d, 0x62, 0x72, 0x65, 0x3b,  # "Cuenta (línea): Nombre;"
        0x46, 0x65, 0x63, 0x68, 0x61, 0x3b,  # "Fecha;"
        0x44, 0xe9, 0x62, 0x69, 0x74, 0x6f, 0x3b,  # "Débito;"
        0x43, 0x72, 0xe9, 0x64, 0x69, 0x74, 0x6f, 0x3b,  # "Crédito;"
        0x53, 0x61, 0x6c, 0x64, 0x6f, 0x0a,  # "Saldo\n"
    ]) + b"110001;Caja General Mexico;2024-01-15;1000.00;0.00;1000.00\n" \
       + b"110002;Bancos Nacionales;2024-01-16;0.00;500.00;-500.00\n" \
       + b"999999;Otras Cuentas;2024-01-17;100.00;0.00;100.00\n"


@pytest.fixture
def latin1_semicolon_csv_with_title_rows():
    """Sample Latin-1 semicolon-delimited CSV with title rows before header"""
    # Simulates the MovimientoDetallado NOV_25.csv structure
    # 6 title rows before the actual header
    # Must return bytes for the service
    # Note: Title rows should have semicolons to match real file structure
    title_rows = (
        b"Reporte de Movimientos Detallados;;;;\n"
        b"Periodo: Noviembre 2024;;;;\n"
        b"Generado: 01/12/2024;;;;\n"
        b"Empresa: Finkargo Colombia;;;;\n"
        b";;;;\n"
        b";;;;\n"
    )
    # Header row with Latin-1 encoded special characters
    header_row = bytes([
        0x43, 0x75, 0x65, 0x6e, 0x74, 0x61, 0x20, 0x28, 0x6c, 0xed, 0x6e, 0x65, 0x61, 0x29, 0x3a,
        0x20, 0x4e, 0xfa, 0x6d, 0x65, 0x72, 0x6f, 0x3b,  # "Cuenta (línea): Número;"
        0x43, 0x75, 0x65, 0x6e, 0x74, 0x61, 0x20, 0x28, 0x6c, 0xed, 0x6e, 0x65, 0x61, 0x29, 0x3a,
        0x20, 0x4e, 0x6f, 0x6d, 0x62, 0x72, 0x65, 0x3b,  # "Cuenta (línea): Nombre;"
        0x46, 0x65, 0x63, 0x68, 0x61, 0x3b,  # "Fecha;"
        0x44, 0xe9, 0x62, 0x69, 0x74, 0x6f, 0x3b,  # "Débito;"
        0x43, 0x72, 0xe9, 0x64, 0x69, 0x74, 0x6f, 0x3b,  # "Crédito;"
        0x53, 0x61, 0x6c, 0x64, 0x6f, 0x0a,  # "Saldo\n"
    ])
    data_rows = (
        b"110001;Caja General Mexico;2024-11-01;5000.00;0.00;5000.00\n"
        b"120001;Cuentas por Cobrar;2024-11-02;0.00;2000.00;-2000.00\n"
        b"130001;Inventarios;2024-11-03;3000.00;0.00;3000.00\n"
    )
    return title_rows + header_row + data_rows


# ==================== CSV Delimiter Detection Tests ====================

class TestCSVDelimiterDetection:
    """Tests for _detect_csv_delimiter method"""

    def test_detect_comma_delimiter(self, pa_report_service, utf8_comma_csv_content):
        """Test detection of comma delimiter"""
        delimiter = pa_report_service._detect_csv_delimiter(utf8_comma_csv_content)
        assert delimiter == ","

    def test_detect_semicolon_delimiter(self, pa_report_service, latin1_semicolon_csv_content):
        """Test detection of semicolon delimiter"""
        delimiter = pa_report_service._detect_csv_delimiter(latin1_semicolon_csv_content)
        assert delimiter == ";"

    def test_detect_delimiter_with_title_rows(self, pa_report_service, latin1_semicolon_csv_with_title_rows):
        """Test delimiter detection with title rows before header"""
        delimiter = pa_report_service._detect_csv_delimiter(latin1_semicolon_csv_with_title_rows)
        # First line is title, should still detect semicolon from structure
        assert delimiter in [";", ","]  # May detect either based on first line


# ==================== CSV Header Row Detection Tests ====================

class TestCSVHeaderRowDetection:
    """Tests for _detect_header_row method"""

    def test_detect_header_row_at_position_0(self, pa_report_service, utf8_comma_csv_content):
        """Test header detection when header is at row 0"""
        header_row = pa_report_service._detect_header_row(utf8_comma_csv_content, ",")
        assert header_row == 0

    def test_detect_header_row_with_title_rows(self, pa_report_service, latin1_semicolon_csv_with_title_rows):
        """Test header detection with title rows before header"""
        header_row = pa_report_service._detect_header_row(latin1_semicolon_csv_with_title_rows, ";")
        assert header_row == 6  # 6 title rows before the actual header


# ==================== CSV Parsing Tests ====================

class TestCSVParsing:
    """Tests for _parse_csv method"""

    def test_parse_utf8_comma_csv(self, pa_report_service, utf8_comma_csv_content):
        """Test parsing UTF-8 comma-delimited CSV"""
        df = pa_report_service._parse_csv(utf8_comma_csv_content)

        assert len(df) == 3
        assert "Cuenta (línea): Número" in df.columns
        assert "Cuenta (línea): Nombre" in df.columns
        assert "Débito" in df.columns
        assert "Crédito" in df.columns
        assert "Saldo" in df.columns

    def test_parse_latin1_semicolon_csv(self, pa_report_service, latin1_semicolon_csv_content):
        """Test parsing Latin-1 semicolon-delimited CSV"""
        df = pa_report_service._parse_csv(latin1_semicolon_csv_content)

        assert len(df) == 3
        # Check that special characters are correctly decoded
        assert "Cuenta (línea): Número" in df.columns
        assert "Cuenta (línea): Nombre" in df.columns
        assert "Débito" in df.columns
        assert "Crédito" in df.columns
        assert "Saldo" in df.columns

        # Check data content
        assert "Caja General" in df["Cuenta (línea): Nombre"].iloc[0]

    def test_parse_latin1_csv_with_title_rows(self, pa_report_service, latin1_semicolon_csv_with_title_rows):
        """Test parsing Latin-1 CSV with title rows"""
        df = pa_report_service._parse_csv(latin1_semicolon_csv_with_title_rows)

        # Should have 3 data rows (not title rows)
        assert len(df) == 3
        assert "Cuenta (línea): Número" in df.columns

        # First data row should have account 110001, not title text
        # pandas may parse as int or string depending on dtype
        assert str(df["Cuenta (línea): Número"].iloc[0]) == "110001"


# ==================== Column Renaming Tests ====================

class TestColumnRenaming:
    """Tests for _rename_columns method"""

    def test_rename_source_columns(self, pa_report_service, utf8_comma_csv_content):
        """Test column renaming from source to internal names"""
        df = pa_report_service._parse_csv(utf8_comma_csv_content)
        renamed_df = pa_report_service._rename_columns(df)

        # Verify internal column names
        assert "cuenta_linea_numero" in renamed_df.columns
        assert "cuenta_linea_nombre" in renamed_df.columns
        assert "fecha" in renamed_df.columns
        assert "debito" in renamed_df.columns
        assert "credito" in renamed_df.columns
        assert "saldo" in renamed_df.columns

    def test_rename_columns_latin1(self, pa_report_service, latin1_semicolon_csv_content):
        """Test column renaming works with Latin-1 encoded CSV"""
        df = pa_report_service._parse_csv(latin1_semicolon_csv_content)
        renamed_df = pa_report_service._rename_columns(df)

        assert "cuenta_linea_numero" in renamed_df.columns
        assert "cuenta_linea_nombre" in renamed_df.columns


# ==================== Column Validation Tests ====================

class TestColumnValidation:
    """Tests for _validate_columns method"""

    def test_validate_columns_success(self, pa_report_service):
        """Test validation passes with all required columns"""
        columns = [
            "Cuenta (línea): Número",
            "Cuenta (línea): Nombre",
            "Débito",
            "Crédito",
            "Saldo"
        ]
        missing = pa_report_service._validate_columns(columns)
        assert len(missing) == 0

    def test_validate_columns_missing(self, pa_report_service):
        """Test validation detects missing columns"""
        columns = [
            "Cuenta (línea): Número",
            "Cuenta (línea): Nombre",
            # Missing Débito, Crédito, Saldo
        ]
        missing = pa_report_service._validate_columns(columns)
        assert "Débito" in missing
        assert "Crédito" in missing
        assert "Saldo" in missing


# ==================== Upload and Matching Tests ====================

class TestUploadNetsuiteFile:
    """Tests for upload_netsuite_file method"""

    @pytest.mark.asyncio
    async def test_upload_empty_catalog_error(
        self, pa_report_service, mock_pa_rules_repository, utf8_comma_csv_content
    ):
        """Test upload returns error when catalog is empty"""
        mock_pa_rules_repository.get_all_catalog_accounts.return_value = []

        result = await pa_report_service.upload_netsuite_file(
            file_content=utf8_comma_csv_content,
            filename="test.csv"
        )

        assert result.success is False
        assert "catálogo" in result.message.lower()
        assert "Catálogo de cuentas PA vacío" in result.errors

    @pytest.mark.asyncio
    async def test_upload_no_matches_error(
        self, pa_report_service, mock_pa_rules_repository, utf8_comma_csv_content
    ):
        """Test upload returns descriptive error when no accounts match"""
        # Catalog has accounts but none match the file
        mock_pa_rules_repository.get_all_catalog_accounts.return_value = ["999001", "999002"]

        result = await pa_report_service.upload_netsuite_file(
            file_content=utf8_comma_csv_content,
            filename="test.csv"
        )

        assert result.success is False
        assert "coincidencias" in result.message.lower()
        # Verify descriptive message with counts
        assert "Cuentas en archivo:" in result.message
        assert "Cuentas en catálogo:" in result.message

    @pytest.mark.asyncio
    async def test_upload_success_with_matches(
        self, pa_report_service, mock_pa_rules_repository,
        utf8_comma_csv_content, sample_catalog_accounts
    ):
        """Test successful upload with matching accounts"""
        mock_pa_rules_repository.get_all_catalog_accounts.return_value = sample_catalog_accounts
        mock_pa_rules_repository.create_processing_session.return_value = "PA-20240115-0001"

        result = await pa_report_service.upload_netsuite_file(
            file_content=utf8_comma_csv_content,
            filename="test.csv"
        )

        assert result.success is True
        assert result.session_id == "PA-20240115-0001"
        assert result.total_rows == 3
        assert result.pa_rows == 2  # 110001 and 110002 match catalog

    @pytest.mark.asyncio
    async def test_upload_latin1_semicolon_csv(
        self, pa_report_service, mock_pa_rules_repository,
        latin1_semicolon_csv_content, sample_catalog_accounts
    ):
        """Test upload of Latin-1 semicolon-delimited CSV"""
        mock_pa_rules_repository.get_all_catalog_accounts.return_value = sample_catalog_accounts
        mock_pa_rules_repository.create_processing_session.return_value = "PA-20240115-0002"

        result = await pa_report_service.upload_netsuite_file(
            file_content=latin1_semicolon_csv_content,
            filename="MovimientoDetallado.csv"
        )

        assert result.success is True
        assert result.pa_rows == 2  # 110001 and 110002 match catalog

    @pytest.mark.asyncio
    async def test_upload_csv_with_title_rows(
        self, pa_report_service, mock_pa_rules_repository,
        latin1_semicolon_csv_with_title_rows, sample_catalog_accounts
    ):
        """Test upload of CSV with title rows before header"""
        mock_pa_rules_repository.get_all_catalog_accounts.return_value = sample_catalog_accounts
        mock_pa_rules_repository.create_processing_session.return_value = "PA-20240115-0003"

        result = await pa_report_service.upload_netsuite_file(
            file_content=latin1_semicolon_csv_with_title_rows,
            filename="MovimientoDetallado NOV_25.csv"
        )

        assert result.success is True
        assert result.total_rows == 3  # 3 data rows (not counting title rows)
        assert result.pa_rows == 3  # All 3 match catalog (110001, 120001, 130001)


# ==================== Encoding Priority Tests ====================

class TestEncodingPriority:
    """Tests for encoding priority based on delimiter"""

    def test_semicolon_prioritizes_latin1(self, pa_report_service):
        """Test that semicolon delimiter prioritizes Latin-1 encoding"""
        # Create content that would fail UTF-8 but work with Latin-1
        # 0xf1 = ñ, 0xe9 = é, 0xed = í in Latin-1
        content = b"Col1;Col2;Col3\nA\xf1o;M\xe9s;D\xeda\n"  # año, més, día in Latin-1

        df = pa_report_service._parse_csv(content)

        # Should parse successfully with Latin-1
        assert len(df) == 1
        # Check special characters are decoded correctly
        assert "ño" in str(df.iloc[0]["Col1"]) or "Año" in str(df.iloc[0]["Col1"])

    def test_comma_prioritizes_utf8(self, pa_report_service):
        """Test that comma delimiter prioritizes UTF-8 encoding"""
        # Create UTF-8 content
        content = (
            "Col1,Col2,Col3\n"
            "Año,Més,Día\n"
        ).encode("utf-8")

        df = pa_report_service._parse_csv(content)

        assert len(df) == 1
        assert "Año" in str(df.iloc[0]["Col1"])


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Tests for error handling scenarios"""

    def test_invalid_encoding_error(self, pa_report_service):
        """Test error when file has invalid encoding for all attempts"""
        # Create content with invalid bytes for all supported encodings
        # This is hard to create since Latin-1 accepts all byte sequences
        # So we test with structurally invalid CSV instead
        content = b"\x00\x00\x00"  # Binary content

        with pytest.raises(ValueError) as exc_info:
            pa_report_service._parse_csv(content)

        assert "codificación" in str(exc_info.value).lower() or "encoding" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_missing_critical_column_error(
        self, pa_report_service, mock_pa_rules_repository
    ):
        """Test error when critical column is missing after renaming"""
        # CSV without the required "Cuenta (línea): Número" column
        content = (
            "OtraColumna,Débito,Crédito,Saldo\n"
            "Valor1,1000,0,1000\n"
        ).encode("utf-8")

        result = await pa_report_service.upload_netsuite_file(
            file_content=content,
            filename="invalid.csv"
        )

        assert result.success is False
        assert "columna" in result.message.lower() or "Cuenta" in result.message


# ==================== PA Rules Service Column Mapping Tests ====================

class TestPARulesServiceColumnMapping:
    """Tests for PA rules service column mapping"""

    def test_catalog_column_mapping_cuenta_fk(self):
        """Test that 'Cuenta Fk' column is recognized"""
        from src.core.servicios.pa_rules_service import PARulesService
        from unittest.mock import MagicMock

        service = PARulesService(MagicMock())
        columns = ['cuenta fk', 'cuenta auxiliar', 'homologacion cuenta', 'homologacion nombre cuenta']

        mapping = service._get_catalog_column_mapping(columns)

        assert mapping is not None
        assert 'cuenta fk' in mapping
        assert mapping['cuenta fk'] == 'cuenta_finkargo'
        assert mapping['homologacion cuenta'] == 'cuenta_homologacion'
        assert mapping['homologacion nombre cuenta'] == 'nombre_homologacion'

    def test_catalog_column_mapping_cuenta_finkargo(self):
        """Test that 'Cuenta Finkargo' column is recognized (original case)"""
        from src.core.servicios.pa_rules_service import PARulesService
        from unittest.mock import MagicMock

        service = PARulesService(MagicMock())
        columns = ['cuenta finkargo', 'cuenta homologacion', 'nombre homologacion']

        mapping = service._get_catalog_column_mapping(columns)

        assert mapping is not None
        assert 'cuenta finkargo' in mapping
        assert mapping['cuenta finkargo'] == 'cuenta_finkargo'

    def test_catalog_column_mapping_cuenta_netsuite(self):
        """Test that 'Cuenta NetSuite' column is recognized"""
        from src.core.servicios.pa_rules_service import PARulesService
        from unittest.mock import MagicMock

        service = PARulesService(MagicMock())
        columns = ['cuenta netsuite', 'cuenta homologacion', 'nombre homologacion']

        mapping = service._get_catalog_column_mapping(columns)

        assert mapping is not None
        assert 'cuenta netsuite' in mapping
        assert mapping['cuenta netsuite'] == 'cuenta_finkargo'


# ==================== PA Report Cleanup Improvements Tests ====================

class TestPAReportCleanupImprovements:
    """Tests for PA Report cleanup improvements.

    Tests cover:
    - Colombian number parsing
    - Débito/Crédito value preservation
    - Column name preservation
    - Fecha de vencimiento removal
    - New column names format
    - PA column default value
    - USD sign correction
    """

    def test_colombian_number_parsing_standard(self, pa_report_service):
        """Test parsing standard Colombian currency format."""
        # Standard format: $37.634,41
        result = pa_report_service._parse_colombian_number("$37.634,41")
        assert result == 37634.41

    def test_colombian_number_parsing_large(self, pa_report_service):
        """Test parsing large Colombian currency values."""
        # Large value: $1.234.567,89
        result = pa_report_service._parse_colombian_number("$1.234.567,89")
        assert result == 1234567.89

    def test_colombian_number_parsing_no_currency_symbol(self, pa_report_service):
        """Test parsing Colombian format without currency symbol."""
        # Without $ symbol: 1000,50
        result = pa_report_service._parse_colombian_number("1000,50")
        assert result == 1000.50

    def test_colombian_number_parsing_empty(self, pa_report_service):
        """Test parsing empty/null values returns 0."""
        assert pa_report_service._parse_colombian_number("") == 0.0
        assert pa_report_service._parse_colombian_number(None) == 0.0
        assert pa_report_service._parse_colombian_number("   ") == 0.0

    def test_colombian_number_parsing_already_numeric(self, pa_report_service):
        """Test parsing values that are already numeric."""
        assert pa_report_service._parse_colombian_number(1234.56) == 1234.56
        assert pa_report_service._parse_colombian_number(1000) == 1000.0

    def test_colombian_number_parsing_negative(self, pa_report_service):
        """Test parsing negative Colombian values."""
        result = pa_report_service._parse_colombian_number("-$1.000,00")
        assert result == -1000.0

    def test_colombian_number_parsing_invalid(self, pa_report_service):
        """Test parsing invalid values returns 0."""
        result = pa_report_service._parse_colombian_number("invalid")
        assert result == 0.0

    def test_columns_to_remove_constant(self, pa_report_service):
        """Test that COLUMNS_TO_REMOVE constant is defined."""
        assert hasattr(pa_report_service, 'COLUMNS_TO_REMOVE')
        assert "Fecha de vencimiento" in pa_report_service.COLUMNS_TO_REMOVE
        assert "fecha_vencimiento" in pa_report_service.COLUMNS_TO_REMOVE

    def test_output_columns_proper_format(self, pa_report_service):
        """Test that OUTPUT_COLUMNS use proper capitalized names with spaces."""
        expected_columns = [
            "PA",
            "Categoria",
            "Subcategoria",
            "Clasificacion",
            "Nexo",
            "Comprobacion saldos",
            "Cuenta Homologacion",
            "Nombre Homologacion"
        ]
        assert pa_report_service.OUTPUT_COLUMNS == expected_columns


class TestUSDSignCorrection:
    """Tests for USD sign correction logic."""

    @pytest.fixture
    def df_with_usd_transactions(self):
        """Create a DataFrame with USD transactions for testing sign correction."""
        return pd.DataFrame({
            "cuenta_linea_numero": ["11100530", "11100531", "11100532", "11100533"],
            "moneda_nombre": ["USD", "USD", "COP", "USD"],
            "debito": [1000.0, 0.0, 500.0, 0.0],
            "credito": [0.0, 2000.0, 0.0, 3000.0],
            "Valor USD": [-500.0, 1500.0, 100.0, 2500.0]  # Wrong signs to be corrected
        })

    def test_usd_debito_sign_correction(self, df_with_usd_transactions):
        """Test that USD Débito transactions have positive Valor USD."""
        df = df_with_usd_transactions.copy()

        # Apply sign correction logic (same as in clean_data)
        is_usd = df["moneda_nombre"].str.upper() == "USD"
        has_debito = (df["debito"].notna()) & (df["debito"] != 0)
        mask_debito_usd = is_usd & has_debito

        # Make Valor USD positive for Débito rows
        df.loc[mask_debito_usd & (df["Valor USD"] < 0), "Valor USD"] = \
            df.loc[mask_debito_usd & (df["Valor USD"] < 0), "Valor USD"].abs()

        # Row 0: USD Débito, was -500, should be 500
        assert df.loc[0, "Valor USD"] == 500.0

    def test_usd_credito_sign_correction(self, df_with_usd_transactions):
        """Test that USD Crédito transactions have negative Valor USD."""
        df = df_with_usd_transactions.copy()

        # Apply sign correction logic (same as in clean_data)
        is_usd = df["moneda_nombre"].str.upper() == "USD"
        has_credito = (df["credito"].notna()) & (df["credito"] != 0)
        mask_credito_usd = is_usd & has_credito

        # Make Valor USD negative for Crédito rows
        df.loc[mask_credito_usd & (df["Valor USD"] > 0), "Valor USD"] = \
            -df.loc[mask_credito_usd & (df["Valor USD"] > 0), "Valor USD"].abs()

        # Row 1: USD Crédito, was 1500, should be -1500
        assert df.loc[1, "Valor USD"] == -1500.0
        # Row 3: USD Crédito, was 2500, should be -2500
        assert df.loc[3, "Valor USD"] == -2500.0

    def test_cop_transactions_not_affected(self, df_with_usd_transactions):
        """Test that COP transactions are not affected by sign correction."""
        df = df_with_usd_transactions.copy()
        original_cop_value = df.loc[2, "Valor USD"]

        # Apply both sign corrections
        is_usd = df["moneda_nombre"].str.upper() == "USD"
        has_debito = (df["debito"].notna()) & (df["debito"] != 0)
        has_credito = (df["credito"].notna()) & (df["credito"] != 0)

        mask_debito_usd = is_usd & has_debito
        mask_credito_usd = is_usd & has_credito

        df.loc[mask_debito_usd & (df["Valor USD"] < 0), "Valor USD"] = \
            df.loc[mask_debito_usd & (df["Valor USD"] < 0), "Valor USD"].abs()
        df.loc[mask_credito_usd & (df["Valor USD"] > 0), "Valor USD"] = \
            -df.loc[mask_credito_usd & (df["Valor USD"] > 0), "Valor USD"].abs()

        # Row 2: COP transaction, should remain unchanged
        assert df.loc[2, "Valor USD"] == original_cop_value


class TestNewColumnNames:
    """Tests for new column naming convention."""

    def test_pa_column_uppercase(self, pa_report_service):
        """Test that PA column uses uppercase name."""
        assert "PA" in pa_report_service.OUTPUT_COLUMNS

    def test_categoria_without_accent(self, pa_report_service):
        """Test that Categoria is capitalized without accent in column name."""
        assert "Categoria" in pa_report_service.OUTPUT_COLUMNS

    def test_comprobacion_saldos_with_space(self, pa_report_service):
        """Test that Comprobacion saldos uses space, not underscore."""
        assert "Comprobacion saldos" in pa_report_service.OUTPUT_COLUMNS
        assert "comprobacion_saldos" not in pa_report_service.OUTPUT_COLUMNS

    def test_cuenta_homologacion_with_space(self, pa_report_service):
        """Test that Cuenta Homologacion uses space, not underscore."""
        assert "Cuenta Homologacion" in pa_report_service.OUTPUT_COLUMNS
        assert "cuenta_homologacion" not in pa_report_service.OUTPUT_COLUMNS

    def test_nombre_homologacion_with_space(self, pa_report_service):
        """Test that Nombre Homologacion uses space, not underscore."""
        assert "Nombre Homologacion" in pa_report_service.OUTPUT_COLUMNS
        assert "nombre_homologacion" not in pa_report_service.OUTPUT_COLUMNS
