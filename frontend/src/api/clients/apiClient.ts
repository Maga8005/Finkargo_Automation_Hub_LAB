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
let sessionCacheTime = 0;
const CACHE_DURATION = 5000; // 5 seconds

// Update cache when auth state changes
supabase.auth.onAuthStateChange((_event, session) => {
  cachedSession = session;
  sessionCacheTime = Date.now();
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Use cached session if available and recent
    const isCacheValid = cachedSession && (Date.now() - sessionCacheTime < CACHE_DURATION);

    if (isCacheValid && cachedSession?.access_token) {
      config.headers.Authorization = `Bearer ${cachedSession.access_token}`;
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
