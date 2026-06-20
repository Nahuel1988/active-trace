// ── AuditLogFilters ───────────────────────────────────────────────────────────
// Barra de filtros controlada para el log de auditoría.

import type { AuditLogFilters } from '../types';

interface Props {
  filters: AuditLogFilters;
  onChange: (filters: AuditLogFilters) => void;
}

export function AuditLogFilters({ filters, onChange }: Props) {
  const handleChange =
    (field: keyof AuditLogFilters) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({ ...filters, [field]: e.target.value || undefined });
    };

  return (
    <div className="flex flex-wrap gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <div className="flex flex-col gap-1">
        <label htmlFor="alf-desde" className="text-xs font-medium text-gray-500">Desde</label>
        <input
          id="alf-desde"
          type="date"
          value={filters.desde ?? ''}
          onChange={handleChange('desde')}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="alf-hasta" className="text-xs font-medium text-gray-500">Hasta</label>
        <input
          id="alf-hasta"
          type="date"
          value={filters.hasta ?? ''}
          onChange={handleChange('hasta')}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="alf-materia" className="text-xs font-medium text-gray-500">Materia ID</label>
        <input
          id="alf-materia"
          type="text"
          placeholder="UUID de materia"
          value={filters.materia_id ?? ''}
          onChange={handleChange('materia_id')}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="alf-accion" className="text-xs font-medium text-gray-500">Acción</label>
        <input
          id="alf-accion"
          type="text"
          placeholder="ej. CREATE_ALUMNO"
          value={filters.accion ?? ''}
          onChange={handleChange('accion')}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>
    </div>
  );
}
