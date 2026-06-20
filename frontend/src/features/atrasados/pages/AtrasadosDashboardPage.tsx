import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useComisionContext } from '@/shared/comision/useComisionContext';
import { usePermission } from '@/shared/hooks/usePermission';
import {
  useAtrasados,
  useRanking,
  useReportes,
  useNotasFinales,
  useEntregasPendientes,
} from '@/features/atrasados/hooks/useAtrasados';
import { AtrasadosTable } from '@/features/atrasados/components/AtrasadosTable';
import { RankingTable } from '@/features/atrasados/components/RankingTable';
import { ReportesResumen } from '@/features/atrasados/components/ReportesResumen';
import { NotasFinalesTable } from '@/features/atrasados/components/NotasFinalesTable';
import { EntregasSinCorregir } from '@/features/atrasados/components/EntregasSinCorregir';

export default function AtrasadosDashboardPage() {
  const { materia_id, cohorte_id } = useComisionContext();
  const canCommunicate = usePermission('comunicacion:enviar');
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string[]>([]);

  const { data: atrasadosData, isLoading: atrasadosLoading } = useAtrasados(materia_id, cohorte_id);
  const { data: rankingData, isLoading: rankingLoading } = useRanking(materia_id, cohorte_id);
  const { data: reportesData, isLoading: reportesLoading } = useReportes(materia_id, cohorte_id);
  const { data: notasData, isLoading: notasLoading } = useNotasFinales(materia_id, cohorte_id);
  const { data: entregasData, isLoading: entregasLoading } = useEntregasPendientes(materia_id, cohorte_id);

  const handleCommunicate = () => {
    if (selected.length === 0) return;
    const ids = selected.join(',');
    navigate(`/comunicaciones?alumnos=${ids}&materia=${materia_id}&cohorte=${cohorte_id}`);
  };

  if (!materia_id || !cohorte_id) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">
        Seleccioná una comisión para ver el dashboard
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard académico</h1>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Atrasados</h2>
        {atrasadosLoading ? (
          <span className="text-sm text-gray-500">Cargando...</span>
        ) : (
          <AtrasadosTable
            items={atrasadosData?.items ?? []}
            selected={selected}
            onSelectionChange={setSelected}
            canCommunicate={canCommunicate}
            onCommunicate={handleCommunicate}
          />
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Ranking</h2>
        {rankingLoading ? (
          <span className="text-sm text-gray-500">Cargando...</span>
        ) : (
          <RankingTable items={rankingData?.items ?? []} />
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Reportes</h2>
        {reportesLoading ? (
          <span className="text-sm text-gray-500">Cargando...</span>
        ) : reportesData ? (
          <ReportesResumen data={reportesData} />
        ) : null}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Notas finales</h2>
        {notasLoading ? (
          <span className="text-sm text-gray-500">Cargando...</span>
        ) : (
          <NotasFinalesTable items={notasData?.items ?? []} />
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-800">Entregas sin corregir</h2>
        {entregasLoading ? (
          <span className="text-sm text-gray-500">Cargando...</span>
        ) : entregasData ? (
          <EntregasSinCorregir
            items={entregasData.items}
            todasCorregidas={entregasData.todas_corregidas}
            materiaId={materia_id}
            cohorteId={cohorte_id}
          />
        ) : null}
      </section>
    </div>
  );
}
