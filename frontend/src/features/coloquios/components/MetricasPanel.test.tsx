import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const { mockUseMetricas } = vi.hoisted(() => ({
  mockUseMetricas: vi.fn(),
}));

vi.mock('@/features/coloquios/hooks/useColoquios', () => ({
  useMetricas: mockUseMetricas,
}));

import { MetricasPanel } from './MetricasPanel';

describe('MetricasPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows spinner while loading', () => {
    mockUseMetricas.mockReturnValue({ data: undefined, isLoading: true });
    render(<MetricasPanel />);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  it('renders 4 metric cards with data', () => {
    mockUseMetricas.mockReturnValue({
      data: {
        total_candidatos: 150,
        instancias_activas: 12,
        reservas_activas: 45,
        notas_registradas: 320,
      },
      isLoading: false,
    });
    render(<MetricasPanel />);

    expect(screen.getByText('Total candidatos')).toBeInTheDocument();
    expect(screen.getByText('Instancias activas')).toBeInTheDocument();
    expect(screen.getByText('Reservas activas')).toBeInTheDocument();
    expect(screen.getByText('Notas registradas')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();
    expect(screen.getByText('320')).toBeInTheDocument();
  });

  it('returns null when no data', () => {
    mockUseMetricas.mockReturnValue({ data: undefined, isLoading: false });
    const { container } = render(<MetricasPanel />);
    expect(container.firstChild).toBeNull();
  });
});
