import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AtrasadosTable } from './AtrasadosTable';

const items = [
  { entrada_padron_id: '1', alumno_nombre: 'Juan', alumno_apellido: 'Pérez', email: 'j@t.com', materia_id: 'm1', materia_nombre: 'Matemática', clasificacion: 'missing' as const, actividad: 'TP1' },
  { entrada_padron_id: '2', alumno_nombre: 'María', alumno_apellido: 'García', email: 'm@t.com', materia_id: 'm1', materia_nombre: 'Matemática', clasificacion: 'below_threshold' as const, actividad: 'Examen' },
];

describe('AtrasadosTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders atrasados items with classification', () => {
    render(<AtrasadosTable items={items} selected={[]} onSelectionChange={vi.fn()} canCommunicate={false} onCommunicate={vi.fn()} />);

    expect(screen.getByText('Juan')).toBeInTheDocument();
    expect(screen.getByText('Pérez')).toBeInTheDocument();
    expect(screen.getByText('María')).toBeInTheDocument();
    expect(screen.getByText('Missing: TP1')).toBeInTheDocument();
    expect(screen.getByText('Below threshold: Examen')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<AtrasadosTable items={[]} selected={[]} onSelectionChange={vi.fn()} canCommunicate={false} onCommunicate={vi.fn()} />);

    expect(screen.getByText('No hay alumnos atrasados en esta comisión')).toBeInTheDocument();
  });

  it('shows two reasons in one row (one item with both via separate entries)', () => {
    const twoItems = [
      { entrada_padron_id: '1', alumno_nombre: 'Juan', alumno_apellido: 'Pérez', email: 'j@t.com', materia_id: 'm1', materia_nombre: 'Matemática', clasificacion: 'missing' as const, actividad: 'TP1' },
      { entrada_padron_id: '1', alumno_nombre: 'Juan', alumno_apellido: 'Pérez', email: 'j@t.com', materia_id: 'm1', materia_nombre: 'Matemática', clasificacion: 'below_threshold' as const, actividad: 'Examen' },
    ];
    render(<AtrasadosTable items={twoItems} selected={[]} onSelectionChange={vi.fn()} canCommunicate={false} onCommunicate={vi.fn()} />);

    expect(screen.getByText('Missing: TP1')).toBeInTheDocument();
    expect(screen.getByText('Below threshold: Examen')).toBeInTheDocument();
  });

  it('select checkbox calls onSelectionChange', async () => {
    const onSelectionChange = vi.fn();
    const user = userEvent.setup();

    render(<AtrasadosTable items={items} selected={[]} onSelectionChange={onSelectionChange} canCommunicate={false} onCommunicate={vi.fn()} />);

    const checkbox = screen.getByLabelText('Seleccionar Pérez, Juan');
    await user.click(checkbox);

    expect(onSelectionChange).toHaveBeenCalledWith(['1']);
  });
});
