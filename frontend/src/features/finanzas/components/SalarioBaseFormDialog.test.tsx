import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SalarioBaseFormDialog } from './SalarioBaseFormDialog';

describe('SalarioBaseFormDialog', () => {
  it('submit válido llama onSubmit con los datos', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <SalarioBaseFormDialog open onSubmit={onSubmit} onCancel={vi.fn()} error={null} isPending={false} />,
    );
    fireEvent.change(screen.getByLabelText(/rol/i), { target: { value: 'PROFESOR' } });
    fireEvent.change(screen.getByLabelText(/monto/i), { target: { value: '1000' } });
    fireEvent.change(screen.getByLabelText(/desde/i), { target: { value: '2026-01-01' } });
    fireEvent.click(screen.getByRole('button', { name: /guardar/i }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalled());
  });

  it('muestra error 409 de solapamiento inline y conserva el formulario abierto', () => {
    render(
      <SalarioBaseFormDialog
        open
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        error="Solapamiento de vigencia para el rol seleccionado"
        isPending={false}
      />,
    );
    expect(screen.getByText(/solapamiento de vigencia/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /guardar/i })).toBeInTheDocument();
  });

  it('deshabilita el botón mientras isPending', () => {
    render(
      <SalarioBaseFormDialog open onSubmit={vi.fn()} onCancel={vi.fn()} error={null} isPending />,
    );
    expect(screen.getByRole('button', { name: /guardar/i })).toBeDisabled();
  });
});
