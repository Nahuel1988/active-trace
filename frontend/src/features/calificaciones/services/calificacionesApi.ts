import { api } from '@/shared/services/api';
import type {
  CalificacionesPreviewResponse,
  CalificacionesCommitResponse,
  UmbralResponse,
} from '@/features/calificaciones/types';

export function previewCalificaciones(materia_id: string, file: File): Promise<CalificacionesPreviewResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/api/materias/${materia_id}/calificaciones/preview`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
}

export function commitCalificaciones(
  materia_id: string,
  import_id: string,
  actividades_seleccionadas: string[],
): Promise<CalificacionesCommitResponse> {
  return api.post(`/api/materias/${materia_id}/calificaciones/commit`, {
    import_id,
    actividades_seleccionadas,
  }).then(r => r.data);
}

export function getUmbral(materia_id: string): Promise<UmbralResponse> {
  return api.get(`/api/materias/${materia_id}/umbral`).then(r => r.data);
}

export function putUmbral(materia_id: string, umbral_porcentaje: number): Promise<void> {
  return api.put(`/api/materias/${materia_id}/umbral`, { umbral_porcentaje });
}
