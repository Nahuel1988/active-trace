import { useState } from 'react';
import { useComisionContext } from '@/shared/comision/useComisionContext';
import {
  useCalificacionesPreview,
  useCalificacionesCommit,
  useUmbral,
} from '@/features/calificaciones/hooks/useCalificacionesMutations';
import { ActividadesSelector } from '@/features/calificaciones/components/ActividadesSelector';
import { UmbralForm } from '@/features/calificaciones/components/UmbralForm';

export default function ImportCalificacionesPage() {
  const { materia_id } = useComisionContext();
  const previewMutation = useCalificacionesPreview();
  const commitMutation = useCalificacionesCommit();
  const umbral = useUmbral(materia_id);
  const [importId, setImportId] = useState<string | null>(null);
  const [selectedActividades, setSelectedActividades] = useState<string[]>([]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !materia_id) return;
    previewMutation.mutate(
      { materia_id, file },
      {
        onSuccess: (data) => {
          setImportId(data.import_id);
          setSelectedActividades(data.actividades.map((a) => a.id));
        },
      },
    );
  };

  const handleCommit = () => {
    if (!materia_id || !importId || selectedActividades.length === 0) return;
    commitMutation.mutate({ materia_id, import_id: importId, actividades_seleccionadas: selectedActividades });
  };

  const handleSaveUmbral = (value: number) => {
    umbral.mutation.mutate(value);
  };

  if (!materia_id) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">
        Seleccioná una comisión para importar calificaciones
      </div>
    );
  }

  if (commitMutation.isSuccess) {
    return (
      <div className="space-y-4">
        <div className="rounded-md bg-green-50 border border-green-200 p-4">
          <p className="text-sm font-medium text-green-800">Importación completada</p>
          <p className="text-sm text-green-600 mt-1">
            {commitMutation.data.total_procesados} alumnos procesados
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            commitMutation.reset();
            setImportId(null);
          }}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          Importar otro archivo
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Importar calificaciones</h1>

      <div className="rounded-md bg-white border border-gray-200 p-4 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Configuración de umbral</h2>
        {umbral.isLoading ? (
          <span className="text-sm text-gray-500">Cargando umbral...</span>
        ) : (
          <UmbralForm
            umbralPorcentaje={umbral.data?.umbral_porcentaje ?? 60}
            isPending={umbral.mutation.isPending}
            onSave={handleSaveUmbral}
          />
        )}
      </div>

      <div className="rounded-md bg-white border border-gray-200 p-4 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Archivo de calificaciones</h2>
        {!importId && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Archivo de calificaciones
            </label>
            <input
              type="file"
              accept=".xlsx,.csv"
              onChange={handleFileUpload}
              disabled={previewMutation.isPending}
              aria-label="Archivo de calificaciones"
              className="block w-full text-sm text-gray-700 file:mr-4 file:rounded-md file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100"
            />
            {previewMutation.isPending && (
              <p className="text-sm text-gray-500 mt-2">Procesando archivo...</p>
            )}
            {previewMutation.isError && (
              <p className="text-sm text-red-600 mt-2">
                Error: {(previewMutation.error as Error)?.message ?? 'Error al procesar archivo'}
              </p>
            )}
          </div>
        )}

        {importId && previewMutation.data && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              {previewMutation.data.total_alumnos} alumnos, {previewMutation.data.actividades.length} actividades detectadas
            </p>

            {previewMutation.data.errores.length > 0 && (
              <div className="rounded-md bg-red-50 border border-red-200 p-3">
                <p className="text-sm font-medium text-red-800">Errores en el archivo</p>
                <ul className="mt-1 list-disc list-inside text-sm text-red-600">
                  {previewMutation.data.errores.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            <ActividadesSelector
              actividades={previewMutation.data.actividades}
              selected={selectedActividades}
              onChange={setSelectedActividades}
            />

            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleCommit}
                disabled={commitMutation.isPending || selectedActividades.length === 0}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
              >
                {commitMutation.isPending ? 'Importando...' : 'Confirmar importación'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
