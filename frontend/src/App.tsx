import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, Navigate, useNavigate, useLocation } from 'react-router-dom';
import api from './config/axios';
import './App.css';
import LeadForm from './components/LeadForm';
import Login from './components/Login';
import LeadsTable from './components/LeadsTable';
import ProtectedRoute from './components/ProtectedRoute';

interface HealthStatus {
  status: string;
}

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [apiStatus, setApiStatus] = useState<{
    loading: boolean;
    error: string | null;
  }>({
    loading: true,
    error: null,
  });

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        await api.get<HealthStatus>('/api/v1/health');
        setApiStatus({ loading: false, error: null });
      } catch (error) {
        setApiStatus({
          loading: false,
          error: 'Unable to connect to the API server. Please make sure the backend is running.',
        });
      }
    };

    checkApiHealth();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <header className="flex justify-between items-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            <Link to="/" className="hover:text-gray-700">
              Alma Lead Management
            </Link>
          </h1>
          <nav className="flex items-center space-x-4">
            {localStorage.getItem('token') ? (
              <>
                <Link
                  to="/leads"
                  className="text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  Leads
                </Link>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Login
              </Link>
            )}
          </nav>
        </header>

        <main className="max-w-7xl mx-auto">
          {apiStatus.loading ? (
            <p className="text-center text-lg text-gray-600">Checking API status...</p>
          ) : apiStatus.error ? (
            <div className="p-4 bg-red-50 rounded-md">
              <p className="text-red-700">{apiStatus.error}</p>
              <p className="mt-2 text-sm text-red-600">
                Make sure the backend server is running and accessible.
              </p>
            </div>
          ) : (
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<LeadForm />} />
              <Route element={<ProtectedRoute />}>
                <Route path="/leads" element={<LeadsTable />} />
              </Route>
              <Route path="/debug" element={
                <div>
                  <h1>Debug Info</h1>
                  <pre>{JSON.stringify({
                    env: {
                      VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
                      NODE_ENV: import.meta.env.NODE_ENV,
                      MODE: import.meta.env.MODE,
                      PROD: import.meta.env.PROD,
                      DEV: import.meta.env.DEV,
                    },
                    location: window.location.href,
                  }, null, 2)}</pre>
                </div>
              } />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
