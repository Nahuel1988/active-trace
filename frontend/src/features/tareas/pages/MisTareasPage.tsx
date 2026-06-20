import { Link } from 'react-router-dom';
import { useMisTareas } from '@/features/tareas/hooks/useTareas';
import { TareaTable } from '@/features/tareas/components/TareaTable';

export default function MisTareasPage() {
  const { data: tareas, isLoading } = useMisTareas();

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Mis Tareas</h1>
        <Link
          to="/tareas"
          className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          Ver todas las tareas
        </Link>
      </div>

      {!isLoading && tareas && tareas.length === 0 ? (
        <p className="py-8 text-center text-gray-500">
          No tenés tareas pendientes.
        </p>
      ) : (
        <TareaTable tareas={tareas ?? []} isLoading={isLoading} />
      )}
    </div>
  );
}
