import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';

const { mockFetchSalariosBase, mockFetchSalariosPlus } = vi.hoisted(() => ({
  mockFetchSalariosBase: vi.fn(),
  mockFetchSalariosPlus: vi.fn(),
}));

vi.mock('@/features/finanzas/services/grillaApi', () => ({
  fetchSalariosBase: mockFetchSalariosBase,
  fetchSalariosPlus: mockFetchSalariosPlus,
  crearSalarioBase: vi.fn(),
  actualizarSalarioBase: vi.fn(),
  eliminarSalarioBase: vi.fn(),
  crearSalarioPlus: vi.fn(),
  actualizarSalarioPlus: vi.fn(),
  eliminarSalarioPlus: vi.fn(),
}));

import { useSalariosBase, useSalariosPlus } from './useGrilla';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('useSalariosBase', () => {
  it('fetches without rol filter', async () => {
    mockFetchSalariosBase.mockResolvedValue([]);
    const { result } = renderHook(() => useSalariosBase(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchSalariosBase).toHaveBeenCalledWith(undefined);
  });

  it('fetches with rol filter', async () => {
    mockFetchSalariosBase.mockResolvedValue([]);
    const { result } = renderHook(() => useSalariosBase('PROFESOR'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchSalariosBase).toHaveBeenCalledWith('PROFESOR');
  });
});

describe('useSalariosPlus', () => {
  it('fetches without grupo filter', async () => {
    mockFetchSalariosPlus.mockResolvedValue([]);
    const { result } = renderHook(() => useSalariosPlus(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchSalariosPlus).toHaveBeenCalledWith(undefined);
  });

  it('fetches with grupo filter', async () => {
    mockFetchSalariosPlus.mockResolvedValue([]);
    const { result } = renderHook(() => useSalariosPlus('PROG'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchSalariosPlus).toHaveBeenCalledWith('PROG');
  });
});
