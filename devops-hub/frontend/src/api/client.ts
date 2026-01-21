import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for API key (if needed)
client.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey');
  // Only add API key header if it's a real key (not guest mode)
  if (apiKey && apiKey !== '__guest__') {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

export const apiClient = client;
export default client;
