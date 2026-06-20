import type { Equipo } from '@/features/equipos/types';

interface EquipoCardProps {
  equipo: Equipo;
}

export function EquipoCard({ equipo }: EquipoCardProps) {
  const desde = new Date(equipo.vigencia_desde).toLocaleDateString('es-AR');
  const hasta = new Date(equipo.vigencia_hasta).toLocaleDateString('es-AR');
  const activa = new Date(equipo.vigencia_hasta) >= new Date();

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md">
      <h3 className="text-lg font-semibold text-gray-900">
        {equipo.materia_nombre}
      </h3>
      <div className="mt-2 space-y-1 text-sm text-gray-600">
        <p>
          <span className="font-medium">Carrera:</span> {equipo.carrera_nombre}
        </p>
        <p>
          <span className="font-medium">Cohorte:</span> {equipo.cohorte_nombre}
        </p>
        <p>
          <span className="font-medium">Docentes:</span>{' '}
          {equipo.cantidad_docentes}
        </p>
      </div>
      <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-3">
        <span className="text-xs text-gray-500">
          {desde} — {hasta}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            activa
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-500'
          }`}
        >
          {activa ? 'Vigente' : 'Vencida'}
        </span>
      </div>
    </div>
  );
}
