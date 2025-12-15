"""
Payment Group Aggregator for Treasury Declaration-Historial Matching.

Groups HistorialRecords by (cliente_normalized, fecha_pago) and sums capital amounts.
"""

import logging
import uuid
from typing import List, Dict
from collections import defaultdict

from src.interface.treasury_matching_dtos import (
    HistorialRecord,
    PaymentGroup,
)

logger = logging.getLogger(__name__)


class PaymentGroupAggregator:
    """
    Service for grouping payment records by customer and date.

    Groups records by (cliente_normalized, fecha_pago) and aggregates:
    - Sum of capital amounts
    - List of original row numbers
    - First record's metadata (cliente, identificacion_cliente, moneda)
    """

    def aggregate_payments(
        self,
        records: List[HistorialRecord]
    ) -> List[PaymentGroup]:
        """
        Group payment records by (cliente_normalized, fecha_pago).

        Args:
            records: List of parsed HistorialRecords

        Returns:
            List of PaymentGroup aggregations
        """
        logger.info(f"Aggregating {len(records)} payment records into groups")

        # Group by (cliente_normalized, fecha_pago)
        groups: Dict[str, Dict] = defaultdict(lambda: {
            'records': [],
            'total_capital': 0.0,
            'row_numbers': [],
        })

        for record in records:
            # Create grouping key
            key = f"{record.cliente_normalized}|{record.fecha_pago}"

            groups[key]['records'].append(record)
            groups[key]['total_capital'] += record.capital
            groups[key]['row_numbers'].append(record.row_number)

        # Convert to PaymentGroup objects
        payment_groups: List[PaymentGroup] = []

        for key, group_data in groups.items():
            first_record = group_data['records'][0]

            payment_group = PaymentGroup(
                group_id=str(uuid.uuid4()),
                cliente=first_record.cliente,
                cliente_normalized=first_record.cliente_normalized,
                identificacion_cliente=first_record.identificacion_cliente,
                fecha_pago=first_record.fecha_pago,
                total_capital=round(group_data['total_capital'], 2),
                record_count=len(group_data['records']),
                record_row_numbers=sorted(group_data['row_numbers']),
                moneda=first_record.moneda,
            )

            payment_groups.append(payment_group)

        # Sort by date descending, then by customer name
        payment_groups.sort(key=lambda g: (g.fecha_pago, g.cliente_normalized), reverse=True)

        logger.info(
            f"Created {len(payment_groups)} payment groups from {len(records)} records. "
            f"Average records per group: {len(records) / max(len(payment_groups), 1):.1f}"
        )

        return payment_groups

    def get_group_statistics(
        self,
        groups: List[PaymentGroup]
    ) -> Dict:
        """
        Calculate statistics about the payment groups.

        Args:
            groups: List of PaymentGroups

        Returns:
            Dictionary with statistics
        """
        if not groups:
            return {
                'total_groups': 0,
                'total_records': 0,
                'total_capital': 0.0,
                'avg_capital_per_group': 0.0,
                'max_records_in_group': 0,
                'single_record_groups': 0,
                'multi_record_groups': 0,
            }

        total_records = sum(g.record_count for g in groups)
        total_capital = sum(g.total_capital for g in groups)
        max_records = max(g.record_count for g in groups)
        single_record_groups = sum(1 for g in groups if g.record_count == 1)
        multi_record_groups = sum(1 for g in groups if g.record_count > 1)

        return {
            'total_groups': len(groups),
            'total_records': total_records,
            'total_capital': round(total_capital, 2),
            'avg_capital_per_group': round(total_capital / len(groups), 2),
            'max_records_in_group': max_records,
            'single_record_groups': single_record_groups,
            'multi_record_groups': multi_record_groups,
        }


# Singleton instance
payment_group_aggregator = PaymentGroupAggregator()
