// ── useUsuarioMutations ────────────────────────────────────────────────────
// Mutation hooks for Usuarios ABM (create / update / delete).

import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  crearUsuario,
  actualizarUsuario,
  eliminarUsuario,
} from '@/features/admin/services/usuariosApi';
import { usuariosKeys } from '@/features/admin/services/usuariosKeys';
import type { UsuarioFormData } from '@/features/admin/types';

export function useCrearUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UsuarioFormData) => crearUsuario(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: usuariosKeys.all });
    },
  });
}

export function useActualizarUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<UsuarioFormData> }) =>
      actualizarUsuario(id, data),
    onSuccess: (_result, variables) => {
      qc.invalidateQueries({ queryKey: usuariosKeys.lists() });
      qc.invalidateQueries({ queryKey: usuariosKeys.detail(variables.id) });
    },
  });
}

export function useEliminarUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => eliminarUsuario(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: usuariosKeys.all });
    },
  });
}
