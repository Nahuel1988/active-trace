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
    id: '1',
    materia_id: 'm1',
    materia_nombre: 'Matemática',
    carrera_id: 'c1',
    carrera_nombre: 'Ingeniería',
    cohorte_id: 'co1',
    cohorte_nombre: '2025',
    comisiones: ['A', 'B'],
    cantidad_docentes: 3,
    vigencia_desde: '2025-01-01',
    vigencia_hasta: '2025-12-31',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    materia_id: 'm2',
    materia_nombre: 'Lengua',
    carrera_id: 'c1',
    carrera_nombre: 'Ingeniería',
    cohorte_id: 'co1',
    cohorte_nombre: '2025',
    comisiones: ['C'],
    cantidad_docentes: 2,
    vigencia_desde: '2025-03-01',
    vigencia_hasta: '2025-11-30',
    created_at: '2025-01-15T00:00:00Z',
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
    expect(screen.getAllByText('Matemática').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Lengua').length).toBeGreaterThanOrEqual(1);
  });

  it('shows empty state', () => {
    mockUseEquipos.mockReturnValue({ data: [], isLoading: false, isError: false });
    renderPage();
    expect(screen.getByText('No hay equipos cargados')).toBeInTheDocument();
  });
});
