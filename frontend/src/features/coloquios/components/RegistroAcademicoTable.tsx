import { useState } from 'react';
import { useRegistroAcademico } from '../hooks/useColoquios';
import { Spinner } from '@/shared/components/Spinner';
import type { RegistroAcademico } from '../types';

export function RegistroAcademicoTable() {
  const [materiaId, setMateriaId] = useState('');
  const [cohorteId, setCohorteId] = useState('');

  const filters: { materia_id?: string; cohorte_id?: string } = {};
  if (materiaId) filters.materia_id = materiaId;
  if (cohorteId) filters.cohorte_id = cohorteId;

  const { data: registros, isLoading } = useRegistroAcademico(
    Object.keys(filters).length ? filters : undefined,
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 rounded-lg border border-gray-200 bg-white p-4">
        <div>
          <label className="block text-xs font-medium text-gray-500">
            Materia
          </label>
          <input
            value={materiaId}
            onChange={(e) => setMateriaId(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500">
            Cohorte
          </label>
          <input
            value={cohorteId}
            onChange={(e) => setCohorteId(e.target.value)}
            className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>
      </div>

      {isLoading ? (
        <Spinner className="py-8" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Alumno
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Materia
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Nota
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Fecha
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Estado
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {(!registros || registros.length === 0) && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-8 text-center text-sm text-gray-500"
                  >
                    No hay registros académicos
                  </td>
                </tr>
              )}
              {registros?.map((registro: RegistroAcademico) => (
                <tr key={registro.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                    {registro.alumno}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {registro.materia}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-900">
                    {registro.nota}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {registro.fecha}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {registro.estado}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
