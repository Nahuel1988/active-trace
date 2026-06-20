// ── FechaTable ────────────────────────────────────────────────────────────────
// Tabla de fechas académicas con acciones de editar/crear.

import { useState } from 'react';
import { useFechas } from '@/features/estructura/hooks/useEstructura';
import { FechaFormDialog } from '@/features/estructura/components/FechaFormDialog';
import { Spinner } from '@/shared/components/Spinner';
import type { FechaAcademica } from '@/features/estructura/types';

export function FechaTable() {
  const { data: fechas, isLoading } = useFechas();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editFecha, setEditFecha] = useState<FechaAcademica | undefined>();

  const handleEdit = (f: FechaAcademica) => {
    setEditFecha(f);
    setDialogOpen(true);
  };

  const handleCreate = () => {
    setEditFecha(undefined);
    setDialogOpen(true);
  };

  const handleClose = () => {
    setDialogOpen(false);
    setEditFecha(undefined);
  };

  if (isLoading) return <Spinner className="py-8" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Fechas académicas
        </h2>
        <button
          type="button"
          onClick={handleCreate}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Nueva fecha
        </button>
      </div>

      {fechas && fechas.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Título
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  N°
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Período
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Fecha
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {fechas.map((f) => (
                <tr key={f.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{f.titulo}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        f.tipo === 'Parcial'
                          ? 'bg-blue-100 text-blue-700'
                          : f.tipo === 'TP'
                            ? 'bg-purple-100 text-purple-700'
                            : f.tipo === 'Coloquio'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {f.tipo}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{f.numero}</td>
                  <td className="px-4 py-3 text-gray-500">{f.periodo}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(f.fecha).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => handleEdit(f)}
                      className="text-indigo-600 hover:text-indigo-500"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-gray-500">
          No hay fechas académicas registradas.
        </p>
      )}

      <FechaFormDialog
        isOpen={dialogOpen}
        onClose={handleClose}
        editFecha={editFecha}
      />
    </div>
  );
}
