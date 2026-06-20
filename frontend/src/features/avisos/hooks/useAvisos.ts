// ── useAvisos ─────────────────────────────────────────────────────────────────
// Hooks de React Query para el módulo de avisos.

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as avisosApi from '@/features/avisos/services/avisosApi';
import type { AvisoFormData } from '@/features/avisos/types';

const queryKeys = {
  all: ['avisos'] as const,
  detail: (id: string) => ['avisos', id] as const,
};

export function useAvisos() {
  return useQuery({
    queryKey: queryKeys.all,
    queryFn: avisosApi.fetchAvisos,
  });
}

export function useAviso(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.detail(id!),
    queryFn: () => avisosApi.fetchAviso(id!),
    enabled: !!id,
  });
}

export function useCrearAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AvisoFormData) => avisosApi.crearAviso(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.all });
    },
  });
}

export function useActualizarAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AvisoFormData & { activo: boolean }> }) =>
      avisosApi.actualizarAviso(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.detail(variables.id) });
    },
  });
}

export function useEliminarAviso() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => avisosApi.eliminarAviso(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.all });
    },
  });
}
