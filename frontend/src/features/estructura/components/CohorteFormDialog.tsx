// ── CohorteFormDialog ─────────────────────────────────────────────────────────
// Modal RHF+Zod para crear o editar una cohorte.

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { CohorteFormData } from '@/features/estructura/types';

const cohorteSchema = z.object({
  etiqueta: z.string().min(1, 'La etiqueta es requerida'),
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  fecha_inicio: z.string().min(1, 'La fecha de inicio es requerida'),
  fecha_fin: z.string().optional(),
});

interface CohorteFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: CohorteFormData) => void;
  isPending: boolean;
  error: string | null;
  defaultValues?: Partial<CohorteFormData>;
}

export function CohorteFormDialog({
  open,
  onClose,
  onSubmit,
  isPending,
  error,
  defaultValues,
}: CohorteFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CohorteFormData>({
    resolver: zodResolver(cohorteSchema),
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
          {defaultValues ? 'Editar cohorte' : 'Nueva cohorte'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Etiqueta
            </label>
            <input
              {...register('etiqueta')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Ej: 2024-A"
            />
            {errors.etiqueta && (
              <p className="mt-1 text-xs text-red-600">{errors.etiqueta.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Carrera
            </label>
            <input
              {...register('carrera_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="ID de la carrera"
            />
            {errors.carrera_id && (
              <p className="mt-1 text-xs text-red-600">{errors.carrera_id.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Fecha de inicio
            </label>
            <input
              type="date"
              {...register('fecha_inicio')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.fecha_inicio && (
              <p className="mt-1 text-xs text-red-600">{errors.fecha_inicio.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Fecha de fin <span className="text-gray-400">(opcional)</span>
            </label>
            <input
              type="date"
              {...register('fecha_fin')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
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
