import React, { useEffect } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

const ProtectedRoute: React.FC = () => {
  const location = useLocation();
  const isAuthenticated = !!localStorage.getItem('token');

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Store the current location they were trying to go to
    const redirectTo = location.pathname !== '/login' ? `?redirect=${encodeURIComponent(location.pathname)}` : '';
    return <Navigate to={`/login${redirectTo}`} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
