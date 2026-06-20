import type { PreviewItem } from '@/features/comunicaciones/types';

interface ComunicacionPreviewProps {
  items: PreviewItem[];
  onConfirm: () => void;
  onBack: () => void;
  isPending: boolean;
}

export function ComunicacionPreview({ items, onConfirm, onBack, isPending }: ComunicacionPreviewProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-700">Vista previa ({items.length} destinatarios)</h3>

      <div className="max-h-80 overflow-y-auto space-y-3">
        {items.map((item, i) => (
          <div key={i} className="rounded-md border border-gray-200 p-3">
            <p className="text-xs text-gray-500 mb-1">{item.destinatario}</p>
            <p className="text-sm font-medium text-gray-800">{item.asunto_render}</p>
            <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">{item.cuerpo_render}</p>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={onBack}
          disabled={isPending}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Volver
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isPending}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-300 disabled:text-gray-500"
        >
          {isPending ? 'Enviando...' : 'Enviar comunicaciones'}
        </button>
      </div>
    </div>
  );
}
