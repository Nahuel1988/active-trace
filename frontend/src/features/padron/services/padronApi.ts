import { api } from '@/shared/services/api';
import type { PadronPreviewResponse, PadronCommitResponse } from '@/features/padron/types';

export function previewPadron(materia_id: string, file: File): Promise<PadronPreviewResponse> {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/api/materias/${materia_id}/padron/preview`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
}

export function commitPadron(materia_id: string, import_id: string): Promise<PadronCommitResponse> {
  return api.post(`/api/materias/${materia_id}/padron/commit`, { import_id }).then(r => r.data);
}
