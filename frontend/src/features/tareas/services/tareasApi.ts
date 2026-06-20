import { api } from '@/shared/services/api';
import type { Tarea, TareaFormData, Comentario } from '@/features/tareas/types';

export function fetchMisTareas(): Promise<Tarea[]> {
  return api.get('/api/tareas/mias').then((r) => r.data);
}

export function fetchTareas(
  filters?: Record<string, string | undefined>,
): Promise<Tarea[]> {
  const params = new URLSearchParams();
  if (filters) {
    for (const [k, v] of Object.entries(filters)) {
      if (v !== undefined && v !== '') {
        params.set(k, v);
      }
    }
  }
  const qs = params.toString();
  return api.get(`/api/tareas${qs ? `?${qs}` : ''}`).then((r) => r.data);
}

export function fetchTarea(id: string): Promise<Tarea> {
  return api.get(`/api/tareas/${id}`).then((r) => r.data);
}

export function crearTarea(data: TareaFormData): Promise<Tarea> {
  return api.post('/api/tareas', data).then((r) => r.data);
}

export function eliminarTarea(id: string): Promise<void> {
  return api.delete(`/api/tareas/${id}`);
}

export function reasignarTarea(id: string, asignado_a: string): Promise<Tarea> {
  return api.post(`/api/tareas/${id}/asignar`, { asignado_a }).then((r) => r.data);
}

export function cambiarEstado(id: string, estado: string): Promise<Tarea> {
  return api.patch(`/api/tareas/${id}/estado`, { estado }).then((r) => r.data);
}

export function fetchComentarios(tareaId: string): Promise<Comentario[]> {
  return api.get(`/api/tareas/${tareaId}/comentarios`).then((r) => r.data);
}

export function agregarComentario(tareaId: string, contenido: string): Promise<Comentario> {
  return api.post(`/api/tareas/${tareaId}/comentarios`, { contenido }).then((r) => r.data);
}
