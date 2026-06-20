// ── UsuariosListPage ───────────────────────────────────────────────────────
// List page for Usuarios ABM.
// SECURITY (D-04): Only `Usuario` (no PII) flows into this page and its
// children. PII is only loaded in UsuarioDetailPage / UsuarioFormPage.

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUsuarios } from '@/features/admin/hooks/useUsuarios';
import { UsuarioFiltersBar } from '@/features/admin/components/UsuarioFilters';
import { UsuarioTable } from '@/features/admin/components/UsuarioTable';
import type { UsuarioFilters } from '@/features/admin/types';

export function UsuariosListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<UsuarioFilters>({});
  const { data: usuarios = [], isLoading } = useUsuarios(filters);

  const handleEditar = (id: string) => {
    navigate(`/admin/usuarios/${id}/editar`);
  };

  const handleDetalle = (id: string) => {
    navigate(`/admin/usuarios/${id}`);
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
        <button
          type="button"
          onClick={() => navigate('/admin/usuarios/nuevo')}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          Nuevo usuario
        </button>
      </div>

      <div className="mb-4">
        <UsuarioFiltersBar filters={filters} onChange={setFilters} />
      </div>

      {isLoading ? (
        <p className="py-8 text-center text-sm text-gray-400">Cargando usuarios…</p>
      ) : (
        <UsuarioTable
          usuarios={usuarios}
          onEditar={handleEditar}
          onDetalle={handleDetalle}
        />
      )}
    </div>
  );
}
