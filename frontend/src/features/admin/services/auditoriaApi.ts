import { api } from '@/shared/services/api';
import type {
  AuditFilters,
  AuditLogFilters,
  AuditLogItem,
  MetricasAuditoria,
} from '../types';

export async function fetchMetricas(
  filters: AuditFilters,
): Promise<MetricasAuditoria> {
  const params = { desde: filters.desde, hasta: filters.hasta };
  const [
    acciones_por_dia,
    comunicaciones_por_docente,
    interacciones,
    ultimas_acciones,
  ] = await Promise.all([
    api
      .get('/api/v1/auditoria/metricas/acciones-por-dia', { params })
      .then((r) => r.data),
    api
      .get('/api/v1/auditoria/metricas/comunicaciones-por-docente', { params })
      .then((r) => r.data),
    api
      .get('/api/v1/auditoria/metricas/interacciones', { params })
      .then((r) => r.data),
    api
      .get('/api/v1/auditoria/metricas/ultimas-acciones', {
        params: { limite: 200 },
      })
      .then((r) => r.data),
  ]);
  return {
    acciones_por_dia,
    comunicaciones_por_docente,
    interacciones,
    ultimas_acciones,
  };
}

export async function fetchAuditLog(
  filters: AuditLogFilters,
): Promise<AuditLogItem[]> {
  const { data } = await api.get<AuditLogItem[]>('/api/v1/auditoria/log', {
    params: {
      desde: filters.desde,
      hasta: filters.hasta,
      materia_id: filters.materia_id,
      actor_id: filters.actor_id,
      accion: filters.accion,
    },
  });
  return data;
}
