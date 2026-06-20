import { Spinner } from '@/shared/components/Spinner';
import { GuardiaEstadoBadge } from './GuardiaEstadoBadge';
import type {
  Guardia,
  GuardiaFiltros,
  EstadoGuardia,
  CatalogoItem,
} from '../types';

interface GuardiaTableProps {
  guardias: Guardia[];
  isLoading: boolean;
  filters: GuardiaFiltros;
  onFilterChange: (filters: GuardiaFiltros) => void;
  onCambiarEstado: (id: string, estado: EstadoGuardia) => void;
  carreras: CatalogoItem[];
  materias: CatalogoItem[];
  cohortes: CatalogoItem[];
}

export function GuardiaTable({
  guardias,
  isLoading,
  filters,
  onFilterChange,
  onCambiarEstado,
  carreras,
  materias,
  cohortes,
}: GuardiaTableProps) {
  return (
    <div>
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <select
          value={filters.materia_id ?? ''}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              materia_id: e.target.value || undefined,
            })
          }
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todas las materias</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>
              {m.nombre}
            </option>
          ))}
        </select>

        <select
          value={filters.carrera_id ?? ''}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              carrera_id: e.target.value || undefined,
            })
          }
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todas las carreras</option>
          {carreras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>

        <select
          value={filters.cohorte_id ?? ''}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              cohorte_id: e.target.value || undefined,
            })
          }
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todos los cohortes</option>
          {cohortes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>

        <select
          value={filters.estado ?? ''}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              estado: (e.target.value || undefined) as
                | EstadoGuardia
                | undefined,
            })
          }
          className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todos los estados</option>
          <option value="pendiente">Pendiente</option>
          <option value="realizada">Realizada</option>
          <option value="cancelada">Cancelada</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : guardias.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 py-12 text-center">
          <p className="text-sm text-gray-500">No hay guardias registradas</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Materia
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Carrera
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Cohorte
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Día
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Horario
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Estado
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {guardias.map((g) => (
                <tr key={g.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                    {g.materia.nombre}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                    {g.carrera.nombre}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                    {g.cohorte.nombre}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                    {g.dia.charAt(0).toUpperCase() + g.dia.slice(1)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                    {g.horario}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm">
                    <GuardiaEstadoBadge
                      estado={g.estado}
                      onChange={(nuevo) => onCambiarEstado(g.id, nuevo)}
                    />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                    {g.comentarios && (
                      <span
                        className="cursor-help text-xs text-gray-400 underline decoration-dotted"
                        title={g.comentarios}
                      >
                        Comentario
                      </span>
                    )}
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
