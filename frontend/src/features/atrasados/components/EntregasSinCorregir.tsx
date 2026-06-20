import type { EntregaPendiente } from '@/features/atrasados/types';
import { exportEntregasPendientes } from '@/features/atrasados/services/atrasadosApi';

interface EntregasSinCorregirProps {
  items: EntregaPendiente[];
  todasCorregidas: boolean;
  materiaId: string;
  cohorteId: string;
}

export function EntregasSinCorregir({ items, todasCorregidas, materiaId, cohorteId }: EntregasSinCorregirProps) {
  if (todasCorregidas) {
    return (
      <div className="text-sm text-gray-500 py-4">
        Todas las entregas están corregidas
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => exportEntregasPendientes(materiaId, cohorteId)}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          Exportar
        </button>
      </div>

      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Alumno</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actividad</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Materia</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {items.map((item, i) => (
            <tr key={i} className="text-sm text-gray-700">
              <td className="px-4 py-2">{item.alumno}</td>
              <td className="px-4 py-2">{item.actividad}</td>
              <td className="px-4 py-2">{item.fecha_submission}</td>
              <td className="px-4 py-2">{item.materia}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
