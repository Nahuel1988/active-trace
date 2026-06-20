import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RankingTable } from './RankingTable';

const items = [
  { entrada_padron_id: '1', alumno_nombre: 'Juan', alumno_apellido: 'Pérez', actividades_aprobadas: 5, total_actividades: 10, porcentaje_aprobacion: 50 },
  { entrada_padron_id: '2', alumno_nombre: 'María', alumno_apellido: 'García', actividades_aprobadas: 3, total_actividades: 10, porcentaje_aprobacion: 30 },
];

describe('RankingTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders ranking items sorted by aprobadas descending', () => {
    render(<RankingTable items={items} />);

    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Pérez');
    expect(rows[1]).toHaveTextContent('5');
    expect(rows[2]).toHaveTextContent('García');
    expect(rows[2]).toHaveTextContent('3');
  });

  it('excludes alumnos with 0 aprobadas (RN-09)', () => {
    const withZero = [
      ...items,
      { entrada_padron_id: '3', alumno_nombre: 'Luis', alumno_apellido: 'López', actividades_aprobadas: 0, total_actividades: 10, porcentaje_aprobacion: 0 },
    ];
    render(<RankingTable items={withZero} />);

    expect(screen.queryByText('López')).not.toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<RankingTable items={[]} />);
    expect(screen.getByText('No hay datos de ranking para esta comisión')).toBeInTheDocument();
  });
});
