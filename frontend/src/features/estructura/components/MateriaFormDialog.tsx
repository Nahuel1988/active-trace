// ── MateriaFormDialog ─────────────────────────────────────────────────────────
// Modal RHF+Zod para crear o editar una materia.

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { MateriaFormData, ClavePlus } from '@/features/estructura/types';

const CLAVES_PLUS: ClavePlus[] = ['PROG', 'BD', 'ARQ', 'MAT', 'MET'];

const CLAVES_PLUS_SET = new Set(['PROG', 'BD', 'ARQ', 'MAT', 'MET']);

const materiaSchema = z.object({
  nombre: z.string().min(1, 'El nombre es requerido'),
  clave_plus: z
    .string()
    .min(1, 'La clave de Plus es obligatoria')
    .refine((val): val is ClavePlus => CLAVES_PLUS_SET.has(val), 'Clave inválida'),
});

interface MateriaFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: MateriaFormData) => void;
  isPending: boolean;
  error: string | null;
  defaultValues?: Partial<MateriaFormData>;
}

export function MateriaFormDialog({
  open,
  onClose,
  onSubmit,
  isPending,
  error,
  defaultValues,
}: MateriaFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MateriaFormData>({
    resolver: zodResolver(materiaSchema),
    defaultValues,
  });

  if (!open) return null;

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          {defaultValues ? 'Editar materia' : 'Nueva materia'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Nombre
            </label>
            <input
              {...register('nombre')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Nombre de la materia"
            />
            {errors.nombre && (
              <p className="mt-1 text-xs text-red-600">{errors.nombre.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Clave de Plus
            </label>
            <select
              {...register('clave_plus')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              defaultValue=""
            >
              <option value="" disabled>
                Seleccionar clave…
              </option>
              {CLAVES_PLUS.map((clave) => (
                <option key={clave} value={clave}>
                  {clave}
                </option>
              ))}
            </select>
            {errors.clave_plus && (
              <p className="mt-1 text-xs text-red-600">{errors.clave_plus.message}</p>
            )}
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isPending ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
