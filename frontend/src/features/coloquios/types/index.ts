export interface Coloquio {
  id: string;
  materia: string;
  instancia: string;
  tipo: string;
  convocados: number;
  reservas: number;
  cupos: number;
  fecha: string;
  estado: string;
}

export interface ColoquioFormData {
  materia_id: string;
  cohorte_id: string;
  tipo: string;
  instancia: string;
  dias_disponibles: string[];
}

export interface MetricasColoquios {
  total_candidatos: number;
  instancias_activas: number;
  reservas_activas: number;
  notas_registradas: number;
}

export interface AgendaItem {
  id: string;
  alumno: string;
  materia: string;
  fecha_hora: string;
  tipo: string;
  estado: string;
}

export interface RegistroAcademico {
  id: string;
  alumno: string;
  materia: string;
  nota: number;
  fecha: string;
  estado: string;
}
