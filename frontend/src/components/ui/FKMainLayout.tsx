/**
 * FKMainLayout - Main application layout with navbar and sidebar
 */
import React from 'react';
import { Box, Toolbar } from '@mui/material';
import { Outlet } from 'react-router-dom';
import FKTopNavbar from './FKTopNavbar';
import FKSidebarWithCollapse from './FKSidebarWithCollapse';

const FKMainLayout: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <FKTopNavbar />
      <FKSidebarWithCollapse />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: 'background.default',
          minHeight: '100vh',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default FKMainLayout;
