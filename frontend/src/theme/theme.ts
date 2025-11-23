/**
 * Finkargo Design System - MUI Theme Configuration
 * Supports both light and dark themes with Finkargo branding
 */
import { createTheme } from '@mui/material/styles';
import type { ThemeOptions } from '@mui/material/styles';
import { darkPalette } from './darkTheme';
import type { ThemeMode } from '../types/theme';

declare module '@mui/material/styles' {
  interface Palette {
    coral: Palette['primary'];
  }
  interface PaletteOptions {
    coral?: PaletteOptions['primary'];
  }
}

/**
 * Light theme color palette - Original Finkargo design system
 */
const lightPalette = {
  mode: 'light' as const,
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
};

/**
 * Common theme configuration shared between light and dark themes
 */
const commonThemeOptions: Omit<ThemeOptions, 'palette'> = {
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
  transitions: {
    duration: {
      shortest: 150,
      shorter: 200,
      short: 250,
      standard: 300,
      complex: 375,
      enteringScreen: 225,
      leavingScreen: 195,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          transition: 'background-color 0.3s ease-in-out, color 0.3s ease-in-out',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '12px 24px',
          fontSize: '1rem',
          fontWeight: 600,
          boxShadow: 'none',
          transition: 'all 0.2s ease-in-out',
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
          transition: 'box-shadow 0.3s ease-in-out',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            height: 48,
            transition: 'background-color 0.2s ease-in-out',
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: 'none',
          transition: 'background-color 0.3s ease-in-out',
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
          transition: 'all 0.2s ease-in-out',
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
};

/**
 * Creates a theme based on the specified mode (light or dark)
 * @param mode - The theme mode ('light' or 'dark')
 * @returns A configured Material-UI theme object
 */
export const createAppTheme = (mode: ThemeMode = 'light') => {
  const isDark = mode === 'dark';
  const basePalette = isDark ? darkPalette : lightPalette;

  // Add coral color for both themes
  const coral = isDark
    ? {
        main: '#F19F90',
        light: '#F5B8AB',
        dark: '#EB8774',
        contrastText: '#000000',
      }
    : lightPalette.coral;

  return createTheme({
    ...commonThemeOptions,
    palette: {
      ...basePalette,
      coral,
    },
  });
};

// Export default theme for backward compatibility
export default createAppTheme('light');
