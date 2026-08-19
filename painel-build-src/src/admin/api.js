import axios from 'axios';

// Sempre usa URL relativa (/api) — funciona em qualquer domínio (Emergent preview, VPS, etc.)
// O proxy/ingress do servidor (nginx na VPS, ingress no Emergent) encaminha /api -> backend.
const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem('donas_admin_token');
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem('donas_admin_token');
      // HashRouter: rota de login fica após o '#'
      if (!window.location.hash.endsWith('/login')) {
        window.location.href = '/donaspainel/#/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;
