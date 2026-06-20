// ── AvisoTable ────────────────────────────────────────────────────────────────
// Tabla de avisos con badges de alcance/severidad, vigencia y acciones.

import { useActualizarAviso, useEliminarAviso } from '@/features/avisos/hooks/useAvisos';
import type { Aviso, Severidad } from '@/features/avisos/types';

interface AvisoTableProps {
  avisos: Aviso[];
  onEdit: (aviso: Aviso) => void;
}

const severidadBadge: Record<Severidad, string> = {
  Informativo: 'bg-blue-100 text-blue-800',
  Advertencia: 'bg-yellow-100 text-yellow-800',
  Critico: 'bg-red-100 text-red-800',
};

const alcanceLabels: Record<string, string> = {
  Global: 'Global',
  PorMateria: 'Materia',
  PorCohorte: 'Cohorte',
  PorRol: 'Rol',
};

function formatDateRange(inicio: string, fin: string): string {
  const opts: Intl.DateTimeFormatOptions = { day: '2-digit', month: '2-digit', year: 'numeric' };
  const from = new Date(inicio).toLocaleDateString('es-AR', opts);
  const to = new Date(fin).toLocaleDateString('es-AR', opts);
  return `${from} → ${to}`;
}

export function AvisoTable({ avisos, onEdit }: AvisoTableProps) {
  const actualizarAviso = useActualizarAviso();
  const eliminarAviso = useEliminarAviso();

  const handleToggleActivo = (aviso: Aviso) => {
    actualizarAviso.mutate({ id: aviso.id, data: { activo: !aviso.activo } });
  };

  const handleEliminar = (aviso: Aviso) => {
    if (window.confirm(`¿Eliminar el aviso "${aviso.titulo}"?`)) {
      eliminarAviso.mutate(aviso.id);
    }
  };

  if (avisos.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
        No hay avisos registrados.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Título</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Alcance</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Severidad</th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Vigencia</th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">Activo</th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {avisos.map((aviso) => (
            <tr key={aviso.id} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                {aviso.titulo}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                  {alcanceLabels[aviso.alcance] ?? aviso.alcance}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${severidadBadge[aviso.severidad as Severidad] ?? ''}`}>
                  {aviso.severidad}
                </span>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                {formatDateRange(aviso.inicio_en, aviso.fin_en)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-sm text-gray-600">
                <button
                  onClick={() => handleToggleActivo(aviso)}
                  className={`relative inline-flex h-5 w-9 cursor-pointer items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                    aviso.activo ? 'bg-indigo-600' : 'bg-gray-300'
                  }`}
                  role="switch"
                  aria-checked={aviso.activo}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      aviso.activo ? 'translate-x-[18px]' : 'translate-x-[2px]'
                    }`}
                  />
                </button>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                <button
                  onClick={() => onEdit(aviso)}
                  className="mr-2 font-medium text-indigo-600 hover:text-indigo-500"
                >
                  Editar
                </button>
                <button
                  onClick={() => handleEliminar(aviso)}
                  className="font-medium text-red-600 hover:text-red-500"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
