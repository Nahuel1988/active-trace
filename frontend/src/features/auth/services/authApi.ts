// ── authApi ──────────────────────────────────────────────────────────────────
// Wrapper tipado sobre la instancia Axios centralizada para endpoints de auth.
// Todos los calls pasan por el interceptor de refresh transparente de api.ts.

import { api, getAccessToken } from '@/shared/services/api';
import type {
  LoginRequest,
  LoginResponse,
  ResetRequest,
} from '@/features/auth/types';

export function login(data: LoginRequest): Promise<LoginResponse> {
  return api.post('/api/auth/login', data).then((r) => r.data);
}

export function verify2FA(code: string): Promise<LoginResponse> {
  // D-01: El challenge JWT se almacenó en memoria durante el login
  // (ver useLogin.ts linea 31: setAccessToken(response.access_token))
  // Lo recuperamos para pasarlo al endpoint junto con el código TOTP.
  const challenge = getAccessToken();
  return api.post('/api/auth/2fa/verify', { challenge, code }).then((r) => r.data);
}

export function requestRecovery(email: string): Promise<void> {
  return api.post('/api/auth/forgot', { email });
}

export function resetPassword(data: ResetRequest): Promise<void> {
  return api.post('/api/auth/reset', data);
}

export function refresh(): Promise<LoginResponse> {
  return api.post('/api/auth/refresh').then((r) => r.data);
}

export function logout(): Promise<void> {
  return api.post('/api/auth/logout');
}
