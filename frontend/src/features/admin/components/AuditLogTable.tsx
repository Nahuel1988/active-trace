// ── AuditLogTable ─────────────────────────────────────────────────────────────
// Tabla de solo lectura del log de auditoría (paginación delegada al servidor).

import type { AuditLogItem } from '../types';

interface Props {
  items: AuditLogItem[];
}

export function AuditLogTable({ items }: Props) {
  if (items.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-gray-500">
        No hay registros de auditoría
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
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              IP
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              User Agent
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.map((item) => (
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
              <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-500">
                {item.ip}
              </td>
              <td
                className="max-w-xs truncate px-4 py-3 text-xs text-gray-400"
                title={item.user_agent}
              >
                {item.user_agent}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
