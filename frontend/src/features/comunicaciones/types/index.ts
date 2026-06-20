export type ComunicacionEstado = 'pendiente' | 'enviando' | 'enviado' | 'error' | 'cancelado';

export interface DestinatarioInput {
  email: string;
  variables: Record<string, string>;
}

export interface PreviewRequest {
  asunto_template: string;
  cuerpo_template: string;
  destinatarios: DestinatarioInput[];
}

export interface PreviewItem {
  destinatario: string;
  asunto_render: string;
  cuerpo_render: string;
}

export interface PreviewResponse {
  items: PreviewItem[];
}

export interface EnviarRequest {
  asunto_template: string;
  cuerpo_template: string;
  destinatarios: DestinatarioInput[];
  materia_id?: string;
  requiere_aprobacion?: boolean;
}

export interface ComunicacionResponse {
  id: string;
  destinatario: string;
  asunto: string;
  cuerpo: string;
  estado: ComunicacionEstado;
  lote_id: string;
  requiere_aprobacion: boolean;
}

export interface EnviarResponse {
  id: string;
  estado: string;
}
