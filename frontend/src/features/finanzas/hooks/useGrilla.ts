import { useQuery } from '@tanstack/react-query';
import { fetchSalariosBase, fetchSalariosPlus } from '@/features/finanzas/services/grillaApi';
import { grillaKeys } from '@/features/finanzas/services/grillaKeys';
import type { RolLiquidacion, GrupoPlus } from '@/features/finanzas/types';

export function useSalariosBase(rol?: RolLiquidacion) {
  return useQuery({
    queryKey: grillaKeys.base.list(rol),
    queryFn: () => fetchSalariosBase(rol),
  });
}

export function useSalariosPlus(grupo?: GrupoPlus) {
  return useQuery({
    queryKey: grillaKeys.plus.list(grupo),
    queryFn: () => fetchSalariosPlus(grupo),
  });
}
