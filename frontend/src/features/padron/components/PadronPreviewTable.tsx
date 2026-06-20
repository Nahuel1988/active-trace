import type { AlumnoDTO } from '@/features/padron/types';

interface PadronPreviewTableProps {
  alumnos: AlumnoDTO[];
  errores: string[];
  totalDetectados: number;
  onConfirm: () => void;
}

export function PadronPreviewTable({ alumnos, errores, totalDetectados, onConfirm }: PadronPreviewTableProps) {
  const hasErrors = errores.length > 0;

  if (alumnos.length === 0 && !hasErrors) {
    return (
      <div className="text-sm text-gray-500 py-4">
        No se detectaron alumnos en el archivo
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">{totalDetectados} alumnos detectados</p>

      {hasErrors && (
        <div className="rounded-md bg-red-50 border border-red-200 p-3">
          <p className="text-sm font-medium text-red-800">Errores detectados</p>
          <ul className="mt-1 list-disc list-inside text-sm text-red-600">
            {errores.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Apellido</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Grupo</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {alumnos.map((alumno, i) => (
            <tr key={i} className="text-sm text-gray-700">
              <td className="px-4 py-2">{alumno.apellido}</td>
              <td className="px-4 py-2">{alumno.nombre}</td>
              <td className="px-4 py-2">{alumno.email}</td>
              <td className="px-4 py-2">{alumno.grupo ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={onConfirm}
          disabled={hasErrors}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
        >
          {hasErrors ? 'Errores detectados' : 'Confirmar importación'}
        </button>
      </div>
    </div>
  );
}
