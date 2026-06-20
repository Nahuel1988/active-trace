import { useQuery } from '@tanstack/react-query';
import { fetchCola } from '@/features/comunicaciones/services/comunicacionesApi';
import type { ComunicacionEstado, ComunicacionResponse } from '@/features/comunicaciones/types';

const terminalStates: ComunicacionEstado[] = ['enviado', 'error', 'cancelado'];

function hasNonTerminal(items: ComunicacionResponse[]): boolean {
  return items.some((item) => !terminalStates.includes(item.estado));
}

export function useColaComunicaciones(materia_id?: string) {
  return useQuery({
    queryKey: ['comunicaciones-cola', materia_id],
    queryFn: () => fetchCola(materia_id),
    enabled: !!materia_id,
    refetchInterval: (query) => {
      const data = query.state.data as ComunicacionResponse[] | undefined;
      if (!data || data.length === 0) return false;
      return hasNonTerminal(data) ? 5000 : false;
    },
  });
}
