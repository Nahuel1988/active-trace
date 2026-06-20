export interface AlumnoDTO {
  nombre: string;
  apellido: string;
  email: string;
  grupo?: string;
}

export interface PadronPreviewResponse {
  import_id: string;
  alumnos: AlumnoDTO[];
  total_detectados: number;
  errores: string[];
}

export interface PadronCommitResponse {
  total_importados: number;
  total_reemplazados: number;
}
