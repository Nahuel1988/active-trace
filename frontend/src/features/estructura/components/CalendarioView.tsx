// ── CalendarioView ────────────────────────────────────────────────────────────
// Vista mensual simple del calendario de fechas académicas, agrupado por período.

import { useCalendario } from '@/features/estructura/hooks/useEstructura';
import { Spinner } from '@/shared/components/Spinner';

export function CalendarioView() {
  const { data: periodos, isLoading } = useCalendario();

  if (isLoading) return <Spinner className="py-8" />;

  if (!periodos || periodos.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500">
        No hay fechas en el calendario.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {periodos.map((p) => (
        <div key={p.periodo}>
          <h3 className="mb-3 text-md font-semibold text-gray-900">
            {p.periodo}
          </h3>
          <div className="space-y-2">
            {p.fechas.map((f) => (
              <div
                key={f.id}
                className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                      f.tipo === 'Parcial'
                        ? 'bg-blue-100 text-blue-700'
                        : f.tipo === 'TP'
                          ? 'bg-purple-100 text-purple-700'
                          : f.tipo === 'Coloquio'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {f.tipo}
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {f.titulo}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(f.fecha).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
