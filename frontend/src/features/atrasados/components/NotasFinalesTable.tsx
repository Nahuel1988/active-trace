import type { NotaFinalAlumno } from '@/features/atrasados/types';

interface NotasFinalesTableProps {
  items: NotaFinalAlumno[];
}

export function NotasFinalesTable({ items }: NotasFinalesTableProps) {
  if (items.length === 0) {
    return (
      <div className="text-sm text-gray-500 py-4">
        No hay notas finales registradas
      </div>
    );
  }

  return (
    <table className="min-w-full divide-y divide-gray-200">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Apellido</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nota final</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Condición</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-200">
        {items.map((item) => (
          <tr key={item.entrada_padron_id} className="text-sm text-gray-700">
            <td className="px-4 py-2">{item.alumno_apellido}</td>
            <td className="px-4 py-2">{item.alumno_nombre}</td>
            <td className="px-4 py-2">{item.nota_final}</td>
            <td className="px-4 py-2">{item.condicion}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
