import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockApiGet, mockApiPost, mockApiPut } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
  mockApiPost: vi.fn(),
  mockApiPut: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    get: mockApiGet,
    post: mockApiPost,
    put: mockApiPut,
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { fetchFacturas, fetchFactura, crearFactura, actualizarFactura, abonarFactura } from './facturasApi';

describe('facturasApi', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetchFacturas calls GET with filters', async () => {
    mockApiGet.mockResolvedValue({ data: [] });
    await fetchFacturas({ periodo: '2026-06', estado: 'Pendiente' });
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/facturas', {
      params: { periodo: '2026-06', estado: 'Pendiente', usuario_id: undefined },
    });
  });

  it('fetchFacturas calls GET with no filters', async () => {
    mockApiGet.mockResolvedValue({ data: [] });
    await fetchFacturas({});
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/facturas', {
      params: { periodo: undefined, estado: undefined, usuario_id: undefined },
    });
  });

  it('fetchFactura calls GET by id', async () => {
    mockApiGet.mockResolvedValue({ data: { id: 'f-1' } });
    const result = await fetchFactura('f-1');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/facturas/f-1');
    expect(result).toEqual({ id: 'f-1' });
  });

  it('crearFactura calls POST', async () => {
    const payload = { usuario_id: 'u-1', periodo: '2026-06', detalle: 'det', referencia_archivo: 'ref', tamano_kb: '100' };
    mockApiPost.mockResolvedValue({ data: { id: 'f-2', ...payload } });
    await crearFactura(payload);
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/facturas', payload);
  });

  it('actualizarFactura calls PUT', async () => {
    mockApiPut.mockResolvedValue({ data: { id: 'f-1' } });
    await actualizarFactura('f-1', { detalle: 'nuevo' });
    expect(mockApiPut).toHaveBeenCalledWith('/api/v1/facturas/f-1', { detalle: 'nuevo' });
  });

  it('abonarFactura calls POST /abonar', async () => {
    mockApiPost.mockResolvedValue({ data: { id: 'f-1', estado: 'Abonada' } });
    const result = await abonarFactura('f-1');
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/facturas/f-1/abonar');
    expect(result).toMatchObject({ estado: 'Abonada' });
  });
});
