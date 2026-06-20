import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/services/api';
import { GuardiaTable } from '../components/GuardiaTable';
import { GuardiaFormDialog } from '../components/GuardiaFormDialog';
import {
  useGuardias,
  useCrearGuardia,
  useCambiarEstadoGuardia,
} from '../hooks/useGuardias';
import type { CatalogoItem, GuardiaFiltros } from '../types';

function useCatalogo(endpoint: string) {
  return useQuery<CatalogoItem[]>({
    queryKey: ['catalogo', endpoint],
    queryFn: () => api.get(endpoint).then((r) => r.data),
    staleTime: 5 * 60_000,
  });
}

export default function GuardiasListPage() {
  const [filters, setFilters] = useState<GuardiaFiltros>({});
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: guardias = [], isLoading: guardiasLoading } =
    useGuardias(filters);
  const { data: materias = [] } = useCatalogo('/api/materias');
  const { data: carreras = [] } = useCatalogo('/api/v1/estructura/carreras');
  const { data: cohortes = [] } = useCatalogo('/api/cohortes');

  const { mutateAsync: crearGuardia } = useCrearGuardia();
  const { mutate: cambiarEstado } = useCambiarEstadoGuardia();

  const catalogsLoading =
    materias.length === 0 && carreras.length === 0 && cohortes.length === 0;

  const handleCreate = useCallback(
    async (data: Parameters<typeof crearGuardia>[0]) => {
      await crearGuardia(data);
      setDialogOpen(false);
    },
    [crearGuardia],
  );

  const handleExport = useCallback(async () => {
    const { exportGuardiasCSV } = await import('../services/guardiasApi');
    const blob = await exportGuardiasCSV(filters);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'guardias.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [filters]);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Guardias</h1>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleExport}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Exportar CSV
          </button>
          <button
            type="button"
            onClick={() => setDialogOpen(true)}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Nueva guardia
          </button>
        </div>
      </div>

      <GuardiaTable
        guardias={guardias}
        isLoading={guardiasLoading}
        filters={filters}
        onFilterChange={setFilters}
        onCambiarEstado={(id, estado) => cambiarEstado({ id, estado })}
        carreras={carreras}
        materias={materias}
        cohortes={cohortes}
      />

      <GuardiaFormDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleCreate}
        materias={materias}
        carreras={carreras}
        cohortes={cohortes}
        isLoadingCatalogs={catalogsLoading}
      />
    </div>
  );
}
