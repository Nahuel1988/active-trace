import type { SegmentoLiquidacion } from '@/features/finanzas/types';

interface Props {
  titulo: string;
  segmento: SegmentoLiquidacion;
  onCerrar?: (id: string) => void;
  canCerrar?: boolean;
}

export function SegmentoTable({ titulo, segmento, onCerrar, canCerrar }: Props) {
  if (segmento.liquidaciones.length === 0) {
    return null;
  }

  return (
    <section className="mb-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">{titulo}</h3>
      <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left">Docente</th>
            <th className="px-4 py-2 text-left">Rol</th>
            <th className="px-4 py-2 text-right">Monto</th>
            <th className="px-4 py-2 text-left">Estado</th>
            {canCerrar && <th className="px-4 py-2" />}
          </tr>
        </thead>
        <tbody>
          {segmento.liquidaciones.map((liq) => (
            <tr key={liq.id} className="border-t border-gray-100">
              <td className="px-4 py-2">{liq.usuario_id}</td>
              <td className="px-4 py-2">{liq.rol}</td>
              <td className="px-4 py-2 text-right">${parseFloat(liq.total).toLocaleString('es-AR', { minimumFractionDigits: 2 })}</td>
              <td className="px-4 py-2">{liq.estado}</td>
              {canCerrar && (
                <td className="px-4 py-2">
                  {liq.estado === 'Abierta' && (
                    <button
                      onClick={() => onCerrar?.(liq.id)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Cerrar
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-gray-50">
          <tr>
            <td colSpan={canCerrar ? 4 : 3} className="px-4 py-2 text-right font-semibold">Subtotal</td>
            <td className="px-4 py-2 text-right font-semibold">
              ${parseFloat(segmento.subtotal).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
            </td>
            {canCerrar && <td />}
          </tr>
        </tfoot>
      </table>
    </section>
  );
}
