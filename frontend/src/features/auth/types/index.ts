// ── Tipos del feature auth ───────────────────────────────────────────────────
// Re-exportamos AuthUser desde shared context para mantener cohesión del módulo.

import type { AuthUser } from '@/shared/context/AuthContext';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: AuthUser;
  requires_2fa?: boolean;
}

export interface TwoFARequest {
  code: string;
}

export interface RecoveryRequest {
  email: string;
}

export interface ResetRequest {
  token: string;
  password: string;
  confirm_password: string;
}

export type { AuthUser };
