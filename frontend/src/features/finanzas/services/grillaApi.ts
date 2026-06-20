import { api } from '@/shared/services/api';
import type {
  SalarioBase,
  SalarioBaseFormData,
  SalarioPlus,
  SalarioPlusFormData,
  RolLiquidacion,
  GrupoPlus,
} from '@/features/finanzas/types';

export function fetchSalariosBase(rol?: RolLiquidacion): Promise<SalarioBase[]> {
  return api.get('/api/v1/grilla/salarios-base', { params: { rol } }).then((r) => r.data);
}

export function crearSalarioBase(data: SalarioBaseFormData): Promise<SalarioBase> {
  return api.post('/api/v1/grilla/salarios-base', data).then((r) => r.data);
}

export function actualizarSalarioBase(
  id: string,
  data: Partial<Pick<SalarioBaseFormData, 'monto' | 'hasta'>>,
): Promise<SalarioBase> {
  return api.put(`/api/v1/grilla/salarios-base/${id}`, data).then((r) => r.data);
}

export function eliminarSalarioBase(id: string): Promise<void> {
  return api.delete(`/api/v1/grilla/salarios-base/${id}`).then(() => undefined);
}

export function fetchSalariosPlus(grupo?: GrupoPlus): Promise<SalarioPlus[]> {
  return api.get('/api/v1/grilla/salarios-plus', { params: { grupo } }).then((r) => r.data);
}

export function crearSalarioPlus(data: SalarioPlusFormData): Promise<SalarioPlus> {
  return api.post('/api/v1/grilla/salarios-plus', data).then((r) => r.data);
}

export function actualizarSalarioPlus(
  id: string,
  data: Partial<Pick<SalarioPlusFormData, 'descripcion' | 'monto' | 'hasta'>>,
): Promise<SalarioPlus> {
  return api.put(`/api/v1/grilla/salarios-plus/${id}`, data).then((r) => r.data);
}

export function eliminarSalarioPlus(id: string): Promise<void> {
  return api.delete(`/api/v1/grilla/salarios-plus/${id}`).then(() => undefined);
}
