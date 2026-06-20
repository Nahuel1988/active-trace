// ── AuditoriaLogPage ──────────────────────────────────────────────────────────
// Página de log de auditoría con filtros y tabla paginada por el servidor.

import { useState } from 'react';
import { Spinner } from '@/shared/components/Spinner';
import { useAuditLog } from '../hooks/useAuditoria';
import { AuditLogFilters } from '../components/AuditLogFilters';
import { AuditLogTable } from '../components/AuditLogTable';
import type { AuditLogFilters as AuditLogFiltersType } from '../types';

export function AuditoriaLogPage() {
  const [filters, setFilters] = useState<AuditLogFiltersType>({});
  const { data: items, isLoading } = useAuditLog(filters);

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-xl font-semibold text-gray-900">Log de Auditoría</h1>

      <AuditLogFilters filters={filters} onChange={setFilters} />

      {isLoading && <Spinner className="py-12" />}

      {!isLoading && (
        <AuditLogTable items={items ?? []} />
      )}
    </div>
  );
}
