// ── usePermission ────────────────────────────────────────────────────────────
// Verifica si el usuario autenticado tiene un permiso específico.
// Retorna false si no hay sesión activa.

import { useAuth } from '@/shared/hooks/useAuth';

export function usePermission(perm: string): boolean {
  const { user } = useAuth();
  if (!user) return false;
  return user.permissions.includes(perm);
}
