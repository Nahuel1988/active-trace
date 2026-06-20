// ── CohorteTable ──────────────────────────────────────────────────────────────
// Tabla de cohortes con acciones de edición y eliminación.

import type { Cohorte } from '@/features/estructura/types';

interface CohorteTableProps {
  cohortes: Cohorte[];
  onEditar?: (id: string) => void;
  onEliminar?: (id: string) => void;
}

export function CohorteTable({ cohortes, onEditar, onEliminar }: CohorteTableProps) {
  if (cohortes.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No hay cohortes registradas
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Etiqueta
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Carrera
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Fecha inicio
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Fecha fin
            </th>
            {(onEditar ?? onEliminar) && (
              <th className="px-4 py-3 text-left font-medium text-gray-500">
                Acciones
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {cohortes.map((c) => (
            <tr key={c.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-900">{c.etiqueta}</td>
              <td className="px-4 py-3 text-gray-900">{c.carrera_id}</td>
              <td className="px-4 py-3 text-gray-600">{c.fecha_inicio}</td>
              <td className="px-4 py-3 text-gray-600">
                {c.fecha_fin ?? 'Sin fecha fin'}
              </td>
              {(onEditar ?? onEliminar) && (
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    {onEditar && (
                      <button
                        type="button"
                        onClick={() => onEditar(c.id)}
                        className="text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                      >
                        Editar
                      </button>
                    )}
                    {onEliminar && (
                      <button
                        type="button"
                        onClick={() => onEliminar(c.id)}
                        className="text-red-600 hover:text-red-800 text-xs font-medium"
                      >
                        Eliminar
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
