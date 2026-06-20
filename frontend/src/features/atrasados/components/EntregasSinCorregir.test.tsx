import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EntregasSinCorregir } from './EntregasSinCorregir';

const { mockExport } = vi.hoisted(() => ({
  mockExport: vi.fn(),
}));

vi.mock('@/features/atrasados/services/atrasadosApi', () => ({
  exportEntregasPendientes: mockExport,
}));

const items = [
  { alumno: 'Juan Pérez', actividad: 'TP1', fecha_submission: '2025-03-15', materia: 'Matemática' },
  { alumno: 'María García', actividad: 'TP2', fecha_submission: '2025-03-16', materia: 'Matemática' },
];

describe('EntregasSinCorregir', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders entregas pendientes', () => {
    render(<EntregasSinCorregir items={items} todasCorregidas={false} materiaId="m1" cohorteId="c1" />);

    expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
    expect(screen.getByText('TP1')).toBeInTheDocument();
    expect(screen.getByText('María García')).toBeInTheDocument();
  });

  it('shows todas corregidas message', () => {
    render(<EntregasSinCorregir items={[]} todasCorregidas={true} materiaId="m1" cohorteId="c1" />);

    expect(screen.getByText('Todas las entregas están corregidas')).toBeInTheDocument();
  });

  it('export button calls export function', async () => {
    const user = (await import('@testing-library/user-event')).default;
    render(<EntregasSinCorregir items={items} todasCorregidas={false} materiaId="m1" cohorteId="c1" />);

    const exportBtn = screen.getByText('Exportar');
    await user.click(exportBtn);

    expect(mockExport).toHaveBeenCalledWith('m1', 'c1');
  });
});
