import { useQuery } from '@tanstack/react-query';
import { equiposKeys } from '@/features/equipos/hooks/equiposKeys';
import {
  fetchMisEquipos,
  fetchEquipos,
  fetchAsignaciones,
} from '@/features/equipos/services/equiposApi';
import type { EquipoFilters } from '@/features/equipos/types';

export function useMisEquipos() {
  return useQuery({
    queryKey: equiposKeys.misEquipos(),
    queryFn: fetchMisEquipos,
  });
}

export function useEquipos(filters?: EquipoFilters) {
  return useQuery({
    queryKey: equiposKeys.list(filters),
    queryFn: () => fetchEquipos(filters),
  });
}

export function useAsignaciones(equipoFilters?: { equipo_id?: string }) {
  return useQuery({
    queryKey: equiposKeys.asignacionesList(equipoFilters),
    queryFn: () => fetchAsignaciones(equipoFilters),
  });
}
