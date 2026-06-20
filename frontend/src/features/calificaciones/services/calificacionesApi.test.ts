import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockApiPost, mockApiGet, mockApiPut } = vi.hoisted(() => ({
  mockApiPost: vi.fn(),
  mockApiGet: vi.fn(),
  mockApiPut: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    post: mockApiPost,
    get: mockApiGet,
    put: mockApiPut,
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

import { previewCalificaciones, commitCalificaciones, getUmbral, putUmbral } from './calificacionesApi';

describe('calificacionesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('previewCalificaciones POSTs multipart to /api/materias/{id}/calificaciones/preview', async () => {
    const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    mockApiPost.mockResolvedValue({ data: { import_id: 'i1', actividades: [], total_alumnos: 0, errores: [] } });

    await previewCalificaciones('m1', mockFile);

    expect(mockApiPost).toHaveBeenCalledTimes(1);
    const [url, body, config] = mockApiPost.mock.calls[0];
    expect(url).toBe('/api/materias/m1/calificaciones/preview');
    expect(body).toBeInstanceOf(FormData);
    expect(config?.headers?.['Content-Type']).toBe('multipart/form-data');
  });

  it('previewCalificaciones returns actividades with escala', async () => {
    const preview = { import_id: 'i1', actividades: [{ id: 'a1', nombre: 'TP1', escala: 'numerica' }], total_alumnos: 10, errores: [] };
    mockApiPost.mockResolvedValue({ data: preview });

    const mockFile = new File(['test'], 'test.xlsx');
    const result = await previewCalificaciones('m1', mockFile);
    expect(result).toEqual(preview);
  });

  it('commitCalificaciones POSTs selected activitades to commit', async () => {
    mockApiPost.mockResolvedValue({ data: { total_procesados: 8 } });

    const result = await commitCalificaciones('m1', 'i1', ['a1', 'a2']);
    expect(mockApiPost).toHaveBeenCalledWith('/api/materias/m1/calificaciones/commit', {
      import_id: 'i1',
      actividades_seleccionadas: ['a1', 'a2'],
    });
    expect(result).toEqual({ total_procesados: 8 });
  });

  it('commit only sends selected actividades', async () => {
    mockApiPost.mockResolvedValue({ data: { total_procesados: 0 } });

    await commitCalificaciones('m1', 'i1', ['a1']);
    const body = mockApiPost.mock.calls[0][1];
    expect(body.actividades_seleccionadas).toEqual(['a1']);
  });

  describe('umbral', () => {
    it('getUmbral calls GET /api/materias/{id}/umbral', async () => {
      mockApiGet.mockResolvedValue({ data: { umbral_porcentaje: 60 } });
      const result = await getUmbral('m1');
      expect(mockApiGet).toHaveBeenCalledWith('/api/materias/m1/umbral');
      expect(result).toEqual({ umbral_porcentaje: 60 });
    });

    it('getUmbral returns default 60 when not configured', async () => {
      mockApiGet.mockResolvedValue({ data: { umbral_porcentaje: 60 } });
      const result = await getUmbral('m1');
      expect(result.umbral_porcentaje).toBe(60);
    });

    it('putUmbral sends the value', async () => {
      mockApiPut.mockResolvedValue({});
      await putUmbral('m1', 75);
      expect(mockApiPut).toHaveBeenCalledWith('/api/materias/m1/umbral', { umbral_porcentaje: 75 });
    });
  });
});
