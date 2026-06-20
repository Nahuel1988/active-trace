export interface AtrasadoItem {
  entrada_padron_id: string;
  alumno_nombre: string;
  alumno_apellido: string;
  email: string | null;
  materia_id: string;
  materia_nombre: string;
  clasificacion: 'missing' | 'below_threshold';
  actividad: string | null;
}

export interface AtrasadosResponse {
  items: AtrasadoItem[];
  total: number;
}

export interface RankingItem {
  entrada_padron_id: string;
  alumno_nombre: string;
  alumno_apellido: string;
  actividades_aprobadas: number;
  total_actividades: number;
  porcentaje_aprobacion: number;
}

export interface RankingResponse {
  items: RankingItem[];
}

export interface ReportesResponse {
  total_alumnos: number;
  total_actividades: number;
  tasa_abrobacion_pct: number;
  alumnos_atrasados: number;
  alumnos_al_dia: number;
  sin_datos: boolean;
}

export interface NotaFinalAlumno {
  entrada_padron_id: string;
  alumno_nombre: string;
  alumno_apellido: string;
  nota_final: number;
  condicion: string;
}

export interface NotasFinalesResponse {
  items: NotaFinalAlumno[];
}

export interface EntregaPendiente {
  alumno: string;
  actividad: string;
  fecha_submission: string;
  materia: string;
}

export interface EntregasPendientesResponse {
  items: EntregaPendiente[];
  todas_corregidas: boolean;
}
