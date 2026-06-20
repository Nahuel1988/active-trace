import { useState } from 'react';
import { useTareas } from '@/features/tareas/hooks/useTareas';
import { TareaTable } from '@/features/tareas/components/TareaTable';
import { TareaKanban } from '@/features/tareas/components/TareaKanban';
import { TareaFormDialog } from '@/features/tareas/components/TareaFormDialog';

export default function TareasListPage() {
  const [showKanban, setShowKanban] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const { data: tareas, isLoading } = useTareas();

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Tareas</h1>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowKanban(!showKanban)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            {showKanban ? 'Vista Tabla' : 'Vista Kanban'}
          </button>
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            Nueva tarea
          </button>
        </div>
      </div>

      {showKanban ? (
        <TareaKanban tareas={tareas ?? []} isLoading={isLoading} />
      ) : (
        <TareaTable tareas={tareas ?? []} isLoading={isLoading} />
      )}

      <TareaFormDialog open={showForm} onClose={() => setShowForm(false)} />
    </div>
  );
}
