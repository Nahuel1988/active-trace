import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useActualizarVigencia } from '@/features/equipos/hooks/useEquipoMutations';

const schema = z
  .object({
    vigencia_desde: z.string().min(1, 'Requerido'),
    vigencia_hasta: z.string().min(1, 'Requerido'),
  })
  .refine(
    (data) => {
      if (!data.vigencia_desde || !data.vigencia_hasta) return true;
      return new Date(data.vigencia_desde) < new Date(data.vigencia_hasta);
    },
    {
      message: 'La fecha de inicio debe ser anterior a la fecha de fin',
      path: ['vigencia_hasta'],
    },
  );

type FormData = z.infer<typeof schema>;

interface VigenciaFormProps {
  equipoIds: string[];
  onSuccess?: () => void;
}

export function VigenciaForm({ equipoIds, onSuccess }: VigenciaFormProps) {
  const mutation = useActualizarVigencia();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = (data: FormData) => {
    mutation.mutate(
      {
        equipo_ids: equipoIds,
        vigencia_desde: data.vigencia_desde,
        vigencia_hasta: data.vigencia_hasta,
      },
      {
        onSuccess: (res) => {
          onSuccess?.();
        },
      },
    );
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex items-end gap-3 rounded-lg border border-gray-200 bg-white p-4"
    >
      <div>
        <label className="block text-xs font-medium text-gray-700">
          Desde
        </label>
        <input
          type="date"
          {...register('vigencia_desde')}
          className="mt-1 block rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.vigencia_desde && (
          <p className="mt-1 text-xs text-red-500">
            {errors.vigencia_desde.message}
          </p>
        )}
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-700">Hasta</label>
        <input
          type="date"
          {...register('vigencia_hasta')}
          className="mt-1 block rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.vigencia_hasta && (
          <p className="mt-1 text-xs text-red-500">
            {errors.vigencia_hasta.message}
          </p>
        )}
      </div>
      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded-md bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {mutation.isPending ? 'Guardando...' : 'Guardar'}
      </button>
      {mutation.isError && (
        <p className="text-sm text-red-600">Error al actualizar vigencia</p>
      )}
    </form>
  );
}
