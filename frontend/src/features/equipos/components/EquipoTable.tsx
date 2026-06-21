import { useNavigate } from 'react-router-dom';
import type { Equipo } from '@/features/equipos/types';

interface EquipoTableProps {
  equipos: Equipo[];
}

export function EquipoTable({ equipos }: EquipoTableProps) {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Materia
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Carrera
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Cohorte
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-500">
              Docentes
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-500">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {equipos.map((equipo) => {
            const rowKey = `${equipo.materia_id}-${equipo.carrera_id}-${equipo.cohorte_id}`;
            return (
              <tr key={rowKey} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {equipo.materia_nombre ?? equipo.materia_id ?? '—'}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {equipo.carrera_nombre ?? equipo.carrera_id ?? '—'}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {equipo.cohorte_nombre ?? equipo.cohorte_id ?? '—'}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {equipo.conteo}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => navigate('/equipos/asignacion-masiva')}
                      className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
                    >
                      Asignar
                    </button>
                    <button
                      type="button"
                      onClick={() => navigate('/equipos/clonar')}
                      className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
                    >
                      Clonar
                    </button>
                    <button
                      type="button"
                      className="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100"
                    >
                      Exportar
                    </button>
                    <button
                      type="button"
                      className="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100"
                    >
                      Vigencia
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
