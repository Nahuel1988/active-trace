// ── authApi ──────────────────────────────────────────────────────────────────
// Wrapper tipado sobre la instancia Axios centralizada para endpoints de auth.
// Todos los calls pasan por el interceptor de refresh transparente de api.ts.

import { api } from '@/shared/services/api';
import type {
  LoginRequest,
  LoginResponse,
  ResetRequest,
} from '@/features/auth/types';

export function login(data: LoginRequest): Promise<LoginResponse> {
  return api.post('/api/auth/login', data).then((r) => r.data);
}

export function verify2FA(code: string): Promise<LoginResponse> {
  return api.post('/api/auth/2fa/verify', { code }).then((r) => r.data);
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
