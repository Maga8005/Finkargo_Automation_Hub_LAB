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
import OperationsPagaLocalColombia from './pages/operations/OperationsPagaLocalColombia';
import ClientDashboard from './pages/ClientDashboard';
import LoginPage from './pages/LoginPage';
import ReporteriaAutomaticaCO from './pages/finance/ReporteriaAutomaticaCO';
import ReporteriaAutomaticaMX from './pages/finance/ReporteriaAutomaticaMX';
import PlantillasNetSuite from './pages/tesoreria/PlantillasNetSuite';
import PlantillasNetSuiteCO from './pages/tesoreria/PlantillasNetSuiteCO';
import PlantillasNetSuiteMX from './pages/tesoreria/PlantillasNetSuiteMX';
import BrokersPage from './pages/alianzas/BrokersPage';
import ComisionesCalculo from './pages/alianzas/ComisionesCalculo';
import PagosHistorial from './pages/alianzas/PagosHistorial';
import BrokerIncentivesPage from './pages/alianzas/BrokerIncentivesPage';
import HistorialMatchingPage from './pages/treasury/HistorialMatchingPage';
import DirectoryScannerPage from './pages/treasury/DirectoryScannerPage';
import RiskDashboard from './pages/risk/RiskDashboard';
import RiskEvaluationDetail from './pages/risk/RiskEvaluationDetail';
import RiskConfiguration from './pages/risk/RiskConfiguration';
import ReglasClasificacionPA from './pages/finance/ReglasClasificacionPA';
import ReportePA from './pages/finance/ReportePA';
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

              {/* Finance Routes - PA Classification */}
              <Route
                path="finance/reporte-pa"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.FINANCE, UserRole.FINANCE_ADMIN, UserRole.ADMIN]}>
                    <ReportePA />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="finance/reglas-clasificacion-pa"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.FINANCE_ADMIN, UserRole.ADMIN]}>
                    <ReglasClasificacionPA />
                  </RoleProtectedRoute>
                }
              />

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
              <Route
                path="treasury/declaration-matching"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>
                    <HistorialMatchingPage />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="treasury/directory-scanner"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>
                    <DirectoryScannerPage />
                  </RoleProtectedRoute>
                }
              />

              {/* Operations Routes - Country-specific contracts */}
              <Route
                path="operations/contratos-colombia"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.OPERATIONS]}>
                    <OperationsContractsColombia />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="operations/contratos-mexico"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.OPERATIONS]}>
                    <OperationsContractsMexico />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="operations/paga-local-colombia"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.OPERATIONS, UserRole.COMERCIAL_PAGA_LOCAL]}>
                    <OperationsPagaLocalColombia />
                  </RoleProtectedRoute>
                }
              />

              {/* Alianzas Routes - Broker management */}
              <Route
                path="alianzas/brokers"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>
                    <BrokersPage />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="alianzas/comisiones"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>
                    <ComisionesCalculo />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="alianzas/pagos"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>
                    <PagosHistorial />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="alianzas/incentivos"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>
                    <BrokerIncentivesPage />
                  </RoleProtectedRoute>
                }
              />

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
              {/* Alianzas department route - Redirect to brokers page */}
              <Route
                path="department/alianzas"
                element={<Navigate to="/alianzas/brokers" replace />}
              />

              {/* Risk Routes - Fraud detection and risk management */}
              <Route
                path="risk/dashboard"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.RISK_ANALYST, UserRole.RISK_MANAGER, UserRole.ADMIN]}>
                    <RiskDashboard />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="risk/evaluations/:id"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.RISK_ANALYST, UserRole.RISK_MANAGER, UserRole.ADMIN]}>
                    <RiskEvaluationDetail />
                  </RoleProtectedRoute>
                }
              />
              <Route
                path="risk/configuration"
                element={
                  <RoleProtectedRoute allowedRoles={[UserRole.RISK_MANAGER, UserRole.ADMIN]}>
                    <RiskConfiguration />
                  </RoleProtectedRoute>
                }
              />
              {/* Risk department route - Redirect to risk dashboard */}
              <Route
                path="department/risk"
                element={<Navigate to="/risk/dashboard" replace />}
              />

              {/* Finance department route - Redirect to PA report (most common use case) */}
              <Route
                path="department/finance"
                element={<Navigate to="/finance/reporte-pa" replace />}
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
