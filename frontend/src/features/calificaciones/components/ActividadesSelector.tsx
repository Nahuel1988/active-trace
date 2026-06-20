import type { ActividadDTO } from '@/features/calificaciones/types';

interface ActividadesSelectorProps {
  actividades: ActividadDTO[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

export function ActividadesSelector({ actividades, selected, onChange }: ActividadesSelectorProps) {
  const allSelected = selected.length === actividades.length && actividades.length > 0;

  const toggleSelectAll = () => {
    if (allSelected) {
      onChange([]);
    } else {
      onChange(actividades.map((a) => a.id));
    }
  };

  const toggleActividad = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">
          {selected.length} de {actividades.length} seleccionadas
        </span>
        <button
          type="button"
          onClick={toggleSelectAll}
          className="text-sm text-indigo-600 hover:text-indigo-500"
        >
          {allSelected ? 'Deseleccionar todas' : 'Seleccionar todas'}
        </button>
      </div>
      <div className="max-h-60 overflow-y-auto rounded-md border border-gray-200 divide-y divide-gray-200">
        {actividades.map((act) => (
          <label
            key={act.id}
            className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer"
          >
            <input
              type="checkbox"
              checked={selected.includes(act.id)}
              onChange={() => toggleActividad(act.id)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              aria-label={act.nombre}
            />
            <span className="text-sm text-gray-700 flex-1">{act.nombre}</span>
            <span className="text-xs text-gray-400">{act.escala}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
