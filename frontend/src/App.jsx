import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout/Layout';

import { Dashboard } from './pages/Dashboard';
import { Appointments } from './pages/Appointments';
import { Services } from './pages/Services';
import { Schedule } from './pages/Schedule';
import { Clients } from './pages/Clients';
import { BotSettings } from './pages/BotSettings';
import { SuperAdmin } from './pages/SuperAdmin';
import { Login } from './pages/Login';

const PrivateRoute = ({ children }) => {
  const { tenant, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Загрузка приложения...
      </div>
    );
  }

  return tenant ? <Layout>{children}</Layout> : <Navigate to="/login" replace />;
};

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/appointments"
            element={
              <PrivateRoute>
                <Appointments />
              </PrivateRoute>
            }
          />
          <Route
            path="/services"
            element={
              <PrivateRoute>
                <Services />
              </PrivateRoute>
            }
          />
          <Route
            path="/schedule"
            element={
              <PrivateRoute>
                <Schedule />
              </PrivateRoute>
            }
          />
          <Route
            path="/clients"
            element={
              <PrivateRoute>
                <Clients />
              </PrivateRoute>
            }
          />
          <Route
            path="/bot-settings"
            element={
              <PrivateRoute>
                <BotSettings />
              </PrivateRoute>
            }
          />
          <Route
            path="/superadmin"
            element={
              <PrivateRoute>
                <SuperAdmin />
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
