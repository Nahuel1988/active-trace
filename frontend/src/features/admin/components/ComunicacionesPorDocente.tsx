// ── ComunicacionesPorDocente ──────────────────────────────────────────────────
// Tabla de comunicaciones agrupadas por docente con totales por estado.

import type { ComunicacionPorDocente } from '../types';

interface Props {
  data: ComunicacionPorDocente[];
}

export function ComunicacionesPorDocente({ data }: Props) {
  if (data.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-gray-500">
        Sin datos de comunicaciones
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
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Total
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Enviadas
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Fallidas
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Canceladas
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.map((row) => (
            <tr key={row.usuario_id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-900">
                {row.nombre} {row.apellidos}
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {row.total}
              </td>
              <td className="px-4 py-3 text-right text-green-700">
                {row.enviadas}
              </td>
              <td className="px-4 py-3 text-right text-red-700">
                {row.fallidas}
              </td>
              <td className="px-4 py-3 text-right text-gray-500">
                {row.canceladas}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
