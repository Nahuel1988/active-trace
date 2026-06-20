import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { SalarioBaseFormData, RolLiquidacion } from '@/features/finanzas/types';

const ROLES: RolLiquidacion[] = ['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR'];

const schema = z.object({
  rol: z.enum(['PROFESOR', 'TUTOR', 'NEXO', 'COORDINADOR']),
  monto: z.string().min(1, 'Requerido'),
  desde: z.string().min(1, 'Requerido'),
  hasta: z.string().optional(),
});

interface Props {
  open: boolean;
  onSubmit: (data: SalarioBaseFormData) => Promise<void>;
  onCancel: () => void;
  error: string | null;
  isPending: boolean;
  defaultValues?: Partial<SalarioBaseFormData>;
}

export function SalarioBaseFormDialog({ open, onSubmit, onCancel, error, isPending, defaultValues }: Props) {
  const { register, handleSubmit, formState: { errors } } = useForm<SalarioBaseFormData>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  if (!open) return null;

  return (
    <div role="dialog" aria-modal className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Salario base</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="sb-rol" className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
            <select id="sb-rol" {...register('rol')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="">Seleccioná un rol</option>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            {errors.rol && <p className="text-xs text-red-600 mt-1">{errors.rol.message}</p>}
          </div>
          <div>
            <label htmlFor="sb-monto" className="block text-sm font-medium text-gray-700 mb-1">Monto</label>
            <input id="sb-monto" type="number" step="0.01" {...register('monto')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            {errors.monto && <p className="text-xs text-red-600 mt-1">{errors.monto.message}</p>}
          </div>
          <div>
            <label htmlFor="sb-desde" className="block text-sm font-medium text-gray-700 mb-1">Desde</label>
            <input id="sb-desde" type="date" {...register('desde')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            {errors.desde && <p className="text-xs text-red-600 mt-1">{errors.desde.message}</p>}
          </div>
          <div>
            <label htmlFor="sb-hasta" className="block text-sm font-medium text-gray-700 mb-1">Hasta (opcional)</label>
            <input id="sb-hasta" type="date" {...register('hasta')} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
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
