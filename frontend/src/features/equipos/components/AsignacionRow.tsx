import { useState } from 'react';
import type { Asignacion } from '@/features/equipos/types';
import { useEliminarAsignacion } from '@/features/equipos/hooks/useEquipoMutations';

interface AsignacionRowProps {
  asignacion: Asignacion;
}

export function AsignacionRow({ asignacion }: AsignacionRowProps) {
  const [confirming, setConfirming] = useState(false);
  const eliminarMutation = useEliminarAsignacion();

  const handleDelete = () => {
    eliminarMutation.mutate(asignacion.id, {
      onSuccess: () => setConfirming(false),
    });
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3 text-sm text-gray-900">
        {asignacion.apellido}, {asignacion.nombre}
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">{asignacion.email}</td>
      <td className="px-4 py-3 text-sm text-gray-600">{asignacion.rol}</td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {asignacion.responsable ? (
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
            Sí
          </span>
        ) : (
          <span className="text-gray-400">No</span>
        )}
      </td>
      <td className="px-4 py-3 text-right">
        {confirming ? (
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setConfirming(false)}
              className="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={eliminarMutation.isPending}
              className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
            >
              {eliminarMutation.isPending ? 'Eliminando...' : 'Confirmar'}
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
          >
            Eliminar
          </button>
        )}
      </td>
    </tr>
  );
}
