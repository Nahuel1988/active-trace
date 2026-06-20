import { useColoquios } from '../hooks/useColoquios';
import { Spinner } from '@/shared/components/Spinner';
import type { Coloquio } from '../types';

export function ColoquioTable() {
  const { data: coloquios, isLoading } = useColoquios();

  if (isLoading) return <Spinner className="py-8" />;

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Materia
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Instancia
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Tipo
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Convocados
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Reservas
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Cupos
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {(!coloquios || coloquios.length === 0) && (
            <tr>
              <td
                colSpan={7}
                className="px-4 py-8 text-center text-sm text-gray-500"
              >
                No hay coloquios registrados
              </td>
            </tr>
          )}
          {coloquios?.map((coloquio: Coloquio) => (
            <tr key={coloquio.id} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                {coloquio.materia}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {coloquio.instancia}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                {coloquio.tipo}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
                {coloquio.convocados}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
                {coloquio.reservas}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
                {coloquio.cupos}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                <button className="text-indigo-600 hover:text-indigo-900">
                  Editar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
