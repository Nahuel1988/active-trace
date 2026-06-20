import type { SlotEncuentro } from '../types';

interface SlotTableProps {
  slots: SlotEncuentro[];
  onViewDetail: (id: string) => void;
  onDelete: (id: string) => void;
  onExportHTML: (id: string) => void;
}

const DIAS: Record<string, string> = {
  lunes: 'Lunes',
  martes: 'Martes',
  miércoles: 'Miércoles',
  jueves: 'Jueves',
  viernes: 'Viernes',
  sábado: 'Sábado',
  domingo: 'Domingo',
};

export function SlotTable({ slots, onViewDetail, onDelete, onExportHTML }: SlotTableProps) {
  if (slots.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
        <p className="text-gray-500">No hay encuentros programados</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Materia</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Título</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Día</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Hora</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Tipo</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Instancias</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {slots.map((slot) => (
            <tr key={slot.id} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                {slot.materia_id.slice(0, 8)}...
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                {slot.titulo}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                {DIAS[slot.dia_semana] ?? slot.dia_semana}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                {slot.hora}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                    slot.modo === 'recurrente'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-purple-100 text-purple-700'
                  }`}
                >
                  {slot.modo === 'recurrente' ? 'Recurrente' : 'Único'}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                {slot.instancias?.length ?? '-'}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                <button
                  type="button"
                  onClick={() => onViewDetail(slot.id)}
                  className="mr-2 text-indigo-600 hover:text-indigo-800"
                >
                  Ver
                </button>
                <button
                  type="button"
                  onClick={() => onExportHTML(slot.id)}
                  className="mr-2 text-green-600 hover:text-green-800"
                >
                  HTML
                </button>
                <button
                  type="button"
                  onClick={() => onDelete(slot.id)}
                  className="text-red-600 hover:text-red-800"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
