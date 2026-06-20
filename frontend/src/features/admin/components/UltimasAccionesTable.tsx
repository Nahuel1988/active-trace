// ── UltimasAccionesTable ──────────────────────────────────────────────────────
// Tabla de últimas N acciones en orden descendente (ya ordenadas por la API).

import type { AuditLogItem } from '../types';

interface Props {
  data: AuditLogItem[];
}

export function UltimasAccionesTable({ data }: Props) {
  if (data.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-gray-500">
        Sin acciones recientes
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Fecha / Hora
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Actor
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Materia
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Acción
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Filas
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-gray-500">
                {item.fecha_hora}
              </td>
              <td className="px-4 py-3 text-gray-900">{item.actor_nombre}</td>
              <td className="px-4 py-3 text-gray-700">
                {item.materia_nombre ?? '—'}
              </td>
              <td className="px-4 py-3 text-gray-700">{item.accion}</td>
              <td className="px-4 py-3 text-right text-gray-900">
                {item.filas_afectadas}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
