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
      const allowed = ['equipos:asignar', 'avisos:publicar', 'tareas:gestionar'];
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
    expect(renderedItems).toEqual(['Inicio', 'Equipos docentes', 'Avisos', 'Tareas']);
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
    ]);
  });
});
