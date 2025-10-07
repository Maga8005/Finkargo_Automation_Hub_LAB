/**
 * API Client with Axios interceptors
 * Uses Supabase session for authentication
 */
import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import { supabase } from '../../services/supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 30000;

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cache session in memory to avoid repeated getSession() calls
let cachedSession: any = null;

// Initialize session cache immediately
(async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    cachedSession = session;
    console.log('[apiClient] Initial session loaded:', session ? 'Has token' : 'No session');
  } catch (error) {
    console.error('[apiClient] Error loading initial session:', error);
  }
})();

// Update cache when auth state changes
supabase.auth.onAuthStateChange((_event, session) => {
  console.log('[apiClient] Auth state changed:', _event, session ? 'Has token' : 'No session');
  cachedSession = session;
});

// Request interceptor - synchronous, just add token
apiClient.interceptors.request.use(
  (config) => {
    // Use cached session (synchronous)
    if (cachedSession?.access_token) {
      config.headers.Authorization = `Bearer ${cachedSession.access_token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token expiration
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response) {
      // Handle specific error codes
      switch (error.response.status) {
        case 401:
          // If this is the first 401 and we haven't retried yet
          if (!originalRequest._retry) {
            originalRequest._retry = true;
            console.log('[apiClient] 401 error, attempting to refresh session and retry...');

            try {
              // Force refresh session
              const { data: { session }, error: refreshError } = await supabase.auth.refreshSession();

              if (refreshError || !session) {
                console.error('[apiClient] Session refresh failed, signing out');
                await supabase.auth.signOut();
                window.location.href = '/login';
                return Promise.reject(error);
              }

              // Update cached session
              cachedSession = session;
              console.log('[apiClient] Session refreshed, retrying request');

              // Retry original request with new token
              originalRequest.headers.Authorization = `Bearer ${session.access_token}`;
              return apiClient(originalRequest);
            } catch (refreshError) {
              console.error('[apiClient] Error refreshing session:', refreshError);
              await supabase.auth.signOut();
              window.location.href = '/login';
              return Promise.reject(error);
            }
          } else {
            // Already retried, sign out
            console.error('[apiClient] 401 after retry, signing out');
            await supabase.auth.signOut();
            window.location.href = '/login';
          }
          break;
        case 403:
          console.error('Access forbidden');
          break;
        case 500:
          console.error('Server error');
          break;
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
