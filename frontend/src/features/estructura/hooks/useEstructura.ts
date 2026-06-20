// ── Estructura Query Keys & Hooks ──────────────────────────────────────────

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/features/estructura/services/estructuraApi';
import type {
  CarreraFormData,
  FechaAcademicaFormData,
  FechaAcademicaUpdateData,
  CohorteFormData,
  MateriaFormData,
} from '@/features/estructura/types';

export const estructuraKeys = {
  all: ['estructura'] as const,
  carreras: () => [...estructuraKeys.all, 'carreras'] as const,
  programas: (filters?: Record<string, string | undefined>) =>
    [...estructuraKeys.all, 'programas', filters] as const,
  fechas: (filters?: Record<string, string | undefined>) =>
    [...estructuraKeys.all, 'fechas', filters] as const,
  calendario: (filters?: Record<string, string | undefined>) =>
    [...estructuraKeys.all, 'calendario', filters] as const,
  cohortes: () => [...estructuraKeys.all, 'cohortes'] as const,
  materias: () => [...estructuraKeys.all, 'materias'] as const,
};

// ── Carreras ────────────────────────────────────────────────────────────────

export function useCarreras() {
  return useQuery({
    queryKey: estructuraKeys.carreras(),
    queryFn: api.fetchCarreras,
  });
}

export function useCrearCarrera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CarreraFormData) => api.crearCarrera(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.carreras() });
    },
  });
}

// ── Programas ───────────────────────────────────────────────────────────────

export function useProgramas(filters?: {
  materia_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
}) {
  return useQuery({
    queryKey: estructuraKeys.programas(
      filters as Record<string, string | undefined>,
    ),
    queryFn: () => api.fetchProgramas(filters),
  });
}

export function useCrearPrograma() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => api.crearPrograma(formData),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.programas() });
    },
  });
}

// ── Fechas Académicas ───────────────────────────────────────────────────────

export function useFechas(filters?: {
  materia_id?: string;
  cohorte_id?: string;
  tipo?: string;
}) {
  return useQuery({
    queryKey: estructuraKeys.fechas(
      filters as Record<string, string | undefined>,
    ),
    queryFn: () => api.fetchFechas(filters),
  });
}

export function useCrearFecha() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FechaAcademicaFormData) => api.crearFecha(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.fechas() });
      qc.invalidateQueries({ queryKey: estructuraKeys.calendario() });
    },
  });
}

export function useActualizarFecha() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: FechaAcademicaUpdateData }) =>
      api.actualizarFecha(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.fechas() });
      qc.invalidateQueries({ queryKey: estructuraKeys.calendario() });
    },
  });
}

// ── Calendario ──────────────────────────────────────────────────────────────

export function useCalendario(filters?: {
  materia_id?: string;
  cohorte_id?: string;
}) {
  return useQuery({
    queryKey: estructuraKeys.calendario(
      filters as Record<string, string | undefined>,
    ),
    queryFn: () => api.fetchCalendario(filters),
  });
}

// ── Cohortes ─────────────────────────────────────────────────────────────────

export function useCohortes() {
  return useQuery({
    queryKey: estructuraKeys.cohortes(),
    queryFn: api.fetchCohortes,
  });
}

export function useCrearCohorte() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CohorteFormData) => api.crearCohorte(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.cohortes() });
    },
  });
}

export function useActualizarCohorte() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CohorteFormData> }) =>
      api.actualizarCohorte(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.cohortes() });
    },
  });
}

export function useEliminarCohorte() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.eliminarCohorte(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.cohortes() });
    },
  });
}

// ── Materias ─────────────────────────────────────────────────────────────────

export function useMaterias() {
  return useQuery({
    queryKey: estructuraKeys.materias(),
    queryFn: api.fetchMaterias,
  });
}

export function useCrearMateria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: MateriaFormData) => api.crearMateria(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.materias() });
    },
  });
}

export function useActualizarMateria() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MateriaFormData> }) =>
      api.actualizarMateria(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: estructuraKeys.materias() });
    },
  });
}
