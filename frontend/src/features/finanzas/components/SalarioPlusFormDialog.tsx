import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { SalarioPlusFormData, RolLiquidacion, GrupoPlus } from '@/features/finanzas/types';

const ROLES: RolLiquidacion[] = ['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'];
const GRUPOS: GrupoPlus[] = ['PROG', 'BD', 'ARQ', 'MAT', 'MET'];

const schema = z.object({
  grupo: z.enum(['PROG', 'BD', 'ARQ', 'MAT', 'MET']),
  rol: z.enum(['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR']),
  descripcion: z.string().min(1, 'Requerido'),
  monto: z.string().min(1, 'Requerido'),
  desde: z.string().min(1, 'Requerido'),
  hasta: z.string().optional(),
});

interface Props {
  open: boolean;
  onSubmit: (data: SalarioPlusFormData) => Promise<void>;
  onCancel: () => void;
  error: string | null;
  isPending: boolean;
  defaultValues?: Partial<SalarioPlusFormData>;
}

export function SalarioPlusFormDialog({ open, onSubmit, onCancel, error, isPending, defaultValues }: Props) {
  const { register, handleSubmit, formState: { errors } } = useForm<SalarioPlusFormData>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  if (!open) return null;

  return (
    <div role="dialog" aria-modal className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Salario plus</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="sp-grupo" className="block text-sm font-medium text-gray-700 mb-1">Grupo</label>
              <select id="sp-grupo" {...register('grupo')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value="">Seleccioná</option>
                {GRUPOS.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
              {errors.grupo && <p className="text-xs text-red-600 mt-1">{errors.grupo.message}</p>}
            </div>
            <div>
              <label htmlFor="sp-rol" className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
              <select id="sp-rol" {...register('rol')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value="">Seleccioná</option>
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
              {errors.rol && <p className="text-xs text-red-600 mt-1">{errors.rol.message}</p>}
            </div>
          </div>
          <div>
            <label htmlFor="sp-desc" className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
            <input id="sp-desc" type="text" {...register('descripcion')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            {errors.descripcion && <p className="text-xs text-red-600 mt-1">{errors.descripcion.message}</p>}
          </div>
          <div>
            <label htmlFor="sp-monto" className="block text-sm font-medium text-gray-700 mb-1">Monto</label>
            <input id="sp-monto" type="number" step="0.01" {...register('monto')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            {errors.monto && <p className="text-xs text-red-600 mt-1">{errors.monto.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="sp-desde" className="block text-sm font-medium text-gray-700 mb-1">Desde</label>
              <input id="sp-desde" type="date" {...register('desde')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              {errors.desde && <p className="text-xs text-red-600 mt-1">{errors.desde.message}</p>}
            </div>
            <div>
              <label htmlFor="sp-hasta" className="block text-sm font-medium text-gray-700 mb-1">Hasta (opcional)</label>
              <input id="sp-hasta" type="date" {...register('hasta')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onCancel} className="px-4 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={isPending} className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">Guardar</button>
          </div>
        </form>
      </div>
    </div>
  );
}
