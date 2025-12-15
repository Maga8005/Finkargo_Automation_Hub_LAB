/**
 * FKHistorialMatchingUploader - File upload component for Declaration-Historial matching.
 *
 * Handles upload of both Historial de Pagos and Declaration inventory Excel files
 * with drag & drop support and validation feedback.
 */
import React, { useCallback, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  InsertDriveFile as FileIcon,
} from '@mui/icons-material';
import type {
  HistorialUploadResponse,
  DeclarationInventoryUploadResponse,
  ColumnValidationStatus,
} from '../../types/treasuryMatching';

interface FKHistorialMatchingUploaderProps {
  onHistorialUpload: (file: File) => Promise<void>;
  onDeclarationsUpload: (file: File) => Promise<void>;
  historialResponse: HistorialUploadResponse | null;
  declarationsResponse: DeclarationInventoryUploadResponse | null;
  loading: boolean;
  sessionId: string | null;
}

const FKHistorialMatchingUploader: React.FC<FKHistorialMatchingUploaderProps> = ({
  onHistorialUpload,
  onDeclarationsUpload,
  historialResponse,
  declarationsResponse,
  loading,
  sessionId,
}) => {
  const [historialDragActive, setHistorialDragActive] = useState(false);
  const [declarationsDragActive, setDeclarationsDragActive] = useState(false);
  const [historialFile, setHistorialFile] = useState<File | null>(null);
  const [declarationsFile, setDeclarationsFile] = useState<File | null>(null);

  const handleDrag = useCallback((e: React.DragEvent, setActive: (active: boolean) => void, active: boolean) => {
    e.preventDefault();
    e.stopPropagation();
    setActive(active);
  }, []);

  const handleHistorialDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setHistorialDragActive(false);

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        const file = files[0];
        if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
          setHistorialFile(file);
          await onHistorialUpload(file);
        }
      }
    },
    [onHistorialUpload]
  );

  const handleDeclarationsDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDeclarationsDragActive(false);

      if (!sessionId) return;

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        const file = files[0];
        if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
          setDeclarationsFile(file);
          await onDeclarationsUpload(file);
        }
      }
    },
    [onDeclarationsUpload, sessionId]
  );

  const handleHistorialFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setHistorialFile(file);
      await onHistorialUpload(file);
    }
  };

  const handleDeclarationsFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!sessionId) return;

    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setDeclarationsFile(file);
      await onDeclarationsUpload(file);
    }
  };

  const renderColumnStatus = (columnStatus: ColumnValidationStatus[]) => (
    <List dense>
      {columnStatus.map((col, idx) => (
        <ListItem key={idx} sx={{ py: 0.5 }}>
          <ListItemIcon sx={{ minWidth: 32 }}>
            {col.found ? (
              <CheckCircleIcon color="success" fontSize="small" />
            ) : (
              <ErrorIcon color="error" fontSize="small" />
            )}
          </ListItemIcon>
          <ListItemText
            primary={col.column_name}
            secondary={col.found ? col.source_column : 'No encontrada'}
            primaryTypographyProps={{ variant: 'body2' }}
            secondaryTypographyProps={{ variant: 'caption' }}
          />
        </ListItem>
      ))}
    </List>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Historial de Pagos Upload */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            1. Historial de Pagos
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Suba el archivo Excel con el historial de pagos. El sistema agrupara los pagos
            por cliente y fecha.
          </Typography>

          {!historialResponse?.success ? (
            <Box
              sx={{
                border: '2px dashed',
                borderColor: historialDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                backgroundColor: historialDragActive ? 'action.hover' : 'background.paper',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onDragEnter={(e) => handleDrag(e, setHistorialDragActive, true)}
              onDragLeave={(e) => handleDrag(e, setHistorialDragActive, false)}
              onDragOver={(e) => handleDrag(e, setHistorialDragActive, true)}
              onDrop={handleHistorialDrop}
            >
              {loading ? (
                <CircularProgress />
              ) : (
                <>
                  <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="body1" gutterBottom>
                    Arrastre el archivo Excel aqui
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    o
                  </Typography>
                  <Button
                    variant="contained"
                    component="label"
                    startIcon={<FileIcon />}
                  >
                    Seleccionar Archivo
                    <input
                      type="file"
                      hidden
                      accept=".xlsx,.xls"
                      onChange={handleHistorialFileSelect}
                    />
                  </Button>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Formatos soportados: .xlsx, .xls
                  </Typography>
                </>
              )}
            </Box>
          ) : (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                Archivo cargado: {historialFile?.name}
              </Alert>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                <Chip
                  icon={<DescriptionIcon />}
                  label={`${historialResponse.total_rows} filas`}
                  variant="outlined"
                />
                <Chip
                  icon={<CheckCircleIcon />}
                  label={`${historialResponse.valid_rows} validas`}
                  color="success"
                  variant="outlined"
                />
                <Chip
                  label={`${historialResponse.group_count} grupos de pago`}
                  color="primary"
                  variant="outlined"
                />
              </Box>

              {historialResponse.column_status.length > 0 && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    Columnas Requeridas:
                  </Typography>
                  {renderColumnStatus(historialResponse.column_status)}
                </>
              )}

              {historialResponse.errors.length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Advertencias:</Typography>
                  {historialResponse.errors.slice(0, 5).map((err, idx) => (
                    <Typography key={idx} variant="body2">
                      {err}
                    </Typography>
                  ))}
                  {historialResponse.errors.length > 5 && (
                    <Typography variant="caption">
                      ... y {historialResponse.errors.length - 5} mas
                    </Typography>
                  )}
                </Alert>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Declarations Upload */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            2. Inventario de Declaraciones
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Suba el archivo Excel con el inventario de declaraciones de cambio.
            Debe contener: Cliente, Fecha, Monto, Numero de Declaracion.
          </Typography>

          {!sessionId ? (
            <Alert severity="info">
              Primero suba el archivo de Historial de Pagos
            </Alert>
          ) : !declarationsResponse?.success ? (
            <Box
              sx={{
                border: '2px dashed',
                borderColor: declarationsDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                backgroundColor: declarationsDragActive ? 'action.hover' : 'background.paper',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onDragEnter={(e) => handleDrag(e, setDeclarationsDragActive, true)}
              onDragLeave={(e) => handleDrag(e, setDeclarationsDragActive, false)}
              onDragOver={(e) => handleDrag(e, setDeclarationsDragActive, true)}
              onDrop={handleDeclarationsDrop}
            >
              {loading ? (
                <CircularProgress />
              ) : (
                <>
                  <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="body1" gutterBottom>
                    Arrastre el archivo Excel aqui
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    o
                  </Typography>
                  <Button
                    variant="contained"
                    component="label"
                    startIcon={<FileIcon />}
                  >
                    Seleccionar Archivo
                    <input
                      type="file"
                      hidden
                      accept=".xlsx,.xls"
                      onChange={handleDeclarationsFileSelect}
                    />
                  </Button>
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Columnas requeridas: Cliente, Fecha, Monto, Numero DC
                  </Typography>
                </>
              )}
            </Box>
          ) : (
            <Box>
              <Alert severity="success" sx={{ mb: 2 }}>
                Archivo cargado: {declarationsFile?.name}
              </Alert>

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                <Chip
                  icon={<DescriptionIcon />}
                  label={`${declarationsResponse.total_declarations} declaraciones`}
                  color="primary"
                  variant="outlined"
                />
              </Box>

              {declarationsResponse.errors.length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">Advertencias:</Typography>
                  {declarationsResponse.errors.slice(0, 5).map((err, idx) => (
                    <Typography key={idx} variant="body2">
                      {err}
                    </Typography>
                  ))}
                </Alert>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default FKHistorialMatchingUploader;
