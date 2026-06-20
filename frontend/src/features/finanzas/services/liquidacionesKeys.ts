import type { HistorialFilters } from '@/features/finanzas/types';

export const liquidacionesKeys = {
  all: ['liquidaciones'] as const,
  vista: (cohorte_id: string, periodo: string, usuario_id?: string) =>
    ['liquidaciones', 'vista', cohorte_id, periodo, usuario_id] as const,
  historial: (filters: HistorialFilters) =>
    ['liquidaciones', 'historial', filters] as const,
};
