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
} from '@mui/material';
import {
  Settings,
  TrendingUp,
  AttachMoney,
  People,
  Code,
  Support,
  Gavel,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { departmentService } from '../../services/departmentService';
import { useAuth } from '../../hooks/useAuth';
import type { Department } from '../../types';

const DRAWER_WIDTH = 280;

// Icon mapping
const iconMap: Record<string, React.ReactElement> = {
  Settings: <Settings />,
  TrendingUp: <TrendingUp />,
  AttachMoney: <AttachMoney />,
  People: <People />,
  Code: <Code />,
  Support: <Support />,
  Gavel: <Gavel />,
};

const FKSidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { userProfile } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    try {
      const data = await departmentService.getDepartments();
      setDepartments(data);
    } catch (error) {
      console.error('Error loading departments:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Check if user has access to a department based on their role
   * Admin has access to all departments
   * Legal role only has access to Legal department
   * Operations role only has access to Operations department
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

    // For other roles, deny access (can be extended later)
    return false;
  };

  const handleDepartmentClick = (departmentId: string) => {
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
          backgroundColor: 'grey.50',
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
            color: 'grey.600',
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
        ) : (
          <List sx={{ mt: 1 }}>
            {departments
              .filter((department) => hasAccessToDepartment(department.id))
              .map((department) => {
                const isActive = location.pathname.includes(`/department/${department.id}`);
                return (
                  <ListItem key={department.id} disablePadding sx={{ mb: 0.5 }}>
                    <ListItemButton
                      onClick={() => handleDepartmentClick(department.id)}
                      sx={{
                        borderRadius: 2,
                        py: 1.5,
                        backgroundColor: isActive ? 'primary.main' : 'transparent',
                        color: isActive ? 'white' : 'grey.800',
                        '&:hover': {
                          backgroundColor: isActive ? 'primary.dark' : 'grey.100',
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          color: isActive ? 'white' : 'primary.main',
                          minWidth: 40,
                        }}
                      >
                        {iconMap[department.icon] || <Settings />}
                      </ListItemIcon>
                      <ListItemText
                        primary={department.name}
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
