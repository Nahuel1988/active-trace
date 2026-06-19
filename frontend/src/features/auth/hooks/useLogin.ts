// ── useLogin ─────────────────────────────────────────────────────────────────
// Hook que maneja el flujo completo de login/2FA:
// 1. Llama a authApi.login()
// 2. Si requires_2fa → almacena token temporal y setea pendingTwoFactor
// 3. Si no → setSession + redirige a returnTo o "/"

import { useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { setAccessToken } from '@/shared/services/api';
import * as authApi from '@/features/auth/services/authApi';
import type { LoginRequest } from '@/features/auth/types';

export function useLogin() {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { setSession, setPendingTwoFactor } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const login = useCallback(
    async (data: LoginRequest) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await authApi.login(data);

        if (response.requires_2fa) {
          // Almacenar token temporal para la verificación 2FA
          setAccessToken(response.access_token);
          setPendingTwoFactor(true);
        } else {
          setSession(response.user, response.access_token);
          const returnTo =
            (location.state as { returnTo?: string })?.returnTo ?? '/';
          navigate(returnTo, { replace: true });
        }
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Error de conexión');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [setSession, setPendingTwoFactor, navigate, location.state],
  );

  return { login, error, isLoading } as const;
}
