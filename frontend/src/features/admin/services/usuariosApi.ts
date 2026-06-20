import { api } from '@/shared/services/api';
import type {
  Usuario,
  UsuarioDetalle,
  UsuarioFormData,
  UsuarioFilters,
} from '../types';

export async function fetchUsuarios(filters: UsuarioFilters): Promise<Usuario[]> {
  const { data } = await api.get<Usuario[]>('/api/v1/admin/usuarios', {
    params: {
      regional: filters.regional,
      facturador: filters.facturador,
      q: filters.q,
    },
  });
  return data;
}

export async function fetchUsuario(id: string): Promise<UsuarioDetalle> {
  const { data } = await api.get<UsuarioDetalle>(`/api/v1/admin/usuarios/${id}`);
  return data;
}

export async function crearUsuario(payload: UsuarioFormData): Promise<UsuarioDetalle> {
  const { data } = await api.post<UsuarioDetalle>('/api/v1/admin/usuarios', payload);
  return data;
}

export async function actualizarUsuario(
  id: string,
  payload: Partial<UsuarioFormData>,
): Promise<UsuarioDetalle> {
  const { data } = await api.put<UsuarioDetalle>(
    `/api/v1/admin/usuarios/${id}`,
    payload,
  );
  return data;
}

export async function eliminarUsuario(id: string): Promise<void> {
  await api.delete(`/api/v1/admin/usuarios/${id}`);
}
