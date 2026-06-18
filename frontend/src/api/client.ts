import axios from 'axios';
import { getSessionId } from '../utils/session';
import { keysToSnake, keysToCamel } from '../utils/transform';

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request: Session ID + camelCase → snake_case ──
apiClient.interceptors.request.use((config) => {
  config.headers['X-Session-Id'] = getSessionId();
  if (config.data && typeof config.data === 'object' && !(config.data instanceof FormData)) {
    config.data = keysToSnake(config.data);
  }
  return config;
});

// ── Response: snake_case → camelCase + 解包 ──
apiClient.interceptors.response.use(
  (res) => {
    if (res.data) {
      res.data = keysToCamel(res.data);
    }
    return res.data;
  },
  (err) => {
    const data = err.response?.data ? keysToCamel(err.response.data) : null;
    const message = data?.message || '网络错误，请稍后重试';
    const code = data?.code || err.response?.status || 0;
    const detail = data?.detail || '';
    return Promise.reject({ message, code, detail });
  },
);
