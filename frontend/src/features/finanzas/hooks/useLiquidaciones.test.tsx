import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';

const { mockFetchLiquidaciones, mockFetchHistorial } = vi.hoisted(() => ({
  mockFetchLiquidaciones: vi.fn(),
  mockFetchHistorial: vi.fn(),
}));

vi.mock('@/features/finanzas/services/liquidacionesApi', () => ({
  fetchLiquidaciones: mockFetchLiquidaciones,
  fetchHistorial: mockFetchHistorial,
  cerrarLiquidacion: vi.fn(),
  calcularPeriodo: vi.fn(),
}));

import { useLiquidaciones, useHistorial } from './useLiquidaciones';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('useLiquidaciones', () => {
  it('does not fetch when cohorte_id is empty', () => {
    renderHook(() => useLiquidaciones('', '2026-06'), { wrapper });
    expect(mockFetchLiquidaciones).not.toHaveBeenCalled();
  });

  it('does not fetch when periodo is empty', () => {
    renderHook(() => useLiquidaciones('c-1', ''), { wrapper });
    expect(mockFetchLiquidaciones).not.toHaveBeenCalled();
  });

  it('fetches when both cohorte_id and periodo are set', async () => {
    const mock = { segmentos: { general: { liquidaciones: [], subtotal: '0' }, nexo: { liquidaciones: [], subtotal: '0' }, facturantes: { liquidaciones: [], subtotal: '0' } }, kpis: { total_sin_factura: '0', total_con_factura: '0' } };
    mockFetchLiquidaciones.mockResolvedValue(mock);
    const { result } = renderHook(() => useLiquidaciones('c-1', '2026-06'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mock);
  });
});

describe('useHistorial', () => {
  it('fetches historial with filters', async () => {
    mockFetchHistorial.mockResolvedValue({ items: [] });
    const { result } = renderHook(() => useHistorial({ cohorte_id: 'c-1' }), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchHistorial).toHaveBeenCalledWith({ cohorte_id: 'c-1' });
  });

  it('fetches historial with no filters', async () => {
    mockFetchHistorial.mockResolvedValue({ items: [] });
    const { result } = renderHook(() => useHistorial({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchHistorial).toHaveBeenCalledWith({});
  });
});
