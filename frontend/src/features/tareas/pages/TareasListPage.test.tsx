import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

const { mockUseTareas } = vi.hoisted(() => ({
  mockUseTareas: vi.fn(),
}));

vi.mock('@/features/tareas/hooks/useTareas', () => ({
  useTareas: mockUseTareas,
}));

vi.mock('@/features/tareas/hooks/useTareaMutations', () => ({
  useCrearTarea: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useCambiarEstado: vi.fn(() => ({ mutate: vi.fn() })),
}));

import TareasListPage from './TareasListPage';

function renderPage() {
  return render(
    <MemoryRouter>
      <TareasListPage />
    </MemoryRouter>,
  );
}

describe('TareasListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders title and action buttons', () => {
    mockUseTareas.mockReturnValue({ data: [], isLoading: false });
    renderPage();
    expect(screen.getByText('Tareas')).toBeInTheDocument();
    expect(screen.getByText('Nueva tarea')).toBeInTheDocument();
    expect(screen.getByText('Vista Kanban')).toBeInTheDocument();
  });

  it('toggles between table and kanban view', async () => {
    const user = userEvent.setup();
    mockUseTareas.mockReturnValue({ data: [], isLoading: false });
    renderPage();

    const toggleBtn = screen.getByText('Vista Kanban');
    await user.click(toggleBtn);

    expect(screen.getByText('Vista Tabla')).toBeInTheDocument();
    expect(screen.queryByText('Vista Kanban')).not.toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseTareas.mockReturnValue({ data: [], isLoading: true });
    renderPage();
    expect(screen.getByText('Tareas')).toBeInTheDocument();
    expect(screen.getByText('Nueva tarea')).toBeInTheDocument();
  });
});
