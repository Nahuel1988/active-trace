import { useState } from 'react';
import { useAgenda } from '../hooks/useColoquios';
import { Spinner } from '@/shared/components/Spinner';
import type { AgendaItem } from '../types';

export function AgendaTable() {
  const [materiaId, setMateriaId] = useState('');
  const [cohorteId, setCohorteId] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  const filters: {
    materia_id?: string;
    cohorte_id?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  } = {};
  if (materiaId) filters.materia_id = materiaId;
  if (cohorteId) filters.cohorte_id = cohorteId;
  if (fechaDesde) filters.fecha_desde = fechaDesde;
  if (fechaHasta) filters.fecha_hasta = fechaHasta;

  const { data: agenda, isLoading } = useAgenda(
    Object.keys(filters).length ? filters : undefined,
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 rounded-lg border border-gray-200 bg-white p-4">
        <div>
          <label className="block text-xs font-medium text-gray-500">
            Materia
          </label>
          <input
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500">
            Cohorte
          </label>
          <input
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500">
            Fecha desde
          </label>
          <input
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500">
            Fecha hasta
          </label>
          <input
            type="date"
            value={fechaHasta}
            onChange={(e) => setFechaHasta(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
      </div>

      {isLoading ? (
        <Spinner className="py-8" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Alumno
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Materia
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Fecha y hora
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {(!agenda || agenda.length === 0) && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-8 text-center text-sm text-gray-500"
                  >
                    No hay agenda disponible
                  </td>
                </tr>
              )}
              {agenda?.map((item: AgendaItem) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                    {item.alumno}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {item.materia}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {item.fecha_hora}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {item.tipo}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {item.estado}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
