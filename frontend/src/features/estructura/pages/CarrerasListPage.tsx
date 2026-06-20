// ── CarrerasListPage ──────────────────────────────────────────────────────────
// Página de listado de carreras con tabla y formulario de creación inline.

import { CarreraTable } from '@/features/estructura/components/CarreraTable';

export default function CarrerasListPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Carreras</h1>
        <p className="mt-1 text-sm text-gray-500">
          Gestión de carreras de la institución.
        </p>
      </div>
      <CarreraTable />
    </div>
  );
}
