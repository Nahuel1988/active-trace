// No `any`. All fields snake_case.

export interface Usuario {
  id: string;
  tenant_id: string;
  legajo: string;
  nombre: string;
  apellidos: string;
  email: string;
  regional: string;
  facturador: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsuarioDetalle extends Usuario {
  // PII fields — only in detail endpoint
  dni: string;
  cuil: string;
  cbu: string | null;
  alias_cbu: string | null;
}

export interface UsuarioFormData {
  legajo: string;
  nombre: string;
  apellidos: string;
  email: string;
  regional: string;
  facturador: boolean;
  dni: string;
  cuil: string;
  cbu?: string;
  alias_cbu?: string;
  password?: string; // only on create
}

export interface UsuarioFilters {
  regional?: string;
  facturador?: boolean;
  q?: string;
}

export interface AccionesPorDia {
  fecha: string; // YYYY-MM-DD
  cantidad: number;
}

export interface ComunicacionPorDocente {
  usuario_id: string;
  nombre: string;
  apellidos: string;
  total: number;
  enviadas: number;
  fallidas: number;
  canceladas: number;
}

export interface InteraccionDocenteMateria {
  usuario_id: string;
  nombre: string;
  apellidos: string;
  materia_id: string | null;
  materia_nombre: string | null;
  accion: string;
  cantidad: number;
}

export interface AuditLogItem {
  id: string;
  tenant_id: string;
  actor_id: string;
  actor_nombre: string;
  materia_id: string | null;
  materia_nombre: string | null;
  accion: string;
  filas_afectadas: number;
  ip: string;
  user_agent: string;
  fecha_hora: string;
}

export interface AuditFilters {
  desde?: string;
  hasta?: string;
}

export interface AuditLogFilters extends AuditFilters {
  materia_id?: string;
  actor_id?: string;
  accion?: string;
}

export interface MetricasAuditoria {
  acciones_por_dia: AccionesPorDia[];
  comunicaciones_por_docente: ComunicacionPorDocente[];
  interacciones: InteraccionDocenteMateria[];
  ultimas_acciones: AuditLogItem[];
}
