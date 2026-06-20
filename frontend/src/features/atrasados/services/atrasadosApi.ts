import { api } from '@/shared/services/api';
import type {
  AtrasadosResponse,
  RankingResponse,
  ReportesResponse,
  NotasFinalesResponse,
  EntregasPendientesResponse,
} from '@/features/atrasados/types';

export function fetchAtrasados(materia_id: string, cohorte_id: string): Promise<AtrasadosResponse> {
  return api.get('/api/v1/analisis/atrasados', {
    params: { materia_id, cohorte_id },
  }).then(r => r.data);
}

export function fetchRanking(materia_id: string, cohorte_id: string): Promise<RankingResponse> {
  return api.get('/api/v1/analisis/ranking', {
    params: { materia_id, cohorte_id },
  }).then(r => r.data);
}

export function fetchReportes(materia_id: string, cohorte_id: string): Promise<ReportesResponse> {
  return api.get('/api/v1/analisis/reportes', {
    params: { materia_id, cohorte_id },
  }).then(r => r.data);
}

export function fetchNotasFinales(materia_id: string, cohorte_id: string): Promise<NotasFinalesResponse> {
  return api.get('/api/v1/analisis/notas-finales', {
    params: { materia_id, cohorte_id },
  }).then(r => r.data);
}

export function fetchEntregasPendientes(materia_id: string, cohorte_id: string): Promise<EntregasPendientesResponse> {
  return api.get('/api/v1/analisis/entregas-pendientes', {
    params: { materia_id, cohorte_id },
  }).then(r => r.data);
}

export async function exportEntregasPendientes(materia_id: string, cohorte_id: string): Promise<void> {
  const response = await api.get('/api/v1/analisis/entregas-pendientes', {
    params: { materia_id, cohorte_id, format: 'csv' },
    responseType: 'blob',
  });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = `entregas_pendientes_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
