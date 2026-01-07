"""
Finance Report Repository - Database operations for finance report history.

Handles CRUD operations for the finance_reports table tracking all
report generations for Colombia (CO) and Mexico (MX) operations.
"""

from typing import List, Optional
from supabase import Client
from datetime import datetime, timedelta
import logging

from src.interface.finance_history_dtos import (
    FinanceHistoryFilter,
)

logger = logging.getLogger(__name__)


class FinanceReportRepository:
    """Repository for finance report history operations."""

    def __init__(self, supabase_client: Client):
        """
        Initialize repository with Supabase client.

        Args:
            supabase_client: Supabase client instance.
        """
        self.db = supabase_client
        self.table_name = "finance_reports"

    async def generate_report_id(self, country: str) -> str:
        """
        Generate next report ID using database function.

        Args:
            country: Country code ('CO' or 'MX').

        Returns:
            str: Generated report ID (e.g., FIN-CO-2025-0001).
        """
        try:
            response = self.db.rpc(
                'generate_finance_report_id',
                {'p_country': country}
            ).execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error generating report ID: {e}")
            # Fallback: generate ID manually
            year = datetime.now().strftime("%Y")
            timestamp = datetime.now().strftime("%H%M%S")
            return f"FIN-{country}-{year}-{timestamp}"

    async def create(self, report_data: dict) -> Optional[dict]:
        """
        Create new finance report record.

        Args:
            report_data: Report data including country, stats, etc.

        Returns:
            dict: Created report record or None if failed.
        """
        try:
            # Generate report_id if not provided
            if 'report_id' not in report_data:
                country = report_data.get('country', 'CO')
                report_data['report_id'] = await self.generate_report_id(country)

            response = self.db.table(self.table_name)\
                .insert(report_data)\
                .execute()

            if response.data:
                logger.info(f"Created finance report: {report_data.get('report_id')}")
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error creating finance report: {e}")
            return None

    async def get_by_id(self, report_id: str) -> Optional[dict]:
        """
        Get report by UUID.

        Args:
            report_id: Report UUID.

        Returns:
            Optional[dict]: Report record.
        """
        try:
            response = self.db.table(self.table_name)\
                .select('*')\
                .eq('id', report_id)\
                .execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error getting report by ID: {e}")
            return None

    async def get_by_report_id(self, report_id: str) -> Optional[dict]:
        """
        Get report by business report ID (e.g., FIN-CO-2025-0001).

        Args:
            report_id: Business report ID.

        Returns:
            Optional[dict]: Report record.
        """
        try:
            response = self.db.table(self.table_name)\
                .select('*')\
                .eq('report_id', report_id)\
                .execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error getting report by report_id: {e}")
            return None

    async def update_status(
        self,
        report_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[dict]:
        """
        Update report status.

        Args:
            report_id: Report UUID.
            status: New status.
            error_message: Optional error message for failed status.

        Returns:
            Optional[dict]: Updated report record.
        """
        try:
            update_data = {"status": status}
            if error_message:
                update_data["error_message"] = error_message

            response = self.db.table(self.table_name)\
                .update(update_data)\
                .eq('id', report_id)\
                .execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error updating report status: {e}")
            return None

    async def get_history(
        self,
        filters: FinanceHistoryFilter
    ) -> tuple[List[dict], int]:
        """
        Get report history with filters and pagination.

        Args:
            filters: Filter parameters.

        Returns:
            Tuple of (list of reports, total count).
        """
        try:
            # Build query
            query = self.db.table(self.table_name).select('*', count='exact')

            # Apply filters
            if filters.country:
                query = query.eq('country', filters.country.value)

            if filters.report_type:
                query = query.eq('report_type', filters.report_type.value)

            if filters.status:
                query = query.eq('status', filters.status.value)

            if filters.generated_by:
                query = query.eq('generated_by', filters.generated_by)

            if filters.date_from:
                query = query.gte('generated_at', filters.date_from.isoformat())

            if filters.date_to:
                query = query.lte('generated_at', filters.date_to.isoformat())

            # Order by most recent first
            query = query.order('generated_at', desc=True)

            # Apply pagination
            query = query.range(
                filters.offset,
                filters.offset + filters.limit - 1
            )

            response = query.execute()

            total_count = response.count if response.count else 0
            reports = response.data if response.data else []

            return reports, total_count

        except Exception as e:
            logger.error(f"Error getting report history: {e}")
            return [], 0

    async def get_stats(
        self,
        country: Optional[str] = None
    ) -> dict:
        """
        Get statistics for finance reports.

        Args:
            country: Optional country filter.

        Returns:
            dict: Statistics dictionary.
        """
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=now.weekday())
            month_start = today_start.replace(day=1)

            stats = {
                "total_reports": 0,
                "reports_today": 0,
                "reports_this_week": 0,
                "reports_this_month": 0,
                "co_reports": 0,
                "mx_reports": 0,
                "facturacion_count": 0,
                "consulta_count": 0,
                "zip_download_count": 0,
                "completed_count": 0,
                "failed_count": 0
            }

            # Total reports
            query = self.db.table(self.table_name).select('*', count='exact')
            if country:
                query = query.eq('country', country)
            response = query.execute()
            stats["total_reports"] = response.count or 0

            # Reports today
            query = self.db.table(self.table_name).select('*', count='exact')\
                .gte('generated_at', today_start.isoformat())
            if country:
                query = query.eq('country', country)
            response = query.execute()
            stats["reports_today"] = response.count or 0

            # Reports this week
            query = self.db.table(self.table_name).select('*', count='exact')\
                .gte('generated_at', week_start.isoformat())
            if country:
                query = query.eq('country', country)
            response = query.execute()
            stats["reports_this_week"] = response.count or 0

            # Reports this month
            query = self.db.table(self.table_name).select('*', count='exact')\
                .gte('generated_at', month_start.isoformat())
            if country:
                query = query.eq('country', country)
            response = query.execute()
            stats["reports_this_month"] = response.count or 0

            # By country (only if not filtering by country)
            if not country:
                response = self.db.table(self.table_name).select('*', count='exact')\
                    .eq('country', 'CO').execute()
                stats["co_reports"] = response.count or 0

                response = self.db.table(self.table_name).select('*', count='exact')\
                    .eq('country', 'MX').execute()
                stats["mx_reports"] = response.count or 0

            # By type
            base_query = self.db.table(self.table_name).select('*', count='exact')
            if country:
                base_query = base_query.eq('country', country)

            for report_type in ['facturacion', 'consulta', 'zip_download']:
                query = self.db.table(self.table_name).select('*', count='exact')\
                    .eq('report_type', report_type)
                if country:
                    query = query.eq('country', country)
                response = query.execute()
                stats[f"{report_type}_count"] = response.count or 0

            # By status
            for status in ['completed', 'failed']:
                query = self.db.table(self.table_name).select('*', count='exact')\
                    .eq('status', status)
                if country:
                    query = query.eq('country', country)
                response = query.execute()
                stats[f"{status}_count"] = response.count or 0

            return stats

        except Exception as e:
            logger.error(f"Error getting report stats: {e}")
            return {
                "total_reports": 0,
                "reports_today": 0,
                "reports_this_week": 0,
                "reports_this_month": 0,
                "co_reports": 0,
                "mx_reports": 0,
                "facturacion_count": 0,
                "consulta_count": 0,
                "zip_download_count": 0,
                "completed_count": 0,
                "failed_count": 0
            }

    async def get_recent_by_user(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        Get recent reports by a specific user.

        Args:
            user_id: User UUID.
            limit: Maximum number of reports.

        Returns:
            List of report records.
        """
        try:
            response = self.db.table(self.table_name)\
                .select('*')\
                .eq('generated_by', user_id)\
                .order('generated_at', desc=True)\
                .limit(limit)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error getting recent reports by user: {e}")
            return []


# Singleton instance
_finance_report_repo_instance: Optional[FinanceReportRepository] = None


def get_finance_report_repository(supabase_client: Client) -> FinanceReportRepository:
    """
    Get or create finance report repository instance.

    Args:
        supabase_client: Supabase client.

    Returns:
        FinanceReportRepository instance.
    """
    global _finance_report_repo_instance
    if _finance_report_repo_instance is None:
        _finance_report_repo_instance = FinanceReportRepository(supabase_client)
    return _finance_report_repo_instance
