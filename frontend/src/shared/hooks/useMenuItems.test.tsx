import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

const { mockUsePermission } = vi.hoisted(() => ({
  mockUsePermission: vi.fn(),
}));

vi.mock('@/shared/hooks/usePermission', () => ({
  usePermission: mockUsePermission,
}));

import { useMenuItems } from './useMenuItems';

describe('useMenuItems', () => {
  it('filters items based on permissions — only allowed items shown', () => {
    mockUsePermission.mockImplementation((perm: string) => {
      const allowed = ['equipos:asignar', 'avisos:publicar', 'tareas:gestionar', 'calificaciones:importar'];
      return allowed.includes(perm);
    });

    function TestComponent() {
      const items = useMenuItems();
      return (
        <ul>
          {items.map((item) => (
            <li key={item.path} data-testid="menu-item">
              {item.label}
            </li>
          ))}
        </ul>
      );
    }

    render(<TestComponent />);

    const renderedItems = screen.getAllByTestId('menu-item').map((el) => el.textContent);
    expect(renderedItems).toEqual(['Inicio', 'Equipos docentes', 'Avisos', 'Tareas', 'Importar padr\u00f3n/calificaciones']);
  });

  it('returns Inicio when no permissions granted', () => {
    mockUsePermission.mockImplementation(() => false);

    function TestComponent() {
      const items = useMenuItems();
      return (
        <ul>
          {items.map((item) => (
            <li key={item.path} data-testid="menu-item">
              {item.label}
            </li>
          ))}
        </ul>
      );
    }

    render(<TestComponent />);

    const renderedItems = screen.getAllByTestId('menu-item').map((el) => el.textContent);
    expect(renderedItems).toEqual(['Inicio']);
  });

  it('returns all items when all permissions granted', () => {
    mockUsePermission.mockImplementation(() => true);

    function TestComponent() {
      const items = useMenuItems();
      return (
        <ul>
          {items.map((item) => (
            <li key={item.path} data-testid="menu-item">
              {item.label}
            </li>
          ))}
        </ul>
      );
    }

    render(<TestComponent />);

    const renderedItems = screen.getAllByTestId('menu-item').map((el) => el.textContent);
    expect(renderedItems).toEqual([
      'Inicio',
      'Equipos docentes',
      'Avisos',
      'Tareas',
      'Coloquios',
      'Estructura',
      'Encuentros',
      'Guardias',
      'Importar padrón/calificaciones',
      'Atrasados',
      'Comunicaciones',
      'Finanzas',
      'Usuarios',
      'Auditoría',
    ]);
  });

  it('incluye Finanzas solo con liquidaciones:ver', () => {
    mockUsePermission.mockImplementation((perm: string) => perm === 'liquidaciones:ver');

    function TestComponent() {
      const items = useMenuItems();
      return <ul>{items.map((i) => <li key={i.path}>{i.label}</li>)}</ul>;
    }

    render(<TestComponent />);
    expect(screen.getByText('Finanzas')).toBeInTheDocument();
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument();
    expect(screen.queryByText('Auditoría')).not.toBeInTheDocument();
  });

  it('incluye Usuarios solo con usuarios:gestionar', () => {
    mockUsePermission.mockImplementation((perm: string) => perm === 'usuarios:gestionar');

    function TestComponent() {
      const items = useMenuItems();
      return <ul>{items.map((i) => <li key={i.path}>{i.label}</li>)}</ul>;
    }

    render(<TestComponent />);
    expect(screen.getByText('Usuarios')).toBeInTheDocument();
    expect(screen.queryByText('Finanzas')).not.toBeInTheDocument();
    expect(screen.queryByText('Auditoría')).not.toBeInTheDocument();
  });

  it('incluye Auditoría solo con auditoria:ver', () => {
    mockUsePermission.mockImplementation((perm: string) => perm === 'auditoria:ver');

    function TestComponent() {
      const items = useMenuItems();
      return <ul>{items.map((i) => <li key={i.path}>{i.label}</li>)}</ul>;
    }

    render(<TestComponent />);
    expect(screen.getByText('Auditoría')).toBeInTheDocument();
    expect(screen.queryByText('Finanzas')).not.toBeInTheDocument();
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument();
  });
});
