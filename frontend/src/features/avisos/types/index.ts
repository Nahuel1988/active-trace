// ── Tipos del feature avisos ──────────────────────────────────────────────────

export type Alcance = 'global' | 'por_materia' | 'por_cohorte' | 'por_rol';

export type Severidad = 'info' | 'advertencia' | 'critico';

export interface Aviso {
  id: string;
  titulo: string;
  cuerpo: string;
  alcance: Alcance;
  severidad: Severidad;
  materia_id: string | null;
  cohorte_id: string | null;
  rol_destino: string | null;
  inicio_en: string;
  fin_en: string;
  orden: number;
  requiere_ack: boolean;
  activo: boolean;
  creado_por: string;
  created_at: string;
  updated_at: string;
}

export interface AvisoFormData {
  titulo: string;
  cuerpo: string;
  alcance: Alcance;
  severidad: Severidad;
  materia_id: string | null;
  cohorte_id: string | null;
  rol_destino: string | null;
  inicio_en: string;
  fin_en: string;
  orden: number | null;
  requiere_ack: boolean;
}
