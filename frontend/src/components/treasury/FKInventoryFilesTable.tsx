/**
 * FKInventoryFilesTable - Inventory files display and download
 *
 * Displays a list of available inventory Excel files with:
 * - File name, creation date, file size
 * - Download button for each file
 * - Auto-refresh capability
 */
import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  CircularProgress,
  Alert,
  Chip,
  Tooltip,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import RefreshIcon from '@mui/icons-material/Refresh';
import DescriptionIcon from '@mui/icons-material/Description';
import {
  listInventoryFiles,
  downloadInventoryFile,
  formatFileSize,
  formatDate,
  type InventoryFileMetadata,
} from '../../services/directoryScannerService';

interface FKInventoryFilesTableProps {
  refreshTrigger?: number; // Increment to trigger refresh
}

const FKInventoryFilesTable: React.FC<FKInventoryFilesTableProps> = ({
  refreshTrigger = 0,
}) => {
  const [files, setFiles] = useState<InventoryFileMetadata[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null);

  console.log('[FKInventoryFilesTable] Rendering', {
    filesCount: files.length,
    isLoading,
    refreshTrigger,
  });

  /**
   * Fetch inventory files list
   */
  const fetchFiles = async () => {
    console.log('[FKInventoryFilesTable] Fetching files list');

    try {
      setIsLoading(true);
      setError('');

      const filesData = await listInventoryFiles();

      console.log('[FKInventoryFilesTable] Files fetched:', filesData.length);
      setFiles(filesData);
    } catch (err: any) {
      console.error('[FKInventoryFilesTable] Failed to fetch files:', err);
      setError(err.message || 'Error al cargar archivos de inventario');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle file download
   */
  const handleDownload = async (filename: string) => {
    console.log('[FKInventoryFilesTable] Downloading file:', filename);

    try {
      setDownloadingFile(filename);
      setError('');

      await downloadInventoryFile(filename);

      console.log('[FKInventoryFilesTable] File downloaded successfully');
    } catch (err: any) {
      console.error('[FKInventoryFilesTable] Download failed:', err);
      setError(err.message || 'Error al descargar archivo');
    } finally {
      setDownloadingFile(null);
    }
  };

  // Fetch files on mount and when refreshTrigger changes
  useEffect(() => {
    fetchFiles();
  }, [refreshTrigger]);

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        backgroundColor: 'background.paper',
        borderRadius: 2,
      }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box display="flex" alignItems="center" gap={1}>
          <DescriptionIcon color="primary" />
          <Typography variant="h6" component="h2" color="primary">
            Archivos de Inventario
          </Typography>
          {files.length > 0 && (
            <Chip
              label={`${files.length} archivo${files.length !== 1 ? 's' : ''}`}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </Box>

        <Tooltip title="Actualizar lista">
          <IconButton
            onClick={fetchFiles}
            disabled={isLoading}
            size="small"
            color="primary"
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {isLoading ? (
        <Box display="flex" justifyContent="center" alignItems="center" py={4}>
          <CircularProgress />
        </Box>
      ) : files.length === 0 ? (
        <Alert severity="info" icon={false}>
          <Typography variant="body2" color="text.secondary">
            No hay archivos de inventario disponibles. Escanea un directorio
            para generar un nuevo inventario.
          </Typography>
        </Alert>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Nombre de Archivo
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Fecha de Creación
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Tamaño
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Registros
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="subtitle2" fontWeight={600}>
                    Acciones
                  </Typography>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {files.map((file) => (
                <TableRow
                  key={file.file_name}
                  hover
                  sx={{
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {file.file_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(file.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {formatFileSize(file.file_size_bytes)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {file.record_count
                        ? `${file.record_count} PDFs`
                        : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Descargar archivo">
                      <IconButton
                        onClick={() => handleDownload(file.file_name)}
                        disabled={downloadingFile === file.file_name}
                        size="small"
                        color="primary"
                      >
                        {downloadingFile === file.file_name ? (
                          <CircularProgress size={20} />
                        ) : (
                          <DownloadIcon />
                        )}
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default FKInventoryFilesTable;
