import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PadronPreviewTable } from './PadronPreviewTable';

describe('PadronPreviewTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const alumnos = [
    { nombre: 'Juan', apellido: 'Pérez', email: 'j@t.com', grupo: 'A' },
    { nombre: 'María', apellido: 'García', email: 'm@t.com' },
  ];

  it('renders detected students', () => {
    render(<PadronPreviewTable alumnos={alumnos} errores={[]} totalDetectados={2} onConfirm={vi.fn()} />);

    expect(screen.getByText('Juan')).toBeInTheDocument();
    expect(screen.getByText('Pérez')).toBeInTheDocument();
    expect(screen.getByText('María')).toBeInTheDocument();
    expect(screen.getByText('2 alumnos detectados')).toBeInTheDocument();
  });

  it('blocks confirm when there are errors', () => {
    render(
      <PadronPreviewTable
        alumnos={alumnos}
        errores={['Formato inválido en fila 3']}
        totalDetectados={2}
        onConfirm={vi.fn()}
      />,
    );

    expect(screen.getByText('Formato inválido en fila 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Errores detectados' })).toBeDisabled();
  });

  it('enables confirm when no errors', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();

    render(<PadronPreviewTable alumnos={alumnos} errores={[]} totalDetectados={2} onConfirm={onConfirm} />);

    const confirmBtn = screen.getByRole('button', { name: 'Confirmar importación' });
    expect(confirmBtn).not.toBeDisabled();

    await user.click(confirmBtn);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('shows empty state when no alumnos', () => {
    render(<PadronPreviewTable alumnos={[]} errores={[]} totalDetectados={0} onConfirm={vi.fn()} />);

    expect(screen.getByText('No se detectaron alumnos en el archivo')).toBeInTheDocument();
  });
});
