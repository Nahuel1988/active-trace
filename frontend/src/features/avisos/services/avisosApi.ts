// ── avisosApi ─────────────────────────────────────────────────────────────────
// Wrapper tipado sobre la instancia Axios centralizada para endpoints de avisos.

import { api } from '@/shared/services/api';
import type { Aviso, AvisoFormData } from '@/features/avisos/types';

export function fetchAvisos(): Promise<Aviso[]> {
  return api.get('/api/v1/avisos/').then((r) => r.data);
}

export function fetchAviso(id: string): Promise<Aviso> {
  return api.get(`/api/v1/avisos/${id}`).then((r) => r.data);
}

export function crearAviso(data: AvisoFormData): Promise<Aviso> {
  return api.post('/api/v1/avisos/', data).then((r) => r.data);
}

export function actualizarAviso(id: string, data: Partial<AvisoFormData & { activo: boolean }>): Promise<Aviso> {
  return api.put(`/api/v1/avisos/${id}`, data).then((r) => r.data);
}

export function eliminarAviso(id: string): Promise<void> {
  return api.delete(`/api/v1/avisos/${id}`);
}
