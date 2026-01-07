/**
 * FKManualMatchDialog - Dialog for manual match override.
 *
 * Allows users to manually assign a declaration to a payment group.
 */
import React, { useState, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  Autocomplete,
  Card,
  CardContent,
  Divider,
  Chip,
  InputAdornment,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  CalendarMonth as CalendarIcon,
  AttachMoney as MoneyIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import type { PaymentGroup, DeclarationItem } from '../../types/treasuryMatching';

interface FKManualMatchDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (declarationId: string) => void;
  paymentGroup: PaymentGroup | null;
  declarations: DeclarationItem[];
  loading?: boolean;
}

const FKManualMatchDialog: React.FC<FKManualMatchDialogProps> = ({
  open,
  onClose,
  onConfirm,
  paymentGroup,
  declarations,
  loading = false,
}) => {
  const [selectedDeclaration, setSelectedDeclaration] = useState<DeclarationItem | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter declarations based on search term
  const filteredDeclarations = useMemo(() => {
    if (!searchTerm) return declarations;

    const term = searchTerm.toLowerCase();
    return declarations.filter(
      (d) =>
        d.customer_name.toLowerCase().includes(term) ||
        d.declaration_number.toLowerCase().includes(term) ||
        d.fecha.includes(term)
    );
  }, [declarations, searchTerm]);

  // Sort by relevance to payment group
  const sortedDeclarations = useMemo(() => {
    if (!paymentGroup) return filteredDeclarations;

    return [...filteredDeclarations].sort((a, b) => {
      // Prioritize similar customer names
      const aNameMatch = a.customer_name_normalized.includes(paymentGroup.cliente_normalized) ? 1 : 0;
      const bNameMatch = b.customer_name_normalized.includes(paymentGroup.cliente_normalized) ? 1 : 0;
      if (aNameMatch !== bNameMatch) return bNameMatch - aNameMatch;

      // Then by date proximity
      const paymentDate = new Date(paymentGroup.fecha_pago).getTime();
      const aDateDiff = Math.abs(new Date(a.fecha).getTime() - paymentDate);
      const bDateDiff = Math.abs(new Date(b.fecha).getTime() - paymentDate);
      if (aDateDiff !== bDateDiff) return aDateDiff - bDateDiff;

      // Then by amount proximity
      const aAmtDiff = Math.abs(a.amount - paymentGroup.total_capital);
      const bAmtDiff = Math.abs(b.amount - paymentGroup.total_capital);
      return aAmtDiff - bAmtDiff;
    });
  }, [filteredDeclarations, paymentGroup]);

  const handleConfirm = () => {
    if (selectedDeclaration) {
      onConfirm(selectedDeclaration.declaration_id);
      setSelectedDeclaration(null);
      setSearchTerm('');
    }
  };

  const handleClose = () => {
    setSelectedDeclaration(null);
    setSearchTerm('');
    onClose();
  };

  // Calculate differences for preview
  const differences = useMemo(() => {
    if (!paymentGroup || !selectedDeclaration) return null;

    const paymentDate = new Date(paymentGroup.fecha_pago);
    const declDate = new Date(selectedDeclaration.fecha);
    const dateDiff = Math.round((declDate.getTime() - paymentDate.getTime()) / (1000 * 60 * 60 * 24));
    const amountDiff = selectedDeclaration.amount - paymentGroup.total_capital;

    return {
      dateDiff,
      amountDiff,
    };
  }, [paymentGroup, selectedDeclaration]);

  if (!paymentGroup) return null;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Asignar Declaracion Manualmente</DialogTitle>
      <DialogContent>
        {/* Payment Group Info */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Grupo de Pago
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon fontSize="small" color="action" />
                <Typography variant="body1" fontWeight={500}>
                  {paymentGroup.cliente}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Chip
                  icon={<CalendarIcon fontSize="small" />}
                  label={paymentGroup.fecha_pago}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  icon={<MoneyIcon fontSize="small" />}
                  label={`$${paymentGroup.total_capital.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                  })}`}
                  size="small"
                  variant="outlined"
                  color="primary"
                />
                <Chip
                  label={`${paymentGroup.record_count} registro(s)`}
                  size="small"
                  variant="outlined"
                />
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Declaration Search */}
        <Typography variant="subtitle2" gutterBottom>
          Seleccionar Declaracion
        </Typography>

        <Autocomplete
          options={sortedDeclarations}
          value={selectedDeclaration}
          onChange={(_event, newValue) => setSelectedDeclaration(newValue)}
          getOptionLabel={(option) =>
            `${option.declaration_number} - ${option.customer_name} - ${option.fecha} - $${option.amount.toFixed(2)}`
          }
          renderOption={(props, option) => (
            <Box component="li" {...props} key={option.declaration_id}>
              <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" fontWeight={500}>
                    DC #{option.declaration_number}
                  </Typography>
                  <Typography variant="body2" color="primary">
                    ${option.amount.toFixed(2)}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {option.customer_name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {option.fecha}
                </Typography>
              </Box>
            </Box>
          )}
          renderInput={(params) => (
            <TextField
              {...params}
              placeholder="Buscar por numero, cliente o fecha..."
              InputProps={{
                ...params.InputProps,
                startAdornment: (
                  <>
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                    {params.InputProps.startAdornment}
                  </>
                ),
              }}
            />
          )}
          filterOptions={(options, state) => {
            const term = state.inputValue.toLowerCase();
            if (!term) return options;
            return options.filter(
              (opt) =>
                opt.declaration_number.toLowerCase().includes(term) ||
                opt.customer_name.toLowerCase().includes(term) ||
                opt.fecha.includes(term)
            );
          }}
          sx={{ mb: 3 }}
        />

        {/* Selected Declaration Preview */}
        {selectedDeclaration && (
          <>
            <Divider sx={{ my: 2 }} />
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Declaracion Seleccionada
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1" fontWeight={500}>
                      DC #{selectedDeclaration.declaration_number}
                    </Typography>
                  </Box>
                  <Typography variant="body2">
                    {selectedDeclaration.customer_name}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Chip
                      icon={<CalendarIcon fontSize="small" />}
                      label={selectedDeclaration.fecha}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      icon={<MoneyIcon fontSize="small" />}
                      label={`$${selectedDeclaration.amount.toFixed(2)}`}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    Archivo: {selectedDeclaration.pdf_file_name}
                  </Typography>
                </Box>

                {/* Differences */}
                {differences && (
                  <Alert
                    severity={
                      Math.abs(differences.dateDiff) <= 7 && Math.abs(differences.amountDiff) <= 2
                        ? 'success'
                        : 'warning'
                    }
                    sx={{ mt: 2 }}
                  >
                    <Typography variant="body2">
                      <strong>Diferencia de fecha:</strong>{' '}
                      {differences.dateDiff > 0
                        ? `+${differences.dateDiff}`
                        : differences.dateDiff}{' '}
                      dias
                      <br />
                      <strong>Diferencia de monto:</strong>{' '}
                      {differences.amountDiff > 0
                        ? `+$${differences.amountDiff.toFixed(2)}`
                        : `$${differences.amountDiff.toFixed(2)}`}
                    </Typography>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancelar
        </Button>
        <Button
          variant="contained"
          onClick={handleConfirm}
          disabled={!selectedDeclaration || loading}
        >
          Confirmar Asignacion
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FKManualMatchDialog;
