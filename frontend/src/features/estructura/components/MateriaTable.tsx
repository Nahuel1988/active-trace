// ── MateriaTable ──────────────────────────────────────────────────────────────
// Tabla de materias con badge de clave_plus y soporte para edición.

import type { Materia } from '@/features/estructura/types';

interface MateriaTableProps {
  materias: Materia[];
  onEditar?: (id: string) => void;
}

export function MateriaTable({ materias, onEditar }: MateriaTableProps) {
  if (materias.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No hay materias registradas
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Nombre
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Clave Plus
            </th>
            {onEditar && (
              <th className="px-4 py-3 text-left font-medium text-gray-500">
                Acciones
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {materias.map((m) => (
            <tr key={m.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-900">{m.nombre}</td>
              <td className="px-4 py-3">
                <span className="inline-flex rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                  {m.clave_plus}
                </span>
              </td>
              {onEditar && (
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => onEditar(m.id)}
                    className="text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                  >
                    Editar
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
