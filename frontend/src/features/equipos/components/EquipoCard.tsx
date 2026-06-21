import type { MisEquipoItem } from '@/features/equipos/types';

interface EquipoCardProps {
  equipo: MisEquipoItem;
}

export function EquipoCard({ equipo }: EquipoCardProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md">
      <h3 className="text-sm font-semibold text-gray-900 font-mono">
        {equipo.materia_id ?? '—'}
      </h3>
      <div className="mt-2 space-y-1 text-sm text-gray-600">
        <p>
          <span className="font-medium">Carrera:</span>{' '}
          <span className="font-mono text-xs">{equipo.carrera_id ?? '—'}</span>
        </p>
        <p>
          <span className="font-medium">Cohorte:</span>{' '}
          <span className="font-mono text-xs">{equipo.cohorte_id ?? '—'}</span>
        </p>
        <p>
          <span className="font-medium">Asignaciones:</span>{' '}
          {equipo.asignaciones.length}
        </p>
      </div>
    </div>
  );
}
