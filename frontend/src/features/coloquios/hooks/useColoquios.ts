import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { coloquiosKeys } from './coloquiosKeys';
import {
  fetchColoquios,
  fetchMetricas,
  fetchAgenda,
  fetchRegistroAcademico,
  crearColoquio,
} from '../services/coloquiosApi';
import type { ColoquioFormData } from '../types';

export function useColoquios() {
  return useQuery({
    queryKey: coloquiosKeys.lists(),
    queryFn: fetchColoquios,
  });
}

export function useMetricas() {
  return useQuery({
    queryKey: coloquiosKeys.metricas(),
    queryFn: fetchMetricas,
  });
}

export function useAgenda(
  filters?: {
    materia_id?: string;
    cohorte_id?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  },
) {
  return useQuery({
    queryKey: coloquiosKeys.agenda(filters as Record<string, unknown> | undefined),
    queryFn: () => fetchAgenda(filters),
  });
}

export function useRegistroAcademico(
  filters?: { materia_id?: string; cohorte_id?: string },
) {
  return useQuery({
    queryKey: coloquiosKeys.registroAcademico(
      filters as Record<string, unknown> | undefined,
    ),
    queryFn: () => fetchRegistroAcademico(filters),
  });
}

export function useCrearColoquio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ColoquioFormData) => crearColoquio(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: coloquiosKeys.all });
    },
  });
}
