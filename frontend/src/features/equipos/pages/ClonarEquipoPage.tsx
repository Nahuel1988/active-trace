import { ClonarEquipoForm } from '@/features/equipos/components/ClonarEquipoForm';

export default function ClonarEquipoPage() {
  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">
        Clonar equipo
      </h1>
      <p className="mb-6 text-sm text-gray-500">
        Cloná las asignaciones de un equipo existente a una nueva carrera y/o
        cohorte. Las asignaciones vigentes se copiarán al destino.
      </p>
      <ClonarEquipoForm />
    </div>
  );
}
