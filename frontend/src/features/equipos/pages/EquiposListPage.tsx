import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useEquipos } from '@/features/equipos/hooks/useEquipos';
import { EquipoTable } from '@/features/equipos/components/EquipoTable';
import { VigenciaForm } from '@/features/equipos/components/VigenciaForm';
import { exportarEquipo } from '@/features/equipos/services/equiposApi';
import { Spinner } from '@/shared/components/Spinner';
import type { EquipoFilters } from '@/features/equipos/types';

export default function EquiposListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<EquipoFilters>({});
  const [showVigencia, setShowVigencia] = useState(false);
  const { data: equipos, isLoading, isError, refetch } = useEquipos(filters);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Equipos docentes</h1>
        </div>
        <Spinner />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">
          Equipos docentes
        </h1>
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-red-700">Error al cargar equipos</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Equipos docentes</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => navigate('/equipos/asignacion-masiva')}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Asignación masiva
          </button>
          <button
            type="button"
            onClick={() => navigate('/equipos/clonar')}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Clonar
          </button>
          <button
            type="button"
            onClick={() => setShowVigencia(!showVigencia)}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Ajustar vigencia
          </button>
          <button
            type="button"
            onClick={() => {
              exportarEquipo(filters).catch(() => {});
            }}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Exportar CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={filters.materia_id ?? ''}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, materia_id: e.target.value || undefined }))
          }
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todas las materias</option>
          <option value="1">Matemática</option>
          <option value="2">Lengua</option>
        </select>
        <select
          value={filters.carrera_id ?? ''}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, carrera_id: e.target.value || undefined }))
          }
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todas las carreras</option>
          <option value="1">Ingeniería</option>
          <option value="2">Licenciatura</option>
        </select>
        <select
          value={filters.cohorte_id ?? ''}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, cohorte_id: e.target.value || undefined }))
          }
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todos los cohortes</option>
          <option value="1">2025</option>
          <option value="2">2026</option>
        </select>
      </div>

      {/* Vigencia Form */}
      {showVigencia && equipos && equipos.length > 0 && (
        <div className="mb-4">
          <VigenciaForm
            equipoIds={equipos.map((e) => e.id)}
            onSuccess={() => setShowVigencia(false)}
          />
        </div>
      )}

      {/* Table */}
      {equipos && equipos.length > 0 ? (
        <EquipoTable equipos={equipos} />
      ) : (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-12 text-center">
          <p className="mb-3 text-gray-500">No hay equipos cargados</p>
          <button
            type="button"
            onClick={() => navigate('/equipos/asignacion-masiva')}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Ir a asignación masiva
          </button>
        </div>
      )}
    </div>
  );
}
