// ── Tipos del módulo Estructura Académica ───────────────────────────────

export type TipoFecha = 'Parcial' | 'TP' | 'Coloquio' | 'Recuperatorio';

export interface Carrera {
  id: string;
  tenant_id: string;
  codigo: string;
  nombre: string;
  estado: string;
  created_at: string;
  updated_at: string;
}

export interface CarreraFormData {
  codigo: string;
  nombre: string;
}

export interface Programa {
  id: string;
  tenant_id: string;
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  titulo: string;
  referencia_archivo: string | null;
  cargado_at: string;
  created_at: string;
  updated_at: string;
}

export interface FechaAcademica {
  id: string;
  tenant_id: string;
  materia_id: string;
  cohorte_id: string;
  tipo: TipoFecha;
  numero: number;
  periodo: string;
  fecha: string;
  titulo: string;
  created_at: string;
  updated_at: string;
}

export interface FechaAcademicaFormData {
  materia_id: string;
  cohorte_id: string;
  tipo: TipoFecha;
  numero: number;
  periodo: string;
  fecha: string;
  titulo: string;
}

export interface FechaAcademicaUpdateData {
  periodo?: string;
  fecha?: string;
  titulo?: string;
}

export interface CalendarioItem {
  periodo: string;
  fechas: FechaAcademica[];
}

// ── Cohortes ─────────────────────────────────────────────────────────────────

export interface Cohorte {
  id: string;
  tenant_id: string;
  etiqueta: string;
  carrera_id: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  created_at: string;
  updated_at: string;
}

export interface CohorteFormData {
  etiqueta: string;
  carrera_id: string;
  fecha_inicio: string;
  fecha_fin?: string;
}

// ── Materias ─────────────────────────────────────────────────────────────────

export type ClavePlus = 'PROG' | 'BD' | 'ARQ' | 'MAT' | 'MET';

export interface Materia {
  id: string;
  tenant_id: string;
  nombre: string;
  clave_plus: ClavePlus;
  created_at: string;
  updated_at: string;
}

export interface MateriaFormData {
  nombre: string;
  clave_plus: ClavePlus;
}
