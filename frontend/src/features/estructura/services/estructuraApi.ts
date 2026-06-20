// ── estructuraApi ────────────────────────────────────────────────────────────
// Wrapper tipado sobre la instancia Axios centralizada para estructura académica.

import { api } from '@/shared/services/api';
import type {
  Carrera,
  CarreraFormData,
  Programa,
  FechaAcademica,
  FechaAcademicaFormData,
  FechaAcademicaUpdateData,
  CalendarioItem,
} from '@/features/estructura/types';

// ── Carreras ────────────────────────────────────────────────────────────────

export function fetchCarreras(): Promise<Carrera[]> {
  return api.get('/api/v1/estructura/carreras').then((r) => r.data);
}

export function crearCarrera(data: CarreraFormData): Promise<Carrera> {
  return api.post('/api/v1/estructura/carreras', data).then((r) => r.data);
}

// ── Programas ───────────────────────────────────────────────────────────────

export function fetchProgramas(params?: {
  materia_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
}): Promise<Programa[]> {
  return api.get('/api/v1/programas', { params }).then((r) => r.data);
}

export function crearPrograma(formData: FormData): Promise<Programa> {
  return api
    .post('/api/v1/programas', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data);
}

export function fetchPrograma(id: string): Promise<Programa> {
  return api.get(`/api/v1/programas/${id}`).then((r) => r.data);
}

// ── Fechas Académicas ───────────────────────────────────────────────────────

export function fetchFechas(params?: {
  materia_id?: string;
  cohorte_id?: string;
  tipo?: string;
}): Promise<FechaAcademica[]> {
  return api.get('/api/v1/fechas-academicas', { params }).then((r) => r.data);
}

export function crearFecha(data: FechaAcademicaFormData): Promise<FechaAcademica> {
  return api.post('/api/v1/fechas-academicas', data).then((r) => r.data);
}

export function actualizarFecha(
  id: string,
  data: FechaAcademicaUpdateData,
): Promise<FechaAcademica> {
  return api.put(`/api/v1/fechas-academicas/${id}`, data).then((r) => r.data);
}

export function fetchCalendario(params?: {
  materia_id?: string;
  cohorte_id?: string;
}): Promise<CalendarioItem[]> {
  return api
    .get('/api/v1/fechas-academicas/calendario', { params })
    .then((r) => r.data);
}
