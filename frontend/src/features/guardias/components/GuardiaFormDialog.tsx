import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Spinner } from '@/shared/components/Spinner';
import type { CatalogoItem, GuardiaCreateRequest } from '../types';

const DIAS = [
  'lunes',
  'martes',
  'miércoles',
  'jueves',
  'viernes',
  'sábado',
  'domingo',
] as const;

const guardiaSchema = z.object({
  materia_id: z.string().min(1, 'Seleccioná una materia'),
  carrera_id: z.string().min(1, 'Seleccioná una carrera'),
  cohorte_id: z.string().min(1, 'Seleccioná un cohorte'),
  dia: z.string().min(1, 'Seleccioná un día'),
  horario: z.string().min(1, 'Ingresá el horario'),
  comentarios: z.string().optional(),
});

type GuardiaFormValues = z.infer<typeof guardiaSchema>;

interface GuardiaFormDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: GuardiaCreateRequest) => Promise<void>;
  materias: CatalogoItem[];
  carreras: CatalogoItem[];
  cohortes: CatalogoItem[];
  isLoadingCatalogs?: boolean;
}

export function GuardiaFormDialog({
  isOpen,
  onClose,
  onSubmit,
  materias,
  carreras,
  cohortes,
  isLoadingCatalogs = false,
}: GuardiaFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GuardiaFormValues>({
    resolver: zodResolver(guardiaSchema),
    defaultValues: {
      materia_id: '',
      carrera_id: '',
      cohorte_id: '',
      dia: '',
      horario: '',
      comentarios: '',
    },
  });

  if (!isOpen) return null;

  const handleFormSubmit = async (values: GuardiaFormValues) => {
    await onSubmit(values);
    reset();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative z-10 w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900">
          Nueva guardia
        </h2>

        {isLoadingCatalogs ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : (
          <form
            onSubmit={handleSubmit(handleFormSubmit)}
            className="mt-4 space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Materia
              </label>
              <select
                {...register('materia_id')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">Seleccionar materia</option>
                {materias.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nombre}
                  </option>
                ))}
              </select>
              {errors.materia_id && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.materia_id.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Carrera
              </label>
              <select
                {...register('carrera_id')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">Seleccionar carrera</option>
                {carreras.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
              {errors.carrera_id && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.carrera_id.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Cohorte
              </label>
              <select
                {...register('cohorte_id')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">Seleccionar cohorte</option>
                {cohortes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
              {errors.cohorte_id && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.cohorte_id.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Día
              </label>
              <select
                {...register('dia')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">Seleccionar día</option>
                {DIAS.map((d) => (
                  <option key={d} value={d}>
                    {d.charAt(0).toUpperCase() + d.slice(1)}
                  </option>
                ))}
              </select>
              {errors.dia && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.dia.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Horario
              </label>
              <input
                type="text"
                {...register('horario')}
                placeholder="Ej: 14:00–15:00"
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {errors.horario && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.horario.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Comentarios{' '}
                <span className="text-gray-400">(opcional)</span>
              </label>
              <textarea
                {...register('comentarios')}
                rows={3}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  reset();
                  onClose();
                }}
                disabled={isSubmitting}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {isSubmitting ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
