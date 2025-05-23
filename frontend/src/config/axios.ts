import axios from 'axios';

// Get the base URL and ensure it doesn't end with a slash
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
const baseUrl = apiBaseUrl.endsWith('/') ? apiBaseUrl.slice(0, -1) : apiBaseUrl;

// Create axios instance with default config
const api = axios.create({
  baseURL: baseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create a separate instance for form data requests
const formDataApi = axios.create({
  baseURL: baseUrl,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// Helper function to add interceptors to an axios instance
const addInterceptors = (instance: any) => {
  // Request interceptor
  instance.interceptors.request.use(
    (config: any) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: any) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response: any) => response,
    (error: any) => {
      // Handle 401 Unauthorized responses
      if (error.response?.status === 401) {
        // Don't redirect if already on login page
        if (window.location.pathname !== '/login') {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
  );
};

// Add interceptors to both instances
addInterceptors(api);
addInterceptors(formDataApi);

export { api, formDataApi };

export default api;
