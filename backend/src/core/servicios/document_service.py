"""
Document Generation Service for Legal Contracts
Handles Word template population and PDF conversion
"""
from docx import Document
from datetime import datetime
from typing import Dict, Any
import os
import tempfile
from pathlib import Path
import logging
from supabase import Client
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# DIAN Payment Constants
DIAN_RAZON_SOCIAL = "DIAN"
DIAN_NIT = "800.197.268-4"
DIAN_NA_MESSAGE = "N/A – En la medida en que el pago del instrumento de pago se deberá realizar por el Mandato usando el link de pago enviado por el Mandante."
DIAN_KEYWORDS = ["DIAN", "Direccion de Impuestos", "Aduanas Nacionales", "Entidad de pago de Impuestos"]
# Legacy constant for backwards compatibility
DIAN_WORDING = DIAN_RAZON_SOCIAL

# Keyword mappings for Gastos Nacionales de Importación checkboxes
# Maps category keys to lists of keywords that indicate that category
GASTOS_CATEGORY_KEYWORDS = {
    'tributos_aduaneros': ['tributo', 'arancel', 'dian', 'aduanero', 'aduana'],
    'servicios_aduanales': ['impuesto', 'entidad de pago', 'pago de impuestos', 'servicio aduanal'],
    'logisticos': ['logístic', 'logistic', 'operador logístico'],
    'transporte': ['transporte', 'transportador', 'flete', 'envío', 'envio', 'carga'],
    'almacenamiento': ['almacén', 'almacen', 'almacenamiento', 'bodega', 'storage', 'depósito', 'deposito'],
}

# Index mapping for checkbox cells in nested table (Table 0, Row 3, Cell 0, Nested Table Row 0)
GASTOS_CHECKBOX_INDICES = {
    'tributos_aduaneros': 0,
    'servicios_aduanales': 1,
    'logisticos': 2,
    'transporte': 3,
    'almacenamiento': 4,
}


