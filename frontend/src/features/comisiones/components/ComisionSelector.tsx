import { useComisionContext } from '@/shared/comision/useComisionContext';
import { useMaterias, useCohortes } from '@/features/comisiones/hooks/useMaterias';

export function ComisionSelector() {
  const { materia_id, cohorte_id, setComision } = useComisionContext();
  const { data: materias, isLoading: materiasLoading } = useMaterias();
  const { data: cohortes, isLoading: cohortesLoading } = useCohortes(materia_id);

  return (
    <div className="flex gap-4 items-end">
      <div className="flex flex-col gap-1">
        <label htmlFor="materia-select" className="text-sm font-medium text-gray-700">
          Materia
        </label>
        {materiasLoading ? (
          <span className="text-sm text-gray-500">Cargando materias...</span>
        ) : (
          <select
            id="materia-select"
            aria-label="Materia"
            value={materia_id}
            onChange={(e) => setComision(e.target.value, '')}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Seleccioná una materia</option>
            {materias?.map((m) => (
              <option key={m.materia_id} value={m.materia_id}>
                {m.nombre}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="cohorte-select" className="text-sm font-medium text-gray-700">
          Cohorte
        </label>
        {cohortesLoading ? (
          <span className="text-sm text-gray-500">Cargando cohortes...</span>
        ) : (
          <select
            id="cohorte-select"
            aria-label="Cohorte"
            value={cohorte_id}
            onChange={(e) => setComision(materia_id, e.target.value)}
            disabled={!materia_id}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-100 disabled:text-gray-400"
          >
            <option value="">Seleccioná una cohorte</option>
            {cohortes?.map((c) => (
              <option key={c.cohorte_id} value={c.cohorte_id}>
                {c.etiqueta}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}
