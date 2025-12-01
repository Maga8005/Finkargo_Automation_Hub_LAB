"""
Invoice Search Service for Facturación MX.

This service manages session data and provides search functionality
for invoice records loaded from Excel files.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
import threading
import json
from pathlib import Path

from src.interface.finance_dtos import (
    InvoiceRecord,
    InvoiceSearchRequest,
    InvoiceSearchResponse,
    InvoiceSearchResult,
    SearchType,
    ArchivoEstado
)

logger = logging.getLogger(__name__)


class InvoiceSearchService:
    """
    Service for storing session data and searching invoices.

    Uses file-based persistence for session management with automatic expiration.
    Sessions survive backend restarts.
    """

    def __init__(self, cache_ttl_minutes: int = 30):
        """
        Initialize the search service.

        Args:
            cache_ttl_minutes: Time-to-live for session data in minutes
        """
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._lock = threading.Lock()

        # Create temp directory for sessions
        self._session_dir = Path("temp/sessions")
        self._session_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Session storage initialized at {self._session_dir.absolute()}")

    def store_session(self, session_id: str, data: List[InvoiceRecord]) -> None:
        """
        Store invoice data for a session.

        Args:
            session_id: Unique session identifier
            data: List of invoice records from Excel
        """
        with self._lock:
            session_file = self._session_dir / f"{session_id}.json"

            # Convert Pydantic models to dicts
            session_data = {
                'data': [record.model_dump(mode='json') for record in data],
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat()
            }

            # Write to file
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Session {session_id} stored with {len(data)} records")

        # Clean expired sessions
        self._cleanup_expired_sessions()

    def get_session_data(self, session_id: str) -> Optional[List[InvoiceRecord]]:
        """
        Retrieve invoice data for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List of invoice records or None if session not found/expired
        """
        with self._lock:
            session_file = self._session_dir / f"{session_id}.json"

            if not session_file.exists():
                logger.warning(f"Session {session_id} not found")
                return None

            # Read session file
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                created_at = datetime.fromisoformat(session_data['created_at'])

                # Check if expired
                if datetime.now() - created_at > self._cache_ttl:
                    logger.warning(f"Session {session_id} expired")
                    session_file.unlink()  # Delete expired file
                    return None

                # Update last accessed time
                session_data['last_accessed'] = datetime.now().isoformat()
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)

                # Convert back to Pydantic models
                records = [InvoiceRecord(**record_data) for record_data in session_data['data']]
                return records

            except Exception as e:
                logger.error(f"Error reading session {session_id}: {e}")
                return None

    def search(self, request: InvoiceSearchRequest) -> InvoiceSearchResponse:
        """
        Search invoices based on provided criteria.

        Supports combined filters:
        - codigo_operacion + optional date range
        - rfc + optional date range
        - date range only

        Args:
            request: Search request with criteria

        Returns:
            InvoiceSearchResponse with matching results

        Raises:
            ValueError: If session not found or search criteria invalid
        """
        # Get session data
        data = self.get_session_data(request.session_id)
        if data is None:
            raise ValueError(f"Sesión no encontrada o expirada: {request.session_id}")

        # Step 1: Apply primary filter based on search type
        results: List[InvoiceRecord] = []

        if request.search_type == SearchType.CODIGO_OPERACION:
            if not request.codigo_operacion:
                raise ValueError("Código de operación es requerido para este tipo de búsqueda")

            # Support multiple codes separated by comma
            search_terms = [
                term.strip().upper()
                for term in request.codigo_operacion.split(',')
                if term.strip()
            ]

            results = [
                record for record in data
                if any(term in record.codigo_operacion.upper() for term in search_terms)
            ]
            logger.info(f"Codigo search: {len(results)} records found for codes: {search_terms}")

        elif request.search_type == SearchType.RFC:
            if not request.rfc:
                raise ValueError("RFC es requerido para este tipo de búsqueda")

            search_rfc = request.rfc.strip().upper()
            results = [
                record for record in data
                if record.rfc_receptor.upper() == search_rfc
            ]
            logger.info(f"RFC search: {len(results)} records found for RFC: {search_rfc}")

        elif request.search_type == SearchType.FECHA:
            if not request.fecha_inicio or not request.fecha_fin:
                raise ValueError("Fecha inicio y fecha fin son requeridas para búsqueda solo por fecha")

            # For fecha-only search, start with all records
            results = data.copy()

        # Step 2: Apply date range filter if provided (combined filter)
        has_date_filter = request.fecha_inicio and request.fecha_fin
        if has_date_filter and request.search_type != SearchType.FECHA:
            # This is a combined filter scenario
            logger.info(f"Applying combined date filter: {request.fecha_inicio} to {request.fecha_fin}")
            logger.info(f"Records before date filter: {len(results)}")

        if has_date_filter:
            filtered_by_date = []
            for record in results:
                # Ensure both dates are date objects for comparison
                record_date = record.fecha_emision
                if isinstance(record_date, str):
                    record_date = datetime.fromisoformat(record_date).date()
                elif isinstance(record_date, datetime):
                    record_date = record_date.date()

                if request.fecha_inicio <= record_date <= request.fecha_fin:
                    filtered_by_date.append(record)

            results = filtered_by_date
            logger.info(f"Records after date filter: {len(results)}")

            # Debug: Log first 5 results
            if results and len(results) <= 10:
                logger.info(f"Date filtered results ({len(results)} total):")
                for i, r in enumerate(results[:5]):
                    logger.info(f"  [{i+1}] {r.uuid[:8]}: {r.fecha_emision} - {r.codigo_operacion}")

        # Convert to search results with pending status
        search_results = [
            InvoiceSearchResult(
                uuid=record.uuid,
                codigo_operacion=record.codigo_operacion,
                conceptos=record.conceptos,
                fecha_emision=record.fecha_emision,
                rfc_receptor=record.rfc_receptor,
                razon_receptor=record.razon_receptor,
                subtotal=record.subtotal,
                iva_trasladado=record.iva_trasladado,
                iva_exento=record.iva_exento,
                total=record.total,
                clasificacion_gasto=record.clasificacion_gasto,
                archivo_estado=ArchivoEstado.PENDIENTE
            )
            for record in results
        ]

        # Calculate total amount
        total_amount = sum(record.total for record in results)

        logger.info(f"Search in session {request.session_id}: found {len(results)} records, total: ${total_amount:.2f}")

        return InvoiceSearchResponse(
            results=search_results,
            total_found=len(search_results),
            total_amount=total_amount
        )

    def clear_session(self, session_id: str) -> bool:
        """
        Remove session data from cache.

        Args:
            session_id: Unique session identifier

        Returns:
            True if session was found and removed, False otherwise
        """
        with self._lock:
            session_file = self._session_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Session {session_id} cleared")
                return True
            return False

    def _cleanup_expired_sessions(self) -> None:
        """Remove all expired sessions from file storage."""
        now = datetime.now()
        expired_count = 0

        for session_file in self._session_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                created_at = datetime.fromisoformat(session_data['created_at'])

                if now - created_at > self._cache_ttl:
                    session_file.unlink()
                    expired_count += 1
                    logger.info(f"Expired session {session_file.stem} removed")

            except Exception as e:
                logger.error(f"Error checking session file {session_file}: {e}")

        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        self._cleanup_expired_sessions()
        return len(list(self._session_dir.glob("*.json")))


# Singleton instance for dependency injection
_invoice_search_service: Optional[InvoiceSearchService] = None


def get_invoice_search_service() -> InvoiceSearchService:
    """
    Get or create the invoice search service singleton.

    Returns:
        InvoiceSearchService instance
    """
    global _invoice_search_service
    if _invoice_search_service is None:
        _invoice_search_service = InvoiceSearchService()
    return _invoice_search_service
