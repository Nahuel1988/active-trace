import { api } from '@/shared/services/api';
import type {
  PreviewRequest,
  PreviewResponse,
  EnviarRequest,
  EnviarResponse,
  ComunicacionResponse,
} from '@/features/comunicaciones/types';

export function previewComunicacion(payload: PreviewRequest): Promise<PreviewResponse> {
  return api.post('/api/v1/comunicaciones/preview', payload).then(r => r.data);
}

export function enviarComunicacion(payload: EnviarRequest): Promise<EnviarResponse> {
  return api.post('/api/v1/comunicaciones', payload).then(r => r.data);
}

export function fetchCola(materia_id?: string): Promise<ComunicacionResponse[]> {
  return api.get('/api/v1/comunicaciones', {
    params: { materia_id },
  }).then(r => r.data);
}

export function aprobarComunicacion(comunicacion_id: string): Promise<ComunicacionResponse> {
  return api.post(`/api/v1/comunicaciones/${comunicacion_id}/aprobar`).then(r => r.data);
}

export function cancelarComunicacion(comunicacion_id: string): Promise<ComunicacionResponse> {
  return api.post(`/api/v1/comunicaciones/${comunicacion_id}/cancelar`).then(r => r.data);
}

export function aprobarLote(lote_id: string): Promise<{ total: number }> {
  return api.post(`/api/v1/comunicaciones/lote/${lote_id}/aprobar`).then(r => r.data);
}

export function cancelarLote(lote_id: string): Promise<{ total: number }> {
  return api.post(`/api/v1/comunicaciones/lote/${lote_id}/cancelar`).then(r => r.data);
}
