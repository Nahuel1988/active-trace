import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { mockUseCarreras } = vi.hoisted(() => ({
  mockUseCarreras: vi.fn(),
}));

vi.mock('@/features/estructura/hooks/useEstructura', () => ({
  useCarreras: mockUseCarreras,
  useCrearCarrera: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false })),
}));

import CarrerasListPage from './CarrerasListPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <CarrerasListPage />
    </MemoryRouter>,
  );
}

describe('CarrerasListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders title and description', () => {
    mockUseCarreras.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getAllByText('Carreras').length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText('Gestión de carreras de la institución.'),
    ).toBeInTheDocument();
  });

  it('renders CarreraTable component with empty state', () => {
    mockUseCarreras.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText('No hay carreras registradas.')).toBeInTheDocument();
  });
});
