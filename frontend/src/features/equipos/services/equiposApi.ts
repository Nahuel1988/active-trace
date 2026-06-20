import { api } from '@/shared/services/api';
import type {
  Equipo,
  Asignacion,
  AsignacionMasivaRequest,
  AsignacionMasivaResult,
  EquipoFilters,
  ClonarRequest,
  ClonarResult,
  VigenciaRequest,
  RoleOption,
} from '@/features/equipos/types';

export function fetchRoles(): Promise<RoleOption[]> {
  return api.get('/api/v1/rbac/roles').then((r) => r.data);
}

export function fetchMisEquipos(): Promise<Equipo[]> {
  return api.get('/api/v1/equipos/mis-equipos').then((r) => r.data);
}

export function fetchEquipos(filters?: EquipoFilters): Promise<Equipo[]> {
  return api.get('/api/v1/equipos', { params: filters }).then((r) => r.data);
}

export function crearAsignacionMasiva(
  payload: AsignacionMasivaRequest,
): Promise<AsignacionMasivaResult> {
  return api.post('/api/v1/equipos/asignacion-masiva', payload).then((r) => r.data);
}

export function clonarEquipo(payload: ClonarRequest): Promise<ClonarResult> {
  return api.post('/api/v1/equipos/clonar', payload).then((r) => r.data);
}

export function actualizarVigencia(payload: VigenciaRequest): Promise<{ afectadas: number }> {
  return api.patch('/api/v1/equipos/vigencia', payload).then((r) => r.data);
}

export async function exportarEquipo(filters?: EquipoFilters): Promise<void> {
  const response = await api.get('/api/v1/equipos/export', {
    params: filters,
    responseType: 'blob',
  });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = `equipos_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function fetchAsignaciones(filters?: {
  equipo_id?: string;
}): Promise<Asignacion[]> {
  return api.get('/api/v1/asignaciones', { params: filters }).then((r) => r.data);
}

export function crearAsignacion(payload: {
  equipo_id: string;
  user_id: string;
  rol: string;
  responsable?: boolean;
  vigencia_desde: string;
  vigencia_hasta: string;
}): Promise<Asignacion> {
  return api.post('/api/v1/asignaciones', payload).then((r) => r.data);
}

export function eliminarAsignacion(id: string): Promise<void> {
  return api.delete(`/api/v1/asignaciones/${id}`);
}
