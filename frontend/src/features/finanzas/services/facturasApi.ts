import { api } from '@/shared/services/api';
import type { Factura, FacturaFormData, FacturaFilters } from '@/features/finanzas/types';

export function fetchFacturas(filters: FacturaFilters): Promise<Factura[]> {
  return api
    .get('/api/v1/facturas', { params: { periodo: filters.periodo, estado: filters.estado, usuario_id: filters.usuario_id } })
    .then((r) => r.data);
}

export function fetchFactura(id: string): Promise<Factura> {
  return api.get(`/api/v1/facturas/${id}`).then((r) => r.data);
}

export function crearFactura(data: FacturaFormData): Promise<Factura> {
  return api.post('/api/v1/facturas', data).then((r) => r.data);
}

export function actualizarFactura(
  id: string,
  data: Partial<Pick<FacturaFormData, 'detalle' | 'referencia_archivo' | 'tamano_kb'>>,
): Promise<Factura> {
  return api.put(`/api/v1/facturas/${id}`, data).then((r) => r.data);
}

export function abonarFactura(id: string): Promise<Factura> {
  return api.post(`/api/v1/facturas/${id}/abonar`).then((r) => r.data);
}
