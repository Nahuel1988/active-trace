// ── FechasAcademicasPage ──────────────────────────────────────────────────────
// Página de fechas académicas con toggle entre tabla y calendario.

import { useState } from 'react';
import { FechaTable } from '@/features/estructura/components/FechaTable';
import { CalendarioView } from '@/features/estructura/components/CalendarioView';

type ViewMode = 'tabla' | 'calendario';

export default function FechasAcademicasPage() {
  const [view, setView] = useState<ViewMode>('tabla');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Fechas académicas
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Calendario de parciales, TP, coloquios y recuperatorios.
          </p>
        </div>
        <div className="flex rounded-lg border border-gray-300 bg-gray-100 p-0.5">
          <button
            type="button"
            onClick={() => setView('tabla')}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              view === 'tabla'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Tabla
          </button>
          <button
            type="button"
            onClick={() => setView('calendario')}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              view === 'calendario'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Calendario
          </button>
        </div>
      </div>

      {view === 'tabla' ? <FechaTable /> : <CalendarioView />}
    </div>
  );
}
