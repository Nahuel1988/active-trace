import { useMutation, useQueryClient } from '@tanstack/react-query';
import { equiposKeys } from '@/features/equipos/hooks/equiposKeys';
import {
  crearAsignacionMasiva,
  clonarEquipo,
  actualizarVigencia,
  crearAsignacion,
  eliminarAsignacion,
} from '@/features/equipos/services/equiposApi';
import type {
  AsignacionMasivaRequest,
  ClonarRequest,
  VigenciaRequest,
} from '@/features/equipos/types';

export function useAsignacionMasiva() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AsignacionMasivaRequest) =>
      crearAsignacionMasiva(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equiposKeys.lists() });
      queryClient.invalidateQueries({ queryKey: equiposKeys.asignaciones() });
    },
  });
}

export function useClonarEquipo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ClonarRequest) => clonarEquipo(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equiposKeys.lists() });
    },
  });
}

export function useActualizarVigencia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: VigenciaRequest) => actualizarVigencia(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equiposKeys.lists() });
    },
  });
}

export function useCrearAsignacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      equipo_id: string;
      user_id: string;
      rol: string;
      responsable?: boolean;
      vigencia_desde: string;
      vigencia_hasta: string;
    }) => crearAsignacion(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equiposKeys.asignaciones() });
    },
  });
}

export function useEliminarAsignacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => eliminarAsignacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: equiposKeys.asignaciones() });
    },
  });
}
