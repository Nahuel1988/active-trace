// ── AccionesPorDiaChart ───────────────────────────────────────────────────────
// Gráfico de barras horizontales CSS mostrando acciones por día.
// D-05: inline style={{ width }} es permitido para anchos dinámicos en barras.

import type { AccionesPorDia } from '../types';

interface Props {
  data: AccionesPorDia[];
}

export function AccionesPorDiaChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-gray-500">Sin datos</p>
    );
  }

  const max = Math.max(...data.map((item) => item.cantidad), 1);

  return (
    <div className="space-y-2">
      {data.map((item) => (
        <div key={item.fecha} className="flex items-center gap-3 text-sm">
          <span className="w-24 shrink-0 text-gray-500">{item.fecha}</span>
          <div className="flex-1 rounded bg-gray-100">
            <div
              className="h-5 rounded bg-indigo-500"
              style={{ width: `${(item.cantidad / max) * 100}%` }}
            />
          </div>
          <span className="w-8 shrink-0 text-right text-gray-700">
            {item.cantidad}
          </span>
        </div>
      ))}
    </div>
  );
}
