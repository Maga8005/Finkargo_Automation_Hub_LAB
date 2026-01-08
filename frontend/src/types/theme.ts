/**
 * Type definitions for the Finkargo theme system
 * Supports light and dark mode themes with persistent user preferences
 */

/**
 * Theme mode type - defines available theme options
 */
export type ThemeMode = 'light' | 'dark';

/**
 * Theme context interface - provides theme state and control functions
 */
export interface ThemeContextType {
  /** Current active theme mode */
  mode: ThemeMode;
  /** Toggle between light and dark themes */
  toggleTheme: () => void;
  /** Set a specific theme mode */
  setTheme: (mode: ThemeMode) => void;
  /** Computed boolean indicating if dark mode is active */
  isDarkMode: boolean;
}

/**
 * localStorage key for persisting theme preference
 */
export const THEME_STORAGE_KEY = 'finkargo_theme_mode';

/**
 * Default theme mode when no preference is stored
 */
export const DEFAULT_THEME_MODE: ThemeMode = 'light';
