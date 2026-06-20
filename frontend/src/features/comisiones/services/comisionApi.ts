import { api } from '@/shared/services/api';
import type { MateriaDTO, CohorteDTO } from '@/features/comisiones/types';

export function fetchMaterias(): Promise<MateriaDTO[]> {
  return api.get('/api/materias').then(r => r.data.materias);
}

export function fetchCohortes(materia_id: string): Promise<CohorteDTO[]> {
  return api.get('/api/cohortes', { params: { materia_id } }).then(r => r.data.cohortes);
}
