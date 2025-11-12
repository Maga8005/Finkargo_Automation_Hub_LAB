/**
 * FKSidebarWithCollapse - Enhanced sidebar with collapsible nested menus
 * Supports hierarchical department structure with country-specific modules
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
  Collapse,
} from '@mui/material';
import {
  Settings,
  TrendingUp,
  AttachMoney,
  People,
  Code,
  Support,
  Gavel,
  Assessment,
  ExpandLess,
  ExpandMore,
  Flag,
  Description,
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
  Assessment: <Assessment />,
};

// Mock departments data - Replace with API call when backend is ready
const mockDepartments: Department[] = [
  { id: 'operations', name: 'Operaciones', icon: 'Settings' },
  { id: 'sales', name: 'Ventas', icon: 'TrendingUp' },
  { id: 'finance', name: 'Finanzas', icon: 'AttachMoney' }, // This one will have fiscal reporting
  { id: 'hr', name: 'Recursos Humanos', icon: 'People' },
  { id: 'tech', name: 'Tecnología', icon: 'Code' },
  { id: 'support', name: 'Atención al Cliente', icon: 'Support' },
  { id: 'legal', name: 'Legal', icon: 'Gavel' },
  { id: 'collections', name: 'Collections', icon: 'Settings' },
];

// Finance sub-modules (direct navigation, no further nesting)
interface FinanceModule {
  id: string;
  name: string;
  route: string;
  icon: React.ReactElement;
  badge?: string;
}

const financeModules: FinanceModule[] = [
  {
    id: 'reporteria-co',
    name: 'Reportería Automática CO',
    route: '/finance/reporteria-automatica-co',
    icon: <Description fontSize="small" />,
  },
  {
    id: 'reporteria-mx',
    name: 'Reportería Automática MX',
    route: '/finance/reporteria-automatica-mx',
    icon: <Description fontSize="small" />,
  },
];

const FKSidebarWithCollapse: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { userProfile } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  // Collapse state for departments with submenus
  const [financeOpen, setFinanceOpen] = useState(false);

  useEffect(() => {
    loadDepartments();

    // Auto-expand finance if on a finance route
    if (location.pathname.includes('/finance/')) {
      setFinanceOpen(true);
    }
  }, [location.pathname]);

  const loadDepartments = async () => {
    try {
      // Try to load from API, fallback to mock data
      try {
        const data = await departmentService.getDepartments();
        setDepartments(data.length > 0 ? data : mockDepartments);
      } catch (apiError) {
        console.log('[Sidebar] Using mock departments data');
        setDepartments(mockDepartments);
      }
    } catch (error) {
      console.error('Error loading departments:', error);
      setDepartments(mockDepartments);
    } finally {
      setLoading(false);
    }
  };

  const hasAccessToDepartment = (_departmentId: string): boolean => {
    // Show all departments to all users
    // Access control is enforced at the route/page level
    return true;
  };

  const handleDepartmentClick = (departmentId: string) => {
    navigate(`/department/${departmentId}`);
  };

  const handleFinanceToggle = () => {
    setFinanceOpen(!financeOpen);
  };

  const handleFinanceModuleClick = (route: string) => {
    navigate(route);
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
            letterSpacing: '0.5px',
          }}
        >
          Departamentos
        </Typography>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={32} />
          </Box>
        ) : (
          <>
            {/* Departments List */}
            <List sx={{ mt: 1 }}>
              {departments
                .filter((department) => hasAccessToDepartment(department.id))
                .map((department) => {
                  // Special handling for Finance department (has submenu)
                  if (department.id === 'finance') {
                    // Don't mark parent as active, only submenu items
                    const hasActiveSubmenu = financeModules.some(m => location.pathname === m.route);
                    return (
                      <React.Fragment key={department.id}>
                        <ListItem disablePadding sx={{ mb: 0.5 }}>
                          <ListItemButton
                            onClick={handleFinanceToggle}
                            sx={{
                              borderRadius: 2,
                              py: 1.5,
                              backgroundColor: 'transparent',
                              color: hasActiveSubmenu ? 'primary.main' : 'grey.800',
                              '&:hover': {
                                backgroundColor: 'grey.100',
                              },
                            }}
                          >
                            <ListItemIcon
                              sx={{
                                color: hasActiveSubmenu ? 'primary.main' : 'primary.main',
                                minWidth: 40,
                              }}
                            >
                              {iconMap[department.icon] || <Settings />}
                            </ListItemIcon>
                            <ListItemText
                              primary={department.name}
                              primaryTypographyProps={{
                                fontWeight: hasActiveSubmenu ? 600 : 500,
                                fontSize: '0.95rem',
                              }}
                            />
                            {financeOpen ? (
                              <ExpandLess sx={{ color: 'grey.600' }} />
                            ) : (
                              <ExpandMore sx={{ color: 'grey.600' }} />
                            )}
                          </ListItemButton>
                        </ListItem>

                        {/* Finance Modules Submenu */}
                        <Collapse in={financeOpen} timeout="auto" unmountOnExit>
                          <List component="div" disablePadding sx={{ position: 'relative' }}>
                            {/* Visual separator/connector for hierarchy */}
                            <Box
                              sx={{
                                position: 'absolute',
                                left: 20,
                                top: 0,
                                bottom: 0,
                                width: '2px',
                                backgroundColor: 'grey.200',
                              }}
                            />
                            {financeModules.map((module) => {
                              const isModuleActive = location.pathname === module.route;
                              return (
                                <ListItem key={module.id} disablePadding sx={{ mb: 0.5 }}>
                                  <ListItemButton
                                    onClick={() => handleFinanceModuleClick(module.route)}
                                    sx={{
                                      pl: 7,
                                      pr: 2,
                                      borderRadius: 2,
                                      ml: 1,
                                      py: 1,
                                      backgroundColor: isModuleActive ? 'primary.main' : 'transparent',
                                      color: isModuleActive ? 'white' : 'grey.600',
                                      '&:hover': {
                                        backgroundColor: isModuleActive ? 'primary.dark' : 'grey.100',
                                      },
                                    }}
                                  >
                                    <ListItemIcon
                                      sx={{
                                        color: isModuleActive ? 'white' : 'grey.400',
                                        minWidth: 32,
                                      }}
                                    >
                                      {module.icon}
                                    </ListItemIcon>
                                    <ListItemText
                                      primary={module.name}
                                      primaryTypographyProps={{
                                        fontWeight: isModuleActive ? 600 : 500,
                                        fontSize: '0.8125rem',
                                      }}
                                    />
                                    {module.badge && (
                                      <Typography
                                        variant="caption"
                                        sx={{
                                          backgroundColor: 'coral.main',
                                          color: 'white',
                                          px: 1,
                                          py: 0.25,
                                          borderRadius: 1,
                                          fontSize: '0.625rem',
                                          fontWeight: 600,
                                        }}
                                      >
                                        {module.badge}
                                      </Typography>
                                    )}
                                  </ListItemButton>
                                </ListItem>
                              );
                            })}
                          </List>
                        </Collapse>
                      </React.Fragment>
                    );
                  }

                  // Regular departments without submenu
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
          </>
        )}
      </Box>
    </Drawer>
  );
};

export default FKSidebarWithCollapse;
