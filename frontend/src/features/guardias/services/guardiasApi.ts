import { api } from '@/shared/services/api';
import type {
  Guardia,
  GuardiaCreateRequest,
  GuardiaFiltros,
  EstadoGuardia,
} from '../types';

export function fetchGuardias(filters?: GuardiaFiltros): Promise<Guardia[]> {
  return api.get('/api/guardias', { params: filters }).then((r) => r.data);
}

export function crearGuardia(data: GuardiaCreateRequest): Promise<Guardia> {
  return api.post('/api/guardias', data).then((r) => r.data);
}

export function fetchGuardia(id: string): Promise<Guardia> {
  return api.get(`/api/guardias/${id}`).then((r) => r.data);
}

export function cambiarEstado(
  id: string,
  estado: EstadoGuardia,
): Promise<Guardia> {
  return api
    .patch(`/api/guardias/${id}/estado`, { estado })
    .then((r) => r.data);
}

export function exportGuardiasCSV(filters?: GuardiaFiltros): Promise<Blob> {
  return api
    .get('/api/guardias/export', {
      params: filters ?? {},
      responseType: 'blob',
    })
    .then((r) => r.data);
}
