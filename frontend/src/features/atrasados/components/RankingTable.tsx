import type { RankingItem } from '@/features/atrasados/types';

interface RankingTableProps {
  items: RankingItem[];
}

export function RankingTable({ items }: RankingTableProps) {
  const filtered = items.filter((i) => i.actividades_aprobadas > 0)
    .sort((a, b) => b.actividades_aprobadas - a.actividades_aprobadas);

  if (filtered.length === 0) {
    return (
      <div className="text-sm text-gray-500 py-4">
        No hay datos de ranking para esta comisión
      </div>
    );
  }

  return (
    <table className="min-w-full divide-y divide-gray-200">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">#</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Apellido</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Aprobadas</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">%</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-200">
        {filtered.map((item, idx) => (
          <tr key={item.entrada_padron_id} className="text-sm text-gray-700">
            <td className="px-4 py-2">{idx + 1}</td>
            <td className="px-4 py-2">{item.alumno_apellido}</td>
            <td className="px-4 py-2">{item.alumno_nombre}</td>
            <td className="px-4 py-2">{item.actividades_aprobadas}</td>
            <td className="px-4 py-2">{item.total_actividades}</td>
            <td className="px-4 py-2">{item.porcentaje_aprobacion}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
