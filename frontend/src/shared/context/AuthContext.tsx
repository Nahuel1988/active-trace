// ── AuthContext ──────────────────────────────────────────────────────────────
// Estado de sesión del frontend. Token en memoria (useRef implícito via state),
// NUNCA en localStorage. D-01: refresh token en cookie httpOnly.
//
// D-02: AuthContext para estado de sesión. TanStack Query gestiona server state
// de features de dominio, NO la sesión de auth.
//
// D-03: Refresh silencioso al montar para recuperar sesión desde cookie httpOnly.
// El estado `isLoading` evita renderizar rutas hasta saber si hay sesión.

import {
  createContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import {
  api,
  setAccessToken,
  setOnSessionExpired,
} from '@/shared/services/api';

// ── Tipos ────────────────────────────────────────────────────────────────────
export interface AuthUser {
  user_id: string;
  tenant_id: string;
  roles: string[];
  permissions: string[];
}

export interface AuthState {
  /** Claims del JWT decodificado */
  user: AuthUser | null;
  /** Access token JWT (en memoria, nunca localStorage) */
  accessToken: string | null;
  /** true si hay usuario y NO está en estado pendingTwoFactor */
  isAuthenticated: boolean;
  /** true si el login fue exitoso pero falta verificar 2FA */
  pendingTwoFactor: boolean;
  /** true mientras se verifica si hay sesión activa (refresh silencioso) */
  isLoading: boolean;
}

export interface AuthContextValue extends AuthState {
  /** Establece la sesión tras login exitoso (o verify 2FA) */
  setSession: (user: AuthUser, accessToken: string) => void;
  /** Marca el estado de 2FA pendiente (login con 2FA activo) */
  setPendingTwoFactor: (value: boolean) => void;
  /** Limpia la sesión (logout, refresh fallido, etc.) */
  clearSession: () => void;
}

// ── Context ──────────────────────────────────────────────────────────────────
export const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ─────────────────────────────────────────────────────────────────
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [pendingTwoFactor, setPendingTwoFactorState] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const setSession = useCallback((newUser: AuthUser, newToken: string) => {
    setUser(newUser);
    setToken(newToken);
    setPendingTwoFactorState(false);
    // Sincronizar con el módulo api.ts para los interceptors
    setAccessToken(newToken);
  }, []);

  const clearSession = useCallback(() => {
    setUser(null);
    setToken(null);
    setPendingTwoFactorState(false);
    setAccessToken(null);
  }, []);

  const setPendingTwoFactor = useCallback((value: boolean) => {
    setPendingTwoFactorState(value);
  }, []);

  // ── Refresh silencioso al montar (recuperar sesión desde cookie httpOnly) ──
  useEffect(() => {
    let mounted = true;

    api
      .post('/api/auth/refresh')
      .then((response) => {
        if (!mounted) return;
        const { user: userData, access_token } = response.data as {
          user: AuthUser;
          access_token: string;
        };
        setSession(userData, access_token);
      })
      .catch(() => {
        // Sin sesión — comportamiento normal para usuarios no logueados
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [setSession]);

  // ── Registrar handler de sesión expirada (lo invoca el interceptor 401) ──
  useEffect(() => {
    setOnSessionExpired(() => {
      clearSession();
      window.location.href = '/login';
    });
    return () => {
      setOnSessionExpired(null);
    };
  }, [clearSession]);

  const value: AuthContextValue = {
    user,
    accessToken: token,
    isAuthenticated: user !== null && !pendingTwoFactor,
    pendingTwoFactor,
    isLoading,
    setSession,
    setPendingTwoFactor,
    clearSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
