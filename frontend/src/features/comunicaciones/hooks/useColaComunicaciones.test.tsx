import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const { mockFetchCola } = vi.hoisted(() => ({
  mockFetchCola: vi.fn(),
}));

vi.mock('@/features/comunicaciones/services/comunicacionesApi', () => ({
  fetchCola: mockFetchCola,
  previewComunicacion: vi.fn(),
  enviarComunicacion: vi.fn(),
  aprobarComunicacion: vi.fn(),
  cancelarComunicacion: vi.fn(),
  aprobarLote: vi.fn(),
  cancelarLote: vi.fn(),
}));

import { useColaComunicaciones } from './useColaComunicaciones';

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useColaComunicaciones', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches cola on mount', async () => {
    mockFetchCola.mockResolvedValue([]);
    const { result } = renderHook(() => useColaComunicaciones('m1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetchCola).toHaveBeenCalledWith('m1');
  });

  it('does not fetch without materia_id', () => {
    const { result } = renderHook(() => useColaComunicaciones(''), { wrapper: createWrapper() });
    expect(result.current.isPending).toBe(true);
    expect(mockFetchCola).not.toHaveBeenCalled();
  });

  it('fetches cola data with non-terminal messages', async () => {
    mockFetchCola.mockResolvedValue([
      { id: 'c1', destinatario: 'a@b.com', asunto: 'A', cuerpo: 'C', estado: 'pendiente', lote_id: 'l1', requiere_aprobacion: false },
    ]);

    const { result } = renderHook(() => useColaComunicaciones('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].estado).toBe('pendiente');
  });

  it('handles terminal messages', async () => {
    mockFetchCola.mockResolvedValue([
      { id: 'c1', destinatario: 'a@b.com', asunto: 'A', cuerpo: 'C', estado: 'enviado', lote_id: 'l1', requiere_aprobacion: false },
    ]);

    const { result } = renderHook(() => useColaComunicaciones('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].estado).toBe('enviado');
  });
});
