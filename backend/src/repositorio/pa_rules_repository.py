"""
PA Rules Repository - Database operations for PA classification rules.

Handles CRUD operations for:
- pa_account_catalog: Account mapping for filtering and homologation
- pa_classification_rules: Main classification rules
- pa_clasificacion_cuenta_rules: Account name → classification rules
- pa_nexo_rules: Account name → nexo rules
- pa_processing_history: Processing audit trail
"""

from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class PARulesRepository:
    """Repository for PA classification rules operations."""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client.

        Args:
            supabase_client: Supabase client instance.
        """
        self.db = supabase_client

    # =========================================================================
    # Account Catalog Operations
    # =========================================================================

    async def get_account_catalog(self, limit: int = 1000, offset: int = 0) -> tuple[List[Dict], int]:
        """
        Get PA account catalog entries.

        Args:
            limit: Maximum entries to return.
            offset: Number of entries to skip.

        Returns:
            Tuple of (list of entries, total count).
        """
        try:
            response = self.db.table("pa_account_catalog")\
                .select("*", count="exact")\
                .order("cuenta_finkargo")\
                .range(offset, offset + limit - 1)\
                .execute()

            return response.data or [], response.count or 0
        except Exception as e:
            logger.error(f"Error getting account catalog: {e}")
            return [], 0

    async def get_catalog_entry_by_cuenta(self, cuenta_finkargo: str) -> Optional[Dict]:
        """
        Get a single catalog entry by account number.

        Args:
            cuenta_finkargo: Finkargo account number.

        Returns:
            Catalog entry dict or None.
        """
        try:
            response = self.db.table("pa_account_catalog")\
                .select("*")\
                .eq("cuenta_finkargo", cuenta_finkargo)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting catalog entry: {e}")
            return None

    async def get_all_catalog_accounts(self) -> List[str]:
        """
        Get all account numbers from the catalog.

        Returns:
            List of cuenta_finkargo values.
        """
        try:
            response = self.db.table("pa_account_catalog")\
                .select("cuenta_finkargo")\
                .execute()

            accounts = [r["cuenta_finkargo"] for r in (response.data or [])]
            account_count = len(accounts)
            logger.info(f"Retrieved {account_count} accounts from pa_account_catalog")
            if account_count == 0:
                logger.warning("PA account catalog is empty. Please upload catalog first.")
            elif account_count > 0:
                logger.debug(f"Sample catalog accounts: {accounts[:5]}")
            return accounts
        except Exception as e:
            logger.error(f"Error getting catalog accounts: {e}")
            return []

    async def upsert_catalog_entries(
        self,
        entries: List[Dict],
        created_by: Optional[str] = None
    ) -> tuple[int, int, int, List[str]]:
        """
        Upsert catalog entries (insert or update).

        Args:
            entries: List of catalog entry dicts.
            created_by: User ID who created the entries.

        Returns:
            Tuple of (uploaded, updated, skipped, errors).
        """
        uploaded = 0
        updated = 0
        skipped = 0
        errors = []

        for entry in entries:
            try:
                # Check if entry exists
                existing = await self.get_catalog_entry_by_cuenta(entry["cuenta_finkargo"])

                if existing:
                    # Update existing entry
                    self.db.table("pa_account_catalog")\
                        .update({
                            "cuenta_homologacion": entry["cuenta_homologacion"],
                            "nombre_homologacion": entry["nombre_homologacion"],
                            "updated_at": datetime.utcnow().isoformat()
                        })\
                        .eq("cuenta_finkargo", entry["cuenta_finkargo"])\
                        .execute()
                    updated += 1
                else:
                    # Insert new entry
                    new_entry = {
                        "id": str(uuid.uuid4()),
                        "cuenta_finkargo": entry["cuenta_finkargo"],
                        "cuenta_homologacion": entry["cuenta_homologacion"],
                        "nombre_homologacion": entry["nombre_homologacion"],
                        "created_by": created_by
                    }
                    self.db.table("pa_account_catalog").insert(new_entry).execute()
                    uploaded += 1

            except Exception as e:
                errors.append(f"Error with account {entry.get('cuenta_finkargo', 'unknown')}: {str(e)}")
                skipped += 1

        return uploaded, updated, skipped, errors

    async def clear_catalog(self) -> bool:
        """
        Clear all entries from the account catalog.

        Returns:
            True if successful.
        """
        try:
            self.db.table("pa_account_catalog").delete().neq("id", "").execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing catalog: {e}")
            return False

    # =========================================================================
    # Classification Rules Operations
    # =========================================================================

    async def get_classification_rules(self, active_only: bool = True) -> List[Dict]:
        """
        Get classification rules.

        Args:
            active_only: Only return active rules.

        Returns:
            List of rule dicts.
        """
        try:
            query = self.db.table("pa_classification_rules")\
                .select("*")\
                .order("prioridad")

            if active_only:
                query = query.eq("is_active", True)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting classification rules: {e}")
            return []

    async def upsert_classification_rules(
        self,
        rules: List[Dict],
        created_by: Optional[str] = None
    ) -> tuple[int, int, int, List[str]]:
        """
        Upsert classification rules.

        Args:
            rules: List of rule dicts.
            created_by: User ID who created the rules.

        Returns:
            Tuple of (uploaded, updated, skipped, errors).
        """
        uploaded = 0
        updated = 0
        skipped = 0
        errors = []

        for rule in rules:
            try:
                # Check for existing rule with same key
                tipo_trans = rule.get("tipo_transaccion", "")
                tipo_comp = rule.get("tipo_comprobante", "")
                num_doc_patron = rule.get("numero_documento_patron")

                query = self.db.table("pa_classification_rules")\
                    .select("id")\
                    .eq("tipo_transaccion", tipo_trans)\
                    .eq("tipo_comprobante", tipo_comp)

                if num_doc_patron:
                    query = query.eq("numero_documento_patron", num_doc_patron)
                else:
                    query = query.is_("numero_documento_patron", "null")

                existing = query.execute()

                if existing.data:
                    # Update existing
                    self.db.table("pa_classification_rules")\
                        .update({
                            "categoria": rule.get("categoria"),
                            "subcategoria_base": rule.get("subcategoria_base"),
                            "clasificacion_default": rule.get("clasificacion_default"),
                            "prioridad": rule.get("prioridad", 100),
                            "is_active": True,
                            "updated_at": datetime.utcnow().isoformat()
                        })\
                        .eq("id", existing.data[0]["id"])\
                        .execute()
                    updated += 1
                else:
                    # Insert new
                    new_rule = {
                        "id": str(uuid.uuid4()),
                        "tipo_transaccion": tipo_trans,
                        "tipo_comprobante": tipo_comp,
                        "numero_documento_patron": num_doc_patron,
                        "categoria": rule.get("categoria"),
                        "subcategoria_base": rule.get("subcategoria_base"),
                        "clasificacion_default": rule.get("clasificacion_default"),
                        "prioridad": rule.get("prioridad", 100),
                        "is_active": True,
                        "created_by": created_by
                    }
                    self.db.table("pa_classification_rules").insert(new_rule).execute()
                    uploaded += 1

            except Exception as e:
                errors.append(f"Error with rule {rule.get('tipo_transaccion', 'unknown')}: {str(e)}")
                skipped += 1

        return uploaded, updated, skipped, errors

    async def clear_classification_rules(self) -> bool:
        """Clear all classification rules."""
        try:
            self.db.table("pa_classification_rules").delete().neq("id", "").execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing classification rules: {e}")
            return False

    # =========================================================================
    # Clasificación Cuenta Rules Operations
    # =========================================================================

    async def get_clasificacion_cuenta_rules(self, active_only: bool = True) -> List[Dict]:
        """
        Get clasificación cuenta rules.

        Args:
            active_only: Only return active rules.

        Returns:
            List of rule dicts.
        """
        try:
            query = self.db.table("pa_clasificacion_cuenta_rules")\
                .select("*")\
                .order("prioridad")

            if active_only:
                query = query.eq("is_active", True)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting clasificacion cuenta rules: {e}")
            return []

    async def upsert_clasificacion_cuenta_rules(
        self,
        rules: List[Dict],
        created_by: Optional[str] = None
    ) -> tuple[int, int, int, List[str]]:
        """
        Upsert clasificación cuenta rules.

        Args:
            rules: List of rule dicts.
            created_by: User ID who created the rules.

        Returns:
            Tuple of (uploaded, updated, skipped, errors).
        """
        uploaded = 0
        updated = 0
        skipped = 0
        errors = []

        for rule in rules:
            try:
                cuenta_patron = rule.get("cuenta_nombre_patron", "")
                categoria_aplicable = rule.get("categoria_aplicable")

                query = self.db.table("pa_clasificacion_cuenta_rules")\
                    .select("id")\
                    .eq("cuenta_nombre_patron", cuenta_patron)

                if categoria_aplicable:
                    query = query.eq("categoria_aplicable", categoria_aplicable)
                else:
                    query = query.is_("categoria_aplicable", "null")

                existing = query.execute()

                if existing.data:
                    self.db.table("pa_clasificacion_cuenta_rules")\
                        .update({
                            "clasificacion": rule.get("clasificacion"),
                            "prioridad": rule.get("prioridad", 100),
                            "is_active": True,
                            "updated_at": datetime.utcnow().isoformat()
                        })\
                        .eq("id", existing.data[0]["id"])\
                        .execute()
                    updated += 1
                else:
                    new_rule = {
                        "id": str(uuid.uuid4()),
                        "cuenta_nombre_patron": cuenta_patron,
                        "clasificacion": rule.get("clasificacion"),
                        "categoria_aplicable": categoria_aplicable,
                        "prioridad": rule.get("prioridad", 100),
                        "is_active": True,
                        "created_by": created_by
                    }
                    self.db.table("pa_clasificacion_cuenta_rules").insert(new_rule).execute()
                    uploaded += 1

            except Exception as e:
                errors.append(f"Error with cuenta rule {rule.get('cuenta_nombre_patron', 'unknown')}: {str(e)}")
                skipped += 1

        return uploaded, updated, skipped, errors

    async def clear_clasificacion_cuenta_rules(self) -> bool:
        """Clear all clasificación cuenta rules."""
        try:
            self.db.table("pa_clasificacion_cuenta_rules").delete().neq("id", "").execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing clasificacion cuenta rules: {e}")
            return False

    # =========================================================================
    # Nexo Rules Operations
    # =========================================================================

    async def get_nexo_rules(self, active_only: bool = True) -> List[Dict]:
        """
        Get nexo rules.

        Args:
            active_only: Only return active rules.

        Returns:
            List of rule dicts.
        """
        try:
            query = self.db.table("pa_nexo_rules")\
                .select("*")\
                .order("prioridad")

            if active_only:
                query = query.eq("is_active", True)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting nexo rules: {e}")
            return []

    async def upsert_nexo_rules(
        self,
        rules: List[Dict],
        created_by: Optional[str] = None
    ) -> tuple[int, int, int, List[str]]:
        """
        Upsert nexo rules.

        Args:
            rules: List of rule dicts.
            created_by: User ID who created the rules.

        Returns:
            Tuple of (uploaded, updated, skipped, errors).
        """
        uploaded = 0
        updated = 0
        skipped = 0
        errors = []

        for rule in rules:
            try:
                cuenta_patron = rule.get("cuenta_nombre_patron", "")

                existing = self.db.table("pa_nexo_rules")\
                    .select("id")\
                    .eq("cuenta_nombre_patron", cuenta_patron)\
                    .execute()

                if existing.data:
                    self.db.table("pa_nexo_rules")\
                        .update({
                            "nexo": rule.get("nexo"),
                            "prioridad": rule.get("prioridad", 100),
                            "is_active": True,
                            "updated_at": datetime.utcnow().isoformat()
                        })\
                        .eq("id", existing.data[0]["id"])\
                        .execute()
                    updated += 1
                else:
                    new_rule = {
                        "id": str(uuid.uuid4()),
                        "cuenta_nombre_patron": cuenta_patron,
                        "nexo": rule.get("nexo"),
                        "prioridad": rule.get("prioridad", 100),
                        "is_active": True,
                        "created_by": created_by
                    }
                    self.db.table("pa_nexo_rules").insert(new_rule).execute()
                    uploaded += 1

            except Exception as e:
                errors.append(f"Error with nexo rule {rule.get('cuenta_nombre_patron', 'unknown')}: {str(e)}")
                skipped += 1

        return uploaded, updated, skipped, errors

    async def clear_nexo_rules(self) -> bool:
        """Clear all nexo rules."""
        try:
            self.db.table("pa_nexo_rules").delete().neq("id", "").execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing nexo rules: {e}")
            return False

    # =========================================================================
    # Processing History Operations
    # =========================================================================

    async def create_processing_session(
        self,
        filename: str,
        file_size: int,
        processed_by: Optional[str] = None,
        processed_by_email: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new processing session record.

        Args:
            filename: Original filename.
            file_size: File size in bytes.
            processed_by: User ID.
            processed_by_email: User email.

        Returns:
            Session ID or None if failed.
        """
        try:
            # Generate session ID using database function
            session_id_response = self.db.rpc("generate_pa_session_id").execute()
            session_id = session_id_response.data if session_id_response.data else None

            if not session_id:
                # Fallback: generate manually
                timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                session_id = f"PA-{timestamp}-0001"

            record = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "status": "uploading",
                "original_filename": filename,
                "original_file_size": file_size,
                "stats": {},
                "processed_by": processed_by,
                "processed_by_email": processed_by_email,
                "started_at": datetime.utcnow().isoformat()
            }

            self.db.table("pa_processing_history").insert(record).execute()
            return session_id

        except Exception as e:
            logger.error(f"Error creating processing session: {e}")
            return None

    async def get_processing_session(self, session_id: str) -> Optional[Dict]:
        """
        Get processing session by session ID.

        Args:
            session_id: Session ID.

        Returns:
            Session dict or None.
        """
        try:
            response = self.db.table("pa_processing_history")\
                .select("*")\
                .eq("session_id", session_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting processing session: {e}")
            return None

    async def update_processing_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update processing session.

        Args:
            session_id: Session ID.
            updates: Dict of fields to update.

        Returns:
            True if successful.
        """
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            self.db.table("pa_processing_history")\
                .update(updates)\
                .eq("session_id", session_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating processing session: {e}")
            return False

    async def get_processing_history(
        self,
        status: Optional[str] = None,
        processed_by: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[Dict], int]:
        """
        Get processing history with filters.

        Args:
            status: Filter by status.
            processed_by: Filter by user ID.
            date_from: Filter by start date.
            date_to: Filter by end date.
            limit: Maximum entries.
            offset: Entries to skip.

        Returns:
            Tuple of (list of entries, total count).
        """
        try:
            query = self.db.table("pa_processing_history")\
                .select("*", count="exact")\
                .order("started_at", desc=True)

            if status:
                query = query.eq("status", status)
            if processed_by:
                query = query.eq("processed_by", processed_by)
            if date_from:
                query = query.gte("started_at", date_from)
            if date_to:
                query = query.lte("started_at", date_to)

            query = query.range(offset, offset + limit - 1)

            response = query.execute()
            return response.data or [], response.count or 0

        except Exception as e:
            logger.error(f"Error getting processing history: {e}")
            return [], 0

    # =========================================================================
    # Rules Summary
    # =========================================================================

    async def get_rules_summary(self) -> Dict[str, Any]:
        """
        Get summary of all loaded rules.

        Returns:
            Summary dict with counts and last update times.
        """
        try:
            # Get counts
            catalog_response = self.db.table("pa_account_catalog")\
                .select("*", count="exact")\
                .limit(1)\
                .execute()
            catalog_count = catalog_response.count or 0

            class_response = self.db.table("pa_classification_rules")\
                .select("*", count="exact")\
                .eq("is_active", True)\
                .limit(1)\
                .execute()
            class_count = class_response.count or 0

            cuenta_response = self.db.table("pa_clasificacion_cuenta_rules")\
                .select("*", count="exact")\
                .eq("is_active", True)\
                .limit(1)\
                .execute()
            cuenta_count = cuenta_response.count or 0

            nexo_response = self.db.table("pa_nexo_rules")\
                .select("*", count="exact")\
                .eq("is_active", True)\
                .limit(1)\
                .execute()
            nexo_count = nexo_response.count or 0

            # Get last update times
            catalog_last = self.db.table("pa_account_catalog")\
                .select("updated_at")\
                .order("updated_at", desc=True)\
                .limit(1)\
                .execute()

            class_last = self.db.table("pa_classification_rules")\
                .select("updated_at")\
                .order("updated_at", desc=True)\
                .limit(1)\
                .execute()

            cuenta_last = self.db.table("pa_clasificacion_cuenta_rules")\
                .select("updated_at")\
                .order("updated_at", desc=True)\
                .limit(1)\
                .execute()

            nexo_last = self.db.table("pa_nexo_rules")\
                .select("updated_at")\
                .order("updated_at", desc=True)\
                .limit(1)\
                .execute()

            return {
                "catalog_count": catalog_count,
                "classification_rules_count": class_count,
                "clasificacion_cuenta_rules_count": cuenta_count,
                "nexo_rules_count": nexo_count,
                "last_catalog_update": catalog_last.data[0]["updated_at"] if catalog_last.data else None,
                "last_classification_update": class_last.data[0]["updated_at"] if class_last.data else None,
                "last_clasificacion_cuenta_update": cuenta_last.data[0]["updated_at"] if cuenta_last.data else None,
                "last_nexo_update": nexo_last.data[0]["updated_at"] if nexo_last.data else None
            }

        except Exception as e:
            logger.error(f"Error getting rules summary: {e}")
            return {
                "catalog_count": 0,
                "classification_rules_count": 0,
                "clasificacion_cuenta_rules_count": 0,
                "nexo_rules_count": 0,
                "last_catalog_update": None,
                "last_classification_update": None,
                "last_clasificacion_cuenta_update": None,
                "last_nexo_update": None
            }


# Singleton instance
_pa_rules_repo_instance: Optional[PARulesRepository] = None


def get_pa_rules_repository(supabase_client: Client) -> PARulesRepository:
    """
    Get or create PA rules repository instance.

    Args:
        supabase_client: Supabase client.

    Returns:
        PARulesRepository instance.
    """
    global _pa_rules_repo_instance
    if _pa_rules_repo_instance is None:
        _pa_rules_repo_instance = PARulesRepository(supabase_client)
    return _pa_rules_repo_instance
