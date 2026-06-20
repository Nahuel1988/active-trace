import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const { mockMutate } = vi.hoisted(() => ({
  mockMutate: vi.fn(),
}));

vi.mock('@/features/equipos/hooks/useEquipoMutations', () => ({
  useAsignacionMasiva: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
    isError: false,
  })),
}));

import { AsignacionMasivaForm } from './AsignacionMasivaForm';

describe('AsignacionMasivaForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders step 1 by default', () => {
    render(<AsignacionMasivaForm />);
    expect(screen.getByText('Paso 1: Datos del equipo')).toBeInTheDocument();
    expect(screen.getByText('Siguiente')).toBeInTheDocument();
  });

  it('proceeds to step 2', async () => {
    const user = userEvent.setup();
    render(<AsignacionMasivaForm />);

    await user.click(screen.getByText('Siguiente'));

    expect(screen.getByText('Paso 2: Asignación')).toBeInTheDocument();
    expect(screen.getByText('Asignar docentes')).toBeInTheDocument();
  });

  it('shows validation errors on empty submit in step 2', async () => {
    const user = userEvent.setup();
    render(<AsignacionMasivaForm />);

    await user.click(screen.getByText('Siguiente'));

    await user.click(screen.getByText('Asignar docentes'));

    const errorMessages = screen.queryAllByText(/Seleccioná|Requerido|Ingresá/);
    expect(errorMessages.length).toBeGreaterThan(0);
  });

  it('calls mutation on valid submit', async () => {
    const user = userEvent.setup();
    const { container } = render(<AsignacionMasivaForm />);

    const combosStep1 = screen.getAllByRole('combobox');
    await user.selectOptions(combosStep1[0], '1');
    await user.selectOptions(combosStep1[1], '1');
    await user.selectOptions(combosStep1[2], '1');

    await user.click(screen.getByText('Siguiente'));

    const combosStep2 = screen.getAllByRole('combobox');
    await user.selectOptions(combosStep2[0], 'profesor');

    const comisionesInput = screen.getByPlaceholderText('A, B, C');
    await user.type(comisionesInput, 'A, B');

    const dateInputs = container.querySelectorAll<HTMLInputElement>('input[type="date"]');
    await user.type(dateInputs[0], '2025-01-01');
    await user.type(dateInputs[1], '2025-12-31');

    await user.click(screen.getByText('Asignar docentes'));

    expect(mockMutate).toHaveBeenCalledTimes(1);
  });
});
