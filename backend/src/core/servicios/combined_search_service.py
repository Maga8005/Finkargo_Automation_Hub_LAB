"""
Combined Search Service for Facturas + Complementos de Pago.

This service handles session management and search operations for
combined invoice and payment supplement data.
"""

import json
import logging
import os
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.interface.finance_dtos import (
    CombinedRecord,
    CombinedSearchRequest,
    CombinedSearchResponse,
    CombinedSearchResult,
    DocumentType,
    SearchType,
    ArchivoEstado
)

logger = logging.getLogger(__name__)


class CombinedSearchService:
    """
    Service for managing combined session data and search operations.

    Sessions are stored as JSON files for persistence across server restarts.
    """

    def __init__(self, session_dir: str = "temp/combined_sessions"):
        """
        Initialize the search service.

        Args:
            session_dir: Directory for storing session files
        """
        self.session_dir = session_dir
        self.session_ttl_minutes = 30
        self._lock = threading.Lock()

        # Create session directory if not exists
        os.makedirs(self.session_dir, exist_ok=True)
        logger.info(f"CombinedSearchService initialized with session dir: {self.session_dir}")

    def store_session(
        self,
        session_id: str,
        facturas: List[CombinedRecord],
        complementos: List[CombinedRecord]
    ) -> None:
        """
        Store combined data in a session.

        Args:
            session_id: Unique session identifier
            facturas: List of invoice records
            complementos: List of payment supplement records
        """
        session_file = os.path.join(self.session_dir, f"{session_id}.json")

        data = {
            "created_at": datetime.utcnow().isoformat(),
            "facturas": [r.model_dump(mode='json') for r in facturas],
            "complementos": [r.model_dump(mode='json') for r in complementos]
        }

        with self._lock:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str)

        logger.info(
            f"Session {session_id} stored: {len(facturas)} facturas, "
            f"{len(complementos)} complementos"
        )

    def get_session_data(
        self,
        session_id: str
    ) -> Optional[Dict[str, List[CombinedRecord]]]:
        """
        Retrieve session data.

        Args:
            session_id: Session identifier

        Returns:
            Dict with 'facturas' and 'complementos' lists, or None if not found
        """
        session_file = os.path.join(self.session_dir, f"{session_id}.json")

        if not os.path.exists(session_file):
            logger.warning(f"Session file not found: {session_id}")
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check TTL
            created_at = datetime.fromisoformat(data.get('created_at', ''))
            if datetime.utcnow() - created_at > timedelta(minutes=self.session_ttl_minutes):
                logger.info(f"Session {session_id} expired, removing")
                self.clear_session(session_id)
                return None

            # Convert back to CombinedRecord objects
            facturas = [
                CombinedRecord(**self._convert_dates(r))
                for r in data.get('facturas', [])
            ]
            complementos = [
                CombinedRecord(**self._convert_dates(r))
                for r in data.get('complementos', [])
            ]

            return {
                'facturas': facturas,
                'complementos': complementos
            }

        except Exception as e:
            logger.error(f"Error reading session {session_id}: {e}")
            return None

    def _convert_dates(self, record_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert date strings back to date objects."""
        if 'fecha_emision' in record_dict and isinstance(record_dict['fecha_emision'], str):
            record_dict['fecha_emision'] = datetime.fromisoformat(
                record_dict['fecha_emision']
            ).date()
        return record_dict

    def search(self, request: CombinedSearchRequest) -> CombinedSearchResponse:
        """
        Search combined data based on criteria.

        Args:
            request: Search request with filters

        Returns:
            CombinedSearchResponse with matching results
        """
        session_data = self.get_session_data(request.session_id)
        if session_data is None:
            raise ValueError(f"Sesión no encontrada o expirada: {request.session_id}")

        # Combine data based on include flags
        all_records: List[CombinedRecord] = []

        if request.include_facturas:
            all_records.extend(session_data['facturas'])

        if request.include_complementos:
            all_records.extend(session_data['complementos'])

        # Apply filters
        filtered = self._apply_filters(all_records, request)

        # Convert to search results with file status
        results = [
            CombinedSearchResult(
                **record.model_dump(),
                archivo_estado=ArchivoEstado.PENDIENTE
            )
            for record in filtered
        ]

        # Calculate totals
        facturas_results = [r for r in results if r.document_type == DocumentType.FACTURA]
        complementos_results = [r for r in results if r.document_type == DocumentType.COMPLEMENTO_PAGO]

        facturas_amount = sum(r.total for r in facturas_results)
        complementos_amount = sum(r.total for r in complementos_results)

        return CombinedSearchResponse(
            results=results,
            total_found=len(results),
            facturas_count=len(facturas_results),
            complementos_count=len(complementos_results),
            total_amount=facturas_amount + complementos_amount,
            facturas_amount=facturas_amount,
            complementos_amount=complementos_amount
        )

    def _apply_filters(
        self,
        records: List[CombinedRecord],
        request: CombinedSearchRequest
    ) -> List[CombinedRecord]:
        """Apply search filters to records."""
        filtered = records

        # Filter by search type
        if request.search_type == SearchType.CODIGO_OPERACION and request.codigo_operacion:
            # Support comma-separated codes
            codes = [c.strip().upper() for c in request.codigo_operacion.split(',')]
            filtered = [
                r for r in filtered
                if any(code in r.codigo_operacion.upper() for code in codes)
            ]

        elif request.search_type == SearchType.RFC and request.rfc:
            rfc_upper = request.rfc.strip().upper()
            filtered = [
                r for r in filtered
                if r.rfc_receptor.upper() == rfc_upper
            ]

        # Apply date range filter (works with any search type)
        if request.fecha_inicio:
            filtered = [
                r for r in filtered
                if r.fecha_emision >= request.fecha_inicio
            ]

        if request.fecha_fin:
            filtered = [
                r for r in filtered
                if r.fecha_emision <= request.fecha_fin
            ]

        return filtered

    def get_all_records(self, session_id: str) -> List[CombinedRecord]:
        """
        Get all records (facturas + complementos) from a session.

        Args:
            session_id: Session identifier

        Returns:
            List of all combined records
        """
        session_data = self.get_session_data(session_id)
        if session_data is None:
            return []

        all_records = session_data['facturas'] + session_data['complementos']
        return all_records

    def clear_session(self, session_id: str) -> bool:
        """
        Remove session data.

        Args:
            session_id: Session identifier

        Returns:
            True if session was removed, False if not found
        """
        session_file = os.path.join(self.session_dir, f"{session_id}.json")

        with self._lock:
            if os.path.exists(session_file):
                os.remove(session_file)
                logger.info(f"Session {session_id} cleared")
                return True

        return False

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict with session statistics or None if not found
        """
        session_data = self.get_session_data(session_id)
        if session_data is None:
            return None

        facturas = session_data['facturas']
        complementos = session_data['complementos']

        facturas_total = sum(r.total for r in facturas)
        complementos_total = sum(r.total for r in complementos)

        unique_rfcs = set()
        unique_operaciones = set()

        for r in facturas + complementos:
            unique_rfcs.add(r.rfc_receptor)
            unique_operaciones.add(r.codigo_operacion)

        return {
            "session_id": session_id,
            "facturas_count": len(facturas),
            "complementos_count": len(complementos),
            "total_records": len(facturas) + len(complementos),
            "facturas_total": round(facturas_total, 2),
            "complementos_total": round(complementos_total, 2),
            "combined_total": round(facturas_total + complementos_total, 2),
            "unique_rfcs": len(unique_rfcs),
            "unique_operaciones": len(unique_operaciones)
        }


# Singleton instance
_combined_search_service: Optional[CombinedSearchService] = None


def get_combined_search_service() -> CombinedSearchService:
    """Get or create the combined search service instance."""
    global _combined_search_service
    if _combined_search_service is None:
        _combined_search_service = CombinedSearchService()
    return _combined_search_service
