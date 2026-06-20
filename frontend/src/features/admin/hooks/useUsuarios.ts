// ── useUsuarios / useUsuario ───────────────────────────────────────────────
// Query hooks for Usuarios ABM.
// NOTE: useUsuario returns UsuarioDetalle (with PII). Only use inside
// UsuarioDetailPage or UsuarioFormPage — never pass PII downstream to list
// views or global state.

import { useQuery } from '@tanstack/react-query';
import { fetchUsuarios, fetchUsuario } from '@/features/admin/services/usuariosApi';
import { usuariosKeys } from '@/features/admin/services/usuariosKeys';
import type { UsuarioFilters } from '@/features/admin/types';

export function useUsuarios(filters: UsuarioFilters) {
  return useQuery({
    queryKey: usuariosKeys.list(filters),
    queryFn: () => fetchUsuarios(filters),
  });
}

export function useUsuario(id: string) {
  return useQuery({
    queryKey: usuariosKeys.detail(id),
    queryFn: () => fetchUsuario(id),
    enabled: !!id,
  });
}
