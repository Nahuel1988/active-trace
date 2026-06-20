import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MateriaFormDialog } from './MateriaFormDialog';

const noop = vi.fn();

const minimalProps = {
  open: true,
  onClose: noop,
  onSubmit: noop,
  isPending: false,
  error: null,
};

describe('MateriaFormDialog', () => {
  it('no renderiza cuando open es false', () => {
    render(<MateriaFormDialog {...minimalProps} open={false} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('submit sin clave_plus muestra error de validación Zod', async () => {
    render(<MateriaFormDialog {...minimalProps} />);
    await userEvent.type(screen.getByPlaceholderText(/nombre de la materia/i), 'Matemáticas');
    await userEvent.click(screen.getByRole('button', { name: /guardar/i }));
    await waitFor(() => {
      expect(screen.getByText(/la clave de plus es obligatoria/i)).toBeInTheDocument();
    });
  });

  it('submit sin nombre muestra error de validación Zod', async () => {
    render(<MateriaFormDialog {...minimalProps} />);
    await userEvent.selectOptions(screen.getByRole('combobox'), 'PROG');
    await userEvent.click(screen.getByRole('button', { name: /guardar/i }));
    await waitFor(() => {
      expect(screen.getByText(/el nombre es requerido/i)).toBeInTheDocument();
    });
  });

  it('submit válido (nombre + clave) llama onSubmit', async () => {
    const onSubmit = vi.fn();
    render(<MateriaFormDialog {...minimalProps} onSubmit={onSubmit} />);
    await userEvent.type(screen.getByPlaceholderText(/nombre de la materia/i), 'Programación I');
    await userEvent.selectOptions(screen.getByRole('combobox'), 'PROG');
    await userEvent.click(screen.getByRole('button', { name: /guardar/i }));
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ nombre: 'Programación I', clave_plus: 'PROG' }),
        expect.anything(),
      );
    });
  });

  it('muestra error del servidor inline', () => {
    render(<MateriaFormDialog {...minimalProps} error="Materia duplicada" />);
    expect(screen.getByText(/materia duplicada/i)).toBeInTheDocument();
  });
});
