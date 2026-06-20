import { useState } from 'react';
import { useSalariosBase, useSalariosPlus } from '@/features/finanzas/hooks/useGrilla';
import {
  useCrearSalarioBase,
  useActualizarSalarioBase,
  useEliminarSalarioBase,
  useCrearSalarioPlus,
  useActualizarSalarioPlus,
  useEliminarSalarioPlus,
} from '@/features/finanzas/hooks/useGrillaMutations';
import { SalarioBaseTable } from '@/features/finanzas/components/SalarioBaseTable';
import { SalarioBaseFormDialog } from '@/features/finanzas/components/SalarioBaseFormDialog';
import { SalarioPlusTable } from '@/features/finanzas/components/SalarioPlusTable';
import { SalarioPlusFormDialog } from '@/features/finanzas/components/SalarioPlusFormDialog';
import type { SalarioBase, SalarioPlus, RolLiquidacion, GrupoPlus, SalarioBaseFormData, SalarioPlusFormData } from '@/features/finanzas/types';

export function GrillaSalarialPage() {
  const [rolFilter, setRolFilter] = useState<RolLiquidacion | undefined>();
  const [grupoFilter, setGrupoFilter] = useState<GrupoPlus | undefined>();

  const [baseDialog, setBaseDialog] = useState<{ open: boolean; item?: SalarioBase }>({ open: false });
  const [plusDialog, setPlusDialog] = useState<{ open: boolean; item?: SalarioPlus }>({ open: false });
  const [baseError, setBaseError] = useState<string | null>(null);
  const [plusError, setPlusError] = useState<string | null>(null);

  const { data: salariosBase = [] } = useSalariosBase(rolFilter);
  const { data: salariosPlus = [] } = useSalariosPlus(grupoFilter);

  const crearBase = useCrearSalarioBase();
  const actualizarBase = useActualizarSalarioBase();
  const eliminarBase = useEliminarSalarioBase();
  const crearPlus = useCrearSalarioPlus();
  const actualizarPlus = useActualizarSalarioPlus();
  const eliminarPlus = useEliminarSalarioPlus();

  async function handleSubmitBase(data: SalarioBaseFormData) {
    setBaseError(null);
    try {
      if (baseDialog.item) {
        await actualizarBase.mutateAsync({ id: baseDialog.item.id, data: { monto: data.monto, hasta: data.hasta } });
      } else {
        await crearBase.mutateAsync(data);
      }
      setBaseDialog({ open: false });
    } catch {
      setBaseError('Solapamiento de vigencia para el rol seleccionado');
    }
  }

  async function handleSubmitPlus(data: SalarioPlusFormData) {
    setPlusError(null);
    try {
      if (plusDialog.item) {
        await actualizarPlus.mutateAsync({ id: plusDialog.item.id, data: { descripcion: data.descripcion, monto: data.monto, hasta: data.hasta } });
      } else {
        await crearPlus.mutateAsync(data);
      }
      setPlusDialog({ open: false });
    } catch {
      setPlusError('Solapamiento de vigencia para el grupo y rol seleccionados');
    }
  }

  return (
    <div className="p-6 space-y-10">
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Salario Base</h2>
          <button
            onClick={() => { setBaseError(null); setBaseDialog({ open: true }); }}
            className="px-4 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Nuevo salario base
          </button>
        </div>
        <SalarioBaseTable
          items={salariosBase}
          rolFilter={rolFilter}
          onRolFilter={setRolFilter}
          onEditar={(item) => { setBaseError(null); setBaseDialog({ open: true, item }); }}
          onEliminar={(id) => eliminarBase.mutate(id)}
        />
      </section>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Salario Plus</h2>
          <button
            onClick={() => { setPlusError(null); setPlusDialog({ open: true }); }}
            className="px-4 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Nuevo plus
          </button>
        </div>
        <SalarioPlusTable
          items={salariosPlus}
          grupoFilter={grupoFilter}
          onGrupoFilter={setGrupoFilter}
          onEditar={(item) => { setPlusError(null); setPlusDialog({ open: true, item }); }}
          onEliminar={(id) => eliminarPlus.mutate(id)}
        />
      </section>

      <SalarioBaseFormDialog
        open={baseDialog.open}
        onSubmit={handleSubmitBase}
        onCancel={() => setBaseDialog({ open: false })}
        error={baseError}
        isPending={crearBase.isPending || actualizarBase.isPending}
        defaultValues={baseDialog.item ? { rol: baseDialog.item.rol, monto: baseDialog.item.monto, desde: baseDialog.item.desde, hasta: baseDialog.item.hasta ?? undefined } : undefined}
      />

      <SalarioPlusFormDialog
        open={plusDialog.open}
        onSubmit={handleSubmitPlus}
        onCancel={() => setPlusDialog({ open: false })}
        error={plusError}
        isPending={crearPlus.isPending || actualizarPlus.isPending}
        defaultValues={plusDialog.item ? { grupo: plusDialog.item.grupo, rol: plusDialog.item.rol, descripcion: plusDialog.item.descripcion, monto: plusDialog.item.monto, desde: plusDialog.item.desde, hasta: plusDialog.item.hasta ?? undefined } : undefined}
      />
    </div>
  );
}
