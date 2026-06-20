import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const { mockFetchAtrasados, mockFetchRanking, mockFetchReportes, mockFetchNotasFinales, mockFetchEntregasPendientes } = vi.hoisted(() => ({
  mockFetchAtrasados: vi.fn(),
  mockFetchRanking: vi.fn(),
  mockFetchReportes: vi.fn(),
  mockFetchNotasFinales: vi.fn(),
  mockFetchEntregasPendientes: vi.fn(),
}));

vi.mock('@/features/atrasados/services/atrasadosApi', () => ({
  fetchAtrasados: mockFetchAtrasados,
  fetchRanking: mockFetchRanking,
  fetchReportes: mockFetchReportes,
  fetchNotasFinales: mockFetchNotasFinales,
  fetchEntregasPendientes: mockFetchEntregasPendientes,
}));

import { ForbiddenError } from '@/shared/services/api';
import { useAtrasados, useRanking, useReportes, useNotasFinales, useEntregasPendientes } from './useAtrasados';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useAtrasados', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('fetches atrasados with materia_id and cohorte_id', async () => {
    mockFetchAtrasados.mockResolvedValue({ items: [], total: 0 });
    const { result } = renderHook(() => useAtrasados('m1', 'c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchAtrasados).toHaveBeenCalledWith('m1', 'c1');
  });

  it('is disabled when no materia_id', () => {
    const { result } = renderHook(() => useAtrasados('', ''), { wrapper: createWrapper() });
    expect(result.current.isPending).toBe(true);
    expect(mockFetchAtrasados).not.toHaveBeenCalled();
  });

  it('throws ForbiddenError on 403', async () => {
    mockFetchAtrasados.mockRejectedValue(new ForbiddenError());
    const { result } = renderHook(() => useAtrasados('m1', 'c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ForbiddenError);
  });
});

describe('useRanking', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('fetches ranking with params', async () => {
    mockFetchRanking.mockResolvedValue({ items: [] });
    const { result } = renderHook(() => useRanking('m1', 'c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchRanking).toHaveBeenCalledWith('m1', 'c1');
  });
});

describe('useReportes', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('fetches reportes with params', async () => {
    mockFetchReportes.mockResolvedValue({ total_alumnos: 0, total_actividades: 0, tasa_abrobacion_pct: 0, alumnos_atrasados: 0, alumnos_al_dia: 0, sin_datos: false });
    const { result } = renderHook(() => useReportes('m1', 'c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchReportes).toHaveBeenCalledWith('m1', 'c1');
  });
});

describe('useNotasFinales', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('fetches notas finales with params', async () => {
    mockFetchNotasFinales.mockResolvedValue({ items: [] });
    const { result } = renderHook(() => useNotasFinales('m1', 'c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchNotasFinales).toHaveBeenCalledWith('m1', 'c1');
  });
});

describe('useEntregasPendientes', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('fetches entregas pendientes with params', async () => {
    mockFetchEntregasPendientes.mockResolvedValue({ items: [], todas_corregidas: false });
    const { result } = renderHook(() => useEntregasPendientes('m1', 'c1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchEntregasPendientes).toHaveBeenCalledWith('m1', 'c1');
  });
});
