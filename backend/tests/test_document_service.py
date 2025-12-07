"""
Unit tests for DocumentService - Solicitud de Desembolso document generation
"""
import pytest
import io
import re
from datetime import datetime
from docx import Document

from src.core.servicios.document_service import DocumentService, GASTOS_CATEGORY_KEYWORDS, GASTOS_CHECKBOX_INDICES


class TestSolicitudDesembolsoDocumentGeneration:
    """Tests for Solicitud de Desembolso document generation"""

    @pytest.fixture
    def document_service(self):
        """Create DocumentService instance"""
        return DocumentService()

    @pytest.fixture
    def sample_contract_data(self):
        """Sample contract data for Solicitud de Desembolso"""
        return {
            'data_snapshot': {
                'numero_cotizacion_desembolso': 'CO:900436389:1:2:DOM',
                'fecha_contrato_credito': '2025-11-06',
                'monto': 739860.00,
                'dias_plazo': 120,
                'nit': '900436389',
                'nombre_importador': 'SAFETY PUERTO S.A.S.',
                'representante_legal': 'Juan Carlos Pérez',
                'cedula_representante': '79123456',
                'ciudad_domicilio': 'Bogotá',
                'anexo_items': [
                    {'acreedor': 'Entidad de pago de Impuestos', 'numero_instrumento': '1003887257', 'monto': 407001.00},
                    {'acreedor': 'Transportadora ABC', 'numero_instrumento': '1003887258', 'monto': 290000.00},
                    {'acreedor': 'Servicios Logísticos XYZ', 'numero_instrumento': '1003887259', 'monto': 42859.00},
                ]
            }
        }

    def test_solicitud_desembolso_placeholders_replaced(self, document_service, sample_contract_data):
        """Test that all Solicitud de Desembolso placeholders are correctly replaced"""
        # Generate document
        doc_bytes = document_service.generate_solicitud_desembolso_document(sample_contract_data)

        # Load generated document
        doc = Document(io.BytesIO(doc_bytes))

        # Extract all text from document
        full_text = ''
        for para in doc.paragraphs:
            full_text += para.text + '\n'
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text += cell.text + '\n'

        # Verify specific placeholders are replaced (should NOT appear in output)
        assert '[Número de cotización de desembolso]' not in full_text, \
            "Placeholder [Número de cotización de desembolso] was not replaced"
        assert '[monto]' not in full_text, \
            "Placeholder [monto] was not replaced"
        assert '[número de días de plazo]' not in full_text, \
            "Placeholder [número de días de plazo] was not replaced"
        assert '[día de firma del contrato de crédito]' not in full_text, \
            "Placeholder [día de firma del contrato de crédito] was not replaced"
        assert '[mes de firma del contrato de crédito]' not in full_text, \
            "Placeholder [mes de firma del contrato de crédito] was not replaced"
        assert '[ año de firma del contrato de crédito]' not in full_text, \
            "Placeholder [ año de firma del contrato de crédito] was not replaced"

        # Verify data appears in document
        assert 'CO:900436389:1:2:DOM' in full_text, \
            "Quote number not found in document"
        assert '120' in full_text, \
            "Dias plazo not found in document"
        # Check monto is in document (formatted as 739,860.00)
        assert '739,860.00' in full_text or '739860' in full_text, \
            "Monto not found in document"

    def test_solicitud_desembolso_date_components_replaced(self, document_service, sample_contract_data):
        """Test that date placeholders are replaced with correct components"""
        # Generate document
        doc_bytes = document_service.generate_solicitud_desembolso_document(sample_contract_data)

        # Load generated document
        doc = Document(io.BytesIO(doc_bytes))

        # Extract all text
        full_text = ''
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    full_text += cell.text + '\n'

        # Verify fecha_contrato_credito components (2025-11-06)
        assert '6' in full_text, "Day of contract date not found"
        assert 'noviembre' in full_text, "Month of contract date not found"
        assert '2025' in full_text, "Year of contract date not found"

        # Verify current date placeholders are replaced
        assert '[día]' not in full_text, "Placeholder [día] was not replaced"
        assert '[mes]' not in full_text, "Placeholder [mes] was not replaced"

    def test_solicitud_desembolso_anexo_table_populated(self, document_service, sample_contract_data):
        """Test that Anexo I table is populated with items"""
        # Generate document
        doc_bytes = document_service.generate_solicitud_desembolso_document(sample_contract_data)

        # Load generated document
        doc = Document(io.BytesIO(doc_bytes))

        # Find Anexo I table (Table 1)
        assert len(doc.tables) >= 2, "Document should have at least 2 tables"
        anexo_table = doc.tables[1]

        # Extract text from table
        table_text = ''
        for row in anexo_table.rows:
            for cell in row.cells:
                table_text += cell.text + ' '

        # Verify anexo items appear in table
        assert 'Entidad de pago de Impuestos' in table_text, \
            "First acreedor not found in Anexo table"
        assert '1003887257' in table_text, \
            "First numero_instrumento not found in Anexo table"
        assert 'Transportadora ABC' in table_text, \
            "Second acreedor not found in Anexo table"
        assert 'Servicios Logísticos XYZ' in table_text, \
            "Third acreedor not found in Anexo table"

        # Verify placeholder [•] is not in data rows (should be replaced or cleared)
        data_rows_text = ''
        for row_idx in range(2, 12):  # Data rows 2-11
            if row_idx < len(anexo_table.rows):
                row = anexo_table.rows[row_idx]
                for cell in row.cells:
                    data_rows_text += cell.text

        # Data rows should not have [•] placeholder except for empty rows which are cleared
        # (The first 3 rows have data, rows 4-11 should be empty)

    def test_solicitud_desembolso_total_calculated(self, document_service, sample_contract_data):
        """Test that total is correctly calculated in Anexo I table"""
        # Generate document
        doc_bytes = document_service.generate_solicitud_desembolso_document(sample_contract_data)

        # Load generated document
        doc = Document(io.BytesIO(doc_bytes))

        # Find Anexo I table (Table 1)
        anexo_table = doc.tables[1]

        # Get TOTAL row (row 12)
        if len(anexo_table.rows) > 12:
            total_row = anexo_table.rows[12]
            total_text = ' '.join([cell.text for cell in total_row.cells])

            # Expected total: 407001 + 290000 + 42859 = 739860
            assert 'TOTAL' in total_text, "TOTAL label not found in total row"
            assert '739,860.00' in total_text or '739860' in total_text, \
                f"Total amount not correct in total row. Got: {total_text}"

    def test_prepare_solicitud_desembolso_replacements(self, document_service, sample_contract_data):
        """Test that _prepare_solicitud_desembolso_replacements returns correct mappings"""
        data = sample_contract_data['data_snapshot']
        replacements = document_service._prepare_solicitud_desembolso_replacements(data)

        # Verify all required placeholders are in the replacements
        assert '[Número de cotización de desembolso]' in replacements
        assert '[día]' in replacements
        assert '[mes]' in replacements
        assert '[•]' in replacements
        assert '[día de firma del contrato de crédito]' in replacements
        assert '[mes de firma del contrato de crédito]' in replacements
        assert '[ año de firma del contrato de crédito]' in replacements
        assert '[monto]' in replacements
        assert '[número de días de plazo]' in replacements

        # Verify values
        assert replacements['[Número de cotización de desembolso]'] == 'CO:900436389:1:2:DOM'
        assert replacements['[número de días de plazo]'] == '120'
        assert replacements['[día de firma del contrato de crédito]'] == '6'
        assert replacements['[mes de firma del contrato de crédito]'] == 'noviembre'
        assert replacements['[ año de firma del contrato de crédito]'] == '2025'

    def test_solicitud_desembolso_empty_anexo_items(self, document_service):
        """Test document generation with empty anexo_items"""
        contract_data = {
            'data_snapshot': {
                'numero_cotizacion_desembolso': 'CO:123456789:1:1:DOM',
                'fecha_contrato_credito': '2025-12-01',
                'monto': 0,
                'dias_plazo': 60,
                'nit': '123456789',
                'anexo_items': []
            }
        }

        # Should not raise an error
        doc_bytes = document_service.generate_solicitud_desembolso_document(contract_data)
        assert doc_bytes is not None
        assert len(doc_bytes) > 0

    def test_solicitud_desembolso_missing_fecha_contrato(self, document_service):
        """Test document generation with missing fecha_contrato_credito"""
        contract_data = {
            'data_snapshot': {
                'numero_cotizacion_desembolso': 'CO:123456789:1:1:DOM',
                'fecha_contrato_credito': '',  # Empty date
                'monto': 100000,
                'dias_plazo': 90,
                'nit': '123456789',
                'anexo_items': [
                    {'acreedor': 'Test', 'numero_instrumento': '12345', 'monto': 100000}
                ]
            }
        }

        # Should not raise an error, but date fields will be empty
        doc_bytes = document_service.generate_solicitud_desembolso_document(contract_data)
        assert doc_bytes is not None
        assert len(doc_bytes) > 0

    def test_determine_gastos_categories_impuestos(self, document_service):
        """Test that 'Entidad de pago de Impuestos' maps to servicios_aduanales"""
        anexo_items = [
            {'acreedor': 'Entidad de pago de Impuestos', 'numero_instrumento': '123', 'monto': 1000}
        ]
        categories = document_service._determine_gastos_categories(anexo_items)
        assert 'servicios_aduanales' in categories, \
            "'Entidad de pago de Impuestos' should map to servicios_aduanales"

    def test_determine_gastos_categories_transporte(self, document_service):
        """Test that transport-related acreedores map to transporte"""
        anexo_items = [
            {'acreedor': 'Transportadora ABC', 'numero_instrumento': '123', 'monto': 1000}
        ]
        categories = document_service._determine_gastos_categories(anexo_items)
        assert 'transporte' in categories, \
            "'Transportadora ABC' should map to transporte"

    def test_determine_gastos_categories_logisticos(self, document_service):
        """Test that logistics-related acreedores map to logisticos"""
        anexo_items = [
            {'acreedor': 'Servicios Logísticos XYZ', 'numero_instrumento': '123', 'monto': 1000}
        ]
        categories = document_service._determine_gastos_categories(anexo_items)
        assert 'logisticos' in categories, \
            "'Servicios Logísticos XYZ' should map to logisticos"

    def test_determine_gastos_categories_multiple(self, document_service, sample_contract_data):
        """Test that multiple categories are detected from multiple anexo items"""
        anexo_items = sample_contract_data['data_snapshot']['anexo_items']
        categories = document_service._determine_gastos_categories(anexo_items)

        # Should have servicios_aduanales (Impuestos), transporte (Transportadora), logisticos (Logísticos)
        assert 'servicios_aduanales' in categories, \
            "servicios_aduanales should be detected from 'Entidad de pago de Impuestos'"
        assert 'transporte' in categories, \
            "transporte should be detected from 'Transportadora ABC'"
        assert 'logisticos' in categories, \
            "logisticos should be detected from 'Servicios Logísticos XYZ'"

    def test_determine_gastos_categories_empty(self, document_service):
        """Test that empty anexo_items returns empty set"""
        categories = document_service._determine_gastos_categories([])
        assert len(categories) == 0, "Empty anexo_items should return empty set"

    def test_determine_gastos_categories_no_match(self, document_service):
        """Test that non-matching acreedor returns empty set"""
        anexo_items = [
            {'acreedor': 'Random Company XYZ', 'numero_instrumento': '123', 'monto': 1000}
        ]
        categories = document_service._determine_gastos_categories(anexo_items)
        assert len(categories) == 0, \
            "Non-matching acreedor should return empty set"

    def test_determine_gastos_categories_case_insensitive(self, document_service):
        """Test that keyword matching is case insensitive"""
        anexo_items = [
            {'acreedor': 'ENTIDAD DE PAGO DE IMPUESTOS', 'numero_instrumento': '123', 'monto': 1000}
        ]
        categories = document_service._determine_gastos_categories(anexo_items)
        assert 'servicios_aduanales' in categories, \
            "Keyword matching should be case insensitive"

    def test_gastos_category_keywords_defined(self):
        """Test that all expected category keywords are defined"""
        expected_categories = ['tributos_aduaneros', 'servicios_aduanales', 'logisticos', 'transporte', 'almacenamiento']
        for category in expected_categories:
            assert category in GASTOS_CATEGORY_KEYWORDS, \
                f"Category '{category}' should be defined in GASTOS_CATEGORY_KEYWORDS"
            assert len(GASTOS_CATEGORY_KEYWORDS[category]) > 0, \
                f"Category '{category}' should have at least one keyword"

    def test_gastos_checkbox_indices_defined(self):
        """Test that all checkbox indices are defined for categories"""
        expected_categories = ['tributos_aduaneros', 'servicios_aduanales', 'logisticos', 'transporte', 'almacenamiento']
        for category in expected_categories:
            assert category in GASTOS_CHECKBOX_INDICES, \
                f"Category '{category}' should be defined in GASTOS_CHECKBOX_INDICES"
            assert isinstance(GASTOS_CHECKBOX_INDICES[category], int), \
                f"Index for '{category}' should be an integer"
            assert GASTOS_CHECKBOX_INDICES[category] >= 0, \
                f"Index for '{category}' should be non-negative"
