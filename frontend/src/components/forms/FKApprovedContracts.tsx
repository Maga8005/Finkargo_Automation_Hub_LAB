/**
 * FK Approved Contracts - Operations view for downloading approved contracts
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  PictureAsPdf as PdfIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { operationsService } from '../../services/operationsService';
import type { ContractGeneration } from '../../types/legal';

const FKApprovedContracts: React.FC = () => {
  const [contracts, setContracts] = useState<ContractGeneration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    loadApprovedContracts();
  }, []);

  const loadApprovedContracts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await operationsService.getApprovedContracts();
      setContracts(data);
    } catch (err) {
      console.error('Error loading approved contracts:', err);
      setError('Error al cargar los contratos aprobados');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async (contract: ContractGeneration) => {
    if (!contract.approved_document_url) {
      alert('No hay PDF disponible para este contrato');
      return;
    }

    try {
      setDownloadingId(contract.id);

      // Download via backend API endpoint
      const blob = await operationsService.downloadApprovedContractPdf(contract.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `contrato_${contract.contract_id}_aprobado.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading PDF:', err);
      alert('Error al descargar el PDF');
    } finally {
      setDownloadingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (contracts.length === 0) {
    return (
      <Alert severity="info" icon={<InfoIcon />}>
        No hay contratos aprobados disponibles para descarga.
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Contratos Aprobados ({contracts.length})
        </Typography>
        <Button
          variant="outlined"
          size="small"
          onClick={loadApprovedContracts}
          sx={{ textTransform: 'none' }}
        >
          Actualizar
        </Button>
      </Box>

      <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
        <Table>
          <TableHead sx={{ bgcolor: 'grey.50' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>ID Contrato</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Cliente</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>NIT</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Cupo Aprobado</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Fecha Aprobación</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Estado</TableCell>
              <TableCell align="center" sx={{ fontWeight: 600 }}>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {contracts.map((contract) => (
              <TableRow
                key={contract.id}
                hover
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                    {contract.contract_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {contract.data_snapshot?.nombre_importador || 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{contract.client_nit}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                    {formatCurrency(contract.data_snapshot?.cupo_plataforma || 0)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {contract.reviewed_at ? formatDate(contract.reviewed_at) : 'N/A'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    icon={<CheckCircleIcon />}
                    label="Aprobado"
                    color="success"
                    size="small"
                    sx={{ fontWeight: 500 }}
                  />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Descargar PDF aprobado">
                    <span>
                      <IconButton
                        color="primary"
                        onClick={() => handleDownloadPDF(contract)}
                        disabled={!contract.approved_document_url || downloadingId === contract.id}
                        size="small"
                      >
                        {downloadingId === contract.id ? (
                          <CircularProgress size={20} />
                        ) : (
                          <PdfIcon />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>
                  {!contract.approved_document_url && (
                    <Tooltip title="PDF no disponible">
                      <InfoIcon color="disabled" fontSize="small" sx={{ ml: 1 }} />
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2 }}>
        <Alert severity="info" icon={<InfoIcon />}>
          <Typography variant="body2">
            <strong>Instrucciones:</strong> Haga clic en el ícono <PdfIcon fontSize="small" sx={{ verticalAlign: 'middle' }} /> para descargar el PDF aprobado del contrato. Estos documentos están listos para ser enviados al cliente para su firma.
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default FKApprovedContracts;
