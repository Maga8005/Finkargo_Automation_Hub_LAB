/**
 * FKExternalContactTab - External contact email validation tab
 *
 * Allows users to:
 * - Add external contact emails received via commercial channels
 * - Validate email domains for typosquatting detection
 * - View validation results with similarity scores
 * - Delete contacts
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Divider,
  Chip,
  Tooltip,
  List,
  ListItem,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add,
  Delete,
  VerifiedUser,
  Email,
  Person,
  Business,
  Notes,
  ExpandMore,
  Link as LinkIcon,
} from '@mui/icons-material';
import { riskService } from '../../services/riskService';
import FKEmailValidationResult from './FKEmailValidationResult';
import FKEmailChainUploader from './FKEmailChainUploader';
import FKExternalContactValidationItem from './FKExternalContactValidationItem';
import type {
  ExternalContactRequest,
  ClientInfo,
  ExternalContactWithValidation,
  ExternalContactListWithValidationsResponse,
  ExternalContactValidationRequest,
  EmailChainWithValidations,
} from '../../types/risk';
import { EXTERNAL_CONTACT_SOURCE_LABELS, EXTERNAL_CONTACT_VALIDATION_STATUS_CONFIG } from '../../types/risk';
import { useAuth } from '../../hooks/useAuth';
import { extractErrorMessage } from '../../utils/errorUtils';

interface FKExternalContactTabProps {
  evaluationId: string;
  assessmentId?: string;
  clientInfo?: ClientInfo;
  onEmailChainsUpdate?: (chains: EmailChainWithValidations[]) => void;
}

interface ContactFormData {
  email: string;
  sender_name: string;
  source: string;
  notes: string;
}

const FKExternalContactTab: React.FC<FKExternalContactTabProps> = ({
  evaluationId,
  clientInfo,
  onEmailChainsUpdate,
}) => {
  // Auth context to check user roles
  const { userProfile } = useAuth();

  // State
  const [contacts, setContacts] = useState<ExternalContactWithValidation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [validatingId, setValidatingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [validationProgress, setValidationProgress] = useState<{ validated: number; total: number } | null>(null);

  // Check if user can validate alerts
  const canValidateAlert = userProfile?.role &&
    ['admin', 'risk_manager', 'mesa_control'].includes(userProfile.role);

  // Form setup
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ContactFormData>({
    defaultValues: {
      email: '',
      sender_name: '',
      source: 'comercial_team',
      notes: '',
    },
  });

  // Load contacts with validations
  const loadContacts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response: ExternalContactListWithValidationsResponse = await riskService.getExternalContactsWithValidations(evaluationId);
      setContacts(response.contacts);
      if (response.validation_progress) {
        setValidationProgress({
          validated: response.validation_progress.validated_count,
          total: response.validation_progress.total_alerts,
        });
      }
    } catch (err) {
      console.error('Error loading external contacts:', err);
      setError('Error al cargar los contactos externos');
    } finally {
      setLoading(false);
    }
  }, [evaluationId]);

  useEffect(() => {
    loadContacts();
  }, [loadContacts]);

  // Handle form submit
  const onSubmit = async (data: ContactFormData) => {
    try {
      setSubmitting(true);
      setError(null);

      const request: ExternalContactRequest = {
        email: data.email,
        sender_name: data.sender_name || undefined,
        source: data.source,
        notes: data.notes || undefined,
      };

      const newContact = await riskService.createExternalContact(evaluationId, request);
      setContacts((prev) => [...prev, newContact]);
      reset();
      setSuccessMessage('Contacto agregado exitosamente');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: unknown) {
      console.error('Error creating contact:', err);
      const message = err instanceof Error ? err.message : 'Error al agregar el contacto';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle validate
  const handleValidate = async (contactId: string) => {
    try {
      setValidatingId(contactId);
      setError(null);

      const updatedContact = await riskService.validateExternalContact(evaluationId, contactId);
      setContacts((prev) =>
        prev.map((c) => (c.id === contactId ? updatedContact : c))
      );
      setSuccessMessage('Validación completada');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: unknown) {
      console.error('Error validating contact:', err);
      const message = err instanceof Error ? err.message : 'Error al validar el dominio';
      setError(message);
    } finally {
      setValidatingId(null);
    }
  };

  // Handle delete
  const handleDelete = async (contactId: string) => {
    try {
      setDeletingId(contactId);
      setError(null);

      await riskService.deleteExternalContact(evaluationId, contactId);
      setContacts((prev) => prev.filter((c) => c.id !== contactId));
      setSuccessMessage('Contacto eliminado');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: unknown) {
      console.error('Error deleting contact:', err);
      const message = err instanceof Error ? err.message : 'Error al eliminar el contacto';
      setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  // Handle alert validation
  const handleValidateAlert = async (contactId: string, request: ExternalContactValidationRequest) => {
    try {
      await riskService.validateExternalContactAlert(evaluationId, contactId, request);
      setSuccessMessage('Alerta validada correctamente');
      await loadContacts(); // Reload to get updated validation state
    } catch (err) {
      console.error('Error validating alert:', err);
      throw new Error(extractErrorMessage(err) || 'Error al validar alerta');
    }
  };

  // Handle remove alert validation
  const handleRemoveAlertValidation = async (contactId: string) => {
    try {
      await riskService.removeExternalContactValidation(evaluationId, contactId);
      setSuccessMessage('Validación removida correctamente');
      await loadContacts(); // Reload to get updated validation state
    } catch (err) {
      console.error('Error removing validation:', err);
      throw new Error(extractErrorMessage(err) || 'Error al remover validación');
    }
  };

  // Count suspicious/critical contacts
  const suspiciousCount = contacts.filter(
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
      {/* Company Info */}
      {clientInfo?.nombre_importador && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            <Business sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
            Empresa: {clientInfo.nombre_importador}
          </Typography>
        </Alert>
      )}

      {/* Email Chain Uploader Section */}
      <Accordion defaultExpanded sx={{ mb: 3 }}>
        <AccordionSummary
          expandIcon={<ExpandMore />}
          aria-controls="email-chains-content"
          id="email-chains-header"
        >
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LinkIcon /> Cadenas de Email
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <FKEmailChainUploader evaluationId={evaluationId} onEmailChainsUpdate={onEmailChainsUpdate} />
        </AccordionDetails>
      </Accordion>

      {/* External Contacts Section */}
      <Accordion defaultExpanded>
        <AccordionSummary
          expandIcon={<ExpandMore />}
          aria-controls="contacts-content"
          id="contacts-header"
        >
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Email /> Contactos Externos Individuales
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          {/* Info Alert */}
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              Ingrese los emails de contacto recibidos a través de canales comerciales para validar
              si el dominio coincide con la empresa evaluada. El sistema detectará posibles intentos
              de typosquatting (dominios similares pero fraudulentos).
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

      {/* Add Contact Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Add /> Agregar Contacto Externo
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                {/* Email Field */}
                <Controller
                  name="email"
                  control={control}
                  rules={{
                    required: 'El email es requerido',
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: 'Ingrese un email válido',
                    },
                  }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Email del Remitente"
                      placeholder="contacto@empresa.com"
                      error={!!errors.email}
                      helperText={errors.email?.message}
                      disabled={submitting}
                      sx={{ flex: 2, minWidth: 250 }}
                      InputProps={{
                        startAdornment: <Email sx={{ mr: 1, color: 'action.active' }} />,
                      }}
                    />
                  )}
                />

                {/* Sender Name Field */}
                <Controller
                  name="sender_name"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Nombre del Remitente (Opcional)"
                      placeholder="Juan Pérez"
                      disabled={submitting}
                      sx={{ flex: 1, minWidth: 200 }}
                      InputProps={{
                        startAdornment: <Person sx={{ mr: 1, color: 'action.active' }} />,
                      }}
                    />
                  )}
                />
              </Box>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                {/* Source Select */}
                <Controller
                  name="source"
                  control={control}
                  render={({ field }) => (
                    <FormControl sx={{ minWidth: 200 }}>
                      <InputLabel>Fuente</InputLabel>
                      <Select {...field} label="Fuente" disabled={submitting}>
                        {Object.entries(EXTERNAL_CONTACT_SOURCE_LABELS).map(([value, label]) => (
                          <MenuItem key={value} value={value}>
                            {label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                />

                {/* Notes Field */}
                <Controller
                  name="notes"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Notas (Opcional)"
                      placeholder="Información adicional..."
                      disabled={submitting}
                      sx={{ flex: 1, minWidth: 200 }}
                      InputProps={{
                        startAdornment: <Notes sx={{ mr: 1, color: 'action.active' }} />,
                      }}
                    />
                  )}
                />
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={submitting ? <CircularProgress size={20} /> : <Add />}
                  disabled={submitting}
                >
                  Agregar Contacto
                </Button>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Contacts List */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Email /> Contactos Externos
              {contacts.length > 0 && (
                <Chip label={contacts.length} size="small" color="primary" />
              )}
            </Typography>
            {suspiciousCount > 0 && (
              <Chip
                label={`${suspiciousCount} sospechoso${suspiciousCount > 1 ? 's' : ''}`}
                color="error"
                size="small"
              />
            )}
            {validationProgress && validationProgress.total > 0 && (
              <Chip
                label={`Validados: ${validationProgress.validated}/${validationProgress.total}`}
                size="small"
                color={validationProgress.validated >= validationProgress.total ? 'success' : 'default'}
                icon={<VerifiedUser />}
              />
            )}
          </Box>
          <Divider sx={{ mb: 2 }} />

          {contacts.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Email sx={{ fontSize: 48, color: 'action.disabled', mb: 1 }} />
              <Typography color="text.secondary">
                No hay contactos externos registrados
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Agregue emails recibidos via canales comerciales para validar
              </Typography>
            </Box>
          ) : (
            <Box>
              {/* Suspicious/Critical Contacts - with validation controls */}
              {contacts.filter(c => c.validation_status === 'suspicious' || c.validation_status === 'critical').length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="error.main" sx={{ mb: 1 }}>
                    Contactos con Alertas ({contacts.filter(c => c.validation_status === 'suspicious' || c.validation_status === 'critical').length})
                  </Typography>
                  {contacts
                    .filter(c => c.validation_status === 'suspicious' || c.validation_status === 'critical')
                    .map((contact) => (
                      <FKExternalContactValidationItem
                        key={contact.id}
                        contact={contact}
                        canValidate={canValidateAlert ?? false}
                        onValidate={handleValidateAlert}
                        onRemoveValidation={handleRemoveAlertValidation}
                      />
                    ))}
                </Box>
              )}

              {/* Other contacts - standard list */}
              <List sx={{ '& .MuiListItem-root': { px: 0 } }}>
                {contacts.filter(c => c.validation_status !== 'suspicious' && c.validation_status !== 'critical').map((contact, index) => {
                  const statusConfig = EXTERNAL_CONTACT_VALIDATION_STATUS_CONFIG[contact.validation_status];
                  const isValidating = validatingId === contact.id;
                  const isDeleting = deletingId === contact.id;

                  return (
                    <React.Fragment key={contact.id}>
                      {index > 0 && <Divider sx={{ my: 2 }} />}
                      <ListItem
                        sx={{
                          flexDirection: 'column',
                          alignItems: 'flex-start',
                          gap: 1,
                        }}
                      >
                        <Box sx={{ display: 'flex', width: '100%', alignItems: 'center', gap: 2 }}>
                          <Box sx={{ flex: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                {contact.email}
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
                            {contact.sender_name && (
                              <Typography variant="body2" color="text.secondary">
                                <Person sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                                {contact.sender_name}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary">
                              Fuente: {EXTERNAL_CONTACT_SOURCE_LABELS[contact.source as keyof typeof EXTERNAL_CONTACT_SOURCE_LABELS] || contact.source}
                              {contact.notes && ` • ${contact.notes}`}
                            </Typography>
                          </Box>

                          <ListItemSecondaryAction sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Validar Dominio">
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
                                  onClick={() => handleValidate(contact.id)}
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
                                  onClick={() => handleDelete(contact.id)}
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

                        {/* Validation Result */}
                        {contact.validation_status !== 'pending' && (
                          <Box sx={{ width: '100%', mt: 1 }}>
                            <FKEmailValidationResult
                              validationStatus={contact.validation_status}
                              validationResult={contact.validation_result}
                            />
                          </Box>
                        )}
                      </ListItem>
                    </React.Fragment>
                  );
                })}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Azelis Case Example */}
      <Alert severity="warning" sx={{ mt: 3 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
          Ejemplo de Typosquatting (Caso Azelis)
        </Typography>
        <Typography variant="body2">
          Un caso real de fraude utilizó el dominio <code>azelis.com.co</code> para hacerse pasar
          por la empresa legítima <code>azelis.com</code>. La variación de TLD (.com vs .com.co)
          pasó desapercibida y resultó en pérdidas significativas. Este sistema detectaría
          automáticamente esta variación como sospechosa.
        </Typography>
      </Alert>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default FKExternalContactTab;
