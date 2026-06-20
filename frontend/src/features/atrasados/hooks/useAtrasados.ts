import { useQuery } from '@tanstack/react-query';
import {
  fetchAtrasados,
  fetchRanking,
  fetchReportes,
  fetchNotasFinales,
  fetchEntregasPendientes,
} from '@/features/atrasados/services/atrasadosApi';

export function useAtrasados(materia_id: string, cohorte_id: string) {
  return useQuery({
    queryKey: ['atrasados', materia_id, cohorte_id],
    queryFn: () => fetchAtrasados(materia_id, cohorte_id),
    enabled: !!materia_id && !!cohorte_id,
  });
}

export function useRanking(materia_id: string, cohorte_id: string) {
  return useQuery({
    queryKey: ['ranking', materia_id, cohorte_id],
    queryFn: () => fetchRanking(materia_id, cohorte_id),
    enabled: !!materia_id && !!cohorte_id,
  });
}

export function useReportes(materia_id: string, cohorte_id: string) {
  return useQuery({
    queryKey: ['reportes', materia_id, cohorte_id],
    queryFn: () => fetchReportes(materia_id, cohorte_id),
    enabled: !!materia_id && !!cohorte_id,
  });
}

export function useNotasFinales(materia_id: string, cohorte_id: string) {
  return useQuery({
    queryKey: ['notas-finales', materia_id, cohorte_id],
    queryFn: () => fetchNotasFinales(materia_id, cohorte_id),
    enabled: !!materia_id && !!cohorte_id,
  });
}

export function useEntregasPendientes(materia_id: string, cohorte_id: string) {
  return useQuery({
    queryKey: ['entregas-pendientes', materia_id, cohorte_id],
    queryFn: () => fetchEntregasPendientes(materia_id, cohorte_id),
    enabled: !!materia_id && !!cohorte_id,
  });
}
