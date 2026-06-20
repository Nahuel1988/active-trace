import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { mockUseSlots } = vi.hoisted(() => ({
  mockUseSlots: vi.fn(),
}));

vi.mock('@/features/encuentros/hooks/useEncuentros', () => ({
  useSlots: mockUseSlots,
}));

vi.mock('@/features/encuentros/hooks/useEncuentroMutations', () => ({
  useCrearSlot: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useEliminarSlot: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

import EncuentrosSlotsPage from './EncuentrosSlotsPage';

const mockSlots = [
  {
    id: '1',
    materia_id: 'm1',
    titulo: 'Clase 1',
    dia_semana: 'lunes',
    hora: '10:00',
    modo: 'recurrente' as const,
    fecha_inicio: '2025-03-01',
    cant_semanas: 16,
    fecha_unica: null,
    meet_url: 'https://meet.google.com/abc',
    vig_desde: '2025-03-01',
    vig_hasta: '2025-07-01',
    instancias: [],
  },
  {
    id: '2',
    materia_id: 'm2',
    titulo: 'Clase especial',
    dia_semana: 'miércoles',
    hora: '14:00',
    modo: 'unico' as const,
    fecha_inicio: '2025-04-15',
    cant_semanas: null,
    fecha_unica: '2025-04-15',
    meet_url: null,
    vig_desde: '2025-04-15',
    vig_hasta: '2025-04-15',
    instancias: [],
  },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <EncuentrosSlotsPage />
    </MemoryRouter>,
  );
}

describe('EncuentrosSlotsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders title and new slot button', () => {
    mockUseSlots.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText('Encuentros')).toBeInTheDocument();
    expect(screen.getByText('Nuevo slot')).toBeInTheDocument();
  });

  it('shows loading spinner', () => {
    mockUseSlots.mockReturnValue({ data: undefined, isLoading: true });
    renderPage();
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  it('renders slot data in table', () => {
    mockUseSlots.mockReturnValue({ data: mockSlots, isLoading: false });
    renderPage();
    expect(screen.getByText('Clase 1')).toBeInTheDocument();
    expect(screen.getByText('Clase especial')).toBeInTheDocument();
    expect(screen.getByText('Recurrente')).toBeInTheDocument();
    expect(screen.getByText('Único')).toBeInTheDocument();
  });
});
