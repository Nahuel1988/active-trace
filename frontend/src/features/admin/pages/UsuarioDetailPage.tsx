// ── UsuarioDetailPage ──────────────────────────────────────────────────────
// Detail page for a single Usuario, including PII fields.
// SECURITY (D-04): PII is displayed only here via UsuarioDetail.
// No console.log. No PII forwarded to child components other than
// UsuarioDetail itself.

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useUsuario } from '@/features/admin/hooks/useUsuarios';
import { useEliminarUsuario } from '@/features/admin/hooks/useUsuarioMutations';
import { UsuarioDetail } from '@/features/admin/components/UsuarioDetail';

export function UsuarioDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [confirmBaja, setConfirmBaja] = useState(false);

  const { data: usuario, isLoading, isError } = useUsuario(id ?? '');
  const { mutate: eliminar, isPending: isEliminating } = useEliminarUsuario();

  const handleBaja = () => {
    if (!id) return;
    eliminar(id, {
      onSuccess: () => navigate('/admin/usuarios'),
    });
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <p className="text-sm text-gray-400">Cargando usuario…</p>
      </div>
    );
  }

  if (isError || !usuario) {
    return (
      <div className="p-6">
        <p className="text-sm text-red-600">No se pudo cargar el usuario.</p>
        <button
          type="button"
          onClick={() => navigate('/admin/usuarios')}
          className="mt-4 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          ← Volver a la lista
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl">
      <div className="mb-6 flex items-center gap-4">
        <button
          type="button"
          onClick={() => navigate('/admin/usuarios')}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          ← Volver
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          {usuario.nombre} {usuario.apellidos}
        </h1>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm mb-6">
        <UsuarioDetail usuario={usuario} />
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => navigate(`/admin/usuarios/${usuario.id}/editar`)}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          Editar
        </button>
        <button
          type="button"
          onClick={() => setConfirmBaja(true)}
          className="rounded-md border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 shadow-sm hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-400"
        >
          Dar de baja
        </button>
      </div>

      {confirmBaja && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Confirmar baja de usuario"
        >
          <div className="w-full max-w-sm rounded-lg bg-white shadow-xl p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-2">
              ¿Dar de baja a este usuario?
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              El usuario{' '}
              <strong>
                {usuario.nombre} {usuario.apellidos}
              </strong>{' '}
              quedará inactivo. Esta acción puede revertirse.
            </p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setConfirmBaja(false)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleBaja}
                disabled={isEliminating}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isEliminating ? 'Procesando…' : 'Confirmar baja'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
