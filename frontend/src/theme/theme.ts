/**
 * Finkargo Design System - MUI Theme Configuration
 */
import { createTheme } from '@mui/material/styles';

declare module '@mui/material/styles' {
  interface Palette {
    coral: Palette['primary'];
  }
  interface PaletteOptions {
    coral?: PaletteOptions['primary'];
  }
}

const theme = createTheme({
  palette: {
    primary: {
      main: '#3C47D3',
      dark: '#0C147B',
      light: '#77A1E2',
      contrastText: '#FFFFFF',
    },
    coral: {
      main: '#EB8774',
      light: '#F19F90',
      dark: '#D97563',
      contrastText: '#FFFFFF',
    },
    success: {
      main: '#2CA14D',
      light: '#E0F7E6',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#CC071E',
      light: '#FFE4E4',
      contrastText: '#FFFFFF',
    },
    grey: {
      50: '#F9FAFB',
      100: '#F3F4F6',
      200: '#E5E7EB',
      300: '#D1D5DB',
      400: '#9CA3AF',
      500: '#6B7280',
      600: '#4B5563',
      700: '#374151',
      800: '#1F2937',
      900: '#111827',
    },
    background: {
      default: '#F9FAFB',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: "'Epilogue', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 720,
      md: 1024,
      lg: 1440,
      xl: 1920,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '12px 24px',
          fontSize: '1rem',
          fontWeight: 600,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
          },
          '&:active': {
            boxShadow: '0 1px 4px rgba(0, 0, 0, 0.1)',
          },
        },
        sizeLarge: {
          height: 52,
          padding: '14px 32px',
        },
        sizeMedium: {
          height: 44,
          padding: '12px 24px',
        },
        sizeSmall: {
          height: 36,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.12)',
          },
        },
        outlined: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: 24,
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            height: 48,
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: 'none',
          boxShadow: '2px 0 8px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          border: '1px solid rgba(0, 0, 0, 0.12)',
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
          '&:hover': {
            borderColor: 'rgba(60, 71, 211, 0.5)',
            backgroundColor: 'rgba(60, 71, 211, 0.04)',
          },
          '&.Mui-selected': {
            border: '1px solid',
            borderColor: '#3C47D3',
            backgroundColor: '#3C47D3',
            color: '#ffffff',
            '&:hover': {
              borderColor: '#0C147B',
              backgroundColor: '#0C147B',
            },
          },
          '&:focus': {
            outline: 'none',
          },
        },
      },
    },
    MuiToggleButtonGroup: {
      styleOverrides: {
        root: {
          gap: 8,
        },
      },
    },
  },
});

export default theme;
