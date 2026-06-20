import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const { mockUseGuardias, mockApiGet } = vi.hoisted(() => ({
  mockUseGuardias: vi.fn(),
  mockApiGet: vi.fn().mockResolvedValue({ data: [] }),
}));

vi.mock('@/features/guardias/hooks/useGuardias', () => ({
  useGuardias: mockUseGuardias,
  useCrearGuardia: vi.fn(() => ({ mutateAsync: vi.fn() })),
  useCambiarEstadoGuardia: vi.fn(() => ({ mutate: vi.fn() })),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    post: vi.fn(),
    get: mockApiGet,
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { baseURL: '', withCredentials: true },
  },
  setAccessToken: vi.fn(),
  setOnSessionExpired: vi.fn(),
  getAccessToken: vi.fn(),
  ForbiddenError: class ForbiddenError extends Error {
    constructor(message?: string) {
      super(message ?? 'Forbidden');
      this.name = 'ForbiddenError';
    }
  },
}));

import GuardiasListPage from './GuardiasListPage';

const mockGuardias = [
  {
    id: '1',
    materia: { id: 'm1', nombre: 'Matemática' },
    tutor: { id: 't1', nombre: 'Juan Pérez' },
    carrera: { id: 'c1', nombre: 'Ingeniería' },
    cohorte: { id: 'co1', nombre: '2025' },
    dia: 'lunes',
    horario: '10:00-12:00',
    estado: 'pendiente' as const,
    comentarios: '',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    materia: { id: 'm2', nombre: 'Lengua' },
    tutor: { id: 't2', nombre: 'María García' },
    carrera: { id: 'c1', nombre: 'Ingeniería' },
    cohorte: { id: 'co1', nombre: '2025' },
    dia: 'miércoles',
    horario: '14:00-16:00',
    estado: 'realizada' as const,
    comentarios: 'Ok',
    created_at: '2025-01-15T00:00:00Z',
  },
];

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, gcTime: 0 },
  },
});

function renderPage() {
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <GuardiasListPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe('GuardiasListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders title, export and new buttons', () => {
    mockUseGuardias.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText('Guardias')).toBeInTheDocument();
    expect(screen.getByText('Exportar CSV')).toBeInTheDocument();
    expect(screen.getByText('Nueva guardia')).toBeInTheDocument();
  });

  it('renders guardia table with data', () => {
    mockUseGuardias.mockReturnValue({ data: mockGuardias, isLoading: false });
    renderPage();
    expect(screen.getByText('Matemática')).toBeInTheDocument();
    expect(screen.getByText('Lengua')).toBeInTheDocument();
  });

  it('shows filters in GuardiaTable', () => {
    mockUseGuardias.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText('Todas las materias')).toBeInTheDocument();
    expect(screen.getByText('Todos los cohortes')).toBeInTheDocument();
  });
});
