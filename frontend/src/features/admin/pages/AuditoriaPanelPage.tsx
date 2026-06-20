// ── AuditoriaPanelPage ────────────────────────────────────────────────────────
// Panel de métricas de auditoría con filtros de rango de fechas.

import { useState } from 'react';
import { Spinner } from '@/shared/components/Spinner';
import { useMetricasAuditoria } from '../hooks/useAuditoria';
import { AccionesPorDiaChart } from '../components/AccionesPorDiaChart';
import { ComunicacionesPorDocente } from '../components/ComunicacionesPorDocente';
import { InteraccionesTable } from '../components/InteraccionesTable';
import { UltimasAccionesTable } from '../components/UltimasAccionesTable';
import type { AuditFilters } from '../types';

export function AuditoriaPanelPage() {
  const [filters, setFilters] = useState<AuditFilters>({});
  const { data: metricas, isLoading } = useMetricasAuditoria(filters);

  const handleDesde = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, desde: e.target.value || undefined }));
  };

  const handleHasta = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, hasta: e.target.value || undefined }));
  };

  return (
    <div className="space-y-8 p-6">
      <div className="flex flex-wrap items-end gap-4">
        <h1 className="text-xl font-semibold text-gray-900">
          Panel de Auditoría
        </h1>
        <div className="flex flex-wrap gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-500">Desde</label>
            <input
              type="date"
              value={filters.desde ?? ''}
              onChange={handleDesde}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-gray-500">Hasta</label>
            <input
              type="date"
              value={filters.hasta ?? ''}
              onChange={handleHasta}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {isLoading && <Spinner className="py-12" />}

      {metricas && (
        <>
          <section className="space-y-3">
            <h2 className="text-base font-semibold text-gray-800">
              Acciones por día
            </h2>
            <AccionesPorDiaChart data={metricas.acciones_por_dia} />
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-semibold text-gray-800">
              Comunicaciones por docente
            </h2>
            <ComunicacionesPorDocente
              data={metricas.comunicaciones_por_docente}
            />
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-semibold text-gray-800">
              Interacciones docente × materia
            </h2>
            <InteraccionesTable data={metricas.interacciones} />
          </section>

          <section className="space-y-3">
            <h2 className="text-base font-semibold text-gray-800">
              Últimas acciones
            </h2>
            <UltimasAccionesTable data={metricas.ultimas_acciones} />
          </section>
        </>
      )}
    </div>
  );
}
