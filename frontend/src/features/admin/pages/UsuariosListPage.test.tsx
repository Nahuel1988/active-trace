import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

const mockUseUsuarios = vi.fn();

vi.mock('@/features/admin/hooks/useUsuarios', () => ({
  useUsuarios: (filters: unknown) => mockUseUsuarios(filters),
}));

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => vi.fn() };
});

import { UsuariosListPage } from './UsuariosListPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <UsuariosListPage />
    </MemoryRouter>,
  );
}

describe('UsuariosListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUsuarios.mockReturnValue({ data: [], isLoading: false });
  });

  it('renderiza el título y botón de alta', () => {
    renderPage();
    expect(screen.getByText('Usuarios')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /nuevo usuario/i })).toBeInTheDocument();
  });

  it('filtro búsqueda llama a useUsuarios con q actualizado', async () => {
    renderPage();
    const input = screen.getByPlaceholderText(/nombre, legajo, email/i);
    await userEvent.type(input, 'Ana');
    expect(mockUseUsuarios).toHaveBeenCalledWith(
      expect.objectContaining({ q: expect.stringContaining('A') }),
    );
  });

  it('filtro regional llama a useUsuarios con regional actualizado', async () => {
    renderPage();
    const select = screen.getByRole('combobox', { name: /regional/i });
    await userEvent.selectOptions(select, 'GBA');
    expect(mockUseUsuarios).toHaveBeenCalledWith(
      expect.objectContaining({ regional: 'GBA' }),
    );
  });

  it('filtro facturador llama a useUsuarios con facturador booleano', async () => {
    renderPage();
    const select = screen.getByRole('combobox', { name: /facturador/i });
    await userEvent.selectOptions(select, 'true');
    expect(mockUseUsuarios).toHaveBeenCalledWith(
      expect.objectContaining({ facturador: true }),
    );
  });

  it('muestra estado de carga', () => {
    mockUseUsuarios.mockReturnValue({ data: undefined, isLoading: true });
    renderPage();
    expect(screen.getByText(/cargando usuarios/i)).toBeInTheDocument();
  });
});
