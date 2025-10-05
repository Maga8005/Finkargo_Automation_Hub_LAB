/**
 * Finkargo Automation Hub - Main Application Component
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme/theme';
import FKMainLayout from './components/ui/FKMainLayout';
import HomePage from './pages/HomePage';
import DepartmentPage from './pages/DepartmentPage';
import LegalDashboard from './pages/legal/LegalDashboard';
import OperationsDashboard from './pages/operations/OperationsDashboard';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<FKMainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="department/legal" element={<LegalDashboard />} />
            <Route path="department/operations" element={<OperationsDashboard />} />
            <Route path="department/:departmentId" element={<DepartmentPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
