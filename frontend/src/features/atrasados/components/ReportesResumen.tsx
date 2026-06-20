import type { ReportesResponse } from '@/features/atrasados/types';

interface ReportesResumenProps {
  data: ReportesResponse;
}

export function ReportesResumen({ data }: ReportesResumenProps) {
  if (data.sin_datos) {
    return (
      <div className="text-sm text-gray-500 py-4">
        No hay datos disponibles para esta comisión
      </div>
    );
  }

  const cards = [
    { label: 'Alumnos', value: data.total_alumnos },
    { label: 'Actividades', value: data.total_actividades },
    { label: 'Tasa aprobación', value: `${data.tasa_abrobacion_pct}%` },
    { label: 'Atrasados', value: data.alumnos_atrasados },
    { label: 'Al día', value: data.alumnos_al_dia },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="rounded-md bg-white border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{card.value}</p>
          <p className="mt-1 text-xs text-gray-500">{card.label}</p>
        </div>
      ))}
    </div>
  );
}
