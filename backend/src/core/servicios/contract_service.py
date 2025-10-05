"""
Contract Service - Business logic for contract generation
"""
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from src.repositorio.client_repository import ClientRepository
from src.repositorio.contract_repository import ContractRepository
from src.repositorio.template_repository import TemplateRepository
from src.core.servicios.document_service import DocumentService
from src.interface.legal_dtos import (
    ContractGenerationRequest,
    ContractStatus,
    ContractReviewAction,
    ClientDataSnapshot
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
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate a new asset guarantee contract

        Args:
            request: Contract generation request
            user_id: ID of user generating contract

        Returns:
            Dict[str, Any]: Generated contract data

        Raises:
            ValueError: If client not found or template not available
        """
        # 1. Fetch client data
        client = await self.client_repo.get_by_nit(request.client_nit)
        if not client:
            raise ValueError(f"Client with NIT {request.client_nit} not found")

        # 2. Get active template
        template = await self.template_repo.get_active_template('activos')
        if not template:
            raise ValueError("No active contract template found")

        # 3. Generate contract ID
        contract_id = await self.contract_repo.generate_contract_id()
        if not contract_id:
            raise ValueError("Failed to generate contract ID")

        # 4. Create data snapshot
        generation_date = datetime.utcnow().strftime('%Y-%m-%d')
        data_snapshot = {
            'nit': client['nit'],
            'nombre_importador': client['nombre_importador'],
            'representante_legal': client['representante_legal'],
            'cedula_representante': client['cedula_representante'],
            'ciudad_domicilio': client['ciudad_domicilio'],
            'cupo_plataforma': float(client['cupo_plataforma']),
            'contract_id': contract_id,
            'generation_date': generation_date
        }

        # 5. Create contract generation record
        contract_data = {
            'contract_id': contract_id,
            'client_nit': client['nit'],
            'client_id': client['id'],
            'status': ContractStatus.UNDER_REVIEW.value,  # Start with review status
            'generated_by': user_id,
            'template_id': template['id'],
            'template_version': template['version'],
            'data_snapshot': data_snapshot
        }

        contract = await self.contract_repo.create(contract_data)

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
            contract_id: Contract UUID
            action: approve or reject
            reviewer_id: ID of reviewer
            notes: Review notes

        Returns:
            Dict[str, Any]: Updated contract data

        Raises:
            ValueError: If contract not found or not in reviewable status
        """
        # Get contract
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Check if contract is reviewable
        if contract['status'] not in [ContractStatus.GENERATED.value, ContractStatus.UNDER_REVIEW.value]:
            raise ValueError(f"Contract cannot be reviewed in status: {contract['status']}")

        # Determine new status
        new_status = ContractStatus.APPROVED if action == ContractReviewAction.APPROVE else ContractStatus.REJECTED

        # If approved, generate and upload PDF for Operations
        approved_document_url = None
        if action == ContractReviewAction.APPROVE:
            try:
                # Generate DOCX document
                docx_bytes = self.document_service.generate_contract_document(
                    contract_data=contract
                )

                # Convert to PDF
                pdf_bytes = self.document_service.convert_to_pdf(docx_bytes)

                # Upload to Supabase Storage
                approved_document_url = self.document_service.upload_to_storage(
                    pdf_bytes=pdf_bytes,
                    contract_id=contract['id']
                )

            except Exception as e:
                # Log error but don't fail approval if upload fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to upload approved contract PDF: {e}")
                # Continue with approval but without document URL

        # Update contract
        updated_contract = await self.contract_repo.update_status(
            contract_id=contract_id,
            status=new_status,
            reviewed_by=reviewer_id,
            review_notes=notes,
            approved_document_url=approved_document_url
        )

        return updated_contract

    async def get_contract_details(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Get contract details by ID

        Args:
            contract_id: Contract UUID or business contract ID

        Returns:
            Optional[Dict[str, Any]]: Contract details
        """
        # Try UUID first
        contract = await self.contract_repo.get_by_id(contract_id)

        # If not found, try business contract ID (ACT-2025-001)
        if not contract:
            contract = await self.contract_repo.get_by_contract_id(contract_id)

        return contract

    async def get_pending_reviews(self) -> list:
        """
        Get all contracts pending legal review

        Returns:
            list: Contracts awaiting review
        """
        return await self.contract_repo.get_pending_review()

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
            contract_id: Contract UUID

        Returns:
            str: Populated template content

        Raises:
            ValueError: If contract or template not found
        """
        # Get contract
        contract = await self.contract_repo.get_by_id(contract_id)
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
            contract_id: Contract UUID

        Returns:
            bytes: DOCX file content

        Raises:
            ValueError: If contract not found
        """
        # Get contract
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

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
        # First generate DOCX
        docx_bytes = await self.generate_contract_document(contract_id)

        # Convert to PDF
        pdf_bytes = self.document_service.convert_to_pdf(docx_bytes)

        return pdf_bytes
