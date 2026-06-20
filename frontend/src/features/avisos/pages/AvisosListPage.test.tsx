import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { mockUseAvisos } = vi.hoisted(() => ({
  mockUseAvisos: vi.fn(),
}));

vi.mock('@/features/avisos/hooks/useAvisos', () => ({
  useAvisos: mockUseAvisos,
  useCrearAviso: vi.fn(() => ({ mutateAsync: vi.fn(), error: null })),
  useActualizarAviso: vi.fn(() => ({ mutate: vi.fn(), error: null })),
  useEliminarAviso: vi.fn(() => ({ mutate: vi.fn() })),
}));

import AvisosListPage from './AvisosListPage';

const mockAvisos = [
  {
    id: '1',
    titulo: 'Aviso importante',
    cuerpo: 'Este es un aviso de prueba',
    alcance: 'Global' as const,
    severidad: 'Advertencia' as const,
    materia_id: null,
    cohorte_id: null,
    rol_destino: null,
    inicio_en: '2025-01-01T00:00:00',
    fin_en: '2025-01-15T00:00:00',
    orden: 1,
    requiere_ack: false,
    activo: true,
    creado_por: 'u1',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    titulo: 'Aviso crítico',
    cuerpo: 'Situación crítica',
    alcance: 'PorRol' as const,
    severidad: 'Critico' as const,
    materia_id: null,
    cohorte_id: null,
    rol_destino: 'profesor',
    inicio_en: '2025-02-01T00:00:00',
    fin_en: '2025-02-10T00:00:00',
    orden: 2,
    requiere_ack: true,
    activo: true,
    creado_por: 'u1',
    created_at: '2025-02-01T00:00:00Z',
    updated_at: '2025-02-01T00:00:00Z',
  },
];

function renderPage() {
  return render(
    <MemoryRouter>
      <AvisosListPage />
    </MemoryRouter>,
  );
}

describe('AvisosListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner', () => {
    mockUseAvisos.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    renderPage();
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  it('shows error message', () => {
    mockUseAvisos.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed'),
    });
    renderPage();
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('renders avisos table with data and badges', () => {
    mockUseAvisos.mockReturnValue({ data: mockAvisos, isLoading: false, isError: false });
    renderPage();
    expect(screen.getByText('Aviso importante')).toBeInTheDocument();
    expect(screen.getByText('Aviso crítico')).toBeInTheDocument();
    expect(screen.getByText('Advertencia')).toBeInTheDocument();
    expect(screen.getByText('Critico')).toBeInTheDocument();
  });
});
