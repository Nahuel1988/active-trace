// ── UsuarioTable ───────────────────────────────────────────────────────────
// List table for Usuarios ABM.
// SECURITY (D-04): PII columns (dni, cuil, cbu, alias_cbu) MUST NOT appear
// here. This component only receives the `Usuario` type (no PII).

import type { Usuario } from '@/features/admin/types';

interface UsuarioTableProps {
  usuarios: Usuario[];
  onEditar?: (id: string) => void;
  onEliminar?: (id: string) => void;
  onDetalle?: (id: string) => void;
}

function FacturadorBadge({ value }: { value: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        value ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
      }`}
    >
      {value ? 'Sí' : 'No'}
    </span>
  );
}

function ActivoBadge({ value }: { value: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        value ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}
    >
      {value ? 'Activo' : 'Baja'}
    </span>
  );
}

export function UsuarioTable({
  usuarios,
  onEditar,
  onEliminar,
  onDetalle,
}: UsuarioTableProps) {
  if (usuarios.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No hay usuarios registrados.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Nombre y apellidos
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Legajo
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Email
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Regional
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Facturador
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Estado
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {usuarios.map((u) => (
            <tr key={u.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-900">
                {u.nombre} {u.apellidos}
              </td>
              <td className="px-4 py-3 text-gray-700">{u.legajo}</td>
              <td className="px-4 py-3 text-gray-700">{u.email}</td>
              <td className="px-4 py-3 text-gray-700">{u.regional}</td>
              <td className="px-4 py-3">
                <FacturadorBadge value={u.facturador} />
              </td>
              <td className="px-4 py-3">
                <ActivoBadge value={u.is_active} />
              </td>
              <td className="px-4 py-3 text-right space-x-2 whitespace-nowrap">
                {onDetalle && (
                  <button
                    type="button"
                    onClick={() => onDetalle(u.id)}
                    className="text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                  >
                    Ver
                  </button>
                )}
                {onEditar && (
                  <button
                    type="button"
                    onClick={() => onEditar(u.id)}
                    className="text-gray-600 hover:text-gray-900 text-xs font-medium"
                  >
                    Editar
                  </button>
                )}
                {onEliminar && (
                  <button
                    type="button"
                    onClick={() => onEliminar(u.id)}
                    className="text-red-600 hover:text-red-800 text-xs font-medium"
                  >
                    Dar de baja
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
