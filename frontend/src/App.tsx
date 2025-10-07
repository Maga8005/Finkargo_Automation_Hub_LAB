/**
 * Finkargo Automation Hub - Main Application Component
 */
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme/theme';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleProtectedRoute from './components/RoleProtectedRoute';
import FKMainLayout from './components/ui/FKMainLayout';
import HomePage from './pages/HomePage';
import DepartmentPage from './pages/DepartmentPage';
import LegalDashboard from './pages/legal/LegalDashboard';
import OperationsDashboard from './pages/operations/OperationsDashboard';
import LoginPage from './pages/LoginPage';
import { UserRole } from './types';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public route - Login */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected routes - Require authentication */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <FKMainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<HomePage />} />
              <Route
                path="department/legal"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.LEGAL]}>
                    <LegalDashboard />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="department/operations"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.OPERATIONS]}>
                    <OperationsDashboard />
                  </RoleProtectedRoute>
                }
              />
              <Route path="department/:departmentId" element={<DepartmentPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
