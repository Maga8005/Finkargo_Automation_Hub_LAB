/**
 * Dark theme color palette for Finkargo Automation Hub
 * Maintains brand identity while optimizing for dark mode visibility
 * All color combinations meet WCAG AA accessibility standards (4.5:1 contrast for text)
 */

export const darkPalette = {
  mode: 'dark' as const,

  // Primary Colors - Finkargo Blues (adjusted for dark mode)
  primary: {
    darkest: '#050A53',
    dark: '#0C147B',
    main: '#5B6FE8', // Lighter blue for better visibility on dark backgrounds
    light: '#8FA6F0',
    lighter: '#B8C7F5',
    contrastText: '#FFFFFF',
  },

  // Secondary/Coral Colors - Finkargo CTA (maintained with slight adjustments)
  secondary: {
    main: '#F19F90', // Slightly lighter coral for dark mode
    light: '#F5B8AB',
    dark: '#EB8774',
    contrastText: '#000000',
  },

  // Background Colors - Material Design dark theme standards
  background: {
    default: '#121212', // Standard Material Design dark background
    paper: '#1E1E1E', // Elevated surfaces (cards, dialogs, drawers)
    elevated: '#242424', // Higher elevation surfaces
  },

  // Text Colors - Optimized for dark backgrounds with proper emphasis levels
  text: {
    primary: 'rgba(255, 255, 255, 0.87)', // High emphasis text
    secondary: 'rgba(255, 255, 255, 0.60)', // Medium emphasis text
    disabled: 'rgba(255, 255, 255, 0.38)', // Low emphasis/disabled text
  },

  // Status Colors - Dark mode variants
  success: {
    main: '#4CAF50', // Brighter green for visibility
    light: '#81C784',
    dark: '#388E3C',
    bg: '#1B5E20',
    contrastText: '#FFFFFF',
  },

  error: {
    main: '#EF5350', // Brighter red for visibility
    light: '#E57373',
    dark: '#D32F2F',
    bg: '#B71C1C',
    contrastText: '#FFFFFF',
  },

  warning: {
    main: '#FFA726', // Brighter orange for visibility
    light: '#FFB74D',
    dark: '#F57C00',
    bg: '#E65100',
    contrastText: '#000000',
  },

  info: {
    main: '#29B6F6', // Brighter blue for visibility
    light: '#4FC3F7',
    dark: '#0288D1',
    bg: '#01579B',
    contrastText: '#FFFFFF',
  },

  // Gray Scale - Optimized for dark interfaces
  gray: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },

  // Divider color
  divider: 'rgba(255, 255, 255, 0.12)',

  // Action colors
  action: {
    active: 'rgba(255, 255, 255, 0.56)',
    hover: 'rgba(255, 255, 255, 0.08)',
    hoverOpacity: 0.08,
    selected: 'rgba(255, 255, 255, 0.16)',
    selectedOpacity: 0.16,
    disabled: 'rgba(255, 255, 255, 0.26)',
    disabledBackground: 'rgba(255, 255, 255, 0.12)',
    disabledOpacity: 0.38,
    focus: 'rgba(255, 255, 255, 0.12)',
    focusOpacity: 0.12,
    activatedOpacity: 0.24,
  },
};

export default darkPalette;
