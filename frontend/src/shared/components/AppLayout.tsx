// ── AppLayout ────────────────────────────────────────────────────────────────
// Layout shell de la aplicación autenticada.
// Sidebar + header + <Outlet /> para contenido.
// Responsive mobile-first: sidebar oculta en mobile, visible con toggle.
// Botón de logout en header.

import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/shared/hooks/useAuth';
import { Sidebar } from '@/shared/components/Sidebar';
import * as authApi from '@/features/auth/services/authApi';

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { clearSession, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Aunque la request falle, limpiamos sesión local
    } finally {
      clearSession();
      navigate('/login', { replace: true });
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar />
      </div>

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 lg:px-6">
          {/* Mobile menu button */}
          <button
            type="button"
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 lg:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Abrir menú"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              {sidebarOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>

          {/* Spacer */}
          <div className="flex-1" />

          {/* User info + logout */}
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-gray-600 sm:block">
              {user?.roles?.join(', ') ?? 'Usuario'}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-md px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Cerrar sesión
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
