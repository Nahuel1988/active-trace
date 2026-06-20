import { useState } from 'react';
import { useHistorial } from '@/features/finanzas/hooks/useLiquidaciones';
import { HistorialTable } from '@/features/finanzas/components/HistorialTable';
import type { HistorialFilters } from '@/features/finanzas/types';

export function HistorialLiquidacionesPage() {
  const [filters, setFilters] = useState<HistorialFilters>({});
  const { data, isLoading } = useHistorial(filters);

  const items = (data as { items?: NonNullable<typeof data>[] })?.items ?? [];

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-gray-900 mb-6">Historial de liquidaciones</h1>
      {isLoading ? (
        <p className="text-gray-400">Cargando...</p>
      ) : (
        <HistorialTable
          items={items as Parameters<typeof HistorialTable>[0]['items']}
          filters={filters}
          onFilterChange={setFilters}
        />
      )}
    </div>
  );
}
