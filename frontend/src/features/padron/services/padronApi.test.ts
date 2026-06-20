import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockApiPost } = vi.hoisted(() => ({
  mockApiPost: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    post: mockApiPost,
    get: vi.fn(),
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

import { previewPadron, commitPadron } from './padronApi';

describe('padronApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('previewPadron POSTs multipart to /api/materias/{id}/padron/preview', async () => {
    const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    mockApiPost.mockResolvedValue({ data: { import_id: 'i1', alumnos: [], total_detectados: 0, errores: [] } });

    await previewPadron('m1', mockFile);

    expect(mockApiPost).toHaveBeenCalledTimes(1);
    const [url, body, config] = mockApiPost.mock.calls[0];
    expect(url).toBe('/api/materias/m1/padron/preview');
    expect(body).toBeInstanceOf(FormData);
    expect(config?.headers?.['Content-Type']).toBe('multipart/form-data');
  });

  it('previewPadron returns preview data', async () => {
    const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const preview = { import_id: 'i1', alumnos: [{ nombre: 'Juan', apellido: 'Pérez', email: 'j@t.com' }], total_detectados: 1, errores: [] };
    mockApiPost.mockResolvedValue({ data: preview });

    const result = await previewPadron('m1', mockFile);
    expect(result).toEqual(preview);
  });

  it('commitPadron POSTs to /api/materias/{id}/padron/commit', async () => {
    mockApiPost.mockResolvedValue({ data: { total_importados: 5, total_reemplazados: 2 } });

    const result = await commitPadron('m1', 'i1');
    expect(mockApiPost).toHaveBeenCalledWith('/api/materias/m1/padron/commit', { import_id: 'i1' });
    expect(result).toEqual({ total_importados: 5, total_reemplazados: 2 });
  });

  it('preview does not persist - no commit call', async () => {
    const mockFile = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    mockApiPost.mockResolvedValue({ data: { import_id: 'i1', alumnos: [], total_detectados: 0, errores: [] } });

    await previewPadron('m1', mockFile);
    expect(mockApiPost).toHaveBeenCalledTimes(1);
    expect(mockApiPost).not.toHaveBeenCalledWith(expect.stringContaining('/commit'), expect.anything());
  });
});
