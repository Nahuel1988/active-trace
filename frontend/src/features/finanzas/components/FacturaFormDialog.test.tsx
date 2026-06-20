import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FacturaFormDialog } from './FacturaFormDialog';

const facturadores = [
  { id: 'u-1', nombre: 'Ana', apellidos: 'López' },
  { id: 'u-2', nombre: 'Juan', apellidos: 'Pérez' },
];

describe('FacturaFormDialog', () => {
  it('selector incluye todos los facturadores proporcionados', () => {
    render(
      <FacturaFormDialog
        open
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        isPending={false}
        error={null}
        facturadores={facturadores}
      />,
    );

    // The component renders apellidos, nombre format
    expect(screen.getByText('López, Ana')).toBeInTheDocument();
    expect(screen.getByText('Pérez, Juan')).toBeInTheDocument();
  });

  it('selector no muestra facturadores ajenos a la lista', () => {
    render(
      <FacturaFormDialog
        open
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        isPending={false}
        error={null}
        facturadores={[{ id: 'u-1', nombre: 'Ana', apellidos: 'López' }]}
      />,
    );

    expect(screen.queryByText('Pérez, Juan')).not.toBeInTheDocument();
  });

  it('muestra error 422 inline sin cerrar el dialog', () => {
    render(
      <FacturaFormDialog
        open
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        isPending={false}
        error="El usuario no es facturador"
        facturadores={facturadores}
      />,
    );

    expect(screen.getByText('El usuario no es facturador')).toBeInTheDocument();
    // Dialog remains open: the submit button is still visible
    expect(screen.getByRole('button', { name: /crear factura/i })).toBeInTheDocument();
  });

  it('deshabilita el botón de envío mientras isPending es true', () => {
    render(
      <FacturaFormDialog
        open
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        isPending
        error={null}
        facturadores={facturadores}
      />,
    );

    expect(screen.getByRole('button', { name: /guardando/i })).toBeDisabled();
  });

  it('no renderiza el dialog cuando open es false', () => {
    render(
      <FacturaFormDialog
        open={false}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        isPending={false}
        error={null}
        facturadores={facturadores}
      />,
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
