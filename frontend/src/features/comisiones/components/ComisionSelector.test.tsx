import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ComisionProvider } from '@/shared/comision/ComisionContext';

const { mockUseMaterias, mockUseCohortes } = vi.hoisted(() => ({
  mockUseMaterias: vi.fn(),
  mockUseCohortes: vi.fn(),
}));

vi.mock('@/features/comisiones/hooks/useMaterias', () => ({
  useMaterias: mockUseMaterias,
  useCohortes: mockUseCohortes,
}));

import { ComisionSelector } from './ComisionSelector';

const materias = [
  { materia_id: 'm1', nombre: 'Matemática' },
  { materia_id: 'm2', nombre: 'Lengua' },
];

const cohortes = [
  { cohorte_id: 'c1', etiqueta: '2025' },
  { cohorte_id: 'c2', etiqueta: '2026' },
];

function renderSelector() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <ComisionProvider>
        <ComisionSelector />
      </ComisionProvider>
    </MemoryRouter>,
  );
}

describe('ComisionSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseMaterias.mockReturnValue({ data: materias, isLoading: false, isError: false });
    mockUseCohortes.mockReturnValue({ data: [], isLoading: false, isError: false });
  });

  it('renders materia selector with options', () => {
    renderSelector();
    const select = screen.getByLabelText('Materia');
    expect(select).toBeInTheDocument();
    expect(screen.getByText('Matemática')).toBeInTheDocument();
    expect(screen.getByText('Lengua')).toBeInTheDocument();
  });

  it('loads cohortes when materia is selected', async () => {
    const user = userEvent.setup();
    mockUseCohortes.mockReturnValue({ data: cohortes, isLoading: false, isError: false });

    renderSelector();
    const select = screen.getByLabelText('Materia');
    await user.selectOptions(select, 'm1');

    expect(screen.getByText('2025')).toBeInTheDocument();
    expect(screen.getByText('2026')).toBeInTheDocument();
  });

  it('shows empty cohorte state when materia has no cohortes', async () => {
    const user = userEvent.setup();
    mockUseCohortes.mockReturnValue({ data: [], isLoading: false, isError: false });

    renderSelector();
    const select = screen.getByLabelText('Materia');
    await user.selectOptions(select, 'm1');

    const cohorteSelect = screen.getByLabelText('Cohorte');
    expect(cohorteSelect).toBeInTheDocument();
  });

  it('shows loading state for materias', () => {
    mockUseMaterias.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    renderSelector();
    expect(screen.getByText('Cargando materias...')).toBeInTheDocument();
  });
});
