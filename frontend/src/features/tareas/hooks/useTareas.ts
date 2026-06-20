import { useQuery } from '@tanstack/react-query';
import { tareasKeys } from '@/features/tareas/hooks/tareasKeys';
import * as tareasApi from '@/features/tareas/services/tareasApi';

export function useMisTareas() {
  return useQuery({
    queryKey: [...tareasKeys.all, 'mias'],
    queryFn: tareasApi.fetchMisTareas,
  });
}

export function useTareas(filters?: Record<string, string | undefined>) {
  return useQuery({
    queryKey: tareasKeys.list(filters),
    queryFn: () => tareasApi.fetchTareas(filters),
  });
}

export function useTarea(id: string) {
  return useQuery({
    queryKey: tareasKeys.detail(id),
    queryFn: () => tareasApi.fetchTarea(id),
    enabled: !!id,
  });
}

export function useComentarios(tareaId: string) {
  return useQuery({
    queryKey: tareasKeys.comentarios(tareaId),
    queryFn: () => tareasApi.fetchComentarios(tareaId),
    enabled: !!tareaId,
  });
}
