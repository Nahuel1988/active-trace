import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockApiGet, mockApiPost } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
  mockApiPost: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    get: mockApiGet,
    post: mockApiPost,
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import {
  fetchLiquidaciones,
  cerrarLiquidacion,
  fetchHistorial,
  calcularPeriodo,
} from './liquidacionesApi';

describe('liquidacionesApi', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetchLiquidaciones calls GET with cohorte_id and periodo', async () => {
    const mockVista = { segmentos: { general: { liquidaciones: [], subtotal: '0' }, nexo: { liquidaciones: [], subtotal: '0' }, facturantes: { liquidaciones: [], subtotal: '0' } }, kpis: { total_sin_factura: '0', total_con_factura: '0' } };
    mockApiGet.mockResolvedValue({ data: mockVista });
    const result = await fetchLiquidaciones('cohorte-1', '2026-06');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/liquidaciones', { params: { cohorte_id: 'cohorte-1', periodo: '2026-06', usuario_id: undefined } });
    expect(result).toEqual(mockVista);
  });

  it('fetchLiquidaciones passes usuario_id when provided', async () => {
    mockApiGet.mockResolvedValue({ data: {} });
    await fetchLiquidaciones('cohorte-1', '2026-06', 'user-1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/liquidaciones', { params: { cohorte_id: 'cohorte-1', periodo: '2026-06', usuario_id: 'user-1' } });
  });

  it('cerrarLiquidacion calls POST /cerrar', async () => {
    mockApiPost.mockResolvedValue({ data: { id: 'liq-1', estado: 'Cerrada' } });
    const result = await cerrarLiquidacion('liq-1');
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/liquidaciones/liq-1/cerrar');
    expect(result).toEqual({ id: 'liq-1', estado: 'Cerrada' });
  });

  it('fetchHistorial calls GET /historial with filters', async () => {
    mockApiGet.mockResolvedValue({ data: { items: [] } });
    await fetchHistorial({ cohorte_id: 'c-1', periodo: '2026-06' });
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/liquidaciones/historial', { params: { cohorte_id: 'c-1', periodo: '2026-06', usuario_id: undefined } });
  });

  it('calcularPeriodo calls POST /calcular', async () => {
    mockApiPost.mockResolvedValue({ data: { cantidad_generada: 5, total_general: '5000', docentes_omitidos_sin_cbu: 0 } });
    const result = await calcularPeriodo('cohorte-1', '2026-06');
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/liquidaciones/calcular', { cohorte_id: 'cohorte-1', periodo: '2026-06' });
    expect(result.cantidad_generada).toBe(5);
  });
});
