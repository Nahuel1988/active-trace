import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useComisionContext } from '@/shared/comision/useComisionContext';
import { usePermission } from '@/shared/hooks/usePermission';
import { useComunicacionPreview, useEnviarComunicacion } from '@/features/comunicaciones/hooks/useComunicacionMutations';
import { useColaComunicaciones } from '@/features/comunicaciones/hooks/useColaComunicaciones';
import { ComunicacionPreview } from '@/features/comunicaciones/components/ComunicacionPreview';
import { ColaTable } from '@/features/comunicaciones/components/ColaTable';

export default function ComunicacionesQueuePage() {
  const { materia_id, cohorte_id } = useComisionContext();
  const canAprobar = usePermission('comunicacion:aprobar');
  const [searchParams] = useSearchParams();
  const alumnosParam = searchParams.get('alumnos') || '';
  const alumnos = alumnosParam ? alumnosParam.split(',').filter(Boolean) : [];

  const [asunto, setAsunto] = useState('');
  const [cuerpo, setCuerpo] = useState('');
  const [showPreview, setShowPreview] = useState(false);

  const previewMut = useComunicacionPreview();
  const enviarMut = useEnviarComunicacion();
  const colaQuery = useColaComunicaciones(materia_id);

  if (!materia_id || !cohorte_id) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">
        Seleccioná una comisión para gestionar comunicaciones
      </div>
    );
  }

  const handlePreview = () => {
    previewMut.mutate({
      asunto_template: asunto,
      cuerpo_template: cuerpo,
      destinatarios: alumnos.map((id) => ({ email: `${id}@placeholder`, variables: {} })),
    });
    setShowPreview(true);
  };

  const handleEnviar = () => {
    enviarMut.mutate({
      asunto_template: asunto,
      cuerpo_template: cuerpo,
      destinatarios: alumnos.map((id) => ({ email: `${id}@placeholder`, variables: {} })),
      materia_id,
      requiere_aprobacion: canAprobar,
    });
  };

  const handleAprobar = (lote_id: string) => {
    // TODO: call aprobarLote when backend endpoint available
  };

  const handleCancelar = (lote_id: string) => {
    // TODO: call cancelarLote when backend endpoint available
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Comunicaciones</h1>

      {alumnos.length > 0 && (
        <p className="text-sm text-indigo-600 font-medium">
          Destinatarios ({alumnos.length} desde atrasados)
        </p>
      )}

      <section className="space-y-4">
        <div>
          <label htmlFor="asunto" className="block text-sm font-medium text-gray-700 mb-1">
            Asunto
          </label>
          <textarea
            id="asunto"
            value={asunto}
            onChange={(e) => setAsunto(e.target.value)}
            rows={2}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            placeholder="Usá {'{variable}'} para templates"
          />
        </div>
        <div>
          <label htmlFor="cuerpo" className="block text-sm font-medium text-gray-700 mb-1">
            Cuerpo del mensaje
          </label>
          <textarea
            id="cuerpo"
            value={cuerpo}
            onChange={(e) => setCuerpo(e.target.value)}
            rows={6}
            className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            placeholder="Usá {'{variable}'} para templates"
          />
        </div>
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handlePreview}
            disabled={!asunto || !cuerpo || alumnos.length === 0}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-300 disabled:text-gray-500"
          >
            Previsualizar
          </button>
        </div>
      </section>

      {showPreview && previewMut.data && (
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Vista previa</h2>
          <ComunicacionPreview
            items={previewMut.data.items}
            onConfirm={handleEnviar}
            onBack={() => setShowPreview(false)}
            isPending={enviarMut.isPending}
          />
        </section>
      )}

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Cola de envío</h2>
        {colaQuery.isLoading ? (
          <span className="text-sm text-gray-500">Cargando cola...</span>
        ) : (
          <ColaTable
            items={colaQuery.data ?? []}
            onAprobar={handleAprobar}
            onCancelar={handleCancelar}
            isPending={false}
            canAprobar={canAprobar}
          />
        )}
      </section>
    </div>
  );
}
