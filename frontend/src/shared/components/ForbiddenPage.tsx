// ── ForbiddenPage ────────────────────────────────────────────────────────────
// Página 403 — el usuario no tiene permiso para acceder al recurso.

import { Link } from 'react-router-dom';

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-300">403</h1>
        <p className="mt-4 text-lg text-gray-600">
          No tenés permisos para acceder a esta sección.
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Si creés que esto es un error, contactá al administrador del sistema.
        </p>
        <Link
          to="/"
          className="mt-6 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}
