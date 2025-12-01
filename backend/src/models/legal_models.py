"""
Legal Contract Automation - SQLAlchemy Models
"""
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, Text, DateTime,
    ForeignKey, JSON, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Client(Base):
    """Client data imported from platform exports"""
    __tablename__ = 'clients'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nit = Column(String(20), unique=True, nullable=False, index=True)
    nombre_importador = Column(String(255), nullable=False, index=True)
    representante_legal = Column(String(255), nullable=False)
    cedula_representante = Column(String(50), nullable=False)
    ciudad_domicilio = Column(String(100), nullable=False)
    cupo_plataforma = Column(Numeric(15, 2), nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    imported_by = Column(UUID(as_uuid=True))

    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)


class ContractTemplate(Base):
    """Contract template versions"""
    __tablename__ = 'contract_templates'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(20), nullable=False)
    contract_type = Column(String(50), default='activos')
    template_content = Column(Text, nullable=False)

    # Status
    active = Column(Boolean, default=False)

    # Audit
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)

    __table_args__ = (
        Index('idx_one_active_template', 'contract_type', unique=True,
              postgresql_where=active),
    )


class ContractGeneration(Base):
    """Audit trail for all generated contracts"""
    __tablename__ = 'contract_generations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Contract identification
    contract_id = Column(String(50), unique=True, nullable=False, index=True)
    client_nit = Column(String(20), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey('clients.id'))

    # Status workflow
    status = Column(
        String(50),
        default='generated',
        nullable=False,
        index=True
    )

    # Generation info
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Review info
    reviewed_by = Column(UUID(as_uuid=True))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)

    # File storage
    pdf_url = Column(Text)
    pdf_storage_path = Column(Text)

    # Template version
    template_id = Column(UUID(as_uuid=True), ForeignKey('contract_templates.id'))
    template_version = Column(String(20))

    # Data snapshot
    data_snapshot = Column(JSON, nullable=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            status.in_(['generated', 'under_review', 'approved', 'rejected']),
            name='valid_status'
        ),
    )


class ContractIDSequence(Base):
    """Manages contract ID sequencing by year"""
    __tablename__ = 'contract_id_sequence'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year = Column(Integer, nullable=False, unique=True)
    last_sequence = Column(Integer, default=0)


class DataImport(Base):
    """Tracks CSV/Excel uploads"""
    __tablename__ = 'data_imports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File info
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)

    # Import results
    total_rows = Column(Integer)
    successful_rows = Column(Integer)
    failed_rows = Column(Integer)
    error_log = Column(JSON)

    # Audit
    imported_by = Column(UUID(as_uuid=True))
    imported_at = Column(DateTime(timezone=True), server_default=func.now())

    # Status
    status = Column(String(50), default='processing')

    __table_args__ = (
        CheckConstraint(
            status.in_(['processing', 'completed', 'failed']),
            name='valid_import_status'
        ),
    )
