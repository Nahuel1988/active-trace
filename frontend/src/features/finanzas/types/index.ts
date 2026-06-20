export type RolLiquidacion = 'PROFESOR' | 'TUTOR' | 'NEXO' | 'COORDINADOR';
export type GrupoPlus = 'PROG' | 'BD' | 'ARQ' | 'MAT' | 'MET';
export type EstadoLiquidacion = 'Abierta' | 'Cerrada';
export type EstadoFactura = 'Pendiente' | 'Abonada';

export interface LiquidacionItem {
  id: string;
  tenant_id: string;
  cohorte_id: string;
  periodo: string;
  usuario_id: string;
  rol: RolLiquidacion;
  comisiones: string[];
  monto_base: string;
  monto_plus: string;
  total: string;
  es_nexo: boolean;
  excluido_por_factura: boolean;
  estado: EstadoLiquidacion;
  created_at: string;
  updated_at: string;
}

export interface SegmentoLiquidacion {
  liquidaciones: LiquidacionItem[];
  subtotal: string;
}

export interface KpisLiquidacion {
  total_sin_factura: string;
  total_con_factura: string;
}

export interface LiquidacionVista {
  segmentos: {
    general: SegmentoLiquidacion;
    nexo: SegmentoLiquidacion;
    facturantes: SegmentoLiquidacion;
  };
  kpis: KpisLiquidacion;
}

export interface LiquidacionResumen {
  cantidad_generada: number;
  total_general: string;
  docentes_omitidos_sin_cbu: number;
}

export interface HistorialFilters {
  cohorte_id?: string;
  periodo?: string;
  usuario_id?: string;
}

export interface SalarioBase {
  id: string;
  tenant_id: string;
  rol: RolLiquidacion;
  monto: string;
  desde: string;
  hasta: string | null;
  created_at: string;
  updated_at: string;
}

export interface SalarioBaseFormData {
  rol: RolLiquidacion;
  monto: string;
  desde: string;
  hasta?: string;
}

export interface SalarioPlus {
  id: string;
  tenant_id: string;
  grupo: GrupoPlus;
  rol: RolLiquidacion;
  descripcion: string;
  monto: string;
  desde: string;
  hasta: string | null;
  created_at: string;
  updated_at: string;
}

export interface SalarioPlusFormData {
  grupo: GrupoPlus;
  rol: RolLiquidacion;
  descripcion: string;
  monto: string;
  desde: string;
  hasta?: string;
}

export interface Factura {
  id: string;
  tenant_id: string;
  usuario_id: string;
  periodo: string;
  detalle: string;
  referencia_archivo: string;
  tamano_kb: string;
  estado: EstadoFactura;
  cargada_at: string;
  abonada_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FacturaFormData {
  usuario_id: string;
  periodo: string;
  detalle: string;
  referencia_archivo: string;
  tamano_kb: string;
}

export interface FacturaFilters {
  periodo?: string;
  estado?: EstadoFactura;
  usuario_id?: string;
}
