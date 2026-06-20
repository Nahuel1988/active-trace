// ── Instancia Axios centralizada ─────────────────────────────────────────────
// Único axios.create() del frontend. Nadie debe importar axios directamente
// ni crear instancias adicionales.
//
// D-01: Access token en memoria (no localStorage). Refresh token en cookie httpOnly.
// D-03: Refresh transparente con cola de requests fallidos.

import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios';

// ── ForbiddenError ───────────────────────────────────────────────────────────
// Error tipado para 403. La UI captura este error para mostrar mensajes.
// NO se redirige automáticamente — la UI decide cómo manejar el 403.
export class ForbiddenError extends Error {
  constructor(message?: string) {
    super(message ?? 'Forbidden');
    this.name = 'ForbiddenError';
  }
}

// ── Token management (memoria, nunca localStorage) ───────────────────────────
let accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

// ── Session expired callback ─────────────────────────────────────────────────
// Registrado por AuthContext al montar. Se invoca cuando el refresh falla.
let onSessionExpiredHandler: (() => void) | null = null;

export function setOnSessionExpired(handler: (() => void) | null): void {
  onSessionExpiredHandler = handler;
}

// ── Cola de requests fallidos (refresh queue) ────────────────────────────────
interface QueueItem {
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}

let isRefreshing = false;
let failedQueue: QueueItem[] = [];

function processQueue(error: unknown, token: string | null = null): void {
  if (error) {
    for (const item of failedQueue) {
      item.reject(error);
    }
  } else {
    for (const item of failedQueue) {
      item.resolve(token!);
    }
  }
  failedQueue = [];
}

// ── Axios instance ───────────────────────────────────────────────────────────
export const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL as string | undefined,
  withCredentials: true,
});

// ── Request interceptor: adjunta Authorization header ───────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: 401 → refresh transparente, 403 → ForbiddenError ──
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (!originalRequest) {
      return Promise.reject(error);
    }

    // ── 403: ForbiddenError (nunca redirigir automáticamente) ──
    if (error.response?.status === 403) {
      return Promise.reject(new ForbiddenError());
    }

    // ── 401: refresh transparente ──
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Si la request que falló ES el refresh, no reintentar — sesión expiró.
      // No redirigir si ya estamos en /login (evita loop infinito en refresh silencioso inicial).
      if (originalRequest.url === '/api/auth/refresh') {
        onSessionExpiredHandler?.();
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      // Ya hay un refresh en curso → encolar esta request
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((newToken) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        });
      }

      // Primer 401 → iniciar refresh
      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await api.post('/api/auth/refresh');
        const newToken: string = response.data.access_token;
        setAccessToken(newToken);
        processQueue(null, newToken);

        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        onSessionExpiredHandler?.();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);
