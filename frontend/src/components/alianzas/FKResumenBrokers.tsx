/**
 * FKResumenBrokers - Summary table showing commission totals aggregated by broker
 */
import React, { useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Skeleton,
} from '@mui/material';

import type { ComisionCalculada, ComisionResumenBroker } from '../../types/alianzas';

interface FKResumenBrokersProps {
  comisiones: ComisionCalculada[];
  resumenFromApi?: ComisionResumenBroker[];
  loading?: boolean;
}

/**
 * Simple broker summary computed from commission list
 * Used when we don't have the API response for summaries
 */
interface SimpleBrokerSummary {
  broker_id: string;
  broker_nombre: string;
  total_clientes: number;
  total_usd: number;
  total_mxn: number;
}

const FKResumenBrokers: React.FC<FKResumenBrokersProps> = ({
  comisiones,
  resumenFromApi,
  loading = false,
}) => {
  // Format currency for display
  const formatCurrency = (value: number, currency: 'USD' | 'MXN'): string => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Compute summary from commissions if API response not available
  const computedSummary = useMemo((): SimpleBrokerSummary[] => {
    if (resumenFromApi && resumenFromApi.length > 0) {
      // Convert API response to simple summary format
      return resumenFromApi.map((r) => ({
        broker_id: r.broker_id,
        broker_nombre: r.broker_nombre,
        total_clientes: r.num_comisiones,
        total_usd: r.total_usd,
        total_mxn: r.total_mxn,
      }));
    }

    // Compute from commissions list
    const brokerMap = new Map<string, SimpleBrokerSummary>();

    comisiones.forEach((comision) => {
      const existing = brokerMap.get(comision.broker_id);
      if (existing) {
        existing.total_clientes += 1;
        existing.total_usd += comision.monto_broker_usd;
        existing.total_mxn += comision.monto_broker_mxn;
      } else {
        brokerMap.set(comision.broker_id, {
          broker_id: comision.broker_id,
          broker_nombre: comision.broker_nombre || comision.broker_id.substring(0, 8),
          total_clientes: 1,
          total_usd: comision.monto_broker_usd,
          total_mxn: comision.monto_broker_mxn,
        });
      }
    });

    return Array.from(brokerMap.values()).sort((a, b) =>
      a.broker_nombre.localeCompare(b.broker_nombre)
    );
  }, [comisiones, resumenFromApi]);

  // Compute grand totals
  const grandTotals = useMemo(() => {
    return computedSummary.reduce(
      (acc, broker) => ({
        total_clientes: acc.total_clientes + broker.total_clientes,
        total_usd: acc.total_usd + broker.total_usd,
        total_mxn: acc.total_mxn + broker.total_mxn,
      }),
      { total_clientes: 0, total_usd: 0, total_mxn: 0 }
    );
  }, [computedSummary]);

  if (loading) {
    return (
      <Box>
        <Skeleton variant="rectangular" height={200} />
      </Box>
    );
  }

  if (computedSummary.length === 0) {
    return (
      <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No hay comisiones para mostrar el resumen
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
        RESUMEN POR BROKER
      </Typography>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: 'grey.100' }}>
              <TableCell>
                <Typography variant="subtitle2">Broker</Typography>
              </TableCell>
              <TableCell align="center">
                <Typography variant="subtitle2">Registros</Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="subtitle2">Total USD</Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="subtitle2">Total MXN</Typography>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {computedSummary.map((broker) => (
              <TableRow
                key={broker.broker_id}
                sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
              >
                <TableCell>
                  <Typography variant="body2">{broker.broker_nombre}</Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2">{broker.total_clientes}</Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2" fontWeight={500}>
                    {formatCurrency(broker.total_usd, 'USD')}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2" fontWeight={500}>
                    {formatCurrency(broker.total_mxn, 'MXN')}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}

            {/* Grand Total Row */}
            <TableRow
              sx={{
                backgroundColor: 'primary.50',
                '& td': { borderTop: '2px solid', borderTopColor: 'primary.main' },
              }}
            >
              <TableCell>
                <Typography variant="subtitle2" fontWeight={700}>
                  TOTAL PERÍODO
                </Typography>
              </TableCell>
              <TableCell align="center">
                <Typography variant="subtitle2" fontWeight={700}>
                  {grandTotals.total_clientes}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="subtitle2" fontWeight={700} color="primary.main">
                  {formatCurrency(grandTotals.total_usd, 'USD')}
                </Typography>
              </TableCell>
              <TableCell align="right">
                <Typography variant="subtitle2" fontWeight={700} color="primary.main">
                  {formatCurrency(grandTotals.total_mxn, 'MXN')}
                </Typography>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary line below table */}
      <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="body1" fontWeight={600} textAlign="center">
          TOTAL PERÍODO:{' '}
          <Typography component="span" color="primary.main" fontWeight={700}>
            {formatCurrency(grandTotals.total_usd, 'USD')}
          </Typography>
          {' | '}
          <Typography component="span" color="primary.main" fontWeight={700}>
            {formatCurrency(grandTotals.total_mxn, 'MXN')}
          </Typography>
        </Typography>
      </Box>
    </Box>
  );
};

export default FKResumenBrokers;
