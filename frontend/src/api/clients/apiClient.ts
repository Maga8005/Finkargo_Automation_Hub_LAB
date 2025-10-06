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

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Always use cached session (no time limit)
    if (cachedSession?.access_token) {
      config.headers.Authorization = `Bearer ${cachedSession.access_token}`;
      console.log('[apiClient] Request with auth token to:', config.url);
    } else {
      console.warn('[apiClient] Request WITHOUT auth token to:', config.url);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response) {
      // Handle specific error codes
      switch (error.response.status) {
        case 401:
          // Unauthorized - sign out and redirect to login
          await supabase.auth.signOut();
          window.location.href = '/login';
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
