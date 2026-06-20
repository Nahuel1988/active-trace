import { useMutation, useQueryClient } from '@tanstack/react-query';
import { cerrarLiquidacion, calcularPeriodo } from '@/features/finanzas/services/liquidacionesApi';
import { liquidacionesKeys } from '@/features/finanzas/services/liquidacionesKeys';

export function useCerrarLiquidacion(cohorte_id: string, periodo: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => cerrarLiquidacion(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: liquidacionesKeys.vista(cohorte_id, periodo) });
      qc.invalidateQueries({ queryKey: ['liquidaciones', 'historial'] });
    },
  });
}

export function useCalcularPeriodo(cohorte_id: string, periodo: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => calcularPeriodo(cohorte_id, periodo),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: liquidacionesKeys.vista(cohorte_id, periodo) });
    },
  });
}
