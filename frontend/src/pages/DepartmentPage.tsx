/**
 * DepartmentPage - Shows modules and features for a department
 */
import React from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
} from '@mui/material';

const DepartmentPage: React.FC = () => {
  const { departmentId } = useParams<{ departmentId: string }>();

  // TODO: Fetch department details and modules from API
  const departmentName = departmentId
    ? departmentId.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    : 'Departamento';

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'primary.dark' }}>
          {departmentName}
        </Typography>
        <Typography variant="body1" sx={{ color: 'grey.700' }}>
          Módulos de automatización disponibles para este departamento
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6, lg: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Módulo de Ejemplo
                </Typography>
                <Chip label="Próximamente" size="small" color="default" />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Los módulos de automatización se agregarán aquí. Cada módulo contendrá
                funcionalidades específicas en pestañas separadas.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DepartmentPage;
