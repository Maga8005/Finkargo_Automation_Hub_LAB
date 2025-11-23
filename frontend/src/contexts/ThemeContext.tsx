/**
 * Theme Context Provider
 * Manages theme mode state (light/dark) and persistence to localStorage
 */
/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useState, useEffect, useMemo } from 'react';
import type { ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { createAppTheme } from '../theme/theme';
import type { ThemeMode, ThemeContextType } from '../types/theme';
import { THEME_STORAGE_KEY, DEFAULT_THEME_MODE } from '../types/theme';

/**
 * Theme context for managing theme mode across the application
 */
export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Props for ThemeProvider component
 */
interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * Theme Provider component
 * Wraps the application with theme context and Material-UI ThemeProvider
 * Handles theme state management and localStorage persistence
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Read initial theme from localStorage, default to light mode
  const [mode, setMode] = useState<ThemeMode>(() => {
    try {
      const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
      if (savedTheme === 'light' || savedTheme === 'dark') {
        return savedTheme;
      }
    } catch (error) {
      console.warn('Failed to read theme from localStorage:', error);
    }
    return DEFAULT_THEME_MODE;
  });

  // Create theme instance based on current mode
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  // Persist theme preference to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch (error) {
      console.warn('Failed to save theme to localStorage:', error);
    }
  }, [mode]);

  /**
   * Toggle between light and dark themes
   */
  const toggleTheme = () => {
    setMode((prevMode: ThemeMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  /**
   * Set a specific theme mode
   * @param newMode - The theme mode to set
   */
  const setTheme = (newMode: ThemeMode) => {
    if (newMode === 'light' || newMode === 'dark') {
      setMode(newMode);
    }
  };

  // Context value with all theme controls
  const contextValue = useMemo<ThemeContextType>(
    () => ({
      mode,
      toggleTheme,
      setTheme,
      isDarkMode: mode === 'dark',
    }),
    [mode]
  );

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
