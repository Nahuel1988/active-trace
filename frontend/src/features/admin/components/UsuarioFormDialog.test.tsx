import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UsuarioFormDialog } from './UsuarioFormDialog';

const noop = vi.fn();

const minimalProps = {
  open: true,
  onClose: noop,
  onSubmit: noop,
  isPending: false,
  error: null,
};

describe('UsuarioFormDialog', () => {
  it('no renderiza cuando open es false', () => {
    render(<UsuarioFormDialog {...minimalProps} open={false} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renderiza el formulario cuando open es true', () => {
    render(<UsuarioFormDialog {...minimalProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /crear usuario/i })).toBeInTheDocument();
  });

  it('muestra error 422 inline sin cerrar el dialog', () => {
    render(
      <UsuarioFormDialog
        {...minimalProps}
        error="El campo email ya existe"
      />,
    );
    expect(screen.getByText(/El campo email ya existe/i)).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('onClose se llama al clickear Cancelar', async () => {
    const onClose = vi.fn();
    render(<UsuarioFormDialog {...minimalProps} onClose={onClose} />);
    await userEvent.click(screen.getByRole('button', { name: /cancelar/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('botón de submit deshabilitado mientras isPending', () => {
    render(<UsuarioFormDialog {...minimalProps} isPending />);
    expect(screen.getByRole('button', { name: /guardando/i })).toBeDisabled();
  });

  it('modo edición muestra "Editar usuario" como título', () => {
    render(<UsuarioFormDialog {...minimalProps} isEdit />);
    expect(screen.getByText('Editar usuario')).toBeInTheDocument();
  });
});
