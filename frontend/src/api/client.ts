import axios from 'axios';
import { getSessionId } from '../utils/session';

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// 自动附加 Session ID
apiClient.interceptors.request.use((config) => {
  config.headers['X-Session-Id'] = getSessionId();
  return config;
});

// 统一响应解包
apiClient.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const message = err.response?.data?.message || '网络错误，请稍后重试';
    const code = err.response?.data?.code || err.response?.status || 0;
    const detail = err.response?.data?.detail || '';
    return Promise.reject({ message, code, detail });
  },
);
