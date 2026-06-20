import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ComisionProvider } from '@/shared/comision/ComisionContext';

const { mockUseAtrasados, mockUseRanking, mockUseReportes, mockUseNotasFinales, mockUseEntregasPendientes, mockUseComisionCtx, mockUsePermission } = vi.hoisted(() => ({
  mockUseAtrasados: vi.fn(),
  mockUseRanking: vi.fn(),
  mockUseReportes: vi.fn(),
  mockUseNotasFinales: vi.fn(),
  mockUseEntregasPendientes: vi.fn(),
  mockUseComisionCtx: vi.fn(),
  mockUsePermission: vi.fn(),
}));

vi.mock('@/features/atrasados/hooks/useAtrasados', () => ({
  useAtrasados: mockUseAtrasados,
  useRanking: mockUseRanking,
  useReportes: mockUseReportes,
  useNotasFinales: mockUseNotasFinales,
  useEntregasPendientes: mockUseEntregasPendientes,
}));

vi.mock('@/shared/comision/useComisionContext', () => ({
  useComisionContext: mockUseComisionCtx,
}));

vi.mock('@/shared/hooks/usePermission', () => ({
  usePermission: mockUsePermission,
}));

import AtrasadosDashboardPage from './AtrasadosDashboardPage';

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <ComisionProvider>
          <AtrasadosDashboardPage />
        </ComisionProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('AtrasadosDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseComisionCtx.mockReturnValue({ materia_id: 'm1', cohorte_id: 'c1', setComision: vi.fn() });
    mockUsePermission.mockReturnValue(false);
    mockUseAtrasados.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false, isError: false });
    mockUseRanking.mockReturnValue({ data: { items: [] }, isLoading: false, isError: false });
    mockUseReportes.mockReturnValue({ data: { total_alumnos: 0, total_actividades: 0, tasa_abrobacion_pct: 0, alumnos_atrasados: 0, alumnos_al_dia: 0, sin_datos: true }, isLoading: false });
    mockUseNotasFinales.mockReturnValue({ data: { items: [] }, isLoading: false });
    mockUseEntregasPendientes.mockReturnValue({ data: { items: [], todas_corregidas: true }, isLoading: false });
  });

  it('shows message without comision', () => {
    mockUseComisionCtx.mockReturnValue({ materia_id: '', cohorte_id: '', setComision: vi.fn() });
    renderPage();
    expect(screen.getByText('Seleccioná una comisión para ver el dashboard')).toBeInTheDocument();
  });

  it('shows sections with comision selected', () => {
    mockUseAtrasados.mockReturnValue({
      data: {
        items: [{ entrada_padron_id: '1', alumno_nombre: 'Juan', alumno_apellido: 'Pérez', email: 'j@t.com', materia_id: 'm1', materia_nombre: 'Matemática', clasificacion: 'missing', actividad: 'TP1' }],
        total: 1,
      },
      isLoading: false, isError: false,
    });

    renderPage();
    expect(screen.getByText('Atrasados')).toBeInTheDocument();
    expect(screen.getByText('Ranking')).toBeInTheDocument();
    expect(screen.getByText('Reportes')).toBeInTheDocument();
    expect(screen.getByText('Notas finales')).toBeInTheDocument();
    expect(screen.getByText('Entregas sin corregir')).toBeInTheDocument();
  });

  it('shows communicate button when permission exists and selection made', async () => {
    mockUsePermission.mockReturnValue(true);
    mockUseAtrasados.mockReturnValue({
      data: {
        items: [{ entrada_padron_id: '1', alumno_nombre: 'Juan', alumno_apellido: 'Pérez', email: 'j@t.com', materia_id: 'm1', materia_nombre: 'Matemática', clasificacion: 'missing', actividad: 'TP1' }],
        total: 1,
      },
      isLoading: false, isError: false,
    });

    const user = userEvent.setup();
    renderPage();

    const checkbox = screen.getByLabelText('Seleccionar Pérez, Juan');
    await user.click(checkbox);

    expect(mockUsePermission).toHaveBeenCalledWith('comunicacion:enviar');
  });
});
