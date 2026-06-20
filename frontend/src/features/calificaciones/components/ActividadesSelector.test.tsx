import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActividadesSelector } from './ActividadesSelector';

const actividades = [
  { id: 'a1', nombre: 'TP1', escala: 'numerica' as const },
  { id: 'a2', nombre: 'TP2', escala: 'textual' as const },
  { id: 'a3', nombre: 'Examen', escala: 'numerica' as const },
];

describe('ActividadesSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all actividades with checkboxes', () => {
    render(<ActividadesSelector actividades={actividades} selected={[]} onChange={vi.fn()} />);

    expect(screen.getByText('TP1')).toBeInTheDocument();
    expect(screen.getByText('TP2')).toBeInTheDocument();
    expect(screen.getByText('Examen')).toBeInTheDocument();
  });

  it('shows escala for each actividad', () => {
    render(<ActividadesSelector actividades={actividades} selected={[]} onChange={vi.fn()} />);

    expect(screen.getAllByText('numerica').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('textual')).toBeInTheDocument();
  });

  it('calls onChange with selected ids', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<ActividadesSelector actividades={actividades} selected={['a1']} onChange={onChange} />);

    const tp2Checkbox = screen.getByLabelText('TP2');
    await user.click(tp2Checkbox);

    expect(onChange).toHaveBeenCalledWith(['a1', 'a2']);
  });

  it('unselects an actividad', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<ActividadesSelector actividades={actividades} selected={['a1', 'a2']} onChange={onChange} />);

    const tp1Checkbox = screen.getByLabelText('TP1');
    await user.click(tp1Checkbox);

    expect(onChange).toHaveBeenCalledWith(['a2']);
  });

  it('select all / deselect all works', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<ActividadesSelector actividades={actividades} selected={[]} onChange={onChange} />);

    const selectAll = screen.getByText('Seleccionar todas');
    await user.click(selectAll);

    expect(onChange).toHaveBeenCalledWith(['a1', 'a2', 'a3']);
  });
});
