import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockApiGet } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    get: mockApiGet,
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    defaults: {},
  },
  setAccessToken: vi.fn(),
  setOnSessionExpired: vi.fn(),
  getAccessToken: vi.fn(),
  ForbiddenError: class ForbiddenError extends Error {
    constructor(m?: string) { super(m ?? 'Forbidden'); this.name = 'ForbiddenError'; }
  },
}));

import {
  fetchAtrasados,
  fetchRanking,
  fetchReportes,
  fetchNotasFinales,
  fetchEntregasPendientes,
  exportEntregasPendientes,
} from './atrasadosApi';

describe('atrasadosApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchAtrasados calls GET /api/v1/analisis/atrasados with params', async () => {
    mockApiGet.mockResolvedValue({ data: { items: [], total: 0 } });
    await fetchAtrasados('m1', 'c1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/analisis/atrasados', {
      params: { materia_id: 'm1', cohorte_id: 'c1' },
    });
  });

  it('fetchRanking calls GET /api/v1/analisis/ranking with params', async () => {
    mockApiGet.mockResolvedValue({ data: { items: [] } });
    await fetchRanking('m1', 'c1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/analisis/ranking', {
      params: { materia_id: 'm1', cohorte_id: 'c1' },
    });
  });

  it('fetchReportes calls GET /api/v1/analisis/reportes with params', async () => {
    mockApiGet.mockResolvedValue({ data: { total_alumnos: 0, total_actividades: 0, tasa_abrobacion_pct: 0, alumnos_atrasados: 0, alumnos_al_dia: 0, sin_datos: false } });
    await fetchReportes('m1', 'c1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/analisis/reportes', {
      params: { materia_id: 'm1', cohorte_id: 'c1' },
    });
  });

  it('fetchNotasFinales calls GET /api/v1/analisis/notas-finales with params', async () => {
    mockApiGet.mockResolvedValue({ data: { items: [] } });
    await fetchNotasFinales('m1', 'c1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/analisis/notas-finales', {
      params: { materia_id: 'm1', cohorte_id: 'c1' },
    });
  });

  it('fetchEntregasPendientes calls GET /api/v1/analisis/entregas-pendientes with params', async () => {
    mockApiGet.mockResolvedValue({ data: { items: [], todas_corregidas: false } });
    await fetchEntregasPendientes('m1', 'c1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/analisis/entregas-pendientes', {
      params: { materia_id: 'm1', cohorte_id: 'c1' },
    });
  });

  it('exportEntregasPendientes calls export endpoint', async () => {
    const blob = new Blob(['test'], { type: 'text/csv' });
    mockApiGet.mockResolvedValue({ data: blob });

    const createObjectURL = vi.fn(() => 'blob:test');
    const originalCreateObjectURL = URL.createObjectURL;
    URL.createObjectURL = createObjectURL;

    await exportEntregasPendientes('m1', 'c1');

    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/analisis/entregas-pendientes', {
      params: { materia_id: 'm1', cohorte_id: 'c1', format: 'csv' },
      responseType: 'blob',
    });

    URL.createObjectURL = originalCreateObjectURL;
  });
});
