import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  previewComunicacion,
  enviarComunicacion,
  fetchCola,
  aprobarLote,
  cancelarLote,
  aprobarComunicacion,
  cancelarComunicacion,
} from '@/features/comunicaciones/services/comunicacionesApi';
import type {
  PreviewRequest,
  EnviarRequest,
} from '@/features/comunicaciones/types';

export function useComunicacionPreview() {
  return useMutation({
    mutationFn: (payload: PreviewRequest) => previewComunicacion(payload),
  });
}

export function useEnviarComunicacion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: EnviarRequest) => enviarComunicacion(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comunicaciones-cola'] });
    },
  });
}
