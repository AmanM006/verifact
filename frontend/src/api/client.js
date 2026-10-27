import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const API = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'bypass-tunnel-reminder': '1',
  },
});

export const getScenarios = () => API.get('/scenarios');
export const runInvestigation = (scenarioId, customQuery) =>
  API.post('/investigate', { scenario_id: scenarioId, custom_query: customQuery });
export const getGraph = (investigationId) =>
  API.get(`/graph/${investigationId}`);
