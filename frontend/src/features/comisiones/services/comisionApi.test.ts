import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockApiGet } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    get: mockApiGet,
    post: vi.fn(),
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

import { fetchMaterias, fetchCohortes } from './comisionApi';

describe('comisionApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchMaterias calls GET /api/materias', async () => {
    mockApiGet.mockResolvedValue({ data: { materias: [] } });
    await fetchMaterias();
    expect(mockApiGet).toHaveBeenCalledWith('/api/materias');
  });

  it('fetchCohortes calls GET /api/cohortes with materia_id param', async () => {
    mockApiGet.mockResolvedValue({ data: { cohortes: [] } });
    await fetchCohortes('m1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/cohortes', { params: { materia_id: 'm1' } });
  });

  it('fetchMaterias returns data from response', async () => {
    const materias = [{ materia_id: '1', nombre: 'Matemática' }];
    mockApiGet.mockResolvedValue({ data: { materias } });
    const result = await fetchMaterias();
    expect(result).toEqual(materias);
  });

  it('fetchCohortes returns data from response', async () => {
    const cohortes = [{ cohorte_id: 'c1', etiqueta: '2025' }];
    mockApiGet.mockResolvedValue({ data: { cohortes } });
    const result = await fetchCohortes('m1');
    expect(result).toEqual(cohortes);
  });
});
