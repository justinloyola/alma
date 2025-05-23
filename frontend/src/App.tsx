import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import LeadForm from './components/LeadForm';

interface HealthStatus {
  status: string;
}

const App: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<{
    loading: boolean;
    error: string | null;
    health: string | null;
  }>({
    loading: true,
    error: null,
    health: null,
  });

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
        const apiUrl = apiBaseUrl ? `${apiBaseUrl}/api` : '/api';
        
        const response = await axios.get<HealthStatus>(`${apiUrl}/health`);
        setApiStatus({
          loading: false,
          error: null,
          health: response.data.status,
        });
      } catch (error) {
        console.error('Error checking API health:', error);
        setApiStatus({
          loading: false,
          error: 'Unable to connect to the API server. Please make sure the backend is running.',
          health: null,
        });
      }
    };

    checkApiHealth();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            Alma Lead Management
          </h1>
          
          {apiStatus.loading ? (
            <p className="mt-4 text-lg text-gray-600">Checking API status...</p>
          ) : apiStatus.error ? (
            <div className="mt-4 p-4 bg-red-50 rounded-md">
              <p className="text-red-700">{apiStatus.error}</p>
              <p className="mt-2 text-sm text-red-600">
                Make sure the backend server is running and accessible.
              </p>
            </div>
          ) : (
            <p className="mt-4 text-lg text-gray-600">
              API Status: <span className="font-semibold text-green-600">Connected</span>
            </p>
          )}
        </header>

        <main className="max-w-3xl mx-auto">
          <LeadForm />
        </main>
      </div>
    </div>
  );
};

export default App;
