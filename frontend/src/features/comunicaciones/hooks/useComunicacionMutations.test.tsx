import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const { mockPreview, mockEnviar, mockFetchCola, mockAprobar, mockCancelar, mockAprobarLote, mockCancelarLote } = vi.hoisted(() => ({
  mockPreview: vi.fn(),
  mockEnviar: vi.fn(),
  mockFetchCola: vi.fn(),
  mockAprobar: vi.fn(),
  mockCancelar: vi.fn(),
  mockAprobarLote: vi.fn(),
  mockCancelarLote: vi.fn(),
}));

vi.mock('@/features/comunicaciones/services/comunicacionesApi', () => ({
  previewComunicacion: mockPreview,
  enviarComunicacion: mockEnviar,
  fetchCola: mockFetchCola,
  aprobarComunicacion: mockAprobar,
  cancelarComunicacion: mockCancelar,
  aprobarLote: mockAprobarLote,
  cancelarLote: mockCancelarLote,
}));

import { useComunicacionPreview, useEnviarComunicacion } from './useComunicacionMutations';

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useComunicacionPreview', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('returns preview on success', async () => {
    const preview = { items: [{ destinatario: 'a@b.com', asunto_render: 'Hola', cuerpo_render: 'Mundo' }] };
    mockPreview.mockResolvedValue(preview);

    const { result } = renderHook(() => useComunicacionPreview(), { wrapper: createWrapper() });
    const payload = { asunto_template: 'A', cuerpo_template: 'C', destinatarios: [{ email: 'a@b.com', variables: {} }] };

    result.current.mutate(payload);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(preview);
  });
});

describe('useEnviarComunicacion', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('enqueue in pendiente and expose requiere_aprobacion', async () => {
    const response = { id: 'l1', estado: 'pendiente' };
    mockEnviar.mockResolvedValue(response);

    const { result } = renderHook(() => useEnviarComunicacion(), { wrapper: createWrapper() });
    const payload = { asunto_template: 'A', cuerpo_template: 'C', destinatarios: [{ email: 'a@b.com', variables: {} }], materia_id: 'm1', requiere_aprobacion: true };

    result.current.mutate(payload);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(response);
    expect(mockEnviar).toHaveBeenCalledWith(payload);
  });
});
