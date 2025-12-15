/**
 * FKMatchingConfigForm - Configuration form for matching parameters.
 *
 * Allows users to configure tolerance settings for the matching algorithm.
 */
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  FormControlLabel,
  Switch,
  Grid,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  CalendarMonth as CalendarIcon,
  AttachMoney as MoneyIcon,
  Person as PersonIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import type { MatchConfig } from '../../types/treasuryMatching';

interface FKMatchingConfigFormProps {
  config: MatchConfig;
  onChange: (config: MatchConfig) => void;
  groupCount: number;
  declarationCount: number;
}

const FKMatchingConfigForm: React.FC<FKMatchingConfigFormProps> = ({
  config,
  onChange,
  groupCount,
  declarationCount,
}) => {
  const handleDateToleranceChange = (_event: Event, newValue: number | number[]) => {
    onChange({
      ...config,
      date_tolerance_days: newValue as number,
    });
  };

  const handleAmountToleranceChange = (_event: Event, newValue: number | number[]) => {
    onChange({
      ...config,
      amount_tolerance: newValue as number,
    });
  };

  const handleCustomerThresholdChange = (_event: Event, newValue: number | number[]) => {
    onChange({
      ...config,
      customer_match_threshold: newValue as number,
    });
  };

  const handleStrictMatchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange({
      ...config,
      customer_match_strict: event.target.checked,
    });
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Parametros de Coincidencia
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Ajuste los parametros de tolerancia para el algoritmo de coincidencias.
          Valores mas altos encontraran mas coincidencias pero pueden incluir falsos positivos.
        </Typography>

        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>{groupCount}</strong> grupos de pago seran comparados con{' '}
            <strong>{declarationCount}</strong> declaraciones disponibles.
          </Typography>
        </Alert>

        <Grid container spacing={4}>
          {/* Date Tolerance */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <CalendarIcon color="primary" />
              <Typography variant="subtitle1">
                Tolerancia de Fecha
              </Typography>
              <Tooltip title="Dias de diferencia permitidos entre la fecha de pago y la fecha de declaracion">
                <InfoIcon fontSize="small" color="action" />
              </Tooltip>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              +/- {config.date_tolerance_days} dias
            </Typography>
            <Slider
              value={config.date_tolerance_days}
              onChange={handleDateToleranceChange}
              min={1}
              max={14}
              step={1}
              marks={[
                { value: 1, label: '1' },
                { value: 7, label: '7' },
                { value: 14, label: '14' },
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value} dias`}
            />
          </Grid>

          {/* Amount Tolerance */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <MoneyIcon color="primary" />
              <Typography variant="subtitle1">
                Tolerancia de Monto
              </Typography>
              <Tooltip title="Diferencia en USD permitida entre el capital del pago y el monto de la declaracion">
                <InfoIcon fontSize="small" color="action" />
              </Tooltip>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              +/- ${config.amount_tolerance.toFixed(2)} USD
            </Typography>
            <Slider
              value={config.amount_tolerance}
              onChange={handleAmountToleranceChange}
              min={0.5}
              max={5}
              step={0.5}
              marks={[
                { value: 0.5, label: '$0.50' },
                { value: 2, label: '$2.00' },
                { value: 5, label: '$5.00' },
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `$${value.toFixed(2)}`}
            />
          </Grid>

          {/* Customer Match Threshold */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <PersonIcon color="primary" />
              <Typography variant="subtitle1">
                Umbral de Similitud de Cliente
              </Typography>
              <Tooltip title="Porcentaje minimo de similitud requerido entre nombres de cliente (usando coincidencia difusa)">
                <InfoIcon fontSize="small" color="action" />
              </Tooltip>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Minimo {config.customer_match_threshold}% de similitud
            </Typography>
            <Slider
              value={config.customer_match_threshold}
              onChange={handleCustomerThresholdChange}
              min={50}
              max={100}
              step={5}
              marks={[
                { value: 50, label: '50%' },
                { value: 85, label: '85%' },
                { value: 100, label: '100%' },
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
              disabled={config.customer_match_strict}
            />
          </Grid>

          {/* Strict Match Toggle */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Typography variant="subtitle1">
                Coincidencia Exacta de Cliente
              </Typography>
              <Tooltip title="Cuando esta activo, requiere que los nombres de cliente coincidan exactamente (sin coincidencia difusa)">
                <InfoIcon fontSize="small" color="action" />
              </Tooltip>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {config.customer_match_strict
                ? 'Requiere coincidencia exacta'
                : 'Permite variaciones en el nombre'}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={config.customer_match_strict}
                  onChange={handleStrictMatchChange}
                  color="primary"
                />
              }
              label={config.customer_match_strict ? 'Activado' : 'Desactivado'}
            />
          </Grid>
        </Grid>

        {/* Preview of settings impact */}
        <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            Resumen de Configuracion
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Un pago coincidira con una declaracion si:
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
            <Typography component="li" variant="body2">
              Los nombres de cliente tienen al menos{' '}
              {config.customer_match_strict ? '100' : config.customer_match_threshold}% de similitud
            </Typography>
            <Typography component="li" variant="body2">
              Las fechas estan dentro de {config.date_tolerance_days} dias
            </Typography>
            <Typography component="li" variant="body2">
              Los montos difieren en maximo ${config.amount_tolerance.toFixed(2)} USD
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FKMatchingConfigForm;
