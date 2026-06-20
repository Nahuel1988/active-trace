import { api } from '@/shared/services/api';
import type { LiquidacionVista, LiquidacionResumen, HistorialFilters } from '@/features/finanzas/types';

export function fetchLiquidaciones(
  cohorte_id: string,
  periodo: string,
  usuario_id?: string,
): Promise<LiquidacionVista> {
  return api
    .get('/api/v1/liquidaciones', { params: { cohorte_id, periodo, usuario_id } })
    .then((r) => r.data);
}

export function cerrarLiquidacion(id: string): Promise<{ id: string; estado: string }> {
  return api.post(`/api/v1/liquidaciones/${id}/cerrar`).then((r) => r.data);
}

export function fetchHistorial(filters: HistorialFilters): Promise<{ items: LiquidacionVista[] }> {
  return api
    .get('/api/v1/liquidaciones/historial', {
      params: { cohorte_id: filters.cohorte_id, periodo: filters.periodo, usuario_id: filters.usuario_id },
    })
    .then((r) => r.data);
}

export function calcularPeriodo(cohorte_id: string, periodo: string): Promise<LiquidacionResumen> {
  return api.post('/api/v1/liquidaciones/calcular', { cohorte_id, periodo }).then((r) => r.data);
}
