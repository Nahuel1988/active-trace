import type { KpisLiquidacion } from '@/features/finanzas/types';

interface Props {
  kpis: KpisLiquidacion;
}

function formatMonto(monto: string): string {
  return `$${parseFloat(monto).toLocaleString('es-AR', { minimumFractionDigits: 2 })}`;
}

export function KpisCabecera({ kpis }: Props) {
  return (
    <div className="flex gap-6 mb-6">
      <div className="rounded-lg border border-gray-200 bg-white p-4 flex-1">
        <p className="text-sm text-gray-500">Total sin factura</p>
        <p className="text-2xl font-bold text-gray-900">{formatMonto(kpis.total_sin_factura)}</p>
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-4 flex-1">
        <p className="text-sm text-gray-500">Total con factura</p>
        <p className="text-2xl font-bold text-gray-900">{formatMonto(kpis.total_con_factura)}</p>
      </div>
    </div>
  );
}
