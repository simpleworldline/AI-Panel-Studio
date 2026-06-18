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
  if (config.params && typeof config.params === 'object') {
    config.params = keysToSnake({ ...config.params });
  }
  return config;
});

// ── Response: snake_case → camelCase ──
apiClient.interceptors.response.use(
  (res) => {
    if (res.data && typeof res.data === 'object') {
      res.data = keysToCamel(res.data);
    }
    return res.data;
  },
  (err) => {
    const data = err.response?.data ? keysToCamel(err.response.data) : null;
    // 优先取 message，其次 detail（FastAPI HTTPException），最后通用文案
    const message = data?.message || data?.detail || '网络错误，请稍后重试';
    const code = data?.code || err.response?.status || 0;
    return Promise.reject({ message, code });
  },
);
