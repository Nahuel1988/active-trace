import type { LiquidacionItem, HistorialFilters } from '@/features/finanzas/types';

interface Props {
  items: LiquidacionItem[];
  filters: HistorialFilters;
  onFilterChange: (f: HistorialFilters) => void;
}

export function HistorialTable({ items, filters, onFilterChange }: Props) {
  return (
    <div>
      <div className="flex gap-3 mb-4">
        <input
          type="month"
          value={filters.periodo ?? ''}
          onChange={(e) => onFilterChange({ ...filters, periodo: e.target.value || undefined })}
          placeholder="Período"
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
          aria-label="Filtrar por período"
        />
        <input
          type="text"
          value={filters.usuario_id ?? ''}
          onChange={(e) => onFilterChange({ ...filters, usuario_id: e.target.value || undefined })}
          placeholder="ID docente"
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
          aria-label="Filtrar por docente"
        />
      </div>
      {items.length === 0 ? (
        <p className="text-center text-gray-400 py-8">Sin liquidaciones cerradas</p>
      ) : (
        <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Período</th>
              <th className="px-4 py-2 text-left">Docente</th>
              <th className="px-4 py-2 text-left">Rol</th>
              <th className="px-4 py-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((liq) => (
              <tr key={liq.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{liq.periodo}</td>
                <td className="px-4 py-2">{liq.usuario_id}</td>
                <td className="px-4 py-2">{liq.rol}</td>
                <td className="px-4 py-2 text-right">${parseFloat(liq.total).toLocaleString('es-AR', { minimumFractionDigits: 2 })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
