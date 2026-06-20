import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Cohorte } from '@/features/estructura/types';

const { mockUseCohortes } = vi.hoisted(() => ({
  mockUseCohortes: vi.fn(),
}));

vi.mock('@/features/estructura/hooks/useEstructura', () => ({
  useCohortes: () => mockUseCohortes(),
  useCrearCohorte: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
  useEliminarCohorte: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock('@/shared/components/Spinner', () => ({
  Spinner: () => <div>Loading...</div>,
}));

import CohortesListPage from './CohortesListPage';

const mockCohortes: Cohorte[] = [
  {
    id: 'c-1',
    tenant_id: 't',
    etiqueta: '2026-S1',
    carrera_id: 'car-1',
    fecha_inicio: '2026-03-01',
    fecha_fin: '2026-07-31',
    created_at: '',
    updated_at: '',
  },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <CohortesListPage />
    </MemoryRouter>,
  );
}

describe('CohortesListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renderiza el título y botón de alta', () => {
    mockUseCohortes.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText('Cohortes')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /nueva cohorte/i })).toBeInTheDocument();
  });

  it('estado vacío "No hay cohortes registradas"', () => {
    mockUseCohortes.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText(/no hay cohortes registradas/i)).toBeInTheDocument();
  });

  it('renderiza cohortes cuando hay datos', () => {
    mockUseCohortes.mockReturnValue({ data: mockCohortes, isLoading: false });
    renderPage();
    expect(screen.getByText('2026-S1')).toBeInTheDocument();
  });

  it('muestra spinner mientras carga', () => {
    mockUseCohortes.mockReturnValue({ data: undefined, isLoading: true });
    renderPage();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
