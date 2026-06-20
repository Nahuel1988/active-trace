import { describe, it, expect, vi, beforeEach } from 'vitest';

const { mockApiGet, mockApiPost, mockApiPut, mockApiDelete } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
  mockApiPost: vi.fn(),
  mockApiPut: vi.fn(),
  mockApiDelete: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    get: mockApiGet,
    post: mockApiPost,
    put: mockApiPut,
    delete: mockApiDelete,
    patch: vi.fn(),
  },
}));

import {
  fetchSalariosBase,
  crearSalarioBase,
  actualizarSalarioBase,
  eliminarSalarioBase,
  fetchSalariosPlus,
  crearSalarioPlus,
  actualizarSalarioPlus,
  eliminarSalarioPlus,
} from './grillaApi';

describe('grillaApi — SalarioBase', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetchSalariosBase calls GET without filter', async () => {
    mockApiGet.mockResolvedValue({ data: [] });
    await fetchSalariosBase();
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/grilla/salarios-base', { params: { rol: undefined } });
  });

  it('fetchSalariosBase passes rol filter', async () => {
    mockApiGet.mockResolvedValue({ data: [] });
    await fetchSalariosBase('PROFESOR');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/grilla/salarios-base', { params: { rol: 'PROFESOR' } });
  });

  it('crearSalarioBase calls POST', async () => {
    const payload = { rol: 'PROFESOR' as const, monto: '1000', desde: '2026-01-01' };
    mockApiPost.mockResolvedValue({ data: { id: 'sb-1', ...payload } });
    const result = await crearSalarioBase(payload);
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/grilla/salarios-base', payload);
    expect(result).toMatchObject({ id: 'sb-1' });
  });

  it('actualizarSalarioBase calls PUT with id', async () => {
    mockApiPut.mockResolvedValue({ data: { id: 'sb-1', monto: '1200' } });
    await actualizarSalarioBase('sb-1', { monto: '1200' });
    expect(mockApiPut).toHaveBeenCalledWith('/api/v1/grilla/salarios-base/sb-1', { monto: '1200' });
  });

  it('eliminarSalarioBase calls DELETE', async () => {
    mockApiDelete.mockResolvedValue({ data: null });
    await eliminarSalarioBase('sb-1');
    expect(mockApiDelete).toHaveBeenCalledWith('/api/v1/grilla/salarios-base/sb-1');
  });
});

describe('grillaApi — SalarioPlus', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetchSalariosPlus calls GET without filter', async () => {
    mockApiGet.mockResolvedValue({ data: [] });
    await fetchSalariosPlus();
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/grilla/salarios-plus', { params: { grupo: undefined } });
  });

  it('fetchSalariosPlus passes grupo filter', async () => {
    mockApiGet.mockResolvedValue({ data: [] });
    await fetchSalariosPlus('PROG');
    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/grilla/salarios-plus', { params: { grupo: 'PROG' } });
  });

  it('crearSalarioPlus calls POST', async () => {
    const payload = { grupo: 'PROG' as const, rol: 'PROFESOR' as const, descripcion: 'Plus prog', monto: '500', desde: '2026-01-01' };
    mockApiPost.mockResolvedValue({ data: { id: 'sp-1', ...payload } });
    await crearSalarioPlus(payload);
    expect(mockApiPost).toHaveBeenCalledWith('/api/v1/grilla/salarios-plus', payload);
  });

  it('actualizarSalarioPlus calls PUT', async () => {
    mockApiPut.mockResolvedValue({ data: { id: 'sp-1' } });
    await actualizarSalarioPlus('sp-1', { monto: '600' });
    expect(mockApiPut).toHaveBeenCalledWith('/api/v1/grilla/salarios-plus/sp-1', { monto: '600' });
  });

  it('eliminarSalarioPlus calls DELETE', async () => {
    mockApiDelete.mockResolvedValue({ data: null });
    await eliminarSalarioPlus('sp-1');
    expect(mockApiDelete).toHaveBeenCalledWith('/api/v1/grilla/salarios-plus/sp-1');
  });
});
