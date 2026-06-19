// ── Sidebar ──────────────────────────────────────────────────────────────────
// Menú de navegación lateral. Array declarativo de items filtrados por permiso.
// D-05: Menú dinámico derivado de permisos. Sin lógica de roles hardcodeada.

import { NavLink } from 'react-router-dom';
import { usePermission } from '@/shared/hooks/usePermission';

interface SidebarItem {
  label: string;
  path: string;
  /** Ícono SVG inline opcional */
  icon?: string;
  /** Permiso requerido (opcional). Si no se especifica, visible para todos */
  permission?: string;
}

const sidebarItems: SidebarItem[] = [
  {
    label: 'Inicio',
    path: '/',
    icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  },
  // Los items de features de dominio se agregan acá (C-22, C-23, C-24)
  // Ejemplo:
  // { label: 'Alumnos', path: '/alumnos', permission: 'alumnos:ver' },
  // { label: 'Estructura', path: '/estructura', permission: 'estructura:gestionar' },
  // { label: 'Liquidaciones', path: '/liquidaciones', permission: 'liquidaciones:ver' },
];

export function Sidebar() {
  const visibleItems = sidebarItems.filter((item) => {
    if (!item.permission) return true;
    return usePermission(item.permission);
  });

  return (
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 bg-white">
      {/* Brand */}
      <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6">
        <span className="text-xl font-bold text-indigo-600">trace</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {visibleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`
            }
          >
            {item.icon && (
              <svg
                className="h-5 w-5 flex-shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d={item.icon}
                />
              </svg>
            )}
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
