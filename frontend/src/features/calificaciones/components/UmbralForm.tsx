import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const umbralSchema = z.object({
  umbral: z.coerce.number().int().min(0, 'Debe ser un número entre 0 y 100').max(100, 'Debe ser un número entre 0 y 100'),
});

type UmbralFormData = z.infer<typeof umbralSchema>;

interface UmbralFormProps {
  umbralPorcentaje: number;
  isPending: boolean;
  onSave: (value: number) => void;
}

export function UmbralForm({ umbralPorcentaje, isPending, onSave }: UmbralFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UmbralFormData>({
    resolver: zodResolver(umbralSchema),
    defaultValues: { umbral: umbralPorcentaje },
  });

  const onSubmit = (data: UmbralFormData) => {
    onSave(data.umbral);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex items-end gap-4">
      <div className="flex flex-col gap-1">
        <label htmlFor="umbral-input" className="text-sm font-medium text-gray-700">
          Umbral de aprobación (%)
        </label>
        <input
          id="umbral-input"
          type="number"
          aria-label="Umbral de aprobación (%)"
          {...register('umbral')}
          className="w-32 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.umbral && (
          <p className="text-xs text-red-600">{errors.umbral.message}</p>
        )}
      </div>
      <button
        type="submit"
        disabled={isPending}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:bg-gray-300 disabled:text-gray-500"
      >
        {isPending ? 'Guardando...' : 'Guardar umbral'}
      </button>
    </form>
  );
}
