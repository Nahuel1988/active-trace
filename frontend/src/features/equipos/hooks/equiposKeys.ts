import type { EquipoFilters } from '@/features/equipos/types';

export const equiposKeys = {
  all: ['equipos'] as const,
  lists: () => [...equiposKeys.all, 'list'] as const,
  list: (filters?: EquipoFilters) => [...equiposKeys.lists(), filters] as const,
  details: () => [...equiposKeys.all, 'detail'] as const,
  detail: (id: string) => [...equiposKeys.details(), id] as const,
  misEquipos: () => [...equiposKeys.all, 'mis-equipos'] as const,
  asignaciones: () => [...equiposKeys.all, 'asignaciones'] as const,
  asignacionesList: (filters?: { equipo_id?: string }) =>
    [...equiposKeys.asignaciones(), filters] as const,
};
