"""
Contract Service - Business logic for contract generation
"""
from typing import Optional, Dict, Any
from datetime import datetime
from src.repositorio.client_repository import ClientRepository
from src.repositorio.contract_repository import ContractRepository
from src.repositorio.template_repository import TemplateRepository
from src.core.servicios.document_service import DocumentService
from src.interface.legal_dtos import (
    ContractGenerationRequest,
    ContractStatus,
    ContractReviewAction
)


class ContractService:
    """Service for contract generation business logic"""

    def __init__(
        self,
        client_repo: ClientRepository,
        contract_repo: ContractRepository,
        template_repo: TemplateRepository,
        document_service: Optional[DocumentService] = None
    ):
        """
        Initialize service with repositories

        Args:
            client_repo: Client repository
            contract_repo: Contract repository
            template_repo: Template repository
            document_service: Document generation service
        """
        self.client_repo = client_repo
        self.contract_repo = contract_repo
        self.template_repo = template_repo
        self.document_service = document_service or DocumentService()

    async def generate_contract(
        self,
        request: ContractGenerationRequest,
        user_id: str,
        custom_data_snapshot: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new contract (Activos or Otrosí)

        Args:
            request: Contract generation request with contract_type
            user_id: ID of user generating contract
            custom_data_snapshot: Optional custom data snapshot (used for Solicitud de Desembolso and similar contracts)

        Returns:
            Dict[str, Any]: Generated contract data

        Raises:
            ValueError: If client not found or template not available
        """
        import logging
        logger = logging.getLogger(__name__)

        # Extract contract type from request (default to 'activos' for backward compatibility)
        contract_type = request.contract_type.value if hasattr(request.contract_type, 'value') else str(request.contract_type)
        logger.info(f"Generating {contract_type} contract for client NIT: {request.client_nit}")

        # 1. Fetch client data
        client = await self.client_repo.get_by_nit(request.client_nit)
        if not client:
            raise ValueError(f"Client with NIT {request.client_nit} not found")

        # 2. Get active template for contract type
        template = await self.template_repo.get_active_template(contract_type)
        if not template:
            raise ValueError(f"No active contract template found for type: {contract_type}")

        # 3. Generate contract ID with contract type
        contract_id = await self.contract_repo.generate_contract_id(contract_type)
        if not contract_id:
            raise ValueError("Failed to generate contract ID")

        logger.info(f"Generated contract ID: {contract_id}")

        # 4. Create data snapshot
        generation_date = datetime.utcnow().strftime('%Y-%m-%d')

        # Use custom data snapshot if provided (for Solicitud de Desembolso and similar contracts)
        if custom_data_snapshot:
            data_snapshot = custom_data_snapshot.copy()
            data_snapshot['contract_id'] = contract_id
            data_snapshot['contract_type'] = contract_type
            data_snapshot['generation_date'] = generation_date
            logger.info(f"Using custom data snapshot for contract type: {contract_type}")
        else:
            # Standard data snapshot from client data
            data_snapshot = {
                'nit': client['nit'],
                'nombre_importador': client['nombre_importador'],
                'representante_legal': client['representante_legal'],
                'cedula_representante': client['cedula_representante'],
                'ciudad_domicilio': client['ciudad_domicilio'],
                'cupo_plataforma': float(client['cupo_plataforma']),
                'contract_id': contract_id,
                'contract_type': contract_type,
                'generation_date': generation_date,
                # New fields for complete contract template population
                'direccion_comercial': client.get('direccion_comercial'),
                'tipo_identificacion_representante': client.get('tipo_identificacion_representante', 'CC'),
                'nombre_contrato_marco': client.get('nombre_contrato_marco', 'Compra de Cartera'),
                'kam_nombre': client.get('kam_nombre'),
                'kam_email': client.get('kam_email'),
                'destinatario_nombre': client.get('destinatario_nombre'),
                'destinatario_email': client.get('destinatario_email'),
            }

            # Add custodian data for Inventario Bodega contracts
            if request.custodian_data:
                data_snapshot.update({
                    'nombre_operador_custodio': request.custodian_data.nombre_operador_custodio,
                    'ciudad_domicilio_custodio': request.custodian_data.ciudad_domicilio_custodio,
                    'nit_operador_custodio': request.custodian_data.nit_operador_custodio,
                    'nombre_representante_legal_custodio': request.custodian_data.nombre_representante_legal_custodio,
                    'email_operador_custodio': request.custodian_data.email_operador_custodio,
                    'cc_representante_legal_custodio': request.custodian_data.cc_representante_legal_custodio,
                    'tipo_identificacion_representante_legal_custodio': request.custodian_data.tipo_identificacion_representante_legal_custodio,
                })
                logger.info(f"Added custodian data to contract snapshot: {request.custodian_data.nombre_operador_custodio}")

        # 5. Create contract generation record
        contract_data = {
            'contract_id': contract_id,
            'contract_type': contract_type,
            'client_nit': client['nit'],
            'client_id': client['id'],
            'status': ContractStatus.UNDER_REVIEW.value,  # Start with review status
            'generated_by': user_id,
            'template_id': template['id'],
            'template_version': template['version'],
            'data_snapshot': data_snapshot
        }

        contract = await self.contract_repo.create(contract_data)

        logger.info(f"Contract {contract_id} created successfully with status: {contract['status']}")

        return contract

    async def review_contract(
        self,
        contract_id: str,
        action: ContractReviewAction,
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review a contract (approve or reject)

        When approved, generates PDF and uploads to Supabase Storage for Operations.

        Args:
            contract_id: Contract UUID or business contract ID (e.g., ACT-2025-033)
            action: approve or reject
            reviewer_id: ID of reviewer
            notes: Review notes

        Returns:
            Dict[str, Any]: Updated contract data

        Raises:
            ValueError: If contract not found or not in reviewable status
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Starting review for contract_id={contract_id}, action={action}")

        # Get contract - try UUID first, then business contract ID
        contract = None
        try:
            # Try to get by UUID (will fail if contract_id is not a valid UUID format)
            contract = await self.contract_repo.get_by_id(contract_id)
            if contract:
                logger.info(f"Found contract by UUID: {contract.get('contract_id')}")
        except Exception as e:
            # If UUID parsing fails, it's likely a business ID
            logger.info(f"Contract ID is not a valid UUID (expected for business IDs): {e}")

        if not contract:
            # Try business contract ID (e.g., ACT-2025-033)
            logger.info(f"Trying to find contract by business ID: {contract_id}")
            contract = await self.contract_repo.get_by_contract_id(contract_id)

        if not contract:
            logger.error(f"Contract {contract_id} not found")
            raise ValueError(f"Contract {contract_id} not found")

        logger.info(f"Found contract: {contract.get('contract_id')}, status: {contract.get('status')}")

        # Check if contract is reviewable
        if contract['status'] not in [ContractStatus.GENERATED.value, ContractStatus.UNDER_REVIEW.value]:
            logger.error(f"Contract cannot be reviewed in status: {contract['status']}")
            raise ValueError(f"Contract cannot be reviewed in status: {contract['status']}")

        # Determine new status
        new_status = ContractStatus.APPROVED if action == ContractReviewAction.APPROVE else ContractStatus.REJECTED
        logger.info(f"Determined new status: {new_status.value}")

        # If approved, generate and upload PDF for Operations
        approved_document_url = None
        if action == ContractReviewAction.APPROVE:
            try:
                logger.info("Generating DOCX document...")
                docx_bytes = self.document_service.generate_contract_document(
                    contract_data=contract
                )
                logger.info(f"DOCX generated successfully, size: {len(docx_bytes)} bytes")

                logger.info("Converting DOCX to PDF...")
                pdf_bytes = self.document_service.convert_to_pdf(docx_bytes)
                logger.info(f"PDF converted successfully, size: {len(pdf_bytes)} bytes")

                logger.info("Uploading PDF to Supabase Storage...")
                approved_document_url = self.document_service.upload_to_storage(
                    pdf_bytes=pdf_bytes,
                    contract_id=contract['id']
                )
                logger.info(f"PDF uploaded successfully: {approved_document_url}")

            except Exception as e:
                logger.error(f"Failed to upload approved contract PDF: {e}", exc_info=True)

        # Update contract (use the UUID from the fetched contract, not the input which could be business ID)
        logger.info(f"Updating contract status to {new_status.value}")
        updated_contract = await self.contract_repo.update_status(
            contract_id=contract['id'],
            status=new_status,
            reviewed_by=reviewer_id,
            review_notes=notes,
            approved_document_url=approved_document_url
        )

        logger.info("Contract review completed successfully")
        return updated_contract

    async def get_contract_details(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contract details by ID

        Args:
            contract_id: Contract UUID or business contract ID

        Returns:
            Optional[Dict[str, Any]]: Contract details
        """
        # Try UUID first (will raise exception if not valid UUID format)
        contract = None
        try:
            contract = await self.contract_repo.get_by_id(contract_id)
        except Exception:
            # Not a valid UUID, try business ID
            pass

        # If not found, try business contract ID (ACT-2025-001)
        if not contract:
            contract = await self.contract_repo.get_by_contract_id(contract_id)

        return contract

    async def get_pending_reviews(self, contract_type: Optional[str] = None) -> list:
        """
        Get all contracts pending legal review, optionally filtered by contract type

        Args:
            contract_type: Optional filter by contract type ('activos' or 'otrosi')

        Returns:
            list: Contracts awaiting review
        """
        return await self.contract_repo.get_pending_review(contract_type)

    async def get_approved_contracts(self, contract_type: Optional[str] = None) -> list:
        """
        Get all approved contracts, optionally filtered by contract type

        Args:
            contract_type: Optional filter by contract type ('activos' or 'otrosi')

        Returns:
            list: Approved contracts
        """
        return await self.contract_repo.get_approved_contracts(contract_type)

    async def get_contract_stats(self) -> Dict[str, int]:
        """
        Get contract generation statistics

        Returns:
            Dict[str, int]: Statistics
        """
        return await self.contract_repo.get_stats()

    async def populate_template(self, contract_id: str) -> str:
        """
        Populate contract template with client data

        Args:
            contract_id: Contract UUID or business contract ID

        Returns:
            str: Populated template content

        Raises:
            ValueError: If contract or template not found
        """
        # Get contract (supports both UUID and business ID)
        contract = None
        try:
            contract = await self.contract_repo.get_by_id(contract_id)
        except Exception:
            pass

        if not contract:
            contract = await self.contract_repo.get_by_contract_id(contract_id)

        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Get template
        template = await self.template_repo.get_by_id(contract['template_id'])
        if not template:
            raise ValueError("Template not found")

        # Get data snapshot
        data = contract['data_snapshot']

        # Replace placeholders in template
        populated_content = template['template_content']

        # Format currency with Colombian peso format
        cupo_formatted = f"${data['cupo_plataforma']:,.2f}".replace(',', '.')

        replacements = {
            '{{IMPORTER_NAME}}': data['nombre_importador'],
            '{{TAX_ID}}': data['nit'],
            '{{LEGAL_REP_NAME}}': data['representante_legal'],
            '{{LEGAL_REP_ID}}': data['cedula_representante'],
            '{{CITY}}': data['ciudad_domicilio'],
            '{{CREDIT_LIMIT}}': cupo_formatted,
            '{{CONTRACT_ID}}': data['contract_id'],
            '{{GENERATION_DATE}}': data['generation_date'],
        }

        for placeholder, value in replacements.items():
            populated_content = populated_content.replace(placeholder, str(value))

        return populated_content

    async def generate_contract_document(self, contract_id: str) -> bytes:
        """
        Generate Word document for a contract

        Args:
            contract_id: Contract UUID or business contract ID

        Returns:
            bytes: DOCX file content

        Raises:
            ValueError: If contract not found
        """
        # Get contract (supports both UUID and business ID)
        contract = None
        try:
            contract = await self.contract_repo.get_by_id(contract_id)
        except Exception:
            pass

        if not contract:
            contract = await self.contract_repo.get_by_contract_id(contract_id)

        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Log contract data for debugging template selection
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Contract data for document generation - contract_type: {contract.get('contract_type')}, contract_id: {contract.get('contract_id')}")

        # Generate document using DocumentService
        docx_bytes = self.document_service.generate_contract_document(contract)

        return docx_bytes

    async def generate_contract_pdf(self, contract_id: str) -> bytes:
        """
        Generate PDF document for a contract

        Args:
            contract_id: Contract UUID

        Returns:
            bytes: PDF file content

        Raises:
            ValueError: If contract not found
            RuntimeError: If PDF conversion fails
        """
        # First generate DOCX from Word template
        docx_bytes = await self.generate_contract_document(contract_id)

        # Convert to PDF
        pdf_bytes = self.document_service.convert_to_pdf(docx_bytes)

        return pdf_bytes
