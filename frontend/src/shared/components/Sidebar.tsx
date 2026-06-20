// ── Sidebar ──────────────────────────────────────────────────────────────────
// Menú de navegación lateral. Usa useMenuItems hook para filtrado por permisos.
// D-02 + D-05: Menú dinámico derivado de permisos, sin hooks violation.

import { NavLink } from 'react-router-dom';
import { useMenuItems } from '@/shared/hooks/useMenuItems';

export function Sidebar() {
  const visibleItems = useMenuItems();

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
