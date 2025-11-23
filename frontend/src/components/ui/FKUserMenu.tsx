/**
 * FKUserMenu - User profile menu with logout functionality
 * Displays user avatar, name, role, theme toggle and logout button
 */
import React, { useState } from 'react';
import {
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Typography,
  Divider,
  ListItemIcon,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  Logout as LogoutIcon,
  Person as PersonIcon,
  ExpandMore as ExpandMoreIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useThemeMode } from '../../hooks/useThemeMode';

const FKUserMenu: React.FC = () => {
  const navigate = useNavigate();
  const { user, userProfile, signOut, loading } = useAuth();
  const { isDarkMode, toggleTheme } = useThemeMode();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    handleClose();

    try {
      await signOut();
      navigate('/login', { replace: true });
    } catch (error) {
      console.error('Error logging out:', error);
      // Still navigate to login even if sign out fails
      navigate('/login', { replace: true });
    } finally {
      setIsLoggingOut(false);
    }
  };

  // Get user initials for avatar
  const getInitials = (name: string): string => {
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Get role label in Spanish
  const getRoleLabel = (role: string): string => {
    const roleLabels: Record<string, string> = {
      admin: 'Administrador',
      legal: 'Legal',
      operations: 'Operaciones',
      commercial: 'Comercial',
      analyst: 'Analista',
      mesa_control: 'Mesa de Control',
      manager: 'Gerente',
      user: 'Usuario',
      cliente: 'Cliente',
    };
    return roleLabels[role] || role;
  };

  // Get user type badge color
  const getUserTypeBadgeColor = (userType: string) => {
    return userType === 'cliente' ? 'secondary' : 'primary';
  };

  // Only show loading spinner on initial load (when we don't have user data yet)
  // Once we have user profile, keep showing it even if there's a background refresh
  if (!user && loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={24} sx={{ color: 'white' }} />
      </Box>
    );
  }

  // If we have user but no profile yet, show loading
  if (user && !userProfile && loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={24} sx={{ color: 'white' }} />
      </Box>
    );
  }

  // If we have user but profile failed to load, show minimal user info
  if (user && !userProfile) {
    return (
      <Box>
        <IconButton
          size="small"
          sx={{
            gap: 1.5,
            px: 1.5,
            py: 0.5,
            borderRadius: 2,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          <Avatar
            sx={{
              width: 36,
              height: 36,
              bgcolor: 'coral.main',
              fontSize: '0.875rem',
              fontWeight: 600,
            }}
          >
            {user.email ? user.email.substring(0, 2).toUpperCase() : '??'}
          </Avatar>
          <Box sx={{ display: { xs: 'none', md: 'block' }, textAlign: 'left' }}>
            <Typography
              variant="body2"
              sx={{ color: 'white', fontWeight: 600, lineHeight: 1.2 }}
            >
              {user.email || 'Usuario'}
            </Typography>
          </Box>
        </IconButton>
      </Box>
    );
  }

  // TypeScript guard: if we reach here, userProfile must exist
  if (!userProfile) {
    return null;
  }

  return (
    <Box>
      {/* User Button */}
      <IconButton
        onClick={handleClick}
        size="small"
        sx={{
          gap: 1.5,
          px: 1.5,
          py: 0.5,
          borderRadius: 2,
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
          },
        }}
        aria-controls={open ? 'user-menu' : undefined}
        aria-haspopup="true"
        aria-expanded={open ? 'true' : undefined}
      >
        <Avatar
          sx={{
            width: 36,
            height: 36,
            bgcolor: 'coral.main',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}
        >
          {getInitials(userProfile.full_name)}
        </Avatar>
        <Box sx={{ display: { xs: 'none', md: 'block' }, textAlign: 'left' }}>
          <Typography
            variant="body2"
            sx={{ color: 'white', fontWeight: 600, lineHeight: 1.2 }}
          >
            {userProfile.full_name}
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: 'rgba(255, 255, 255, 0.7)', lineHeight: 1 }}
          >
            {getRoleLabel(userProfile.role)}
          </Typography>
        </Box>
        <ExpandMoreIcon sx={{ color: 'white', ml: 0.5 }} />
      </IconButton>

      {/* Dropdown Menu */}
      <Menu
        anchorEl={anchorEl}
        id="user-menu"
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        PaperProps={{
          elevation: 4,
          sx: {
            minWidth: 280,
            mt: 1.5,
            borderRadius: 2,
            '& .MuiMenuItem-root': {
              borderRadius: 1,
              mx: 1,
              my: 0.5,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {/* User Info Header */}
        <Box sx={{ px: 2, py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
            <Avatar
              sx={{
                width: 48,
                height: 48,
                bgcolor: 'primary.main',
                fontSize: '1.125rem',
                fontWeight: 600,
              }}
            >
              {getInitials(userProfile.full_name)}
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, lineHeight: 1.3 }}>
                {userProfile.full_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8125rem' }}>
                {user?.email}
              </Typography>
            </Box>
          </Box>

          {/* User Type and Role Badges */}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label={userProfile.user_type === 'cliente' ? 'Cliente' : 'Funcionario'}
              size="small"
              color={getUserTypeBadgeColor(userProfile.user_type)}
              sx={{ fontSize: '0.75rem', height: 24 }}
            />
            <Chip
              label={getRoleLabel(userProfile.role)}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem', height: 24 }}
            />
          </Box>

          {/* Company name for clients */}
          {userProfile.company_name && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: 'block', mt: 1 }}
            >
              <strong>Empresa:</strong> {userProfile.company_name}
            </Typography>
          )}
        </Box>

        <Divider />

        {/* Theme Toggle */}
        <MenuItem
          onClick={(e) => {
            e.stopPropagation();
            toggleTheme();
          }}
          sx={{ py: 1.5 }}
        >
          <ListItemIcon>
            {isDarkMode ? (
              <LightModeIcon fontSize="small" />
            ) : (
              <DarkModeIcon fontSize="small" />
            )}
          </ListItemIcon>
          <Typography variant="body2">
            {isDarkMode ? 'Modo Claro' : 'Modo Oscuro'}
          </Typography>
        </MenuItem>

        {/* Profile Option (Optional - could navigate to profile page) */}
        <MenuItem sx={{ py: 1.5 }}>
          <ListItemIcon>
            <PersonIcon fontSize="small" />
          </ListItemIcon>
          <Typography variant="body2">Mi Perfil</Typography>
        </MenuItem>

        <Divider />

        {/* Logout Option */}
        <MenuItem
          onClick={handleLogout}
          disabled={isLoggingOut}
          sx={{
            py: 1.5,
            color: 'error.main',
            '&:hover': {
              backgroundColor: 'error.light',
              color: 'error.dark',
            },
          }}
        >
          <ListItemIcon>
            {isLoggingOut ? (
              <CircularProgress size={20} color="error" />
            ) : (
              <LogoutIcon fontSize="small" sx={{ color: 'error.main' }} />
            )}
          </ListItemIcon>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {isLoggingOut ? 'Cerrando sesión...' : 'Cerrar Sesión'}
          </Typography>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default FKUserMenu;
