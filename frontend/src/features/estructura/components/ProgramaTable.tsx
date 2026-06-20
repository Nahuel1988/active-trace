// ── ProgramaTable ─────────────────────────────────────────────────────────────
// Tabla de programas con indicador de archivo y acciones.

import { useProgramas } from '@/features/estructura/hooks/useEstructura';
import { Spinner } from '@/shared/components/Spinner';

interface Props {
  materiaId?: string;
  carreraId?: string;
  cohorteId?: string;
}

export function ProgramaTable({ materiaId, carreraId, cohorteId }: Props) {
  const { data: programas, isLoading } = useProgramas({
    materia_id: materiaId,
    carrera_id: carreraId,
    cohorte_id: cohorteId,
  });

  if (isLoading) return <Spinner className="py-8" />;

  return (
    <div className="space-y-4">
      {programas && programas.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Título
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Archivo
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Cargado
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {programas.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{p.titulo}</td>
                  <td className="px-4 py-3">
                    {p.referencia_archivo ? (
                      <a
                        href={p.referencia_archivo}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:text-indigo-500"
                      >
                        Ver archivo
                      </a>
                    ) : (
                      <span className="text-gray-400">Sin archivo</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(p.cargado_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-gray-500">
          No hay programas registrados.
        </p>
      )}
    </div>
  );
}
