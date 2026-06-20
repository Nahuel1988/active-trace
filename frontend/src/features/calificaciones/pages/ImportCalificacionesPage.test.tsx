import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ComisionProvider } from '@/shared/comision/ComisionContext';

const { mockPreview, mockCommit, mockUmbral, mockComisionCtx } = vi.hoisted(() => ({
  mockPreview: vi.fn(),
  mockCommit: vi.fn(),
  mockUmbral: vi.fn(),
  mockComisionCtx: vi.fn(),
}));

vi.mock('@/features/calificaciones/hooks/useCalificacionesMutations', () => ({
  useCalificacionesPreview: mockPreview,
  useCalificacionesCommit: mockCommit,
  useUmbral: mockUmbral,
}));

vi.mock('@/shared/comision/useComisionContext', () => ({
  useComisionContext: mockComisionCtx,
}));

import ImportCalificacionesPage from './ImportCalificacionesPage';

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <ComisionProvider>
          <ImportCalificacionesPage />
        </ComisionProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ImportCalificacionesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockComisionCtx.mockReturnValue({ materia_id: 'm1', cohorte_id: 'c1', setComision: vi.fn() });
    mockPreview.mockReturnValue({ mutate: vi.fn(), isPending: false, isSuccess: false, data: undefined, isError: false, error: null });
    mockCommit.mockReturnValue({ mutate: vi.fn(), isPending: false, isSuccess: false, data: undefined, isError: false, error: null, reset: vi.fn() });
    mockUmbral.mockReturnValue({ data: { umbral_porcentaje: 60 }, isLoading: false, mutation: { mutate: vi.fn(), isPending: false } });
  });

  it('shows message when no comision selected', () => {
    mockComisionCtx.mockReturnValue({ materia_id: '', cohorte_id: '', setComision: vi.fn() });
    renderPage();
    expect(screen.getByText('Seleccioná una comisión para importar calificaciones')).toBeInTheDocument();
  });

  it('renders with comision selected', () => {
    renderPage();
    expect(screen.getByText('Importar calificaciones')).toBeInTheDocument();
  });

  it('shows file upload input', () => {
    renderPage();
    expect(screen.getByLabelText('Archivo de calificaciones')).toBeInTheDocument();
  });

  it('renders umbral section', () => {
    renderPage();
    expect(screen.getByText('Umbral de aprobación (%)')).toBeInTheDocument();
  });

  it('upload triggers preview mutation', async () => {
    const mutateMock = vi.fn();
    mockPreview.mockReturnValue({ mutate: mutateMock, isPending: false, isSuccess: false, data: undefined, isError: false, error: null });

    const user = userEvent.setup();
    renderPage();

    const file = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const fileInput = screen.getByLabelText('Archivo de calificaciones');
    await user.upload(fileInput, file);

    expect(mutateMock).toHaveBeenCalledWith(
      { materia_id: 'm1', file },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });
});
