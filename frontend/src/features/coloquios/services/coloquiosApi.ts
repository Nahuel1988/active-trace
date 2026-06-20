import { api } from '@/shared/services/api';
import type {
  Coloquio,
  ColoquioFormData,
  MetricasColoquios,
  AgendaItem,
  RegistroAcademico,
} from '../types';

export async function fetchColoquios(
  params?: { limit?: number; offset?: number },
): Promise<Coloquio[]> {
  const { data } = await api.get<Coloquio[]>('/api/v1/coloquios', { params });
  return data;
}

export async function crearColoquio(
  payload: ColoquioFormData,
): Promise<Coloquio> {
  const { data } = await api.post<Coloquio>('/api/v1/coloquios', payload);
  return data;
}

export async function fetchMetricas(): Promise<MetricasColoquios> {
  const { data } = await api.get<MetricasColoquios>(
    '/api/v1/coloquios/metricas',
  );
  return data;
}

export async function fetchAgenda(
  params?: {
    materia_id?: string;
    cohorte_id?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  },
): Promise<AgendaItem[]> {
  const { data } = await api.get<AgendaItem[]>('/api/v1/coloquios/agenda', {
    params,
  });
  return data;
}

export async function fetchRegistroAcademico(
  params?: { materia_id?: string; cohorte_id?: string },
): Promise<RegistroAcademico[]> {
  const { data } = await api.get<RegistroAcademico[]>(
    '/api/v1/coloquios/registro-academico',
    { params },
  );
  return data;
}
