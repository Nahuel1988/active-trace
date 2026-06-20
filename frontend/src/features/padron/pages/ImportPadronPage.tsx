import { useState } from 'react';
import { useComisionContext } from '@/shared/comision/useComisionContext';
import { usePadronPreview, usePadronCommit } from '@/features/padron/hooks/usePadronMutations';
import { PadronPreviewTable } from '@/features/padron/components/PadronPreviewTable';
import { ConfirmDestructiveDialog } from '@/features/padron/components/ConfirmDestructiveDialog';

export default function ImportPadronPage() {
  const { materia_id } = useComisionContext();
  const previewMutation = usePadronPreview();
  const commitMutation = usePadronCommit();
  const [importId, setImportId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !materia_id) return;
    previewMutation.mutate(
      { materia_id, file },
      {
        onSuccess: (data) => {
          setImportId(data.import_id);
        },
      },
    );
  };

  const handleConfirm = () => {
    if (!materia_id || !importId) return;
    commitMutation.mutate({ materia_id, import_id: importId });
    setShowConfirm(false);
  };

  if (!materia_id) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">
        Seleccioná una comisión para importar el padrón
      </div>
    );
  }

  if (commitMutation.isSuccess) {
    return (
      <div className="space-y-4">
        <div className="rounded-md bg-green-50 border border-green-200 p-4">
          <p className="text-sm font-medium text-green-800">Importación completada</p>
          <p className="text-sm text-green-600 mt-1">
            {commitMutation.data.total_importados} importados, {commitMutation.data.total_reemplazados} reemplazados
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
      <h1 className="text-2xl font-bold text-gray-900">Importar padrón de alumnos</h1>

      {!importId && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Archivo de padrón
          </label>
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={handleFileUpload}
            disabled={previewMutation.isPending}
            aria-label="Archivo de padrón"
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
        <>
          <PadronPreviewTable
            alumnos={previewMutation.data.alumnos}
            errores={previewMutation.data.errores}
            totalDetectados={previewMutation.data.total_detectados}
            onConfirm={() => setShowConfirm(true)}
          />
          <ConfirmDestructiveDialog
            open={showConfirm}
            title="Reemplazar padrón"
            description="Esto reemplazará el padrón actual de la materia. Los alumnos existentes que no estén en el nuevo archivo serán eliminados."
            onConfirm={handleConfirm}
            onCancel={() => setShowConfirm(false)}
          />
        </>
      )}

      {commitMutation.isPending && (
        <p className="text-sm text-gray-500">Guardando padrón...</p>
      )}
    </div>
  );
}
