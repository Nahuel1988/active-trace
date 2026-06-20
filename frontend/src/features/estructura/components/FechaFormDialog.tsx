// ── FechaFormDialog ───────────────────────────────────────────────────────────
// Modal con RHF + Zod para crear/editar fechas académicas.

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type {
  FechaAcademica,
  FechaAcademicaFormData,
  TipoFecha,
} from '@/features/estructura/types';
import { useCrearFecha, useActualizarFecha } from '@/features/estructura/hooks/useEstructura';

const TIPOS: { value: TipoFecha; label: string }[] = [
  { value: 'Parcial', label: 'Parcial' },
  { value: 'TP', label: 'TP' },
  { value: 'Coloquio', label: 'Coloquio' },
  { value: 'Recuperatorio', label: 'Recuperatorio' },
];

const fechaSchema = z.object({
  materia_id: z.string().min(1, 'La materia es requerida'),
  cohorte_id: z.string().min(1, 'El cohorte es requerido'),
  tipo: z.enum(['Parcial', 'TP', 'Coloquio', 'Recuperatorio']),
  numero: z.coerce.number().int().min(1, 'Debe ser ≥ 1'),
  periodo: z.string().min(1, 'El período es requerido'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  titulo: z.string().min(1, 'El título es requerido'),
});

type FormData = z.infer<typeof fechaSchema>;

interface Props {
  isOpen: boolean;
  onClose: () => void;
  editFecha?: FechaAcademica;
}

export function FechaFormDialog({ isOpen, onClose, editFecha }: Props) {
  const crearFecha = useCrearFecha();
  const actualizarFecha = useActualizarFecha();
  const isEditing = !!editFecha;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(fechaSchema),
    defaultValues: editFecha
      ? {
          materia_id: editFecha.materia_id,
          cohorte_id: editFecha.cohorte_id,
          tipo: editFecha.tipo,
          numero: editFecha.numero,
          periodo: editFecha.periodo,
          fecha: editFecha.fecha.slice(0, 16),
          titulo: editFecha.titulo,
        }
      : {
          materia_id: '',
          cohorte_id: '',
          tipo: 'Parcial',
          numero: 1,
          periodo: '',
          fecha: '',
          titulo: '',
        },
  });

  if (!isOpen) return null;

  const onSubmit = (data: FormData) => {
    if (isEditing && editFecha) {
      actualizarFecha.mutate(
        { id: editFecha.id, data: { periodo: data.periodo, fecha: data.fecha, titulo: data.titulo } },
        {
          onSuccess: () => {
            reset();
            onClose();
          },
        },
      );
    } else {
      crearFecha.mutate(data as FechaAcademicaFormData, {
        onSuccess: () => {
          reset();
          onClose();
        },
      });
    }
  };

  const isPending = crearFecha.isPending || actualizarFecha.isPending;
  const mutationError = crearFecha.error || actualizarFecha.error;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          {isEditing ? 'Editar fecha' : 'Nueva fecha académica'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Materia ID
              </label>
              <input
                {...register('materia_id')}
                disabled={isEditing}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-100"
              />
              {errors.materia_id && (
                <p className="mt-1 text-xs text-red-600">{errors.materia_id.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Cohorte ID
              </label>
              <input
                {...register('cohorte_id')}
                disabled={isEditing}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-100"
              />
              {errors.cohorte_id && (
                <p className="mt-1 text-xs text-red-600">{errors.cohorte_id.message}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Tipo
              </label>
              <select
                {...register('tipo')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                {TIPOS.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
              {errors.tipo && (
                <p className="mt-1 text-xs text-red-600">{errors.tipo.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Número
              </label>
              <input
                type="number"
                min={1}
                {...register('numero')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {errors.numero && (
                <p className="mt-1 text-xs text-red-600">{errors.numero.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Período
            </label>
            <input
              {...register('periodo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="2025-1C"
            />
            {errors.periodo && (
              <p className="mt-1 text-xs text-red-600">{errors.periodo.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Fecha
            </label>
            <input
              type="datetime-local"
              {...register('fecha')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.fecha && (
              <p className="mt-1 text-xs text-red-600">{errors.fecha.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Título
            </label>
            <input
              {...register('titulo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="1er parcial"
            />
            {errors.titulo && (
              <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>
            )}
          </div>

          {mutationError && (
            <p className="text-sm text-red-600">
              {(mutationError as Error).message}
            </p>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isPending ? 'Guardando...' : isEditing ? 'Actualizar' : 'Crear'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
