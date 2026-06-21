import { useMisEquipos } from '@/features/equipos/hooks/useEquipos';
import { EquipoCard } from '@/features/equipos/components/EquipoCard';
import type { MisEquipoItem } from '@/features/equipos/types';
import { Spinner } from '@/shared/components/Spinner';

export default function MisEquiposPage() {
  const { data: equipos, isLoading, isError, refetch } = useMisEquipos();

  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Mis Equipos</h1>
        <Spinner />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Mis Equipos</h1>
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-red-700">Error al cargar tus equipos</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  if (!equipos || equipos.length === 0) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Mis Equipos</h1>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-12 text-center">
          <p className="text-gray-500">No tenés equipos asignados</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Mis Equipos</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {equipos.map((equipo: MisEquipoItem) => (
          <EquipoCard
            key={`${equipo.materia_id}-${equipo.carrera_id}-${equipo.cohorte_id}`}
            equipo={equipo}
          />
        ))}
      </div>
    </div>
  );
}
