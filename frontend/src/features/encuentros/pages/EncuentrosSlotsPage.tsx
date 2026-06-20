import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { SlotTable } from '@/features/encuentros/components/SlotTable';
import { EncuentroFormDialog } from '@/features/encuentros/components/EncuentroFormDialog';
import { useSlots } from '@/features/encuentros/hooks/useEncuentros';
import { useCrearSlot, useEliminarSlot } from '@/features/encuentros/hooks/useEncuentroMutations';
import * as encuentrosApi from '@/features/encuentros/services/encuentrosApi';
import type { SlotCreateRequest } from '@/features/encuentros/types';
import { Spinner } from '@/shared/components/Spinner';

export default function EncuentrosSlotsPage() {
  const navigate = useNavigate();
  const [materiaFilter, setMateriaFilter] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [htmlModal, setHtmlModal] = useState<string | null>(null);

  const { data: slots, isLoading } = useSlots(materiaFilter || undefined);
  const crearSlot = useCrearSlot();
  const eliminarSlot = useEliminarSlot();

  const handleCreate = useCallback(
    (data: SlotCreateRequest) => {
      crearSlot.mutate(data, {
        onSuccess: () => {
          setDialogOpen(false);
        },
      });
    },
    [crearSlot],
  );

  const handleDelete = useCallback(
    (id: string) => {
      if (window.confirm('¿Eliminar este slot? Se eliminarán todas sus instancias.')) {
        eliminarSlot.mutate(id);
      }
    },
    [eliminarSlot],
  );

  const handleExportHTML = useCallback(async (id: string) => {
    try {
      const html = await encuentrosApi.exportarHTML(id);
      setHtmlModal(html);
    } catch {
      alert('Error al exportar HTML');
    }
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Encuentros</h1>
        <button
          type="button"
          onClick={() => setDialogOpen(true)}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          Nuevo slot
        </button>
      </div>

      {/* Filter */}
      <div className="max-w-xs">
        <label htmlFor="materia-filter" className="block text-sm font-medium text-gray-700">
          Filtrar por materia
        </label>
        <input
          id="materia-filter"
          type="text"
          value={materiaFilter}
          onChange={(e) => setMateriaFilter(e.target.value)}
          placeholder="ID de materia"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner />
        </div>
      ) : (
        <SlotTable
          slots={slots ?? []}
          onViewDetail={(id) => navigate(`/encuentros/slots/${id}`)}
          onDelete={handleDelete}
          onExportHTML={handleExportHTML}
        />
      )}

      {/* Create dialog */}
      <EncuentroFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleCreate}
        isSubmitting={crearSlot.isPending}
      />

      {/* HTML export modal */}
      {htmlModal !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">HTML para LMS</h2>
              <button
                type="button"
                onClick={() => setHtmlModal(null)}
                className="rounded-md p-1 text-gray-400 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <textarea
              readOnly
              value={htmlModal}
              rows={12}
              className="w-full rounded-md border border-gray-300 bg-gray-50 p-3 font-mono text-xs"
            />
            <div className="mt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(htmlModal);
                    alert('HTML copiado al portapapeles');
                  } catch {
                    alert('No se pudo copiar');
                  }
                }}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
              >
                Copiar
              </button>
              <button
                type="button"
                onClick={() => setHtmlModal(null)}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
