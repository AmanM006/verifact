import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:8000' });

export const getScenarios = () => API.get('/scenarios');
export const runInvestigation = (scenarioId, customQuery) =>
  API.post('/investigate', { scenario_id: scenarioId, custom_query: customQuery });
export const getGraph = (investigationId) =>
  API.get(`/graph/${investigationId}`);
