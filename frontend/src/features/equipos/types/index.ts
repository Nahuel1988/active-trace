export interface Equipo {
  materia_id: string | null;
  carrera_id: string | null;
  cohorte_id: string | null;
  conteo: number;
  materia_nombre: string | null;
  carrera_nombre: string | null;
  cohorte_nombre: string | null;
}

export interface Asignacion {
  id: string;
  equipo_id: string;
  user_id: string;
  nombre: string;
  apellido: string;
  email: string;
  rol: string;
  responsable: boolean;
  vigencia_desde: string;
  vigencia_hasta: string;
  created_at: string;
}

export interface AsignacionMasivaRequest {
  usuario_ids: string[];
  role_id: string;
  materia_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
  comisiones: string[];
  responsable_id?: string;
  desde: string;
  hasta?: string;
}

export interface EquipoFilters {
  materia_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
  rol?: string;
  q?: string;
}

export interface ClonarRequest {
  origen_equipo_id: string;
  destino_carrera_id: string;
  destino_cohorte_id: string;
  nueva_vigencia_desde?: string;
  nueva_vigencia_hasta?: string;
}

export interface VigenciaRequest {
  equipo_ids: string[];
  vigencia_desde: string;
  vigencia_hasta: string;
}

export interface AsignacionMasivaItem {
  usuario_id: string;
  motivo: string;
}

export interface AsignacionMasivaResult {
  creadas: number;
  rechazadas: AsignacionMasivaItem[];
  omitidas: AsignacionMasivaItem[];
}

export interface ClonarResult {
  clonadas: number;
  omitidas: number;
}

export interface MisEquiposAsignacion {
  usuario_id: string;
  role_code: string;
  vigencia_desde: string;
  vigencia_hasta?: string;
}

export interface MisEquipoItem {
  materia_id: string | null;
  carrera_id: string | null;
  cohorte_id: string | null;
  asignaciones: MisEquiposAsignacion[];
}