class DocumentService:
    """Service for generating contract documents from templates"""

    def __init__(self, template_dir: str = None, supabase_client: Client = None):
        """
        Initialize DocumentService

        Args:
            template_dir: Directory containing Word templates
            supabase_client: Supabase client for storage operations
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates"
        self.template_dir = Path(template_dir)
        self.supabase = supabase_client

    def generate_contract_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL - GM - Activos.docx"
    ) -> bytes:
        """
        Generate contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        # Route to appropriate method based on contract type
        # Enhanced logging and defensive handling for contract_type
        contract_type = contract_data.get('contract_type')
        logger.debug(f"Full contract_data keys: {list(contract_data.keys())}")
        logger.debug(f"Raw contract_type value: {repr(contract_type)}")

        # Defensive handling: fall back to data_snapshot if top-level is None/empty
        if not contract_type:
            logger.warning("contract_type is None or empty at top level, checking data_snapshot")
            data_snapshot = contract_data.get('data_snapshot', {})
            contract_type = data_snapshot.get('contract_type', 'activos')
            logger.info(f"Using contract_type from data_snapshot: {contract_type}")

        logger.info(f"Generating document for contract type: {contract_type}")

        if contract_type == 'otrosi':
            return self.generate_otrosi_document(contract_data)
        elif contract_type == 'inventario_bodega':
            return self.generate_inventario_bodega_document(contract_data)
        elif contract_type == 'pl_co_credito_no_aval':
            return self.generate_paga_local_credito_no_aval_document(contract_data)
        elif contract_type == 'pl_co_mandato_no_aval':
            return self.generate_paga_local_mandato_no_aval_document(contract_data)
        elif contract_type == 'pl_co_mandato_pj':
            # Mandato PJ uses the same template as Mandato No Aval
            return self.generate_paga_local_mandato_no_aval_document(contract_data)
        elif contract_type == 'pl_co_mandato_pn':
            # Mandato PN uses the same template as Mandato No Aval
            return self.generate_paga_local_mandato_no_aval_document(contract_data)
        elif contract_type == 'pl_co_credito_aval_pj':
            return self.generate_paga_local_credito_aval_pj_document(contract_data)
        elif contract_type == 'pl_co_credito_aval_pn':
            return self.generate_paga_local_credito_aval_pn_document(contract_data)
        elif contract_type == 'pl_co_solicitud_desembolso':
            return self.generate_solicitud_desembolso_document(contract_data)
        elif contract_type == 'pl_co_mandato_im':
            return self.generate_instruccion_mandato_document(contract_data)
        elif contract_type == 'pl_co_dian_mandato_im':
            return self.generate_dian_mandato_document(contract_data)
        else:
            return self.generate_activos_document(contract_data, template_name)

    def generate_activos_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL - GM - Activos.docx"
    ) -> bytes:
        """
        Generate Activos contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Prepare replacement data
        replacements = self._prepare_replacements(contract_data)

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, replacements)

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, replacements)

        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name

        # Save document
        doc.save(tmp_path)

        # Read bytes
        with open(tmp_path, 'rb') as f:
            content = f.read()

        # Clean up
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Ignore cleanup errors on Windows

        return content

    def generate_otrosi_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL - K Marco - Otrosí No. 1.docx"
    ) -> bytes:
        """
        Generate Otrosí No. 1 contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Otrosí template not found: {template_path}")

        logger.info(f"Loading Otrosí template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Prepare Otrosí-specific replacement data
        replacements = self._prepare_otrosi_replacements(contract_data)

        logger.info(f"Replacing {len(replacements)} placeholders in Otrosí template")

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, replacements)

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, replacements)

        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name

        # Save document
        doc.save(tmp_path)

        # Read bytes
        with open(tmp_path, 'rb') as f:
            content = f.read()

        # Clean up
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Ignore cleanup errors on Windows

        logger.info("Otrosí document generated successfully")

        return content

    def generate_paga_local_credito_no_aval_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL paga local - Fin. COP - K° Crédito (No Aval).docx"
    ) -> bytes:
        """
        Generate Paga Local Colombia K° Crédito (No Aval) contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Paga Local Crédito (No Aval) template not found: {template_path}")

        logger.info(f"Loading Paga Local Crédito (No Aval) template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Prepare replacement data - use standard replacements with Paga Local specific mappings
        replacements = self._prepare_paga_local_replacements(contract_data)

        logger.info(f"Replacing {len(replacements)} placeholders in Paga Local Crédito (No Aval) template")

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, replacements)

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, replacements)

        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name

        # Save document
        doc.save(tmp_path)

        # Read bytes
        with open(tmp_path, 'rb') as f:
            content = f.read()

        # Clean up
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Ignore cleanup errors on Windows

        logger.info("Paga Local Crédito (No Aval) document generated successfully")

        return content

    def generate_paga_local_mandato_no_aval_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL paga local - Fin. COP - K° Mandato.docx"
    ) -> bytes:
        """
        Generate Paga Local Colombia K° Mandato (No Aval) contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Paga Local Mandato (No Aval) template not found: {template_path}")

        logger.info(f"Loading Paga Local Mandato (No Aval) template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Prepare replacement data - use standard replacements with Paga Local specific mappings
        replacements = self._prepare_paga_local_replacements(contract_data)

        logger.info(f"Replacing {len(replacements)} placeholders in Paga Local Mandato (No Aval) template")

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, replacements)

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, replacements)

        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name

        # Save document
        doc.save(tmp_path)

        # Read bytes
        with open(tmp_path, 'rb') as f:
            content = f.read()

        # Clean up
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Ignore cleanup errors on Windows

        logger.info("Paga Local Mandato (No Aval) document generated successfully")

        return content

    def generate_paga_local_credito_aval_pj_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL paga local - Fin. COP - K° Crédito (Aval PJ).docx"
    ) -> bytes:
        """
        Generate Paga Local Colombia K° Crédito (Aval PJ) contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Paga Local Crédito (Aval PJ) template not found: {template_path}")

        logger.info(f"Loading Paga Local Crédito (Aval PJ) template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Prepare replacement data - use standard replacements with Paga Local specific mappings
        replacements = self._prepare_paga_local_replacements(contract_data)

        logger.info(f"Replacing {len(replacements)} placeholders in Paga Local Crédito (Aval PJ) template")

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, replacements)

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, replacements)

        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name

        # Save document
        doc.save(tmp_path)

        # Read bytes
        with open(tmp_path, 'rb') as f:
            content = f.read()

        # Clean up
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Ignore cleanup errors on Windows

        logger.info("Paga Local Crédito (Aval PJ) document generated successfully")

        return content

    def generate_paga_local_credito_aval_pn_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx"
    ) -> bytes:
        """
        Generate Paga Local Colombia K° Crédito (Aval PN) contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Paga Local Crédito (Aval PN) template not found: {template_path}")

        logger.info(f"Loading Paga Local Crédito (Aval PN) template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Prepare replacement data - use standard replacements with Paga Local specific mappings
        replacements = self._prepare_paga_local_replacements(contract_data)

        logger.info(f"Replacing {len(replacements)} placeholders in Paga Local Crédito (Aval PN) template")

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, replacements)

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, replacements)

        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name

        # Save document
        doc.save(tmp_path)

        # Read bytes
        with open(tmp_path, 'rb') as f:
            content = f.read()

        # Clean up
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Ignore cleanup errors on Windows

        logger.info("Paga Local Crédito (Aval PN) document generated successfully")

        return content

    def generate_inventario_bodega_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL - GM - Inventario Bodega de 3ro.docx"
    ) -> bytes:
        """
        Generate Inventario Bodega de 3ro contract document from template and data

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the Word template file

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Inventario Bodega template not found: {template_path}")

        logger.info(f"Loading Inventario Bodega template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Prepare replacement data with custodian fields
        replacements = self._prepare_inventario_bodega_replacements(contract_data)

        logger.info(f"Replacing {len(replacements)} placeholders in Inventario Bodega template")

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            self._replace_in_paragraph(para, replacements)

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, replacements)

        # Save to temporary file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name

        # Save document
        doc.save(tmp_path)

        # Read bytes
        with open(tmp_path, 'rb') as f:
            content = f.read()

        # Clean up
        try:
            os.unlink(tmp_path)
        except Exception:
            pass  # Ignore cleanup errors on Windows

        logger.info("Inventario Bodega document generated successfully")

        return content

    def generate_contract_pdf_from_template(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL - GM - Activos.pdf"
    ) -> bytes:
        """
        Generate contract PDF directly from PDF template (preserves formatting and numbering)

        Args:
            contract_data: Dictionary containing all contract data including client info
            template_name: Name of the PDF template file

        Returns:
            bytes: Generated PDF file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"PDF template not found: {template_path}")

        logger.info(f"Loading PDF template from: {template_path}")

        # Open the PDF template
        pdf_document = fitz.open(str(template_path))

        # Prepare replacement data
        replacements = self._prepare_replacements(contract_data)

        logger.info(f"Replacing {len(replacements)} placeholders in PDF")

        # Log sample replacements for debugging
        sample_replacements = list(replacements.items())[:3]
        logger.info(f"Sample replacements: {sample_replacements}")

        # Track total replacements made
        total_replacements = 0

        # Iterate through all pages
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # Get all text on the page for debugging
            page_text = page.get_text()
            logger.debug(f"Page {page_num + 1} contains {len(page_text)} characters")

            # Replace each placeholder using text block replacement
            for placeholder, value in replacements.items():
                # Search for all instances of the placeholder
                text_instances = page.search_for(placeholder)

                if text_instances:
                    logger.info(f"Found {len(text_instances)} instances of '{placeholder}' = '{value}' on page {page_num + 1}")
                    total_replacements += len(text_instances)

                    # Replace each instance
                    for inst in text_instances:
                        # Get the rectangle coordinates of the placeholder
                        placeholder_rect = fitz.Rect(inst)

                        # Calculate the width needed for the replacement text
                        # Approximate: 1 character = 5.4 points at fontsize 9
                        fontsize = 9
                        char_width = fontsize * 0.6  # Approximate width per character
                        text_width = len(value) * char_width

                        # Create a larger rectangle to cover both placeholder and replacement
                        # Use the maximum of placeholder width or text width, plus some padding
                        cover_width = max(placeholder_rect.width, text_width) + 20  # Add 20 points padding

                        cover_rect = fitz.Rect(
                            placeholder_rect.x0,
                            placeholder_rect.y0,
                            placeholder_rect.x0 + cover_width,
                            placeholder_rect.y1
                        )

                        # Draw white rectangle to cover the area
                        page.draw_rect(cover_rect, color=(1, 1, 1), fill=(1, 1, 1))

                        # Insert the replacement text at the original position
                        page.insert_text(
                            (placeholder_rect.x0, placeholder_rect.y1 - 2),  # Position at bottom-left
                            value,
                            fontsize=fontsize,
                            color=(0, 0, 0)
                        )

        logger.info(f"Total replacements made: {total_replacements}")

        # Save to bytes
        pdf_bytes = pdf_document.tobytes()
        pdf_document.close()

        logger.info("PDF generation completed successfully")

        return pdf_bytes

    def _prepare_replacements(self, contract_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare replacement dictionary from contract data

        Args:
            contract_data: Raw contract data from database

        Returns:
            Dictionary mapping placeholders to replacement values
        """
        # Helper function to safely get string values
        def safe_get(d: dict, key: str, default: str = '') -> str:
            """Get value from dict and ensure it's a string"""
            value = d.get(key, default)
            return str(value) if value is not None else default

        # Extract data_snapshot
        snapshot = contract_data.get('data_snapshot', {})

        # Get current date info
        now = datetime.now()
        generation_date = contract_data.get('generated_at', now)
        if isinstance(generation_date, str):
            generation_date = datetime.fromisoformat(generation_date.replace('Z', '+00:00'))

        # Format currency
        cupo_plataforma = float(snapshot.get('cupo_plataforma', 0))
        cupo_formatted = f"${cupo_plataforma:,.0f}".replace(',', '.')
        cupo_letras = self._number_to_words_spanish(cupo_plataforma)

        # Build replacements dictionary
        replacements = {
            # Date fields
            '[día]': str(generation_date.day),
            '[mes]': self._get_month_name_spanish(generation_date.month),
            '[•]': str(generation_date.year)[-1],  # Last digit of year for 202[•] format

            # Client information
            '[NOMBRE DEL CLIENTE]': safe_get(snapshot, 'nombre_importador'),
            '[NIT]': safe_get(snapshot, 'nit'),

            # Legal representative information
            '[Nombre del representante legal]': safe_get(snapshot, 'representante_legal'),
            '[nombre del representante legal]': safe_get(snapshot, 'representante_legal'),
            '[tipo de identificación]': safe_get(snapshot, 'tipo_identificacion_representante', 'CC'),
            '[identificación RL]': safe_get(snapshot, 'cedula_representante'),

            # Location
            '[nombre de la ciudad]': safe_get(snapshot, 'ciudad_domicilio'),
            '[Domicilio en que el Importador adelanta sus actividades comerciales]':
                safe_get(snapshot, 'direccion_comercial') or safe_get(snapshot, 'ciudad_domicilio'),

            # Financial information
            '[valor Cupo de Operaciones en números]': cupo_formatted,
            '[valor Cupo de Operaciones en letras]': cupo_letras,
            '[valor en números]': cupo_formatted,
            '[valor en letras]': cupo_letras,

            # Contract information
            '[nombre del contrato marco]': safe_get(snapshot, 'nombre_contrato_marco', 'Compra de Cartera'),

            # KAM Contact information
            '[nombre del KAM]': safe_get(snapshot, 'kam_nombre', 'Key Account Manager'),
            '[KAM e-mail]': safe_get(snapshot, 'kam_email', 'kam@finkargo.com'),

            # Recipient Contact information
            '[nombre del destinatario]': safe_get(snapshot, 'destinatario_nombre', 'Departamento Legal'),
            '[destinatario e-mail]': safe_get(snapshot, 'destinatario_email', 'legal@finkargo.com'),

            # Document ID
            '[sic]': safe_get(contract_data, 'contract_id'),
        }

        return replacements

    def _prepare_otrosi_replacements(self, contract_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare replacement dictionary for Otrosí template from contract data
        Otrosí templates use similar placeholders to Activos templates

        Args:
            contract_data: Raw contract data from database

        Returns:
            Dictionary mapping placeholders to replacement values
        """
        # Helper function to safely get string values
        def safe_get(d: dict, key: str, default: str = '') -> str:
            """Get value from dict and ensure it's a string"""
            value = d.get(key, default)
            return str(value) if value is not None else default

        # Extract data_snapshot
        snapshot = contract_data.get('data_snapshot', {})

        # Get current date info
        now = datetime.now()
        generation_date = contract_data.get('generated_at', now)
        if isinstance(generation_date, str):
            generation_date = datetime.fromisoformat(generation_date.replace('Z', '+00:00'))

        # Format currency
        cupo_plataforma = float(snapshot.get('cupo_plataforma', 0))
        cupo_formatted = f"${cupo_plataforma:,.0f}".replace(',', '.')
        cupo_letras = self._number_to_words_spanish(cupo_plataforma)

        # Build replacements dictionary (Otrosí uses same placeholders as Activos)
        replacements = {
            # Date fields
            '[día]': str(generation_date.day),
            '[mes]': self._get_month_name_spanish(generation_date.month),
            '[•]': str(generation_date.year)[-1],  # Last digit of year for 202[•] format

            # Client information
            '[NOMBRE DEL CLIENTE]': safe_get(snapshot, 'nombre_importador'),
            '[NIT]': safe_get(snapshot, 'nit'),

            # Legal representative information
            '[Nombre del representante legal]': safe_get(snapshot, 'representante_legal'),
            '[nombre del representante legal]': safe_get(snapshot, 'representante_legal'),
            '[tipo de identificación]': safe_get(snapshot, 'tipo_identificacion_representante', 'CC'),
            '[identificación RL]': safe_get(snapshot, 'cedula_representante'),

            # Location
            '[nombre de la ciudad]': safe_get(snapshot, 'ciudad_domicilio'),
            '[Domicilio en que el Importador adelanta sus actividades comerciales]':
                safe_get(snapshot, 'direccion_comercial') or safe_get(snapshot, 'ciudad_domicilio'),

            # Financial information
            '[valor Cupo de Operaciones en números]': cupo_formatted,
            '[valor Cupo de Operaciones en letras]': cupo_letras,
            '[valor en números]': cupo_formatted,
            '[valor en letras]': cupo_letras,

            # Contract information
            '[nombre del contrato marco]': safe_get(snapshot, 'nombre_contrato_marco', 'Compra de Cartera'),

            # KAM Contact information
            '[nombre del KAM]': safe_get(snapshot, 'kam_nombre', 'Key Account Manager'),
            '[KAM e-mail]': safe_get(snapshot, 'kam_email', 'kam@finkargo.com'),

            # Recipient Contact information
            '[nombre del destinatario]': safe_get(snapshot, 'destinatario_nombre', 'Departamento Legal'),
            '[destinatario e-mail]': safe_get(snapshot, 'destinatario_email', 'legal@finkargo.com'),

            # Document ID
            '[sic]': safe_get(contract_data, 'contract_id'),
        }

        logger.debug(f"Prepared {len(replacements)} replacements for Otrosí template")

        return replacements

    def _prepare_inventario_bodega_replacements(self, contract_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare replacement dictionary for Inventario Bodega template from contract data
        Includes both client data and custodian operator data from RUT

        Args:
            contract_data: Raw contract data from database

        Returns:
            Dictionary mapping placeholders to replacement values
        """
        # Helper function to safely get string values
        def safe_get(d: dict, key: str, default: str = '') -> str:
            """Get value from dict and ensure it's a string"""
            value = d.get(key, default)
            return str(value) if value is not None else default

        # Start with base replacements (client data)
        replacements = self._prepare_replacements(contract_data)

        # Extract data_snapshot
        snapshot = contract_data.get('data_snapshot', {})

        # Add custodian fields from RUT data
        custodian_replacements = {
            '[NOMBRE DEL OPERADOR CUSTODIO]': safe_get(snapshot, 'nombre_operador_custodio'),
            '[nombre de la ciudad de domicilio del Operador Custodio]': safe_get(snapshot, 'ciudad_domicilio_custodio'),
            '[NIT Operador Custodio]': safe_get(snapshot, 'nit_operador_custodio'),
            '[nombre del representante legal del Operador Custodio]': safe_get(snapshot, 'nombre_representante_legal_custodio'),
            '[e-mail del operador custodio]': safe_get(snapshot, 'email_operador_custodio'),
            '[CC representante legal del Operador Custodio]': safe_get(snapshot, 'cc_representante_legal_custodio'),
            '[id RL del Operador Custodio]': safe_get(snapshot, 'cc_representante_legal_custodio'),  # Same as CC field
            '[tipo de id RL Operador Custodio]': safe_get(snapshot, 'tipo_identificacion_representante_legal_custodio'),
        }

        # Merge custodian fields into replacements
        replacements.update(custodian_replacements)

        logger.debug(f"Prepared {len(replacements)} replacements for Inventario Bodega template (including {len(custodian_replacements)} custodian field placeholders)")

        return replacements

    def _prepare_paga_local_replacements(self, contract_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare replacement dictionary for Paga Local templates from contract data
        Handles placeholders specific to Paga Local Colombia contracts

        Args:
            contract_data: Raw contract data from database

        Returns:
            Dictionary mapping placeholders to replacement values
        """
        # Helper function to safely get string values
        def safe_get(d: dict, key: str, default: str = '') -> str:
            """Get value from dict and ensure it's a string"""
            value = d.get(key, default)
            return str(value) if value is not None else default

        # Start with base replacements from standard method
        base_replacements = self._prepare_replacements(contract_data)

        # Extract data_snapshot
        snapshot = contract_data.get('data_snapshot', {})

        # Get current date info
        now = datetime.now()
        generation_date = contract_data.get('generated_at', now)
        if isinstance(generation_date, str):
            generation_date = datetime.fromisoformat(generation_date.replace('Z', '+00:00'))

        # Format currency for Paga Local specific fields
        cupo_plataforma = float(snapshot.get('cupo_plataforma', 0))
        cupo_formatted = f"${cupo_plataforma:,.0f}".replace(',', '.')
        cupo_letras = self._number_to_words_spanish(cupo_plataforma)

        # Add Paga Local specific placeholders
        paga_local_replacements = {
            # K° Crédito specific placeholders (alternative representations)
            '[representante legal del Cliente]': safe_get(snapshot, 'representante_legal'),
            '[número de documento del representante legal]': safe_get(snapshot, 'cedula_representante'),

            # K° Mandato specific placeholders
            '[nombre del representante legal]': safe_get(snapshot, 'representante_legal'),
            '[monto a transferir en números]': cupo_formatted,
            '[monto a transferir en letras]': cupo_letras,
            '[consecutivo correspondiente]': safe_get(contract_data, 'contract_id'),

            # Alternative date representations for K° Mandato
            '[-día-]': str(generation_date.day),
            '[-mes-]': self._get_month_name_spanish(generation_date.month),
            '[-•-]': str(generation_date.year)[-1],  # Last digit of year
            '[-*-]': str(generation_date.year),  # Full year

            # Placeholder for attachments
            '[SE ADJUNTA POR SEPARADO]': 'SE ADJUNTA POR SEPARADO',
        }

        # Merge with base replacements (Paga Local specific takes precedence)
        base_replacements.update(paga_local_replacements)

        logger.debug(f"Prepared {len(base_replacements)} replacements for Paga Local template")

        return base_replacements

    def _replace_in_paragraph(self, paragraph, replacements: Dict[str, str]):
        """
        Replace placeholders in a paragraph while preserving formatting

        Args:
            paragraph: python-docx Paragraph object
            replacements: Dictionary of placeholder -> value mappings
        """
        # Get full text
        full_text = paragraph.text

        # Check if any replacements are needed
        needs_replacement = any(placeholder in full_text for placeholder in replacements.keys())

        if not needs_replacement:
            return

        # Perform replacements
        for placeholder, value in replacements.items():
            if placeholder in full_text:
                full_text = full_text.replace(placeholder, value)

        # Clear existing runs and add new text
        # This approach preserves paragraph formatting but not run-level formatting
        for run in paragraph.runs:
            run.text = ''

        if paragraph.runs:
            paragraph.runs[0].text = full_text
        else:
            paragraph.add_run(full_text)

    def _get_month_name_spanish(self, month: int) -> str:
        """Get Spanish month name"""
        months = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        return months.get(month, '')

    def generate_instruccion_mandato_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL - Fin. COP - Mandato (IM).docx"
    ) -> bytes:
        """
        Generate Instruccion de Mandato contract document from template and data

        Args:
            contract_data: Dictionary containing contract data with data_snapshot including:
                - Client data (nit, nombre_importador, representante_legal, cedula_representante)
                - numero_cotizacion_desembolso
                - fecha_contrato_mandato
                - monto
                - acreedores (list of dict with razon_social, nit, banco, tipo_cuenta, numero_cuenta)

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        logger.info(f"Loading Instruccion de Mandato template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Extract data from data_snapshot
        data = contract_data.get('data_snapshot', contract_data)
        logger.debug(f"Data snapshot keys: {list(data.keys())}")
        logger.debug(f"numero_cotizacion_desembolso: {data.get('numero_cotizacion_desembolso')}")
        logger.debug(f"fecha_contrato_mandato: {data.get('fecha_contrato_mandato')}")
        logger.debug(f"monto: {data.get('monto')}")
        logger.debug(f"acreedores count: {len(data.get('acreedores', []))}")

        # Prepare replacements
        replacements = self._prepare_instruccion_mandato_replacements(data)
        logger.info(f"Prepared {len(replacements)} placeholder replacements")
        for placeholder, value in replacements.items():
            logger.debug(f"  {placeholder} -> {value}")

        # Replace placeholders in paragraphs
        para_replacements = 0
        for paragraph in doc.paragraphs:
            for placeholder, value in replacements.items():
                if placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(placeholder, str(value))
                    para_replacements += 1

        # Replace placeholders in tables (EXCEPT nested creditor table which we handle separately)
        table_replacements = 0
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for placeholder, value in replacements.items():
                            if placeholder in paragraph.text:
                                paragraph.text = paragraph.text.replace(placeholder, str(value))
                                table_replacements += 1

        logger.info(f"Replacements made: {para_replacements} in paragraphs, {table_replacements} in tables")

        # Populate creditor table (nested table in Table 0, Row 3, Cell 0)
        acreedores = data.get('acreedores', [])
        if acreedores:
            self._populate_acreedores_table(doc, acreedores)

        # Save to bytes
        import io
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        logger.info(f"Generated Instruccion de Mandato document for contract {data.get('contract_id', 'unknown')}")
        return file_stream.read()

    def _prepare_instruccion_mandato_replacements(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare placeholder replacements for Instruccion de Mandato template

        Template placeholders (exact match required):
        - [Fecha actual]
        - [Número de cotización de desembolso]
        - [día de firma contrato mandato]
        - [mes de firma contrato mandato]
        - [año de firma contrato mandato]
        - [monto a transferir en letras]
        - [monto a transferir en números]
        - [Nombre del representante legal del Cliente]
        - [número ID representante legal]

        Args:
            data: Contract data snapshot

        Returns:
            Dictionary mapping placeholders to values
        """
        # Current date for fecha actual
        fecha_actual = datetime.utcnow()

        # Parse fecha_contrato_mandato into datetime for component extraction
        fecha_mandato_str = data.get('fecha_contrato_mandato', '')
        fecha_mandato_dt = None
        if fecha_mandato_str:
            try:
                # Handle ISO format: 2025-11-06 or 2025-11-06T00:00:00Z
                fecha_mandato_dt = datetime.fromisoformat(fecha_mandato_str.replace('Z', '+00:00').split('+')[0])
                logger.debug(f"Parsed fecha_contrato_mandato: {fecha_mandato_dt}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse fecha_contrato_mandato '{fecha_mandato_str}': {e}")

        # Format monto
        monto = data.get('monto', 0)
        try:
            monto_float = float(monto)
            # Format: $739,860 (Colombian format uses comma for thousands, dollar sign prefix)
            monto_formatted = f"${monto_float:,.0f}"
            # Convert to words in Spanish
            monto_letras = self._number_to_words_spanish(monto_float) + " PESOS"
        except (ValueError, TypeError):
            monto_formatted = str(monto)
            monto_letras = str(monto)

        # Format fecha actual in Spanish: "DD de MONTH de YYYY"
        fecha_actual_str = f"{fecha_actual.day} de {self._get_month_name_spanish(fecha_actual.month)} de {fecha_actual.year}"

        # Build replacements with EXACT placeholder keys matching the template
        replacements = {
            # Fecha actual
            '[Fecha actual]': fecha_actual_str,

            # Numero de cotizacion de desembolso
            '[Número de cotización de desembolso]': data.get('numero_cotizacion_desembolso', ''),

            # Fecha de firma del contrato de mandato - split into components
            '[día de firma contrato mandato]': str(fecha_mandato_dt.day) if fecha_mandato_dt else '',
            '[mes de firma contrato mandato]': self._get_month_name_spanish(fecha_mandato_dt.month) if fecha_mandato_dt else '',
            '[año de firma contrato mandato]': str(fecha_mandato_dt.year) if fecha_mandato_dt else '',

            # Financial fields
            '[monto a transferir en letras]': monto_letras,
            '[monto a transferir en números]': monto_formatted,

            # Client representative information
            '[Nombre del representante legal del Cliente]': data.get('representante_legal', ''),
            '[número ID representante legal]': data.get('cedula_representante', ''),
        }

        return replacements

    def _populate_acreedores_table(self, doc: Document, acreedores: list) -> None:
        """
        Populate creditor information table in Instruccion de Mandato template

        The creditor table is nested: Table 0 → Row 3 → Cell 0 → Nested Table
        The nested table has:
        - Row 0: Header row
        - Rows 1-3: Data rows for up to 3 creditors

        Each creditor row has 5 columns:
        - Column 0: Razon Social
        - Column 1: NIT (si aplica)
        - Column 2: Banco
        - Column 3: Tipo de Cuenta
        - Column 4: Numero de Cuenta

        For DIAN creditors (es_dian=True):
        - Razon Social: "DIAN"
        - NIT: "800.197.268-4"
        - Banco: N/A message (payment via link)
        - Tipo de Cuenta: N/A message (payment via link)
        - Numero de Cuenta: N/A message (payment via link)

        Args:
            doc: Document object with template loaded
            acreedores: List of creditor dictionaries (max 3)
        """
        try:
            # Navigate to nested table: Table 0 → Row 3 → Cell 0 → Nested Table
            if len(doc.tables) == 0:
                logger.error("No tables found in document")
                return

            main_table = doc.tables[0]
            if len(main_table.rows) < 4:
                logger.error(f"Main table has only {len(main_table.rows)} rows, expected at least 4")
                return

            target_cell = main_table.rows[3].cells[0]

            # Check if nested table exists
            if len(target_cell.tables) == 0:
                logger.error("No nested table found in target cell")
                return

            nested_table = target_cell.tables[0]
            logger.info(f"Found nested creditor table with {len(nested_table.rows)} rows")

            # Verify table structure (should have header + 3 data rows = 4 rows)
            if len(nested_table.rows) < 4:
                logger.warning(f"Nested table has {len(nested_table.rows)} rows, expected 4 (1 header + 3 data rows)")

            # Populate creditor rows (rows 1-3, row 0 is header)
            for idx, acreedor in enumerate(acreedores[:3]):  # Max 3 creditors
                row_idx = idx + 1  # Skip header row
                if row_idx >= len(nested_table.rows):
                    logger.warning(f"Cannot populate row {row_idx}, table has only {len(nested_table.rows)} rows")
                    break

                row = nested_table.rows[row_idx]
                cells = row.cells

                if len(cells) < 5:
                    logger.warning(f"Row {row_idx} has only {len(cells)} cells, expected 5")
                    continue

                # Check if this is a DIAN creditor
                is_dian = acreedor.get('es_dian', False)

                if is_dian:
                    # DIAN creditor: use predefined wording per spec
                    razon_social = DIAN_RAZON_SOCIAL
                    nit = DIAN_NIT
                    banco = DIAN_NA_MESSAGE
                    tipo_cuenta = DIAN_NA_MESSAGE
                    numero_cuenta = DIAN_NA_MESSAGE
                    logger.debug(f"Creditor {idx + 1} is DIAN - using predefined wording")
                else:
                    # Non-DIAN creditor: use provided data
                    razon_social = acreedor.get('razon_social', '')
                    nit = acreedor.get('nit', 'N/A')
                    banco = acreedor.get('banco', '')
                    tipo_cuenta = acreedor.get('tipo_cuenta', '')
                    numero_cuenta = acreedor.get('numero_cuenta', '')

                # Log the values being set for non-DIAN creditors
                if not is_dian:
                    logger.debug(f"Non-DIAN creditor {idx + 1} values: banco={banco}, tipo_cuenta={tipo_cuenta}, numero_cuenta={numero_cuenta}")

                # Helper function to set cell text (handles both placeholder replacement and empty cells)
                def set_cell_text(cell, value, cell_name):
                    """Set cell text - replace placeholder if exists, or set directly if cell is empty"""
                    if cell.paragraphs:
                        para = cell.paragraphs[0]
                        original = para.text
                        # Replace if there's a placeholder OR if cell is empty/whitespace
                        if ('[' in original and ']' in original) or not original.strip():
                            para.text = value
                            logger.debug(f"  {cell_name}: '{original}' -> '{value}'")
                        else:
                            logger.debug(f"  {cell_name}: kept as '{original}' (no placeholder, not empty)")

                # Set values in each cell
                set_cell_text(cells[0], razon_social, "Razon Social")
                set_cell_text(cells[1], nit if nit else 'N/A', "NIT")
                set_cell_text(cells[2], banco, "Banco")
                set_cell_text(cells[3], tipo_cuenta, "Tipo Cuenta")
                set_cell_text(cells[4], numero_cuenta, "Numero Cuenta")

                logger.debug(f"Populated creditor row {row_idx}: {razon_social} (DIAN: {is_dian})")

            logger.info(f"Successfully populated {len(acreedores[:3])} creditor rows")

        except Exception as e:
            logger.error(f"Error populating creditor table: {str(e)}")
            raise

    def _number_to_words_spanish(self, number: float) -> str:
        """
        Convert number to Spanish words (simplified version for large amounts)

        Args:
            number: Amount to convert

        Returns:
            String representation in Spanish words
        """
        # For MVP, use a simplified conversion
        # TODO: Implement full number-to-words conversion library

        try:
            amount = int(number)

            if amount == 0:
                return "CERO"

            # Simplified for millions (common range for contracts)
            millions = amount // 1000000
            remainder = amount % 1000000
            thousands = remainder // 1000
            units = remainder % 1000

            parts = []

            if millions > 0:
                if millions == 1:
                    parts.append("un millón")
                else:
                    parts.append(f"{self._simple_number_to_words(millions)} millones")

            if thousands > 0:
                parts.append(f"{self._simple_number_to_words(thousands)} mil")

            if units > 0:
                parts.append(self._simple_number_to_words(units))

            result = " ".join(parts)
            return result.upper()

        except Exception as e:
            logger.error(f"Error converting number to words: {e}")
            return f"{number:,.0f} PESOS"

    def _simple_number_to_words(self, n: int) -> str:
        """
        Simple number to words conversion (1-999)
        """
        if n == 0:
            return ""
        if n == 1:
            return "uno"
        if n <= 20:
            ones = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
                   "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis",
                   "diecisiete", "dieciocho", "diecinueve", "veinte"]
            return ones[n]

        # For larger numbers, use simplified format
        hundreds = n // 100
        remainder = n % 100

        result = ""
        if hundreds > 0:
            if hundreds == 1:
                result = "cien" if remainder == 0 else "ciento"
            else:
                hundreds_names = ["", "ciento", "doscientos", "trescientos", "cuatrocientos",
                                 "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
                result = hundreds_names[hundreds]

        if remainder > 0:
            if result:
                result += " "
            if remainder <= 20:
                ones = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
                       "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis",
                       "diecisiete", "dieciocho", "diecinueve", "veinte"]
                result += ones[remainder]
            else:
                tens = remainder // 10
                units = remainder % 10
                tens_names = ["", "", "veinte", "treinta", "cuarenta", "cincuenta",
                             "sesenta", "setenta", "ochenta", "noventa"]
                result += tens_names[tens]
                if units > 0:
                    ones = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
                    result += " y " + ones[units]

        return result

    def convert_to_pdf(self, docx_bytes: bytes) -> bytes:
        """
        Convert DOCX to PDF using LibreOffice headless mode

        This method works on Windows, Linux, and Mac without requiring Microsoft Word.
        LibreOffice must be installed on the system.

        Args:
            docx_bytes: DOCX file content as bytes

        Returns:
            PDF file content as bytes

        Raises:
            RuntimeError: If LibreOffice is not installed or conversion fails
        """
        import subprocess
        import platform

        try:
            # Save DOCX to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as docx_tmp:
                docx_tmp.write(docx_bytes)
                docx_path = docx_tmp.name

            # Create output directory for PDF
            output_dir = os.path.dirname(docx_path)
            pdf_filename = os.path.basename(docx_path).replace('.docx', '.pdf')
            pdf_path = os.path.join(output_dir, pdf_filename)

            # Detect LibreOffice path based on OS
            system = platform.system()
            if system == 'Windows':
                # Common Windows installation paths
                libreoffice_paths = [
                    r'C:\Program Files\LibreOffice\program\soffice.exe',
                    r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
                ]
            elif system == 'Darwin':  # macOS
                libreoffice_paths = [
                    '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                ]
            else:  # Linux and others
                libreoffice_paths = [
                    '/usr/bin/libreoffice',
                    '/usr/bin/soffice',
                ]

            # Find LibreOffice executable
            soffice_path = None
            for path in libreoffice_paths:
                if os.path.exists(path):
                    soffice_path = path
                    break

            if not soffice_path:
                raise RuntimeError(
                    "LibreOffice not found. Please install LibreOffice: "
                    "https://www.libreoffice.org/download/download/"
                )

            # Convert DOCX to PDF using LibreOffice headless mode
            cmd = [
                soffice_path,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                docx_path
            ]

            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            # Check if PDF was created
            if not os.path.exists(pdf_path):
                raise RuntimeError("PDF file was not created")

            # Read PDF bytes
            with open(pdf_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()

            # Cleanup
            try:
                os.unlink(docx_path)
                os.unlink(pdf_path)
            except Exception:
                pass  # Ignore cleanup errors

            return pdf_bytes

        except subprocess.TimeoutExpired:
            logger.error("PDF conversion timed out")
            raise RuntimeError("PDF conversion timed out (> 30 seconds)")
        except Exception as e:
            logger.error(f"Error converting to PDF: {e}")
            raise RuntimeError(f"PDF conversion failed: {str(e)}")

    def upload_to_storage(self, pdf_bytes: bytes, contract_id: str) -> str:
        """
        Upload approved contract PDF to Supabase Storage

        Args:
            pdf_bytes: PDF file content as bytes
            contract_id: Contract UUID for file naming

        Returns:
            str: Public URL of uploaded file

        Raises:
            RuntimeError: If upload fails or Supabase client not configured
        """
        if not self.supabase:
            raise RuntimeError("Supabase client not configured for storage operations")

        try:
            # Define storage path: contracts/{contract_id}/{contract_id}_approved.pdf
            file_path = f"contracts/{contract_id}/{contract_id}_approved.pdf"
            bucket_name = "contract-documents"

            logger.info(f"Uploading contract {contract_id} to Supabase Storage")

            # Upload file to Supabase Storage
            response = self.supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=pdf_bytes,
                file_options={
                    "content-type": "application/pdf",
                    "upsert": "true"  # Overwrite if exists (in case of reapproval)
                }
            )

            logger.info(f"Upload response: {response}")

            # Get public URL for the uploaded file
            public_url = self.supabase.storage.from_(bucket_name).get_public_url(file_path)

            logger.info(f"Contract {contract_id} uploaded successfully to: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Error uploading to storage: {e}")
            raise RuntimeError(f"Failed to upload contract to storage: {str(e)}")

    def generate_solicitud_desembolso_document(self, contract_data: Dict[str, Any]) -> bytes:
        """
        Generate Solicitud de Desembolso contract document from template and data

        Args:
            contract_data: Dictionary containing contract data with data_snapshot including:
                - Client data (nit, nombre_importador, etc.)
                - numero_cotizacion_desembolso
                - fecha_contrato_credito
                - monto
                - dias_plazo
                - anexo_items (list of dict with acreedor, numero_instrumento, monto)

        Returns:
            bytes: Generated DOCX file content
        """
        template_name = "FK COL - Fin. COP - Solicitud de Desembolso.docx"
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        logger.info(f"Loading Solicitud de Desembolso template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Extract data from data_snapshot
        data = contract_data.get('data_snapshot', contract_data)
        logger.info(f"Data snapshot keys: {list(data.keys())}")
        logger.info(f"iteracion_contrato in data: {data.get('iteracion_contrato', 'NOT FOUND - defaulting to 1')}")
        logger.debug(f"numero_cotizacion_desembolso: {data.get('numero_cotizacion_desembolso')}")
        logger.debug(f"fecha_contrato_credito: {data.get('fecha_contrato_credito')}")
        logger.debug(f"monto: {data.get('monto')}")
        logger.debug(f"dias_plazo: {data.get('dias_plazo')}")
        logger.debug(f"anexo_items count: {len(data.get('anexo_items', []))}")

        # Prepare replacements
        replacements = self._prepare_solicitud_desembolso_replacements(data)
        logger.info(f"Prepared {len(replacements)} placeholder replacements")
        logger.info(f"[ITERACION] replacement value: {replacements.get('[ITERACION]', 'NOT IN REPLACEMENTS!')}")
        for placeholder, value in replacements.items():
            logger.debug(f"  {placeholder} -> {value}")

        # Populate Anexo I table FIRST (before general replacements)
        # This ensures the table rows are filled before [•] placeholders are replaced
        anexo_items = data.get('anexo_items', [])
        if anexo_items:
            self._populate_anexo_table(doc, anexo_items)

            # Populate Gastos Nacionales checkboxes based on anexo items
            gastos_categories = self._determine_gastos_categories(anexo_items)
            self._populate_gastos_checkboxes(doc, gastos_categories)

        # Replace placeholders in paragraphs
        para_replacements = 0
        for paragraph in doc.paragraphs:
            for placeholder, value in replacements.items():
                if placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(placeholder, str(value))
                    para_replacements += 1

        # Replace placeholders in tables
        table_replacements = 0
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for placeholder, value in replacements.items():
                            if placeholder in paragraph.text:
                                paragraph.text = paragraph.text.replace(placeholder, str(value))
                                table_replacements += 1

        logger.info(f"Replacements made: {para_replacements} in paragraphs, {table_replacements} in tables")

        # Save to bytes
        import io
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        logger.info(f"Generated Solicitud de Desembolso document for contract {data.get('contract_id', 'unknown')}")
        return file_stream.read()

    def _prepare_solicitud_desembolso_replacements(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare placeholder replacements for Solicitud de Desembolso template

        Template placeholders (exact match required):
        - [Número de cotización de desembolso]
        - [NIT] (client tax identification number)
        - [día], [mes], [•] (for current date - 202[•] format)
        - [día de firma del contrato de crédito], [mes de firma del contrato de crédito], [ año de firma del contrato de crédito]
        - [monto]
        - [número de días de plazo]

        Args:
            data: Contract data snapshot

        Returns:
            Dictionary mapping placeholders to values
        """
        # Current date for fecha_solicitud
        fecha_solicitud = datetime.utcnow()

        # Parse fecha_contrato_credito into datetime for component extraction
        fecha_contrato_str = data.get('fecha_contrato_credito', '')
        fecha_contrato_dt = None
        if fecha_contrato_str:
            try:
                # Handle ISO format: 2025-11-06 or 2025-11-06T00:00:00Z
                fecha_contrato_dt = datetime.fromisoformat(fecha_contrato_str.replace('Z', '+00:00').split('+')[0])
                logger.debug(f"Parsed fecha_contrato_credito: {fecha_contrato_dt}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse fecha_contrato_credito '{fecha_contrato_str}': {e}")

        # Format monto - remove "COP" suffix for template since template has COP$ prefix
        monto = data.get('monto', 0)
        try:
            monto_float = float(monto)
            # Format: 739,860.00 (Colombian format uses comma for thousands, period for decimals)
            monto_formatted = f"{monto_float:,.2f}"
        except (ValueError, TypeError):
            monto_formatted = str(monto)

        # Dias plazo
        dias_plazo = str(data.get('dias_plazo', 120))

        # Build replacements with EXACT placeholder keys matching the template
        replacements = {
            # Numero de cotizacion de desembolso
            '[Número de cotización de desembolso]': data.get('numero_cotizacion_desembolso', ''),

            # Client identification
            '[NIT]': data.get('nit', ''),

            # Contract iteration number (for contract code format CO:NIT:ITERATION:D:M:DOM)
            '[ITERACION]': str(data.get('iteracion_contrato', 1)),

            # Fecha de la Solicitud de Desembolso (current date) - split into components
            # Template format: "[día] de [mes] de 202[•]"
            '[día]': str(fecha_solicitud.day),
            '[mes]': self._get_month_name_spanish(fecha_solicitud.month),
            '[•]': str(fecha_solicitud.year)[-1],  # Last digit of year for 202[•]

            # Fecha de firma del contrato de crédito - split into components
            # Template format: "[día de firma del contrato de crédito] de [mes de firma del contrato de crédito] de [ año de firma del contrato de crédito]"
            '[día de firma del contrato de crédito]': str(fecha_contrato_dt.day) if fecha_contrato_dt else '',
            '[mes de firma del contrato de crédito]': self._get_month_name_spanish(fecha_contrato_dt.month) if fecha_contrato_dt else '',
            '[ año de firma del contrato de crédito]': str(fecha_contrato_dt.year) if fecha_contrato_dt else '',

            # Financial fields
            # Template has "COP$[monto]" so we just provide the number
            '[monto]': monto_formatted,

            # Dias de plazo
            '[número de días de plazo]': dias_plazo,
        }

        return replacements

    def _populate_anexo_table(self, doc: Document, anexo_items: list) -> None:
        """
        Populate Anexo I table by filling existing placeholder rows

        The template has Table 1 (index 1) with structure:
        - Row 0: Header "ANEXO I LISTADO DE INSTRUMENTOS DE PAGO"
        - Row 1: Column headers (Acreedor, No. Instrumento, Monto)
        - Rows 2-11: Data rows with [•] placeholders
        - Row 12: TOTAL row with $[•] placeholder

        This method fills the existing [•] placeholder rows with actual data
        instead of adding new rows.

        Args:
            doc: Document object
            anexo_items: List of anexo items (dict with acreedor, numero_instrumento, monto)
        """
        # Find Anexo I table - it's Table 1 (second table) in the document
        if len(doc.tables) < 2:
            logger.warning("Could not find Anexo I table - document has fewer than 2 tables")
            return

        anexo_table = doc.tables[1]  # Table 1 is the Anexo I table
        logger.info(f"Found Anexo I table with {len(anexo_table.rows)} rows")

        # Calculate total for the TOTAL row
        total_monto = 0.0
        for item in anexo_items:
            try:
                monto = float(item.get('monto', 0))
                total_monto += monto
            except (ValueError, TypeError):
                pass

        # Fill data rows (rows 2-11 have [•] placeholders)
        # Row indices: 0=header, 1=column headers, 2-11=data rows, 12=total row
        data_row_start = 2
        data_row_end = 12  # exclusive (rows 2-11 = 10 data rows)

        for i, item in enumerate(anexo_items):
            row_index = data_row_start + i
            if row_index >= data_row_end:
                logger.warning(f"More anexo items ({len(anexo_items)}) than available rows (10). Extra items will be truncated.")
                break

            row = anexo_table.rows[row_index]
            if len(row.cells) >= 3:
                # Fill acreedor
                row.cells[0].text = str(item.get('acreedor', ''))
                # Fill numero_instrumento
                row.cells[1].text = str(item.get('numero_instrumento', ''))
                # Fill monto with $ prefix
                try:
                    monto = float(item.get('monto', 0))
                    row.cells[2].text = f"${monto:,.2f}"
                except (ValueError, TypeError):
                    row.cells[2].text = f"${item.get('monto', 0)}"

                logger.debug(f"Filled row {row_index}: {item.get('acreedor')} | {item.get('numero_instrumento')} | {item.get('monto')}")

        # Clear remaining unused data rows (replace [•] with empty)
        for row_index in range(data_row_start + len(anexo_items), data_row_end):
            row = anexo_table.rows[row_index]
            if len(row.cells) >= 3:
                row.cells[0].text = ''
                row.cells[1].text = ''
                row.cells[2].text = ''

        # Fill TOTAL row (row 12)
        if len(anexo_table.rows) > 12:
            total_row = anexo_table.rows[12]
            if len(total_row.cells) >= 3:
                # Keep "TOTAL" in first cell (or set it)
                if 'TOTAL' not in total_row.cells[0].text:
                    total_row.cells[0].text = 'TOTAL'
                # Second cell stays empty
                total_row.cells[1].text = ''
                # Third cell gets the total amount
                total_row.cells[2].text = f"${total_monto:,.2f}"

        logger.info(f"Populated Anexo I table with {len(anexo_items)} items, total: ${total_monto:,.2f}")

    def _determine_gastos_categories(self, anexo_items: list) -> set:
        """
        Analyze anexo items to determine which expense categories should be checked.

        Based on the acreedor field content, determines which Gastos Nacionales
        de Importación checkbox categories should be marked as checked.

        Args:
            anexo_items: List of anexo items with 'acreedor' field

        Returns:
            Set of category keys that should be checked (e.g., {'servicios_aduanales', 'transporte'})
        """
        categories = set()

        for item in anexo_items:
            acreedor = item.get('acreedor', '').lower()

            for category, keywords in GASTOS_CATEGORY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in acreedor:
                        categories.add(category)
                        logger.debug(f"Matched keyword '{keyword}' in acreedor '{item.get('acreedor')}' -> category '{category}'")
                        break  # Found match for this category, move to next category

        logger.info(f"Determined gastos categories from {len(anexo_items)} items: {categories}")
        return categories

    def _populate_gastos_checkboxes(self, doc: Document, categories: set) -> None:
        """
        Populate the Gastos Nacionales de Importación checkbox table.

        The nested table is located at: Table 0 → Row 3 → Cell 0 → Nested Table → Row 0
        Each cell (0-4) contains a checkbox SDT (Structured Document Tag) that needs
        to be checked/unchecked based on the categories set.

        Checkbox structure uses Word 2010 extensions (w14 namespace):
        - w14:checked w14:val="0" = unchecked
        - w14:checked w14:val="1" = checked

        Args:
            doc: Document object
            categories: Set of category keys to check (e.g., {'servicios_aduanales'})
        """
        # Define namespace for w14 (Word 2010 extensions)
        W14_NS = 'http://schemas.microsoft.com/office/word/2010/wordml'

        if len(doc.tables) < 1:
            logger.warning("Document has no tables - cannot populate gastos checkboxes")
            return

        main_table = doc.tables[0]
        if len(main_table.rows) < 4:
            logger.warning("Main table has fewer than 4 rows - cannot find gastos row")
            return

        gastos_cell = main_table.rows[3].cells[0]

        if not gastos_cell.tables:
            logger.warning("No nested table found in gastos cell")
            return

        nested_table = gastos_cell.tables[0]
        checkbox_row = nested_table.rows[0]

        checked_count = 0
        for category, cell_index in GASTOS_CHECKBOX_INDICES.items():
            if cell_index >= len(checkbox_row.cells):
                logger.warning(f"Cell index {cell_index} out of range for category {category}")
                continue

            cell = checkbox_row.cells[cell_index]
            should_check = category in categories

            # Access the cell's XML and find/modify the checkbox
            cell_xml = cell._tc

            # Find w14:checked element and update its value
            for checked_elem in cell_xml.iter('{%s}checked' % W14_NS):
                checked_elem.set('{%s}val' % W14_NS, '1' if should_check else '0')
                if should_check:
                    checked_count += 1
                logger.debug(f"Set checkbox '{category}' to {'checked' if should_check else 'unchecked'}")

        logger.info(f"Populated gastos checkboxes: {checked_count} checked out of {len(GASTOS_CHECKBOX_INDICES)} categories")

    def _format_currency_cop(self, amount: float) -> str:
        """Format amount as Colombian pesos"""
        try:
            amount_float = float(amount)
            return f"${amount_float:,.2f} COP"
        except (ValueError, TypeError):
            return f"${amount} COP"

    def _format_spanish_date(self, date_obj: datetime) -> str:
        """Format date in Spanish format: '6 de noviembre de 2025'"""
        spanish_months = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        day = date_obj.day
        month = spanish_months.get(date_obj.month, '')
        year = date_obj.year
        return f"{day} de {month} de {year}"

    def generate_dian_mandato_document(
        self,
        contract_data: Dict[str, Any],
        template_name: str = "FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx"
    ) -> bytes:
        """
        Generate DIAN Mandato (IM) contract document from template and data

        This is a simplified version of Instruccion de Mandato - no creditor table.
        Uses same placeholders but doesn't have nested creditor table.

        Args:
            contract_data: Dictionary containing contract data with data_snapshot including:
                - Client data (representante_legal, cedula_representante)
                - numero_cotizacion_desembolso
                - fecha_contrato_mandato
                - monto

        Returns:
            bytes: Generated DOCX file content
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        logger.info(f"Loading DIAN Mandato (IM) template from: {template_path}")

        # Load template
        doc = Document(str(template_path))

        # Extract data from data_snapshot
        data = contract_data.get('data_snapshot', contract_data)
        logger.debug(f"Data snapshot keys: {list(data.keys())}")

        # Reuse the same replacements function as regular Mandato (IM)
        replacements = self._prepare_instruccion_mandato_replacements(data)
        logger.info(f"Prepared {len(replacements)} placeholder replacements")

        # Replace placeholders in paragraphs
        para_replacements = 0
        for paragraph in doc.paragraphs:
            for placeholder, value in replacements.items():
                if placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(placeholder, str(value))
                    para_replacements += 1

        # Replace placeholders in tables
        table_replacements = 0
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for placeholder, value in replacements.items():
                            if placeholder in paragraph.text:
                                paragraph.text = paragraph.text.replace(placeholder, str(value))
                                table_replacements += 1

        logger.info(f"Replacements made: {para_replacements} in paragraphs, {table_replacements} in tables")

        # NOTE: No creditor table population needed for DIAN template

        # Save to bytes
        import io
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        logger.info(f"Generated DIAN Mandato (IM) document for contract {data.get('contract_id', 'unknown')}")
        return file_stream.read()
