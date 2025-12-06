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
            logger.warning(f"contract_type is None or empty at top level, checking data_snapshot")
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
