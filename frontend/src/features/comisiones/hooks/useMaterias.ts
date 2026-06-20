import { useQuery } from '@tanstack/react-query';
import { fetchMaterias, fetchCohortes } from '@/features/comisiones/services/comisionApi';

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: fetchMaterias,
  });
}

export function useCohortes(materia_id: string) {
  return useQuery({
    queryKey: ['cohortes', materia_id],
    queryFn: () => fetchCohortes(materia_id),
    enabled: !!materia_id,
  });
}
