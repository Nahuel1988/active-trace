export type EstadoGuardia = 'pendiente' | 'realizada' | 'cancelada';

export interface CatalogoItem {
  id: string;
  nombre: string;
}

export interface Guardia {
  id: string;
  materia: CatalogoItem;
  tutor: CatalogoItem;
  carrera: CatalogoItem;
  cohorte: CatalogoItem;
  dia: string;
  horario: string;
  comentarios?: string;
  estado: EstadoGuardia;
  created_at: string;
  updated_at?: string;
}

export interface GuardiaCreateRequest {
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
  dia: string;
  horario: string;
  comentarios?: string;
}

export interface GuardiaFiltros {
  materia_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
  estado?: EstadoGuardia;
}
