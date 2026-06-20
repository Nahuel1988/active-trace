import type { AtrasadoItem } from '@/features/atrasados/types';

interface AtrasadosTableProps {
  items: AtrasadoItem[];
  selected: string[];
  onSelectionChange: (selected: string[]) => void;
  canCommunicate: boolean;
  onCommunicate: () => void;
}

function groupByAlumno(items: AtrasadoItem[]): Map<string, AtrasadoItem[]> {
  const map = new Map<string, AtrasadoItem[]>();
  for (const item of items) {
    const existing = map.get(item.entrada_padron_id) ?? [];
    existing.push(item);
    map.set(item.entrada_padron_id, existing);
  }
  return map;
}

export function AtrasadosTable({ items, selected, onSelectionChange, canCommunicate, onCommunicate }: AtrasadosTableProps) {
  const grouped = groupByAlumno(items);
  const alumnos = Array.from(grouped.entries());

  if (alumnos.length === 0) {
    return (
      <div className="text-sm text-gray-500 py-4">
        No hay alumnos atrasados en esta comisión
      </div>
    );
  }

  const toggleSelect = (id: string) => {
    if (selected.includes(id)) {
      onSelectionChange(selected.filter((s) => s !== id));
    } else {
      onSelectionChange([...selected, id]);
    }
  };

  const toggleAll = () => {
    if (selected.length === alumnos.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(alumnos.map(([id]) => id));
    }
  };

  return (
    <div className="space-y-4">
      {canCommunicate && selected.length > 0 && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onCommunicate}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
          >
            Comunicar a seleccionados ({selected.length})
          </button>
        </div>
      )}

      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left">
              <input
                type="checkbox"
                checked={selected.length === alumnos.length && alumnos.length > 0}
                onChange={toggleAll}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                aria-label="Seleccionar todos"
              />
            </th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Apellido</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Motivos</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {alumnos.map(([id, alumnoItems]) => {
            const first = alumnoItems[0];
            return (
              <tr key={id} className="text-sm text-gray-700">
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={selected.includes(id)}
                    onChange={() => toggleSelect(id)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    aria-label={`Seleccionar ${first.alumno_apellido}, ${first.alumno_nombre}`}
                  />
                </td>
                <td className="px-4 py-2">{first.alumno_apellido}</td>
                <td className="px-4 py-2">{first.alumno_nombre}</td>
                <td className="px-4 py-2">{first.email ?? '-'}</td>
                <td className="px-4 py-2">
                  <div className="flex flex-wrap gap-1">
                    {alumnoItems.map((ai, idx) => (
                      <span
                        key={idx}
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          ai.clasificacion === 'missing'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}
                      >
                        {ai.clasificacion === 'missing' ? 'Missing' : 'Below threshold'}: {ai.actividad}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
