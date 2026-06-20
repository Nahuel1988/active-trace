import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as guardiasApi from '../services/guardiasApi';
import type {
  GuardiaCreateRequest,
  GuardiaFiltros,
  EstadoGuardia,
} from '../types';
import { guardiasKeys } from './guardiasKeys';

export function useGuardias(filters?: GuardiaFiltros) {
  return useQuery({
    queryKey: guardiasKeys.list(filters),
    queryFn: () => guardiasApi.fetchGuardias(filters),
  });
}

export function useGuardia(id: string) {
  return useQuery({
    queryKey: guardiasKeys.detail(id),
    queryFn: () => guardiasApi.fetchGuardia(id),
    enabled: !!id,
  });
}

export function useCrearGuardia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GuardiaCreateRequest) => guardiasApi.crearGuardia(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardiasKeys.lists() });
    },
  });
}

export function useCambiarEstadoGuardia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, estado }: { id: string; estado: EstadoGuardia }) =>
      guardiasApi.cambiarEstado(id, estado),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardiasKeys.lists() });
    },
  });
}
