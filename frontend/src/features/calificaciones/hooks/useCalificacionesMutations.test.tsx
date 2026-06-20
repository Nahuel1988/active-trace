import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const { mockPreview, mockCommit, mockGetUmbral, mockPutUmbral } = vi.hoisted(() => ({
  mockPreview: vi.fn(),
  mockCommit: vi.fn(),
  mockGetUmbral: vi.fn(),
  mockPutUmbral: vi.fn(),
}));

vi.mock('@/features/calificaciones/services/calificacionesApi', () => ({
  previewCalificaciones: mockPreview,
  commitCalificaciones: mockCommit,
  getUmbral: mockGetUmbral,
  putUmbral: mockPutUmbral,
}));

import { useCalificacionesPreview, useCalificacionesCommit, useUmbral } from './useCalificacionesMutations';

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

describe('useCalificacionesPreview', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('returns preview data on success', async () => {
    const preview = { import_id: 'i1', actividades: [], total_alumnos: 0, errores: [] };
    mockPreview.mockResolvedValue(preview);

    const { result } = renderHook(() => useCalificacionesPreview(), { wrapper: createWrapper() });
    const file = new File(['test'], 'test.xlsx');

    result.current.mutate({ materia_id: 'm1', file });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(preview);
  });
});

describe('useCalificacionesCommit', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('calls commit with selected actividades', async () => {
    mockCommit.mockResolvedValue({ total_procesados: 8 });

    const { result } = renderHook(() => useCalificacionesCommit(), { wrapper: createWrapper() });
    result.current.mutate({ materia_id: 'm1', import_id: 'i1', actividades_seleccionadas: ['a1'] });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockCommit).toHaveBeenCalledWith('m1', 'i1', ['a1']);
  });
});

describe('useUmbral', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('gets umbral with default 60', async () => {
    mockGetUmbral.mockResolvedValue({ umbral_porcentaje: 60 });

    const { result } = renderHook(() => useUmbral('m1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ umbral_porcentaje: 60 });
  });

  it('does not fetch without materia_id', () => {
    const { result } = renderHook(() => useUmbral(''), { wrapper: createWrapper() });
    expect(result.current.isPending).toBe(true);
    expect(mockGetUmbral).not.toHaveBeenCalled();
  });
});
