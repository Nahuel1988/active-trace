import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const mockUseMetricasAuditoria = vi.fn();

vi.mock('@/features/admin/hooks/useAuditoria', () => ({
  useMetricasAuditoria: (filters: unknown) => mockUseMetricasAuditoria(filters),
}));

vi.mock('@/shared/components/Spinner', () => ({
  Spinner: () => <div>Loading...</div>,
}));

import { AuditoriaPanelPage } from './AuditoriaPanelPage';

const mockMetricas = {
  acciones_por_dia: [
    { fecha: '2026-06-01', cantidad: 5 },
    { fecha: '2026-06-02', cantidad: 10 },
  ],
  comunicaciones_por_docente: [
    {
      usuario_id: 'u-1',
      nombre: 'Ana',
      apellidos: 'López',
      total: 3,
      enviadas: 2,
      fallidas: 1,
      canceladas: 0,
    },
  ],
  interacciones: [
    {
      usuario_id: 'u-1',
      nombre: 'Ana',
      apellidos: 'López',
      materia_id: 'm-1',
      materia_nombre: 'Programación',
      accion: 'CREATE_ALUMNO',
      cantidad: 4,
    },
  ],
  ultimas_acciones: [
    {
      id: 'a-1',
      tenant_id: 't',
      actor_id: 'u-1',
      actor_nombre: 'Ana López',
      materia_id: null,
      materia_nombre: null,
      accion: 'LOGIN',
      filas_afectadas: 0,
      ip: '127.0.0.1',
      user_agent: 'Mozilla',
      fecha_hora: '2026-06-01T10:00:00Z',
    },
  ],
};

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('AuditoriaPanelPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('muestra el título del panel', () => {
    mockUseMetricasAuditoria.mockReturnValue({ data: undefined, isLoading: false });
    render(<AuditoriaPanelPage />, { wrapper });
    expect(screen.getByText(/panel de auditoría/i)).toBeInTheDocument();
  });

  it('renderiza las 4 visualizaciones cuando hay datos', () => {
    mockUseMetricasAuditoria.mockReturnValue({ data: mockMetricas, isLoading: false });
    render(<AuditoriaPanelPage />, { wrapper });

    expect(screen.getByText(/acciones por día/i)).toBeInTheDocument();
    expect(screen.getByText(/comunicaciones por docente/i)).toBeInTheDocument();
    expect(screen.getByText(/interacciones docente/i)).toBeInTheDocument();
    expect(screen.getByText(/últimas acciones/i)).toBeInTheDocument();
  });

  it('muestra datos de comunicaciones por docente', () => {
    mockUseMetricasAuditoria.mockReturnValue({ data: mockMetricas, isLoading: false });
    render(<AuditoriaPanelPage />, { wrapper });
    expect(screen.getAllByText(/Ana/i).length).toBeGreaterThanOrEqual(1);
  });

  it('no muestra visualizaciones cuando no hay datos', () => {
    mockUseMetricasAuditoria.mockReturnValue({ data: undefined, isLoading: false });
    render(<AuditoriaPanelPage />, { wrapper });
    expect(screen.queryByText(/acciones por día/i)).not.toBeInTheDocument();
  });
});
