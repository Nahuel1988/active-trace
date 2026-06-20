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
  previewComunicacion,
  enviarComunicacion,
  fetchCola,
  aprobarComunicacion,
  cancelarComunicacion,
  aprobarLote,
  cancelarLote,
} from './comunicacionesApi';

describe('comunicacionesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('previewComunicacion POSTs to /api/v1/comunicaciones/preview', async () => {
    const payload = { asunto_template: 'Asunto', cuerpo_template: 'Cuerpo', destinatarios: [{ email: 'a@b.com', variables: {} }] };
    mockApiPost.mockResolvedValue({ data: { items: [] } });

    await previewComunicacion(payload);
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/comunicaciones/preview', payload);
  });

  it('enviarComunicacion POSTs to /api/v1/comunicaciones', async () => {
    const payload = { asunto_template: 'A', cuerpo_template: 'C', destinatarios: [{ email: 'a@b.com', variables: {} }], materia_id: 'm1', requiere_aprobacion: false };
    mockApiPost.mockResolvedValue({ data: { id: 'l1', estado: 'pendiente' } });

    const result = await enviarComunicacion(payload);
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/comunicaciones', payload);
    expect(result.estado).toBe('pendiente');
  });

  it('fetchCola calls GET /api/v1/comunicaciones with params', async () => {
    mockApiGet.mockResolvedValue({ data: [] });
    await fetchCola('m1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/comunicaciones', { params: { materia_id: 'm1' } });
  });

  it('aprobarComunicacion POSTs to .../{id}/aprobar', async () => {
    mockApiPost.mockResolvedValue({ data: { id: 'c1', estado: 'enviando' } });
    await aprobarComunicacion('c1');
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/comunicaciones/c1/aprobar');
  });

  it('cancelarComunicacion POSTs to .../{id}/cancelar', async () => {
    mockApiPost.mockResolvedValue({ data: { id: 'c1', estado: 'cancelado' } });
    await cancelarComunicacion('c1');
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/comunicaciones/c1/cancelar');
  });

  it('aprobarLote POSTs to .../lote/{lote_id}/aprobar', async () => {
    mockApiPost.mockResolvedValue({ data: { total: 5 } });
    await aprobarLote('l1');
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/comunicaciones/lote/l1/aprobar');
  });

  it('cancelarLote POSTs to .../lote/{lote_id}/cancelar', async () => {
    mockApiPost.mockResolvedValue({ data: { total: 3 } });
    await cancelarLote('l1');
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/comunicaciones/lote/l1/cancelar');
  });
});
