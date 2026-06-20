export type EstadoInstancia = 'programado' | 'realizado' | 'cancelado';

export interface SlotEncuentro {
  id: string;
  materia_id: string;
  titulo: string;
  dia_semana: string;
  hora: string;
  modo: 'recurrente' | 'unico';
  fecha_inicio: string;
  cant_semanas: number | null;
  fecha_unica: string | null;
  meet_url: string | null;
  vig_desde: string;
  vig_hasta: string | null;
  instancias?: InstanciaEncuentro[];
}

export interface InstanciaEncuentro {
  id: string;
  slot_id: string;
  fecha: string;
  hora: string;
  estado: EstadoInstancia;
  meet_url: string | null;
  video_url: string | null;
  comentario: string | null;
}

export interface SlotCreateRequest {
  modo: 'recurrente' | 'unico';
  materia_id: string;
  titulo: string;
  dia_semana: string;
  hora: string;
  fecha_inicio: string;
  cant_semanas?: number | null;
  fecha_unica?: string | null;
  meet_url?: string | null;
  vig_desde: string;
  vig_hasta?: string | null;
}

export interface InstanciaEditRequest {
  estado?: EstadoInstancia;
  meet_url?: string | null;
  video_url?: string | null;
  comentario?: string | null;
}

export interface InstanciaFilters {
  slot_id?: string;
  materia_id?: string;
  estado?: EstadoInstancia;
  fecha_desde?: string;
  fecha_hasta?: string;
}
