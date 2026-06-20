import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UmbralForm } from './UmbralForm';

describe('UmbralForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows default 60 when no umbral configured', () => {
    render(<UmbralForm umbralPorcentaje={60} isPending={false} onSave={vi.fn()} />);

    const input = screen.getByLabelText('Umbral de aprobación (%)');
    expect(input).toHaveValue(60);
  });

  it('shows configured umbral value', () => {
    render(<UmbralForm umbralPorcentaje={75} isPending={false} onSave={vi.fn()} />);

    const input = screen.getByLabelText('Umbral de aprobación (%)');
    expect(input).toHaveValue(75);
  });

  it('does not call onSave with invalid value', async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();

    render(<UmbralForm umbralPorcentaje={60} isPending={false} onSave={onSave} />);

    const input = screen.getByLabelText('Umbral de aprobación (%)');
    await user.clear(input);
    await user.type(input, '-5');

    await user.click(screen.getByText('Guardar umbral'));

    expect(onSave).not.toHaveBeenCalled();
    expect(screen.getByText('Debe ser un número entre 0 y 100')).toBeInTheDocument();
  });

  it('calls onSave with valid value', async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();

    render(<UmbralForm umbralPorcentaje={60} isPending={false} onSave={onSave} />);

    const input = screen.getByLabelText('Umbral de aprobación (%)');
    await user.clear(input);
    await user.type(input, '80');

    await user.click(screen.getByText('Guardar umbral'));

    expect(onSave).toHaveBeenCalledWith(80);
  });

  it('shows loading state', () => {
    render(<UmbralForm umbralPorcentaje={60} isPending={true} onSave={vi.fn()} />);

    expect(screen.getByText('Guardando...')).toBeInTheDocument();
  });
});
