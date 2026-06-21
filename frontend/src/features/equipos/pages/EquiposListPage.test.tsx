import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { mockUseEquipos } = vi.hoisted(() => ({
  mockUseEquipos: vi.fn(),
}));

vi.mock('@/features/equipos/hooks/useEquipos', () => ({
  useEquipos: mockUseEquipos,
  useMisEquipos: vi.fn(),
  useAsignaciones: vi.fn(),
}));

import EquiposListPage from './EquiposListPage';

const mockEquipos = [
  {
    materia_id: 'm1',
    carrera_id: 'c1',
    cohorte_id: 'co1',
    conteo: 3,
  },
  {
    materia_id: 'm2',
    carrera_id: 'c1',
    cohorte_id: 'co1',
    conteo: 2,
  },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <EquiposListPage />
    </MemoryRouter>,
  );
}

describe('EquiposListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner', () => {
    mockUseEquipos.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    renderPage();
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  it('shows error state with retry button', () => {
    mockUseEquipos.mockReturnValue({ data: undefined, isLoading: false, isError: true, refetch: vi.fn() });
    renderPage();
    expect(screen.getByText('Error al cargar equipos')).toBeInTheDocument();
    expect(screen.getByText('Reintentar')).toBeInTheDocument();
  });

  it('renders table with equipos data', () => {
    mockUseEquipos.mockReturnValue({ data: mockEquipos, isLoading: false, isError: false });
    renderPage();
    expect(screen.getAllByText('m1').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('m2').length).toBeGreaterThanOrEqual(1);
  });

  it('shows empty state', () => {
    mockUseEquipos.mockReturnValue({ data: [], isLoading: false, isError: false });
    renderPage();
    expect(screen.getByText('No hay equipos cargados')).toBeInTheDocument();
  });
});
