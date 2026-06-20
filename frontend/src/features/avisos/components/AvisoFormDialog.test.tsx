import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const { mockCrearMutateAsync, mockActualizarMutateAsync } = vi.hoisted(() => ({
  mockCrearMutateAsync: vi.fn(),
  mockActualizarMutateAsync: vi.fn(),
}));

vi.mock('@/features/avisos/hooks/useAvisos', () => ({
  useCrearAviso: vi.fn(() => ({ mutateAsync: mockCrearMutateAsync, error: null })),
  useActualizarAviso: vi.fn(() => ({ mutateAsync: mockActualizarMutateAsync, error: null })),
}));

import { AvisoFormDialog } from './AvisoFormDialog';
import type { Aviso } from '@/features/avisos/types';

const mockAviso: Aviso = {
  id: '1',
  titulo: 'Aviso existente',
  cuerpo: 'Contenido del aviso',
  alcance: 'Global',
  severidad: 'Advertencia',
  materia_id: null,
  cohorte_id: null,
  rol_destino: null,
  inicio_en: '2025-01-01T00:00:00',
  fin_en: '2025-01-15T00:00:00',
  orden: 1,
  requiere_ack: false,
  activo: true,
  creado_por: 'u1',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

describe('AvisoFormDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when closed', () => {
    const { container } = render(
      <AvisoFormDialog open={false} onClose={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders form dialog when open', () => {
    render(<AvisoFormDialog open={true} onClose={vi.fn()} />);
    expect(screen.getByText('Nuevo aviso')).toBeInTheDocument();
    expect(screen.getByText('Crear')).toBeInTheDocument();
  });

  it('shows validation errors on submit vacío', async () => {
    const user = userEvent.setup();
    render(<AvisoFormDialog open={true} onClose={vi.fn()} />);

    await user.click(screen.getByText('Crear'));

    await waitFor(() => {
      const errors = screen.queryAllByText(/requerido|Requerido/);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  it('calls crearAviso on valid submission', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<AvisoFormDialog open={true} onClose={onClose} />);

    await user.type(screen.getByLabelText('Título'), 'Nuevo aviso test');
    await user.type(screen.getByLabelText('Cuerpo'), 'Contenido de prueba');
    await user.type(screen.getByLabelText('Inicio'), '2025-01-01T10:00');
    await user.type(screen.getByLabelText('Fin'), '2025-01-15T10:00');

    await user.click(screen.getByText('Crear'));

    await waitFor(() => {
      expect(mockCrearMutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('pre-fills form in edit mode', async () => {
    render(
      <AvisoFormDialog open={true} onClose={vi.fn()} aviso={mockAviso} />,
    );

    await waitFor(() => {
      const tituloInput = screen.getByLabelText('Título') as HTMLInputElement;
      expect(tituloInput.value).toBe('Aviso existente');
    });
  });
});
