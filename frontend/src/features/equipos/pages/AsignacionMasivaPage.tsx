import { AsignacionMasivaForm } from '@/features/equipos/components/AsignacionMasivaForm';

export default function AsignacionMasivaPage() {
  return (
    <div className="p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">
        Asignación masiva de docentes
      </h1>
      <p className="mb-6 text-sm text-gray-500">
        Asigná docentes a un equipo en tres pasos: seleccioná los datos del
        equipo, configurá los detalles de la asignación y el sistema mostrará el
        resultado.
      </p>
      <AsignacionMasivaForm />
    </div>
  );
}
