import { AbonarFacturaButton } from '@/features/finanzas/components/AbonarFacturaButton';
import type { Factura, EstadoFactura } from '@/features/finanzas/types';

interface Props {
  facturas: Factura[];
  onAbonar?: (id: string) => void;
  canAbonar?: boolean;
}

function EstadoBadge({ estado }: { estado: EstadoFactura }) {
  if (estado === 'Abonada') {
    return (
      <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
        Abonada
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
      Pendiente
    </span>
  );
}

export function FacturaTable({ facturas, canAbonar = false }: Props) {
  if (facturas.length === 0) {
    return (
      <p className="py-8 text-center text-gray-400">No hay facturas registradas</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Usuario</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Período</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Detalle</th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
            <th className="px-4 py-2 text-right font-medium text-gray-600">Tamaño (KB)</th>
            {canAbonar && (
              <th className="px-4 py-2 text-center font-medium text-gray-600">Acciones</th>
            )}
          </tr>
        </thead>
        <tbody>
          {facturas.map((factura) => (
            <tr key={factura.id} className="border-t border-gray-100 hover:bg-gray-50">
              <td className="px-4 py-2 text-gray-700">{factura.usuario_id}</td>
              <td className="px-4 py-2 text-gray-700">{factura.periodo}</td>
              <td className="px-4 py-2 text-gray-700 max-w-xs truncate">{factura.detalle}</td>
              <td className="px-4 py-2">
                <EstadoBadge estado={factura.estado} />
              </td>
              <td className="px-4 py-2 text-right text-gray-700">{factura.tamano_kb}</td>
              {canAbonar && (
                <td className="px-4 py-2 text-center">
                  {factura.estado === 'Pendiente' && (
                    <AbonarFacturaButton facturaId={factura.id} />
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
