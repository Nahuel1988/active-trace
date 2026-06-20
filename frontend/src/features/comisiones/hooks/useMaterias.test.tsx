import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const { mockFetchMaterias, mockFetchCohortes } = vi.hoisted(() => ({
  mockFetchMaterias: vi.fn(),
  mockFetchCohortes: vi.fn(),
}));

vi.mock('@/features/comisiones/services/comisionApi', () => ({
  fetchMaterias: mockFetchMaterias,
  fetchCohortes: mockFetchCohortes,
}));

import { ForbiddenError } from '@/shared/services/api';
import { useMaterias, useCohortes } from './useMaterias';

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

describe('useMaterias', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns materias on success', async () => {
    const materias = [{ materia_id: '1', nombre: 'Matemática' }];
    mockFetchMaterias.mockResolvedValue(materias);

    const { result } = renderHook(() => useMaterias(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(materias);
  });

  it('throws ForbiddenError on 403', async () => {
    mockFetchMaterias.mockRejectedValue(new ForbiddenError());

    const { result } = renderHook(() => useMaterias(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(ForbiddenError);
  });
});

describe('useCohortes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns cohortes on success', async () => {
    const cohortes = [{ cohorte_id: 'c1', etiqueta: '2025' }];
    mockFetchCohortes.mockResolvedValue(cohortes);

    const { result } = renderHook(() => useCohortes('m1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(cohortes);
  });

  it('does not fetch when materia_id is empty', async () => {
    const { result } = renderHook(() => useCohortes(''), { wrapper: createWrapper() });

    expect(result.current.isPending).toBe(true);
    expect(mockFetchCohortes).not.toHaveBeenCalled();
  });
});
