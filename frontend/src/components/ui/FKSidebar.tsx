/**
 * FKSidebar - Left sidebar with department navigation
 */
import React, { useEffect, useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  CircularProgress,
  Typography,
  Alert,
  Button,
} from '@mui/material';
import {
  Settings,
  TrendingUp,
  AttachMoney,
  People,
  Code,
  Support,
  Gavel,
  Shield,
  ErrorOutline,
  Refresh,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { departmentService } from '../../services/departmentService';
import { useAuth } from '../../hooks/useAuth';
import type { Department } from '../../types';

const DRAWER_WIDTH = 280;

/**
 * Type guard to validate Department objects at runtime
 * Ensures object has all required properties with correct types
 */
function isValidDepartment(dept: unknown): dept is Department {
  const isValid = (
    typeof dept === 'object' &&
    dept !== null &&
    'id' in dept &&
    typeof (dept as { id: unknown }).id === 'string' &&
    (dept as { id: string }).id.length > 0 &&
    'name' in dept &&
    typeof (dept as { name: unknown }).name === 'string' &&
    (dept as { name: string }).name.length > 0 &&
    'icon' in dept &&
    typeof (dept as { icon: unknown }).icon === 'string' &&
    (dept as { icon: string }).icon.length > 0
  );

  if (!isValid && dept) {
    const deptObj = dept as Record<string, unknown>;
    console.error('[FKSidebar] Invalid department object:', {
      received: dept,
      hasId: 'id' in deptObj && typeof deptObj.id === 'string',
      hasName: 'name' in deptObj && typeof deptObj.name === 'string',
      hasIcon: 'icon' in deptObj && typeof deptObj.icon === 'string',
    });
  }

  return isValid;
}

// Icon mapping
const iconMap: Record<string, React.ReactElement> = {
  Settings: <Settings />,
  TrendingUp: <TrendingUp />,
  AttachMoney: <AttachMoney />,
  People: <People />,
  Code: <Code />,
  Support: <Support />,
  Gavel: <Gavel />,
  Shield: <Shield />,
};

const FKSidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { userProfile } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('[FKSidebar] Loading departments...');
      const data = await departmentService.getDepartments();

      console.log('[FKSidebar] Received departments:', data);

      // Validate and filter departments
      const validDepartments = data.filter(isValidDepartment);

      if (validDepartments.length !== data.length) {
        console.warn('[FKSidebar] Some departments were invalid and filtered out', {
          total: data.length,
          valid: validDepartments.length,
          invalid: data.length - validDepartments.length,
        });
      }

      setDepartments(validDepartments);
      console.log('[FKSidebar] Successfully loaded departments:', validDepartments.length);
    } catch (error) {
      console.error('[FKSidebar] Error loading departments:', error);
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido al cargar departamentos';
      setError(errorMessage);
      setDepartments([]); // Ensure departments is empty array on error
    } finally {
      setLoading(false);
    }
  };

  /**
   * Check if user has access to a department based on their role
   * Admin has access to all departments
   * Legal role only has access to Legal department
   * Operations role only has access to Operations department
   * Alianzas role only has access to Alianzas department
   * comercial_paga_local role has limited access to Operations (Paga Local only)
   */
  const hasAccessToDepartment = (departmentId: string): boolean => {
    if (!userProfile) return false;

    const userRole = userProfile.role;

    // Admin has access to everything
    if (userRole === 'admin') return true;

    // Legal role only has access to legal department
    if (userRole === 'legal' && departmentId === 'legal') return true;

    // Operations role only has access to operations department
    if (userRole === 'operations' && departmentId === 'operations') return true;

    // Alianzas role only has access to alianzas department
    if (userRole === 'alianzas' && departmentId === 'alianzas') return true;

    // comercial_paga_local role has limited access to operations department
    // (route-level protection will further restrict access to only Paga Local)
    if (userRole === 'comercial_paga_local' && departmentId === 'operations') return true;

    // Risk department roles
    if ((userRole === 'risk_analyst' || userRole === 'risk_manager') && departmentId === 'risk') return true;

    // For other roles, deny access (can be extended later)
    return false;
  };

  const handleDepartmentClick = (departmentId: string) => {
    // For comercial_paga_local users clicking on operations, go directly to Paga Local
    // instead of the default redirect to contratos-colombia
    if (userProfile?.role === 'comercial_paga_local' && departmentId === 'operations') {
      navigate('/operations/paga-local-colombia');
      return;
    }
    navigate(`/department/${departmentId}`);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          backgroundColor: 'background.paper',
        },
      }}
    >
      <Toolbar />
      <Box sx={{ overflow: 'auto', p: 2 }}>
        <Typography
          variant="overline"
          sx={{
            px: 2,
            py: 1,
            color: 'text.secondary',
            fontWeight: 600,
            letterSpacing: '0.5px'
          }}
        >
          Departamentos
        </Typography>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={32} />
          </Box>
        ) : error ? (
          <Box sx={{ p: 2 }}>
            <Alert
              severity="error"
              icon={<ErrorOutline />}
              sx={{ mb: 2 }}
            >
              <Typography variant="body2" sx={{ mb: 1 }}>
                No se pudieron cargar los departamentos
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {error}
              </Typography>
            </Alert>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadDepartments}
              sx={{ borderRadius: 2 }}
            >
              Reintentar
            </Button>
          </Box>
        ) : departments.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              No hay departamentos disponibles para tu rol
            </Typography>
          </Box>
        ) : (
          <List sx={{ mt: 1 }}>
            {departments
              .filter((department) => department && hasAccessToDepartment(department.id))
              .map((department) => {
                const isActive = location.pathname.includes(`/department/${department.id}`);
                return (
                  <ListItem key={department?.id ?? 'unknown'} disablePadding sx={{ mb: 0.5 }}>
                    <ListItemButton
                      onClick={() => handleDepartmentClick(department?.id ?? '')}
                      sx={{
                        borderRadius: 2,
                        py: 1.5,
                        backgroundColor: isActive ? 'primary.main' : 'transparent',
                        color: isActive ? 'white' : 'text.primary',
                        '&:hover': {
                          backgroundColor: isActive ? 'primary.dark' : 'action.hover',
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          color: isActive ? 'white' : 'primary.main',
                          minWidth: 40,
                        }}
                      >
                        {iconMap[department?.icon ?? ''] || <Settings />}
                      </ListItemIcon>
                      <ListItemText
                        primary={department?.name ?? 'Departamento'}
                        primaryTypographyProps={{
                          fontWeight: isActive ? 600 : 500,
                          fontSize: '0.95rem',
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                );
              })}
          </List>
        )}
      </Box>
    </Drawer>
  );
};

export default FKSidebar;
