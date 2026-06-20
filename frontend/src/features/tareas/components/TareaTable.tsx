import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Tarea, TareaEstado } from '@/features/tareas/types';
import { useCambiarEstado } from '@/features/tareas/hooks/useTareaMutations';

const ESTADOS: TareaEstado[] = ['pendiente', 'en_progreso', 'completada'];

const ESTADO_LABEL: Record<TareaEstado, string> = {
  pendiente: 'Pendiente',
  en_progreso: 'En Progreso',
  completada: 'Completada',
};

const ESTADO_COLOR: Record<TareaEstado, string> = {
  pendiente: 'bg-yellow-100 text-yellow-800',
  en_progreso: 'bg-blue-100 text-blue-800',
  completada: 'bg-green-100 text-green-800',
};

interface TareaTableProps {
  tareas: Tarea[];
  isLoading: boolean;
}

export function TareaTable({ tareas, isLoading }: TareaTableProps) {
  const [estadoFilter, setEstadoFilter] = useState<string>('');
  const { mutate: cambiarEstado } = useCambiarEstado();

  const filtered = estadoFilter
    ? tareas.filter((t) => t.estado === estadoFilter)
    : tareas;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <svg
          className="h-8 w-8 animate-spin text-indigo-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">
          Filtrar por estado:
        </label>
        <select
          value={estadoFilter}
          onChange={(e) => setEstadoFilter(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todos</option>
          {ESTADOS.map((estado) => (
            <option key={estado} value={estado}>
              {ESTADO_LABEL[estado]}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <p className="py-8 text-center text-gray-500">
          No se encontraron tareas.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Título
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Asignado
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Estado
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Prioridad
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Vencimiento
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {filtered.map((tarea) => (
                <tr key={tarea.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    <Link
                      to={`/tareas/${tarea.id}`}
                      className="hover:text-indigo-600"
                    >
                      {tarea.titulo}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {tarea.asignado_nombre ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${ESTADO_COLOR[tarea.estado]}`}
                    >
                      {ESTADO_LABEL[tarea.estado]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{tarea.prioridad}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {tarea.fecha_vencimiento
                      ? new Date(tarea.fecha_vencimiento).toLocaleDateString(
                          'es-AR',
                        )
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {tarea.estado !== 'completada' && (
                        <select
                          value={tarea.estado}
                          onChange={(e) =>
                            cambiarEstado({
                              id: tarea.id,
                              estado: e.target.value,
                            })
                          }
                          className="rounded border border-gray-300 px-2 py-1 text-xs focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        >
                          {ESTADOS.map((estado) => (
                            <option key={estado} value={estado}>
                              {ESTADO_LABEL[estado]}
                            </option>
                          ))}
                        </select>
                      )}
                      <Link
                        to={`/tareas/${tarea.id}`}
                        className="text-xs font-medium text-indigo-600 hover:text-indigo-500"
                      >
                        Ver
                      </Link>
                    </div>
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
