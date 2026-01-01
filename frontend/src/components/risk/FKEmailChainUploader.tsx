/**
 * FKEmailChainUploader - Email chain upload and validation component
 *
 * Allows users to:
 * - Upload email chains via file (.eml, .msg, .pdf) or paste text
 * - View parsed email data
 * - Trigger validation against document data
 * - View validation results with discrepancy indicators
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  Divider,
  Chip,
  Tooltip,
  List,
  ListItem,
  ListItemSecondaryAction,
  Collapse,
  Paper,
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  VerifiedUser,
  Email,
  ExpandMore,
  ExpandLess,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  AttachFile,
  ContentPaste,
} from '@mui/icons-material';
import { riskService } from '../../services/riskService';
import { extractErrorMessage } from '../../utils/errorUtils';
import type {
  EmailChainValidationStatus,
  EmailChainWithValidations,
  EmailChainListWithValidationsResponse,
  EmailChainDiscrepancyValidationRequest,
} from '../../types/risk';
import { EMAIL_CHAIN_VALIDATION_STATUS_CONFIG } from '../../types/risk';
import FKEmailChainValidationItem from './FKEmailChainValidationItem';
import { useAuth } from '../../hooks/useAuth';

interface FKEmailChainUploaderProps {
  evaluationId: string;
}

const FKEmailChainUploader: React.FC<FKEmailChainUploaderProps> = ({
  evaluationId,
}) => {
  // Auth context to check user roles
  const { userProfile } = useAuth();

  // State
  const [chains, setChains] = useState<EmailChainWithValidations[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [validatingId, setValidatingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [textContent, setTextContent] = useState('');
  const [expandedChainId, setExpandedChainId] = useState<string | null>(null);
  const [uploadMode, setUploadMode] = useState<'text' | 'file'>('text');
  const [validationProgress, setValidationProgress] = useState<{ validated: number; total: number } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check if user can validate discrepancies
  const canValidate = userProfile?.role &&
    ['admin', 'risk_manager', 'mesa_control'].includes(userProfile.role);

  // Load email chains with validations
  const loadChains = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response: EmailChainListWithValidationsResponse = await riskService.getEmailChainsWithValidations(evaluationId);
      setChains(response.chains);
      if (response.validation_progress) {
        setValidationProgress({
          validated: response.validation_progress.validated_count,
          total: response.validation_progress.total_discrepancies,
        });
      }
    } catch (err) {
      console.error('Error loading email chains:', err);
      setError('Error al cargar las cadenas de email');
    } finally {
      setLoading(false);
    }
  }, [evaluationId]);

  useEffect(() => {
    loadChains();
  }, [loadChains]);

  // Handle text upload
  const handleTextUpload = async () => {
    if (!textContent.trim()) {
      setError('Por favor ingrese el contenido del email');
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const newChain = await riskService.uploadEmailChainText(evaluationId, textContent);
      setChains((prev) => [...prev, newChain]);
      setTextContent('');
      setSuccessMessage('Cadena de email cargada exitosamente');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Error uploading email chain:', err);
      setError(extractErrorMessage(err, 'Error al cargar la cadena de email'));
    } finally {
      setUploading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.eml') && !fileName.endsWith('.msg') && !fileName.endsWith('.pdf')) {
      setError('Solo se aceptan archivos .eml, .msg o .pdf');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('El archivo es demasiado grande. Máximo 10MB');
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const newChain = await riskService.uploadEmailChainFile(evaluationId, file);
      setChains((prev) => [...prev, newChain]);
      setSuccessMessage(`Archivo "${file.name}" cargado exitosamente`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Error uploading file:', err);
      setError(extractErrorMessage(err, 'Error al cargar el archivo'));
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Handle validate
  const handleValidate = async (chainId: string) => {
    try {
      setValidatingId(chainId);
      setError(null);

      const updatedChain = await riskService.validateEmailChain(evaluationId, chainId);
      setChains((prev) =>
        prev.map((c) => (c.id === chainId ? updatedChain : c))
      );
      setExpandedChainId(chainId); // Expand to show results
      setSuccessMessage('Validación completada');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Error validating chain:', err);
      setError(extractErrorMessage(err, 'Error al validar la cadena'));
    } finally {
      setValidatingId(null);
    }
  };

  // Handle delete
  const handleDelete = async (chainId: string) => {
    try {
      setDeletingId(chainId);
      setError(null);

      await riskService.deleteEmailChain(evaluationId, chainId);
      setChains((prev) => prev.filter((c) => c.id !== chainId));
      setSuccessMessage('Cadena de email eliminada');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Error deleting chain:', err);
      setError(extractErrorMessage(err, 'Error al eliminar la cadena'));
    } finally {
      setDeletingId(null);
    }
  };

  // Toggle expand
  const toggleExpand = (chainId: string) => {
    setExpandedChainId((prev) => (prev === chainId ? null : chainId));
  };

  // Handle discrepancy validation
  const handleValidateDiscrepancy = async (
    chainId: string,
    discrepancyIndex: number,
    request: EmailChainDiscrepancyValidationRequest
  ) => {
    try {
      await riskService.validateEmailChainDiscrepancy(evaluationId, chainId, discrepancyIndex, request);
      setSuccessMessage('Discrepancia validada correctamente');
      await loadChains(); // Reload to get updated validation state
    } catch (err) {
      console.error('Error validating discrepancy:', err);
      throw new Error(extractErrorMessage(err) || 'Error al validar discrepancia');
    }
  };

  // Handle remove discrepancy validation
  const handleRemoveDiscrepancyValidation = async (chainId: string, discrepancyIndex: number) => {
    try {
      await riskService.removeEmailChainDiscrepancyValidation(evaluationId, chainId, discrepancyIndex);
      setSuccessMessage('Validación removida correctamente');
      await loadChains(); // Reload to get updated validation state
    } catch (err) {
      console.error('Error removing validation:', err);
      throw new Error(extractErrorMessage(err) || 'Error al remover validación');
    }
  };

  // Get status icon
  const getStatusIcon = (status: EmailChainValidationStatus) => {
    switch (status) {
      case 'validated':
        return <CheckCircle sx={{ color: '#2CA14D' }} />;
      case 'suspicious':
        return <Warning sx={{ color: '#B86E00' }} />;
      case 'critical':
        return <ErrorIcon sx={{ color: '#CC071E' }} />;
      default:
        return null;
    }
  };

  // Count suspicious/critical
  const alertCount = chains.filter(
    (c) => c.validation_status === 'suspicious' || c.validation_status === 'critical'
  ).length;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Info Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          Suba cadenas de email recibidas durante negociaciones comerciales para validar
          automáticamente la información del remitente contra los documentos de la empresa.
          El sistema detectará discrepancias en dominios, nombres de empresa, NITs y representantes legales.
        </Typography>
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Upload Form */}
      <Card sx={{ mb: 3, position: 'relative', zIndex: 1 }}>
        <CardContent sx={{ pr: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CloudUpload /> Subir Cadena de Email
          </Typography>
          <Divider sx={{ mb: 2 }} />

          {/* Mode Toggle */}
          <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
            <Button
              variant={uploadMode === 'text' ? 'contained' : 'outlined'}
              startIcon={<ContentPaste />}
              onClick={() => setUploadMode('text')}
              size="small"
            >
              Pegar Texto
            </Button>
            <Button
              variant={uploadMode === 'file' ? 'contained' : 'outlined'}
              startIcon={<AttachFile />}
              onClick={() => setUploadMode('file')}
              size="small"
            >
              Subir Archivo
            </Button>
          </Box>

          {uploadMode === 'text' ? (
            <>
              <TextField
                multiline
                rows={8}
                fullWidth
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder={`Pegue aquí el contenido del email...

Ejemplo:
From: contacto@empresa.com
To: comercial@finkargo.com
Date: Mon, 23 Dec 2024 10:00:00 -0500
Subject: Solicitud de Pago

Estimados,
Por favor proceder con el pago...`}
                disabled={uploading}
                sx={{
                  mb: 2,
                  '& .MuiInputBase-root': {
                    overflow: 'auto',
                  },
                }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', pr: 1 }}>
                <Button
                  variant="contained"
                  startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
                  onClick={handleTextUpload}
                  disabled={uploading || !textContent.trim()}
                >
                  Subir
                </Button>
              </Box>
            </>
          ) : (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <input
                type="file"
                accept=".eml,.msg,.pdf"
                ref={fileInputRef}
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              <Button
                variant="outlined"
                size="large"
                startIcon={uploading ? <CircularProgress size={24} /> : <AttachFile />}
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                sx={{ py: 2, px: 4 }}
              >
                {uploading ? 'Subiendo...' : 'Seleccionar archivo .eml, .msg o .pdf'}
              </Button>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                Máximo 10MB
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Chains List */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Email /> Cadenas de Email
              {chains.length > 0 && (
                <Chip label={chains.length} size="small" color="primary" />
              )}
            </Typography>
            {alertCount > 0 && (
              <Chip
                label={`${alertCount} alerta${alertCount > 1 ? 's' : ''}`}
                color="error"
                size="small"
                icon={<Warning />}
              />
            )}
            {validationProgress && validationProgress.total > 0 && (
              <Chip
                label={`Validados: ${validationProgress.validated}/${validationProgress.total}`}
                size="small"
                color={validationProgress.validated >= validationProgress.total ? 'success' : 'default'}
                icon={<CheckCircle />}
              />
            )}
          </Box>
          <Divider sx={{ mb: 2 }} />

          {chains.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Email sx={{ fontSize: 48, color: 'action.disabled', mb: 1 }} />
              <Typography color="text.secondary">
                No hay cadenas de email cargadas
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Suba emails para validar contra los documentos
              </Typography>
            </Box>
          ) : (
            <List sx={{ '& .MuiListItem-root': { px: 0 } }}>
              {chains.map((chain, index) => {
                const statusConfig = EMAIL_CHAIN_VALIDATION_STATUS_CONFIG[chain.validation_status];
                const isValidating = validatingId === chain.id;
                const isDeleting = deletingId === chain.id;
                const isExpanded = expandedChainId === chain.id;

                // Get sender info from first message
                const firstMessage = chain.parsed_data?.messages?.[0];
                const senderEmail = firstMessage?.sender_email || 'Email no disponible';
                const senderDomain = firstMessage?.sender_domain || '';
                const subject = firstMessage?.subject || 'Sin asunto';

                return (
                  <React.Fragment key={chain.id}>
                    {index > 0 && <Divider sx={{ my: 2 }} />}
                    <ListItem
                      sx={{
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        gap: 1,
                      }}
                    >
                      <Box sx={{ display: 'flex', width: '100%', alignItems: 'center', gap: 2 }}>
                        <Box sx={{ flex: 1, cursor: 'pointer' }} onClick={() => toggleExpand(chain.id)}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getStatusIcon(chain.validation_status)}
                            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                              {senderEmail}
                            </Typography>
                            <Chip
                              label={statusConfig.label}
                              size="small"
                              sx={{
                                backgroundColor: statusConfig.bgColor,
                                color: statusConfig.textColor,
                                fontSize: '0.7rem',
                              }}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {subject}
                          </Typography>
                          {chain.original_filename && (
                            <Typography variant="caption" color="text.secondary">
                              <AttachFile sx={{ fontSize: 12, mr: 0.5, verticalAlign: 'middle' }} />
                              {chain.original_filename}
                            </Typography>
                          )}
                        </Box>

                        <ListItemSecondaryAction sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title={isExpanded ? "Contraer" : "Expandir"}>
                            <IconButton size="small" onClick={() => toggleExpand(chain.id)}>
                              {isExpanded ? <ExpandLess /> : <ExpandMore />}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Validar contra documentos">
                            <span>
                              <Button
                                variant="outlined"
                                size="small"
                                startIcon={
                                  isValidating ? (
                                    <CircularProgress size={16} />
                                  ) : (
                                    <VerifiedUser />
                                  )
                                }
                                onClick={() => handleValidate(chain.id)}
                                disabled={isValidating || isDeleting}
                              >
                                Validar
                              </Button>
                            </span>
                          </Tooltip>
                          <Tooltip title="Eliminar">
                            <span>
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDelete(chain.id)}
                                disabled={isValidating || isDeleting}
                              >
                                {isDeleting ? (
                                  <CircularProgress size={20} />
                                ) : (
                                  <Delete />
                                )}
                              </IconButton>
                            </span>
                          </Tooltip>
                        </ListItemSecondaryAction>
                      </Box>

                      {/* Expanded Details */}
                      <Collapse in={isExpanded} sx={{ width: '100%' }}>
                        <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
                          {/* Parsed Data */}
                          {chain.parsed_data && (
                            <Box sx={{ mb: 2 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Datos Extraídos
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {senderDomain && (
                                  <Chip label={`Dominio: ${senderDomain}`} size="small" variant="outlined" />
                                )}
                                {chain.parsed_data.mentions?.company_names?.map((c, i) => (
                                  <Chip key={`company-${i}`} label={`Empresa: ${c}`} size="small" variant="outlined" />
                                ))}
                                {chain.parsed_data.mentions?.nits?.map((n, i) => (
                                  <Chip key={`nit-${i}`} label={`NIT: ${n}`} size="small" variant="outlined" />
                                ))}
                                {chain.parsed_data.mentions?.representative_names?.map((r, i) => (
                                  <Chip key={`rep-${i}`} label={`Rep: ${r}`} size="small" variant="outlined" />
                                ))}
                              </Box>
                              {chain.parsed_data.parse_errors?.length > 0 && (
                                <Alert severity="warning" sx={{ mt: 1 }}>
                                  {chain.parsed_data.parse_errors.join(', ')}
                                </Alert>
                              )}
                            </Box>
                          )}

                          {/* Validation Results */}
                          {chain.validation_result && (
                            <Box>
                              <Typography variant="subtitle2" gutterBottom>
                                Resultados de Validación
                              </Typography>
                              <Alert
                                severity={
                                  chain.validation_status === 'critical' ? 'error' :
                                  chain.validation_status === 'suspicious' ? 'warning' : 'success'
                                }
                                sx={{ mb: 2 }}
                              >
                                {chain.validation_result.summary}
                              </Alert>

                              {chain.validation_result.discrepancies?.length > 0 && (
                                <Box>
                                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                                    {chain.validation_result.discrepancies.length} discrepancia{chain.validation_result.discrepancies.length > 1 ? 's' : ''} encontrada{chain.validation_result.discrepancies.length > 1 ? 's' : ''}
                                  </Typography>
                                  {chain.validation_result.discrepancies.map((disc, i) => (
                                    <FKEmailChainValidationItem
                                      key={i}
                                      discrepancy={disc}
                                      discrepancyIndex={i}
                                      chainId={chain.id}
                                      canValidate={canValidate ?? false}
                                      onValidate={handleValidateDiscrepancy}
                                      onRemoveValidation={handleRemoveDiscrepancyValidation}
                                    />
                                  ))}
                                </Box>
                              )}
                            </Box>
                          )}
                        </Paper>
                      </Collapse>
                    </ListItem>
                  </React.Fragment>
                );
              })}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default FKEmailChainUploader;
