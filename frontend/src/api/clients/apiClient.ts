/**
 * API Client with Axios interceptors
 * Uses Supabase session for authentication
 * Bug fix: Improved session synchronization to prevent stale tokens
 * Performance fix v2: Removed competing IIFE session call - let onAuthStateChange handle it
 */
import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import { supabase } from '../../services/supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const API_KEY = import.meta.env.VITE_API_KEY;
const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 30000;

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY && { 'x-api-key': API_KEY }),
  },
});

// Cache session in memory to avoid repeated getSession() calls
let cachedSession: { access_token: string } | null = null;
let lastCacheUpdate = 0;
const CACHE_TTL = 5000; // 5 second cache TTL - increased to reduce getSession() calls

// REMOVED: Competing IIFE that called getSession() on module load
// This was causing redundant network calls competing with AuthContext
// The onAuthStateChange listener below will populate the cache when auth state changes

// Update cache when auth state changes - this is the primary way cache gets populated
supabase.auth.onAuthStateChange((_event, session) => {
  console.log(`[apiClient] Auth state changed:`, _event, session ? 'Has token' : 'No session');

  cachedSession = session;
  lastCacheUpdate = Date.now();

  if (_event === 'TOKEN_REFRESHED') {
    console.log('[apiClient] Token refreshed, cache updated');
  }
});

// Request interceptor - add token with cache freshness check
apiClient.interceptors.request.use(
  async (config) => {
    // Check if cache is stale (older than TTL)
    const cacheAge = Date.now() - lastCacheUpdate;
    if (cacheAge > CACHE_TTL || !cachedSession) {
      console.log('[apiClient] Cache stale or missing, refreshing from Supabase');
      try {
        const { data: { session } } = await supabase.auth.getSession();
        cachedSession = session;
        lastCacheUpdate = Date.now();
      } catch (error) {
        console.error('[apiClient] Error refreshing cache:', error);
      }
    }

    // Use cached session
    if (cachedSession?.access_token) {
      config.headers.Authorization = `Bearer ${cachedSession.access_token}`;
    } else {
      console.warn('[apiClient] No access token available for request');
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
    const originalRequest = error.config as typeof error.config & { _retry?: boolean };

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
