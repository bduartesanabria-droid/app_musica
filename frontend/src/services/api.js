import axios from "axios";
import useAuthStore from "../store/authStore";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            original.headers.Authorization = `Bearer ${token}`;
            return api(original);
          })
          .catch((err) => Promise.reject(err));
      }

      original._retry = true;
      isRefreshing = true;

      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) {
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const response = await axios.post("/api/auth/refresh", null, {
          headers: { Authorization: `Bearer ${refreshToken}` },
        });
        const { access_token } = response.data;
        useAuthStore.getState().setTokens(access_token);
        processQueue(null, access_token);
        original.headers.Authorization = `Bearer ${access_token}`;
        return api(original);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
  changePassword: (data) => api.post("/auth/change-password", data),
  forgotPassword: (email) => api.post("/auth/forgot-password", { email }),
  resetPassword: (data) => api.post("/auth/reset-password", data),
};

export const usersService = {
  list: (params) => api.get("/users/", { params }),
  get: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  profile: (id) => api.get(`/users/${id}/profile`),
};

export const instrumentsService = {
  list: () => api.get("/instruments/"),
  get: (id) => api.get(`/instruments/${id}`),
  create: (data) => api.post("/instruments/", data),
  update: (id, data) => api.put(`/instruments/${id}`, data),
  notes: () => api.get("/instruments/notes"),
  scales: () => api.get("/instruments/scales"),
  intervals: () => api.get("/instruments/intervals"),
};

export const audioService = {
  list: (params) => api.get("/audio/", { params }),
  get: (id, waveform = false) => api.get(`/audio/${id}`, { params: { waveform } }),
  upload: (formData, onProgress) =>
    api.post("/audio/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: onProgress,
    }),
  update: (id, data) => api.put(`/audio/${id}`, data),
  delete: (id) => api.delete(`/audio/${id}`),
  stats: () => api.get("/audio/stats"),
  streamUrl: (filename) => `/api/audio/stream/${filename}`,
};

export const questionsService = {
  generate: (data) => api.post("/questions/generate", data),
  list: (params) => api.get("/questions/", { params }),
  get: (id) => api.get(`/questions/${id}`),
  create: (data) => api.post("/questions/", data),
  update: (id, data) => api.put(`/questions/${id}`, data),
  modes: () => api.get("/questions/modes"),
};

export const sessionsService = {
  create: (data) => api.post("/sessions/", data),
  submitAnswer: (sessionId, data) => api.post(`/sessions/${sessionId}/answer`, data),
  complete: (sessionId) => api.post(`/sessions/${sessionId}/complete`),
  list: (params) => api.get("/sessions/", { params }),
  get: (id) => api.get(`/sessions/${id}`),
};

export const progressService = {
  me: () => api.get("/progress/me"),
  badges: () => api.get("/progress/badges"),
  achievements: () => api.get("/progress/achievements"),
  dailyChallenge: () => api.get("/progress/daily-challenge"),
  weeklySummary: () => api.get("/progress/weekly-summary"),
};

export const statisticsService = {
  me: () => api.get("/statistics/me"),
  user: (id) => api.get(`/statistics/user/${id}`),
  global: () => api.get("/statistics/global"),
};

export const rankingsService = {
  global: (params) => api.get("/rankings/global", { params }),
  accuracy: (params) => api.get("/rankings/accuracy", { params }),
};

export default api;
