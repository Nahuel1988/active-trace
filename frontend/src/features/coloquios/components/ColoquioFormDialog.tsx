import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod/v4';
import type { ColoquioFormData } from '../types';
import { useCrearColoquio } from '../hooks/useColoquios';

const coloquioSchema = z.object({
  materia_id: z.string().min(1, 'La materia es requerida'),
  cohorte_id: z.string().min(1, 'El cohorte es requerido'),
  tipo: z.string().min(1, 'El tipo es requerido'),
  instancia: z.string().min(1, 'La instancia es requerida'),
  dias_disponibles: z
    .array(z.string())
    .min(1, 'Seleccioná al menos un día'),
});

interface ColoquioFormDialogProps {
  open: boolean;
  onClose: () => void;
}

export function ColoquioFormDialog({ open, onClose }: ColoquioFormDialogProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ColoquioFormData>({
    resolver: zodResolver(coloquioSchema),
    defaultValues: {
      materia_id: '',
      cohorte_id: '',
      tipo: '',
      instancia: '',
      dias_disponibles: [],
    },
  });

  const crearColoquio = useCrearColoquio();

  const onSubmit = (data: ColoquioFormData) => {
    crearColoquio.mutate(data, { onSuccess: () => onClose() });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">
          Nueva convocatoria
        </h2>
        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Materia
            </label>
            <input
              {...register('materia_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            {errors.materia_id && (
              <p className="mt-1 text-xs text-red-500">
                {errors.materia_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Cohorte
            </label>
            <input
              {...register('cohorte_id')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            {errors.cohorte_id && (
              <p className="mt-1 text-xs text-red-500">
                {errors.cohorte_id.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Tipo
            </label>
            <select
              {...register('tipo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">Seleccionar...</option>
              <option value="oral">Oral</option>
              <option value="escrito">Escrito</option>
              <option value="practico">Práctico</option>
            </select>
            {errors.tipo && (
              <p className="mt-1 text-xs text-red-500">
                {errors.tipo.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Instancia
            </label>
            <input
              {...register('instancia')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            {errors.instancia && (
              <p className="mt-1 text-xs text-red-500">
                {errors.instancia.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Días disponibles
            </label>
            <div className="mt-1 flex flex-wrap gap-3">
              {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'].map(
                (dia) => (
                  <label
                    key={dia}
                    className="flex items-center gap-1 text-sm"
                  >
                    <input
                      type="checkbox"
                      value={dia}
                      {...register('dias_disponibles')}
                    />
                    {dia}
                  </label>
                ),
              )}
            </div>
            {errors.dias_disponibles && (
              <p className="mt-1 text-xs text-red-500">
                {errors.dias_disponibles.message}
              </p>
            )}
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700"
            >
              Crear
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
