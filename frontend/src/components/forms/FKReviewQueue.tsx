/**
 * FKReviewQueue - Contract review queue for Legal team
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Refresh as RefreshIcon,
  PictureAsPdf as PdfIcon,
  Description as DocIcon,
} from '@mui/icons-material';
import { legalService } from '../../services/legalService';
import type { ContractGeneration } from '../../types/legal';

const FKReviewQueue: React.FC = () => {
  const [contracts, setContracts] = useState<ContractGeneration[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedContract, setSelectedContract] = useState<ContractGeneration | null>(null);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject' | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    loadPendingReviews();
  }, []);

  const loadPendingReviews = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await legalService.getPendingReviews();
      setContracts(data);
    } catch (err) {
      setError('Error al cargar contratos pendientes');
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenReview = (contract: ContractGeneration, action: 'approve' | 'reject') => {
    setSelectedContract(contract);
    setReviewAction(action);
    setReviewNotes('');
    setReviewDialogOpen(true);
  };

  const handleCloseReview = () => {
    setReviewDialogOpen(false);
    setSelectedContract(null);
    setReviewAction(null);
    setReviewNotes('');
  };

  const handleSubmitReview = async () => {
    if (!selectedContract || !reviewAction) return;

    setSubmitting(true);
    setError(null);

    try {
      // Use UUID for API operations, display business ID to users
      await legalService.reviewContract(selectedContract.id, {
        action: reviewAction,
        notes: reviewNotes || undefined,
      });

      setSuccess(
        reviewAction === 'approve'
          ? `Contrato ${selectedContract.contract_id} aprobado exitosamente`
          : `Contrato ${selectedContract.contract_id} rechazado`
      );

      handleCloseReview();
      loadPendingReviews(); // Reload the list
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || 'Error al procesar la revisión');
      console.error('Review error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownload = async (contractId: string, format: 'pdf' | 'docx') => {
    setDownloading(contractId);
    setError(null);

    try {
      let blob: Blob;
      let filename: string;

      if (format === 'pdf') {
        blob = await legalService.downloadContractPDF(contractId);
        const contract = contracts.find(c => c.id === contractId);
        filename = `${contract?.contract_id || 'contrato'}.pdf`;
      } else {
        blob = await legalService.downloadContractDOCX(contractId);
        const contract = contracts.find(c => c.id === contractId);
        filename = `${contract?.contract_id || 'contrato'}.docx`;
      }

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess(`Documento descargado: ${filename}`);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      setError(axiosError.response?.data?.detail || `Error al descargar ${format.toUpperCase()}`);
      console.error('Download error:', err);
    } finally {
      setDownloading(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CO', {
      year: 'numeric',
      month: 'short',
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

  const getContractTypeBadge = (contractType: string) => {
    // Paga Local Colombia - Crédito contracts
    if (contractType === 'pl_co_credito_no_aval') {
      return { label: 'PL Crédito No Aval', color: 'warning' as const };
    }
    if (contractType === 'pl_co_credito_aval_pj') {
      return { label: 'PL Crédito Aval PJ', color: 'primary' as const };
    }
    if (contractType === 'pl_co_credito_aval_pn') {
      return { label: 'PL Crédito Aval PN', color: 'secondary' as const };
    }
    // Paga Local Colombia - Mandato contracts
    if (contractType === 'pl_co_mandato_no_aval') {
      return { label: 'PL Mandato No Aval', color: 'warning' as const };
    }
    if (contractType === 'pl_co_mandato_pj') {
      return { label: 'PL Mandato PJ', color: 'primary' as const };
    }
    if (contractType === 'pl_co_mandato_pn') {
      return { label: 'PL Mandato PN', color: 'secondary' as const };
    }
    // Paga Local Colombia - Operation documents
    if (contractType === 'pl_co_mandato_im') {
      return { label: 'PL Mandato (IM)', color: 'info' as const };
    }
    if (contractType === 'pl_co_solicitud_desembolso') {
      return { label: 'PL Solicitud Desembolso', color: 'success' as const };
    }
    if (contractType === 'pl_co_dian_mandato_im') {
      return { label: 'PL DIAN Mandato', color: 'error' as const };
    }
    // Other contract types
    if (contractType === 'otrosi') {
      return { label: 'Otrosí No. 1', color: 'warning' as const };
    }
    if (contractType === 'inventario_bodega') {
      return { label: 'Inventario Bodega 3ro', color: 'success' as const };
    }
    return { label: 'Activos', color: 'info' as const };
  };

  return (
    <Box>
      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Contratos Pendientes de Revisión
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {contracts.length} contrato{contracts.length !== 1 ? 's' : ''} esperando revisión legal
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadPendingReviews}
          disabled={loading}
        >
          Actualizar
        </Button>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Empty State */}
      {!loading && contracts.length === 0 && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary">
              No hay contratos pendientes de revisión
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Todos los contratos han sido revisados
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Contract List */}
      {!loading && contracts.length > 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {contracts.map((contract) => {
            const snapshot = contract.data_snapshot;
            return (
              <Card key={contract.id}>
                <CardContent>
                  <Grid container spacing={2}>
                    {/* Header Row */}
                    <Grid size={{ xs: 12 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {contract.contract_id}
                            </Typography>
                            {(() => {
                              const badge = getContractTypeBadge(contract.contract_type || 'activos');
                              return (
                                <Chip
                                  label={badge.label}
                                  color={badge.color}
                                  size="small"
                                  sx={{ fontWeight: 500 }}
                                />
                              );
                            })()}
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Generado: {formatDate(contract.generated_at)}
                          </Typography>
                        </Box>
                        <Chip label={contract.status} color="warning" />
                      </Box>
                    </Grid>

                    {/* Client Info */}
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">
                        Importador
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {snapshot?.nombre_importador}
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 12, md: 3 }}>
                      <Typography variant="body2" color="text.secondary">
                        NIT
                      </Typography>
                      <Typography variant="body1">{contract.client_nit}</Typography>
                    </Grid>

                    <Grid size={{ xs: 12, md: 3 }}>
                      <Typography variant="body2" color="text.secondary">
                        Cupo
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600, color: 'primary.main' }}>
                        {formatCurrency(snapshot?.cupo_plataforma || 0)}
                      </Typography>
                    </Grid>

                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">
                        Representante Legal
                      </Typography>
                      <Typography variant="body1">{snapshot?.representante_legal}</Typography>
                    </Grid>

                    <Grid size={{ xs: 12, md: 6 }}>
                      <Typography variant="body2" color="text.secondary">
                        Ciudad
                      </Typography>
                      <Typography variant="body1">{snapshot?.ciudad_domicilio}</Typography>
                    </Grid>

                    {/* Actions */}
                    <Grid size={{ xs: 12 }}>
                      <Divider sx={{ my: 1 }} />
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'space-between', mt: 2, flexWrap: 'wrap' }}>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            variant="outlined"
                            startIcon={downloading === contract.id ? <CircularProgress size={16} /> : <DocIcon />}
                            size="small"
                            onClick={() => handleDownload(contract.id, 'docx')}
                            disabled={downloading === contract.id}
                          >
                            DOCX
                          </Button>
                          <Button
                            variant="outlined"
                            startIcon={downloading === contract.id ? <CircularProgress size={16} /> : <PdfIcon />}
                            size="small"
                            onClick={() => handleDownload(contract.id, 'pdf')}
                            disabled={downloading === contract.id}
                          >
                            PDF
                          </Button>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            variant="outlined"
                            color="error"
                            startIcon={<RejectIcon />}
                            size="small"
                            onClick={() => handleOpenReview(contract, 'reject')}
                          >
                            Rechazar
                          </Button>
                          <Button
                            variant="contained"
                            color="success"
                            startIcon={<ApproveIcon />}
                            size="small"
                            onClick={() => handleOpenReview(contract, 'approve')}
                          >
                            Aprobar
                          </Button>
                        </Box>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            );
          })}
        </Box>
      )}

      {/* Review Dialog */}
      <Dialog open={reviewDialogOpen} onClose={handleCloseReview} maxWidth="sm" fullWidth>
        <DialogTitle>
          {reviewAction === 'approve' ? 'Aprobar Contrato' : 'Rechazar Contrato'}
        </DialogTitle>
        <DialogContent>
          {selectedContract && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Contrato: <strong>{selectedContract.contract_id}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Cliente: <strong>{selectedContract.client_nit}</strong>
              </Typography>
            </Box>
          )}

          <TextField
            fullWidth
            multiline
            rows={4}
            label={reviewAction === 'approve' ? 'Notas (opcional)' : 'Motivo del rechazo'}
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
            placeholder={
              reviewAction === 'approve'
                ? 'Agregue notas si es necesario...'
                : 'Por favor indique el motivo del rechazo...'
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseReview} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            onClick={handleSubmitReview}
            variant="contained"
            color={reviewAction === 'approve' ? 'success' : 'error'}
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={20} /> : null}
          >
            {submitting
              ? 'Procesando...'
              : reviewAction === 'approve'
              ? 'Aprobar'
              : 'Rechazar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FKReviewQueue;
