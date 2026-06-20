import { Link } from 'react-router-dom';
import type { Tarea, TareaEstado } from '@/features/tareas/types';
import { useCambiarEstado } from '@/features/tareas/hooks/useTareaMutations';

const ESTADOS: { key: TareaEstado; label: string }[] = [
  { key: 'pendiente', label: 'Pendiente' },
  { key: 'en_progreso', label: 'En Progreso' },
  { key: 'completada', label: 'Completada' },
];

const COLUMN_COLOR: Record<TareaEstado, string> = {
  pendiente: 'border-t-yellow-400',
  en_progreso: 'border-t-blue-400',
  completada: 'border-t-green-400',
};

interface TareaKanbanProps {
  tareas: Tarea[];
  isLoading: boolean;
}

export function TareaKanban({ tareas, isLoading }: TareaKanbanProps) {
  const { mutate: cambiarEstado } = useCambiarEstado();

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
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      {ESTADOS.map(({ key, label }) => {
        const columnTareas = tareas.filter((t) => t.estado === key);
        return (
          <div
            key={key}
            className={`rounded-lg border border-t-4 border-gray-200 bg-gray-50 ${COLUMN_COLOR[key]}`}
          >
            <div className="border-b border-gray-200 px-4 py-3">
              <h3 className="font-semibold text-gray-900">
                {label}{' '}
                <span className="ml-1 text-sm font-normal text-gray-500">
                  ({columnTareas.length})
                </span>
              </h3>
            </div>
            <div className="space-y-3 p-3">
              {columnTareas.length === 0 ? (
                <p className="py-4 text-center text-sm text-gray-400">
                  Sin tareas
                </p>
              ) : (
                columnTareas.map((tarea) => (
                  <div
                    key={tarea.id}
                    className="rounded-md border border-gray-200 bg-white p-3 shadow-sm"
                  >
                    <Link
                      to={`/tareas/${tarea.id}`}
                      className="font-medium text-gray-900 hover:text-indigo-600"
                    >
                      {tarea.titulo}
                    </Link>
                    <p className="mt-1 text-xs text-gray-500">
                      {tarea.asignado_nombre ?? 'Sin asignar'}
                    </p>
                    {tarea.fecha_vencimiento && (
                      <p className="mt-0.5 text-xs text-gray-400">
                        Vence:{' '}
                        {new Date(tarea.fecha_vencimiento).toLocaleDateString(
                          'es-AR',
                        )}
                      </p>
                    )}
                    <div className="mt-2 flex items-center gap-2">
                      {ESTADOS.map((estado) => (
                        <button
                          key={estado.key}
                          type="button"
                          disabled={estado.key === tarea.estado}
                          onClick={() =>
                            cambiarEstado({
                              id: tarea.id,
                              estado: estado.key,
                            })
                          }
                          className="rounded px-2 py-0.5 text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {estado.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
