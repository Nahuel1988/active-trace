import type { Comentario } from '@/features/tareas/types';

interface ComentarioListProps {
  comentarios: Comentario[];
  isLoading: boolean;
}

export function ComentarioList({ comentarios, isLoading }: ComentarioListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-6">
        <svg
          className="h-6 w-6 animate-spin text-indigo-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  if (comentarios.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-gray-400">
        Sin comentarios aún.
      </p>
    );
  }

  return (
    <div className="relative ml-4 border-l-2 border-gray-200 pl-6">
      {comentarios.map((comentario) => (
        <div key={comentario.id} className="relative mb-6">
          <div className="absolute -left-9 flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-600">
            {comentario.autor_nombre.charAt(0).toUpperCase()}
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">
                {comentario.autor_nombre}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(comentario.created_at).toLocaleString('es-AR')}
              </span>
            </div>
            <p className="text-sm text-gray-600">{comentario.contenido}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
