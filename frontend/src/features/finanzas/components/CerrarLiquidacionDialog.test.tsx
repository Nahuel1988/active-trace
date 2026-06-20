import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CerrarLiquidacionDialog } from './CerrarLiquidacionDialog';

describe('CerrarLiquidacionDialog', () => {
  it('llama onConfirm al confirmar', () => {
    const onConfirm = vi.fn();
    render(<CerrarLiquidacionDialog open onConfirm={onConfirm} onCancel={vi.fn()} isPending={false} error={null} />);
    fireEvent.click(screen.getByRole('button', { name: /confirmar/i }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('muestra error 409 inline sin cerrar el dialog', () => {
    render(
      <CerrarLiquidacionDialog
        open
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        isPending={false}
        error="La liquidación ya está cerrada"
      />,
    );
    expect(screen.getByText('La liquidación ya está cerrada')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument();
  });

  it('deshabilita el botón mientras está pendiente', () => {
    render(<CerrarLiquidacionDialog open onConfirm={vi.fn()} onCancel={vi.fn()} isPending error={null} />);
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeDisabled();
  });
});
