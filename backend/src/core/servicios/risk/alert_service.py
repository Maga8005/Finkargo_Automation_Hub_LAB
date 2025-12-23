"""
Alert Service
Handles risk alert notifications and management
"""
import logging
from typing import List, Optional

from src.interface.risk_dtos import AlertType, AlertSeverity
from src.repositorio.risk_repository import AlertRepository

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service for managing risk alerts and notifications.

    Handles:
    - Creating alerts for risk events
    - Retrieving active alerts
    - Marking alerts as read
    - Future: Email/Slack notifications
    """

    def __init__(self, alert_repo: AlertRepository):
        """
        Initialize alert service

        Args:
            alert_repo: Alert repository for database operations
        """
        self.alert_repo = alert_repo

    async def create_alert(
        self,
        assessment_id: Optional[str],
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str
    ) -> dict:
        """
        Create a new risk alert

        Args:
            assessment_id: Related assessment UUID (optional)
            alert_type: Type of alert
            severity: Alert severity level
            title: Short alert title
            message: Detailed alert message

        Returns:
            dict: Created alert record
        """
        logger.info(f"Creating alert: type={alert_type.value}, severity={severity.value}, title={title[:50]}...")

        alert_data = {
            'assessment_id': assessment_id,
            'alert_type': alert_type.value,
            'severity': severity.value,
            'title': title,
            'message': message,
            'is_read': False,
        }

        alert = await self.alert_repo.create(alert_data)

        # Future: Send notifications based on severity
        if severity == AlertSeverity.CRITICAL:
            await self._send_critical_notification(alert)

        return alert

    async def get_active_alerts(self, limit: int = 20) -> List[dict]:
        """
        Get active (unread) alerts ordered by severity and date

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List[dict]: Unread alerts
        """
        return await self.alert_repo.get_unread(limit=limit)

    async def get_all_alerts(self, limit: int = 50, include_read: bool = False) -> List[dict]:
        """
        Get all alerts with optional read filter

        Args:
            limit: Maximum number of alerts
            include_read: Include read alerts

        Returns:
            List[dict]: Alert records
        """
        return await self.alert_repo.get_all(limit=limit, include_read=include_read)

    async def mark_alert_read(self, alert_id: str, user_id: str) -> bool:
        """
        Mark an alert as read

        Args:
            alert_id: Alert UUID
            user_id: User who read the alert

        Returns:
            bool: True if successful
        """
        logger.info(f"Marking alert {alert_id} as read by user {user_id}")
        return await self.alert_repo.mark_read(alert_id, user_id)

    async def get_alerts_for_assessment(self, assessment_id: str) -> List[dict]:
        """
        Get all alerts for a specific assessment

        Args:
            assessment_id: Assessment UUID

        Returns:
            List[dict]: Alerts for the assessment
        """
        return await self.alert_repo.get_by_assessment(assessment_id)

    async def create_escalation_alert(
        self,
        assessment_id: str,
        client_nit: str,
        escalated_by: str,
        notes: str = None
    ) -> dict:
        """
        Create an escalation alert when an assessment is escalated

        Args:
            assessment_id: Assessment UUID
            client_nit: Client NIT
            escalated_by: User who escalated
            notes: Optional escalation notes

        Returns:
            dict: Created alert
        """
        title = f"Evaluación escalada - {client_nit}"
        message = f"La evaluación de riesgo para el cliente {client_nit} ha sido escalada para revisión adicional."
        if notes:
            message += f"\n\nNotas: {notes}"

        return await self.create_alert(
            assessment_id=assessment_id,
            alert_type=AlertType.ESCALATION,
            severity=AlertSeverity.WARNING,
            title=title,
            message=message
        )

    async def create_threshold_alert(
        self,
        assessment_id: str,
        client_nit: str,
        score: float,
        threshold: str
    ) -> dict:
        """
        Create an alert when a risk threshold is breached

        Args:
            assessment_id: Assessment UUID
            client_nit: Client NIT
            score: Current risk score
            threshold: Threshold that was breached

        Returns:
            dict: Created alert
        """
        title = f"Umbral de riesgo superado - {client_nit}"
        message = f"El cliente {client_nit} ha superado el umbral de riesgo '{threshold}' con un puntaje de {score:.2f}."

        severity = AlertSeverity.WARNING if threshold == 'high' else AlertSeverity.CRITICAL

        return await self.create_alert(
            assessment_id=assessment_id,
            alert_type=AlertType.THRESHOLD_BREACH,
            severity=severity,
            title=title,
            message=message
        )

    async def _send_critical_notification(self, alert: dict):
        """
        Send notification for critical alerts (placeholder for future implementation)

        Args:
            alert: Alert record
        """
        # Future implementation:
        # - Send email to risk team
        # - Send Slack notification
        # - Send push notification
        logger.warning(
            f"CRITICAL ALERT: {alert.get('title', 'No title')} - "
            f"Message: {alert.get('message', 'No message')[:100]}..."
        )

        # Placeholder for email sending
        # await self._send_email_notification(
        #     to=['risk-team@finkargo.com'],
        #     subject=f"[CRÍTICO] {alert.get('title')}",
        #     body=alert.get('message')
        # )

    async def get_alert_summary(self) -> dict:
        """
        Get a summary of alert statistics

        Returns:
            dict: Alert statistics
        """
        all_alerts = await self.alert_repo.get_all(limit=1000, include_read=True)

        unread_count = sum(1 for a in all_alerts if not a.get('is_read', False))
        critical_count = sum(1 for a in all_alerts if a.get('severity') == 'critical' and not a.get('is_read', False))
        warning_count = sum(1 for a in all_alerts if a.get('severity') == 'warning' and not a.get('is_read', False))

        return {
            'total': len(all_alerts),
            'unread': unread_count,
            'critical_unread': critical_count,
            'warning_unread': warning_count,
        }
