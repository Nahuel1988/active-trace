import { useMutation, useQueryClient } from '@tanstack/react-query';
import { tareasKeys } from '@/features/tareas/hooks/tareasKeys';
import * as tareasApi from '@/features/tareas/services/tareasApi';
import type { TareaFormData } from '@/features/tareas/types';

export function useCrearTarea() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TareaFormData) => tareasApi.crearTarea(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tareasKeys.lists() });
    },
  });
}

export function useEliminarTarea() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tareasApi.eliminarTarea(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tareasKeys.lists() });
    },
  });
}

export function useReasignarTarea() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, asignado_a }: { id: string; asignado_a: string }) =>
      tareasApi.reasignarTarea(id, asignado_a),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tareasKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tareasKeys.details() });
    },
  });
}

export function useCambiarEstado() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: string }) =>
      tareasApi.cambiarEstado(id, estado),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tareasKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tareasKeys.details() });
    },
  });
}

export function useAgregarComentario(tareaId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (contenido: string) =>
      tareasApi.agregarComentario(tareaId, contenido),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: tareasKeys.comentarios(tareaId),
      });
    },
  });
}
