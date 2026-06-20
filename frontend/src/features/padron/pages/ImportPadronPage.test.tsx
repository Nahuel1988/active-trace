import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ComisionProvider } from '@/shared/comision/ComisionContext';

const { mockUsePadronPreview, mockUsePadronCommit, mockUseComisionContext } = vi.hoisted(() => ({
  mockUsePadronPreview: vi.fn(),
  mockUsePadronCommit: vi.fn(),
  mockUseComisionContext: vi.fn(),
}));

vi.mock('@/features/padron/hooks/usePadronMutations', () => ({
  usePadronPreview: mockUsePadronPreview,
  usePadronCommit: mockUsePadronCommit,
}));

vi.mock('@/shared/comision/useComisionContext', () => ({
  useComisionContext: mockUseComisionContext,
}));

import ImportPadronPage from './ImportPadronPage';

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <ComisionProvider>
        <ImportPadronPage />
      </ComisionProvider>
    </MemoryRouter>,
  );
}

describe('ImportPadronPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseComisionContext.mockReturnValue({ materia_id: 'm1', cohorte_id: 'c1', setComision: vi.fn() });
    mockUsePadronPreview.mockReturnValue({ mutate: vi.fn(), isPending: false, isSuccess: false, data: undefined, isError: false, error: null });
    mockUsePadronCommit.mockReturnValue({ mutate: vi.fn(), isPending: false, isSuccess: false, data: undefined, isError: false, error: null, reset: vi.fn() });
  });

  it('shows message when no comision selected', () => {
    mockUseComisionContext.mockReturnValue({ materia_id: '', cohorte_id: '', setComision: vi.fn() });
    renderPage();
    expect(screen.getByText('Seleccioná una comisión para importar el padrón')).toBeInTheDocument();
  });

  it('requires comision selected to show upload', () => {
    renderPage();
    expect(screen.getByText('Importar padrón de alumnos')).toBeInTheDocument();
  });

  it('shows upload button initially', () => {
    renderPage();
    const fileInput = screen.getByLabelText('Archivo de padrón');
    expect(fileInput).toBeInTheDocument();
  });

  it('shows destructive dialog before commit', async () => {
    const mockMutate = vi.fn();
    const mockCommitMutate = vi.fn();
    mockUsePadronPreview.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isSuccess: false,
      data: undefined,
      isError: false,
      error: null,
    });
    mockUsePadronCommit.mockReturnValue({
      mutate: mockCommitMutate,
      isPending: false,
      isSuccess: false,
      data: undefined,
      isError: false,
      error: null,
      reset: vi.fn(),
    });

    const user = userEvent.setup();
    renderPage();

    const file = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const fileInput = screen.getByLabelText('Archivo de padrón');
    await user.upload(fileInput, file);

    expect(mockMutate).toHaveBeenCalledWith(
      { materia_id: 'm1', file },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });
});
