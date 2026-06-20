import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { ComisionProvider } from '@/shared/comision/ComisionContext';

const { mockPreviewMut, mockEnviarMut, mockCola, mockComisionCtx, mockPermission } = vi.hoisted(() => ({
  mockPreviewMut: vi.fn(),
  mockEnviarMut: vi.fn(),
  mockCola: vi.fn(),
  mockComisionCtx: vi.fn(),
  mockPermission: vi.fn(),
}));

vi.mock('@/features/comunicaciones/hooks/useComunicacionMutations', () => ({
  useComunicacionPreview: () => ({ mutate: mockPreviewMut, isPending: false, data: undefined, isError: false, error: null }),
  useEnviarComunicacion: () => ({ mutate: mockEnviarMut, isPending: false, isSuccess: false, data: undefined, isError: false, error: null, reset: vi.fn() }),
}));

vi.mock('@/features/comunicaciones/hooks/useColaComunicaciones', () => ({
  useColaComunicaciones: (materia_id?: string) => mockCola(materia_id),
}));

vi.mock('@/shared/comision/useComisionContext', () => ({
  useComisionContext: mockComisionCtx,
}));

vi.mock('@/shared/hooks/usePermission', () => ({
  usePermission: mockPermission,
}));

import ComunicacionesQueuePage from './ComunicacionesQueuePage';

function renderPage(initialEntries = ['/comunicaciones']) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <ComisionProvider>
          <ComunicacionesQueuePage />
        </ComisionProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ComunicacionesQueuePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockComisionCtx.mockReturnValue({ materia_id: 'm1', cohorte_id: 'c1', setComision: vi.fn() });
    mockPermission.mockReturnValue(false);
    mockCola.mockReturnValue({ data: [], isLoading: false });
    mockPreviewMut.mockReturnValue(undefined);
  });

  it('shows message when no comision selected', () => {
    mockComisionCtx.mockReturnValue({ materia_id: '', cohorte_id: '', setComision: vi.fn() });
    renderPage();
    expect(screen.getByText('Seleccioná una comisión para gestionar comunicaciones')).toBeInTheDocument();
  });

  it('renders form fields', () => {
    renderPage();
    expect(screen.getByLabelText('Asunto')).toBeInTheDocument();
    expect(screen.getByLabelText('Cuerpo del mensaje')).toBeInTheDocument();
    expect(screen.getByText('Previsualizar')).toBeInTheDocument();
    expect(screen.getByText('Cola de envío')).toBeInTheDocument();
  });

  it('shows alumnos from URL param as destinatarios', () => {
    mockCola.mockReturnValue({ data: [], isLoading: false });
    renderPage(['/comunicaciones?alumnos=id1,id2']);
    expect(screen.getByText('Destinatarios (2 desde atrasados)')).toBeInTheDocument();
  });

  it('preview button calls preview mutation', async () => {
    const user = userEvent.setup();
    renderPage(['/comunicaciones?alumnos=id1']);

    await user.type(screen.getByLabelText('Asunto'), 'Hola {nombre}');
    await user.type(screen.getByLabelText('Cuerpo del mensaje'), 'Tu nota es {nota}');

    await user.click(screen.getByText('Previsualizar'));
    expect(mockPreviewMut).toHaveBeenCalled();
  });

  it('renders cola section', () => {
    mockCola.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText('No hay comunicaciones en la cola.')).toBeInTheDocument();
  });
});
