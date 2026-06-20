import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCrearTarea } from '@/features/tareas/hooks/useTareaMutations';
import type { TareaFormData } from '@/features/tareas/types';

const tareaSchema = z.object({
  titulo: z.string().min(1, 'El título es requerido'),
  descripcion: z.string().optional().default(''),
  prioridad: z.string().min(1, 'Seleccioná una prioridad'),
  asignado_a: z.string().min(1, 'Seleccioná un usuario'),
  fecha_vencimiento: z.string().optional(),
});

type FormValues = z.infer<typeof tareaSchema>;

interface TareaFormDialogProps {
  open: boolean;
  onClose: () => void;
}

export function TareaFormDialog({ open, onClose }: TareaFormDialogProps) {
  const { mutate: crearTarea, isPending } = useCrearTarea();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(tareaSchema),
    defaultValues: {
      titulo: '',
      descripcion: '',
      prioridad: 'media',
      asignado_a: '',
      fecha_vencimiento: '',
    },
  });

  const onSubmit = (data: TareaFormData) => {
    crearTarea(data, {
      onSuccess: () => {
        reset();
        onClose();
      },
    });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Nueva tarea
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="titulo" className="block text-sm font-medium text-gray-700">
              Título
            </label>
            <input
              id="titulo"
              type="text"
              {...register('titulo')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            {errors.titulo && (
              <p className="mt-1 text-xs text-red-600">{errors.titulo.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="descripcion" className="block text-sm font-medium text-gray-700">
              Descripción
            </label>
            <textarea
              id="descripcion"
              rows={3}
              {...register('descripcion')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="prioridad" className="block text-sm font-medium text-gray-700">
                Prioridad
              </label>
              <select
                id="prioridad"
                {...register('prioridad')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
                <option value="urgente">Urgente</option>
              </select>
              {errors.prioridad && (
                <p className="mt-1 text-xs text-red-600">{errors.prioridad.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="fecha_vencimiento" className="block text-sm font-medium text-gray-700">
                Vencimiento
              </label>
              <input
                id="fecha_vencimiento"
                type="date"
                {...register('fecha_vencimiento')}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label htmlFor="asignado_a" className="block text-sm font-medium text-gray-700">
              Asignar a
            </label>
            <select
              id="asignado_a"
              {...register('asignado_a')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Seleccionar...</option>
              <option value="current-user">Yo</option>
            </select>
            {errors.asignado_a && (
              <p className="mt-1 text-xs text-red-600">{errors.asignado_a.message}</p>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
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
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isPending ? 'Creando...' : 'Crear tarea'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
