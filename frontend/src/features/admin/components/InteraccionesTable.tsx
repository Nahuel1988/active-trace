// ── InteraccionesTable ────────────────────────────────────────────────────────
// Tabla de interacciones docente × materia con columna de acción y cantidad.

import type { InteraccionDocenteMateria } from '../types';

interface Props {
  data: InteraccionDocenteMateria[];
}

export function InteraccionesTable({ data }: Props) {
  if (data.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-gray-500">
        Sin datos de interacciones
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Docente
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Materia
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Acción
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Cantidad
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.map((row, idx) => (
            <tr
              key={`${row.usuario_id}-${row.materia_id ?? 'none'}-${row.accion}-${idx}`}
              className="hover:bg-gray-50"
            >
              <td className="px-4 py-3 text-gray-900">
                {row.nombre} {row.apellidos}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {row.materia_nombre ?? '—'}
              </td>
              <td className="px-4 py-3 text-gray-700">{row.accion}</td>
              <td className="px-4 py-3 text-right text-gray-900">
                {row.cantidad}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
