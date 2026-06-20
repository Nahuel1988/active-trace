export interface ActividadDTO {
  id: string;
  nombre: string;
  escala: 'numerica' | 'textual';
}

export interface CalificacionesPreviewResponse {
  import_id: string;
  actividades: ActividadDTO[];
  total_alumnos: number;
  errores: string[];
}

export interface CalificacionesCommitResponse {
  total_procesados: number;
}

export interface UmbralResponse {
  umbral_porcentaje: number;
}
