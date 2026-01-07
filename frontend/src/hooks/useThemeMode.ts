/**
 * Custom hook for accessing theme context
 * Provides convenient access to theme mode and toggle functions
 */
import { useContext } from 'react';
import { ThemeContext } from '../contexts/ThemeContext';
import type { ThemeContextType } from '../types/theme';

/**
 * Hook to access theme mode and controls
 * @throws Error if used outside of ThemeProvider
 * @returns Theme context value with mode, toggleTheme, setTheme, and isDarkMode
 *
 * @example
 * const { mode, toggleTheme, isDarkMode } = useThemeMode();
 */
export const useThemeMode = (): ThemeContextType => {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useThemeMode must be used within a ThemeProvider');
  }

  return context;
};

export default useThemeMode;
