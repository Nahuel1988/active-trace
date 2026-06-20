import { useQuery } from '@tanstack/react-query';
import { fetchLiquidaciones, fetchHistorial } from '@/features/finanzas/services/liquidacionesApi';
import { liquidacionesKeys } from '@/features/finanzas/services/liquidacionesKeys';
import type { HistorialFilters } from '@/features/finanzas/types';

export function useLiquidaciones(cohorte_id: string, periodo: string, usuario_id?: string) {
  return useQuery({
    queryKey: liquidacionesKeys.vista(cohorte_id, periodo, usuario_id),
    queryFn: () => fetchLiquidaciones(cohorte_id, periodo, usuario_id),
    enabled: !!cohorte_id && !!periodo,
  });
}

export function useHistorial(filters: HistorialFilters) {
  return useQuery({
    queryKey: liquidacionesKeys.historial(filters),
    queryFn: () => fetchHistorial(filters),
  });
}
