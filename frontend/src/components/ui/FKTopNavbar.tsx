/**
 * FKTopNavbar - Top navigation bar component
 */
import React from 'react';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';

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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
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
      </Toolbar>
    </AppBar>
  );
};

export default FKTopNavbar;
