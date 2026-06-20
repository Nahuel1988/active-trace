export type TareaEstado = 'pendiente' | 'en_progreso' | 'completada';

export interface Tarea {
  id: string;
  titulo: string;
  descripcion: string | null;
  estado: TareaEstado;
  prioridad: string;
  creador_id: string;
  creador_nombre: string;
  asignado_a: string | null;
  asignado_nombre: string | null;
  materia_id: string | null;
  fecha_vencimiento: string | null;
  created_at: string;
  updated_at: string;
}

export interface TareaFormData {
  titulo: string;
  descripcion: string;
  prioridad: string;
  asignado_a: string;
  materia_id?: string;
  fecha_vencimiento?: string;
}

export interface Comentario {
  id: string;
  contenido: string;
  autor_id: string;
  autor_nombre: string;
  created_at: string;
}
