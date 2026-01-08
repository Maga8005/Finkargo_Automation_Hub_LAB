"""
Drive File Cache Repository - Database operations for caching Google Drive file IDs.

Caches file IDs to avoid expensive search-by-name operations in Google Drive API.
"""

from typing import Optional, Dict, List
from supabase import Client
import logging

logger = logging.getLogger(__name__)


class DriveFileCacheRepository:
    """Repository for drive file cache operations."""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client.

        Args:
            supabase_client: Supabase client instance.
        """
        self.db = supabase_client
        self.table_name = "drive_file_cache"

    def get_file_id(
        self,
        uuid: str,
        file_type: str,
        country: str = "MX"
    ) -> Optional[str]:
        """
        Get cached Drive file ID for a UUID and file type.

        Args:
            uuid: Document UUID.
            file_type: File type ('pdf' or 'xml').
            country: Country code ('MX' or 'CO').

        Returns:
            str: Drive file ID if cached, None otherwise.
        """
        try:
            response = self.db.table(self.table_name)\
                .select('drive_file_id')\
                .eq('uuid', uuid)\
                .eq('file_type', file_type)\
                .eq('country', country)\
                .execute()

            if response.data and len(response.data) > 0:
                # Return cached file_id directly (skip touch for performance)
                return response.data[0]['drive_file_id']

            return None

        except Exception as e:
            logger.warning(f"Error getting cached file ID for {uuid}.{file_type}: {e}")
            return None

    def _touch_record(self, uuid: str, file_type: str, country: str) -> None:
        """Update last_accessed_at for a record."""
        try:
            self.db.table(self.table_name)\
                .update({'updated_at': 'now()'})\
                .eq('uuid', uuid)\
                .eq('file_type', file_type)\
                .eq('country', country)\
                .execute()
        except Exception:
            pass  # Non-critical operation

    def cache_file_id(
        self,
        uuid: str,
        file_type: str,
        drive_file_id: str,
        drive_file_name: Optional[str] = None,
        country: str = "MX",
        file_size_bytes: Optional[int] = None
    ) -> bool:
        """
        Cache a Drive file ID for a UUID.

        Args:
            uuid: Document UUID.
            file_type: File type ('pdf' or 'xml').
            drive_file_id: Google Drive file ID.
            drive_file_name: Original file name in Drive.
            country: Country code ('MX' or 'CO').
            file_size_bytes: File size in bytes (optional).

        Returns:
            bool: True if cached successfully, False otherwise.
        """
        try:
            data = {
                'uuid': uuid,
                'file_type': file_type,
                'drive_file_id': drive_file_id,
                'country': country
            }

            if drive_file_name:
                data['drive_file_name'] = drive_file_name
            if file_size_bytes:
                data['file_size_bytes'] = file_size_bytes

            # Upsert: insert or update if exists
            self.db.table(self.table_name)\
                .upsert(data, on_conflict='uuid,file_type,country')\
                .execute()

            logger.debug(f"Cached file ID for {uuid}.{file_type}: {drive_file_id[:20]}...")
            return True

        except Exception as e:
            logger.warning(f"Error caching file ID for {uuid}.{file_type}: {e}")
            return False

    def get_bulk_file_ids(
        self,
        uuids: List[str],
        country: str = "MX"
    ) -> Dict[str, Dict[str, str]]:
        """
        Get cached file IDs for multiple UUIDs using batched queries.

        Args:
            uuids: List of document UUIDs.
            country: Country code ('MX' or 'CO').

        Returns:
            Dict mapping UUID to {file_type: drive_file_id}.
            Example: {'uuid1': {'pdf': 'id1', 'xml': 'id2'}, ...}
        """
        if not uuids:
            return {}

        # Batch size to avoid "URL component 'query' too long" error
        # UUIDs are ~36 chars, so 200 UUIDs ≈ 7200 chars, safe for URL limits
        BATCH_SIZE = 200
        result: Dict[str, Dict[str, str]] = {}

        for i in range(0, len(uuids), BATCH_SIZE):
            batch = uuids[i:i + BATCH_SIZE]
            try:
                response = self.db.table(self.table_name)\
                    .select('uuid, file_type, drive_file_id')\
                    .in_('uuid', batch)\
                    .eq('country', country)\
                    .execute()

                for row in response.data or []:
                    uuid = row['uuid']
                    if uuid not in result:
                        result[uuid] = {}
                    result[uuid][row['file_type']] = row['drive_file_id']

            except Exception as e:
                logger.warning(f"Error getting batch {i // BATCH_SIZE + 1}: {e}")
                # Continue with other batches

        logger.info(f"Bulk cache lookup: {len(uuids)} UUIDs in {(len(uuids) + BATCH_SIZE - 1) // BATCH_SIZE} batches, {len(result)} found in cache")
        return result

    def cache_bulk_file_ids(
        self,
        files: List[Dict],
        country: str = "MX"
    ) -> int:
        """
        Cache multiple file IDs using batched upserts.

        Args:
            files: List of dicts with keys: uuid, file_type, drive_file_id, drive_file_name (optional).
            country: Country code ('MX' or 'CO').

        Returns:
            int: Number of files cached successfully.
        """
        if not files:
            return 0

        # Batch size to avoid request body too large errors
        BATCH_SIZE = 500
        total_cached = 0

        # Build all records first
        all_records = []
        for f in files:
            record = {
                'uuid': f['uuid'],
                'file_type': f['file_type'],
                'drive_file_id': f['drive_file_id'],
                'country': country
            }
            if f.get('drive_file_name'):
                record['drive_file_name'] = f['drive_file_name']
            all_records.append(record)

        # Upsert in batches
        for i in range(0, len(all_records), BATCH_SIZE):
            batch = all_records[i:i + BATCH_SIZE]
            try:
                self.db.table(self.table_name)\
                    .upsert(batch, on_conflict='uuid,file_type,country')\
                    .execute()
                total_cached += len(batch)
                logger.debug(f"Cached batch {i // BATCH_SIZE + 1}: {len(batch)} records")
            except Exception as e:
                logger.warning(f"Error caching batch {i // BATCH_SIZE + 1}: {e}")
                # Continue with other batches

        logger.info(f"Bulk cached {total_cached}/{len(all_records)} file IDs for country {country}")
        return total_cached

    def delete_old_entries(self, days_old: int = 90) -> int:
        """
        Delete cache entries not accessed in the specified number of days.

        Args:
            days_old: Number of days after which entries are considered stale.

        Returns:
            int: Number of entries deleted.
        """
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()

            response = self.db.table(self.table_name)\
                .delete()\
                .lt('last_accessed_at', cutoff_date)\
                .execute()

            deleted_count = len(response.data) if response.data else 0
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old cache entries")
            return deleted_count

        except Exception as e:
            logger.warning(f"Error cleaning up old cache entries: {e}")
            return 0

    def get_cache_stats(self, country: Optional[str] = None) -> Dict:
        """
        Get cache statistics.

        Args:
            country: Optional country filter.

        Returns:
            Dict with cache statistics.
        """
        try:
            query = self.db.table(self.table_name).select('*', count='exact')
            if country:
                query = query.eq('country', country)
            response = query.execute()

            total = response.count or 0

            # Count by file type
            pdf_count = 0
            xml_count = 0
            for row in response.data or []:
                if row['file_type'] == 'pdf':
                    pdf_count += 1
                elif row['file_type'] == 'xml':
                    xml_count += 1

            return {
                'total_cached': total,
                'pdf_count': pdf_count,
                'xml_count': xml_count,
                'country': country or 'all'
            }

        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {'total_cached': 0, 'pdf_count': 0, 'xml_count': 0}


# Singleton instance
_cache_repo_instance: Optional[DriveFileCacheRepository] = None


def get_drive_file_cache_repository(supabase_client: Client) -> DriveFileCacheRepository:
    """
    Get or create drive file cache repository instance.

    Args:
        supabase_client: Supabase client.

    Returns:
        DriveFileCacheRepository instance.
    """
    global _cache_repo_instance
    if _cache_repo_instance is None:
        _cache_repo_instance = DriveFileCacheRepository(supabase_client)
    return _cache_repo_instance
