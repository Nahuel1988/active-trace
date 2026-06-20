import { api } from '@/shared/services/api';
import type {
  SlotEncuentro,
  InstanciaEncuentro,
  SlotCreateRequest,
  InstanciaEditRequest,
  InstanciaFilters,
} from '../types';

export function fetchSlots(materia_id?: string): Promise<SlotEncuentro[]> {
  const params = materia_id ? { materia_id } : undefined;
  return api.get('/api/encuentros/slots', { params }).then((r) => r.data);
}

export function crearSlot(data: SlotCreateRequest): Promise<SlotEncuentro> {
  return api.post('/api/encuentros/slots', data).then((r) => r.data);
}

export function fetchSlot(slot_id: string): Promise<SlotEncuentro> {
  return api.get(`/api/encuentros/slots/${slot_id}`).then((r) => r.data);
}

export function eliminarSlot(slot_id: string): Promise<void> {
  return api.delete(`/api/encuentros/slots/${slot_id}`);
}

export function fetchInstancias(filters?: InstanciaFilters): Promise<InstanciaEncuentro[]> {
  return api.get('/api/encuentros/instancias', { params: filters }).then((r) => r.data);
}

export function fetchInstancia(instancia_id: string): Promise<InstanciaEncuentro> {
  return api.get(`/api/encuentros/instancias/${instancia_id}`).then((r) => r.data);
}

export function editarInstancia(
  instancia_id: string,
  data: InstanciaEditRequest,
): Promise<InstanciaEncuentro> {
  return api.patch(`/api/encuentros/instancias/${instancia_id}`, data).then((r) => r.data);
}

export function exportarHTML(slot_id: string): Promise<string> {
  return api.get(`/api/encuentros/slots/${slot_id}/html`, { responseType: 'text' }).then((r) => r.data);
}
