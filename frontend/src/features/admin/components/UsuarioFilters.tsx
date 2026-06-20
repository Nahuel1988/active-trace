// ── UsuarioFilters ─────────────────────────────────────────────────────────
// Filter bar for Usuarios list: free-text search, regional select,
// facturador select.

import type { UsuarioFilters } from '@/features/admin/types';

const REGIONALES = ['GBA', 'Capital', 'Interior', 'Online'];

interface UsuarioFiltersProps {
  filters: UsuarioFilters;
  onChange: (filters: UsuarioFilters) => void;
}

export function UsuarioFiltersBar({ filters, onChange }: UsuarioFiltersProps) {
  const handleQ = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...filters, q: e.target.value || undefined });
  };

  const handleRegional = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, regional: e.target.value || undefined });
  };

  const handleFacturador = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value;
    onChange({
      ...filters,
      facturador: v === '' ? undefined : v === 'true',
    });
  };

  return (
    <div className="flex flex-wrap gap-3 items-end">
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Buscar
        </label>
        <input
          type="text"
          value={filters.q ?? ''}
          onChange={handleQ}
          placeholder="Nombre, legajo, email…"
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-56"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Regional
        </label>
        <select
          aria-label="Regional"
          value={filters.regional ?? ''}
          onChange={handleRegional}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todas</option>
          {REGIONALES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Facturador
        </label>
        <select
          aria-label="Facturador"
          value={
            filters.facturador === undefined ? '' : String(filters.facturador)
          }
          onChange={handleFacturador}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todos</option>
          <option value="true">Sí</option>
          <option value="false">No</option>
        </select>
      </div>
    </div>
  );
}
