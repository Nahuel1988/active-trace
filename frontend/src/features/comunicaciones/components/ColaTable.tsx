import type { ComunicacionResponse } from '@/features/comunicaciones/types';

interface ColaTableProps {
  items: ComunicacionResponse[];
  onAprobar: (lote_id: string) => void;
  onCancelar: (lote_id: string) => void;
  isPending: boolean;
  canAprobar?: boolean;
}

const estadoColors: Record<string, string> = {
  pendiente: 'bg-yellow-100 text-yellow-800',
  enviado: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
  cancelado: 'bg-gray-100 text-gray-500',
};

export function ColaTable({ items, onAprobar, onCancelar, isPending, canAprobar = false }: ColaTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Destinatario</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Asunto</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Requiere aprobación</th>
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-3 py-2 text-sm text-gray-900">{item.destinatario}</td>
              <td className="px-3 py-2 text-sm text-gray-700 max-w-xs truncate">{item.asunto}</td>
              <td className="px-3 py-2">
                <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${estadoColors[item.estado] || 'bg-gray-100 text-gray-700'}`}>
                  {item.estado}
                </span>
              </td>
              <td className="px-3 py-2 text-sm text-gray-600">{item.requiere_aprobacion ? 'Sí' : 'No'}</td>
              <td className="px-3 py-2 text-right">
                {item.estado === 'pendiente' && canAprobar && (
                  <div className="flex gap-2 justify-end">
                    {item.requiere_aprobacion && (
                      <button
                        type="button"
                        onClick={() => onAprobar(item.lote_id)}
                        disabled={isPending}
                        className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-500 disabled:bg-gray-300"
                      >
                        Aprobar
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => onCancelar(item.lote_id)}
                      disabled={isPending}
                      className="rounded-md border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:text-gray-300"
                    >
                      Cancelar
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && (
        <p className="py-6 text-center text-sm text-gray-400">No hay comunicaciones en la cola.</p>
      )}
    </div>
  );
}
