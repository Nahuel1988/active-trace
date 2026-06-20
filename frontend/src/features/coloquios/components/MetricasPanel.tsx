import { useMetricas } from '../hooks/useColoquios';
import { Spinner } from '@/shared/components/Spinner';

export function MetricasPanel() {
  const { data: metricas, isLoading } = useMetricas();

  if (isLoading) return <Spinner className="py-8" />;
  if (!metricas) return null;

  const cards = [
    { label: 'Total candidatos', value: metricas.total_candidatos },
    { label: 'Instancias activas', value: metricas.instancias_activas },
    { label: 'Reservas activas', value: metricas.reservas_activas },
    { label: 'Notas registradas', value: metricas.notas_registradas },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        >
          <p className="text-sm font-medium text-gray-500">{card.label}</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
