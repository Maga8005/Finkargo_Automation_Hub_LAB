/**
 * Finkargo Automation Hub - Main Application Component
 */
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleProtectedRoute from './components/RoleProtectedRoute';
import FKMainLayout from './components/ui/FKMainLayout';
import HomePage from './pages/HomePage';
import DepartmentPage from './pages/DepartmentPage';
import LegalDashboard from './pages/legal/LegalDashboard';
import OperationsContractsColombia from './pages/operations/OperationsContractsColombia';
import OperationsContractsMexico from './pages/operations/OperationsContractsMexico';
import ClientDashboard from './pages/ClientDashboard';
import LoginPage from './pages/LoginPage';
import ReporteriaAutomaticaCO from './pages/finance/ReporteriaAutomaticaCO';
import ReporteriaAutomaticaMX from './pages/finance/ReporteriaAutomaticaMX';
import PlantillasNetSuite from './pages/tesoreria/PlantillasNetSuite';
import PlantillasNetSuiteCO from './pages/tesoreria/PlantillasNetSuiteCO';
import PlantillasNetSuiteMX from './pages/tesoreria/PlantillasNetSuiteMX';
import { UserRole } from './types';

function App() {
  return (
    <ThemeProvider>
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

              {/* Client Dashboard - Accessible only by clients */}
              <Route
                path="client"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.CLIENTE]}>
                    <ClientDashboard />
                  </RoleProtectedRoute>
                }
              />

              {/* Finance Routes - Reportería Automática */}
              <Route path="finance/reporteria-automatica-co" element={<ReporteriaAutomaticaCO />} />
              <Route path="finance/reporteria-automatica-mx" element={<ReporteriaAutomaticaMX />} />

              {/* Treasury Routes - Plantillas NetSuite */}
              <Route path="tesoreria/plantillas-netsuite" element={<PlantillasNetSuite />} />
              <Route
                path="tesoreria/plantillas-netsuite/colombia"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>
                    <PlantillasNetSuiteCO />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="tesoreria/plantillas-netsuite/mexico"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>
                    <PlantillasNetSuiteMX />
                  </RoleProtectedRoute>
                }
              />

              {/* Operations Routes - Country-specific contracts */}
              <Route path="operations/contratos-colombia" element={<OperationsContractsColombia />} />
              <Route path="operations/contratos-mexico" element={<OperationsContractsMexico />} />

              {/* Department Routes - Accessible by funcionarios */}
              <Route
                path="department/legal"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.LEGAL]}>
                    <LegalDashboard />
                  </RoleProtectedRoute>
                }
              />
              {/* Legacy route - Redirect to Colombia contracts for backward compatibility */}
              <Route
                path="department/operations"
                element={<Navigate to="/operations/contratos-colombia" replace />}
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
