import { useState } from 'react';
import { useComisionContext } from '@/shared/comision/useComisionContext';
import { useSearchParams } from 'react-router-dom';
import { useLiquidaciones } from '@/features/finanzas/hooks/useLiquidaciones';
import { useCerrarLiquidacion, useCalcularPeriodo } from '@/features/finanzas/hooks/useLiquidacionMutations';
import { LiquidacionSegmentada } from '@/features/finanzas/components/LiquidacionSegmentada';
import { PeriodoSelector } from '@/features/finanzas/components/PeriodoSelector';
import { CerrarLiquidacionDialog } from '@/features/finanzas/components/CerrarLiquidacionDialog';

interface Props {
  canCerrar?: boolean;
  canCalcular?: boolean;
}

export function LiquidacionesPage({ canCerrar = false, canCalcular = false }: Props) {
  const { cohorte_id } = useComisionContext();
  const [searchParams] = useSearchParams();
  const periodo = searchParams.get('periodo') ?? '';

  const [dialogLiqId, setDialogLiqId] = useState<string | null>(null);
  const [cerrarError, setCerrarError] = useState<string | null>(null);

  const { data, isLoading } = useLiquidaciones(cohorte_id, periodo);
  const cerrarMutation = useCerrarLiquidacion(cohorte_id, periodo);
  const calcularMutation = useCalcularPeriodo(cohorte_id, periodo);

  function handleCerrar(id: string) {
    setCerrarError(null);
    setDialogLiqId(id);
  }

  function handleConfirmarCierre() {
    if (!dialogLiqId) return;
    cerrarMutation.mutate(dialogLiqId, {
      onSuccess: () => setDialogLiqId(null),
      onError: () => setCerrarError('La liquidación ya está cerrada'),
    });
  }

  if (!cohorte_id || !periodo) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-400">
        <p>Seleccioná una comisión y un período para ver las liquidaciones</p>
        <PeriodoSelector className="mt-4 border border-gray-300 rounded-lg px-3 py-2" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Liquidaciones</h1>
        <div className="flex items-center gap-3">
          <PeriodoSelector className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
          {canCalcular && (
            <button
              onClick={() => calcularMutation.mutate()}
              disabled={calcularMutation.isPending}
              className="px-4 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Calcular período
            </button>
          )}
        </div>
      </div>

      {isLoading && <p className="text-gray-400">Cargando...</p>}

      {data && (
        <LiquidacionSegmentada
          vista={data}
          canCerrar={canCerrar}
          onCerrar={handleCerrar}
        />
      )}

      <CerrarLiquidacionDialog
        open={dialogLiqId !== null}
        onConfirm={handleConfirmarCierre}
        onCancel={() => { setDialogLiqId(null); setCerrarError(null); }}
        isPending={cerrarMutation.isPending}
        error={cerrarError}
      />
    </div>
  );
}
