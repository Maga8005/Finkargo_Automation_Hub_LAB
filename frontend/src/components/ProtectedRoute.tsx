/**
 * ProtectedRoute Component
 * Wrapper for routes that require authentication
 * Redirects to login if user is not authenticated
 * Bug fix: Added session recovery to prevent false redirects
 * Performance fix: Skip redundant recovery during auth transitions
 */
import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { CircularProgress, Box, Typography } from '@mui/material';
import { useAuth } from '../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

// Time window (in ms) after login during which we skip recovery attempts
const LOGIN_GRACE_PERIOD = 2000;

/**
 * ProtectedRoute - Guard component for authenticated routes
 *
 * Usage:
 * <Route path="/dashboard" element={
 *   <ProtectedRoute>
 *     <Dashboard />
 *   </ProtectedRoute>
 * } />
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading, revalidateSession, isTransitioning, lastLoginTimestamp } = useAuth();
  const [loadingTimeout, setLoadingTimeout] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [recoveryAttempted, setRecoveryAttempted] = useState(false);

  // Set a timeout to show a message if loading takes too long
  useEffect(() => {
    const timer = setTimeout(() => {
      if (loading) {
        setLoadingTimeout(true);
        console.warn('[ProtectedRoute] Authentication check is taking longer than expected');
      }
    }, 5000); // 5 second timeout

    return () => clearTimeout(timer);
  }, [loading]);

  // Attempt session recovery if not authenticated and recovery not yet attempted
  // Step 7: Skip recovery during auth transitions or within grace period after login
  useEffect(() => {
    const attemptRecovery = async () => {
      // Skip if auth is transitioning (login in progress)
      if (isTransitioning) {
        console.log('[ProtectedRoute] Auth transitioning, skipping recovery');
        return;
      }

      // Skip if we're within the grace period after a recent login
      const timeSinceLogin = Date.now() - lastLoginTimestamp;
      if (lastLoginTimestamp > 0 && timeSinceLogin < LOGIN_GRACE_PERIOD) {
        console.log('[ProtectedRoute] Within login grace period, skipping recovery');
        // Schedule a re-check after the grace period
        const remainingTime = LOGIN_GRACE_PERIOD - timeSinceLogin;
        setTimeout(() => {
          // Trigger a re-render to re-evaluate auth state
          setRecoveryAttempted(prev => prev);
        }, remainingTime + 100);
        return;
      }

      if (!isAuthenticated && !loading && !recoveryAttempted && !isRecovering) {
        console.log('[ProtectedRoute] User appears unauthenticated, attempting session recovery...');
        setIsRecovering(true);
        setRecoveryAttempted(true);

        try {
          const recovered = await revalidateSession();
          if (recovered) {
            console.log('[ProtectedRoute] Session recovered successfully!');
          } else {
            console.log('[ProtectedRoute] No valid session found, will redirect to login');
          }
        } catch (error) {
          console.error('[ProtectedRoute] Error during session recovery:', error);
        } finally {
          setIsRecovering(false);
        }
      }
    };

    attemptRecovery();
  }, [isAuthenticated, loading, recoveryAttempted, isRecovering, revalidateSession, isTransitioning, lastLoginTimestamp]);

  // Show loading spinner while checking authentication, recovering, or transitioning
  if (loading || isRecovering || isTransitioning) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress />
        {(isRecovering || isTransitioning) && (
          <Typography variant="body2" color="text.secondary">
            Verificando sesión...
          </Typography>
        )}
        {loadingTimeout && !isRecovering && !isTransitioning && (
          <Typography variant="body2" color="text.secondary">
            Cargando... Si esto toma mucho tiempo, intenta refrescar la página.
          </Typography>
        )}
      </Box>
    );
  }

  // Redirect to login if not authenticated (after recovery attempt)
  if (!isAuthenticated && recoveryAttempted) {
    console.log('[ProtectedRoute] Redirecting to login - no valid session found');
    return <Navigate to="/login" replace />;
  }

  // Render protected content if authenticated
  return <>{children}</>;
};

export default ProtectedRoute;
