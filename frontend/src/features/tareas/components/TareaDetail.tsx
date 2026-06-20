import { useParams } from 'react-router-dom';
import { useTarea, useComentarios } from '@/features/tareas/hooks/useTareas';
import { useAgregarComentario, useCambiarEstado } from '@/features/tareas/hooks/useTareaMutations';
import { ComentarioList } from '@/features/tareas/components/ComentarioList';
import { ComentarioForm } from '@/features/tareas/components/ComentarioForm';
import { Spinner } from '@/shared/components/Spinner';
import type { TareaEstado } from '@/features/tareas/types';

const ESTADOS: { key: TareaEstado; label: string }[] = [
  { key: 'pendiente', label: 'Pendiente' },
  { key: 'en_progreso', label: 'En Progreso' },
  { key: 'completada', label: 'Completada' },
];

const ESTADO_COLOR: Record<TareaEstado, string> = {
  pendiente: 'bg-yellow-100 text-yellow-800',
  en_progreso: 'bg-blue-100 text-blue-800',
  completada: 'bg-green-100 text-green-800',
};

export function TareaDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: tarea, isLoading: tareaLoading } = useTarea(id!);
  const { data: comentarios, isLoading: comentariosLoading } = useComentarios(id!);
  const { mutate: cambiarEstado } = useCambiarEstado();
  const { mutate: agregarComentario, isPending: commentPending } = useAgregarComentario(id!);

  if (tareaLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner />
      </div>
    );
  }

  if (!tarea) {
    return (
      <p className="py-8 text-center text-gray-500">Tarea no encontrada.</p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{tarea.titulo}</h2>
            {tarea.asignado_nombre && (
              <p className="mt-1 text-sm text-gray-500">
                Asignado a: <span className="font-medium">{tarea.asignado_nombre}</span>
              </p>
            )}
          </div>
          <span
            className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${ESTADO_COLOR[tarea.estado]}`}
          >
            {ESTADOS.find((e) => e.key === tarea.estado)?.label}
          </span>
        </div>

        {tarea.descripcion && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-gray-700">Descripción</h3>
            <p className="mt-1 text-sm text-gray-600">{tarea.descripcion}</p>
          </div>
        )}

        <div className="mb-4 grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Prioridad:</span>{' '}
            <span className="font-medium text-gray-900">{tarea.prioridad}</span>
          </div>
          <div>
            <span className="text-gray-500">Creador:</span>{' '}
            <span className="font-medium text-gray-900">{tarea.creador_nombre}</span>
          </div>
          <div>
            <span className="text-gray-500">Vencimiento:</span>{' '}
            <span className="font-medium text-gray-900">
              {tarea.fecha_vencimiento
                ? new Date(tarea.fecha_vencimiento).toLocaleDateString('es-AR')
                : '—'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">Cambiar estado:</span>
          {ESTADOS.map((estado) => (
            <button
              key={estado.key}
              type="button"
              disabled={estado.key === tarea.estado}
              onClick={() => cambiarEstado({ id: tarea.id, estado: estado.key })}
              className="rounded-md border border-gray-300 px-3 py-1 text-xs font-medium hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {estado.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Comentarios</h3>
        <ComentarioList comentarios={comentarios ?? []} isLoading={comentariosLoading} />
        <div className="mt-4 border-t border-gray-200 pt-4">
          <ComentarioForm onEnviar={(c) => agregarComentario(c)} isPending={commentPending} />
        </div>
      </div>
    </div>
  );
}
