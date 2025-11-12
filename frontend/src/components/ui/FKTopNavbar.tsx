/**
 * FKTopNavbar - Top navigation bar component with user menu
 */
import React from 'react';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import FKUserMenu from './FKUserMenu';

const FKTopNavbar: React.FC = () => {
  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: 'primary.dark',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      }}
    >
      <Toolbar>
        {/* Logo/Title - Left side */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
          <Typography
            variant="h5"
            component="h1"
            sx={{
              fontWeight: 700,
              color: 'white',
              letterSpacing: '0.5px'
            }}
          >
            Finkargo Automation HUB
          </Typography>
        </Box>

        {/* User Menu - Right side */}
        <FKUserMenu />
      </Toolbar>
    </AppBar>
  );
};

export default FKTopNavbar;
