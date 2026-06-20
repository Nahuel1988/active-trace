import type { LiquidacionVista } from '@/features/finanzas/types';
import { KpisCabecera } from './KpisCabecera';
import { SegmentoTable } from './SegmentoTable';

interface Props {
  vista: LiquidacionVista;
  onCerrar?: (id: string) => void;
  canCerrar?: boolean;
}

export function LiquidacionSegmentada({ vista, onCerrar, canCerrar }: Props) {
  const totalItems =
    vista.segmentos.general.liquidaciones.length +
    vista.segmentos.nexo.liquidaciones.length +
    vista.segmentos.facturantes.liquidaciones.length;

  return (
    <div>
      <KpisCabecera kpis={vista.kpis} />
      {totalItems === 0 ? (
        <p className="text-center text-gray-400 py-12">Sin liquidaciones para el período</p>
      ) : (
        <>
          <SegmentoTable titulo="General" segmento={vista.segmentos.general} onCerrar={onCerrar} canCerrar={canCerrar} />
          <SegmentoTable titulo="NEXO" segmento={vista.segmentos.nexo} onCerrar={onCerrar} canCerrar={canCerrar} />
          <SegmentoTable titulo="Facturantes" segmento={vista.segmentos.facturantes} onCerrar={onCerrar} canCerrar={canCerrar} />
        </>
      )}
    </div>
  );
}
