import axios from 'axios';

// Automatically detect Cloudflare Tunnel environment or fallback to localhost
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (typeof window !== 'undefined' && window.location.hostname.includes('trycloudflare.com')) {
    return 'https://cups-arrangements-processing-hoped.trycloudflare.com';
  }
  return 'http://localhost:8000';
};

const API = axios.create({
  baseURL: getApiBaseUrl(),
});

export const getScenarios = () => API.get('/scenarios');
export const runInvestigation = (scenarioId, customQuery) =>
  API.post('/investigate', { scenario_id: scenarioId, custom_query: customQuery });
export const getGraph = (investigationId) =>
  API.get(`/graph/${investigationId}`);
