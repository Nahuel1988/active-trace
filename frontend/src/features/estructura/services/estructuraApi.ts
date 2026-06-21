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
  Cohorte,
  CohorteFormData,
  Materia,
  MateriaFormData,
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

// ── Cohortes ─────────────────────────────────────────────────────────────────

export function fetchCohortes(): Promise<Cohorte[]> {
  return api.get('/api/v1/estructura/cohortes').then((r) => r.data);
}

export function crearCohorte(data: CohorteFormData): Promise<Cohorte> {
  return api.post('/api/v1/estructura/cohortes', data).then((r) => r.data);
}

export function actualizarCohorte(
  id: string,
  data: Partial<CohorteFormData>,
): Promise<Cohorte> {
  return api.put(`/api/v1/estructura/cohortes/${id}`, data).then((r) => r.data);
}

export function eliminarCohorte(id: string): Promise<void> {
  return api.delete(`/api/v1/estructura/cohortes/${id}`).then(() => undefined);
}

// ── Materias ─────────────────────────────────────────────────────────────────

export function fetchMaterias(): Promise<Materia[]> {
  return api.get('/api/v1/estructura/materias').then((r) => r.data);
}

export function crearMateria(data: MateriaFormData): Promise<Materia> {
  return api.post('/api/v1/estructura/materias', data).then((r) => r.data);
}

export function actualizarMateria(
  id: string,
  data: Partial<MateriaFormData>,
): Promise<Materia> {
  return api.put(`/api/v1/estructura/materias/${id}`, data).then((r) => r.data);
}
