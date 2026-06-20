import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockMutate = vi.fn();

vi.mock('@/features/finanzas/hooks/useFacturaMutations', () => ({
  useAbonarFactura: () => ({ mutate: mockMutate, isPending: false }),
}));

import { AbonarFacturaButton } from './AbonarFacturaButton';

describe('AbonarFacturaButton', () => {
  it('muestra botón inicial Abonar', () => {
    render(<AbonarFacturaButton facturaId="f-1" />);
    expect(screen.getByRole('button', { name: /abonar/i })).toBeInTheDocument();
  });

  it('click en Abonar muestra confirmación', async () => {
    render(<AbonarFacturaButton facturaId="f-1" />);
    await userEvent.click(screen.getByRole('button', { name: /abonar/i }));
    expect(screen.getByText(/confirmar pago/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
  });

  it('Confirmar llama mutate con el facturaId', async () => {
    mockMutate.mockImplementation((_id: string, opts: { onSuccess: () => void }) => {
      opts.onSuccess();
    });
    render(<AbonarFacturaButton facturaId="f-99" />);
    await userEvent.click(screen.getByRole('button', { name: /abonar/i }));
    await userEvent.click(screen.getByRole('button', { name: /confirmar/i }));
    expect(mockMutate).toHaveBeenCalledWith('f-99', expect.any(Object));
  });

  it('error 409 muestra mensaje sin crash y no cierra confirmación', async () => {
    mockMutate.mockImplementation(
      (_id: string, opts: { onError: (err: unknown) => void }) => {
        const err = Object.assign(new Error('Conflict'), { response: { status: 409 } });
        opts.onError(err);
      },
    );
    render(<AbonarFacturaButton facturaId="f-1" />);
    await userEvent.click(screen.getByRole('button', { name: /abonar/i }));
    await userEvent.click(screen.getByRole('button', { name: /confirmar/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/ya fue abonada/i);
  });

  it('Cancelar en confirmación vuelve al botón inicial', async () => {
    render(<AbonarFacturaButton facturaId="f-1" />);
    await userEvent.click(screen.getByRole('button', { name: /abonar/i }));
    await userEvent.click(screen.getByRole('button', { name: /cancelar/i }));
    expect(screen.getByRole('button', { name: /abonar/i })).toBeInTheDocument();
    expect(screen.queryByText(/confirmar pago/i)).not.toBeInTheDocument();
  });
});
