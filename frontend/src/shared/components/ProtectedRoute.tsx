// ── ProtectedRoute ───────────────────────────────────────────────────────────
// Guard de rutas. Sin sesión → redirige a /login con returnTo.
// Con sesión pero sin permiso → redirige a /403.
// Con sesión y permiso → renderiza <Outlet />.
//
// D-04: Route guard como wrapper de ruta. El permiso es opcional.

import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { usePermission } from '@/shared/hooks/usePermission';

interface ProtectedRouteProps {
  /** Permiso requerido (opcional). Formato: `modulo:accion` */
  permission?: string;
}

export function ProtectedRoute({ permission }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  // Llamar usePermission SIEMPRE (hook incondicional) para mantener
  // el orden de hooks constante entre renders.
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const hasPermission = permission ? usePermission(permission) : true;

  // Mientras se resuelve el refresh silencioso, no redirigir
  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ returnTo: location.pathname + location.search }}
        replace
      />
    );
  }

  if (permission && !hasPermission) {
    return <Navigate to="/403" replace />;
  }

  return <Outlet />;
}
